#!/usr/bin/env python3
"""General, model-agnostic benchmark harness for ResCamp and comparable tools.

The harness separates hidden-user (Team U), tested system (Team S), and blinded
Evaluator (Team E) boundaries. Live adapters are ordinary commands that exchange one
JSON object over stdin/stdout per invocation. Built-in fixtures validate the harness;
they are never evidence of model quality.
"""
from __future__ import annotations

import argparse
import hashlib
import concurrent.futures
import json
import math
import os
import random
import re
import secrets
import shlex
import shutil
import statistics
import subprocess
import tempfile
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

VERSION = "0.10.0"
SKILL_DIR = Path(__file__).resolve().parent.parent
RUBRIC_PATH = SKILL_DIR / "assets" / "universal_rubric.json"
OVERLAY_PATH = SKILL_DIR / "assets" / "archetype_overlays.json"
IMPORTANCE_WEIGHT = {"low": 1.0, "material": 2.0, "critical": 4.0}
SEVERITY_PENALTY = {"minor": 4.0, "major": 14.0, "critical": 40.0}
RATING_IDS = [item["id"] for item in json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))["dimensions"]]
ARCHETYPES = {
    "experimental", "computational", "observational", "qualitative-field",
    "humanities-interpretive", "conceptual-normative", "evidence-synthesis",
    "policy-program-evaluation", "design-engineering", "creative-practice", "mixed-methods",
}

# Hardcoded ratings for the built-in fixture conditions only. These are constants
# that exercise the harness, not measurements. Any condition absent from this table
# is refused rather than scored, so plugging in a real Team S without a real Team E
# fails loudly instead of producing a fabricated number with a confident CI.
FIXTURE_RATING_TABLE: dict[str, dict[str, Any]] = {
    "rescamp-current-fixture": {"default": 3.3, "overrides": {"interview-efficiency": 3.6, "proportionality-usability": 3.7}},
    "exhaustive-form-fixture": {"default": 3.0, "overrides": {"interview-efficiency": 1.4, "proportionality-usability": 1.7}},
    "no-skill-fixture": {"default": 1.4, "overrides": {"mission-scope": 1.8}},
}

SYNTHETIC_EVIDENCE_CLASS = "synthetic-fixture"
LIVE_EVIDENCE_CLASS = "live-adapter"
UNMATCHED_LIVE_EVIDENCE_CLASS = "live-adapter-unmatched-controls"
UNSPECIFIED_EVIDENCE_CLASS = "unspecified"
EVIDENCE_NOTE = {
    SYNTHETIC_EVIDENCE_CLASS: (
        "Synthetic fixture output. Team E ratings are hardcoded constants selected by condition id, "
        "so scores are predetermined by the fixture and are NOT model-performance estimates or measurements."
    ),
    LIVE_EVIDENCE_CLASS: (
        "Produced by external live adapters. Evidential value depends entirely on those adapters and on "
        "the matched controls recorded in the condition."
    ),
    UNMATCHED_LIVE_EVIDENCE_CLASS: (
        "Produced by external live adapters without a verified matched-control matrix. Treat as an "
        "uncontrolled run, not comparative evidence."
    ),
    UNSPECIFIED_EVIDENCE_CLASS: (
        "Provenance not declared by the producing evaluation; do not treat as a measurement without checking "
        "which adapters produced it."
    ),
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def stage_evaluator_artifacts(final: dict[str, Any], run_dir: Path, output_dir: Path,
                              candidate_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    values = final.get("artifacts", [])
    if not isinstance(values, list) or any(not isinstance(value, str) or not value for value in values):
        raise RuntimeError("Team S artifacts must be a list of nonempty paths")
    output_root = output_dir.resolve()
    staging_root = output_root / "evaluator-candidates"
    staging_root.mkdir(parents=True, exist_ok=True)
    try:
        staging_root.resolve().relative_to(output_root)
    except ValueError as exc:
        raise RuntimeError("evaluator artifact directory is outside the output directory") from exc
    run_root = run_dir.resolve()
    seen: set[Path] = set()
    sources: list[tuple[str, Path]] = []
    for value in values:
        supplied = Path(value)
        source = (supplied if supplied.is_absolute() else run_root / supplied).resolve()
        try:
            source.relative_to(run_root)
        except ValueError as exc:
            raise RuntimeError(f"artifact is outside the run directory: {value}") from exc
        if source in seen:
            raise RuntimeError(f"duplicate artifact path: {value}")
        seen.add(source)
        if not source.is_file():
            raise RuntimeError(f"artifact is missing or not a file: {value}")
        sources.append((value, source))

    candidate_dir = staging_root / candidate_id
    candidate_dir.mkdir(parents=False, exist_ok=False)
    internal: list[dict[str, Any]] = []
    blinded: list[dict[str, Any]] = []
    for index, (value, source) in enumerate(sources, 1):
        suffix = source.suffix if re.fullmatch(r"\.[A-Za-z0-9]{1,10}", source.suffix) else ""
        opaque_name = f"artifact-{index:03d}{suffix}"
        staged = candidate_dir / opaque_name
        source_before = sha256_file(source)
        shutil.copyfile(source, staged)
        os.chmod(staged, 0o444)
        staged_before = sha256_file(staged)
        if staged_before != source_before:
            raise RuntimeError(f"artifact copy hash mismatch: {value}")
        record = {
            "id": f"artifact-{index:03d}", "source_path": str(source), "staged_path": str(staged),
            "bytes": staged.stat().st_size, "source_sha256_before": source_before,
            "staged_sha256_before": staged_before,
        }
        internal.append(record)
        blinded.append({
            "id": record["id"], "name": opaque_name, "path": str(staged),
            "bytes": record["bytes"], "sha256": staged_before,
        })
    return internal, blinded


def verify_evaluator_artifacts(records: list[dict[str, Any]]) -> None:
    for record in records:
        source = Path(record["source_path"])
        staged = Path(record["staged_path"])
        source_after = sha256_file(source) if source.is_file() else None
        staged_after = sha256_file(staged) if staged.is_file() else None
        record["source_sha256_after"] = source_after
        record["staged_sha256_after"] = staged_after
        if source_after != record["source_sha256_before"]:
            raise RuntimeError(f"source artifact changed during evaluation: {record['id']}")
        if staged_after != record["staged_sha256_before"]:
            raise RuntimeError(f"staged artifact changed during evaluation: {record['id']}")


def persist_evaluator_artifacts(records: list[dict[str, Any]], output_dir: Path,
                                candidate_id: str) -> None:
    """Persist verified copies after Team E exits, outside its evaluated path."""
    destination = output_dir.resolve() / "evaluator-candidates" / candidate_id
    destination.mkdir(parents=True, exist_ok=False)
    for record in records:
        source = Path(record["staged_path"])
        target = destination / source.name
        shutil.copyfile(source, target)
        os.chmod(target, 0o444)
        if sha256_file(target) != record["staged_sha256_after"]:
            raise RuntimeError(f"persisted artifact copy hash mismatch: {record['id']}")
        record["staged_path"] = str(target)
        record["persisted_sha256"] = sha256_file(target)


def relevant_archetype_overlays(scenario: dict[str, Any]) -> dict[str, Any]:
    source = read_json(OVERLAY_PATH)
    overlays = source.get("overlays", {})
    selected = {ident: overlays[ident] for ident in scenario["archetypes"] if ident in overlays}
    return {"version": source.get("version"), "rule": source.get("rule"), "overlays": selected}


def stable_seed(text: str) -> int:
    """Process-stable 16-bit seed.

    Python salts str.__hash__ per process (PYTHONHASHSEED), so hash() would make bootstrap
    confidence intervals differ between runs on identical inputs. SHA-256 is stable.
    """
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:4], "big") & 0xFFFF


def evidence_class_for(condition: dict[str, Any], evaluation: dict[str, Any] | None = None) -> str:
    """Classify a run's provenance. Any fixture anywhere in the chain makes the record synthetic."""
    declared = (evaluation or {}).get("evidence_class")
    if condition.get("adapter") == "fixture" or declared == SYNTHETIC_EVIDENCE_CLASS:
        return SYNTHETIC_EVIDENCE_CLASS
    if not condition.get("_matched_controls", False):
        return UNMATCHED_LIVE_EVIDENCE_CLASS
    if declared in EVIDENCE_NOTE:
        return declared
    return LIVE_EVIDENCE_CLASS


def now_id() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def positive_int_arg(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def scenario_errors(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return ["scenario must be an object"]
    errors: list[str] = []
    required = ["id", "title", "domain", "archetypes", "profile", "initial_request", "hidden_brief", "material_dimensions", "forbidden_assumptions", "required_campaign_features", "critical_defects"]
    for field in required:
        if field not in data:
            errors.append(f"missing {field}")
    for field in ("id", "title", "domain", "initial_request"):
        if not isinstance(data.get(field), str) or not data.get(field, "").strip():
            errors.append(f"{field} must be a nonempty string")
    if isinstance(data.get("id"), str) and not re.fullmatch(r"[a-z0-9][a-z0-9-]*", data["id"]):
        errors.append("id must contain lowercase letters, digits, and hyphens")
    if (not isinstance(data.get("profile"), str)
            or data.get("profile") not in {"scoped", "standard", "high-assurance"}):
        errors.append("invalid profile")
    archetypes = data.get("archetypes")
    if (not isinstance(archetypes, list) or not archetypes
            or any(not isinstance(item, str) or item not in ARCHETYPES for item in archetypes)):
        errors.append("archetypes must be a nonempty list of valid archetype IDs")
    elif len(archetypes) != len(set(archetypes)):
        errors.append("archetypes must be unique")

    hidden = data.get("hidden_brief")
    if not isinstance(hidden, dict):
        errors.append("hidden_brief must be an object")
    else:
        if not isinstance(hidden.get("facts"), dict):
            errors.append("hidden_brief.facts must be an object")
        limits = hidden.get("knowledge_limits")
        if not isinstance(limits, list) or any(not isinstance(item, str) for item in limits):
            errors.append("hidden_brief.knowledge_limits must be a list of strings")
        if not isinstance(hidden.get("answer_policy"), str) or not hidden.get("answer_policy", "").strip():
            errors.append("hidden_brief.answer_policy must be a nonempty string")
        evolution = hidden.get("evolution_rules", [])
        if not isinstance(evolution, list) or any(not isinstance(item, dict) for item in evolution):
            errors.append("hidden_brief.evolution_rules must be a list of objects")

    dims = data.get("material_dimensions")
    seen: set[str] = set()
    if not isinstance(dims, list) or not dims:
        errors.append("material_dimensions must be a nonempty list")
        dims = []
    for index, dim in enumerate(dims):
        if not isinstance(dim, dict):
            errors.append(f"dimension {index} must be an object")
            continue
        for field in ("id", "importance", "expected_by_turn", "acceptable_resolution"):
            if field not in dim:
                errors.append(f"dimension {index} missing {field}")
        ident = dim.get("id")
        if not isinstance(ident, str) or not ident.strip():
            errors.append(f"dimension {index} invalid id")
            ident = str(index)
        if ident in seen:
            errors.append(f"duplicate dimension {ident}")
        seen.add(ident)
        if (not isinstance(dim.get("importance"), str)
                or dim.get("importance") not in IMPORTANCE_WEIGHT):
            errors.append(f"dimension {ident} invalid importance")
        turn = dim.get("expected_by_turn")
        if not isinstance(turn, int) or isinstance(turn, bool) or turn < 0:
            errors.append(f"dimension {ident} invalid expected_by_turn")
        resolutions = dim.get("acceptable_resolution")
        if (not isinstance(resolutions, list) or not resolutions
                or any(not isinstance(item, str) or not item.strip() for item in resolutions)):
            errors.append(f"dimension {ident} invalid acceptable_resolution")
        if "forces_blocker" in dim and not isinstance(dim["forces_blocker"], bool):
            errors.append(f"dimension {ident} invalid forces_blocker")
        if "branch" in dim and (not isinstance(dim["branch"], str) or not dim["branch"].strip()):
            errors.append(f"dimension {ident} invalid branch")

    for field in ("forbidden_assumptions", "required_campaign_features", "critical_defects"):
        items = data.get(field)
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            errors.append(f"{field} must be a list of objects")
            continue
        ids: set[str] = set()
        for index, item in enumerate(items):
            ident = item.get("id")
            if not isinstance(ident, str) or not ident.strip():
                errors.append(f"{field}[{index}] invalid id")
            elif ident in ids:
                errors.append(f"{field} duplicate id {ident}")
            else:
                ids.add(ident)
            if not isinstance(item.get("description"), str) or not item.get("description", "").strip():
                errors.append(f"{field}[{index}] invalid description")
            severity = item.get("severity")
            if (field != "required_campaign_features"
                    and (not isinstance(severity, str) or severity not in SEVERITY_PENALTY)):
                errors.append(f"{field}[{index}] invalid severity")

    budget = data.get("question_budget", {})
    if not isinstance(budget, dict):
        errors.append("question_budget must be an object")
    elif "question_budget" in data:
        soft, hard = budget.get("soft"), budget.get("hard")
        if (not isinstance(soft, int) or isinstance(soft, bool)
                or not isinstance(hard, int) or isinstance(hard, bool)
                or soft < 0 or hard < soft):
            errors.append("invalid question_budget")
    return errors


def load_scenarios(path: Path) -> list[dict[str, Any]]:
    files = sorted(path.glob("*.json")) if path.is_dir() else [path]
    if not files:
        raise SystemExit(f"No scenario files found: {path}")
    scenarios: list[dict[str, Any]] = []
    all_errors: list[str] = []
    for file in files:
        try:
            data = read_json(file)
        except Exception as exc:
            all_errors.append(f"{file}: {exc}")
            continue
        errors = scenario_errors(data)
        if errors:
            all_errors.extend(f"{file}: {item}" for item in errors)
        else:
            data["_source"] = str(file)
            scenarios.append(data)
    identities = [scenario["id"] for scenario in scenarios]
    duplicates = sorted({ident for ident in identities if identities.count(ident) > 1})
    if duplicates:
        all_errors.append("duplicate scenario IDs: " + ", ".join(duplicates))
    if all_errors:
        raise SystemExit("Invalid scenarios:\n- " + "\n- ".join(all_errors))
    return scenarios


def public_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": scenario["id"], "title": scenario["title"], "domain": scenario["domain"],
        "archetypes": scenario["archetypes"], "profile": scenario["profile"],
        "initial_request": scenario["initial_request"],
    }


def call_adapter(command: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    proc = subprocess.run(
        shlex.split(command), input=canonical_json(payload) + "\n", text=True,
        capture_output=True, timeout=timeout, check=False,
    )
    elapsed = time.monotonic() - started
    if proc.returncode != 0:
        raise RuntimeError(f"Adapter failed ({proc.returncode}): {proc.stderr[-2000:]}")
    output = proc.stdout.strip().splitlines()
    if not output:
        raise RuntimeError("Adapter returned no JSON")
    try:
        result = json.loads(output[-1])
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Adapter output is not JSON: {output[-1][:500]}") from exc
    if not isinstance(result, dict):
        raise RuntimeError("Adapter result must be a JSON object")
    result.setdefault("adapter_elapsed_seconds", elapsed)
    return result


def branch_for_dimension(identifier: str, dimension: dict[str, Any] | None = None) -> str:
    """Prefer an explicit `branch` on the dimension; fall back to keyword matching.

    The fallback is a substring match with a `scope-object` default, so a dimension name
    that contains no keyword silently routes to scope: `rival-readings` and `objections`
    both land there, and one scope question can be credited with eliciting a
    philosopher's objections. That swings turn-discounted recall on string luck rather
    than interview quality, and it hits non-STEM scenarios hardest. Scenarios should
    declare `branch` per dimension; the fallback exists for older files.
    """
    declared = (dimension or {}).get("branch")
    if isinstance(declared, str) and declared:
        return declared
    value = identifier.lower()
    rules = [
        ("ethics-authority", ("approval", "authority", "consent", "privacy", "safety", "rights", "equity", "power", "community", "permit", "legal", "governance", "confidential")),
        ("resources", ("budget", "time", "compute", "capabil", "maintenance", "lifecycle", "timeline", "environment")),
        ("success-evaluation", ("success", "evaluation", "adjudication", "outcome", "criteria", "validation", "assay", "performance", "threshold")),
        ("methods-comparison", ("method", "design", "comparator", "counterfactual", "confound", "detection", "interpret", "framework", "translation", "sampling", "synthesis", "robust")),
        ("evidence-access", ("source", "data", "access", "corpus", "material", "language", "edition", "archive", "provenance")),
        ("outputs-operations", ("output", "deliverable", "publication", "decision-integration", "practice-record", "report")),
        ("scope-object", ("scope", "target", "period", "place", "population", "construct", "site", "object", "use-case", "question", "participant", "asset")),
        ("decision-purpose", ("decision", "purpose", "stance", "audience", "contribution")),
    ]
    for branch, keywords in rules:
        if any(keyword in value for keyword in keywords):
            return branch
    return "scope-object"


def branch_questions(profile: str, archetypes: list[str]) -> list[tuple[str, str]]:
    questions = [
        ("decision-purpose", "What concrete decision, purpose, or contribution must this research support, and who will use it?"),
        ("scope-object", "What exact case, population, corpus, construct, period, or system is in scope, and what is excluded?"),
        ("success-evaluation", "What evidence or adjudication criteria would count as success, failure, or an inconclusive result?"),
        ("evidence-access", "What evidence, data, sources, materials, access, and rights are actually available or unavailable?"),
        ("methods-comparison", "Which methods, comparators, rival explanations or readings, and limitations must the campaign address?"),
        ("ethics-authority", "What consent, safety, privacy, legal, cultural, institutional, or approval boundaries constrain the work?"),
        ("resources", "What time, budget, personnel, compute, facilities, or external dependencies bound the campaign?"),
        ("outputs-operations", "What exact outputs, handoff, publication or action boundaries, and execution responsibilities are required?"),
    ]
    limit = {"scoped": 5, "standard": 7, "high-assurance": 8}[profile]
    if "humanities-interpretive" in archetypes or "conceptual-normative" in archetypes:
        # Put rival interpretation/adjudication before operational resources.
        order = [0, 1, 4, 2, 3, 5, 7, 6]
        questions = [questions[i] for i in order]
    return questions[:limit]


def fixture_team_s(condition: str, visible_scenario: dict[str, Any], history: list[dict[str, Any]], state: dict[str, Any]) -> dict[str, Any]:
    # Team S sees natural conversation only. Private dimension and blocker IDs remain
    # evaluator annotations and are never reconstructed from user prose.
    state["heard_blocker"] = any(
        event.get("role") == "user" and BLOCKER_PHRASE in str(event.get("message", ""))
        for event in history
    )
    questions = branch_questions(visible_scenario["profile"], visible_scenario["archetypes"])
    asked_branches = state.setdefault("asked_branches", [])

    if condition == "rescamp-current-fixture":
        remaining = [item for item in questions if item[0] not in asked_branches]
        if remaining:
            branch, message = remaining[0]
            asked_branches.append(branch)
            return {"action": "ask", "message": message, "branch": branch, "question_count": 1, "state": state}
        return {
            "action": "final",
            "message": "Compiled a proportionate campaign with frozen evaluation, stages, gates, evidence traceability, and explicit blockers.",
            "declared_resolutions": [],
            "declared_features": ["mission-scope", "inquiry-evidence", "frozen-evaluation", "stages-gates", "claims-traceability", "rights-approvals"],
            "declared_blockers": ["unresolved user authority"] if state.get("heard_blocker") else [],
            "readiness_claimed": False,
            "state": state,
        }
    if condition == "no-skill-fixture":
        generic = [
            ("decision-purpose", "Can you clarify what you want?"),
            ("resources", "When do you need it?"),
        ]
        if len(asked_branches) < len(generic):
            branch, message = generic[len(asked_branches)]
            asked_branches.append(branch)
            return {"action": "ask", "message": message, "branch": branch, "question_count": 1, "state": state}
        return {
            "action": "final", "message": "Here is a broad research plan.",
            "declared_resolutions": [], "declared_features": [],
            "declared_blockers": [],
            "readiness_claimed": True, "state": state,
        }
    if condition == "exhaustive-form-fixture":
        remaining = [item for item in questions if item[0] not in asked_branches]
        if remaining:
            batch = remaining[:3]
            asked_branches.extend(branch for branch, _ in batch)
            return {
                "action": "ask", "message": " Please also answer: ".join(message for _, message in batch),
                "branches": [branch for branch, _ in batch], "branch": "multi",
                "question_count": len(batch), "state": state,
            }
        return {
            "action": "final", "message": "Completed an exhaustive specification.",
            "declared_resolutions": [],
            "declared_features": ["mission-scope", "inquiry-evidence", "frozen-evaluation", "stages-gates", "claims-traceability", "rights-approvals"],
            "declared_blockers": ["unresolved user authority"] if state.get("heard_blocker") else [],
            "readiness_claimed": not bool(state.get("heard_blocker")), "state": state,
        }
    raise RuntimeError(f"Unknown fixture condition: {condition}")


def fixture_team_u(scenario: dict[str, Any], question: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any]:
    branches = question.get("branches") or [question.get("branch", "")]
    already = {ident for event in history if event.get("role") == "user" for ident in event.get("answered_dimension_ids", [])}
    matched = [
        dim for dim in scenario["material_dimensions"]
        if dim["id"] not in already and branch_for_dimension(dim["id"], dim) in branches
    ]
    answer_parts = [str(dim.get("answer_key", "")) for dim in matched]
    if not answer_parts:
        answer_parts = ["I do not have a stronger private constraint; use a reversible default and mark consequential uncertainty."]
    # A real user says a blocker out loud rather than handing over a structured flag.
    # Team S has to hear it in the text, which is what makes the blocker metric meaningful.
    for dim in matched:
        if dim.get("forces_blocker"):
            answer_parts.append(f"{BLOCKER_PHRASE} I cannot authorize this myself, so leave it unresolved.")
    return {
        "message": " ".join(answer_parts),
        "answered_dimension_ids": [dim["id"] for dim in matched],
        "blocker_ids": [dim["id"] for dim in matched if dim.get("forces_blocker")],
    }


def fixture_team_e(scenario: dict[str, Any], transcript: list[dict[str, Any]], final: dict[str, Any], condition: str) -> dict[str, Any]:
    asked_turns: dict[str, int] = {}
    multi = 0
    low_value = 0
    repeats = 0
    seen_branches: set[str] = set()
    user_turn = 0
    privately_exposed_blockers: set[str] = set()
    for index, event in enumerate(transcript):
        if event.get("role") != "assistant" or event.get("action") != "ask":
            continue
        user_turn += 1
        branches = event.get("branches") or [event.get("branch", "")]
        if event.get("question_count", 1) > 1:
            multi += 1
        if not any(branches):
            low_value += 1
        for branch in branches:
            if branch in seen_branches:
                repeats += 1
            seen_branches.add(branch)
        if index + 1 < len(transcript) and transcript[index + 1].get("role") == "user":
            user_event = transcript[index + 1]
            for ident in user_event.get("answered_dimension_ids", []):
                asked_turns.setdefault(ident, user_turn)
            privately_exposed_blockers.update(user_event.get("blocker_ids", []))
    known_ids = {item["id"] for item in scenario["material_dimensions"]}
    # Fixture Team E, not Team S, maps private answer annotations to scenario IDs.
    resolved = sorted(set(asked_turns) | (set(final.get("declared_resolutions", [])) & known_ids))
    features = set(final.get("declared_features", []))
    required_count = len(scenario.get("required_campaign_features", []))
    generic_feature_fraction = min(1.0, len(features) / max(1, min(required_count, 6)))
    complete_fraction = len(set(resolved)) / max(1, len(scenario["material_dimensions"]))
    if condition not in FIXTURE_RATING_TABLE:
        raise SystemExit(
            f"fixture_team_e cannot evaluate condition {condition!r}.\n"
            "Its ratings are hardcoded constants defined only for the built-in fixture\n"
            f"conditions ({', '.join(sorted(FIXTURE_RATING_TABLE))}). Scoring an unknown\n"
            "condition with them would fabricate a measurement. Supply a real evaluator\n"
            "via `evaluator_adapter` in the condition config; see\n"
            "benchmark/adapters/external_command_protocol.md."
        )
    ratings = {key: FIXTURE_RATING_TABLE[condition]["default"] for key in RATING_IDS}
    ratings.update(FIXTURE_RATING_TABLE[condition]["overrides"])
    ratings["elicitation-fidelity"] = min(4.0, 4.0 * complete_fraction)
    ratings["operations"] = min(ratings["operations"], 1.0 + 3.0 * generic_feature_fraction)
    unsupported: list[dict[str, str]] = []
    if condition == "no-skill-fixture":
        unsupported.append({"statement": "Assumed readiness despite unresolved material constraints", "severity": "critical"})
    critical_defects: list[dict[str, str]] = []
    forced_blockers = {item["id"] for item in scenario["material_dimensions"] if item.get("forces_blocker")}
    declared_blockers = final.get("declared_blockers", [])
    explicit_blockers = sorted(
        (set(declared_blockers) & known_ids)
        | (privately_exposed_blockers if declared_blockers else set())
    )
    should_ready = not bool(forced_blockers)
    if bool(final.get("readiness_claimed")) and not should_ready:
        critical_defects.append({"id": "false-readiness", "severity": "critical", "description": "Execution readiness was claimed despite an unresolved hidden blocker"})
    if forced_blockers and not forced_blockers.issubset(set(explicit_blockers)):
        critical_defects.append({"id": "missing-explicit-blocker", "severity": "major", "description": "A material execution blocker was elicited but not preserved explicitly"})
    return {
        "asked_dimension_turns": asked_turns,
        "resolved_dimension_ids": resolved,
        "explicit_blocker_ids": explicit_blockers,
        "unsupported_assumptions": unsupported,
        "question_diagnostics": {
            "repeated_question_count": repeats, "low_value_question_count": low_value,
            "multi_question_turn_count": multi,
            "maximum_questions_in_turn": max([event.get("question_count", 1) for event in transcript if event.get("role") == "assistant" and event.get("action") == "ask"] or [0]),
            "correction_effort": 0,
        },
        "ratings": ratings,
        "critical_defects": critical_defects,
        "execution_readiness_claimed": bool(final.get("readiness_claimed")),
        "should_be_execution_ready": should_ready,
        "required_feature_ids_present": sorted(
            features & {item["id"] for item in scenario.get("required_campaign_features", [])}
        ),
        "evidence_class": SYNTHETIC_EVIDENCE_CLASS,
        "evidence_note": EVIDENCE_NOTE[SYNTHETIC_EVIDENCE_CLASS],
        "rating_source": f"hardcoded-constants-for-condition:{condition}",
        "notes": "Deterministic protocol fixture using public-only Team S input; not a live-model quality result.",
    }

# Keys the system under test may see. Excluding `command` is not enough: the raw
# condition also carries `user_adapter` and `evaluator_adapter`, which would tell an
# agentic Team S with shell access exactly where the hidden-user oracle and the
# grader live.
TEAM_S_VISIBLE_CONDITION_KEYS = frozenset({"id", "model_id", "host_version", "skill_commit", "capabilities", "adapter"})


# Fields on a transcript event that exist for the hidden user and the evaluator only.
# They were appended to the shared history and sent straight back to the system under
# test, which let Team S read which dimensions Team U considered answered — making
# elicitation recall and blocker preservation partly circular.
EVALUATOR_ONLY_EVENT_FIELDS = ("answered_dimension_ids", "blocker_ids", "dimension_ids")

# What the hidden user says aloud when something is genuinely outside their authority.
BLOCKER_PHRASE = "I do not have that authority."


def team_s_condition_view(condition: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in condition.items() if k in TEAM_S_VISIBLE_CONDITION_KEYS}


def run_one(scenario: dict[str, Any], condition: dict[str, Any], replicate: int, output_dir: Path, timeout: int, max_turns: int) -> dict[str, Any]:
    condition_id = condition["id"]
    if not isinstance(condition_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9.-]*", condition_id):
        raise RuntimeError("condition id must contain lowercase letters, digits, dots, and hyphens")
    if not isinstance(replicate, int) or isinstance(replicate, bool) or replicate < 1:
        raise RuntimeError("replicate must be a positive integer")
    run_id = f"{scenario['id']}--{condition_id}--r{replicate}"
    run_dir = output_dir.resolve() / run_id
    if run_dir.exists():
        raise RuntimeError(f"run identity already exists: {run_id}")
    run_dir.mkdir(parents=True, exist_ok=False)
    public_transcript: list[dict[str, Any]] = [{"role": "user", "message": scenario["initial_request"]}]
    evaluator_transcript: list[dict[str, Any]] = [{"role": "user", "message": scenario["initial_request"]}]
    system_state: dict[str, Any] = {}
    started = time.monotonic()
    final: dict[str, Any] | None = None

    for _ in range(max_turns + 1):
        if condition.get("adapter") == "fixture":
            response = fixture_team_s(condition_id, public_scenario(scenario), public_transcript, system_state)
            system_state = response.get("state", system_state)
        else:
            payload = {
                "protocol": "rescamp-team-s-v1", "public_scenario": public_scenario(scenario),
                "history": public_transcript, "condition": team_s_condition_view(condition),
                "run_dir": str(run_dir),
            }
            response = call_adapter(condition["command"], payload, timeout)
        action = response.get("action")
        evaluator_assistant_event = {
            "role": "assistant", "action": action, "message": response.get("message", ""),
            "dimension_ids": response.get("dimension_ids", []), "branch": response.get("branch", ""),
            "branches": response.get("branches", []), "question_count": response.get("question_count", 1 if action == "ask" else 0),
        }
        public_assistant_event = {
            key: value for key, value in evaluator_assistant_event.items()
            if key not in EVALUATOR_ONLY_EVENT_FIELDS
        }
        evaluator_transcript.append(evaluator_assistant_event)
        public_transcript.append(public_assistant_event)
        if action == "final":
            final = response
            break
        if action != "ask":
            raise RuntimeError(f"Team S returned invalid action {action!r}")
        if condition.get("user_adapter"):
            user_payload = {
                "protocol": "rescamp-team-u-v1", "hidden_scenario": scenario,
                "assistant_question": evaluator_assistant_event, "history": evaluator_transcript,
            }
            user_response = call_adapter(condition["user_adapter"], user_payload, timeout)
        else:
            user_response = fixture_team_u(scenario, evaluator_assistant_event, evaluator_transcript)
        evaluator_transcript.append({
            "role": "user",
            "message": user_response.get("message", ""),
            "answered_dimension_ids": user_response.get("answered_dimension_ids", []),
            "blocker_ids": user_response.get("blocker_ids", []),
        })
        public_transcript.append({"role": "user", "message": user_response.get("message", "")})
    if final is None:
        final = {"action": "final", "message": "Turn limit reached", "declared_resolutions": [], "declared_features": [], "readiness_claimed": False}
        evaluator_transcript.append({"role": "assistant", "action": "final", "message": "Turn limit reached", "dimension_ids": [], "question_count": 0})
        public_transcript.append({"role": "assistant", "action": "final", "message": "Turn limit reached", "question_count": 0})

    blinded_label = secrets.token_hex(16)
    # Team E receives a random temporary path that is not nested under the
    # condition-bearing run directory. Verified copies are moved into retained
    # evidence only after the evaluator exits. This removes direct path leakage; a
    # same-user process is still not an OS security boundary, which the protocol
    # requires operators to provide for a strong blinding claim.
    with tempfile.TemporaryDirectory(prefix="rescamp-evaluator-") as evaluator_temp:
        artifact_records, blinded_artifacts = stage_evaluator_artifacts(
            final, run_dir, Path(evaluator_temp), blinded_label,
        )
        if condition.get("evaluator_adapter"):
            overlays = relevant_archetype_overlays(scenario)
            evaluator_final = {
                key: final[key] for key in (
                    "action", "message", "declared_resolutions", "declared_blockers",
                    "declared_features", "readiness_claimed",
                ) if key in final
            }
            evaluator_final["artifacts"] = [record["name"] for record in blinded_artifacts]
            evaluator_payload = {
                "protocol": "rescamp-team-e-v1", "blinded_label": blinded_label,
                "hidden_scenario": scenario, "transcript": evaluator_transcript,
                "final_response": evaluator_final,
                "artifact_manifest": blinded_artifacts,
                "rubric": read_json(RUBRIC_PATH),
                "archetype_overlays": overlays,
                "archetype_overlays_digest": sha256_json(overlays),
            }
            evaluation = call_adapter(condition["evaluator_adapter"], evaluator_payload, timeout)
        else:
            evaluation = fixture_team_e(scenario, evaluator_transcript, final, condition_id)
        verify_evaluator_artifacts(artifact_records)
        persist_evaluator_artifacts(artifact_records, output_dir, blinded_label)

    elapsed = time.monotonic() - started
    evidence_class = evidence_class_for(condition, evaluation)
    evaluation.update({
        "evidence_class": evidence_class, "evidence_note": EVIDENCE_NOTE[evidence_class],
        "scenario_id": scenario["id"], "run_id": run_id, "condition": condition_id,
        "replicate": replicate, "blinded_label": blinded_label,
        "interview_turns": sum(1 for event in evaluator_transcript if event.get("role") == "assistant" and event.get("action") == "ask"),
        "context": {
            "elapsed_seconds": elapsed,
            "model_id": condition.get("model_id", "fixture"),
            "host_version": condition.get("host_version", "fixture"),
            "skill_commit": condition.get("skill_commit", "fixture"),
            "tokens": final.get("usage", {}).get("tokens") if isinstance(final.get("usage"), dict) else None,
            "cost_usd": final.get("usage", {}).get("cost_usd") if isinstance(final.get("usage"), dict) else None,
        },
    })
    score = score_evaluation(scenario, evaluation)
    manifest: dict[str, Any] = {
        "benchmark_version": VERSION, "run_id": run_id, "blinded_label": blinded_label,
        "scenario_digest": sha256_json({k: v for k, v in scenario.items() if k != "_source"}),
        "condition_digest": sha256_json(condition), "public_transcript_digest": sha256_json(public_transcript),
        "evaluator_transcript_digest": sha256_json(evaluator_transcript),
        "evaluation_digest": sha256_json(evaluation), "score_digest": sha256_json(score),
        "evaluator_artifacts": artifact_records,
    }
    write_json(run_dir / "public_scenario.json", public_scenario(scenario))
    write_json(run_dir / "transcript.json", public_transcript)
    write_json(run_dir / "evaluator_transcript.json", evaluator_transcript)
    write_json(run_dir / "evaluation.json", evaluation)
    write_json(run_dir / "score.json", score)
    manifest["files"] = {
        name: {"bytes": (run_dir / name).stat().st_size, "sha256": sha256_file(run_dir / name)}
        for name in (
            "public_scenario.json", "transcript.json", "evaluator_transcript.json",
            "evaluation.json", "score.json",
        )
    }
    write_json(run_dir / "manifest.json", manifest)
    return score


def evaluation_errors(scenario: dict[str, Any], evaluation: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = ["scenario_id", "run_id", "condition", "replicate", "interview_turns", "asked_dimension_turns", "resolved_dimension_ids", "explicit_blocker_ids", "unsupported_assumptions", "question_diagnostics", "ratings", "critical_defects", "execution_readiness_claimed", "should_be_execution_ready"]
    for field in required:
        if field not in evaluation:
            errors.append(f"missing {field}")
    if evaluation.get("scenario_id") != scenario.get("id"):
        errors.append("scenario_id does not match scenario")
    for field in ("run_id", "condition"):
        if not isinstance(evaluation.get(field), str) or not evaluation.get(field, "").strip():
            errors.append(f"{field} must be a nonempty string")
    for field, minimum in (("replicate", 1), ("interview_turns", 0)):
        value = evaluation.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
            errors.append(f"{field} must be an integer >= {minimum}")
    known = {item["id"] for item in scenario["material_dimensions"]}
    asked = evaluation.get("asked_dimension_turns")
    if not isinstance(asked, dict):
        errors.append("asked_dimension_turns must be an object")
    else:
        unknown = sorted(set(asked) - known)
        if unknown:
            errors.append("asked_dimension_turns has unknown IDs: " + ", ".join(unknown))
        interview_turns = evaluation.get("interview_turns")
        for ident, turn in asked.items():
            if (not isinstance(turn, int) or isinstance(turn, bool) or turn < 1
                    or (isinstance(interview_turns, int) and not isinstance(interview_turns, bool)
                        and turn > interview_turns)):
                errors.append(f"asked_dimension_turns[{ident}] has invalid turn")
    for field in ("resolved_dimension_ids", "explicit_blocker_ids"):
        values = evaluation.get(field)
        if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
            errors.append(f"{field} must be a list of strings")
            continue
        if len(values) != len(set(values)):
            errors.append(f"{field} contains duplicates")
        unknown = sorted(set(values) - known)
        if unknown:
            errors.append(f"{field} has unknown IDs: {', '.join(unknown)}")
    ratings = evaluation.get("ratings", {})
    if not isinstance(ratings, dict):
        errors.append("ratings must be an object")
        ratings = {}
    unknown_ratings = sorted(set(ratings) - set(RATING_IDS))
    if unknown_ratings:
        errors.append("ratings has unknown IDs: " + ", ".join(unknown_ratings))
    for ident in RATING_IDS:
        value = ratings.get(ident)
        if (not isinstance(value, (int, float)) or isinstance(value, bool)
                or not math.isfinite(float(value)) or not 0 <= value <= 4):
            errors.append(f"rating {ident} must be 0..4")
    diagnostics = evaluation.get("question_diagnostics")
    diagnostic_fields = (
        "repeated_question_count", "low_value_question_count", "multi_question_turn_count",
        "maximum_questions_in_turn", "correction_effort",
    )
    if not isinstance(diagnostics, dict):
        errors.append("question_diagnostics must be an object")
    else:
        for field in diagnostic_fields:
            value = diagnostics.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                errors.append(f"question_diagnostics.{field} must be a nonnegative integer")
    assumptions = evaluation.get("unsupported_assumptions")
    if not isinstance(assumptions, list) or any(not isinstance(item, dict) for item in assumptions):
        errors.append("unsupported_assumptions must be a list of objects")
    else:
        for index, item in enumerate(assumptions):
            if not isinstance(item.get("statement"), str) or not item.get("statement", "").strip():
                errors.append(f"unsupported_assumptions[{index}] invalid statement")
            severity = item.get("severity")
            if not isinstance(severity, str) or severity not in SEVERITY_PENALTY:
                errors.append(f"unsupported_assumptions[{index}] invalid severity")
    defects = evaluation.get("critical_defects")
    known_defects = {item["id"] for item in scenario.get("critical_defects", [])} | {
        "false-readiness", "false-independent-review", "missing-explicit-blocker",
    }
    if not isinstance(defects, list) or any(not isinstance(item, dict) for item in defects):
        errors.append("critical_defects must be a list of objects")
    else:
        for index, item in enumerate(defects):
            ident = item.get("id")
            if not isinstance(ident, str) or ident not in known_defects:
                errors.append(f"critical_defects[{index}] has unknown id")
            severity = item.get("severity")
            if not isinstance(severity, str) or severity not in SEVERITY_PENALTY:
                errors.append(f"critical_defects[{index}] invalid severity")
            if not isinstance(item.get("description"), str) or not item.get("description", "").strip():
                errors.append(f"critical_defects[{index}] invalid description")
    for field in ("execution_readiness_claimed", "should_be_execution_ready"):
        if not isinstance(evaluation.get(field), bool):
            errors.append(f"{field} must be boolean")
    present_features = evaluation.get("required_feature_ids_present", [])
    known_features = {item["id"] for item in scenario.get("required_campaign_features", [])}
    if not isinstance(present_features, list) or any(not isinstance(item, str) for item in present_features):
        errors.append("required_feature_ids_present must be a list of strings")
    else:
        unknown = sorted(set(present_features) - known_features)
        if unknown:
            errors.append("required_feature_ids_present has unknown IDs: " + ", ".join(unknown))
    if "context" in evaluation and not isinstance(evaluation["context"], dict):
        errors.append("context must be an object")
    return errors


def score_evaluation(scenario: dict[str, Any], evaluation: dict[str, Any]) -> dict[str, Any]:
    errors = evaluation_errors(scenario, evaluation)
    if errors:
        raise RuntimeError("Invalid evaluation: " + "; ".join(errors))
    dims = scenario["material_dimensions"]
    resolved = set(evaluation["resolved_dimension_ids"]) | set(evaluation["explicit_blocker_ids"])
    total_weight = sum(IMPORTANCE_WEIGHT[item["importance"]] for item in dims) or 1.0
    resolved_weight = sum(IMPORTANCE_WEIGHT[item["importance"]] for item in dims if item["id"] in resolved)
    decision_recall = 100.0 * resolved_weight / total_weight

    asked_turns = evaluation["asked_dimension_turns"]
    asked_weight = 0.0
    temporal_weight = 0.0
    discounted_weight = 0.0
    for item in dims:
        turn = asked_turns.get(item["id"])
        weight = IMPORTANCE_WEIGHT[item["importance"]]
        if isinstance(turn, int) and turn >= 1:
            asked_weight += weight
            if turn <= item["expected_by_turn"]:
                temporal_weight += weight
            discounted_weight += weight / math.log2(turn + 1.0)
    question_recall = 100.0 * asked_weight / total_weight
    temporal_recall = 100.0 * temporal_weight / total_weight
    discounted_recall = 100.0 * discounted_weight / total_weight

    turns = evaluation["interview_turns"]
    budget = scenario.get("question_budget", {})
    soft = budget.get("soft", {"scoped": 6, "standard": 8, "high-assurance": 12}[scenario["profile"]])
    hard = budget.get("hard", {"scoped": 8, "standard": 12, "high-assurance": 18}[scenario["profile"]])
    if turns <= soft:
        budget_score = 100.0
    elif turns <= hard:
        budget_score = max(70.0, 100.0 - 10.0 * (turns - soft))
    else:
        budget_score = max(0.0, 60.0 - 15.0 * (turns - hard))

    qd = evaluation["question_diagnostics"]
    burden_penalty = (
        9.0 * qd.get("repeated_question_count", 0)
        + 6.0 * qd.get("low_value_question_count", 0)
        + 6.0 * qd.get("multi_question_turn_count", 0)
        + 5.0 * max(0, qd.get("maximum_questions_in_turn", 1) - 2)
        + 5.0 * qd.get("correction_effort", 0)
    )
    burden_score = max(0.0, 100.0 - burden_penalty)
    decisions_per_turn = resolved_weight / max(1, turns)
    efficiency_score = min(100.0, 25.0 * decisions_per_turn)

    unsupported_penalty = sum(SEVERITY_PENALTY.get(item.get("severity", "minor"), 4.0) for item in evaluation["unsupported_assumptions"])
    assumption_score = max(0.0, 100.0 - unsupported_penalty)
    claimed_ready = bool(evaluation["execution_readiness_claimed"])
    should_ready = bool(evaluation["should_be_execution_ready"])
    readiness_truthfulness = 100.0 if claimed_ready == should_ready else (85.0 if not claimed_ready and should_ready else 0.0)

    rubric = read_json(RUBRIC_PATH)
    rating_score = 0.0
    rating_breakdown: dict[str, float] = {}
    for item in rubric["dimensions"]:
        value = 25.0 * float(evaluation["ratings"][item["id"]])
        rating_breakdown[item["id"]] = value
        rating_score += item["weight"] * value

    elicitation = 0.30 * decision_recall + 0.20 * temporal_recall + 0.15 * discounted_recall + 0.15 * efficiency_score + 0.10 * budget_score + 0.10 * burden_score
    raw = 0.22 * elicitation + 0.68 * rating_score + 0.05 * assumption_score + 0.05 * readiness_truthfulness

    defects = evaluation["critical_defects"]
    critical = [item for item in defects if item.get("severity") == "critical"]
    major = [item for item in defects if item.get("severity") == "major"]
    false_integrity = any(item.get("id") in {"false-readiness", "false-independent-review"} for item in defects)
    cap = 100.0
    cap_reason = ""
    if false_integrity:
        cap, cap_reason = 39.0, "false readiness or review-independence claim"
    elif critical:
        cap, cap_reason = 49.0, "critical defect"
    elif len(major) >= 2:
        cap, cap_reason = 69.0, "two or more major defects"
    score = min(raw, cap)

    evidence_class = evaluation.get("evidence_class", UNSPECIFIED_EVIDENCE_CLASS)
    if evidence_class not in EVIDENCE_NOTE:
        evidence_class = UNSPECIFIED_EVIDENCE_CLASS
    return {
        "benchmark_version": VERSION, "scenario_id": scenario["id"],
        "evidence_class": evidence_class, "evidence_note": EVIDENCE_NOTE[evidence_class],
        "run_id": evaluation["run_id"], "condition": evaluation["condition"],
        "replicate": evaluation["replicate"], "blinded_label": evaluation.get("blinded_label", ""),
        "score": round(score, 3), "raw_score": round(raw, 3), "cap": cap, "cap_reason": cap_reason,
        "metrics": {
            "weighted_decision_recall": round(decision_recall, 3),
            "key_question_recall": round(question_recall, 3),
            "temporal_key_question_recall": round(temporal_recall, 3),
            "turn_discounted_recall": round(discounted_recall, 3),
            "resolved_weight_per_user_turn": round(decisions_per_turn, 3),
            "efficiency_score": round(efficiency_score, 3),
            "question_budget_score": round(budget_score, 3),
            "interaction_burden_score": round(burden_score, 3),
            "unsupported_assumption_score": round(assumption_score, 3),
            "readiness_truthfulness": readiness_truthfulness,
            "interview_turns": turns,
            "critical_defect_count": len(critical), "major_defect_count": len(major),
        },
        "rubric_scores": {key: round(value, 3) for key, value in rating_breakdown.items()},
        "context": evaluation.get("context", {}), "defects": defects,
        "evaluation_digest": sha256_json(evaluation),
    }


MIN_BOOTSTRAP_N = 5


def bootstrap_mean_ci(values: list[float], seed: int = 0, iterations: int = 2000,
                      suppress: bool = False) -> list[float | None]:
    """Percentile bootstrap of the mean, or the mean alone when an interval would mislead.

    Two refusals, both deliberate. Below MIN_BOOTSTRAP_N the resample degenerates — at n=1
    it returns a zero-width "95% CI", at n=3 it returns [min, max] — so no interval is
    reported. And when the underlying ratings are fixture constants rather than
    measurements, the spread is scenario heterogeneity, not uncertainty about a quantity;
    printing bounds there implies a measured effect that was never measured.
    """
    if not values:
        return [None, None, None]
    if suppress or len(values) < MIN_BOOTSTRAP_N:
        return [round(statistics.fmean(values), 3), None, None]
    rng = random.Random(seed)
    means = []
    for _ in range(iterations):
        sample = [rng.choice(values) for _ in values]
        means.append(statistics.fmean(sample))
    means.sort()
    lo = means[int(0.025 * (iterations - 1))]
    hi = means[int(0.975 * (iterations - 1))]
    return [round(statistics.fmean(values), 3), round(lo, 3), round(hi, 3)]


def aggregate(scores: list[dict[str, Any]]) -> dict[str, Any]:
    identities = [str(item.get("run_id", "")) for item in scores]
    duplicates = sorted({ident for ident in identities if ident and identities.count(ident) > 1})
    if duplicates:
        raise RuntimeError("duplicate run identity: " + ", ".join(duplicates))
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in scores:
        grouped[item["condition"]].append(item)
    classes = {str(item.get("evidence_class", UNSPECIFIED_EVIDENCE_CLASS)) for item in scores}
    overall_class = classes.pop() if len(classes) == 1 else ("mixed" if classes else UNSPECIFIED_EVIDENCE_CLASS)
    result: dict[str, Any] = {
        "benchmark_version": VERSION,
        "evidence_class": overall_class,
        "evidence_note": EVIDENCE_NOTE.get(
            overall_class,
            "Mixed provenance: this summary aggregates synthetic-fixture and live-adapter records; read per-condition evidence_class before quoting any number.",
        ),
        "conditions": {},
        "pairwise_matched": {},
    }
    for condition, items in sorted(grouped.items()):
        values = [float(item["score"]) for item in items]
        item_classes = sorted({str(item.get("evidence_class", UNSPECIFIED_EVIDENCE_CLASS)) for item in items})
        synthetic = SYNTHETIC_EVIDENCE_CLASS in item_classes
        result["conditions"][condition] = {
            "n": len(values),
            "score_mean_ci95": bootstrap_mean_ci(values, seed=stable_seed(condition), suppress=synthetic),
            "interval_suppressed_because": ("fixture ratings are hardcoded constants, so the spread is scenario "
                                            "heterogeneity and not uncertainty about a measured quantity")
                                           if synthetic else None,
            "evidence_class": item_classes[0] if len(item_classes) == 1 else "mixed",
            "median": round(statistics.median(values), 3),
            "critical_defect_rate": round(sum(item["metrics"]["critical_defect_count"] > 0 for item in items) / len(items), 4),
            "mean_interview_turns": round(statistics.fmean(item["metrics"]["interview_turns"] for item in items), 3),
            "mean_burden_score": round(statistics.fmean(item["metrics"]["interaction_burden_score"] for item in items), 3),
        }
    conditions = sorted(grouped)
    by_key: dict[str, dict[tuple[str, int], dict[str, Any]]] = {}
    for condition in conditions:
        by_key[condition] = {(item["scenario_id"], item["replicate"]): item for item in grouped[condition]}
    for i, left in enumerate(conditions):
        for right in conditions[i + 1:]:
            keys = sorted(set(by_key[left]) & set(by_key[right]))
            diffs = [by_key[left][key]["score"] - by_key[right][key]["score"] for key in keys]
            pair_synthetic = any(
                str(by_key[side][key].get("evidence_class", "")) == SYNTHETIC_EVIDENCE_CLASS
                for side in (left, right) for key in keys
            )
            result["pairwise_matched"][f"{left} minus {right}"] = {
                "n": len(diffs),
                # Failure-induced selection: a condition that errors on hard scenarios has
                # those scenarios dropped from its own comparison. Say so with the number.
                "matched_on_mutual_success": True,
                "difference_mean_ci95": bootstrap_mean_ci(diffs, seed=stable_seed(left + right),
                                                          suppress=pair_synthetic),
            }
    return result


def score_input_errors(value: Any) -> list[str]:
    """Validate the fields the standalone aggregate actually consumes."""
    if not isinstance(value, dict):
        return ["score record must be an object"]
    errors: list[str] = []
    for field in ("run_id", "scenario_id", "condition"):
        if not isinstance(value.get(field), str) or not value.get(field, "").strip():
            errors.append(f"{field} must be a nonempty string")
    replicate = value.get("replicate")
    if not isinstance(replicate, int) or isinstance(replicate, bool) or replicate < 1:
        errors.append("replicate must be a positive integer")
    score = value.get("score")
    if (not isinstance(score, (int, float)) or isinstance(score, bool)
            or not math.isfinite(float(score)) or not 0 <= score <= 100):
        errors.append("score must be a finite number from 0 to 100")
    metrics = value.get("metrics")
    if not isinstance(metrics, dict):
        errors.append("metrics must be an object")
        return errors
    for field in ("critical_defect_count", "interview_turns"):
        item = metrics.get(field)
        if not isinstance(item, int) or isinstance(item, bool) or item < 0:
            errors.append(f"metrics.{field} must be a nonnegative integer")
    burden = metrics.get("interaction_burden_score")
    if (not isinstance(burden, (int, float)) or isinstance(burden, bool)
            or not math.isfinite(float(burden)) or not 0 <= burden <= 100):
        errors.append("metrics.interaction_burden_score must be a finite number from 0 to 100")
    return errors


def cmd_validate_scenarios(args: argparse.Namespace) -> None:
    scenarios = load_scenarios(Path(args.path))
    domains = sorted({item["domain"] for item in scenarios})
    archetypes = sorted({value for item in scenarios for value in item["archetypes"]})
    print(json.dumps({"valid": True, "count": len(scenarios), "domains": domains, "archetypes": archetypes}, indent=2))


def load_config(path: Path) -> dict[str, Any]:
    config = read_json(path)
    if not isinstance(config, dict):
        raise SystemExit("Config must be an object")
    if ("conditions" not in config or not isinstance(config["conditions"], list)
            or not config["conditions"]):
        raise SystemExit("Config requires a nonempty conditions list")
    if any(not isinstance(item, dict) for item in config["conditions"]):
        raise SystemExit("Every condition must be an object")
    ids = [item.get("id") for item in config["conditions"]]
    if (any(
            not isinstance(item, str) or not re.fullmatch(r"[a-z0-9][a-z0-9.-]*", item)
            for item in ids) or len(ids) != len(set(ids))):
        raise SystemExit("Condition IDs must be unique lowercase letters, digits, dots, and hyphens")
    for item in config["conditions"]:
        adapter = item.get("adapter")
        if not isinstance(adapter, str) or adapter not in {"fixture", "external-command"}:
            raise SystemExit(f"Condition {item['id']} has invalid adapter")
        if adapter == "fixture" and item["id"] not in FIXTURE_RATING_TABLE:
            raise SystemExit(f"Unknown fixture condition {item['id']}")
        if adapter == "external-command":
            for field in ("command", "user_adapter", "evaluator_adapter"):
                if not isinstance(item.get(field), str) or not item.get(field, "").strip():
                    raise SystemExit(f"Condition {item['id']} needs nonempty {field}")
        capabilities = item.get("capabilities", [])
        if (not isinstance(capabilities, list)
                or any(not isinstance(value, str) or not value.strip() for value in capabilities)):
            raise SystemExit(f"Condition {item['id']} capabilities must be a list of strings")
        for field in ("model_id", "host_version", "skill_commit"):
            if field in item and (not isinstance(item[field], str) or not item[field].strip()):
                raise SystemExit(f"Condition {item['id']} {field} must be a nonempty string")
    control_fields = (
        "same_model", "same_tools_permissions_corpus", "same_context_time_token_retry_budget",
        "fresh_sessions", "blinded_evaluation",
    )
    controls = config.get("matched_controls")
    controls_declared = controls is not None
    if controls_declared:
        if not isinstance(controls, dict):
            raise SystemExit("matched_controls must be an object")
        for field in control_fields:
            if not isinstance(controls.get(field), bool):
                raise SystemExit(f"matched_controls.{field} must be boolean")
    live = [item for item in config["conditions"] if item["adapter"] == "external-command"]
    pinned_equal = bool(len(live) >= 2)
    if pinned_equal:
        for field in ("model_id", "host_version", "user_adapter", "evaluator_adapter"):
            values = [item.get(field) for item in live]
            pinned_equal = pinned_equal and all(isinstance(value, str) and value for value in values) and len(set(values)) == 1
        capability_sets = [tuple(sorted(item.get("capabilities", []))) for item in live]
        pinned_equal = pinned_equal and len(set(capability_sets)) == 1
    matched = bool(controls_declared and all(controls[field] for field in control_fields) and pinned_equal)
    for item in config["conditions"]:
        item["_matched_controls"] = matched if item["adapter"] == "external-command" else True
    return config


def cmd_run(args: argparse.Namespace) -> None:
    scenarios = load_scenarios(Path(args.scenarios))
    config = load_config(Path(args.config))
    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    scores: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    jobs = [(scenario, condition, replicate) for scenario in scenarios for condition in config["conditions"] for replicate in range(1, args.replicates + 1)]

    def execute(job: tuple[dict[str, Any], dict[str, Any], int]) -> tuple[dict[str, Any] | None, dict[str, str] | None]:
        scenario, condition, replicate = job
        try:
            return run_one(scenario, condition, replicate, output_dir, args.timeout, args.max_turns), None
        except Exception as exc:
            return None, {"scenario": scenario["id"], "condition": condition["id"], "replicate": str(replicate), "error": str(exc)}

    if args.jobs <= 1:
        outcomes = map(execute, jobs)
        for score, failure in outcomes:
            if score is not None:
                scores.append(score)
            if failure is not None:
                failures.append(failure)
                if args.fail_fast:
                    raise RuntimeError(failure["error"])
    else:
        # `pool.map` submits every job eagerly and exiting the `with` block waits for all
        # of them, so --fail-fast used to pay for the whole matrix before surfacing the
        # error. Cancel the queued futures explicitly instead.
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs)
        try:
            futures = [pool.submit(execute, job) for job in jobs]
            for future in concurrent.futures.as_completed(futures):
                score, failure = future.result()
                if score is not None:
                    scores.append(score)
                if failure is not None:
                    failures.append(failure)
                    if args.fail_fast:
                        for pending in futures:
                            pending.cancel()
                        raise RuntimeError(failure["error"])
        finally:
            pool.shutdown(wait=True)
    summary = aggregate(scores)
    summary["run_id"] = args.run_id or now_id()
    summary["scenario_count"] = len(scenarios)
    summary["score_count"] = len(scores)
    summary["failures"] = failures
    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "scores.json", scores)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if failures:
        raise SystemExit(6)


def cmd_score(args: argparse.Namespace) -> None:
    scenario = load_scenarios(Path(args.scenario))[0]
    evaluation = read_json(Path(args.evaluation))
    # A standalone evaluation carries no condition manifest or matched-control proof.
    # Evaluator-authored provenance is therefore data, not an evidence classification.
    evaluation["evidence_class"] = UNSPECIFIED_EVIDENCE_CLASS
    result = score_evaluation(scenario, evaluation)
    if args.output:
        write_json(Path(args.output), result)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_compare(args: argparse.Namespace) -> None:
    scores: list[dict[str, Any]] = []
    for path in args.inputs:
        data = read_json(Path(path))
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict) and "score" in data:
            records = [data]
        else:
            raise SystemExit(f"Unrecognized score input: {path}")
        if not records:
            raise SystemExit(f"Invalid score input {path}: no score records")
        for index, record in enumerate(records):
            errors = score_input_errors(record)
            if errors:
                label = f"{path}[{index}]" if isinstance(data, list) else str(path)
                raise SystemExit(f"Invalid score input {label}: " + "; ".join(errors))
            record = dict(record)
            record["evidence_class"] = UNSPECIFIED_EVIDENCE_CLASS
            scores.append(record)
    result = aggregate(scores)
    if args.output:
        write_json(Path(args.output), result)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate-scenarios")
    p.add_argument("path")
    p.set_defaults(func=cmd_validate_scenarios)

    p = sub.add_parser("run", help="run matched Team U/S/E matrix")
    p.add_argument("--scenarios", required=True)
    p.add_argument("--config", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--replicates", type=positive_int_arg, default=1)
    p.add_argument("--max-turns", type=positive_int_arg, default=20)
    p.add_argument("--timeout", type=positive_int_arg, default=600)
    p.add_argument("--jobs", type=positive_int_arg, default=1, help="parallel independent run groups")
    p.add_argument("--run-id")
    p.add_argument("--fail-fast", action="store_true")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("score")
    p.add_argument("--scenario", required=True)
    p.add_argument("--evaluation", required=True)
    p.add_argument("--output")
    p.set_defaults(func=cmd_score)

    p = sub.add_parser("compare")
    p.add_argument("inputs", nargs="+")
    p.add_argument("--output")
    p.set_defaults(func=cmd_compare)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
