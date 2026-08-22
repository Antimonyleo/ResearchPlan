#!/usr/bin/env python3
"""ResCamp 0.10 durable campaign state, validation, review, and rendering.

The language model conducts research design and synthesis. This dependency-free utility
keeps canonical state, enforces proportional gates, prepares immutable review packets,
and renders auditable artifacts. It intentionally does not call a model or external API.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

VERSION = "0.10.0"
SCHEMA_VERSION = "3.1"
SKILL_DIR = Path(__file__).resolve().parent.parent
STATE_REL = Path("state/campaign.json")
VALIDATION_REL = Path("working/validation.json")
REVIEW_DIR_REL = Path("working/review_packets")
OUTPUT_DIR_REL = Path("outputs")

PROFILES: dict[str, dict[str, Any]] = {
    "scoped": {
        "typical": [3, 5], "soft": 6, "hard": 8,
        "review_roles": ["skeptical"], "independent_required": False,
    },
    "standard": {
        "typical": [4, 8], "soft": 8, "hard": 12,
        "review_roles": ["methods-evidence", "operations-reproducibility"],
        "independent_required": False,
    },
    "high-assurance": {
        "typical": [6, 12], "soft": 12, "hard": 18,
        "review_roles": ["methods-evidence", "operations-reproducibility", "ethics-claim-integrity"],
        "independent_required": True,
    },
}

ARCHETYPES = {
    "experimental", "computational", "observational", "qualitative-field",
    "humanities-interpretive", "conceptual-normative", "evidence-synthesis",
    "policy-program-evaluation", "design-engineering", "creative-practice",
    "mixed-methods",
}
DIMENSION_STATUSES = {"unresolved", "partial", "resolved", "explicit-default", "deferred", "not-applicable", "blocked"}
COMPLETE_DIMENSION_STATUSES = {"resolved", "explicit-default", "deferred", "not-applicable", "blocked"}
REVIEW_VERDICTS = {"pass", "revise", "block"}
REVIEW_MODES = {"independent-subagent", "separate-session", "external-human", "sequential-pass"}
# Modes that assert the reviewer ran outside this context. Nothing inside this script
# can observe another process, so the claim is an attestation, not proof. Requiring
# execution evidence makes it an attestation with an audit trail and stops a record
# from claiming independence by writing a bare string.
INDEPENDENCE_CLAIMING_MODES = {"independent-subagent", "separate-session", "external-human"}
FINDING_ACTIONS = {"agent-fix", "user-answer", "external-approval", "accepted-risk"}
SEVERITIES = {"info", "minor", "major", "critical"}
# Stopping reasons that describe an unfinished campaign. A draft the user asked for, or a
# campaign waiting on an external dependency, must not reach EXECUTION-READY just because
# every other check happens to pass.
NON_EXECUTABLE_STOP_REASONS = {"user-requested-draft", "blocked-by-external-dependency"}
STOP_REASONS = {
    "material-completeness", "low-next-question-value", "user-budget-reached",
    "blocked-by-external-dependency", "user-requested-draft",
}

# Single source of truth for campaign object shapes. Drives `add` key checking,
# `schema` output, and the rendered campaign prompt. `required` mirrors
# validate_state exactly; changing one without the other is a defect.
OBJECT_SPECS: dict[str, dict[str, Any]] = {
    "campaign.dossier.objects": {
        "label": "object", "title": "name",
        "required": (),
        "fields": (("description", "Description"), ("current_state", "Current state"), ("boundary", "Boundary")),
    },
    "campaign.dossier.source_hierarchy": {
        "label": "source", "title": "source",
        "required": (),
        "fields": (("tier", "Tier"), ("admissibility", "Admissibility"), ("limitations", "Known limitations")),
    },
    "campaign.dossier.context": {
        "label": "context item", "title": "summary",
        "required": (), "fields": (("relevance", "Why it changes the design"),),
    },
    "campaign.dossier.access_rights": {
        "label": "access record", "title": "resource",
        "required": (), "fields": (("rights", "Rights"), ("approval", "Approval"), ("expiry", "Expiry")),
    },
    "campaign.dossier.alternatives": {
        "label": "alternative", "title": "account",
        "required": (), "fields": (("evidence", "Existing evidence"), ("status", "Status")),
    },
    "campaign.inquiries": {
        "label": "inquiry", "title": "question_or_claim",
        "required": ("question_or_claim", "importance", "admissible_support",
                     "counterevidence_or_rival", "verification_or_adjudication", "reporting_rule"),
        "fields": (
            ("importance", "Why it matters"),
            ("admissible_support", "Admissible support"),
            ("counterevidence_or_rival", "Counterevidence, rival explanation, reading, or objection"),
            ("discriminating_implication", "Discriminating prediction or interpretive implication"),
            ("verification_or_adjudication", "Verification or adjudication"),
            ("uncertainty_boundary", "Uncertainty and external-validity boundary"),
            ("reporting_rule", "Reporting rule"),
        ),
    },
    "campaign.methods": {
        "label": "method", "title": "name",
        "required": ("purpose", "inputs", "outputs", "assumptions", "limitations", "cost",
                     "dependencies", "can_change_decision"),
        "fields": (
            ("purpose", "Purpose"), ("inquiry_ids", "Answers inquiries"), ("inputs", "Inputs"),
            ("outputs", "Outputs"), ("assumptions", "Assumptions"), ("limitations", "Limitations"),
            ("cost", "Cost"), ("dependencies", "Dependencies"),
            ("can_change_decision", "Decision it can change"),
        ),
    },
    "campaign.tools": {
        "label": "tool", "title": "name",
        "required": (),
        "fields": (
            ("identity_version", "Identity and version"), ("production", "Production use"),
            ("purpose", "Purpose"), ("access", "Access"), ("access_license", "Access and licence"),
            ("license", "License or rights"), ("documentation", "Authoritative documentation"),
        ),
    },
    "campaign.canaries": {
        "label": "canary", "title": "production_like_test",
        "required": ("tool_id", "production_like_test", "expected_artifacts", "sanity_checks", "downstream_acceptance"),
        "fields": (
            ("tool_id", "Tool"), ("expected_artifacts", "Expected artifacts and schema"),
            ("sanity_checks", "Positive, negative, and sanity cases"),
            ("downstream_acceptance", "Downstream acceptance"),
            ("quarantine_rules", "Quarantine triggers"),
        ),
    },
    "campaign.stages": {
        "label": "stage", "title": "name",
        "required": ("purpose", "activities", "outputs", "owner", "budget", "pace", "gate_id"),
        "fields": (
            ("purpose", "Purpose"), ("prerequisite_stage_ids", "Prerequisites"), ("inputs", "Inputs"),
            ("activities", "Activities"), ("outputs", "Outputs"), ("owner", "Owner"),
            ("budget", "Budget"), ("pace", "Expected pace"), ("gate_id", "Promotion gate"),
        ),
    },
    "campaign.gates": {
        "label": "gate", "title": "criteria",
        "required": ("stage_id", "criteria", "required_evidence", "owner", "on_fail"),
        "fields": (
            ("stage_id", "Stage"), ("required_evidence", "Required evidence"),
            ("owner", "Owner"), ("on_fail", "On failure"),
        ),
    },
    "campaign.roles": {
        "label": "role", "title": "name",
        "required": (),
        "fields": (("description", "Description"), ("responsibility", "Responsibility"),
                   ("authority", "Authority"), ("limits", "Limits")),
    },
    "campaign.work_units": {
        "label": "work unit", "title": "objective",
        "required": ("objective", "authoritative_inputs", "permitted_actions", "prohibited_actions",
                     "outputs", "acceptance_test", "resource_ceiling", "retry_policy", "escalation"),
        "fields": (
            ("authoritative_inputs", "Authoritative inputs and hashes"),
            ("permitted_actions", "Permitted actions"), ("prohibited_actions", "Prohibited actions"),
            ("method_constraints", "Method and tool constraints"), ("outputs", "Exact outputs"),
            ("acceptance_test", "Verification and acceptance"), ("resource_ceiling", "Resource ceiling"),
            ("retry_policy", "Retry and failure classes"), ("escalation", "Escalation and handoff"),
            ("dependency_ids", "Depends on work units"),
        ),
    },
    "campaign.claims": {
        "label": "claim", "title": "statement",
        "required": ("inquiry_id", "statement", "support", "counterevidence_or_objections",
                     "verification", "status", "reporting_rule"),
        "fields": (
            ("inquiry_id", "Inquiry"), ("support", "Support"),
            ("counterevidence_or_objections", "Counterevidence and objections"),
            ("verification", "Verification"), ("status", "Status"),
            ("uncertainty", "Uncertainty"), ("reporting_rule", "Reporting rule"),
        ),
    },
    "campaign.deliverables": {
        "label": "deliverable", "title": "name",
        "required": ("name", "path", "acceptance_test", "owner"),
        "fields": (
            ("path", "Path"), ("schema", "Schema"), ("acceptance_test", "Acceptance test"),
            ("owner", "Owner"), ("immutable_after_freeze", "Immutable after freeze"),
        ),
    },
    "blockers": {
        "label": "blocker", "title": "description",
        "required": (),
        "fields": (("severity", "Severity"), ("status", "Status"), ("owner", "Owner"), ("unblocks", "Unblocked by")),
    },
    "contradictions": {
        "label": "contradiction", "title": "description",
        "required": (),
        "fields": (("importance", "Importance"), ("status", "Status"), ("statements", "Conflicting statements")),
    },
}


# Dict-valued campaign sections. These are written with `set`, not `add`, so they have no
# OBJECT_SPECS entry — but an agent still has to learn their field names, and reading the
# whole architecture reference to find them costs ~4k tokens. `required` mirrors
# validate_state exactly; changing one without the other is a defect.
SECTION_SPECS: dict[str, dict[str, Any]] = {
    "campaign.mission": {
        "required": ("decision_or_purpose", "scope", "completion_definition"),
        "optional": ("non_goals", "intended_users"),
    },
    "campaign.constitution": {"required": ("rules", "worker_inheritance"), "optional": ()},
    "campaign.evaluation": {
        "required": ("criteria", "comparators_or_adjudication", "missing_evidence_policy",
                     "exploration_confirmation_policy", "stop_pivot_no_go_rules", "frozen_before_production_asserted"),
        "optional": (),
    },
    "campaign.resources_dispatch": {
        "required": ("dispatch_rules", "budgets"),
        "optional": ("access_constraints", "concurrency", "approvals"),
    },
    "campaign.runtime": {
        "required": ("continuation_trigger", "state_store", "event_log", "checkpoint_policy",
                     "liveness", "recovery", "idempotency"),
        "optional": ("enabled",),
        "note": "Required only when `enabled` is true.",
    },
    "campaign.ethics_rights_safety": {
        "required": ("constraints",),
        "optional": ("external_actions", "human_approval_points"),
        "note": ("Each entry in external_actions must be an object with an `approval_id` naming the "
                 "specific approval that authorizes it; approvals live in resources_dispatch.approvals "
                 "or human_approval_points and need an `id`. Generic approval prose does not gate an action."),
    },
    "campaign.reporting": {
        "required": ("negative_result_policy", "deviation_policy"),
        "optional": ("claim_rules", "least_favorable_interpretation"),
    },
    "campaign.kickoff": {"required": ("command", "first_gate_id"), "optional": ("initial_backlog",)},
    "campaign.dossier": {
        "required": ("objects", "source_hierarchy"),
        "optional": ("context", "access_rights", "alternatives"),
        "note": "Sub-lists are written with `add`; see their own schema entries.",
    },
}


def spec_for(path: str) -> dict[str, Any] | None:
    return OBJECT_SPECS.get(path)


def allowed_keys(spec: dict[str, Any]) -> set[str]:
    keys = {"id", spec["title"]}
    keys.update(spec["required"])
    keys.update(name for name, _ in spec["fields"])
    return keys


def allowed_section_keys(spec: dict[str, Any]) -> set[str]:
    return set(spec["required"]) | set(spec["optional"])


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(value: Any) -> str:
    return "sha256:" + sha256_bytes(canonical_json(value).encode("utf-8"))


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (slug[:56] or "campaign").rstrip("-")


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    atomic_write(path, json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def resolve_campaign(path: str | Path) -> Path:
    candidate = Path(path).expanduser().resolve()
    if (candidate / STATE_REL).exists():
        return candidate
    if candidate.name == "campaign.json" and candidate.parent.name == "state":
        return candidate.parent.parent
    raise SystemExit(f"Campaign not found: {candidate}")


def load_state(campaign_dir: Path) -> dict[str, Any]:
    return read_json(campaign_dir / STATE_REL)


def substantive_state(state: dict[str, Any], deep: bool = True) -> dict[str, Any]:
    """Remove volatile/review/output fields before computing content digest.

    `status` is derived from validation of the rest of the state, so including it
    would make a successful render mutate the digest its own reviews were bound to.
    """
    value = copy.deepcopy(state) if deep else dict(state)
    for key in ("updated_at", "reviews", "outputs", "last_validation", "status"):
        value.pop(key, None)
    assurance = value.get("assurance")
    if isinstance(assurance, dict):
        # Evidence records bind to this digest, so including them would make their own
        # binding circular. The policy decision remains substantive and review-bound.
        value["assurance"] = {"pilot_required": bool(assurance.get("pilot_required"))}
    return value


def content_digest(state: dict[str, Any]) -> str:
    return sha256_json(substantive_state(state))


def rubric_payload(profile: str) -> dict[str, Any]:
    # Deliberately excludes the tool VERSION. Including it meant a patch release
    # changed the rubric digest with the checks byte-identical, invalidating every
    # frozen review of every in-flight campaign. Bump `rubric_version` only when the
    # checks themselves change.
    return {
        "rubric_version": "3",
        "profile": profile,
        "required_roles": PROFILES[profile]["review_roles"],
        "independent_required": PROFILES[profile]["independent_required"],
        "checks": [
            "mission-scope-and-non-goals", "inquiry-and-counterevidence",
            "method-fit-and-alternatives", "evaluation-freeze-and-stopping",
            "tools-canaries-and-artifacts", "stages-gates-and-resources",
            "delegation-recovery-and-approvals", "ethics-rights-and-safety",
            "claims-evidence-traceability", "proportionality-and-user-burden",
            "readiness-truthfulness",
        ],
    }


def rubric_digest(profile: str) -> str:
    return sha256_json(rubric_payload(profile))


def finding_digest(role: str, finding: dict[str, Any]) -> str:
    """Stable identity for an exact finding in one review role."""
    return sha256_json({"role": role, "finding": finding})


def save_state(campaign_dir: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = now_iso()
    write_json(campaign_dir / STATE_REL, state)


def default_state(goal: str, profile: str, archetypes: list[str], campaign_id: str) -> dict[str, Any]:
    limits = PROFILES[profile]
    return {
        "schema_version": SCHEMA_VERSION,
        "rescamp_version": VERSION,
        "campaign_id": campaign_id,
        "title": goal.strip()[:120],
        "goal_verbatim": goal.strip(),
        "profile": profile,
        "archetypes": archetypes,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "content_version": 1,
        "status": "interviewing",
        "sketch": {
            "decision_or_purpose": "",
            "scope": "",
            "core_inquiries": [],
            "likely_evidence": [],
            "rough_methods_stages": [],
            "success_or_adjudication": "",
            "assumptions_risks": [],
            "proposed_outputs": [],
        },
        "intent_dimensions": [],
        "interview": {
            "soft_limit": limits["soft"],
            "hard_limit": limits["hard"],
            "extension_authorized": False,
            "turns": [],
            "stopping_reason": "",
            "stopping_note": "",
        },
        "campaign": {
            "constitution": {"rules": [], "worker_inheritance": True},
            "mission": {"decision_or_purpose": "", "scope": "", "non_goals": [], "intended_users": [], "completion_definition": ""},
            "dossier": {"objects": [], "context": [], "source_hierarchy": [], "access_rights": [], "alternatives": []},
            "inquiries": [],
            "methods": [],
            "tools": [],
            "canaries": [],
            "evaluation": {
                "frozen_before_production_asserted": False,
                "criteria": [], "comparators_or_adjudication": [],
                "missing_evidence_policy": "", "exploration_confirmation_policy": "",
                "stop_pivot_no_go_rules": [],
            },
            "stages": [],
            "gates": [],
            "resources_dispatch": {"budgets": [], "access_constraints": [], "concurrency": "", "dispatch_rules": [], "approvals": []},
            "roles": [],
            "runtime": {"enabled": False, "continuation_trigger": "", "state_store": "", "event_log": "", "checkpoint_policy": "", "liveness": "", "recovery": "", "idempotency": ""},
            "work_units": [],
            "ethics_rights_safety": {"constraints": [], "external_actions": [], "human_approval_points": []},
            "reporting": {"claim_rules": [], "negative_result_policy": "", "deviation_policy": "", "least_favorable_interpretation": True},
            "claims": [],
            "deliverables": [],
            "kickoff": {"command": "", "first_gate_id": "", "initial_backlog": []},
        },
        "assumptions": [],
        "contradictions": [],
        "blockers": [],
        "assurance": {"pilot_required": profile == "high-assurance", "pilot": {}, "risk_acceptances": []},
        "reviews": {"frozen_content_digest": "", "rubric_digest": "", "records": []},
        "outputs": {"last_rendered_digest": "", "manifest": {}},
        "last_validation": {},
    }


def get_by_path(data: Any, dotted: str) -> Any:
    current = data
    for part in dotted.split("."):
        if isinstance(current, list):
            current = current[int(part)]
        else:
            current = current[part]
    return current


# Engine-owned state. Writing these directly would bypass the checks that make them mean
# anything: `reviews` has ingest-review, `status` is derived from validation, `outputs` and
# `last_validation` are rendered records.
PROTECTED_PATHS = ("reviews", "status", "outputs", "last_validation")


def guard_protected_path(dotted: str) -> None:
    head = dotted.split(".", 1)[0]
    if head in PROTECTED_PATHS:
        raise SystemExit(
            f"Refusing to write {dotted!r}: {head!r} is engine-owned.\n"
            "Review records are written only by `ingest-review`, which checks mode, execution "
            "evidence, verdict, findings shape, and digest binding. `status`, `outputs`, and "
            "`last_validation` are derived by validate/render."
        )


def set_by_path(data: Any, dotted: str, value: Any, create_missing: bool = True) -> None:
    parts = dotted.split(".")
    current = data
    for index, part in enumerate(parts[:-1]):
        if isinstance(current, list):
            position = int(part)
            if position >= len(current):
                raise SystemExit(f"Index out of range at '{'.'.join(parts[:index + 1])}': list has {len(current)} item(s)")
            current = current[position]
        else:
            if part not in current:
                if not create_missing:
                    known = ", ".join(sorted(current)) if isinstance(current, dict) else "(not an object)"
                    raise SystemExit(
                        f"Unknown path segment '{part}' in '{dotted}'.\n"
                        f"known keys at '{'.'.join(parts[:index]) or '<root>'}': {known}"
                    )
                current[part] = {}
            elif not isinstance(current[part], (dict, list)):
                current[part] = {}
            current = current[part]
    last = parts[-1]
    if isinstance(current, list):
        current[int(last)] = value
    else:
        if not create_missing and last not in current:
            known = ", ".join(sorted(current))
            raise SystemExit(
                f"Unknown final field '{last}' in '{dotted}'.\n"
                f"known keys at '{'.'.join(parts[:-1]) or '<root>'}': {known}"
            )
        current[last] = value


def parse_json_arg(value: str) -> Any:
    if value.startswith("@"):
        return read_json(Path(value[1:]))
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def add_unique_id(items: list[dict[str, Any]], item: dict[str, Any], label: str) -> None:
    ident = str(item.get("id", "")).strip()
    if not ident:
        raise SystemExit(f"{label} requires non-empty id")
    if any(str(existing.get("id", "")) == ident for existing in items if isinstance(existing, dict)):
        raise SystemExit(f"duplicate {label} id: {ident}")
    items.append(item)


def cmd_init(args: argparse.Namespace) -> None:
    if args.profile not in PROFILES:
        raise SystemExit(f"Unknown profile: {args.profile}")
    archetypes = [item.strip() for item in args.archetypes.split(",") if item.strip()]
    unknown = sorted(set(archetypes) - ARCHETYPES)
    if unknown:
        raise SystemExit("Unknown archetypes: " + ", ".join(unknown)
                         + "\nvalid archetypes: " + ", ".join(sorted(ARCHETYPES)))
    if not archetypes:
        archetypes = ["evidence-synthesis"]
    base = Path(args.root).expanduser().resolve()
    campaign_id = args.id or slugify(args.goal)
    campaign_dir = base / campaign_id
    if campaign_dir.exists() and any(campaign_dir.iterdir()) and not args.force:
        raise SystemExit(f"Campaign directory already exists: {campaign_dir}")
    for rel in ("state", "working", "working/review_packets", "outputs", "artifacts"):
        (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
    state = default_state(args.goal, args.profile, archetypes, campaign_id)
    save_state(campaign_dir, state)
    print(campaign_dir)


def cmd_set(args: argparse.Namespace) -> None:
    guard_protected_path(args.path)
    campaign_dir = resolve_campaign(args.campaign)
    state = load_state(campaign_dir)
    value = parse_json_arg(args.value)
    section = SECTION_SPECS.get(args.path)
    object_spec = spec_for(args.path)
    if section is not None:
        if not isinstance(value, dict):
            raise SystemExit(f"{args.path} must be an object")
        unknown = sorted(set(value) - allowed_section_keys(section))
        if unknown and not args.create_missing:
            raise SystemExit(
                f"unknown field(s) in {args.path}: {', '.join(unknown)}\n"
                f"known fields: {', '.join(sorted(allowed_section_keys(section)))}"
            )
    elif object_spec is not None:
        if not isinstance(value, list):
            raise SystemExit(f"{args.path} must be a list of objects")
        malformed = [index for index, item in enumerate(value) if not isinstance(item, dict)]
        if malformed:
            raise SystemExit(
                f"{args.path} must contain only objects; malformed item(s): "
                + ", ".join(str(index) for index in malformed)
            )
    # Typing `campaign.evalation.criteria` used to succeed, create a junk key, silently
    # discard the content, and leave the agent staring at "criteria is missing".
    set_by_path(state, args.path, value, create_missing=args.create_missing)
    state["content_version"] += 1
    # Records are not wiped here: staleness is computed from the section digests, so a
    # record whose sections did not move stays valid, and one whose sections did move is
    # filtered out by record_is_current. Wiping would also destroy the findings text the
    # repairing agent is working from.
    save_state(campaign_dir, state)
    print(f"set {args.path}")


def cmd_add(args: argparse.Namespace) -> None:
    guard_protected_path(args.path)
    campaign_dir = resolve_campaign(args.campaign)
    state = load_state(campaign_dir)
    collection = get_by_path(state, args.path)
    if not isinstance(collection, list):
        raise SystemExit(f"Target path is not a list: {args.path}")
    parsed = parse_json_arg(args.json)
    # Accept an array so a campaign can be populated in a handful of calls instead of
    # one subprocess per object, while checking every object's field vocabulary.
    values = parsed if isinstance(parsed, list) else [parsed]
    if not values or not all(isinstance(item, dict) for item in values):
        raise SystemExit("--json must decode to an object or a non-empty array of objects")
    spec = spec_for(args.path)
    if spec is not None and not args.allow_unknown:
        for index, value in enumerate(values):
            unknown = sorted(set(value) - allowed_keys(spec))
            if unknown:
                where = f" (item {index})" if len(values) > 1 else ""
                raise SystemExit(
                    f"unknown {spec['label']} field(s){where}: {', '.join(unknown)}\n"
                    f"known fields: {', '.join(sorted(allowed_keys(spec)))}\n"
                    f"see `rescamp.py schema {args.path}`; pass --allow-unknown to override"
                )
    for value in values:
        if args.require_id:
            add_unique_id(collection, value, args.path)
        else:
            collection.append(value)
    added = [str(value.get("id", "added")) for value in values]
    state["content_version"] += 1
    # Records are not wiped here: staleness is computed from the section digests, so a
    # record whose sections did not move stays valid, and one whose sections did move is
    # filtered out by record_is_current. Wiping would also destroy the findings text the
    # repairing agent is working from.
    save_state(campaign_dir, state)
    print("\n".join(added))


def cmd_apply(args: argparse.Namespace) -> None:
    """Write many sections in one call, with the same field checking `add` performs.

    Without this the agent must choose between 19 separate calls and `set campaign
    @whole.json`, which is one call but silently skips every field check. Neither is
    acceptable: the first burns main-loop turns, the second lets a misspelled field into
    the execution prompt as authoritative content.
    """
    campaign_dir = resolve_campaign(args.campaign)
    state = load_state(campaign_dir)
    payload = parse_json_arg(args.json)
    if not isinstance(payload, dict):
        raise SystemExit("--json must decode to an object mapping dotted paths to values")

    errors: list[str] = []
    for path in payload:
        guard_protected_path(path)
    for path, value in payload.items():
        spec = spec_for(path)
        if spec is None:
            section = SECTION_SPECS.get(path)
            if section is None and not args.allow_unknown:
                errors.append(f"{path}: unknown section; see `rescamp.py schema list`")
            elif section is not None:
                if not isinstance(value, dict):
                    errors.append(f"{path}: expected an object")
                elif not args.allow_unknown:
                    unknown = sorted(set(value) - allowed_section_keys(section))
                    if unknown:
                        errors.append(f"{path}: unknown field(s) {', '.join(unknown)}; "
                                      f"known: {', '.join(sorted(allowed_section_keys(section)))}")
            continue
        if not isinstance(value, list):
            errors.append(f"{path}: expected a list of objects")
            continue
        for index, item in enumerate(value):
            if not isinstance(item, dict):
                errors.append(f"{path}[{index}]: expected an object")
                continue
            unknown = sorted(set(item) - allowed_keys(spec))
            if unknown and not args.allow_unknown:
                errors.append(f"{path}[{index}]: unknown {spec['label']} field(s) {', '.join(unknown)}; "
                              f"known: {', '.join(sorted(allowed_keys(spec)))}")
    if errors:
        raise SystemExit("Nothing was written. Fix these and retry:\n- " + "\n- ".join(errors))

    written: list[str] = []
    for path, value in payload.items():
        set_by_path(state, path, value, create_missing=args.allow_unknown)
        written.append(path)
    state["content_version"] += 1
    save_state(campaign_dir, state)
    print("\n".join(sorted(written)))


def cmd_dimension(args: argparse.Namespace) -> None:
    campaign_dir = resolve_campaign(args.campaign)
    state = load_state(campaign_dir)
    dims = state["intent_dimensions"]
    found = next((item for item in dims if item.get("id") == args.id), None)
    payload = {
        "id": args.id, "label": args.label or args.id.replace("-", " ").title(),
        "status": args.status, "value": parse_json_arg(args.value) if args.value is not None else "",
        "importance": args.importance, "source": args.source,
        "confidence": args.confidence, "reason": args.reason or "",
        "dependencies": [item for item in args.dependencies.split(",") if item] if args.dependencies else [],
    }
    if found:
        found.update(payload)
    else:
        dims.append(payload)
    state["content_version"] += 1
    # Records are not wiped here: staleness is computed from the section digests, so a
    # record whose sections did not move stays valid, and one whose sections did move is
    # filtered out by record_is_current. Wiping would also destroy the findings text the
    # repairing agent is working from.
    save_state(campaign_dir, state)
    print(args.id)


def cmd_turn(args: argparse.Namespace) -> None:
    campaign_dir = resolve_campaign(args.campaign)
    state = load_state(campaign_dir)
    turns = state["interview"]["turns"]
    number = len(turns) + 1
    if number > state["interview"]["hard_limit"] and not state["interview"].get("extension_authorized"):
        raise SystemExit("Hard question limit reached; record explicit extension authorization first")
    record = {
        "number": number, "branch": args.branch, "question": args.question,
        "answer_verbatim": args.answer, "normalized_decision": parse_json_arg(args.normalized),
        "linked_dimensions": [item for item in args.dimensions.split(",") if item],
        "decision_impact": args.impact, "answer_utility": args.utility,
        "asked_at": now_iso(),
    }
    turns.append(record)
    state["content_version"] += 1
    # Records are not wiped here: staleness is computed from the section digests, so a
    # record whose sections did not move stays valid, and one whose sections did move is
    # filtered out by record_is_current. Wiping would also destroy the findings text the
    # repairing agent is working from.
    save_state(campaign_dir, state)
    print(number)


def cmd_stop(args: argparse.Namespace) -> None:
    if args.reason not in STOP_REASONS:
        raise SystemExit("Invalid stopping reason")
    campaign_dir = resolve_campaign(args.campaign)
    state = load_state(campaign_dir)
    state["interview"]["stopping_reason"] = args.reason
    state["interview"]["stopping_note"] = args.note
    state["status"] = "candidate"
    state["content_version"] += 1
    # Records are not wiped here: staleness is computed from the section digests, so a
    # record whose sections did not move stays valid, and one whose sections did move is
    # filtered out by record_is_current. Wiping would also destroy the findings text the
    # repairing agent is working from.
    save_state(campaign_dir, state)
    if args.no_auto_quality:
        print(json.dumps({"stopping_reason": args.reason, "completed_by_this_command": [],
                          "not_run_by_this_command": ["deterministic_validation", "content_freeze",
                                                      "review_packets_written", "reviewer_execution", "defect_repair"],
                          "phase": "quality-loop-skipped"}, indent=2))
        return
    state = load_state(campaign_dir)
    pre = validate_state(state, include_reviews=False)
    write_json(campaign_dir / VALIDATION_REL, pre)
    digest, r_digest, paths = freeze_and_packets(campaign_dir, state)
    state = load_state(campaign_dir)
    still_current, needs_review = review_status(state)
    payload = {
        "stopping_reason": args.reason,
        # What this invocation actually did, versus what still needs an actor.
        "completed_by_this_command": ["deterministic_validation", "content_freeze", "review_packets_written",
                                      "findings_classified"],
        "not_run_by_this_command": ["reviewer_execution", "defect_repair"],
        "phase": "awaiting-review-execution" if pre["valid"] else "awaiting-design-repair",
        "reviews_ingested": 0,
        "content_digest": digest,
        "rubric_digest": r_digest,
        "deterministic_validation": cap_validation_for_stdout(pre),
        "findings_by_action": summarize_findings(classify_validation_findings(pre)),
        "review_packets_are_inputs": True,
        "review_packets_to_execute": [str(path) for path in paths
                                      if path.stem in needs_review],
        "review_packets_all": [str(path) for path in paths],
        "reviews_still_current": still_current,
        "roles_requiring_review": needs_review,
        "next_action": "Resolve deterministic findings and ask only material follow-up questions" if not pre["valid"] else _review_next_action(needs_review),
    }
    write_json(campaign_dir / "working/quality_loop.json", payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _ids(items: Iterable[Any]) -> tuple[set[str], list[str]]:
    seen: set[str] = set()
    dup: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        ident = str(item.get("id", "")).strip()
        if ident:
            if ident in seen:
                dup.append(ident)
            seen.add(ident)
    return seen, sorted(set(dup))


def _nonempty(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value) and all(_nonempty(item) for item in value)
    if isinstance(value, dict):
        return bool(value) and any(_nonempty(item) for item in value.values())
    if isinstance(value, bool):
        return False
    return False


def _required_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _required_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(_nonempty(item) for item in value)


def _displayable(value: Any) -> bool:
    """Keep explicit scalars visible without treating them as filled prose fields."""
    return isinstance(value, (bool, int, float)) or _nonempty(value)


def _operational_value(value: Any) -> bool:
    """Accept a real value, or an explicit not-applicable decision with its reason."""
    if isinstance(value, dict):
        return value.get("status") == "not-applicable" and _nonempty(value.get("reason"))
    return _nonempty(value)


def _is_iso_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _graph_cycle(nodes: set[str], edges: list[tuple[str, str]]) -> list[str]:
    adj: dict[str, list[str]] = {node: [] for node in nodes}
    for left, right in edges:
        if left in nodes and right in nodes:
            adj[left].append(right)
    visiting: set[str] = set()
    visited: set[str] = set()
    trail: list[str] = []

    def visit(node: str) -> list[str] | None:
        if node in visiting:
            # `visiting` and `trail` are pushed and popped together, so the node is on the trail.
            idx = trail.index(node)
            return trail[idx:] + [node]
        if node in visited:
            return None
        visiting.add(node)
        trail.append(node)
        for nxt in adj.get(node, []):
            cycle = visit(nxt)
            if cycle:
                return cycle
        trail.pop()
        visiting.remove(node)
        visited.add(node)
        return None

    for node in sorted(nodes):
        cycle = visit(node)
        if cycle:
            return cycle
    return []


def validate_state(state: dict[str, Any], include_reviews: bool = True) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    def issue(level: str, code: str, message: str, path: str = "") -> None:
        target = errors if level == "error" else warnings
        target.append({"code": code, "message": message, "path": path})

    if not isinstance(state, dict):
        issue("error", "structure.type", "Campaign state must be an object", "")
        return {
            "rescamp_version": VERSION, "checked_at": now_iso(),
            "content_digest": sha256_json(state), "rubric_digest": "",
            "valid": False, "execution_ready": False, "release_status": "draft",
            "errors": errors, "warnings": warnings,
            "counts": {},
            "review": {"required": [], "current": [], "missing": [], "blocking": [],
                       "independence_ok": False},
        }

    # Validation must describe malformed JSON, not throw while walking it. Work on a
    # sanitized copy so callers retain the exact input and the reported digest still
    # fingerprints that input.
    input_digest = content_digest(state)
    state = copy.deepcopy(state)

    def require_object(container: dict[str, Any], key: str, path: str) -> dict[str, Any]:
        if key not in container:
            issue("error", "structure.type", f"{path} is missing; expected an object", path)
            container[key] = {}
        elif not isinstance(container[key], dict):
            issue("error", "structure.type", f"{path} must be an object", path)
            container[key] = {}
        return container[key]

    def require_list(container: dict[str, Any], key: str, path: str) -> list[Any]:
        if key not in container:
            container[key] = []
        elif not isinstance(container[key], list):
            issue("error", "structure.type", f"{path} must be a list", path)
            container[key] = []
        return container[key]

    def require_object_list(container: dict[str, Any], key: str, path: str) -> list[dict[str, Any]]:
        items = require_list(container, key, path)
        valid: list[dict[str, Any]] = []
        for index, item in enumerate(items):
            if isinstance(item, dict):
                valid.append(item)
            else:
                item_path = f"{path}.{index}"
                issue("error", "structure.type", f"{item_path} must be an object", item_path)
        container[key] = valid
        return valid

    def require_string(container: dict[str, Any], key: str, path: str) -> str:
        if key not in container:
            return ""
        if not isinstance(container[key], str):
            issue("error", "structure.type", f"{path} must be a string", path)
            container[key] = ""
        return container[key]

    def require_string_list(container: dict[str, Any], key: str, path: str) -> list[str]:
        if key not in container:
            return []
        items = require_list(container, key, path)
        valid: list[str] = []
        for index, item in enumerate(items):
            if isinstance(item, str):
                valid.append(item)
            else:
                item_path = f"{path}.{index}"
                issue("error", "structure.type", f"{item_path} must be a string", item_path)
        container[key] = valid
        return valid

    interview = require_object(state, "interview", "interview")
    assurance = require_object(state, "assurance", "assurance")
    camp = require_object(state, "campaign", "campaign")
    reviews = require_object(state, "reviews", "reviews")
    require_object(state, "outputs", "outputs")
    for key in ("title", "campaign_id", "profile"):
        if key not in state or not isinstance(state.get(key), str):
            issue("error", "structure.type", f"{key} must be a string", key)
            state[key] = ""
    if "content_version" not in state or isinstance(state.get("content_version"), bool) \
            or not isinstance(state.get("content_version"), int):
        issue("error", "structure.type", "content_version must be an integer", "content_version")
        state["content_version"] = 0

    for key in ("constitution", "mission", "dossier", "evaluation", "resources_dispatch",
                "runtime", "ethics_rights_safety", "reporting", "kickoff"):
        require_object(camp, key, f"campaign.{key}")

    archetypes = require_list(state, "archetypes", "archetypes")
    valid_archetypes: list[str] = []
    for index, archetype in enumerate(archetypes):
        if isinstance(archetype, str):
            valid_archetypes.append(archetype)
        else:
            path = f"archetypes.{index}"
            issue("error", "structure.type", f"{path} must be a string", path)
    state["archetypes"] = valid_archetypes

    require_object_list(state, "intent_dimensions", "intent_dimensions")
    require_list(state, "assumptions", "assumptions")
    require_object_list(state, "contradictions", "contradictions")
    require_object_list(state, "blockers", "blockers")
    require_object_list(interview, "turns", "interview.turns")
    configured_profile = state.get("profile")
    configured_limits = PROFILES.get(configured_profile, PROFILES["standard"]) \
        if isinstance(configured_profile, str) else PROFILES["standard"]
    for limit in ("soft_limit", "hard_limit"):
        if limit in interview and (isinstance(interview[limit], bool) or not isinstance(interview[limit], int)):
            path = f"interview.{limit}"
            issue("error", "structure.type", f"{path} must be an integer", path)
            interview[limit] = configured_limits[limit.split("_")[0]]

    for key in ("inquiries", "methods", "tools", "canaries", "stages", "gates", "roles",
                "work_units", "claims", "deliverables"):
        items = require_object_list(camp, key, f"campaign.{key}")
        for index, item in enumerate(items):
            if "id" in item:
                require_string(item, "id", f"campaign.{key}.{index}.id")
    require_object_list(reviews, "records", "reviews.records")

    dossier = camp["dossier"]
    for key in ("objects", "context", "source_hierarchy", "access_rights", "alternatives"):
        require_list(dossier, key, f"campaign.dossier.{key}")
    constitution = camp["constitution"]
    require_list(constitution, "rules", "campaign.constitution.rules")

    for index, dimension in enumerate(state["intent_dimensions"]):
        for key in ("id", "status", "importance"):
            if key in dimension:
                require_string(dimension, key, f"intent_dimensions.{index}.{key}")
    for key in ("stopping_reason",):
        if key in interview:
            require_string(interview, key, f"interview.{key}")
    for index, method in enumerate(camp["methods"]):
        require_string_list(method, "inquiry_ids", f"campaign.methods.{index}.inquiry_ids")
    for index, tool in enumerate(camp["tools"]):
        if "id" in tool:
            require_string(tool, "id", f"campaign.tools.{index}.id")
    for index, canary in enumerate(camp["canaries"]):
        if "tool_id" in canary:
            require_string(canary, "tool_id", f"campaign.canaries.{index}.tool_id")
    for index, stage in enumerate(camp["stages"]):
        require_string_list(stage, "prerequisite_stage_ids",
                            f"campaign.stages.{index}.prerequisite_stage_ids")
        if "gate_id" in stage:
            require_string(stage, "gate_id", f"campaign.stages.{index}.gate_id")
    for index, gate in enumerate(camp["gates"]):
        if "stage_id" in gate:
            require_string(gate, "stage_id", f"campaign.gates.{index}.stage_id")
    for index, unit in enumerate(camp["work_units"]):
        require_string_list(unit, "dependency_ids", f"campaign.work_units.{index}.dependency_ids")
    for index, claim in enumerate(camp["claims"]):
        if "inquiry_id" in claim:
            require_string(claim, "inquiry_id", f"campaign.claims.{index}.inquiry_id")
    if "first_gate_id" in camp["kickoff"]:
        require_string(camp["kickoff"], "first_gate_id", "campaign.kickoff.first_gate_id")
    for key, items in (("contradictions", state["contradictions"]), ("blockers", state["blockers"])):
        for index, item in enumerate(items):
            for field in ("id", "status", "importance", "severity"):
                if field in item:
                    require_string(item, field, f"{key}.{index}.{field}")

    for index, record in enumerate(reviews["records"]):
        for key in ("role", "reviewer_id", "mode", "verdict", "content_digest", "rubric_digest"):
            if key in record:
                require_string(record, key, f"reviews.records.{index}.{key}")
        if "reviewed_sections" in record and not isinstance(record["reviewed_sections"], dict):
            path = f"reviews.records.{index}.reviewed_sections"
            issue("error", "structure.type", f"{path} must be an object", path)
            record["reviewed_sections"] = {}
        findings = require_object_list(record, "findings", f"reviews.records.{index}.findings")
        for finding_index, finding in enumerate(findings):
            for key in ("severity", "action", "description"):
                if key in finding:
                    require_string(
                        finding, key,
                        f"reviews.records.{index}.findings.{finding_index}.{key}",
                    )
        if "execution_evidence" in record and not isinstance(record["execution_evidence"], dict):
            path = f"reviews.records.{index}.execution_evidence"
            issue("error", "structure.type", f"{path} must be an object", path)
            record["execution_evidence"] = {}
        evidence = record.get("execution_evidence")
        if isinstance(evidence, dict) and "executor_id" in evidence:
            require_string(evidence, "executor_id", f"reviews.records.{index}.execution_evidence.executor_id")

    if state.get("schema_version") != SCHEMA_VERSION:
        issue("error", "schema.unsupported",
              f"Campaign schema {state.get('schema_version')!r} is not current {SCHEMA_VERSION!r}; "
              "migrate explicitly before release", "schema_version")

    profile = state.get("profile")
    if not isinstance(profile, str) or profile not in PROFILES:
        issue("error", "profile.invalid", f"Unknown profile {profile!r}", "profile")
        return {"valid": False, "execution_ready": False, "errors": errors, "warnings": warnings}
    unknown_archetypes = sorted(set(state.get("archetypes", [])) - ARCHETYPES)
    if unknown_archetypes:
        issue("error", "archetype.invalid", ", ".join(unknown_archetypes), "archetypes")

    pilot_required = profile == "high-assurance" or assurance.get("pilot_required") is True
    pilot = assurance.get("pilot", {})
    if pilot_required and not isinstance(pilot, dict):
        issue("error", "pilot.malformed", "assurance.pilot must be an object", "assurance.pilot")
    elif pilot_required and not pilot:
        issue("error", "pilot.missing", "This campaign requires a completed, digest-bound pilot", "assurance.pilot")
    elif pilot_required:
        if not _nonempty(pilot.get("authorized_by")) or not _nonempty(pilot.get("authority")):
            issue("error", "pilot.authority",
                  "A required pilot needs the identity and authority that authorized execution",
                  "assurance.pilot")
        if pilot.get("status") != "passed":
            issue("error", "pilot.not_passed", "The required pilot has not passed", "assurance.pilot.status")
        if pilot.get("content_digest") != input_digest:
            issue("error", "pilot.stale",
                  "The required pilot was executed against an older campaign digest; rerun it after repairs",
                  "assurance.pilot.content_digest")
        missing_pilot_fields = [
            field for field in ("executor_id", "scope", "resource_cap")
            if not _nonempty(pilot.get(field))
        ]
        if not _is_iso_timestamp(pilot.get("executed_at")):
            missing_pilot_fields.append("executed_at")
        list_fields = ("evidence", "failures", "repairs")
        missing_pilot_fields.extend(field for field in list_fields if not isinstance(pilot.get(field), list))
        if not _required_list(pilot.get("evidence")):
            if "evidence" not in missing_pilot_fields:
                missing_pilot_fields.append("evidence")
        if missing_pilot_fields:
            issue("error", "pilot.incomplete",
                  "Required pilot record missing valid fields: " + ", ".join(sorted(missing_pilot_fields)),
                  "assurance.pilot")

    interview = state.get("interview", {})
    turns = interview.get("turns", [])
    if len(turns) > interview.get("hard_limit", PROFILES[profile]["hard"]) and not interview.get("extension_authorized"):
        issue("error", "interview.hard_limit", "Interview exceeded hard limit without explicit authorization", "interview.turns")
    if not interview.get("stopping_reason"):
        issue("error", "interview.no_stop_reason", "Interview stopping reason is missing", "interview.stopping_reason")
    elif interview.get("stopping_reason") not in STOP_REASONS:
        issue("error", "interview.bad_stop_reason", "Interview stopping reason is invalid", "interview.stopping_reason")
    elif interview.get("stopping_reason") in NON_EXECUTABLE_STOP_REASONS:
        # The user asked for a draft, or the campaign is waiting on something outside it.
        # Passing the other checks does not overrule that.
        issue("error", "interview.not_executable",
              f"The interview stopped as {interview['stopping_reason']!r}, which is not an execution-ready "
              "outcome. Resolve the dependency or resume the interview and stop for a completeness reason.",
              "interview.stopping_reason")
    if len(turns) > interview.get("soft_limit", PROFILES[profile]["soft"]):
        warning_text = "Interview exceeded soft limit; ensure extension value was explained"
        issue("warning", "interview.soft_limit", warning_text, "interview.turns")

    dimension_ids, duplicates = _ids(state.get("intent_dimensions", []))
    if duplicates:
        issue("error", "dimension.duplicate", f"Duplicate intent dimensions: {', '.join(duplicates)}", "intent_dimensions")
    for index, dim in enumerate(state.get("intent_dimensions", [])):
        path = f"intent_dimensions.{index}"
        if dim.get("status") not in DIMENSION_STATUSES:
            issue("error", "dimension.status", f"Invalid status for {dim.get('id', index)}", path)
        importance = dim.get("importance", "material")
        if importance in {"critical", "material"} and dim.get("status") not in COMPLETE_DIMENSION_STATUSES:
            issue("error", "dimension.unresolved", f"Material dimension {dim.get('id', index)} is unresolved", path)
        if dim.get("status") in {"explicit-default", "deferred", "not-applicable", "blocked"} \
                and not _required_text(dim.get("reason")):
            issue("error", "dimension.reason", f"Status {dim.get('status')} requires a reason", path)

    camp = state.get("campaign", {})
    mission = camp.get("mission", {})
    for field in ("decision_or_purpose", "scope", "completion_definition"):
        if not _required_text(mission.get(field)):
            issue("error", "mission.missing", f"Mission field {field} is missing", f"campaign.mission.{field}")
    constitution = camp.get("constitution", {})
    rules = constitution.get("rules")
    if not constitution.get("worker_inheritance") or not isinstance(rules, list) \
            or len(rules) < 3 or not all(_required_text(rule) for rule in rules):
        issue("error", "constitution.weak", "Constitution needs inherited verification/provenance/safety/reporting rules", "campaign.constitution")

    dossier = camp.get("dossier", {})
    if not _required_list(dossier.get("objects")):
        issue("error", "dossier.objects", "Exact objects, cases, corpus, population, or system are missing", "campaign.dossier.objects")
    if not _required_list(dossier.get("source_hierarchy")):
        issue("error", "dossier.sources", "Source/evidence hierarchy is missing", "campaign.dossier.source_hierarchy")

    inquiry_ids, inquiry_dups = _ids(camp.get("inquiries", []))
    if inquiry_dups:
        issue("error", "inquiry.duplicate", f"Duplicate inquiry IDs: {', '.join(inquiry_dups)}", "campaign.inquiries")
    if not inquiry_ids:
        issue("error", "inquiry.none", "At least one central inquiry is required", "campaign.inquiries")
    for index, item in enumerate(camp.get("inquiries", [])):
        path = f"campaign.inquiries.{index}"
        field_checks = {
            "question_or_claim": _required_text, "importance": _required_text,
            "admissible_support": _required_list, "counterevidence_or_rival": _required_list,
            "verification_or_adjudication": _required_text, "reporting_rule": _required_text,
        }
        for field, check in field_checks.items():
            if not check(item.get(field)):
                issue("error", "inquiry.incomplete", f"Inquiry {item.get('id', index)} missing {field}", path)

    method_ids, method_dups = _ids(camp.get("methods", []))
    if method_dups:
        issue("error", "method.duplicate", f"Duplicate method IDs: {', '.join(method_dups)}", "campaign.methods")
    if not method_ids:
        issue("error", "method.none", "At least one method is required", "campaign.methods")
    for index, item in enumerate(camp.get("methods", [])):
        path = f"campaign.methods.{index}"
        method_checks = {
            "purpose": _required_text, "inputs": _required_list, "outputs": _required_list,
            "assumptions": _required_list, "limitations": _required_list,
            "cost": _required_text, "dependencies": _operational_value,
            "can_change_decision": _required_text,
        }
        for field, check in method_checks.items():
            if not check(item.get(field)):
                issue("error", "method.incomplete",
                      f"Method {item.get('id', index)} missing {field}; use a value or "
                      "{'status': 'not-applicable', 'reason': '...'}", path)
        linked = set(item.get("inquiry_ids", []))
        unknown = sorted(linked - inquiry_ids)
        if unknown:
            issue("error", "method.bad_inquiry_ref", f"Unknown inquiry refs: {', '.join(unknown)}", path)

    tool_ids, tool_dups = _ids(camp.get("tools", []))
    canary_ids, canary_dups = _ids(camp.get("canaries", []))
    if tool_dups or canary_dups:
        issue("error", "tool.duplicate", f"Duplicate tool/canary IDs: {', '.join(tool_dups + canary_dups)}", "campaign.tools")
    canary_by_tool = {item.get("tool_id") for item in camp.get("canaries", []) if isinstance(item, dict)}
    for index, tool in enumerate(camp.get("tools", [])):
        if tool.get("production") and tool.get("id") not in canary_by_tool:
            issue("error", "tool.no_canary", f"Production tool {tool.get('id')} lacks a canary", f"campaign.tools.{index}")
        if tool.get("production") and not _nonempty(tool.get("identity_version")):
            issue("error", "tool.no_version", f"Production tool {tool.get('id')} lacks identity/version", f"campaign.tools.{index}")
    for index, canary in enumerate(camp.get("canaries", [])):
        if canary.get("tool_id") not in tool_ids:
            issue("error", "canary.bad_tool_ref", f"Canary {canary.get('id')} references unknown tool", f"campaign.canaries.{index}")
        canary_checks = {
            "production_like_test": _required_text, "expected_artifacts": _required_list,
            "sanity_checks": _required_list, "downstream_acceptance": _required_text,
        }
        for field, check in canary_checks.items():
            if not check(canary.get(field)):
                issue("error", "canary.incomplete", f"Canary {canary.get('id')} missing {field}", f"campaign.canaries.{index}")

    evaluation = camp.get("evaluation", {})
    if not evaluation.get("frozen_before_production_asserted"):
        issue("error", "evaluation.not_frozen",
              "The campaign does not assert that the evaluation/adjudication instrument was frozen "
              "before production evidence was inspected. This is an attestation by whoever compiled "
              "the campaign; nothing here can verify when the freeze actually happened.",
              "campaign.evaluation")
    evaluation_checks = {
        "criteria": _required_list, "comparators_or_adjudication": _required_list,
        "missing_evidence_policy": _required_text, "exploration_confirmation_policy": _required_text,
        "stop_pivot_no_go_rules": _required_list,
    }
    for field, check in evaluation_checks.items():
        if not check(evaluation.get(field)):
            issue("error", "evaluation.incomplete", f"Evaluation field {field} is missing", f"campaign.evaluation.{field}")

    stage_ids, stage_dups = _ids(camp.get("stages", []))
    gate_ids, gate_dups = _ids(camp.get("gates", []))
    if stage_dups or gate_dups:
        issue("error", "stage.duplicate", f"Duplicate stage/gate IDs: {', '.join(stage_dups + gate_dups)}", "campaign.stages")
    if not stage_ids:
        issue("error", "stage.none", "At least one stage is required", "campaign.stages")
    edges: list[tuple[str, str]] = []
    for index, stage in enumerate(camp.get("stages", [])):
        path = f"campaign.stages.{index}"
        prereqs = set(stage.get("prerequisite_stage_ids", []))
        for prereq in prereqs:
            if prereq not in stage_ids:
                issue("error", "stage.bad_prereq", f"Unknown prerequisite {prereq}", path)
            edges.append((prereq, stage.get("id", "")))
        stage_checks = {
            "purpose": _required_text, "activities": _required_list, "outputs": _required_list,
            "owner": _required_text, "budget": _required_text, "pace": _required_text,
            "gate_id": _required_text,
        }
        for field, check in stage_checks.items():
            if not check(stage.get(field)):
                issue("error", "stage.incomplete", f"Stage {stage.get('id', index)} missing {field}", path)
        if stage.get("gate_id") not in gate_ids:
            issue("error", "stage.bad_gate", f"Stage {stage.get('id')} references unknown gate", path)
    cycle = _graph_cycle(stage_ids, edges)
    if cycle:
        issue("error", "stage.cycle", "Stage graph cycle: " + " -> ".join(cycle), "campaign.stages")
    for index, gate in enumerate(camp.get("gates", [])):
        path = f"campaign.gates.{index}"
        if gate.get("stage_id") not in stage_ids:
            issue("error", "gate.bad_stage", f"Gate {gate.get('id')} references unknown stage", path)
        gate_checks = {"criteria": _required_list, "required_evidence": _required_list,
                       "owner": _required_text, "on_fail": _required_text}
        for field, check in gate_checks.items():
            if not check(gate.get(field)):
                issue("error", "gate.incomplete", f"Gate {gate.get('id', index)} missing {field}", path)

    resources = camp.get("resources_dispatch", {})
    if not _required_list(resources.get("dispatch_rules")):
        issue("error", "dispatch.rules", "Fail-closed dispatch rules are missing", "campaign.resources_dispatch.dispatch_rules")
    if profile != "scoped" and not _required_list(resources.get("budgets")):
        issue("error", "resources.budget", "Resource/budget ceiling is missing", "campaign.resources_dispatch.budgets")

    runtime = camp.get("runtime", {})
    work_unit_ids, work_unit_dups = _ids(camp.get("work_units", []))
    if work_unit_dups:
        issue("error", "work_unit.duplicate", f"Duplicate work-unit IDs: {', '.join(work_unit_dups)}", "campaign.work_units")
    if runtime.get("enabled"):
        for field in ("continuation_trigger", "state_store", "event_log", "checkpoint_policy", "liveness", "recovery", "idempotency"):
            if not _required_text(runtime.get(field)):
                issue("error", "runtime.incomplete", f"Runtime field {field} is missing", f"campaign.runtime.{field}")
        if not work_unit_ids:
            issue("error", "work_unit.none", "Enabled continuous execution needs bounded work units", "campaign.work_units")
        for index, unit in enumerate(camp.get("work_units", [])):
            unit_checks = {
                "objective": _required_text, "authoritative_inputs": _required_list,
                "permitted_actions": _required_list, "prohibited_actions": _required_list,
                "outputs": _required_list, "acceptance_test": _required_text,
                "resource_ceiling": _required_text, "retry_policy": _required_text,
                "escalation": _required_text,
            }
            for field, check in unit_checks.items():
                if not check(unit.get(field)):
                    issue("error", "work_unit.incomplete", f"Work unit {unit.get('id', index)} missing {field}", f"campaign.work_units.{index}")
    ethics = camp.get("ethics_rights_safety", {})
    external_actions = ethics.get("external_actions", [])
    approval_sources = (
        ("campaign.resources_dispatch.approvals", resources.get("approvals", [])),
        ("campaign.ethics_rights_safety.human_approval_points", ethics.get("human_approval_points", [])),
    )
    require_dispatchable_approvals = bool(external_actions)
    approval_ids: set[str] = set()
    approval_count = 0
    for approval_path, records in approval_sources:
        if not isinstance(records, list):
            if require_dispatchable_approvals:
                issue("error", "approval.malformed", "Approval declarations must be lists", approval_path)
            continue
        approval_count += len(records)
        for approval_index, record in enumerate(records):
            if not isinstance(record, dict) or not isinstance(record.get("id"), str) \
                    or not record["id"].strip() or record["id"] != record["id"].strip():
                if require_dispatchable_approvals:
                    issue("error", "approval.malformed",
                          "Approvals must be structured objects with non-empty string IDs",
                          f"{approval_path}.{approval_index}")
                continue
            approval_id = record["id"]
            if approval_id in approval_ids:
                issue("error", "approval.duplicate", f"Duplicate approval ID {approval_id!r}",
                      f"{approval_path}.{approval_index}")
            approval_ids.add(approval_id)
    if external_actions and approval_count == 0:
        issue("error", "approval.missing", "External actions exist without human approval points", "campaign.ethics_rights_safety")
    external_action_by_id: dict[str, dict[str, Any]] = {}
    for index, action in enumerate(external_actions):
        if not isinstance(action, dict):
            issue("error", "external_action.malformed",
                  f"external_actions[{index}] must be an object naming the action and its approval; "
                  "see `rescamp.py schema campaign.ethics_rights_safety`",
                  f"campaign.ethics_rights_safety.external_actions.{index}")
            continue
        raw_action_id = action.get("id")
        action_id = raw_action_id if isinstance(raw_action_id, str) else ""
        if not action_id.strip() or action_id != action_id.strip():
            issue("error", "external_action.malformed", f"external_actions[{index}] needs a non-empty id",
                  f"campaign.ethics_rights_safety.external_actions.{index}")
        elif action_id in external_action_by_id:
            issue("error", "external_action.duplicate", f"Duplicate external action ID {action_id!r}",
                  f"campaign.ethics_rights_safety.external_actions.{index}")
        else:
            external_action_by_id[action_id] = action
        gate = action.get("approval_id")
        if not isinstance(gate, str) or not gate.strip():
            issue("error", "external_action.ungated",
                  f"External action {action.get('id', index)!r} names no approval_id. An external action "
                  "must point at the specific approval that authorizes it, not at generic approval prose.",
                  f"campaign.ethics_rights_safety.external_actions.{index}")
        elif gate != gate.strip() or gate not in approval_ids:
            issue("error", "external_action.bad_approval_ref",
                  f"External action {action.get('id', index)!r} references unknown approval {gate!r}",
                  f"campaign.ethics_rights_safety.external_actions.{index}")

    # 3. Rendered outputs must still match the state they were rendered from.
    rendered = state.get("outputs", {}).get("last_rendered_digest")
    if rendered and rendered != input_digest:
        issue("error", "outputs.stale",
              "The rendered bundle was produced from an older campaign version; re-render before "
              "relying on it or auditing it.", "outputs.last_rendered_digest")

    claim_ids, claim_dups = _ids(camp.get("claims", []))
    if claim_dups:
        issue("error", "claim.duplicate", f"Duplicate claim IDs: {', '.join(claim_dups)}", "campaign.claims")
    for index, claim in enumerate(camp.get("claims", [])):
        path = f"campaign.claims.{index}"
        if claim.get("inquiry_id") not in inquiry_ids:
            issue("error", "claim.bad_inquiry_ref", f"Claim {claim.get('id')} references unknown inquiry", path)
        claim_checks = {
            "statement": _required_text, "support": _required_list,
            "counterevidence_or_objections": _required_list, "verification": _required_text,
            "status": _required_text, "reporting_rule": _required_text,
        }
        for field, check in claim_checks.items():
            if not check(claim.get(field)):
                issue("error", "claim.incomplete", f"Claim {claim.get('id', index)} missing {field}", path)

    deliverable_ids, deliverable_dups = _ids(camp.get("deliverables", []))
    if deliverable_dups:
        issue("error", "deliverable.duplicate", f"Duplicate deliverable IDs: {', '.join(deliverable_dups)}", "campaign.deliverables")
    if not deliverable_ids:
        issue("error", "deliverable.none", "At least one deliverable is required", "campaign.deliverables")
    for index, item in enumerate(camp.get("deliverables", [])):
        for field in ("name", "path", "acceptance_test", "owner"):
            if not _required_text(item.get(field)):
                issue("error", "deliverable.incomplete", f"Deliverable {item.get('id', index)} missing {field}", f"campaign.deliverables.{index}")

    reporting = camp.get("reporting", {})
    if not _required_text(reporting.get("negative_result_policy")) \
            or not _required_text(reporting.get("deviation_policy")):
        issue("error", "reporting.incomplete", "Negative-result and deviation policies are required", "campaign.reporting")

    kickoff = camp.get("kickoff", {})
    if not _required_text(kickoff.get("command")):
        issue("error", "kickoff.no_command", "Kickoff command is missing; the bundle would ship an empty KICKOFF.md", "campaign.kickoff.command")
    if not _required_text(kickoff.get("first_gate_id")):
        issue("error", "kickoff.no_gate", "Kickoff must name the first executable gate", "campaign.kickoff.first_gate_id")
    elif kickoff.get("first_gate_id") not in gate_ids:
        issue("error", "kickoff.bad_gate", f"Kickoff references unknown gate {kickoff.get('first_gate_id')}", "campaign.kickoff.first_gate_id")
    if not _required_list(ethics.get("constraints")):
        issue("error", "ethics.none", "Ethics, rights, and safety constraints are required; record 'not applicable' with a reason if genuinely none", "campaign.ethics_rights_safety.constraints")

    for index, contradiction in enumerate(state.get("contradictions", [])):
        if not isinstance(contradiction, dict):
            issue("error", "contradiction.malformed",
                  f"contradictions[{index}] must be an object, not {type(contradiction).__name__}; "
                  "see `rescamp.py schema contradictions`", f"contradictions.{index}")
            continue
        if contradiction.get("status", "open") == "open" and contradiction.get("importance", "material") in {"critical", "material"}:
            issue("error", "contradiction.open", f"Open material contradiction {contradiction.get('id', index)}", f"contradictions.{index}")
    for index, blocker in enumerate(state.get("blockers", [])):
        if not isinstance(blocker, dict):
            issue("error", "blocker.malformed",
                  f"blockers[{index}] must be an object, not {type(blocker).__name__}; "
                  "see `rescamp.py schema blockers`", f"blockers.{index}")
    critical_blockers = [item for item in state.get("blockers", [])
                         if isinstance(item, dict) and item.get("status", "open") == "open"
                         and item.get("severity") in {"major", "critical"}]
    for item in critical_blockers:
        issue("error", "blocker.open", f"Open {item.get('severity')} blocker {item.get('id', '')}: {item.get('description', '')}", "blockers")

    review_summary: dict[str, Any] = {"required": [], "current": [], "missing": [], "blocking": [], "independence_ok": True}
    if include_reviews:
        current_content = input_digest
        current_rubric = rubric_digest(profile)
        records = state.get("reviews", {}).get("records", [])
        leaves = section_digests(state)
        valid_records = [item for item in records if record_is_current(item, state, leaves)]
        role_map = {item.get("role"): item for item in valid_records if item.get("role")}
        required = PROFILES[profile]["review_roles"]
        missing = [role for role in required if role not in role_map]
        blocking = [role for role, item in role_map.items() if role in required and item.get("verdict") != "pass"]
        review_summary.update({"required": required, "current": sorted(role_map), "missing": missing, "blocking": blocking})
        if missing:
            issue("error", "review.missing", "Missing current reviews: " + ", ".join(missing), "reviews.records")
        if blocking:
            issue("error", "review.blocking", "Non-passing required reviews: " + ", ".join(blocking), "reviews.records")
        acceptances = assurance.get("risk_acceptances", [])
        if not isinstance(acceptances, list):
            issue("error", "risk_acceptance.malformed", "risk_acceptances must be a list",
                  "assurance.risk_acceptances")
            acceptances = []
        current_acceptances = [item for item in acceptances if isinstance(item, dict)
                               and item.get("content_digest") == current_content]
        # A verdict is only a review summary. Major and critical findings remain
        # blocking until a different, authorized actor accepts that exact finding.
        for role, record in sorted(role_map.items()):
            for finding in record.get("findings", []):
                severity = finding.get("severity")
                if severity not in {"major", "critical"}:
                    continue
                digest = finding_digest(role, finding)
                accepted = any(
                    item.get("finding_digest") == digest
                    and _nonempty(item.get("accepted_by"))
                    and item.get("accepted_by") != record.get("reviewer_id")
                    and _nonempty(item.get("authority"))
                    and _is_iso_timestamp(item.get("accepted_at"))
                    and _nonempty(item.get("scope"))
                    and _nonempty(item.get("evidence"))
                    for item in current_acceptances
                )
                if accepted:
                    continue
                code = ("risk_acceptance.missing" if finding.get("action") == "accepted-risk"
                        else f"review.unresolved_{severity}")
                issue("error", code,
                      f"Review {role} records an unresolved {severity} finding "
                      f"({finding.get('action', 'unclassified')}): {finding.get('description', '')}. "
                      f"Separate acceptance must bind finding {digest} to the current campaign digest.",
                      "reviews.records")
                if record.get("verdict") == "pass":
                    issue("warning", "review.verdict_conflict",
                          f"Review {role} returned verdict 'pass' while recording a {severity} finding",
                          "reviews.records")
        review_summary["attested_modes"] = {role: item.get("mode") for role, item in sorted(role_map.items())}
        review_summary["independence_is_self_attested"] = True
        if PROFILES[profile]["independent_required"]:
            bad_modes = [role for role in required if role in role_map and role_map[role].get("mode") not in INDEPENDENCE_CLAIMING_MODES]
            identities = [role_map[role].get("reviewer_id") for role in required if role in role_map]
            distinct = len(set(identities)) == len(identities) and all(identities)
            # Distinct executors as well as distinct names: one process relabelled twice
            # is a sequential pass wearing two hats.
            executors = [(role_map[role].get("execution_evidence") or {}).get("executor_id")
                         for role in required if role in role_map]
            distinct_executors = len(set(executors)) == len(executors) and all(executors)
            if bad_modes or not distinct:
                review_summary["independence_ok"] = False
                issue("error", "review.independence", "High-assurance review requires separately executed, distinctly identified reviewers", "reviews.records")
            elif not distinct_executors:
                review_summary["independence_ok"] = False
                issue("error", "review.independence_evidence",
                      "High-assurance reviews must record distinct execution_evidence.executor_id per reviewer",
                      "reviews.records")
        elif profile == "standard":
            sequential = [item for item in role_map.values() if item.get("mode") == "sequential-pass"]
            if sequential:
                issue("warning", "review.sequential", "Standard review used sequential passes; disclose limited independence", "reviews.records")

    execution_blocking_prefixes = (
        "pilot.", "review.", "risk_acceptance.", "approval.", "external_action.", "outputs.stale",
    )
    plan_ready = bool(errors) and all(
        item["code"].startswith(execution_blocking_prefixes)
        or (item["code"] == "interview.not_executable"
            and interview.get("stopping_reason") == "blocked-by-external-dependency")
        for item in errors
    )
    release_status = "execution-ready" if not errors else (
        "plan-ready-execution-blocked" if plan_ready else "draft"
    )
    result = {
        "rescamp_version": VERSION,
        "checked_at": now_iso(),
        "content_digest": input_digest,
        "rubric_digest": rubric_digest(profile),
        "valid": not errors,
        "execution_ready": not errors,
        "release_status": release_status,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "interview_turns": len(turns), "intent_dimensions": len(dimension_ids),
            "inquiries": len(inquiry_ids), "methods": len(method_ids), "tools": len(tool_ids),
            "canaries": len(canary_ids), "stages": len(stage_ids), "gates": len(gate_ids),
            "work_units": len(work_unit_ids), "claims": len(claim_ids), "deliverables": len(deliverable_ids),
        },
        "review": review_summary,
    }
    return result


def classify_validation_findings(result: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {
        "agent-fix": [], "user-answer": [], "external-approval": [], "accepted-risk": []
    }
    for item in result.get("errors", []) + result.get("warnings", []):
        code = item.get("code", "")
        if code.startswith(("approval.", "blocker.")):
            action = "external-approval"
        elif code.startswith(("dimension.unresolved", "contradiction.", "mission.missing", "dossier.objects", "interview.hard_limit")):
            action = "user-answer"
        elif code.startswith("review."):
            action = "external-approval" if code == "review.independence" else "agent-fix"
        else:
            action = "agent-fix"
        # Codes and paths only: the full text of every finding is already in
        # `deterministic_validation.errors` in the same payload, and duplicating it made
        # this block ~39% of the largest stdout a driving agent ever reads.
        grouped[action].append({"code": item.get("code", ""), "path": item.get("path", "")})
    return grouped


FINDING_PREVIEW = 10
STDOUT_FINDING_CAP = 25


def summarize_findings(grouped: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    """Counts plus a preview. The full list is already in `deterministic_validation` and on
    disk; re-listing every finding a second time made this the largest stdout an agent
    ever reads, and on a large campaign with a systematic mistake it dominated the turn."""
    out: dict[str, Any] = {}
    for action, items in grouped.items():
        entry: dict[str, Any] = {"count": len(items), "paths": [i["path"] for i in items[:FINDING_PREVIEW]]}
        if len(items) > FINDING_PREVIEW:
            entry["truncated"] = len(items) - FINDING_PREVIEW
        out[action] = entry
    return out


def cap_validation_for_stdout(result: dict[str, Any]) -> dict[str, Any]:
    """Trim the findings arrays for printing. `working/validation.json` keeps everything."""
    trimmed = dict(result)
    for key in ("errors", "warnings"):
        items = result.get(key, [])
        if len(items) > STDOUT_FINDING_CAP:
            trimmed[key] = items[:STDOUT_FINDING_CAP] + [{
                "code": "output.truncated",
                "message": f"{len(items) - STDOUT_FINDING_CAP} more {key} in working/validation.json",
                "path": "",
            }]
    return trimmed


def cmd_validate(args: argparse.Namespace) -> None:
    campaign_dir = resolve_campaign(args.campaign)
    state = load_state(campaign_dir)
    result = validate_state(state, include_reviews=not args.no_reviews)
    state["last_validation"] = result
    write_json(campaign_dir / VALIDATION_REL, result)
    write_json(campaign_dir / STATE_REL, state)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.strict and not result["valid"]:
        raise SystemExit(2)


# What each reviewer role actually has to read. Shipping the whole campaign to every
# reviewer made a methods reviewer read the runtime config and the interview transcript,
# and cost ~16k tokens per role per round. A record still binds to the digest of the full
# frozen campaign, so scoping changes what is *shown*, never what is attested against.
ROLE_SCOPES: dict[str, dict[str, Any]] = {
    "methods-evidence": {
        "sections": ("mission", "dossier", "inquiries", "methods", "evaluation", "claims"),
        "top_level": ("goal_verbatim", "profile", "archetypes", "sketch", "assumptions",
                      "contradictions", "intent_dimensions"),
        "note": "Methods and evidence logic. Operations sections are omitted by design; do not infer they are absent.",
    },
    "operations-reproducibility": {
        # ethics_rights_safety is here so that the two standard-profile roles between them
        # cover every campaign section. Without it a change to consent, rights, or approval
        # boundaries would invalidate nobody's review at `standard`.
        "sections": ("constitution", "tools", "canaries", "stages", "gates", "resources_dispatch",
                     "roles", "runtime", "work_units", "deliverables", "kickoff", "reporting",
                     "ethics_rights_safety"),
        "top_level": ("goal_verbatim", "profile", "archetypes", "blockers", "assurance"),
        "note": "Operations, reproducibility, and the approval and external-action boundaries. Inquiry and method detail is omitted by design; do not infer it is absent.",
    },
    "ethics-claim-integrity": {
        "sections": ("mission", "dossier", "ethics_rights_safety", "reporting", "claims",
                     "inquiries", "deliverables", "resources_dispatch"),
        "top_level": ("goal_verbatim", "profile", "archetypes", "blockers", "contradictions"),
        "note": "Ethics, rights, safety, and claim integrity.",
    },
}


# Cross-section references. A reviewer who saw section X is also reviewing, implicitly,
# the objects X points at: a gate's criteria can name a method, a claim names an inquiry.
# A record therefore goes stale when a referenced section moves, not only when its own does.
SECTION_REFERENCES: dict[str, tuple[str, ...]] = {
    "methods": ("inquiries",),
    "claims": ("inquiries",),
    "canaries": ("tools",),
    "stages": ("gates", "methods", "tools"),
    # Gate criteria routinely name a method or an inquiry by id, so gutting a method must
    # reach whoever approved the gate that depends on it. These are the cross-scope edges;
    # without them the closure was inert and the justification for the table was untrue.
    "gates": ("stages", "methods", "inquiries"),
    "kickoff": ("gates",),
    "work_units": ("deliverables", "methods", "gates", "stages"),
    "evaluation": ("methods", "inquiries"),
}


def invalidation_sections(role: str, campaign: dict[str, Any],
                          leaf_names: Iterable[str] = ()) -> frozenset[str]:
    """Sections whose change makes this role's review stale.

    The role's own packet sections, closed under SECTION_REFERENCES. A role with no scope
    entry reviews the whole campaign and is invalidated by any section.
    """
    scope = ROLE_SCOPES.get(role)
    if scope is None:
        # An unscoped role reviews the whole campaign and is bound to all of it.
        return frozenset(campaign) | {name for name in leaf_names if name.startswith("@")}
    pending = list(scope["sections"])
    seen: set[str] = set()
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        pending.extend(SECTION_REFERENCES.get(name, ()))
    bound = {name for name in seen if name in campaign}
    bound |= {f"@{name}" for name in scope["top_level"] if f"@{name}" in leaf_names}
    return frozenset(bound)


# State a review is deliberately not bound to. `interview` and `content_version` are the
# whole point of per-section binding: recording a turn must not invalidate a methodology
# review. The rest is engine bookkeeping that no reviewer is shown or asked to judge.
UNBOUND_TOP_LEVEL = frozenset({
    "campaign", "interview", "content_version", "updated_at",
    "title", "campaign_id", "created_at", "schema_version", "rescamp_version",
})


def section_digests(state: dict[str, Any]) -> dict[str, str]:
    """One digest per reviewable unit — the leaves under `content_digest`'s root.

    Campaign sections are keyed by name; top-level state is keyed with a leading `@`.
    Binding only `campaign.*` would leave `goal_verbatim`, `sketch`, `assumptions`,
    `contradictions` and `blockers` unbound even though they are shipped inside review
    packets, so a review would attest to text anyone could rewrite afterwards.

    `content_digest` still fingerprints everything for the manifest and audit. These
    leaves exist so staleness can answer *which part moved* instead of discarding every
    review because an unrelated part changed.
    """
    frozen = substantive_state(state, deep=False)
    leaves = {name: sha256_json(value) for name, value in frozen.get("campaign", {}).items()}
    for name, value in frozen.items():
        if name not in UNBOUND_TOP_LEVEL:
            leaves[f"@{name}"] = sha256_json(value)
    return leaves


def record_is_current(record: dict[str, Any], state: dict[str, Any], leaves: dict[str, str] | None = None) -> bool:
    """Is this review record still bound to what it actually reviewed?

    Records carrying `reviewed_sections` are checked per section. Records carrying only a
    whole-campaign `content_digest` fall back to the old all-or-nothing rule, which is
    strictly stronger, so older records stay valid rather than silently expiring.
    """
    if record.get("rubric_digest") != rubric_digest(state["profile"]):
        return False
    reviewed = record.get("reviewed_sections")
    if not isinstance(reviewed, dict):
        return record.get("content_digest") == content_digest(state)
    if not str(record.get("content_digest", "")).startswith("sha256:"):
        return False
    current = leaves if leaves is not None else section_digests(state)
    campaign = substantive_state(state, deep=False).get("campaign", {})
    required = invalidation_sections(record.get("role", ""), campaign, current)
    # The record must cover exactly the sections its role is responsible for: a record
    # that omits a section could otherwise never be invalidated by a change to it.
    if set(reviewed) != set(required):
        return False
    return all(current.get(name) == digest for name, digest in reviewed.items())


def scope_packet_for_role(frozen: dict[str, Any], role: str) -> dict[str, Any]:
    """Project the frozen campaign down to what this role reviews.

    An unknown role (including `skeptical`, which reviews everything) gets the full state.
    """
    scope = ROLE_SCOPES.get(role)
    if scope is None:
        return frozen
    campaign = frozen.get("campaign", {})
    projected = {key: value for key, value in campaign.items() if key in scope["sections"]}
    result = {key: frozen[key] for key in scope["top_level"] if key in frozen}
    result["campaign"] = projected
    return result


def freeze_and_packets(campaign_dir: Path, state: dict[str, Any]) -> tuple[str, str, list[Path]]:
    digest = content_digest(state)
    r_digest = rubric_digest(state["profile"])
    leaves = section_digests(state)
    state["reviews"]["frozen_content_digest"] = digest
    state["reviews"]["rubric_digest"] = r_digest
    state["reviews"]["section_digests"] = leaves
    # Records for sections that did not move survive the re-freeze: a repair to one
    # section no longer forces every reviewer to start over.
    state["reviews"]["records"] = [
        item for item in state["reviews"].get("records", [])
        if record_is_current(item, state, leaves)
    ]
    packet_dir = campaign_dir / REVIEW_DIR_REL
    if packet_dir.exists():
        shutil.rmtree(packet_dir)
    packet_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    frozen = substantive_state(state)
    campaign_sections = frozen.get("campaign", {})
    for role in PROFILES[state["profile"]]["review_roles"]:
        scoped = scope_packet_for_role(frozen, role)
        packet = {
            "packet_version": "1.0",
            "campaign_id": state["campaign_id"],
            "role": role,
            "content_version": state["content_version"],
            "content_digest": digest,
            "rubric": rubric_payload(state["profile"]),
            "rubric_digest": r_digest,
            "instructions": {
                "read_only": True,
                "evaluate_least_favorable_defensible_interpretation": True,
                "do_not_edit_canonical_state": True,
                # Absolute: a reviewer running as a separate process on any host must be
                # able to resolve this without knowing the skill's install location.
                "required_output_schema": str(SKILL_DIR / "assets/review.schema.json"),
                "scope_note": ROLE_SCOPES.get(role, {}).get("note", "Full campaign."),
            },
            "scoped_sections": sorted(scoped.get("campaign", {})),
            # Copy this into the review record verbatim as `reviewed_sections`. It binds
            # the record to the sections it actually reviewed, so a later repair elsewhere
            # in the campaign does not throw this review away.
            "reviewed_sections": {name: leaves[name]
                                  for name in sorted(invalidation_sections(role, campaign_sections, leaves))
                                  if name in leaves},
            "campaign": scoped,
        }
        path = packet_dir / f"{role}.json"
        write_json(path, packet)
        paths.append(path)
    save_state(campaign_dir, state)
    return digest, r_digest, paths


def cmd_quality_loop(args: argparse.Namespace) -> None:
    campaign_dir = resolve_campaign(args.campaign)
    state = load_state(campaign_dir)
    pre = validate_state(state, include_reviews=False)
    write_json(campaign_dir / VALIDATION_REL, pre)
    digest, r_digest, paths = freeze_and_packets(campaign_dir, state)
    state = load_state(campaign_dir)
    still_current, needs_review = review_status(state)
    payload = {
        "completed_by_this_command": ["deterministic_validation", "content_freeze", "review_packets_written",
                                      "findings_classified"],
        "not_run_by_this_command": ["reviewer_execution", "defect_repair"],
        "phase": "awaiting-review-execution" if pre["valid"] else "awaiting-design-repair",
        "reviews_ingested": len(state.get("reviews", {}).get("records", [])),
        "content_digest": digest,
        "rubric_digest": r_digest,
        "deterministic_validation": cap_validation_for_stdout(pre),
        "findings_by_action": summarize_findings(classify_validation_findings(pre)),
        "review_packets_are_inputs": True,
        "review_packets_to_execute": [str(path) for path in paths
                                      if path.stem in needs_review],
        "review_packets_all": [str(path) for path in paths],
        "reviews_still_current": still_current,
        "roles_requiring_review": needs_review,
        "next_action": "Resolve deterministic errors before review" if not pre["valid"] else _review_next_action(needs_review),
    }
    write_json(campaign_dir / "working/quality_loop.json", payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def review_status(state: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Which required reviews survived the freeze, and which must actually be re-run."""
    held = {item.get("role") for item in state.get("reviews", {}).get("records", [])}
    required = PROFILES[state["profile"]]["review_roles"]
    return sorted(role for role in required if role in held), sorted(role for role in required if role not in held)


def _review_next_action(needs_review: list[str]) -> str:
    if not needs_review:
        return "All required reviews are current; run finalize"
    return ("Execute only these review packets as separate read-only reviewers, ingest each record, then finalize: "
            + ", ".join(needs_review))


def review_record_errors(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("role", "reviewer_id", "mode", "verdict", "content_digest", "rubric_digest", "summary"):
        if not _nonempty(record.get(field)):
            errors.append(f"missing {field}")
    # `findings` is required but may legitimately be empty: a reviewer that found
    # nothing must not be pushed into inventing a filler finding to pass.
    if "findings" not in record:
        errors.append("missing findings")
    if record.get("mode") not in REVIEW_MODES:
        errors.append("invalid mode")
    elif record["mode"] in INDEPENDENCE_CLAIMING_MODES:
        evidence = record.get("execution_evidence")
        if not isinstance(evidence, dict):
            errors.append(f"mode {record['mode']} requires execution_evidence (self-attested; recorded for audit)")
        else:
            for field in ("executor_id", "started_at", "completed_at"):
                if not _nonempty(evidence.get(field)):
                    errors.append(f"execution_evidence missing {field}")
    if record.get("verdict") not in REVIEW_VERDICTS:
        errors.append("invalid verdict")
    if not isinstance(record.get("findings"), list):
        errors.append("findings must be a list")
    else:
        for index, finding in enumerate(record["findings"]):
            if finding.get("severity") not in SEVERITIES:
                errors.append(f"finding {index} invalid severity")
            if finding.get("action") not in FINDING_ACTIONS:
                errors.append(f"finding {index} invalid action")
            if not _nonempty(finding.get("description")):
                errors.append(f"finding {index} missing description")
    return errors


def cmd_ingest_review(args: argparse.Namespace) -> None:
    campaign_dir = resolve_campaign(args.campaign)
    state = load_state(campaign_dir)
    record = read_json(Path(args.file))
    errors = review_record_errors(record)
    if errors:
        raise SystemExit("Invalid review record:\n- " + "\n- ".join(errors))
    required = PROFILES[state["profile"]]["review_roles"]
    if record["role"] not in required:
        raise SystemExit(f"Unexpected review role {record['role']}; required: {', '.join(required)}")
    current_rubric = rubric_digest(state["profile"])
    if not record_is_current(record, state):
        detail = []
        if record.get("rubric_digest") != current_rubric:
            detail.append(f"  rubric_digest:  record has {record.get('rubric_digest')}\n"
                          f"                  campaign is {current_rubric}\n"
                          "                  the review rubric changed; re-run the review under the current rubric")
        reviewed = record.get("reviewed_sections")
        if isinstance(reviewed, dict):
            leaves = section_digests(state)
            campaign = substantive_state(state, deep=False).get("campaign", {})
            expected = invalidation_sections(record["role"], campaign, leaves)
            if set(reviewed) != set(expected):
                detail.append(f"  reviewed_sections: record covers {sorted(reviewed)}\n"
                              f"                     role requires {sorted(expected)}\n"
                              "                     copy `reviewed_sections` from the review packet verbatim")
            moved = sorted(name for name, digest in reviewed.items() if leaves.get(name) != digest)
            if moved:
                detail.append(f"  changed sections: {', '.join(moved)}\n"
                              "                     these moved after the review; re-run it against the current freeze")
        elif record.get("content_digest") != content_digest(state):
            detail.append(f"  content_digest: record has {record.get('content_digest')}\n"
                          f"                  campaign is {content_digest(state)}\n"
                          "                  the campaign changed after this review; re-run it against the current freeze")
        raise SystemExit("Review does not match the current freeze:\n" + "\n".join(detail))
    records = [item for item in state["reviews"].get("records", []) if item.get("role") != record["role"]]
    record["ingested_at"] = now_iso()
    records.append(record)
    state["reviews"]["records"] = records
    save_state(campaign_dir, state)
    print(record["role"])


def _md_list(values: Any, fallback: str = "- None recorded") -> str:
    """Render a list of scalars as bullets. Structured objects go through _render_objects."""
    if not values:
        return fallback
    lines: list[str] = []
    for item in values:
        if isinstance(item, dict):
            ident = item.get("id") or item.get("name") or item.get("label") or "item"
            desc = item.get("description") or item.get("statement") or item.get("purpose") or item.get("value")
            lines.append(f"- **{ident}:** {desc}" if desc else f"- **{ident}**")
        else:
            lines.append(f"- {item}")
    return "\n".join(lines)


def _humanize(key: str) -> str:
    return key.replace("_", " ").replace(" ids", " IDs").capitalize()


def _fmt_value(value: Any, indent: str = "  ") -> str:
    """Format one field value as markdown: scalars inline, collections as nested bullets."""
    if value is None or value == "" or value == [] or value == {}:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        rows = [f"\n{indent}- **{_humanize(k)}:** {_fmt_value(v, indent + '  ')}" for k, v in value.items() if _displayable(v)]
        return "".join(rows)
    if isinstance(value, list):
        rows = []
        for item in value:
            if isinstance(item, (dict, list)):
                rows.append(f"\n{indent}- {_fmt_value(item, indent + '  ').lstrip()}")
            else:
                rows.append(f"\n{indent}- {item}")
        return "".join(rows)
    return str(value)


def _labelled(label: str, value: Any) -> str:
    """One `- **Label:** value` bullet, without a trailing space before a nested list."""
    rendered = _fmt_value(value)
    separator = "" if rendered.startswith("\n") else " "
    return f"- **{label}:**{separator}{rendered}".rstrip()


def _render_objects(items: Any, path: str, heading: str = "###", fallback: str = "*None recorded.*") -> str:
    """Render structured campaign objects as readable, complete markdown blocks.

    Every field present on the object is rendered: spec-declared fields first in
    declaration order, then any additional keys. Nothing is silently dropped and
    nothing is dumped as raw JSON.
    """
    if not items:
        return fallback
    spec = spec_for(path)
    if spec is None or not any(isinstance(item, dict) for item in items):
        # Plain scalar lists stay as bullets; only structured objects get blocks.
        return _md_list(items, fallback)
    title_key = spec["title"]
    ordered = [name for name, _ in spec["fields"]]
    labels = dict(spec["fields"])
    blocks: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            blocks.append(f"{heading} {item}")
            continue
        ident = str(item.get("id") or f"{spec['label']}-{index + 1}")
        # Only a scalar makes a usable heading; a list-valued title field is
        # rendered as an ordinary labelled field instead of a Python repr.
        candidate = item.get(title_key) or item.get("name") or item.get("description")
        title = str(candidate).strip() if isinstance(candidate, (str, int, float)) else ""
        blocks.append(f"{heading} {ident}" + (f" — {title}" if title else ""))
        rendered_keys = {"id"} | ({title_key} if title else set())
        lines: list[str] = []
        for key in ordered:
            if key in rendered_keys or not _displayable(item.get(key)):
                continue
            rendered_keys.add(key)
            lines.append(_labelled(labels.get(key, _humanize(key)), item[key]))
        for key in item:
            if key in rendered_keys or not _displayable(item[key]):
                continue
            lines.append(_labelled(_humanize(key), item[key]))
        missing = [key for key in spec["required"] if not _nonempty(item.get(key))]
        if missing:
            lines.append(f"- **INCOMPLETE — missing required:** {', '.join(missing)}")
        blocks.append("\n".join(lines) if lines else "*No fields recorded.*")
    return "\n\n".join(blocks)


def _section(title: str, body: str) -> str:
    return f"\n## {title}\n\n{body.strip()}\n"


def _coverage_note(state: dict[str, Any]) -> str:
    """Deterministic checks verify presence and cross-references, never substance.
    An execution-ready bundle must therefore disclose what it left empty rather than
    let a thin campaign read as a complete one."""
    camp = state["campaign"]
    optional = [("tools", "production tools"), ("canaries", "tool canaries"), ("roles", "named roles"),
                ("work_units", "bounded work units"), ("claims", "recorded claims")]
    empty = [label for key, label in optional if not camp.get(key)]
    lines = ["You are executing a compiled research campaign. Read every section before acting; "
             "section 16 is the kickoff.", ""]
    lines.append(f"**Sections left empty:** {', '.join(empty) if empty else 'none'}. "
                 "Empty is legitimate when the section cannot change the research decision — "
                 "an archival study has no production tools — but it is never evidence of coverage.")
    lines.append("")
    reviews = state.get("reviews", {}).get("records", [])
    modes = sorted({record.get("mode", "") for record in reviews}) if reviews else []
    lines.append(f"**Challenge applied:** {', '.join(modes) if modes else 'none ingested'}. "
                 "Independence is self-attested; agent review checks internal coherence and is not "
                 "external validation.")
    pilot = state.get("assurance", {}).get("pilot", {})
    if isinstance(pilot, dict) and pilot.get("status") == "passed":
        lines.append(
            f"**Pilot:** passed against `{pilot.get('content_digest', 'unrecorded digest')}`; "
            f"scope: {pilot.get('scope', 'unrecorded')}; resource cap: "
            f"{pilot.get('resource_cap', 'unrecorded')}; executor: {pilot.get('executor_id', 'unrecorded')}. "
            "Execution authority is recorded as an attestation, not independently proven."
        )
    elif state.get("profile") == "high-assurance" or state.get("assurance", {}).get("pilot_required") is True:
        lines.append("**Pilot:** required but no passing current pilot is recorded; execution remains blocked.")
    else:
        lines.append("**Pilot:** not required and not recorded; this is reviewed-static plan evidence only.")
    lines.append("")
    lines.append("Deterministic validation checked presence, cross-references, and budgets. It did not "
                 "judge whether any statement here is true, sufficient, or wise.")
    return "\n".join(lines)


def render_campaign_prompt(state: dict[str, Any], status: str) -> str:
    camp = state["campaign"]
    mission = camp["mission"]
    header = f"# Research Campaign Prompt: {state['title']}\n\n**Status:** {status}\n\n**Campaign ID:** `{state['campaign_id']}`  \n**Content version:** {state['content_version']}  \n**Content digest:** `{content_digest(state)}`  \n**Profile:** {state['profile']}  \n**Archetypes:** {', '.join(state['archetypes'])}\n"
    parts = [header, _section("0. Coverage and standing caveats", _coverage_note(state))]
    parts.append(_section("1. Campaign constitution", _md_list(camp["constitution"].get("rules")) + "\n\nEvery worker inherits these rules. Local briefs may narrow scope but may not weaken them."))
    parts.append(_section("2. Mission, boundaries, and deliverables", f"**Decision or purpose:** {mission.get('decision_or_purpose','')}\n\n**Scope:** {mission.get('scope','')}\n\n**Non-goals**\n{_md_list(mission.get('non_goals'))}\n\n**Intended users**\n{_md_list(mission.get('intended_users'))}\n\n**Completion definition:** {mission.get('completion_definition','')}\n\n**Deliverables**\n\n{_render_objects(camp.get('deliverables'), 'campaign.deliverables')}"))
    dossier = camp["dossier"]
    parts.append(_section("3. Object and evidence dossier", f"**Objects, cases, corpus, population, or system**\n\n{_render_objects(dossier.get('objects'), 'campaign.dossier.objects')}\n\n**Context**\n\n{_render_objects(dossier.get('context'), 'campaign.dossier.context')}\n\n**Source hierarchy**\n\n{_render_objects(dossier.get('source_hierarchy'), 'campaign.dossier.source_hierarchy')}\n\n**Access and rights**\n\n{_render_objects(dossier.get('access_rights'), 'campaign.dossier.access_rights')}\n\n**Known alternatives**\n\n{_render_objects(dossier.get('alternatives'), 'campaign.dossier.alternatives')}"))
    parts.append(_section("4. Inquiry and evidence logic", "Each inquiry must be evaluated against admissible support and explicit counterevidence, rival explanations/readings, counterexamples, or objections.\n\n" + _render_objects(camp.get("inquiries"), "campaign.inquiries")))
    parts.append(_section("5. Method portfolio", _render_objects(camp.get("methods"), "campaign.methods")))
    parts.append(_section("6. Tools and production-like canaries", f"**Tools**\n\n{_render_objects(camp.get('tools'), 'campaign.tools')}\n\n**Canaries**\n\nA successful import or help command is not a canary.\n\n{_render_objects(camp.get('canaries'), 'campaign.canaries')}"))
    evaluation = camp["evaluation"]
    parts.append(_section("7. Frozen evaluation or adjudication instrument", f"**Frozen before production (asserted, not verified):** {evaluation.get('frozen_before_production_asserted')}\n\n**Criteria**\n{_md_list(evaluation.get('criteria'))}\n\n**Comparators, controls, cases, or adjudication rules**\n{_md_list(evaluation.get('comparators_or_adjudication'))}\n\n**Missing-evidence policy:** {evaluation.get('missing_evidence_policy','')}\n\n**Exploration versus confirmation:** {evaluation.get('exploration_confirmation_policy','')}\n\n**Stop, pivot, and no-go rules**\n{_md_list(evaluation.get('stop_pivot_no_go_rules'))}"))
    parts.append(_section("8. Staged funnel and promotion gates", f"**Stages**\n\n{_render_objects(camp.get('stages'), 'campaign.stages')}\n\n**Gates**\n\n{_render_objects(camp.get('gates'), 'campaign.gates')}"))
    resources = camp["resources_dispatch"]
    parts.append(_section("9. Resources and fail-closed dispatch", f"**Budgets**\n{_md_list(resources.get('budgets'))}\n\n**Access constraints**\n{_md_list(resources.get('access_constraints'))}\n\n**Concurrency:** {resources.get('concurrency','')}\n\n**Dispatch rules**\n{_md_list(resources.get('dispatch_rules'))}\n\n**Approvals**\n{_md_list(resources.get('approvals'))}"))
    parts.append(_section("10. Delegation", f"**Roles**\n\n{_render_objects(camp.get('roles'), 'campaign.roles')}\n\n**Bounded work units**\n\nDelegates return artifacts and concise findings, not unbounded narrative. A local brief may narrow scope but may not weaken the constitution.\n\n{_render_objects(camp.get('work_units'), 'campaign.work_units')}"))
    runtime = camp["runtime"]
    parts.append(_section("11. Durable operations and recovery", f"**Continuous runtime enabled:** {runtime.get('enabled')}\n\n**Continuation trigger:** {runtime.get('continuation_trigger','')}\n\n**State store:** {runtime.get('state_store','')}\n\n**Event log:** {runtime.get('event_log','')}\n\n**Checkpoint policy:** {runtime.get('checkpoint_policy','')}\n\n**Liveness:** {runtime.get('liveness','')}\n\n**Recovery:** {runtime.get('recovery','')}\n\n**Idempotency:** {runtime.get('idempotency','')}\n\nA conversational session is not a scheduler."))
    ethics = camp["ethics_rights_safety"]
    parts.append(_section("12. Ethics, safety, rights, and external actions", f"**Constraints**\n{_md_list(ethics.get('constraints'))}\n\n**External actions**\n{_md_list(ethics.get('external_actions'))}\n\n**Human approval points**\n{_md_list(ethics.get('human_approval_points'))}"))
    reporting = camp["reporting"]
    parts.append(_section("13. Reporting and claim discipline", f"**Claim rules**\n{_md_list(reporting.get('claim_rules'))}\n\n**Negative/null/failed result policy:** {reporting.get('negative_result_policy','')}\n\n**Deviation policy:** {reporting.get('deviation_policy','')}\n\nLead with the least favorable defensible interpretation.\n\n**Recorded claims**\n\n{_render_objects(camp.get('claims'), 'campaign.claims')}"))
    closeout = ("Validate schemas and references, recompute judgments from raw artifacts where possible, verify every "
                "acceptance test below, disclose deviations and blockers, hash deliverables, and produce a reproducible "
                "handoff. Completion is fail-closed.\n\nOnce a ranked or selected deliverable is frozen there is no "
                "post-hoc re-ranking, re-selection, or quiet substitution; anything selected after close is reported "
                "separately and excluded from the primary result.\n\n**Acceptance tests that must pass**\n\n"
                + _render_objects(camp.get("deliverables"), "campaign.deliverables"))
    parts.append(_section("14. Transactional closeout", closeout))
    review_lines = []
    for record in state.get("reviews", {}).get("records", []):
        review_lines.append(f"- **{record.get('role')}:** {record.get('verdict')} — {record.get('summary')} (mode: {record.get('mode')}, reviewer: {record.get('reviewer_id')})")
    # Ordinal first, label derived. Comparing display strings made an unrecognized mode
    # ("unknown") sort above "4 — human domain expert".
    rungs = {"sequential-pass": (1, "sequential self-critique (no independence)"),
             "independent-subagent": (2, "separate agent context"),
             "separate-session": (2, "separate session"),
             "external-human": (4, "human domain expert")}
    reached = [rungs.get(record.get("mode"), (0, "unrecognized mode"))
               for record in state.get("reviews", {}).get("records", [])]
    top = min(reached, default=None)  # the weakest rung bounds the claim, not the strongest
    highest = f"{top[0]} — {top[1]}" if top else None
    challenge = ("Reviewers are read-only and bound to the frozen content and rubric digests.\n\n"
                 f"**Weakest independence rung among required reviews:** {highest or 'none — no reviews ingested'}\n\n"
                 "The weakest rung bounds the challenge, not the strongest: one sequential pass in the set "
                 "means the set is only as independent as that pass.\n\n"
                 "Rungs: 1 sequential self-critique < 2 separate agent context < 3 separate agent blinded to "
                 "conclusions < 4 human domain expert < 5 external adjudicator with its own data. Rungs 1–3 are "
                 "agent review: they check internal coherence and are **not** external validation. The mode is "
                 "self-attested — recorded for audit, never proven.\n\n"
                 + ("\n".join(review_lines) if review_lines else "- Required reviews are not yet complete."))
    parts.append(_section("15. Independent challenge", challenge))
    kickoff = camp["kickoff"]
    parts.append(_section("16. Kickoff", f"**Command:** {kickoff.get('command','')}\n\n**First gate:** {kickoff.get('first_gate_id','')}\n\n**Initially unverified backlog**\n{_md_list(kickoff.get('initial_backlog'))}"))
    return "".join(parts)


def render_roadmap(state: dict[str, Any], status: str) -> str:
    camp = state["campaign"]
    gate_by_id = {gate.get("id"): gate for gate in camp.get("gates", []) if isinstance(gate, dict)}
    lines = [f"# Roadmap: {state['title']}", "", f"**Status:** {status}", "", f"**Purpose:** {camp['mission'].get('decision_or_purpose','')}", "", "## Stages", ""]
    if not camp.get("stages"):
        lines.extend(["*No stages recorded.*", ""])
    for stage in camp.get("stages", []):
        title = str(stage.get("name") or stage.get("purpose") or "").strip()
        lines.append(f"### {stage.get('id')}" + (f" — {title}" if title else ""))
        lines.append("")
        for key, label in (("purpose", "Purpose"), ("prerequisite_stage_ids", "Prerequisites"),
                           ("outputs", "Outputs"), ("owner", "Owner"), ("budget", "Budget"), ("pace", "Expected pace")):
            if _nonempty(stage.get(key)) and not (key == "purpose" and title == str(stage.get("purpose", "")).strip()):
                lines.append(_labelled(label, stage[key]))
        gate = gate_by_id.get(stage.get("gate_id"))
        if gate:
            lines.append(f"- **Gate {gate.get('id')}:** {_fmt_value(gate.get('criteria'))}")
            if _nonempty(gate.get("on_fail")):
                lines.append(f"- **On gate failure:** {_fmt_value(gate.get('on_fail'))}")
        elif _nonempty(stage.get("gate_id")):
            lines.append(f"- **Gate:** {stage.get('gate_id')} (not defined)")
        lines.append("")
    open_blockers = [item for item in state.get("blockers", []) if item.get("status", "open") == "open"]
    lines.extend(["## Major blockers", "", _render_objects(open_blockers, "blockers", fallback="*None recorded.*"), "",
                  "## Final deliverables", "", _render_objects(camp.get("deliverables"), "campaign.deliverables"), ""])
    return "\n".join(lines)


def render_review_report(state: dict[str, Any], validation: dict[str, Any]) -> str:
    lines = ["# Review report", "", f"**Content digest:** `{content_digest(state)}`", "", f"**Rubric digest:** `{rubric_digest(state['profile'])}`", "", f"**Execution ready:** {validation.get('execution_ready', False)}", "", "## Deterministic findings", ""]
    for item in validation.get("errors", []):
        lines.append(f"- **ERROR {item['code']}:** {item['message']} (`{item.get('path','')}`)")
    for item in validation.get("warnings", []):
        lines.append(f"- **WARNING {item['code']}:** {item['message']} (`{item.get('path','')}`)")
    if not validation.get("errors") and not validation.get("warnings"):
        lines.append("- No deterministic findings.")
    lines.extend([
        "", "## Reviewer records", "",
        "**Independence below is self-attested.** `mode` and `execution_evidence` are claims made",
        "by whoever produced each record. This engine checks that the values are legal and that",
        "records are bound to the frozen content digest; distinct reviewer identities and distinct",
        "executors are enforced only at the high-assurance profile. It cannot observe another",
        "process and prove a separate reviewer ran. An agent reviewer checks internal coherence",
        "and is not external validation.",
        "",
    ])
    for record in state.get("reviews", {}).get("records", []):
        lines.append(f"### {record.get('role')} — {record.get('verdict')}")
        lines.append("")
        lines.append(f"Reviewer: `{record.get('reviewer_id')}`; attested mode: `{record.get('mode')}`")
        evidence = record.get("execution_evidence") or {}
        if evidence:
            lines.append("")
            lines.append(f"Attested executor: `{evidence.get('executor_id')}` "
                         f"({evidence.get('started_at')} → {evidence.get('completed_at')})")
        lines.append("")
        lines.append(record.get("summary", ""))
        lines.append("")
        for finding in record.get("findings", []):
            lines.append(f"- **{finding.get('severity')} / {finding.get('action')}:** {finding.get('description')}")
        lines.append("")
    if not state.get("reviews", {}).get("records"):
        lines.append("- No review records ingested.")
    return "\n".join(lines) + "\n"


def render_kickoff(state: dict[str, Any], status: str) -> str:
    camp = state["campaign"]
    kickoff = camp["kickoff"]
    gate = next((item for item in camp.get("gates", []) if item.get("id") == kickoff.get("first_gate_id")), None)
    lines = [f"# Kickoff: {state['title']}", "", f"**Status:** {status}", "",
             f"**Campaign contract:** `campaign.json` @ `{content_digest(state)}`", ""]
    lines.extend(["## Start here", "", kickoff.get("command") or "*No kickoff command recorded.*", ""])
    lines.extend(["## First gate", ""])
    if gate:
        lines.append(f"**{gate.get('id')}** — {_fmt_value(gate.get('criteria')).lstrip()}")
        for key, label in (("required_evidence", "Required evidence"), ("owner", "Owner"), ("on_fail", "On failure")):
            if _nonempty(gate.get(key)):
                lines.append(_labelled(label, gate[key]))
    else:
        lines.append("*No first gate recorded.*")
    lines.extend(["", "## Initially unverified backlog", "", _md_list(kickoff.get("initial_backlog")), "",
                  "## Standing rules", "", _md_list(camp["constitution"].get("rules")), "",
                  "Read `CAMPAIGN_PROMPT.md` for the full campaign constitution before acting.", ""])
    return "\n".join(lines)


def claims_evidence_matrix(state: dict[str, Any]) -> dict[str, Any]:
    """Inquiries and claims share this matrix's columns; rendering only claims dropped
    the inquiry evidence logic entirely, and a campaign may legitimately have no claims yet."""
    camp = state["campaign"]
    rows = []
    for item in camp.get("inquiries", []):
        rows.append({
            "id": item.get("id"), "kind": "inquiry",
            "statement": item.get("question_or_claim", ""),
            "support": item.get("admissible_support", []),
            "counterevidence_or_objections": item.get("counterevidence_or_rival", []),
            "verification": item.get("verification_or_adjudication", ""),
            "status": "open",
            "reporting_rule": item.get("reporting_rule", ""),
        })
    for item in camp.get("claims", []):
        rows.append({
            "id": item.get("id"), "kind": "claim", "inquiry_id": item.get("inquiry_id"),
            "statement": item.get("statement", ""),
            "support": item.get("support", []),
            "counterevidence_or_objections": item.get("counterevidence_or_objections", []),
            "verification": item.get("verification", ""),
            "status": item.get("status", ""),
            "reporting_rule": item.get("reporting_rule", ""),
        })
    return {"campaign_id": state["campaign_id"], "content_digest": content_digest(state), "rows": rows}


def task_brief_template(state: dict[str, Any]) -> str:
    """Instantiate one brief per defined work unit; fall back to a blank template only
    when none exist. Shipping a generic stub while the campaign holds fully specified
    units (with real prohibitions) is how a delegated worker loses its constraints."""
    camp = state["campaign"]
    header = (f"# Bounded work-unit briefs\n\nCampaign: `{state['campaign_id']}`\n"
              f"Content digest: `{content_digest(state)}`\n\n"
              "A local brief may narrow scope but may not weaken the campaign constitution.\n")
    units = camp.get("work_units") or []
    if not units:
        return header + ("\n*No work units defined. Use this blank contract if you delegate:*\n\n"
                         + _blank_task_brief())
    return header + "\n" + _render_objects(units, "campaign.work_units", heading="##") + "\n"


def _blank_task_brief() -> str:
    fields = [("Objective", "<one objective>"), ("Authoritative inputs and hashes", "<artifact path and hash>"),
              ("Permitted actions", "<action>"),
              ("Prohibited actions", "No scope expansion, external communication, purchase, submission, "
                                     "irreversible action, or use of unapproved data/tool."),
              ("Required method and tools", "<method/tool and version>"),
              ("Exact outputs", "<path, schema, and artifact>"),
              ("Verification and acceptance", "<mechanical and expert checks>"),
              ("Resource ceiling and deadline", "<limit>"),
              ("Retry, failure, and escalation", "<failure classes, retry limit, escalation target>")]
    return "\n".join(f"## {name}\n\n- {value}\n" for name, value in fields)


def runbook(state: dict[str, Any]) -> str:
    runtime = state["campaign"]["runtime"]
    resources = state["campaign"]["resources_dispatch"]
    return f"""# Operator runbook\n\n**Continuous runtime enabled:** {runtime.get('enabled')}\n\n## Start/resume trigger\n\n{runtime.get('continuation_trigger') or 'No autonomous continuation is authorized.'}\n\n## Canonical state and events\n\n- State: {runtime.get('state_store') or 'Not applicable'}\n- Events: {runtime.get('event_log') or 'Not applicable'}\n- Checkpoints: {runtime.get('checkpoint_policy') or 'Not applicable'}\n\n## Liveness and recovery\n\n- Liveness: {runtime.get('liveness') or 'Not applicable'}\n- Recovery: {runtime.get('recovery') or 'Not applicable'}\n- Idempotency: {runtime.get('idempotency') or 'Not applicable'}\n\n## Resource governor\n\n{_md_list(resources.get('budgets'))}\n\n## Fail-closed dispatch\n\n{_md_list(resources.get('dispatch_rules'))}\n\n## Approvals\n\n{_md_list(resources.get('approvals'))}\n"""


def render_blocking_errors(validation: dict[str, Any]) -> list[dict[str, str]]:
    """Errors that make the original state unsafe for renderers to dereference."""
    return [item for item in validation.get("errors", [])
            if item.get("code") in {"structure.type", "profile.invalid"}]


def render_refusal(validation: dict[str, Any]) -> dict[str, Any]:
    return {
        "rendered": False,
        "status": "NOT RENDERED — MALFORMED STATE",
        "output_dir": None,
        "manifest": {},
        "validation": validation,
        "next_action": "Repair the malformed state fields reported by validation, then rerun the command",
    }


def render_outputs(campaign_dir: Path, state: dict[str, Any], force_draft: bool = False) -> dict[str, Any]:
    validation = validate_state(state, include_reviews=True)
    if render_blocking_errors(validation):
        return render_refusal(validation)
    if force_draft:
        status = "NOT EXECUTION-READY — DRAFT"
    elif validation["release_status"] == "execution-ready":
        status = "EXECUTION-READY"
    elif validation["release_status"] == "plan-ready-execution-blocked":
        status = "PLAN-READY; EXECUTION BLOCKED"
    else:
        status = "NOT EXECUTION-READY — DESIGN BLOCKERS"

    out_dir = campaign_dir / OUTPUT_DIR_REL
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # Set the derived status before snapshotting so outputs/campaign.json agrees
    # with canonical state. `status` is excluded from the content digest, so this
    # does not invalidate reviews bound to the frozen content.
    state["status"] = "draft" if force_draft else validation["release_status"]
    state["last_validation"] = validation
    snapshot = copy.deepcopy(state)
    # The snapshot cannot embed its own artifact hash without becoming recursive.
    # Point to the adjacent manifest and never carry a prior render's manifest into
    # the new execution contract. The canonical state receives the full manifest
    # after all output bytes have been written.
    snapshot["outputs"] = {
        "last_rendered_digest": content_digest(state),
        "status": status,
        "manifest_path": "MANIFEST.sha256",
    }
    files: dict[str, str] = {
        "CAMPAIGN_PROMPT.md": render_campaign_prompt(state, status),
        "KICKOFF.md": render_kickoff(state, status),
        "campaign.json": json.dumps(snapshot, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        "ROADMAP.md": render_roadmap(state, status),
        "TASK_BRIEF_TEMPLATE.md": task_brief_template(state),
        "REVIEW_REPORT.md": render_review_report(state, validation),
        "CLAIMS_EVIDENCE_MATRIX.json": json.dumps(claims_evidence_matrix(state), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        "RUNBOOK.md": runbook(state),
    }
    open_blockers = [item for item in state.get("blockers", []) if item.get("status", "open") == "open"]
    if open_blockers or not validation["execution_ready"]:
        blocker_lines = ["# Blockers", "", f"**Status:** {status}", ""]
        for item in validation.get("errors", []):
            blocker_lines.append(f"- `{item['code']}`: {item['message']}")
        for item in open_blockers:
            blocker_lines.append(f"- `{item.get('id','blocker')}` ({item.get('severity','')}): {item.get('description','')}")
        files["BLOCKERS.md"] = "\n".join(blocker_lines) + "\n"

    manifest: dict[str, str] = {}
    for name, content in files.items():
        atomic_write(out_dir / name, content)
        manifest[name] = sha256_bytes(content.encode("utf-8"))
    manifest_lines = [f"{digest}  {name}" for name, digest in sorted(manifest.items())]
    atomic_write(out_dir / "MANIFEST.sha256", "\n".join(manifest_lines) + "\n")
    manifest["MANIFEST.sha256"] = sha256_bytes(("\n".join(manifest_lines) + "\n").encode("utf-8"))
    state["outputs"] = {"last_rendered_digest": content_digest(state), "status": status, "manifest": manifest}
    save_state(campaign_dir, state)
    return {"rendered": True, "status": status, "output_dir": str(out_dir),
            "manifest": manifest, "validation": validation}


def cmd_render(args: argparse.Namespace) -> None:
    campaign_dir = resolve_campaign(args.campaign)
    state = load_state(campaign_dir)
    validation = validate_state(state, include_reviews=True)
    if render_blocking_errors(validation):
        result = render_refusal(validation)
    else:
        result = render_outputs(campaign_dir, state,
                                force_draft=(args.draft or args.command == "draft"))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["rendered"]:
        raise SystemExit(2)


def cmd_finalize(args: argparse.Namespace) -> None:
    campaign_dir = resolve_campaign(args.campaign)
    state = load_state(campaign_dir)
    pre = validate_state(state, include_reviews=False)
    if render_blocking_errors(pre):
        write_json(campaign_dir / VALIDATION_REL, pre)
        print(json.dumps(render_refusal(pre), indent=2, ensure_ascii=False))
        raise SystemExit(2)
    rendered = state.get("outputs", {}).get("last_rendered_digest")
    if rendered and rendered != content_digest(state):
        # Finalize is about to replace the bundle. Do not turn that replaceable cache
        # mismatch into a design defect or an unnecessary review round.
        state["outputs"] = {"last_rendered_digest": "", "manifest": {}}
        pre = validate_state(state, include_reviews=False)
    write_json(campaign_dir / VALIDATION_REL, pre)
    if not pre["valid"]:
        digest, r_digest, paths = freeze_and_packets(campaign_dir, state)
        result = render_outputs(campaign_dir, load_state(campaign_dir), force_draft=True)
        result["next_action"] = "Resolve deterministic blockers; ask only material user questions, then rerun finalize"
        result["review_packets"] = [str(path) for path in paths]
        print(json.dumps(result, indent=2, ensure_ascii=False))
        raise SystemExit(2)
    current_digest = content_digest(state)
    if state["reviews"].get("frozen_content_digest") != current_digest or state["reviews"].get("rubric_digest") != rubric_digest(state["profile"]):
        _, _, paths = freeze_and_packets(campaign_dir, state)
        state = load_state(campaign_dir)
        _, needs_review = review_status(state)
        if needs_review:
            result = render_outputs(campaign_dir, state, force_draft=True)
            result["next_action"] = "Execute and ingest required review packets, then rerun finalize"
            result["review_packets"] = [str(path) for path in paths if path.stem in needs_review]
            print(json.dumps(result, indent=2, ensure_ascii=False))
            raise SystemExit(3)
    final_validation = validate_state(state, include_reviews=True)
    if not final_validation["valid"]:
        result = render_outputs(campaign_dir, state, force_draft=True)
        result["next_action"] = "Resolve or re-review current findings, then rerun finalize"
        print(json.dumps(result, indent=2, ensure_ascii=False))
        raise SystemExit(4)
    result = render_outputs(campaign_dir, state, force_draft=False)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_status(args: argparse.Namespace) -> None:
    campaign_dir = resolve_campaign(args.campaign)
    state = load_state(campaign_dir)
    pre = validate_state(state, include_reviews=False)
    full = validate_state(state, include_reviews=True)
    unresolved = [item for item in state.get("intent_dimensions", []) if item.get("status") not in COMPLETE_DIMENSION_STATUSES]
    payload = {
        "campaign_id": state["campaign_id"], "title": state["title"],
        "status": state["status"], "profile": state["profile"], "archetypes": state["archetypes"],
        "content_version": state["content_version"], "content_digest": content_digest(state),
        "interview": {
            "turns": len(state["interview"].get("turns", [])),
            "soft_limit": state["interview"]["soft_limit"], "hard_limit": state["interview"]["hard_limit"],
            "stopping_reason": state["interview"].get("stopping_reason", ""),
            "unresolved_dimensions": [item.get("id") for item in unresolved],
        },
        "design_valid": pre["valid"], "execution_ready": full["execution_ready"],
        "design_errors": len(pre["errors"]), "review_errors": len(full["errors"]) - len(pre["errors"]),
        "review": full["review"],
        "output_status": state.get("outputs", {}).get("status", "not rendered"),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def cmd_audit(args: argparse.Namespace) -> None:
    campaign_dir = resolve_campaign(args.campaign)
    state = load_state(campaign_dir)
    errors: list[str] = []
    out_dir = campaign_dir / OUTPUT_DIR_REL
    manifest_path = out_dir / "MANIFEST.sha256"
    verified: dict[str, bool] = {}
    # Canonical hashes come from state, not from the manifest sitting in the directory
    # being audited. Trusting that file alone let anyone with sha256sum tamper an artifact
    # and rewrite its one manifest line; the state copy also covers MANIFEST.sha256 itself.
    recorded = state.get("outputs", {}).get("manifest", {})
    if manifest_path.exists():
        if not recorded:
            errors.append("outputs exist but state records no manifest; re-render before auditing")
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            if "  " not in line:
                errors.append("malformed MANIFEST.sha256 line")
                continue
            digest, name = line.split("  ", 1)
            relative = Path(name)
            if relative.is_absolute() or ".." in relative.parts:
                errors.append(f"manifest artifact path escapes outputs: {name}")
                verified[name] = False
                continue
            path = out_dir / relative
            actual = sha256_bytes(path.read_bytes()) if path.exists() else None
            ok = actual is not None and actual == digest
            if ok and recorded and name in recorded and recorded[name] != actual:
                ok = False
                errors.append(f"artifact does not match the hash recorded in state: {name}")
            verified[name] = ok
            if not ok and f"artifact does not match the hash recorded in state: {name}" not in errors:
                errors.append(f"artifact hash mismatch: {name}")
        manifest_digest = sha256_bytes(manifest_path.read_bytes())
        if recorded.get("MANIFEST.sha256") and recorded["MANIFEST.sha256"] != manifest_digest:
            errors.append("MANIFEST.sha256 has been modified since it was rendered")
        verified["MANIFEST.sha256"] = recorded.get("MANIFEST.sha256") == manifest_digest
        for name in sorted(set(recorded) - set(verified)):
            errors.append(f"artifact recorded in state is missing from the manifest: {name}")
            verified[name] = False
        actual_files = {
            path.relative_to(out_dir).as_posix()
            for path in out_dir.rglob("*") if path.is_file()
        }
        unexpected = sorted(actual_files - set(recorded))
        for name in unexpected:
            errors.append(f"unexpected output artifact not recorded in state: {name}")
    elif recorded:
        errors.append("state records a rendered bundle but MANIFEST.sha256 is missing; "
                      "the outputs directory has been removed or emptied")
    elif out_dir.exists() and any(out_dir.iterdir()):
        errors.append("outputs exist without MANIFEST.sha256")
    validation = validate_state(state, include_reviews=True)
    result = {
        "audited_at": now_iso(), "campaign_id": state["campaign_id"],
        "content_digest": content_digest(state), "validation": validation,
        "artifact_verification": verified, "errors": errors,
        "ok": not errors and validation["valid"],
    }
    write_json(campaign_dir / "working/audit.json", result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["ok"]:
        # Non-strict used to print `"ok": false` and exit 0, which reads as success to
        # anything checking the exit code. Strict keeps its dedicated code.
        raise SystemExit(5 if args.strict else 1)


def cmd_schema(args: argparse.Namespace) -> None:
    if args.path == "list":
        print("# list sections (write with `add`)")
        print("\n".join(sorted(OBJECT_SPECS)))
        print("\n# dict sections (write with `set`)")
        print("\n".join(sorted(SECTION_SPECS)))
        return
    if args.path in SECTION_SPECS:
        section = SECTION_SPECS[args.path]
        payload = {
            "path": args.path, "kind": "dict-section", "written_with": "set",
            "required": list(section["required"]), "optional": list(section["optional"]),
        }
        if section.get("note"):
            payload["note"] = section["note"]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    spec = spec_for(args.path)
    if spec is None:
        raise SystemExit(f"Unknown path {args.path!r}; use `schema list`")
    payload = {
        "path": args.path,
        "label": spec["label"],
        "title_field": spec["title"],
        "required": list(spec["required"]),
        "fields": [{"name": name, "label": label} for name, label in spec["fields"]],
        "all_keys": sorted(allowed_keys(spec)),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def cmd_guide(args: argparse.Namespace) -> None:
    reference_dir = SKILL_DIR / "references"
    if not reference_dir.is_dir():
        raise SystemExit(
            f"No references directory at {reference_dir}. The skill bundle is incomplete: "
            "reinstall the whole rescamp/ directory, not SKILL.md alone."
        )
    allowed = {path.stem: path for path in reference_dir.glob("*.md")}
    if not allowed:
        raise SystemExit(f"References directory {reference_dir} is empty; the skill bundle is incomplete.")
    if args.topic == "list":
        print("\n".join(sorted(allowed)))
        return
    path = allowed.get(args.topic)
    if not path:
        raise SystemExit("Unknown guide; use guide list")
    print(path.read_text(encoding="utf-8"))


def cmd_profile(args: argparse.Namespace) -> None:
    campaign_dir = resolve_campaign(args.campaign)
    state = load_state(campaign_dir)
    if args.profile not in PROFILES:
        raise SystemExit("Invalid profile")
    state["profile"] = args.profile
    state["interview"]["soft_limit"] = PROFILES[args.profile]["soft"]
    state["interview"]["hard_limit"] = PROFILES[args.profile]["hard"]
    state["content_version"] += 1
    state["reviews"] = {"frozen_content_digest": "", "rubric_digest": "", "records": []}
    save_state(campaign_dir, state)
    print(args.profile)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="initialize a campaign")
    p.add_argument("--goal", required=True)
    p.add_argument("--root", default="research-campaigns")
    p.add_argument("--id")
    p.add_argument("--profile", choices=sorted(PROFILES), default="standard")
    p.add_argument("--archetypes", default="evidence-synthesis")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("set", help="set a dotted state path")
    p.add_argument("campaign")
    p.add_argument("path")
    p.add_argument("value", help="JSON value, plain string, or @file.json")
    p.add_argument("--create-missing", action="store_true",
                   help="allow creating path segments that do not exist (off by default: a typo'd section name is an error, not a new key)")
    p.set_defaults(func=cmd_set)

    p = sub.add_parser("add", help="append an object to a list path")
    p.add_argument("campaign")
    p.add_argument("path")
    p.add_argument("--json", required=True, help="JSON object, array of objects, or @file.json")
    p.add_argument("--require-id", action="store_true")
    p.add_argument("--allow-unknown", action="store_true", help="accept fields outside the object spec")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("apply", help="write many sections in one call, with add's field checking")
    p.add_argument("campaign")
    p.add_argument("--json", required=True, help="JSON object mapping dotted paths to values, or @file.json")
    p.add_argument("--allow-unknown", action="store_true", help="accept fields and paths outside the specs")
    p.set_defaults(func=cmd_apply)

    p = sub.add_parser("schema", help="print the field vocabulary for campaign objects")
    p.add_argument("path", nargs="?", default="list", help="collection path, or 'list'")
    p.set_defaults(func=cmd_schema)

    p = sub.add_parser("dimension", help="add or update an intent dimension")
    p.add_argument("campaign")
    p.add_argument("--id", required=True)
    p.add_argument("--label")
    p.add_argument("--status", choices=sorted(DIMENSION_STATUSES), required=True)
    p.add_argument("--value")
    p.add_argument("--importance", choices=["low", "material", "critical"], default="material")
    p.add_argument("--source", choices=["user", "researched", "inferred", "default", "external"], default="user")
    p.add_argument("--confidence", choices=["low", "medium", "high"], default="high")
    p.add_argument("--reason")
    p.add_argument("--dependencies", default="")
    p.set_defaults(func=cmd_dimension)

    p = sub.add_parser("turn", help="record one interview question and answer")
    p.add_argument("campaign")
    p.add_argument("--branch", required=True)
    p.add_argument("--question", required=True)
    p.add_argument("--answer", required=True)
    p.add_argument("--normalized", required=True)
    p.add_argument("--dimensions", default="")
    p.add_argument("--impact", choices=["low", "material", "critical"], default="material")
    p.add_argument("--utility", choices=["low", "medium", "high"], default="high")
    p.set_defaults(func=cmd_turn)

    p = sub.add_parser("stop", help="record interview stopping reason")
    p.add_argument("campaign")
    p.add_argument("--reason", choices=sorted(STOP_REASONS), required=True)
    p.add_argument("--note", default="")
    p.add_argument("--no-auto-quality", action="store_true", help="record stop without launching automatic current-plan QA")
    p.set_defaults(func=cmd_stop)

    p = sub.add_parser("profile", help="change assurance profile")
    p.add_argument("campaign")
    p.add_argument("profile", choices=sorted(PROFILES))
    p.set_defaults(func=cmd_profile)

    p = sub.add_parser("validate", help="run deterministic validation")
    p.add_argument("campaign")
    p.add_argument("--no-reviews", action="store_true")
    p.add_argument("--strict", action="store_true")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("quality-loop", aliases=["review", "test"], help="freeze and prepare automatic proportional QA")
    p.add_argument("campaign")
    p.set_defaults(func=cmd_quality_loop)

    p = sub.add_parser("ingest-review", help="ingest a structured reviewer result")
    p.add_argument("campaign")
    p.add_argument("file")
    p.set_defaults(func=cmd_ingest_review)

    p = sub.add_parser("render", aliases=["draft"], help="render current bundle")
    p.add_argument("campaign")
    p.add_argument("--draft", action="store_true")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("finalize", help="run fail-closed automatic QA and render")
    p.add_argument("campaign")
    p.set_defaults(func=cmd_finalize)

    p = sub.add_parser("status", help="show concise campaign status")
    p.add_argument("campaign")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("audit", help="verify state and rendered artifact hashes")
    p.add_argument("campaign")
    p.add_argument("--strict", action="store_true")
    p.set_defaults(func=cmd_audit)

    p = sub.add_parser("guide", help="print one focused reference")
    p.add_argument("topic", help="list or a reference stem")
    p.set_defaults(func=cmd_guide)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
