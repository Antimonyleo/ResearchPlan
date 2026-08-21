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
import shlex
import statistics
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

VERSION = "0.8.5"
SKILL_DIR = Path(__file__).resolve().parent.parent
RUBRIC_PATH = SKILL_DIR / "assets" / "universal_rubric.json"
IMPORTANCE_WEIGHT = {"low": 1.0, "material": 2.0, "critical": 4.0}
SEVERITY_PENALTY = {"minor": 4.0, "major": 14.0, "critical": 40.0}
RATING_IDS = [item["id"] for item in json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))["dimensions"]]

# Hardcoded ratings for the built-in fixture conditions only. These are constants
# that exercise the harness, not measurements. Any condition absent from this table
# is refused rather than scored, so plugging in a real Team S without a real Team E
# fails loudly instead of producing a fabricated number with a confident CI.
FIXTURE_RATING_TABLE: dict[str, dict[str, Any]] = {
    "rescamp-0.8-fixture": {"default": 3.3, "overrides": {"interview-efficiency": 3.6, "proportionality-usability": 3.7}},
    "exhaustive-form-fixture": {"default": 3.0, "overrides": {"interview-efficiency": 1.4, "proportionality-usability": 1.7}},
    "no-skill-fixture": {"default": 1.4, "overrides": {"mission-scope": 1.8}},
}

SYNTHETIC_EVIDENCE_CLASS = "synthetic-fixture"
LIVE_EVIDENCE_CLASS = "live-adapter"
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
    UNSPECIFIED_EVIDENCE_CLASS: (
        "Provenance not declared by the producing evaluation; do not treat as a measurement without checking "
        "which adapters produced it."
    ),
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


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
    if declared in EVIDENCE_NOTE:
        return declared
    return LIVE_EVIDENCE_CLASS


def now_id() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def scenario_errors(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = ["id", "title", "domain", "archetypes", "profile", "initial_request", "hidden_brief", "material_dimensions", "forbidden_assumptions", "required_campaign_features", "critical_defects"]
    for field in required:
        if field not in data:
            errors.append(f"missing {field}")
    if data.get("profile") not in {"scoped", "standard", "high-assurance"}:
        errors.append("invalid profile")
    dims = data.get("material_dimensions", [])
    seen: set[str] = set()
    for index, dim in enumerate(dims):
        for field in ("id", "importance", "expected_by_turn", "acceptable_resolution"):
            if field not in dim:
                errors.append(f"dimension {index} missing {field}")
        ident = str(dim.get("id", ""))
        if ident in seen:
            errors.append(f"duplicate dimension {ident}")
        seen.add(ident)
        if dim.get("importance") not in IMPORTANCE_WEIGHT:
            errors.append(f"dimension {ident} invalid importance")
        if not isinstance(dim.get("expected_by_turn"), int) or dim.get("expected_by_turn", -1) < 0:
            errors.append(f"dimension {ident} invalid expected_by_turn")
    budget = data.get("question_budget", {})
    if budget:
        soft, hard = budget.get("soft"), budget.get("hard")
        if not isinstance(soft, int) or not isinstance(hard, int) or soft < 0 or hard < soft:
            errors.append("invalid question_budget")
    return errors


def load_scenarios(path: Path) -> list[dict[str, Any]]:
    files = sorted(path.glob("*.json")) if path.is_dir() else [path]
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
    answered: list[str] = []
    blockers: list[str] = []
    for event in history:
        if event.get("role") == "user":
            answered.extend(event.get("answered_dimension_ids", []))
            blockers.extend(event.get("blocker_ids", []))
    state["answered_ids"] = sorted(set(answered))
    state["blocker_ids"] = sorted(set(blockers))
    questions = branch_questions(visible_scenario["profile"], visible_scenario["archetypes"])
    asked_branches = state.setdefault("asked_branches", [])

    if condition == "rescamp-0.8-fixture":
        remaining = [item for item in questions if item[0] not in asked_branches]
        if remaining:
            branch, message = remaining[0]
            asked_branches.append(branch)
            return {"action": "ask", "message": message, "branch": branch, "question_count": 1, "state": state}
        return {
            "action": "final",
            "message": "Compiled a proportionate campaign with frozen evaluation, stages, gates, evidence traceability, and explicit blockers.",
            "declared_resolutions": state.get("answered_ids", []),
            "declared_features": ["mission-scope", "inquiry-evidence", "frozen-evaluation", "stages-gates", "claims-traceability", "rights-approvals"],
            "declared_blockers": state.get("blocker_ids", []),
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
            "declared_resolutions": state.get("answered_ids", []), "declared_features": [],
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
            "declared_resolutions": state.get("answered_ids", []),
            "declared_features": ["mission-scope", "inquiry-evidence", "frozen-evaluation", "stages-gates", "claims-traceability", "rights-approvals"],
            "declared_blockers": state.get("blocker_ids", []),
            "readiness_claimed": not bool(state.get("blocker_ids")), "state": state,
        }
    raise RuntimeError(f"Unknown fixture condition: {condition}")


def fixture_team_u(scenario: dict[str, Any], question: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any]:
    branches = question.get("branches") or [question.get("branch", "")]
    already = {ident for event in history if event.get("role") == "user" for ident in event.get("answered_dimension_ids", [])}
    matched = [
        dim for dim in scenario["material_dimensions"]
        if dim["id"] not in already and branch_for_dimension(dim["id"], dim) in branches
    ]
    answer_parts = [f"{dim['id']}: {json.dumps(dim.get('answer_key'), ensure_ascii=False)}" for dim in matched]
    if not answer_parts:
        answer_parts = ["I do not have a stronger private constraint; use a reversible default and mark consequential uncertainty."]
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
            for ident in transcript[index + 1].get("answered_dimension_ids", []):
                asked_turns.setdefault(ident, user_turn)
    resolved = list(final.get("declared_resolutions", []))
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
    explicit_blockers = sorted(set(final.get("declared_blockers", [])) & {item["id"] for item in scenario["material_dimensions"]})
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
        "required_feature_ids_present": sorted(features),
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


def team_s_condition_view(condition: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in condition.items() if k in TEAM_S_VISIBLE_CONDITION_KEYS}


def run_one(scenario: dict[str, Any], condition: dict[str, Any], replicate: int, output_dir: Path, timeout: int, max_turns: int) -> dict[str, Any]:
    condition_id = condition["id"]
    run_id = f"{scenario['id']}--{condition_id}--r{replicate}"
    run_dir = output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    history: list[dict[str, Any]] = [{"role": "user", "message": scenario["initial_request"]}]
    system_state: dict[str, Any] = {}
    started = time.monotonic()
    final: dict[str, Any] | None = None

    for _ in range(max_turns + 1):
        if condition.get("adapter") == "fixture":
            response = fixture_team_s(condition_id, public_scenario(scenario), history, system_state)
            system_state = response.get("state", system_state)
        else:
            payload = {
                "protocol": "rescamp-team-s-v1", "public_scenario": public_scenario(scenario),
                "history": history, "condition": team_s_condition_view(condition),
                "run_dir": str(run_dir),
            }
            response = call_adapter(condition["command"], payload, timeout)
        action = response.get("action")
        assistant_event = {
            "role": "assistant", "action": action, "message": response.get("message", ""),
            "dimension_ids": response.get("dimension_ids", []), "branch": response.get("branch", ""),
            "branches": response.get("branches", []), "question_count": response.get("question_count", 1 if action == "ask" else 0),
        }
        history.append(assistant_event)
        if action == "final":
            final = response
            break
        if action != "ask":
            raise RuntimeError(f"Team S returned invalid action {action!r}")
        if condition.get("user_adapter"):
            user_payload = {
                "protocol": "rescamp-team-u-v1", "hidden_scenario": scenario,
                "assistant_question": assistant_event, "history": history,
            }
            user_response = call_adapter(condition["user_adapter"], user_payload, timeout)
        else:
            user_response = fixture_team_u(scenario, assistant_event, history)
        history.append({
            "role": "user",
            "message": user_response.get("message", ""),
            "answered_dimension_ids": user_response.get("answered_dimension_ids", []),
            "blocker_ids": user_response.get("blocker_ids", []),
        })
    if final is None:
        final = {"action": "final", "message": "Turn limit reached", "declared_resolutions": [], "declared_features": [], "readiness_claimed": False}
        history.append({"role": "assistant", "action": "final", "message": "Turn limit reached", "dimension_ids": [], "question_count": 0})

    blinded_label = hashlib.sha256(run_id.encode("utf-8")).hexdigest()[:12]
    if condition.get("evaluator_adapter"):
        evaluator_payload = {
            "protocol": "rescamp-team-e-v1", "blinded_label": blinded_label,
            "hidden_scenario": scenario, "transcript": history,
            "final_response": {k: v for k, v in final.items() if k != "state"},
            "rubric": read_json(RUBRIC_PATH),
        }
        evaluation = call_adapter(condition["evaluator_adapter"], evaluator_payload, timeout)
    else:
        evaluation = fixture_team_e(scenario, history, final, condition_id)

    elapsed = time.monotonic() - started
    evidence_class = evidence_class_for(condition, evaluation)
    evaluation.update({
        "evidence_class": evidence_class, "evidence_note": EVIDENCE_NOTE[evidence_class],
        "scenario_id": scenario["id"], "run_id": run_id, "condition": condition_id,
        "replicate": replicate, "blinded_label": blinded_label,
        "interview_turns": sum(1 for event in history if event.get("role") == "assistant" and event.get("action") == "ask"),
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
    manifest = {
        "benchmark_version": VERSION, "run_id": run_id, "blinded_label": blinded_label,
        "scenario_digest": sha256_json({k: v for k, v in scenario.items() if k != "_source"}),
        "condition_digest": sha256_json(condition), "transcript_digest": sha256_json(history),
        "evaluation_digest": sha256_json(evaluation), "score_digest": sha256_json(score),
    }
    write_json(run_dir / "public_scenario.json", public_scenario(scenario))
    write_json(run_dir / "transcript.json", history)
    write_json(run_dir / "evaluation.json", evaluation)
    write_json(run_dir / "score.json", score)
    write_json(run_dir / "manifest.json", manifest)
    return score


def evaluation_errors(scenario: dict[str, Any], evaluation: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = ["scenario_id", "run_id", "condition", "replicate", "interview_turns", "asked_dimension_turns", "resolved_dimension_ids", "explicit_blocker_ids", "unsupported_assumptions", "question_diagnostics", "ratings", "critical_defects", "execution_readiness_claimed", "should_be_execution_ready"]
    for field in required:
        if field not in evaluation:
            errors.append(f"missing {field}")
    known = {item["id"] for item in scenario["material_dimensions"]}
    for field in ("resolved_dimension_ids", "explicit_blocker_ids"):
        unknown = sorted(set(evaluation.get(field, [])) - known)
        if unknown:
            errors.append(f"{field} has unknown IDs: {', '.join(unknown)}")
    ratings = evaluation.get("ratings", {})
    for ident in RATING_IDS:
        value = ratings.get(ident)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 4:
            errors.append(f"rating {ident} must be 0..4")
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


def cmd_validate_scenarios(args: argparse.Namespace) -> None:
    scenarios = load_scenarios(Path(args.path))
    domains = sorted({item["domain"] for item in scenarios})
    archetypes = sorted({value for item in scenarios for value in item["archetypes"]})
    print(json.dumps({"valid": True, "count": len(scenarios), "domains": domains, "archetypes": archetypes}, indent=2))


def load_config(path: Path) -> dict[str, Any]:
    config = read_json(path)
    if "conditions" not in config or not isinstance(config["conditions"], list):
        raise SystemExit("Config requires conditions list")
    ids = [item.get("id") for item in config["conditions"]]
    if len(ids) != len(set(ids)) or any(not item for item in ids):
        raise SystemExit("Condition IDs must be unique and non-empty")
    for item in config["conditions"]:
        if item.get("adapter") != "fixture" and not item.get("command"):
            raise SystemExit(f"Condition {item['id']} needs adapter=fixture or command")
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
    result = score_evaluation(scenario, evaluation)
    if args.output:
        write_json(Path(args.output), result)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_compare(args: argparse.Namespace) -> None:
    scores: list[dict[str, Any]] = []
    for path in args.inputs:
        data = read_json(Path(path))
        if isinstance(data, list):
            scores.extend(data)
        elif isinstance(data, dict) and "score" in data:
            scores.append(data)
        else:
            raise SystemExit(f"Unrecognized score input: {path}")
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
    p.add_argument("--replicates", type=int, default=1)
    p.add_argument("--max-turns", type=int, default=20)
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--jobs", type=int, default=1, help="parallel independent run groups")
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
