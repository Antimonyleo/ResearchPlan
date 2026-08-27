#!/usr/bin/env python3
"""ResCamp durable campaign state, validation, review, and rendering.

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

try:
    import fcntl
except ImportError:  # pragma: no cover - advisory locking is Unix-only
    fcntl = None  # type: ignore[assignment]

SKILL_DIR = Path(__file__).resolve().parent.parent
VERSION = (SKILL_DIR / "VERSION").read_text(encoding="utf-8").strip()
SCHEMA_VERSION = "3.2"
STATE_REL = Path("state/campaign.json")
VALIDATION_REL = Path("working/validation.json")
BRIEF_VALIDATION_REL = Path("working/brief_validation.json")
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
ENTRY_MODES = {"new-project", "existing-project"}
PLANNING_MODES = {"auto", "brief", "full"}
ARTIFACT_LEVELS = {"brief", "full"}
PROMOTION_STATUSES = {"pending", "not-offered", "offered", "accepted", "declined", "not-applicable"}
PROMOTION_DECISIONS = {"accept", "decline"}
PROMOTION_SOURCES = {"auto-prompt", "camp-full"}
BRIEF_SOFT_LIMIT = 3
BRIEF_HARD_LIMIT = 4

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
            ("checkpoint_review", "Independent checkpoint review"),
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
    "sketch": {
        "required": (
            "decision_or_purpose", "scope", "non_goals", "core_inquiries",
            "likely_evidence", "rough_methods_stages", "success_or_adjudication",
            "assumptions_risks", "proposed_outputs", "next_action",
        ),
        "optional": (),
        "note": "This is the authoritative Camp-brief content and the seed for Camp-full.",
    },
    "campaign.starting_point": {
        "required": ("entry_mode",),
        "optional": (
            "status_as_of", "status_summary", "assessment_basis",
            "accepted_completed_work", "work_in_progress", "inherited_artifacts",
            "decisions_in_force", "known_deviations", "requires_recheck", "next_decision",
        ),
        "note": ("Use entry_mode 'new-project' or 'existing-project'. Existing projects also "
                 "require status_as_of, status_summary, assessment_basis, and next_decision."),
    },
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


def campaign_directory(campaign_dir: Path, relative: str | Path,
                       label: str, create: bool = False) -> Path:
    """Return a real, contained campaign directory.

    The engine writes several derived files below ``working``. Checking only the
    final path is insufficient: a symlinked parent would redirect every write to
    an unrelated tree. Walk each component before creating anything and reject
    links, non-directories, and resolved paths outside the campaign.
    """
    root = Path(campaign_dir).resolve()
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise SystemExit(f"{label} path must stay inside the campaign")
    current = root
    for component in relative_path.parts:
        current = current / component
        if current.is_symlink():
            raise SystemExit(f"Campaign {label} must not be a symlink")
        if current.exists() and not current.is_dir():
            raise SystemExit(f"Campaign {label} must be a directory")
    if create and not current.exists():
        current.mkdir(parents=True, exist_ok=True)
    if current.exists():
        try:
            current.resolve().relative_to(root)
        except (OSError, ValueError):
            raise SystemExit(f"Campaign {label} escapes the campaign") from None
    return current


def campaign_working_dir(campaign_dir: Path, create: bool = False) -> Path:
    return campaign_directory(campaign_dir, "working", "working directory", create=create)


def staged_directory(target: Path) -> Path:
    if target.is_symlink():
        raise SystemExit(f"Refusing to stage into symlinked directory: {target}")
    if target.parent.is_symlink():
        raise SystemExit(f"Refusing to stage through symlinked parent: {target.parent}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.parent.is_symlink() or not target.parent.is_dir():
        raise SystemExit(f"Staging parent must be a real directory: {target.parent}")
    return Path(tempfile.mkdtemp(prefix=f".{target.name}.staged-", dir=target.parent))


def commit_state_and_directory(campaign_dir: Path, state: dict[str, Any],
                               staged: Path, target: Path) -> None:
    """Publish a complete directory and its matching state as one bounded commit.

    The generated directory is derived data, so it moves first. If the compare-and-swap
    state write then fails, restore the previous directory. A process crash can at worst
    leave new derived data beside old canonical state, which the digest audit rejects;
    canonical state never claims files that were not published.
    """
    campaign_working_dir(campaign_dir, create=True)
    if target.is_symlink():
        raise SystemExit(f"Refusing to replace symlinked generated directory: {target}")
    if target.exists() and not target.is_dir():
        raise SystemExit(f"Generated output target must be a directory: {target}")
    backup = staged.with_name(staged.name.replace(".staged-", ".previous-", 1))
    had_target = target.exists()
    if had_target:
        os.replace(target, backup)
    try:
        os.replace(staged, target)
        save_state(campaign_dir, state)
    except BaseException:
        if target.exists() and not target.is_symlink():
            shutil.rmtree(target)
        if had_target and backup.exists():
            os.replace(backup, target)
        raise
    if backup.exists():
        shutil.rmtree(backup, ignore_errors=True)


def resolve_campaign(path: str | Path) -> Path:
    supplied = Path(path).expanduser()
    if supplied.name == "campaign.json" and supplied.parent.name == "state":
        candidate = supplied.parent.parent.resolve()
    else:
        candidate = supplied.resolve()
    state_path = candidate / STATE_REL
    if state_path.exists() or state_path.is_symlink():
        return candidate
    raise SystemExit(f"Campaign not found: {candidate}")


def campaign_state_path(campaign_dir: Path, require_exists: bool = True) -> Path:
    """Return the lexical state path only when it is a contained regular file."""
    root = campaign_dir.resolve()
    state_dir = root / STATE_REL.parent
    path = root / STATE_REL
    if state_dir.is_symlink():
        raise SystemExit("Campaign state directory must not be a symlink")
    try:
        state_dir.resolve().relative_to(root)
    except (OSError, ValueError):
        raise SystemExit("Campaign state directory escapes the campaign") from None
    if path.is_symlink():
        raise SystemExit("Campaign state file must not be a symlink")
    if path.exists() and not path.is_file():
        raise SystemExit("Campaign state path must be a regular file")
    if require_exists and not path.exists():
        raise SystemExit(f"Campaign state file is missing: {path}")
    return path


def load_state(campaign_dir: Path) -> dict[str, Any]:
    path = campaign_state_path(campaign_dir)
    # Parse and fingerprint the same byte snapshot. Reading the file twice allowed a
    # concurrent replacement between those reads to pair state A with the baseline
    # digest of state B, defeating the later compare-and-swap guard.
    try:
        raw = path.read_bytes()
        state = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Could not read campaign state: {exc}") from None
    if not isinstance(state, dict):
        raise SystemExit("Campaign state must be a JSON object")
    _STATE_BASELINES[path] = sha256_bytes(raw)
    return state


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


def render_digest(state: dict[str, Any]) -> str:
    """Bind rendered bytes to plan content plus review, pilot, and acceptance evidence."""
    value = copy.deepcopy(state)
    for key in ("updated_at", "outputs", "last_validation", "status"):
        value.pop(key, None)
    return sha256_json(value)


def workflow_state(state: dict[str, Any]) -> dict[str, Any]:
    """Return workflow state, treating pre-3.2 campaigns as full campaigns.

    The compatibility default is read-only. Release validation still rejects an old
    schema until `migrate` records the workflow explicitly.
    """
    workflow = state.get("workflow")
    if isinstance(workflow, dict):
        return workflow
    return {
        "requested_mode": "full",
        "artifact_level": "full",
        "promotion": {
            "status": "not-applicable", "brief_digest": "", "answer_verbatim": "",
            "accepted_brief": {}, "source": "", "offered_at": "", "decided_at": "",
        },
    }


def brief_payload(state: dict[str, Any]) -> dict[str, Any]:
    """The accepted brief content, excluding workflow bookkeeping and full-only fields."""
    campaign = state.get("campaign") if isinstance(state.get("campaign"), dict) else {}
    interview = state.get("interview") if isinstance(state.get("interview"), dict) else {}
    return {
        "campaign_id": state.get("campaign_id", ""),
        "goal_verbatim": state.get("goal_verbatim", ""),
        "profile": state.get("profile", ""),
        "archetypes": state.get("archetypes", []),
        "starting_point": campaign.get("starting_point", {"entry_mode": "new-project"}),
        "sketch": state.get("sketch", {}),
        "intent_dimensions": state.get("intent_dimensions", []),
        "interview": {
            "turns": interview.get("turns", []),
            "stopping_reason": interview.get("stopping_reason", ""),
            "stopping_note": interview.get("stopping_note", ""),
        },
        "assumptions": state.get("assumptions", []),
        "contradictions": state.get("contradictions", []),
        "blockers": state.get("blockers", []),
    }


def brief_digest(state: dict[str, Any]) -> str:
    return sha256_json(brief_payload(state))


def mark_content_changed(state: dict[str, Any]) -> None:
    """Invalidate derived readiness after authored content changes."""
    workflow = workflow_state(state)
    if workflow.get("artifact_level") == "brief":
        state["status"] = "brief-draft"
        promotion = workflow.get("promotion")
        if isinstance(promotion, dict) and workflow.get("requested_mode") == "auto" \
                and promotion.get("status") in {"offered", "declined"} \
                and promotion.get("brief_digest") != brief_digest(state):
            promotion.update({
                "status": "pending", "brief_digest": "", "answer_verbatim": "",
                "source": "", "offered_at": "", "accepted_brief": {}, "decided_at": "",
            })
    else:
        state["status"] = "full-draft"


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


_STATE_BASELINES: dict[Path, str] = {}


def save_state(campaign_dir: Path, state: dict[str, Any]) -> None:
    """Atomically save unless another process changed the state after this load."""
    campaign_working_dir(campaign_dir, create=True)
    path = campaign_state_path(campaign_dir, require_exists=False)
    lock_path = campaign_working_dir(campaign_dir) / ".state.lock"
    with lock_path.open("a+", encoding="utf-8") as lock:
        if fcntl is not None:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        current = sha256_bytes(path.read_bytes()) if path.exists() else None
        expected = _STATE_BASELINES.get(path)
        if expected is not None and current != expected:
            raise SystemExit(
                "Campaign state changed in another process; reload it and reapply this edit"
            )
        state["updated_at"] = now_iso()
        encoded = (json.dumps(state, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        atomic_write(path, encoded.decode("utf-8"))
        _STATE_BASELINES[path] = sha256_bytes(encoded)


TITLE_LIMIT = 120


def _title_from_goal(goal: str) -> str:
    """Shorten a long goal to a title without cutting a word in half.

    A hard slice produced headings like "...that clear fro" at the top of the
    rendered prompt and kickoff. Break on the last whitespace instead and mark
    the elision, so the heading reads as shortened rather than as corrupted.
    """
    text = " ".join(goal.split())
    if len(text) <= TITLE_LIMIT:
        return text
    head = text[:TITLE_LIMIT - 1]
    cut = head.rsplit(" ", 1)[0] if " " in head else head
    return cut.rstrip(" ,;:.") + "…"


def question_limits(profile: str, artifact_level: str) -> tuple[int, int]:
    if artifact_level == "brief":
        return BRIEF_SOFT_LIMIT, BRIEF_HARD_LIMIT
    return PROFILES[profile]["soft"], PROFILES[profile]["hard"]


def campaign_template(entry_mode: str) -> dict[str, Any]:
    return {
        "starting_point": {
            "entry_mode": entry_mode,
            "status_as_of": "", "status_summary": "", "assessment_basis": [],
            "accepted_completed_work": [], "work_in_progress": [],
            "inherited_artifacts": [], "decisions_in_force": [],
            "known_deviations": [], "requires_recheck": [], "next_decision": "",
        },
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
    }


def default_state(goal: str, profile: str, archetypes: list[str], campaign_id: str,
                  entry_mode: str = "new-project", planning_mode: str = "full") -> dict[str, Any]:
    if planning_mode not in PLANNING_MODES:
        raise ValueError(f"Unknown planning mode: {planning_mode}")
    artifact_level = "full" if planning_mode == "full" else "brief"
    soft_limit, hard_limit = question_limits(profile, artifact_level)
    promotion_status = (
        "pending" if planning_mode == "auto"
        else "not-offered" if planning_mode == "brief"
        else "not-applicable"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "rescamp_version": VERSION,
        "campaign_id": campaign_id,
        "title": _title_from_goal(goal),
        "goal_verbatim": goal.strip(),
        "profile": profile,
        "archetypes": archetypes,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "content_version": 1,
        "status": "full-draft" if artifact_level == "full" else "brief-draft",
        "workflow": {
            "requested_mode": planning_mode,
            "artifact_level": artifact_level,
            "promotion": {
                "status": promotion_status,
                "brief_digest": "",
                "answer_verbatim": "",
                "accepted_brief": {},
                "source": "",
                "offered_at": "",
                "decided_at": "",
            },
        },
        "sketch": {
            "decision_or_purpose": "",
            "scope": "",
            "non_goals": [],
            "core_inquiries": [],
            "likely_evidence": [],
            "rough_methods_stages": [],
            "success_or_adjudication": "",
            "assumptions_risks": [],
            "proposed_outputs": [],
            "next_action": "",
        },
        "intent_dimensions": [],
        "interview": {
            "soft_limit": soft_limit,
            "hard_limit": hard_limit,
            "extension_authorized": False,
            "turns": [],
            "stopping_reason": "",
            "stopping_note": "",
        },
        "campaign": (campaign_template(entry_mode) if artifact_level == "full" else {
            "starting_point": campaign_template(entry_mode)["starting_point"],
        }),
        "assumptions": [],
        "contradictions": [],
        "blockers": [],
        "assurance": {"pilot_required": profile == "high-assurance", "pilot": {}, "risk_acceptances": []},
        "reviews": {
            "frozen_content_digest": "", "rubric_digest": "", "records": [],
            # Packet metadata is keyed by immutable packet digest so a review that
            # survives an unrelated section repair can remain bound to its original
            # packet while the new freeze publishes replacement packets.
            "packet_metadata": {}, "current_packets": {},
        },
        "outputs": {"last_rendered_digest": "", "manifest": {}},
        "last_validation": {},
    }


def get_by_path(data: Any, dotted: str) -> Any:
    current = data
    for part in dotted.split("."):
        if isinstance(current, list):
            try:
                position = int(part)
            except ValueError as exc:
                raise SystemExit(f"List path segment must be a non-negative integer: {part!r}") from exc
            if position < 0 or position >= len(current):
                raise SystemExit(f"List index out of range: {position}")
            current = current[position]
        else:
            current = current[part]
    return current


# Engine-owned state. Writing these directly would bypass the checks that make them mean
# anything: `reviews` has ingest-review, `status` is derived from validation, `outputs` and
# `last_validation` are rendered records.
PROTECTED_PATHS = ("workflow", "reviews", "status", "outputs", "last_validation")


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
            try:
                position = int(part)
            except ValueError as exc:
                raise SystemExit(f"List path segment must be a non-negative integer: {part!r}") from exc
            if position < 0 or position >= len(current):
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
        try:
            position = int(last)
        except ValueError as exc:
            raise SystemExit(f"List path segment must be a non-negative integer: {last!r}") from exc
        if position < 0 or position >= len(current):
            raise SystemExit(f"Index out of range at '{dotted}': list has {len(current)} item(s)")
        current[position] = value
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
    if len(campaign_id) > 56 or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", campaign_id):
        raise SystemExit("--id must be at most 56 lowercase letters, digits, and hyphens")
    campaign_dir = base / campaign_id
    # A pre-existing empty directory is not safe to reuse: another initializer may
    # have created it between our check and the child-directory writes. Symlinks and
    # non-directories are rejected explicitly instead of being followed.
    if campaign_dir.is_symlink():
        raise SystemExit(f"Campaign target already exists and is a symlink: {campaign_dir}")
    if campaign_dir.exists():
        if not campaign_dir.is_dir():
            raise SystemExit(f"Campaign target already exists and is not a directory: {campaign_dir}")
        raise SystemExit(f"Campaign directory already exists: {campaign_dir}")
    try:
        base.mkdir(parents=True, exist_ok=True)
        campaign_dir.mkdir()
    except FileExistsError:
        raise SystemExit(f"Campaign directory already exists: {campaign_dir}") from None
    for rel in ("state", "working", "working/review_packets", "outputs", "artifacts"):
        (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
    state = default_state(
        args.goal, args.profile, archetypes, campaign_id,
        getattr(args, "entry_mode", "new-project"),
        getattr(args, "planning_mode", "full"),
    )
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
    # A legacy campaign may lack a section introduced by a later compatible release.
    # Let the exact, documented section path create that final key without opening the
    # broader typo-prone `--create-missing` escape hatch.
    before = copy.deepcopy(state)
    set_by_path(state, args.path, value,
                create_missing=args.create_missing or section is not None)
    if state == before:
        print(f"unchanged {args.path}")
        return
    state["content_version"] += 1
    mark_content_changed(state)
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
    mark_content_changed(state)
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
        set_by_path(state, path, value,
                    create_missing=args.allow_unknown or path in SECTION_SPECS)
        written.append(path)
    state["content_version"] += 1
    mark_content_changed(state)
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
    mark_content_changed(state)
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
    hard_limit = (BRIEF_HARD_LIMIT if workflow_state(state).get("artifact_level") == "brief"
                  else state["interview"]["hard_limit"])
    if number > hard_limit and state["interview"].get("extension_authorized") is not True:
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
    mark_content_changed(state)
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
    campaign_working_dir(campaign_dir, create=True)
    state = load_state(campaign_dir)
    state["interview"]["stopping_reason"] = args.reason
    state["interview"]["stopping_note"] = args.note
    if workflow_state(state).get("artifact_level") == "brief":
        state["content_version"] += 1
        mark_content_changed(state)
        save_state(campaign_dir, state)
        print(json.dumps({
            "stopping_reason": args.reason,
            "completed_by_this_command": ["brief-stopping-reason-recorded"],
            "not_run_by_this_command": ["full-campaign-quality-loop"],
            "phase": "ready-for-brief-finalize",
            "next_action": "Run brief-finalize; Camp-auto will then ask the promotion question",
        }, indent=2))
        return
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
    pre = validate_plan_content(state, include_reviews=False)
    write_json(campaign_working_dir(campaign_dir) / VALIDATION_REL.name, pre)
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
        "review_packets_to_execute": ([str(path) for path in paths
                                       if path.stem in needs_review] if pre["valid"] else []),
        "review_packets_all": [str(path) for path in paths],
        "reviews_still_current": still_current,
        "roles_requiring_review": needs_review if pre["valid"] else [],
        "roles_pending_after_design_repair": needs_review if not pre["valid"] else [],
        "next_action": "Resolve deterministic findings and ask only material follow-up questions" if not pre["valid"] else _review_next_action(needs_review),
    }
    write_json(campaign_working_dir(campaign_dir) / "quality_loop.json", payload)
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


def validate_brief_state(state: dict[str, Any]) -> dict[str, Any]:
    """Validate the small, non-executable planning artifact."""
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    def issue(level: str, code: str, message: str, path: str = "") -> None:
        (errors if level == "error" else warnings).append(
            {"code": code, "message": message, "path": path}
        )

    if not isinstance(state, dict):
        issue("error", "structure.type", "Campaign state must be an object")
        return {
            "rescamp_version": VERSION, "checked_at": now_iso(),
            "brief_digest": sha256_json(state), "valid": False, "brief_ready": False,
            "execution_ready": False, "release_status": "brief-draft",
            "errors": errors, "warnings": warnings, "counts": {},
        }

    digest = brief_digest(state)
    if state.get("schema_version") != SCHEMA_VERSION:
        issue(
            "error", "schema.unsupported",
            f"Campaign schema {state.get('schema_version')!r} is not current {SCHEMA_VERSION!r}; "
            "migrate explicitly before release", "schema_version",
        )
    for key in ("campaign_id", "title", "goal_verbatim", "profile"):
        if not isinstance(state.get(key), str) or not state.get(key, "").strip():
            issue("error", "structure.type", f"{key} must be a non-empty string", key)
    if not isinstance(state.get("profile"), str) or state.get("profile") not in PROFILES:
        issue("error", "profile.invalid", f"Unknown profile {state.get('profile')!r}", "profile")

    archetypes = state.get("archetypes")
    if not isinstance(archetypes, list) or not archetypes or not all(isinstance(x, str) for x in archetypes):
        issue("error", "structure.type", "archetypes must be a non-empty list of strings", "archetypes")
    elif set(archetypes) - ARCHETYPES:
        issue("error", "archetype.invalid", ", ".join(sorted(set(archetypes) - ARCHETYPES)), "archetypes")

    workflow = state.get("workflow")
    if not isinstance(workflow, dict):
        issue("error", "structure.type", "workflow must be an object", "workflow")
        workflow = {}
    requested_mode = workflow.get("requested_mode")
    artifact_level = workflow.get("artifact_level")
    if not isinstance(requested_mode, str) or requested_mode not in PLANNING_MODES:
        issue("error", "workflow.mode", f"Unknown planning mode {requested_mode!r}", "workflow.requested_mode")
    if not isinstance(artifact_level, str) or artifact_level not in ARTIFACT_LEVELS:
        issue("error", "workflow.level", f"Unknown artifact level {artifact_level!r}", "workflow.artifact_level")
    elif artifact_level != "brief":
        issue("error", "workflow.not_brief", "This state is already a full campaign", "workflow.artifact_level")
    promotion = workflow.get("promotion")
    if not isinstance(promotion, dict):
        issue("error", "structure.type", "workflow.promotion must be an object", "workflow.promotion")
        promotion = {}
    promotion_status = promotion.get("status")
    if not isinstance(promotion_status, str) or promotion_status not in PROMOTION_STATUSES:
        issue("error", "promotion.status", f"Unknown promotion status {promotion_status!r}", "workflow.promotion.status")
    if requested_mode == "auto" and promotion_status not in {"pending", "offered", "declined"}:
        issue("error", "promotion.auto_state", "An auto brief must be pending, offered, or declined", "workflow.promotion.status")
    if requested_mode == "brief" and promotion_status != "not-offered":
        issue("error", "promotion.brief_state", "An explicit brief does not offer promotion automatically", "workflow.promotion.status")
    if promotion_status in {"offered", "declined"}:
        if promotion.get("brief_digest") != digest:
            issue("error", "promotion.stale", "The promotion decision is bound to an older brief", "workflow.promotion.brief_digest")
        if not _is_iso_timestamp(promotion.get("offered_at")):
            issue("error", "promotion.offered_at", "Promotion offer needs a timezone-aware timestamp", "workflow.promotion.offered_at")
    if promotion_status == "declined":
        if not _required_text(promotion.get("answer_verbatim")):
            issue("error", "promotion.answer", "A declined promotion needs the verbatim answer", "workflow.promotion.answer_verbatim")
        if not _is_iso_timestamp(promotion.get("decided_at")):
            issue("error", "promotion.decided_at", "A declined promotion needs a timezone-aware timestamp", "workflow.promotion.decided_at")

    sketch = state.get("sketch")
    if not isinstance(sketch, dict):
        issue("error", "structure.type", "sketch must be an object", "sketch")
        sketch = {}
    sketch_checks = {
        "decision_or_purpose": _required_text,
        "scope": _required_text,
        "non_goals": _required_list,
        "core_inquiries": _required_list,
        "likely_evidence": _required_list,
        "rough_methods_stages": _required_list,
        "success_or_adjudication": _required_text,
        "assumptions_risks": _required_list,
        "proposed_outputs": _required_list,
        "next_action": _required_text,
    }
    missing = [key for key, check in sketch_checks.items() if not check(sketch.get(key))]
    if missing:
        issue("error", "brief.incomplete", "Research brief is missing: " + ", ".join(missing), "sketch")

    campaign = state.get("campaign")
    if not isinstance(campaign, dict):
        issue("error", "structure.type", "campaign must be an object", "campaign")
        campaign = {}
    point = campaign.get("starting_point")
    if not isinstance(point, dict):
        issue("error", "structure.type", "campaign.starting_point must be an object", "campaign.starting_point")
        point = {}
    entry_mode = point.get("entry_mode")
    if entry_mode not in ENTRY_MODES:
        issue("error", "starting_point.mode", f"Unknown starting-point mode {entry_mode!r}", "campaign.starting_point.entry_mode")
    elif entry_mode == "existing-project":
        missing_point = [
            field for field in ("status_as_of", "status_summary", "assessment_basis", "next_decision")
            if not (_required_list(point.get(field)) if field == "assessment_basis" else _required_text(point.get(field)))
        ]
        if missing_point:
            issue("error", "starting_point.incomplete",
                  "Existing-project brief is missing: " + ", ".join(missing_point),
                  "campaign.starting_point")

    for key in ("intent_dimensions", "assumptions", "contradictions", "blockers"):
        values = state.get(key)
        if not isinstance(values, list):
            issue("error", "structure.type", f"{key} must be a list", key)
        elif key != "assumptions" and any(not isinstance(item, dict) for item in values):
            issue("error", "structure.type", f"{key} must contain only objects", key)
    interview = state.get("interview")
    if not isinstance(interview, dict):
        issue("error", "structure.type", "interview must be an object", "interview")
        interview = {}
    turns = interview.get("turns", [])
    if not isinstance(turns, list) or not all(isinstance(item, dict) for item in turns):
        issue("error", "structure.type", "interview.turns must be a list of objects", "interview.turns")
        turns = []
    extension_authorized = interview.get("extension_authorized", False)
    if not isinstance(extension_authorized, bool):
        issue("error", "interview.extension_type",
              "interview.extension_authorized must be boolean", "interview.extension_authorized")
    stopping_reason = interview.get("stopping_reason")
    if not _required_text(stopping_reason):
        issue("error", "interview.no_stop_reason",
              "Brief interview stopping reason is missing", "interview.stopping_reason")
    elif stopping_reason not in STOP_REASONS:
        issue("error", "interview.bad_stop_reason",
              "Brief interview stopping reason is invalid", "interview.stopping_reason")
    elif stopping_reason == "user-requested-draft":
        issue("error", "interview.draft_requested",
              "A user-requested draft cannot be labeled brief-ready",
              "interview.stopping_reason")
    if len(turns) > BRIEF_SOFT_LIMIT:
        issue("warning", "brief.question_soft_limit",
              f"Brief used {len(turns)} questions; the normal ceiling is {BRIEF_SOFT_LIMIT}",
              "interview.turns")
    if len(turns) > BRIEF_HARD_LIMIT and extension_authorized is not True:
        issue("error", "brief.question_hard_limit",
              f"Brief exceeded {BRIEF_HARD_LIMIT} questions without explicit extension",
              "interview.turns")

    outputs = state.get("outputs")
    if not isinstance(outputs, dict):
        issue("error", "structure.type", "outputs must be an object", "outputs")
        outputs = {}
    rendered = outputs.get("last_rendered_digest")
    if rendered and rendered != digest:
        issue("error", "outputs.stale", "The rendered brief was produced from older content", "outputs.last_rendered_digest")

    release_status = "brief-ready" if not errors else "brief-draft"
    return {
        "rescamp_version": VERSION, "checked_at": now_iso(), "brief_digest": digest,
        "content_digest": content_digest(state), "valid": not errors,
        "brief_ready": not errors, "execution_ready": False,
        "release_status": release_status, "errors": errors, "warnings": warnings,
        "counts": {"interview_turns": len(turns)},
        "promotion": {
            "status": promotion_status,
        },
    }


def validate_brief_content(state: dict[str, Any]) -> dict[str, Any]:
    """Validate authored brief content without treating old rendered output as content."""
    candidate = copy.deepcopy(state)
    candidate["outputs"] = {}
    return validate_brief_state(candidate)


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
    sketch = require_object(state, "sketch", "sketch")
    workflow = require_object(state, "workflow", "workflow")
    promotion = require_object(workflow, "promotion", "workflow.promotion")
    camp = require_object(state, "campaign", "campaign")
    reviews = require_object(state, "reviews", "reviews")
    require_object(state, "outputs", "outputs")
    for key in ("rescamp_version", "title", "campaign_id", "goal_verbatim", "profile"):
        if (key not in state or not isinstance(state.get(key), str)
                or not state.get(key, "").strip()):
            issue("error", "structure.type", f"{key} must be a non-empty string", key)
            state[key] = ""
    if "content_version" not in state or isinstance(state.get("content_version"), bool) \
            or not isinstance(state.get("content_version"), int):
        issue("error", "structure.type", "content_version must be an integer", "content_version")
        state["content_version"] = 0

    for key in ("constitution", "mission", "dossier", "evaluation", "resources_dispatch",
                "runtime", "ethics_rights_safety", "reporting", "kickoff"):
        require_object(camp, key, f"campaign.{key}")
    # `starting_point` was introduced after schema 3.1 shipped. Treat its absence in an
    # older campaign as the previous new-project behavior, while validating it strictly
    # whenever it is present.
    starting_point_present = "starting_point" in camp
    if not starting_point_present:
        starting_point = {"entry_mode": "new-project"}
    else:
        starting_point = require_object(camp, "starting_point", "campaign.starting_point")

    archetypes = require_list(state, "archetypes", "archetypes")
    valid_archetypes: list[str] = []
    for index, archetype in enumerate(archetypes):
        if isinstance(archetype, str):
            valid_archetypes.append(archetype)
        else:
            path = f"archetypes.{index}"
            issue("error", "structure.type", f"{path} must be a string", path)
    state["archetypes"] = valid_archetypes
    if not valid_archetypes:
        issue("error", "archetype.none", "At least one archetype is required", "archetypes")

    require_object_list(state, "intent_dimensions", "intent_dimensions")
    require_list(state, "assumptions", "assumptions")
    require_object_list(state, "contradictions", "contradictions")
    require_object_list(state, "blockers", "blockers")
    turns = require_object_list(interview, "turns", "interview.turns")
    for index, turn in enumerate(turns):
        path = f"interview.turns.{index}"
        number = turn.get("number")
        if not isinstance(number, int) or isinstance(number, bool) or number < 1:
            issue("error", "interview.turn_malformed", "Interview turn number must be positive", path)
        for key in ("branch", "question", "answer_verbatim", "decision_impact",
                    "answer_utility", "asked_at"):
            if not isinstance(turn.get(key), str) or not turn.get(key, "").strip():
                issue("error", "interview.turn_malformed",
                      f"Interview turn requires non-empty {key}", f"{path}.{key}")
        linked = turn.get("linked_dimensions")
        if (not isinstance(linked, list)
                or any(not isinstance(item, str) or not item for item in linked)):
            issue("error", "interview.turn_malformed",
                  "Interview linked_dimensions must be a list of strings",
                  f"{path}.linked_dimensions")
    for key in ("decision_or_purpose", "scope", "success_or_adjudication", "next_action"):
        require_string(sketch, key, f"sketch.{key}")
    for key in ("non_goals", "core_inquiries", "likely_evidence", "rough_methods_stages",
                "assumptions_risks", "proposed_outputs"):
        require_string_list(sketch, key, f"sketch.{key}")
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
    for key in ("entry_mode", "status_as_of", "status_summary", "next_decision"):
        if key in starting_point:
            require_string(starting_point, key, f"campaign.starting_point.{key}")
    for key in ("assessment_basis", "accepted_completed_work", "work_in_progress",
                "inherited_artifacts", "decisions_in_force", "known_deviations",
                "requires_recheck"):
        require_string_list(starting_point, key, f"campaign.starting_point.{key}")

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
        if "checkpoint_review" in gate:
            require_string(gate, "checkpoint_review", f"campaign.gates.{index}.checkpoint_review")
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
        for key in ("role", "reviewer_id", "mode", "verdict", "content_digest", "rubric_digest", "summary"):
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

    requested_mode = workflow.get("requested_mode")
    artifact_level = workflow.get("artifact_level")
    promotion_status = promotion.get("status")
    if not isinstance(requested_mode, str) or requested_mode not in PLANNING_MODES:
        issue("error", "workflow.mode", f"Unknown planning mode {requested_mode!r}",
              "workflow.requested_mode")
    if not isinstance(artifact_level, str) or artifact_level not in ARTIFACT_LEVELS:
        issue("error", "workflow.level", f"Unknown artifact level {artifact_level!r}",
              "workflow.artifact_level")
    elif artifact_level != "full":
        issue("error", "workflow.not_full",
              "A research brief is non-executable; promote it before full campaign validation",
              "workflow.artifact_level")
    if not isinstance(promotion_status, str) or promotion_status not in PROMOTION_STATUSES:
        issue("error", "promotion.status", f"Unknown promotion status {promotion_status!r}",
              "workflow.promotion.status")
    if requested_mode == "full" and promotion_status != "not-applicable":
        issue("error", "promotion.full_state", "A direct full campaign has no promotion record",
              "workflow.promotion.status")
    if (isinstance(requested_mode, str) and requested_mode in {"auto", "brief"}
            and artifact_level == "full"):
        if promotion_status != "accepted":
            issue("error", "promotion.not_accepted",
                  "A brief-origin campaign requires an accepted promotion record",
                  "workflow.promotion.status")
        if not str(promotion.get("brief_digest", "")).startswith("sha256:"):
            issue("error", "promotion.digest", "Promotion must preserve the accepted brief digest",
                  "workflow.promotion.brief_digest")
        accepted_brief = promotion.get("accepted_brief")
        if not isinstance(accepted_brief, dict) or not accepted_brief:
            issue("error", "promotion.brief_missing",
                  "Promotion must preserve the accepted brief content",
                  "workflow.promotion.accepted_brief")
        elif sha256_json(accepted_brief) != promotion.get("brief_digest"):
            issue("error", "promotion.brief_mismatch",
                  "Accepted brief content does not match its recorded digest",
                  "workflow.promotion.accepted_brief")
        if (not isinstance(promotion.get("source"), str)
                or promotion.get("source") not in PROMOTION_SOURCES):
            issue("error", "promotion.source", "Promotion source is invalid",
                  "workflow.promotion.source")
        if not _required_text(promotion.get("answer_verbatim")):
            issue("error", "promotion.answer", "Promotion must preserve the user's verbatim answer",
                  "workflow.promotion.answer_verbatim")
        if not _is_iso_timestamp(promotion.get("decided_at")):
            issue("error", "promotion.timestamp",
                  "Promotion requires a timezone-aware decision timestamp",
                  "workflow.promotion.decided_at")

    profile = state.get("profile")
    if not isinstance(profile, str) or profile not in PROFILES:
        issue("error", "profile.invalid", f"Unknown profile {profile!r}", "profile")
        return {"valid": False, "execution_ready": False, "errors": errors, "warnings": warnings}
    unknown_archetypes = sorted(set(state.get("archetypes", [])) - ARCHETYPES)
    if unknown_archetypes:
        issue("error", "archetype.invalid", ", ".join(unknown_archetypes), "archetypes")

    sketch_checks = {
        "decision_or_purpose": _required_text,
        "scope": _required_text,
        "non_goals": _required_list,
        "core_inquiries": _required_list,
        "likely_evidence": _required_list,
        "rough_methods_stages": _required_list,
        "success_or_adjudication": _required_text,
        "assumptions_risks": _required_list,
        "proposed_outputs": _required_list,
        "next_action": _required_text,
    }
    missing_sketch = [key for key, check in sketch_checks.items()
                      if not check(sketch.get(key))]
    if missing_sketch:
        issue("error", "sketch.incomplete",
              "Campaign sketch v0 is missing: " + ", ".join(missing_sketch),
              "sketch")

    if not isinstance(assurance.get("pilot_required"), bool):
        issue("error", "structure.type", "assurance.pilot_required must be boolean",
              "assurance.pilot_required")
    pilot_required = profile == "high-assurance" or assurance.get("pilot_required") is True
    pilot = assurance.get("pilot", {})
    if pilot_required and not isinstance(pilot, dict):
        issue("error", "pilot.malformed", "assurance.pilot must be an object", "assurance.pilot")
    elif pilot_required and not pilot:
        issue("error", "pilot.missing", "This campaign requires a completed, digest-bound pilot", "assurance.pilot")
    elif pilot_required:
        if (not isinstance(pilot.get("authorized_by"), str)
                or not pilot.get("authorized_by", "").strip()
                or not isinstance(pilot.get("authority"), str)
                or not pilot.get("authority", "").strip()):
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
            if not isinstance(pilot.get(field), str) or not pilot.get(field, "").strip()
        ]
        if not _is_iso_timestamp(pilot.get("executed_at")):
            missing_pilot_fields.append("executed_at")
        list_fields = ("evidence", "failures", "repairs")
        missing_pilot_fields.extend(
            field for field in list_fields
            if (not isinstance(pilot.get(field), list)
                or any(not isinstance(item, str) for item in pilot.get(field, [])))
        )
        if not _required_list(pilot.get("evidence")):
            if "evidence" not in missing_pilot_fields:
                missing_pilot_fields.append("evidence")
        if missing_pilot_fields:
            issue("error", "pilot.incomplete",
                  "Required pilot record missing valid fields: " + ", ".join(sorted(missing_pilot_fields)),
                  "assurance.pilot")

    interview = state.get("interview", {})
    turns = interview.get("turns", [])
    extension_authorized = interview.get("extension_authorized", False)
    if not isinstance(extension_authorized, bool):
        issue("error", "interview.extension_type",
              "interview.extension_authorized must be boolean", "interview.extension_authorized")
    if len(turns) > interview.get("hard_limit", PROFILES[profile]["hard"]) \
            and extension_authorized is not True:
        issue("error", "interview.hard_limit", "Interview exceeded hard limit without explicit authorization", "interview.turns")
    if not interview.get("stopping_reason"):
        issue("error", "interview.no_stop_reason", "Interview stopping reason is missing", "interview.stopping_reason")
    elif (not isinstance(interview.get("stopping_reason"), str)
          or interview.get("stopping_reason") not in STOP_REASONS):
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
        if (not isinstance(dim.get("status"), str)
                or dim.get("status") not in DIMENSION_STATUSES):
            issue("error", "dimension.status", f"Invalid status for {dim.get('id', index)}", path)
        importance = dim.get("importance", "material")
        if (isinstance(importance, str) and importance in {"critical", "material"}
                and dim.get("status") not in COMPLETE_DIMENSION_STATUSES):
            issue("error", "dimension.unresolved", f"Material dimension {dim.get('id', index)} is unresolved", path)
        if dim.get("status") in {"explicit-default", "deferred", "not-applicable", "blocked"} \
                and not _required_text(dim.get("reason")):
            issue("error", "dimension.reason", f"Status {dim.get('status')} requires a reason", path)

    camp = state.get("campaign", {})
    entry_mode = (starting_point.get("entry_mode") if starting_point_present
                  else "new-project")
    if entry_mode not in ENTRY_MODES:
        issue("error", "starting_point.mode",
              f"Unknown entry mode {entry_mode!r}; use new-project or existing-project",
              "campaign.starting_point.entry_mode")
    elif entry_mode == "existing-project":
        missing = [
            field for field in ("status_as_of", "status_summary", "next_decision")
            if not _required_text(starting_point.get(field))
        ]
        if not _required_list(starting_point.get("assessment_basis")):
            missing.append("assessment_basis")
        if missing:
            issue("error", "starting_point.incomplete",
                  "Existing-project intake is missing: " + ", ".join(missing),
                  "campaign.starting_point")
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
        freeze_scope = ("remaining prospective evidence was inspected"
                        if entry_mode == "existing-project"
                        else "production evidence was inspected")
        issue("error", "evaluation.not_frozen",
              "The campaign does not assert that the evaluation/adjudication instrument was frozen before "
              f"{freeze_scope}. This is an attestation by whoever compiled "
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
    if not isinstance(external_actions, list):
        issue("error", "external_action.malformed", "external_actions must be a list",
              "campaign.ethics_rights_safety.external_actions")
        external_actions = []
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
    if rendered and rendered != render_digest(state):
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
        valid_records: list[dict[str, Any]] = []
        for index, record in enumerate(records):
            semantic_errors = review_record_errors(record)
            if semantic_errors:
                issue(
                    "error", "review.record_invalid",
                    f"Review record {index} is invalid: {'; '.join(semantic_errors)}",
                    f"reviews.records.{index}",
                )
                continue
            if record_is_current(record, state, leaves):
                valid_records.append(record)
        records_by_role: dict[str, list[dict[str, Any]]] = {}
        for record in valid_records:
            role = record.get("role")
            if isinstance(role, str) and role:
                records_by_role.setdefault(role, []).append(record)
        # A dict comprehension here used to let the last record for a role replace a
        # blocking earlier record. Keep a deterministic representative for reporting,
        # but make every duplicate role an execution blocker and aggregate verdicts.
        role_map = {role: items[0] for role, items in records_by_role.items()}
        required = PROFILES[profile]["review_roles"]
        missing = [role for role in required if role not in role_map]
        duplicate_roles = sorted(role for role, items in records_by_role.items() if len(items) > 1)
        if duplicate_roles:
            issue("error", "review.duplicate_role",
                  "Multiple current review records claim the same role: " + ", ".join(duplicate_roles),
                  "reviews.records")
        blocking = sorted({
            role for role, items in records_by_role.items()
            if role in required and any(item.get("verdict") != "pass" for item in items)
        })
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
        for role, records_for_role in sorted(records_by_role.items()):
            for record in records_for_role:
                for finding in record.get("findings", []):
                    severity = finding.get("severity")
                    if severity not in {"major", "critical"}:
                        continue
                    digest = finding_digest(role, finding)
                    accepted = any(
                        item.get("finding_digest") == digest
                        and isinstance(item.get("accepted_by"), str)
                        and bool(item["accepted_by"].strip())
                        and item.get("accepted_by") != record.get("reviewer_id")
                        and isinstance(item.get("authority"), str)
                        and bool(item["authority"].strip())
                        and _is_iso_timestamp(item.get("accepted_at"))
                        and isinstance(item.get("scope"), str)
                        and bool(item["scope"].strip())
                        and (
                            (isinstance(item.get("evidence"), str)
                             and bool(item["evidence"].strip()))
                            or _required_list(item.get("evidence"))
                        )
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
    execution_ready = not errors
    if not include_reviews:
        # Deterministic design validation is useful preparation, but it cannot
        # establish execution authority. Keep this rule here so every caller
        # (quality-loop, stop, validate, and finalize) receives the same truth.
        execution_ready = False
        if release_status == "execution-ready":
            release_status = "plan-ready-execution-blocked"
        warnings.append({
            "code": "review.not_checked",
            "message": "Review checks were excluded; this result cannot establish execution readiness",
            "path": "reviews.records",
        })
    result = {
        "rescamp_version": VERSION,
        "checked_at": now_iso(),
        "content_digest": input_digest,
        "rubric_digest": rubric_digest(profile),
        "valid": not errors,
        "execution_ready": execution_ready,
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


def validate_plan_content(state: dict[str, Any], include_reviews: bool) -> dict[str, Any]:
    """Validate authored content without treating a replaceable rendered bundle as design.

    A content edit makes prior outputs stale. Review preparation and a new render are the
    remedy, so those operations must not report that derived-cache mismatch as a plan flaw.
    Explicit `validate`, `status`, and `audit` still expose stale outputs.
    """
    candidate = copy.deepcopy(state)
    candidate["outputs"] = {}
    return validate_state(candidate, include_reviews=include_reviews)


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
    if workflow_state(state).get("artifact_level") == "brief":
        result = validate_brief_state(state)
    else:
        result = validate_state(state, include_reviews=not args.no_reviews)
    state["last_validation"] = result
    write_json(campaign_working_dir(campaign_dir, create=True) / VALIDATION_REL.name, result)
    save_state(campaign_dir, state)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.strict and not result["valid"]:
        raise SystemExit(2)


# What each reviewer role actually has to read. Shipping the whole campaign to every
# reviewer made a methods reviewer read the runtime config and the interview transcript,
# and cost ~16k tokens per role per round. A record carries the packet's full-campaign
# digest as provenance, while its exact section digests are the freshness boundary.
ROLE_SCOPES: dict[str, dict[str, Any]] = {
    "methods-evidence": {
        "sections": ("starting_point", "mission", "dossier", "inquiries", "methods",
                     "evaluation", "claims"),
        "top_level": ("goal_verbatim", "profile", "archetypes", "workflow", "sketch", "assumptions",
                      "contradictions", "intent_dimensions"),
        "note": "Methods and evidence logic. Operations sections are omitted by design; do not infer they are absent.",
    },
    "operations-reproducibility": {
        # ethics_rights_safety is here so that the two standard-profile roles between them
        # cover every campaign section. Without it a change to consent, rights, or approval
        # boundaries would invalidate nobody's review at `standard`.
        "sections": ("starting_point", "constitution", "tools", "canaries", "stages", "gates",
                     "resources_dispatch", "roles", "runtime", "work_units", "deliverables",
                     "kickoff", "reporting", "ethics_rights_safety"),
        "top_level": ("goal_verbatim", "profile", "archetypes", "blockers", "assurance"),
        "note": "Operations, reproducibility, and the approval and external-action boundaries. Inquiry and method detail is omitted by design; do not infer it is absent.",
    },
    "ethics-claim-integrity": {
        "sections": ("starting_point", "mission", "dossier", "ethics_rights_safety",
                     "reporting", "claims", "inquiries", "deliverables", "resources_dispatch"),
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
    if review_record_errors(record):
        return False
    if record.get("rubric_digest") != rubric_digest(state["profile"]):
        return False
    packet_digest = record.get("packet_digest")
    if packet_digest is not None:
        if not isinstance(packet_digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", packet_digest):
            return False
        reviews = state.get("reviews")
        metadata_map = reviews.get("packet_metadata") if isinstance(reviews, dict) else None
        metadata = metadata_map.get(packet_digest) if isinstance(metadata_map, dict) else None
        if not isinstance(metadata, dict):
            return False
        if (metadata.get("role") != record.get("role")
                or metadata.get("content_digest") != record.get("content_digest")
                or metadata.get("rubric_digest") != record.get("rubric_digest")):
            return False
        if metadata.get("reviewed_sections") != record.get("reviewed_sections"):
            return False
        contract_digest = metadata.get("contract_digest")
        if (not isinstance(contract_digest, str)
                or not re.fullmatch(r"sha256:[0-9a-f]{64}", contract_digest)):
            return False
        current_packets = reviews.get("current_packets") if isinstance(reviews, dict) else None
        current_packet = current_packets.get(record.get("role")) if isinstance(current_packets, dict) else None
        current_metadata = metadata_map.get(current_packet) if isinstance(current_packet, str) else None
        if (not isinstance(current_metadata, dict)
                or current_metadata.get("contract_digest") != contract_digest):
            return False
    reviewed = record.get("reviewed_sections")
    if not isinstance(reviewed, dict):
        return record.get("content_digest") == content_digest(state)
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(record.get("content_digest", ""))):
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
    # The invalidation closure is the reviewer's responsibility, not just bookkeeping.
    # Include every referenced section in the packet so a reviewer can actually inspect
    # the content whose digest will later make the record stale.
    reviewed_campaign = {name for name in invalidation_sections(role, campaign)
                         if not name.startswith("@")}
    projected = {key: value for key, value in campaign.items() if key in reviewed_campaign}
    result = {key: frozen[key] for key in scope["top_level"] if key in frozen}
    result["campaign"] = projected
    return result


def packet_identity(packet: dict[str, Any]) -> dict[str, Any]:
    """The immutable packet bytes that a reviewer is expected to inspect."""
    return {key: packet[key] for key in (
        "packet_version", "campaign_id", "role", "content_version", "content_digest",
        "rubric", "rubric_digest", "instructions", "scoped_sections", "reviewed_sections",
        "campaign",
    )}


def packet_contract_identity(packet: dict[str, Any]) -> dict[str, Any]:
    """Review rules independent of the campaign content they are applied to.

    Per-section binding intentionally preserves a review when an unrelated campaign
    section changes. It must not preserve one when the packet instructions, embedded
    schema, rubric, or role scope changes.
    """
    return {
        "packet_version": packet["packet_version"],
        "role": packet["role"],
        "rubric": packet["rubric"],
        "rubric_digest": packet["rubric_digest"],
        "instructions": packet["instructions"],
        "scoped_sections": packet["scoped_sections"],
        "reviewed_section_names": sorted(packet["reviewed_sections"]),
    }


def freeze_and_packets(campaign_dir: Path, state: dict[str, Any]) -> tuple[str, str, list[Path]]:
    campaign_working_dir(campaign_dir, create=True)
    reviews = state.get("reviews")
    if not isinstance(reviews, dict):
        raise SystemExit("Cannot freeze: reviews must be an object")
    records = reviews.get("records", [])
    if not isinstance(records, list):
        raise SystemExit("Cannot freeze: reviews.records must be a list")
    packet_metadata = reviews.get("packet_metadata", {})
    if not isinstance(packet_metadata, dict):
        raise SystemExit("Cannot freeze: reviews.packet_metadata must be an object")
    current_packets = reviews.get("current_packets", {})
    if not isinstance(current_packets, dict):
        raise SystemExit("Cannot freeze: reviews.current_packets must be an object")
    digest = content_digest(state)
    r_digest = rubric_digest(state["profile"])
    leaves = section_digests(state)
    reviews["frozen_content_digest"] = digest
    reviews["rubric_digest"] = r_digest
    reviews["section_digests"] = leaves
    # Records for sections that did not move survive the re-freeze: a repair to one
    # section no longer forces every reviewer to start over.
    reviews["records"] = [
        item for item in records
        if record_is_current(item, state, leaves)
    ]
    # Retain only metadata that still authenticates a surviving review. Current
    # packets are rebuilt below, so obsolete freezes do not accumulate forever.
    surviving_packet_digests = {
        item.get("packet_digest") for item in reviews["records"]
        if isinstance(item, dict) and isinstance(item.get("packet_digest"), str)
    }
    packet_metadata = {
        digest: metadata for digest, metadata in packet_metadata.items()
        if digest in surviving_packet_digests
    }
    current_packets = {}
    reviews["packet_metadata"] = packet_metadata
    reviews["current_packets"] = current_packets
    packet_dir = campaign_dir / REVIEW_DIR_REL
    staged = staged_directory(packet_dir)
    names: list[str] = []
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
                "review_object": (
                    "Review the prospective campaign contract and the truthfulness of its current-state "
                    "claims; do not review it as though the planned execution has already occurred."
                ),
                "future_evidence_rule": (
                    "Do not report a missing future artifact as a defect when the starting point says the "
                    "campaign is unstarted and the contract makes that artifact a prerequisite. Do report "
                    "a missing or ambiguous prerequisite, an unsupported present-tense claim, or authority "
                    "granted before the prerequisite is verified."
                ),
                "scope_boundary_rule": (
                    "Assess only the sections and concerns assigned by this packet's scope note. Do not "
                    "report a section or operational detail assigned to another reviewer as missing merely "
                    "because it is intentionally omitted from this packet."
                ),
                "finding_policy": (
                    "Identify every material finding. Return at most the three highest-priority findings; "
                    "if more exist, use verdict block and state the total count and highest severity in the "
                    "summary. The cap limits returned detail, not disclosure."
                ),
                "required_output_schema": read_json(SKILL_DIR / "assets/review.schema.json"),
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
        packet["packet_digest"] = sha256_json(packet_identity(packet))
        contract_digest = sha256_json(packet_contract_identity(packet))
        packet_metadata[packet["packet_digest"]] = {
            "role": role,
            "packet_digest": packet["packet_digest"],
            "contract_digest": contract_digest,
            "content_digest": digest,
            "rubric_digest": r_digest,
            "reviewed_sections": copy.deepcopy(packet["reviewed_sections"]),
        }
        current_packets[role] = packet["packet_digest"]
        name = f"{role}.json"
        path = staged / name
        write_json(path, packet)
        names.append(name)
    # The first filter above handles campaign-section changes against the previous
    # freeze. Recheck after rebuilding packets so a review produced under an older
    # instruction/schema/scope contract cannot survive merely because its sections
    # stayed byte-identical.
    reviews["records"] = [
        item for item in reviews["records"]
        if record_is_current(item, state, leaves)
    ]
    retained_digests = set(current_packets.values()) | {
        item.get("packet_digest") for item in reviews["records"]
        if isinstance(item, dict) and isinstance(item.get("packet_digest"), str)
    }
    reviews["packet_metadata"] = {
        packet_digest: metadata for packet_digest, metadata in packet_metadata.items()
        if packet_digest in retained_digests
    }
    commit_state_and_directory(campaign_dir, state, staged, packet_dir)
    paths = [packet_dir / name for name in names]
    return digest, r_digest, paths


def cmd_quality_loop(args: argparse.Namespace) -> None:
    campaign_dir = resolve_campaign(args.campaign)
    campaign_working_dir(campaign_dir, create=True)
    state = load_state(campaign_dir)
    if workflow_state(state).get("artifact_level") == "brief":
        raise SystemExit("A brief has no campaign review loop; use `brief-finalize` or promote it")
    pre = validate_plan_content(state, include_reviews=False)
    write_json(campaign_working_dir(campaign_dir) / VALIDATION_REL.name, pre)
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
        "review_packets_to_execute": ([str(path) for path in paths
                                       if path.stem in needs_review] if pre["valid"] else []),
        "review_packets_all": [str(path) for path in paths],
        "reviews_still_current": still_current,
        "roles_requiring_review": needs_review if pre["valid"] else [],
        "roles_pending_after_design_repair": needs_review if not pre["valid"] else [],
        "next_action": "Resolve deterministic errors before review" if not pre["valid"] else _review_next_action(needs_review),
    }
    write_json(campaign_working_dir(campaign_dir) / "quality_loop.json", payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def review_status(state: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Which required reviews survived the freeze, and which must actually be re-run."""
    records = state.get("reviews", {}).get("records", [])
    leaves = section_digests(state)
    held = {item.get("role") for item in records
            if isinstance(item, dict) and record_is_current(item, state, leaves)}
    required = PROFILES[state["profile"]]["review_roles"]
    return sorted(role for role in required if role in held), sorted(role for role in required if role not in held)


def _review_next_action(needs_review: list[str]) -> str:
    if not needs_review:
        return "All required reviews are current; run finalize"
    return ("Execute only these review packets as separate read-only reviewers, ingest each record, then finalize: "
            + ", ".join(needs_review))


def review_record_errors(record: Any) -> list[str]:
    if not isinstance(record, dict):
        return ["review record must be an object"]
    errors: list[str] = []
    for field in ("role", "reviewer_id", "mode", "verdict", "content_digest", "rubric_digest", "summary"):
        value = record.get(field)
        if field not in record or value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"missing {field}")
        elif not isinstance(value, str):
            errors.append(f"invalid {field}" if field.endswith("_digest") else f"invalid {field} type")
    for field in ("content_digest", "rubric_digest"):
        value = record.get(field)
        if isinstance(value, str) and value.strip() and not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
            errors.append(f"invalid {field}")
    if "packet_digest" in record and (
        not isinstance(record.get("packet_digest"), str)
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", record.get("packet_digest", ""))
    ):
        errors.append("invalid packet_digest")
    inspected = record.get("evidence_inspected")
    if ("evidence_inspected" in record
            and (not isinstance(inspected, list)
                 or any(not isinstance(item, str) or not item.strip() for item in inspected))):
        errors.append("evidence_inspected must be a list of non-empty strings")
    reviewed = record.get("reviewed_sections")
    if reviewed is not None:
        if not isinstance(reviewed, dict) or not reviewed:
            errors.append("reviewed_sections must be a non-empty object")
        elif any(
            not isinstance(name, str) or not name
            or not isinstance(digest, str)
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest)
            for name, digest in reviewed.items()
        ):
            errors.append("reviewed_sections contains an invalid section digest")
    # `findings` is required but may legitimately be empty: a reviewer that found
    # nothing must not be pushed into inventing a filler finding to pass.
    if "findings" not in record:
        errors.append("missing findings")
    if not isinstance(record.get("mode"), str) or record.get("mode") not in REVIEW_MODES:
        errors.append("invalid mode")
    evidence_present = "execution_evidence" in record
    evidence = record.get("execution_evidence")
    if evidence_present and not isinstance(evidence, dict):
        errors.append("execution_evidence must be an object")
    if (isinstance(record.get("mode"), str)
            and record["mode"] in INDEPENDENCE_CLAIMING_MODES
            and not isinstance(evidence, dict)):
        errors.append(f"mode {record['mode']} requires execution_evidence (self-attested; recorded for audit)")
    if isinstance(evidence, dict):
        executor_id = evidence.get("executor_id")
        if "executor_id" not in evidence or executor_id is None \
                or (isinstance(executor_id, str) and not executor_id.strip()):
            errors.append("execution_evidence missing executor_id")
        elif not isinstance(executor_id, str):
            errors.append("execution_evidence invalid executor_id")
        for field in ("started_at", "completed_at"):
            value = evidence.get(field)
            if field not in evidence or value is None or (isinstance(value, str) and not value.strip()):
                errors.append(f"execution_evidence missing {field}")
            elif not _is_iso_timestamp(value):
                errors.append(f"execution_evidence invalid {field}")
        if ("host" in evidence
                and (not isinstance(evidence["host"], str)
                     or not evidence["host"].strip())):
            errors.append("execution_evidence invalid host")
    if (not isinstance(record.get("verdict"), str)
            or record.get("verdict") not in REVIEW_VERDICTS):
        errors.append("invalid verdict")
    if not isinstance(record.get("findings"), list):
        errors.append("findings must be a list")
    else:
        if len(record["findings"]) > 3:
            errors.append("findings must contain at most three highest-priority items")
        for index, finding in enumerate(record["findings"]):
            if not isinstance(finding, dict):
                errors.append(f"finding {index} must be an object")
                continue
            if (not isinstance(finding.get("severity"), str)
                    or finding.get("severity") not in SEVERITIES):
                errors.append(f"finding {index} invalid severity")
            if (not isinstance(finding.get("action"), str)
                    or finding.get("action") not in FINDING_ACTIONS):
                errors.append(f"finding {index} invalid action")
            if not isinstance(finding.get("description"), str) or not finding.get("description", "").strip():
                errors.append(f"finding {index} description must be a non-empty string")
            affected = finding.get("affected_ids")
            if ("affected_ids" in finding
                    and (not isinstance(affected, list)
                         or any(not isinstance(item, str) or not item.strip()
                                for item in affected))):
                errors.append(f"finding {index} affected_ids must be a list of non-empty strings")
            remedy = finding.get("recommended_remedy")
            if ("recommended_remedy" in finding
                    and (not isinstance(remedy, str) or not remedy.strip())):
                errors.append(f"finding {index} recommended_remedy must be a non-empty string")
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
    current_digest = content_digest(state)
    reviews = state.get("reviews")
    if not isinstance(reviews, dict):
        raise SystemExit("Cannot ingest review: reviews must be an object")
    if reviews.get("frozen_content_digest") != current_digest:
        raise SystemExit(
            "Cannot ingest review: the campaign has no current content freeze; "
            "run quality-loop first"
        )
    if reviews.get("rubric_digest") != current_rubric:
        raise SystemExit(
            "Cannot ingest review: the campaign freeze uses an older rubric; "
            "run quality-loop again"
        )
    packet_digest = record.get("packet_digest")
    metadata_map = reviews.get("packet_metadata")
    current_packets = reviews.get("current_packets")
    if (not isinstance(metadata_map, dict) or not isinstance(current_packets, dict)
            or not isinstance(packet_digest, str)):
        raise SystemExit(
            "Cannot ingest review: packet_digest and current role packet metadata are required; "
            "copy them from the role packet"
        )
    if current_packets.get(record["role"]) != packet_digest:
        raise SystemExit(
            "Cannot ingest review: packet_digest is not the current role packet; "
            "use the packet produced by the latest quality-loop"
        )
    metadata = metadata_map.get(packet_digest)
    if not isinstance(metadata, dict):
        raise SystemExit("Cannot ingest review: packet_digest is not from a current role packet")
    if (metadata.get("content_digest") != current_digest
            or metadata.get("rubric_digest") != current_rubric):
        raise SystemExit(
            "Cannot ingest review: packet metadata is not bound to the current freeze"
        )
    if (metadata.get("role") != record.get("role")
            or metadata.get("content_digest") != record.get("content_digest")
            or metadata.get("rubric_digest") != record.get("rubric_digest")
            or metadata.get("reviewed_sections") != record.get("reviewed_sections")):
        raise SystemExit(
            "Cannot ingest review: packet metadata, content_digest, rubric_digest, or "
            "reviewed_sections do not match the role packet"
        )
    packet_dir = campaign_directory(campaign_dir, REVIEW_DIR_REL, "review packet directory")
    packet_path = packet_dir / f"{record['role']}.json"
    if packet_path.is_symlink() or not packet_path.is_file():
        raise SystemExit("Cannot ingest review: the current role packet is missing or not a regular file")
    packet = read_json(packet_path)
    if (packet.get("packet_digest") != packet_digest
            or sha256_json(packet_identity(packet)) != packet_digest
            or packet.get("role") != record.get("role")
            or packet.get("reviewed_sections") != record.get("reviewed_sections")):
        raise SystemExit("Cannot ingest review: the role packet bytes do not match its metadata")
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
    records = [item for item in reviews.get("records", [])
               if isinstance(item, dict) and item.get("role") != record["role"]]
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


def _starting_point_block(state: dict[str, Any]) -> str:
    campaign = state.get("campaign", {})
    if "starting_point" not in campaign:
        return "**Entry mode:** New project — legacy campaign with no starting-point record."
    point = campaign.get("starting_point", {})
    if point.get("entry_mode") == "new-project":
        return "**Entry mode:** New project — no prior project state was supplied."
    if point.get("entry_mode") != "existing-project":
        return "**Entry mode:** Not recorded or invalid."
    lines = [
        "**Entry mode:** Existing project",
        f"\n**Status as of:** {point.get('status_as_of') or 'Not recorded'}",
        f"\n**Status summary:** {point.get('status_summary') or 'Not recorded'}",
    ]
    for key, label in (
        ("assessment_basis", "Assessment basis"),
        ("accepted_completed_work", "Accepted as completed"),
        ("work_in_progress", "Work in progress"),
        ("inherited_artifacts", "Inherited artifacts"),
        ("decisions_in_force", "Decisions already in force"),
        ("known_deviations", "Known deviations"),
        ("requires_recheck", "Requires recheck"),
    ):
        lines.extend([f"\n**{label}**", _md_list(point.get(key))])
    lines.append(f"\n**Decision frontier recorded at adoption:** {point.get('next_decision') or 'Not recorded'}")
    return "\n".join(lines)


def _planning_origin_block(state: dict[str, Any]) -> str:
    workflow = workflow_state(state)
    promotion = workflow.get("promotion") if isinstance(workflow.get("promotion"), dict) else {}
    if promotion.get("status") == "accepted":
        return (
            "**Planning origin:** Promoted from an accepted research brief "
            f"`{promotion.get('brief_digest', '')}` via `{promotion.get('source', '')}`."
        )
    return "**Planning origin:** Camp-full selected directly."


def render_research_brief(state: dict[str, Any]) -> str:
    sketch = state.get("sketch", {})
    dimensions = state.get("intent_dimensions", [])
    unresolved = [
        item for item in dimensions
        if isinstance(item, dict) and item.get("status") not in COMPLETE_DIMENSION_STATUSES
    ]
    decisions = [
        item for item in dimensions
        if isinstance(item, dict) and item.get("status") in COMPLETE_DIMENSION_STATUSES
    ]
    blockers = [
        item for item in state.get("blockers", [])
        if isinstance(item, dict) and item.get("status", "open") == "open"
    ]
    lines = [
        f"# Research brief — {state.get('title', '')}", "",
        "**Status:** BRIEF-READY — NON-EXECUTABLE", "",
        f"**Brief digest:** `{brief_digest(state)}`", "",
        "## Goal", "", state.get("goal_verbatim", ""), "",
        "## Starting point", "", _starting_point_block(state), "",
        "## Decision or purpose", "", sketch.get("decision_or_purpose", ""), "",
        "## Scope", "", sketch.get("scope", ""), "",
        "## Non-goals", "", _md_list(sketch.get("non_goals")), "",
        "## Core inquiries", "", _md_list(sketch.get("core_inquiries")), "",
        "## Likely evidence", "", _md_list(sketch.get("likely_evidence")), "",
        "## Rough method and stages", "", _md_list(sketch.get("rough_methods_stages")), "",
        "## Success or adjudication", "", sketch.get("success_or_adjudication", ""), "",
        "## Assumptions and risks", "",
        _md_list(list(sketch.get("assumptions_risks", [])) + list(state.get("assumptions", []))), "",
        "## Proposed outputs", "", _md_list(sketch.get("proposed_outputs")), "",
        "## Decisions already made", "",
    ]
    if decisions:
        lines.extend(
            f"- **{item.get('label') or item.get('id')}:** {_fmt_value(item.get('value'))} "
            f"({item.get('status')})"
            for item in decisions
        )
    else:
        lines.append("*None recorded.*")
    interview = state.get("interview", {})
    turns = interview.get("turns", []) if isinstance(interview, dict) else []
    lines.extend(["", "## Interview record", ""])
    if turns:
        for item in turns:
            lines.extend([
                f"- **Q{item.get('number', '?')}:** {item.get('question', '')}",
                f"  - **Answer:** {item.get('answer_verbatim', '')}",
                f"  - **Recorded decision:** {_fmt_value(item.get('normalized_decision', ''))}",
            ])
    else:
        lines.append("*No interview questions were needed.*")
    lines.extend([
        "", f"**Stopping reason:** {interview.get('stopping_reason', '')}",
        f"**Stopping note:** {interview.get('stopping_note') or 'None recorded'}",
    ])
    lines.extend(["", "## Unknowns and blockers", ""])
    for item in unresolved:
        lines.append(
            f"- **{item.get('label') or item.get('id')}:** {item.get('reason') or 'Unresolved'}"
        )
    for item in blockers:
        lines.append(
            f"- **{item.get('id', 'blocker')}:** {item.get('description', '')}"
        )
    if not unresolved and not blockers:
        lines.append("*No material unknowns or blockers recorded.*")
    lines.extend([
        "", "## Next action", "", sketch.get("next_action", ""), "",
        "Keep this as a planning brief, or promote it to Camp-full before delegating or executing work.",
        "",
    ])
    return "\n".join(lines)


def render_brief_outputs(campaign_dir: Path, state: dict[str, Any],
                         validation: dict[str, Any]) -> dict[str, Any]:
    campaign_working_dir(campaign_dir, create=True)
    out_dir = campaign_dir / OUTPUT_DIR_REL
    staged = staged_directory(out_dir)
    try:
        content = render_research_brief(state)
        atomic_write(staged / "RESEARCH_BRIEF.md", content)
        manifest = {"RESEARCH_BRIEF.md": sha256_bytes(content.encode("utf-8"))}
        manifest_text = "\n".join(
            f"{digest}  {name}" for name, digest in sorted(manifest.items())
        ) + "\n"
        atomic_write(staged / "MANIFEST.sha256", manifest_text)
    except BaseException:
        if staged.exists():
            shutil.rmtree(staged)
        raise
    manifest["MANIFEST.sha256"] = sha256_bytes(manifest_text.encode("utf-8"))
    state["status"] = validation["release_status"]
    state["last_validation"] = validation
    state["outputs"] = {
        "last_rendered_digest": brief_digest(state),
        "status": "BRIEF-READY — NON-EXECUTABLE",
        "manifest": manifest,
    }
    try:
        commit_state_and_directory(campaign_dir, state, staged, out_dir)
    except BaseException:
        if staged.exists():
            shutil.rmtree(staged)
        raise
    return {
        "rendered": True,
        "status": "BRIEF-READY — NON-EXECUTABLE",
        "output_dir": str(out_dir),
        "manifest": manifest,
        "validation": validation,
    }


def cmd_brief_finalize(args: argparse.Namespace) -> None:
    campaign_dir = resolve_campaign(args.campaign)
    campaign_working_dir(campaign_dir, create=True)
    state = load_state(campaign_dir)
    workflow = workflow_state(state)
    if workflow.get("artifact_level") != "brief":
        raise SystemExit("This state is already Camp-full; use the full render/finalize path")

    pre = validate_brief_content(state)
    if not pre["valid"]:
        out_dir = campaign_dir / OUTPUT_DIR_REL
        if out_dir.exists():
            shutil.rmtree(out_dir)
        state["outputs"] = {"last_rendered_digest": "", "manifest": {}}
        state["last_validation"] = pre
        write_json(campaign_working_dir(campaign_dir) / BRIEF_VALIDATION_REL.name, pre)
        save_state(campaign_dir, state)
        print(json.dumps({
            "rendered": False, "status": "brief-draft", "validation": pre,
            "next_action": "Resolve the brief findings, then rerun brief-finalize",
        }, indent=2, ensure_ascii=False))
        raise SystemExit(2)

    promotion = workflow["promotion"]
    promotion_offered_now = False
    if workflow.get("requested_mode") == "auto" and promotion.get("status") == "pending":
        promotion.update({
            "status": "offered",
            "brief_digest": brief_digest(state),
            "answer_verbatim": "",
            "source": "auto-prompt",
            "offered_at": now_iso(),
            "decided_at": "",
        })
        promotion_offered_now = True

    validation = validate_brief_content(state)
    write_json(campaign_working_dir(campaign_dir) / BRIEF_VALIDATION_REL.name, validation)
    result = render_brief_outputs(campaign_dir, state, validation)
    result["promotion_prompt"] = (
        {
            "question": "The research brief is ready. Promote it to Camp-full?",
            "choices": ["Promote to Camp-full", "Keep brief"],
        }
        if promotion_offered_now else None
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_promotion(args: argparse.Namespace) -> None:
    campaign_dir = resolve_campaign(args.campaign)
    campaign_working_dir(campaign_dir, create=True)
    state = load_state(campaign_dir)
    workflow = workflow_state(state)
    promotion = workflow.get("promotion", {})

    if workflow.get("artifact_level") == "full":
        if promotion.get("status") == "accepted" and args.decision == "accept":
            print(json.dumps({
                "changed": False, "artifact_level": "full",
                "promotion_status": "accepted", "brief_digest": promotion.get("brief_digest", ""),
            }, indent=2))
            return
        raise SystemExit("This state is already Camp-full")

    if args.source not in PROMOTION_SOURCES:
        raise SystemExit("Invalid promotion source")
    if not _required_text(args.answer):
        raise SystemExit("Promotion decisions require the user's verbatim answer")

    if args.decision == "decline":
        if args.source != "auto-prompt" or workflow.get("requested_mode") != "auto":
            raise SystemExit("Only the Camp-auto end prompt can record a decline")
        if promotion.get("status") == "declined":
            print(json.dumps({
                "changed": False, "artifact_level": "brief", "promotion_status": "declined",
                "brief_digest": promotion.get("brief_digest", ""),
            }, indent=2))
            return
        if promotion.get("status") != "offered":
            raise SystemExit("No current Camp-auto promotion offer is awaiting an answer")
        if promotion.get("brief_digest") != brief_digest(state):
            raise SystemExit("The promotion offer is bound to an older brief; finalize the current brief first")
        promotion.update({
            "status": "declined", "answer_verbatim": args.answer,
            "source": "auto-prompt", "decided_at": now_iso(),
        })
        state["status"] = "brief-ready"
        save_state(campaign_dir, state)
        print(json.dumps({
            "changed": True, "artifact_level": "brief", "promotion_status": "declined",
            "brief_digest": promotion.get("brief_digest", ""),
        }, indent=2))
        return

    if args.decision != "accept":
        raise SystemExit("Invalid promotion decision")
    if args.source == "auto-prompt" and promotion.get("status") != "offered":
        raise SystemExit("No current Camp-auto promotion offer is awaiting acceptance")

    validation = validate_brief_state(state)
    if not validation["valid"]:
        write_json(campaign_working_dir(campaign_dir) / BRIEF_VALIDATION_REL.name, validation)
        raise SystemExit("The current brief is not ready; resolve brief validation before promotion")
    accepted_digest = brief_digest(state)
    accepted_brief = copy.deepcopy(brief_payload(state))
    decided_at = now_iso()
    promotion.update({
        "status": "accepted", "brief_digest": accepted_digest,
        "accepted_brief": accepted_brief,
        "answer_verbatim": args.answer, "source": args.source,
        "decided_at": decided_at,
    })
    workflow["artifact_level"] = "full"
    point = state.get("campaign", {}).get("starting_point", {})
    defaults = campaign_template(point.get("entry_mode", "new-project"))
    campaign = state.setdefault("campaign", {})
    for key, value in defaults.items():
        campaign.setdefault(key, value)
    sketch = state["sketch"]
    mission = campaign["mission"]
    if not _required_text(mission.get("decision_or_purpose")):
        mission["decision_or_purpose"] = sketch["decision_or_purpose"]
    if not _required_text(mission.get("scope")):
        mission["scope"] = sketch["scope"]
    if not _required_list(mission.get("non_goals")):
        mission["non_goals"] = copy.deepcopy(sketch["non_goals"])
    if not _required_text(mission.get("completion_definition")):
        mission["completion_definition"] = sketch["success_or_adjudication"]
    soft_limit, hard_limit = question_limits(state["profile"], "full")
    state["interview"]["soft_limit"] = soft_limit
    state["interview"]["hard_limit"] = hard_limit
    state["reviews"] = {
        "frozen_content_digest": "", "rubric_digest": "", "records": [],
        "packet_metadata": {}, "current_packets": {},
    }
    state["status"] = "full-draft"
    state["content_version"] += 1
    save_state(campaign_dir, state)
    print(json.dumps({
        "changed": True, "artifact_level": "full", "promotion_status": "accepted",
        "brief_digest": accepted_digest,
        "next_action": "Continue Camp-full from the preserved decisions; ask only missing full-campaign questions",
    }, indent=2))


def cmd_migrate(args: argparse.Namespace) -> None:
    campaign_dir = resolve_campaign(args.campaign)
    state = load_state(campaign_dir)
    current = state.get("schema_version")
    if current == SCHEMA_VERSION:
        print(json.dumps({"changed": False, "schema_version": SCHEMA_VERSION}, indent=2))
        return
    if current != "3.1":
        raise SystemExit(f"No migration path from schema {current!r} to {SCHEMA_VERSION}")
    malformed_containers = [
        key for key in ("campaign", "sketch")
        if key in state and not isinstance(state[key], dict)
    ]
    if malformed_containers:
        # Do not turn a malformed legacy container into an empty object and persist the
        # loss. Validate a private migration candidate only to give the harness a useful
        # repair report; the on-disk legacy state remains byte-for-byte untouched.
        candidate = copy.deepcopy(state)
        candidate["schema_version"] = SCHEMA_VERSION
        candidate["rescamp_version"] = VERSION
        candidate["workflow"] = workflow_state({})
        validation = validate_state(candidate, include_reviews=False)
        payload = {
            "changed": False, "from_schema": current, "schema_version": SCHEMA_VERSION,
            "planning_mode": "full", "status": "repair-required", "valid": False,
            "next_action": "Repair the malformed legacy containers, then rerun migrate",
            "validation": cap_validation_for_stdout(validation),
        }
        print(json.dumps(payload, indent=2))
        raise SystemExit(2)

    candidate = copy.deepcopy(state)
    candidate["schema_version"] = SCHEMA_VERSION
    candidate["rescamp_version"] = VERSION
    candidate["workflow"] = workflow_state({})
    campaign = candidate.get("campaign")
    if not isinstance(campaign, dict):
        campaign = {}
        candidate["campaign"] = campaign
    campaign.setdefault("starting_point", {"entry_mode": "new-project"})
    sketch = candidate.get("sketch")
    if not isinstance(sketch, dict):
        sketch = {}
        candidate["sketch"] = sketch
    # Schema 3.1 did not require these two fields. Reuse explicit existing
    # campaign fields when available; otherwise record conservative placeholders
    # that deliberately keep the migrated campaign in a repair-required state.
    if not _required_list(sketch.get("non_goals")):
        mission = campaign.get("mission") if isinstance(campaign.get("mission"), dict) else {}
        inherited = mission.get("non_goals")
        sketch["non_goals"] = copy.deepcopy(inherited) if _required_list(inherited) else [
            "No work outside the declared scope is authorized until migration is reviewed"
        ]
    if not _required_text(sketch.get("next_action")):
        kickoff = campaign.get("kickoff") if isinstance(campaign.get("kickoff"), dict) else {}
        inherited_action = kickoff.get("command") or candidate.get("next_action")
        sketch["next_action"] = inherited_action if _required_text(inherited_action) else (
            "Repair and validate the migrated sketch before execution"
        )
    candidate["status"] = "full-draft"
    old_content_version = candidate.get("content_version", 0)
    if isinstance(old_content_version, int) and not isinstance(old_content_version, bool):
        candidate["content_version"] = old_content_version + 1
    validation = validate_state(candidate, include_reviews=False)
    migration_status = "migrated" if validation["valid"] else "repair-required"
    save_state(campaign_dir, candidate)
    print(json.dumps({
        "changed": True, "from_schema": current, "schema_version": SCHEMA_VERSION,
        "planning_mode": "full", "status": migration_status,
        "valid": validation["valid"],
        "next_action": ("Revalidate and re-render stale outputs" if validation["valid"] else
                         "Repair the migrated fields listed in validation, then revalidate"),
        "validation": cap_validation_for_stdout(validation),
    }, indent=2))
    if not validation["valid"]:
        raise SystemExit(2)


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
    header = f"# Research Campaign Prompt: {state['title']}\n\n**Status:** {status}\n\n**Campaign ID:** `{state['campaign_id']}`\n\n**Content version:** {state['content_version']}\n\n**Content digest:** `{content_digest(state)}`\n\n**Profile:** {state['profile']}\n\n**Archetypes:** {', '.join(state['archetypes'])}\n"
    parts = [header, _section("0. Coverage and standing caveats", _coverage_note(state))]
    parts.append(_section("1. Campaign constitution", _md_list(camp["constitution"].get("rules")) + "\n\nEvery worker inherits these rules. Local briefs may narrow scope but may not weaken them."))
    parts.append(_section("2. Starting point, mission, boundaries, and deliverables", f"{_starting_point_block(state)}\n\n{_planning_origin_block(state)}\n\n**Decision or purpose:** {mission.get('decision_or_purpose','')}\n\n**Scope:** {mission.get('scope','')}\n\n**Non-goals**\n{_md_list(mission.get('non_goals'))}\n\n**Intended users**\n{_md_list(mission.get('intended_users'))}\n\n**Completion definition:** {mission.get('completion_definition','')}\n\n**Deliverables**\n\n{_render_objects(camp.get('deliverables'), 'campaign.deliverables')}"))
    dossier = camp["dossier"]
    parts.append(_section("3. Object and evidence dossier", f"**Objects, cases, corpus, population, or system**\n\n{_render_objects(dossier.get('objects'), 'campaign.dossier.objects')}\n\n**Context**\n\n{_render_objects(dossier.get('context'), 'campaign.dossier.context')}\n\n**Source hierarchy**\n\n{_render_objects(dossier.get('source_hierarchy'), 'campaign.dossier.source_hierarchy')}\n\n**Access and rights**\n\n{_render_objects(dossier.get('access_rights'), 'campaign.dossier.access_rights')}\n\n**Known alternatives**\n\n{_render_objects(dossier.get('alternatives'), 'campaign.dossier.alternatives')}"))
    parts.append(_section("4. Inquiry and evidence logic", "Each inquiry must be evaluated against admissible support and explicit counterevidence, rival explanations/readings, counterexamples, or objections.\n\n" + _render_objects(camp.get("inquiries"), "campaign.inquiries")))
    parts.append(_section("5. Method portfolio", _render_objects(camp.get("methods"), "campaign.methods")))
    parts.append(_section("6. Tools and production-like canaries", f"**Tools**\n\n{_render_objects(camp.get('tools'), 'campaign.tools')}\n\n**Canaries**\n\nA successful import or help command is not a canary.\n\n{_render_objects(camp.get('canaries'), 'campaign.canaries')}"))
    evaluation = camp["evaluation"]
    if camp.get("starting_point", {}).get("entry_mode") == "existing-project":
        freeze_statement = ("**Frozen before prospective production under this plan (asserted, not verified):** "
                            f"{evaluation.get('frozen_before_production_asserted')}\n\n"
                            "This assertion is not retroactive. Inherited artifacts and observed results keep "
                            "the evidentiary status established by their original protocol and provenance.")
    else:
        freeze_statement = ("**Frozen before production (asserted, not verified):** "
                            f"{evaluation.get('frozen_before_production_asserted')}")
    parts.append(_section("7. Frozen evaluation or adjudication instrument", f"{freeze_statement}\n\n**Criteria**\n{_md_list(evaluation.get('criteria'))}\n\n**Comparators, controls, cases, or adjudication rules**\n{_md_list(evaluation.get('comparators_or_adjudication'))}\n\n**Missing-evidence policy:** {evaluation.get('missing_evidence_policy','')}\n\n**Exploration versus confirmation:** {evaluation.get('exploration_confirmation_policy','')}\n\n**Stop, pivot, and no-go rules**\n{_md_list(evaluation.get('stop_pivot_no_go_rules'))}"))
    parts.append(_section("8. Staged funnel and promotion gates", f"**Stages**\n\n{_render_objects(camp.get('stages'), 'campaign.stages')}\n\n**Gates**\n\n{_render_objects(camp.get('gates'), 'campaign.gates')}"))
    resources = camp["resources_dispatch"]
    parts.append(_section("9. Resources and fail-closed dispatch", f"**Budgets**\n{_md_list(resources.get('budgets'))}\n\n**Access constraints**\n{_md_list(resources.get('access_constraints'))}\n\n**Concurrency:** {resources.get('concurrency','')}\n\n**Dispatch rules**\n{_md_list(resources.get('dispatch_rules'))}\n\n**Approvals**\n{_md_list(resources.get('approvals'))}"))
    parts.append(_section("10. Delegation", f"**Roles**\n\n{_render_objects(camp.get('roles'), 'campaign.roles')}\n\n**Bounded work units**\n\nDelegates return artifacts and concise findings, not unbounded narrative. A local brief may narrow scope but may not weaken the constitution.\n\n{_render_objects(camp.get('work_units'), 'campaign.work_units')}"))
    runtime = camp["runtime"]
    parts.append(_section("11. Durable operations and recovery", f"**Continuous runtime enabled:** {runtime.get('enabled')}\n\n**Continuation trigger:** {runtime.get('continuation_trigger','')}\n\n**State store:** {runtime.get('state_store','')}\n\n**Event log:** {runtime.get('event_log','')}\n\n**Checkpoint policy:** {runtime.get('checkpoint_policy','')}\n\n**Liveness:** {runtime.get('liveness','')}\n\n**Recovery:** {runtime.get('recovery','')}\n\n**Idempotency:** {runtime.get('idempotency','')}\n\nA conversational session is not a scheduler.\n\n**Plan continuity and amendments**\n\n{plan_continuity_protocol(state)}"))
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
    lines = [f"# Roadmap: {state['title']}", "", f"**Status:** {status}", "",
             f"**Purpose:** {camp['mission'].get('decision_or_purpose','')}", ""]
    if camp.get("starting_point", {}).get("entry_mode") == "existing-project":
        point = camp["starting_point"]
        lines.extend(["## Project state at adoption", "", point.get("status_summary") or "*Not recorded.*", "",
                      f"**Decision frontier recorded at adoption:** {point.get('next_decision') or 'Not recorded'}", ""])
    lines.extend(["## Stages", ""])
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
            if _nonempty(gate.get("checkpoint_review")):
                lines.append(f"- **Independent checkpoint review:** {_fmt_value(gate.get('checkpoint_review'))}")
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
        "records are bound to the exact frozen sections they inspected; distinct reviewer identities and distinct",
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
    if camp.get("starting_point", {}).get("entry_mode") == "existing-project":
        point = camp["starting_point"]
        lines.extend([f"**Adopted project status:** {point.get('status_summary') or 'Not recorded'}", "",
                      f"**Decision frontier recorded at adoption:** {point.get('next_decision') or 'Not recorded'}", ""])
    lines.extend(["## Start here", "", kickoff.get("command") or "*No kickoff command recorded.*", ""])
    lines.extend(["## First gate", ""])
    if gate:
        # Multi-criterion gates render as a list. `_fmt_value` indents for nesting
        # under a parent bullet, which is right in the roadmap but wrong here, where
        # the list is a top-level block: lstrip() alone un-indented only the first
        # criterion and left the rest nested beneath it. Use the top-level renderer.
        if isinstance(gate.get("criteria"), (list, tuple)):
            lines.extend([f"**{gate.get('id')}**", "", _md_list(gate.get("criteria"))])
        else:
            lines.append(f"**{gate.get('id')}** — {_fmt_value(gate.get('criteria')).lstrip()}")
        # `checkpoint_review` belongs here: the kickoff exists so execution can start
        # without rereading the whole plan, so omitting it let the first gate look
        # executable without the independent review it actually requires.
        for key, label in (("required_evidence", "Required evidence"),
                           ("checkpoint_review", "Independent checkpoint review"),
                           ("owner", "Owner"), ("on_fail", "On failure")):
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


def plan_continuity_protocol(state: dict[str, Any]) -> str:
    """A small runtime contract shared by the prompt and operator runbook."""
    digest = content_digest(state)
    contract = f"Use `campaign.json` at `{digest}` as the active contract."
    has_checkpoint_reviews = any(
        _nonempty(gate.get("checkpoint_review"))
        for gate in state.get("campaign", {}).get("gates", [])
        if isinstance(gate, dict)
    )
    if not has_checkpoint_reviews:
        return contract + """

If execution reveals a material plan change, pause affected future work, apply the explicit state edits, and run the targeted quality loop to freeze a new digest before continuing. Never rewrite a frozen plan in place: a pending brief carrying an older digest is stale, while completed artifacts remain bound to the version that produced them."""

    return contract + """ At every start or resume, load that contract, the latest checkpoint, open blockers, and the next bounded work unit; verify required inputs before acting.

At each major promotion gate, freeze the stage artifacts and a checkpoint receipt containing the plan digest, work completed, evidence, gate result, deviations, remaining budget, and next action. When the gate declares an independent checkpoint review, give a fresh read-only reviewer only those frozen artifacts, the relevant contract sections, and the rubric. The reviewer returns `pass`, `revise`, or `block` and presents at most three material findings, highest priority first. The cap bounds cost, not disclosure: if more material findings exist, the reviewer returns `block`, states how many it found and the highest severity among them, and presents only the top three. A capped review is never reported as a clean result. Repair once and recheck only the affected scope; after two review rounds, escalate any remaining blocker to the gate owner rather than continuing. Minor or stylistic suggestions go to the backlog.

For a broad campaign spanning multiple days or contexts, place one such review at each major execution stage that produces a decision-bearing artifact: eight major execution stages normally produce eight review gates, not a review after every task. Group small or low-risk steps, and add a further review only where it protects a distinct material decision.

Classify changes before continuing:

- **Operational:** retry, reorder, or substitute an equivalent tool inside frozen limits. Record it in the checkpoint; the plan version stays current.
- **Methodological:** change a method, intermediate criterion, sample, dependency, or stage design. Pause affected future work, apply the explicit state edits, freeze a new digest through `quality-loop`, and rerun only affected reviews.
- **Constitutional:** change the mission, primary evaluation or estimand, ethics or authority boundary, resource ceiling, stop rule, or permitted claim. Stop, obtain the required user or institutional approval, version the plan, and re-review every affected section. If production outcomes motivated the change, keep prior results under their original version and label the affected inference exploratory.

Never rewrite a frozen plan or completed record in place. A pending brief carrying an older digest is stale and must be regenerated; completed artifacts remain bound to the version that produced them."""


def runbook(state: dict[str, Any]) -> str:
    runtime = state["campaign"]["runtime"]
    resources = state["campaign"]["resources_dispatch"]
    return f"""# Operator runbook\n\n**Continuous runtime enabled:** {runtime.get('enabled')}\n\n## Start/resume trigger\n\n{runtime.get('continuation_trigger') or 'No autonomous continuation is authorized.'}\n\n## Canonical state and events\n\n- State: {runtime.get('state_store') or 'Not applicable'}\n- Events: {runtime.get('event_log') or 'Not applicable'}\n- Checkpoints: {runtime.get('checkpoint_policy') or 'Not applicable'}\n\n## Plan continuity and amendments\n\n{plan_continuity_protocol(state)}\n\n## Liveness and recovery\n\n- Liveness: {runtime.get('liveness') or 'Not applicable'}\n- Recovery: {runtime.get('recovery') or 'Not applicable'}\n- Idempotency: {runtime.get('idempotency') or 'Not applicable'}\n\n## Resource governor\n\n{_md_list(resources.get('budgets'))}\n\n## Fail-closed dispatch\n\n{_md_list(resources.get('dispatch_rules'))}\n\n## Approvals\n\n{_md_list(resources.get('approvals'))}\n"""


def render_blocking_errors(validation: dict[str, Any]) -> list[dict[str, str]]:
    """Errors that make the original state unsafe for renderers to dereference."""
    return [item for item in validation.get("errors", [])
            if item.get("code") in {"structure.type", "profile.invalid",
                                     "review.record_invalid", "review.duplicate_role"}]


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
    campaign_working_dir(campaign_dir, create=True)
    validation = validate_plan_content(state, include_reviews=True)
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
        "last_rendered_digest": render_digest(state),
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
    staged = staged_directory(out_dir)
    try:
        for name, content in files.items():
            atomic_write(staged / name, content)
            manifest[name] = sha256_bytes(content.encode("utf-8"))
        manifest_lines = [f"{digest}  {name}" for name, digest in sorted(manifest.items())]
        atomic_write(staged / "MANIFEST.sha256", "\n".join(manifest_lines) + "\n")
    except BaseException:
        if staged.exists():
            shutil.rmtree(staged)
        raise
    manifest["MANIFEST.sha256"] = sha256_bytes(("\n".join(manifest_lines) + "\n").encode("utf-8"))
    state["outputs"] = {"last_rendered_digest": render_digest(state), "status": status, "manifest": manifest}
    try:
        commit_state_and_directory(campaign_dir, state, staged, out_dir)
    except BaseException:
        if staged.exists():
            shutil.rmtree(staged)
        raise
    return {"rendered": True, "status": status, "output_dir": str(out_dir),
            "manifest": manifest, "validation": validation}


def cmd_render(args: argparse.Namespace) -> None:
    campaign_dir = resolve_campaign(args.campaign)
    state = load_state(campaign_dir)
    if workflow_state(state).get("artifact_level") == "brief":
        raise SystemExit("A brief renders through `brief-finalize`, not the full campaign renderer")
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
    campaign_working_dir(campaign_dir, create=True)
    state = load_state(campaign_dir)
    if workflow_state(state).get("artifact_level") == "brief":
        raise SystemExit("A research brief is non-executable; accept promotion before finalizing Camp-full")
    pre = validate_plan_content(state, include_reviews=False)
    if render_blocking_errors(pre):
        write_json(campaign_working_dir(campaign_dir) / VALIDATION_REL.name, pre)
        print(json.dumps(render_refusal(pre), indent=2, ensure_ascii=False))
        raise SystemExit(2)
    write_json(campaign_working_dir(campaign_dir) / VALIDATION_REL.name, pre)
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
    final_validation = validate_plan_content(state, include_reviews=True)
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
    workflow = workflow_state(state)
    is_brief = workflow.get("artifact_level") == "brief"
    if is_brief:
        pre = validate_brief_content(state)
        current = validate_brief_state(state)
        reviewed_plan = pre
        full = current
        review = {"required": [], "current": [], "missing": [], "blocking": [],
                  "independence_ok": True}
    else:
        pre = validate_plan_content(state, include_reviews=False)
        reviewed_plan = validate_plan_content(state, include_reviews=True)
        full = validate_state(state, include_reviews=True)
        review = reviewed_plan.get(
            "review",
            {"required": [], "current": [], "missing": [], "blocking": [],
             "independence_ok": False},
        )
    dimensions = [item for item in state.get("intent_dimensions", [])
                  if isinstance(item, dict)] \
        if isinstance(state.get("intent_dimensions"), list) else []
    unresolved = [item for item in dimensions
                  if item.get("status") not in COMPLETE_DIMENSION_STATUSES]
    priority = {"critical": 0, "material": 1, "low": 2}
    next_dimension = min(
        enumerate(unresolved),
        key=lambda pair: (priority.get(pair[1].get("importance"), 3), pair[0]),
        default=(0, None),
    )[1]
    blockers = [item for item in state.get("blockers", []) if isinstance(item, dict)] \
        if isinstance(state.get("blockers"), list) else []
    contradictions = [item for item in state.get("contradictions", [])
                      if isinstance(item, dict)] \
        if isinstance(state.get("contradictions"), list) else []
    open_blockers = [item for item in blockers
                     if item.get("status", "open") == "open"]
    campaign = state.get("campaign") if isinstance(state.get("campaign"), dict) else {}
    point = campaign.get("starting_point") \
        if isinstance(campaign.get("starting_point"), dict) else {}
    interview = state.get("interview") if isinstance(state.get("interview"), dict) else {}
    outputs = state.get("outputs") if isinstance(state.get("outputs"), dict) else {}
    output_stale = any(item.get("code") == "outputs.stale" for item in full.get("errors", []))
    derived_status = full.get("release_status", "brief-draft" if is_brief else "draft")
    promotion = workflow.get("promotion") if isinstance(workflow.get("promotion"), dict) else {}
    payload = {
        "campaign_id": state.get("campaign_id", ""), "title": state.get("title", ""),
        "status": derived_status, "profile": state.get("profile", ""),
        "archetypes": state.get("archetypes", []),
        "requested_mode": workflow.get("requested_mode"),
        "artifact_level": workflow.get("artifact_level"),
        "promotion": {
            "status": promotion.get("status"),
            "brief_digest": promotion.get("brief_digest", ""),
        },
        "content_version": state.get("content_version"),
        "content_digest": brief_digest(state) if is_brief else content_digest(state),
        "starting_point": {
            "entry_mode": (point.get("entry_mode") if "starting_point" in campaign
                           else "new-project"),
            "status_summary": point.get("status_summary", ""),
            "decisions_in_force": point.get("decisions_in_force", []),
            "requires_recheck": point.get("requires_recheck", []),
            "decision_frontier_at_adoption": point.get("next_decision", ""),
        },
        "interview": {
            "turns": len(interview.get("turns", [])) if isinstance(interview.get("turns"), list) else 0,
            "soft_limit": interview.get("soft_limit"), "hard_limit": interview.get("hard_limit"),
            "stopping_reason": interview.get("stopping_reason", ""),
            "unresolved_dimensions": [item.get("id") for item in unresolved],
            "next_branch": next_dimension.get("id") if next_dimension else None,
        },
        "decisions": [
            {key: item.get(key, "") for key in
             ("id", "label", "status", "value", "importance", "reason", "dependencies")}
            for item in dimensions
        ],
        "assumptions": state.get("assumptions", []),
        "open_contradictions": [item for item in contradictions
                                if item.get("status", "open") == "open"],
        "open_blockers": [
            {key: item.get(key, "") for key in ("id", "severity", "description", "owner", "unblocks")}
            for item in open_blockers
        ],
        "design_valid": pre.get("valid", False),
        "execution_ready": full.get("execution_ready", False),
        "design_errors": len(pre.get("errors", [])),
        "review_errors": (0 if is_brief else
                          max(0, len(reviewed_plan.get("errors", []))
                              - len(pre.get("errors", [])))),
        "review": review,
        "output_status": outputs.get("status", "not rendered"),
        "output_stale": output_stale,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def cmd_audit(args: argparse.Namespace) -> None:
    campaign_dir = resolve_campaign(args.campaign)
    campaign_working_dir(campaign_dir, create=True)
    state = load_state(campaign_dir)
    errors: list[str] = []
    out_dir = campaign_dir / OUTPUT_DIR_REL
    manifest_path = out_dir / "MANIFEST.sha256"
    verified: dict[str, bool] = {}
    # Canonical hashes come from state, not from the manifest sitting in the directory
    # being audited. Trusting that file alone let anyone with sha256sum tamper an artifact
    # and rewrite its one manifest line; the state copy also covers MANIFEST.sha256 itself.
    outputs = state.get("outputs") if isinstance(state.get("outputs"), dict) else {}
    recorded = outputs.get("manifest") if isinstance(outputs.get("manifest"), dict) else {}
    out_dir_safe = True
    if out_dir.is_symlink():
        errors.append("outputs must be a real directory inside the campaign, not a symlink")
        out_dir_safe = False
    elif out_dir.exists() and not out_dir.is_dir():
        errors.append("outputs must be a directory")
        out_dir_safe = False
    elif out_dir.exists():
        try:
            out_dir.resolve().relative_to(campaign_dir.resolve())
        except (OSError, ValueError):
            errors.append("outputs directory escapes the campaign")
            out_dir_safe = False

    if out_dir_safe and out_dir.exists():
        symlink_entries = sorted(
            path.relative_to(out_dir).as_posix()
            for path in out_dir.rglob("*")
            if path.is_symlink()
        )
        for name in symlink_entries:
            errors.append(f"outputs contains a symlink entry: {name}")

    if out_dir_safe and manifest_path.exists():
        if manifest_path.is_symlink() or not manifest_path.is_file():
            errors.append("MANIFEST.sha256 must be a regular file inside outputs")
            manifest_text = ""
            manifest_bytes = b""
        else:
            try:
                manifest_bytes = manifest_path.read_bytes()
                manifest_text = manifest_bytes.decode("utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                errors.append(f"could not read MANIFEST.sha256: {exc}")
                manifest_text = ""
                manifest_bytes = b""
        if not recorded:
            errors.append("outputs exist but state records no manifest; re-render before auditing")
        for line in manifest_text.splitlines():
            if not line.strip():
                continue
            if "  " not in line:
                errors.append("malformed MANIFEST.sha256 line")
                continue
            digest, name = line.split("  ", 1)
            relative = Path(name)
            if (not name or name == "." or relative.is_absolute()
                    or ".." in relative.parts):
                errors.append(f"manifest artifact path escapes outputs: {name}")
                verified[name] = False
                continue
            path = out_dir / relative
            try:
                path.resolve().relative_to(out_dir.resolve())
                contained = True
            except ValueError:
                contained = False
            if path.is_symlink() or not contained:
                errors.append(f"manifest artifact must be a regular file inside outputs: {name}")
                verified[name] = False
                continue
            try:
                actual = sha256_bytes(path.read_bytes()) if path.is_file() else None
            except OSError as exc:
                errors.append(f"could not read output artifact {name}: {exc}")
                actual = None
            ok = actual is not None and actual == digest
            if ok and recorded and name in recorded and recorded[name] != actual:
                ok = False
                errors.append(f"artifact does not match the hash recorded in state: {name}")
            verified[name] = ok
            if not ok and f"artifact does not match the hash recorded in state: {name}" not in errors:
                errors.append(f"artifact hash mismatch: {name}")
        manifest_digest = sha256_bytes(manifest_bytes) if manifest_bytes else ""
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
    elif not out_dir_safe:
        pass
    elif recorded:
        errors.append("state records a rendered bundle but MANIFEST.sha256 is missing; "
                      "the outputs directory has been removed or emptied")
    elif out_dir.exists() and any(out_dir.iterdir()):
        errors.append("outputs exist without MANIFEST.sha256")
    else:
        errors.append("no rendered output manifest exists; finalize the artifact before auditing")
    is_brief = workflow_state(state).get("artifact_level") == "brief"
    validation = (validate_brief_state(state) if is_brief
                  else validate_state(state, include_reviews=True))
    integrity_ok = not errors and validation.get("valid", False)
    execution_ready = validation.get("execution_ready", False)
    strict_ready = is_brief or (
        execution_ready and outputs.get("status") == "EXECUTION-READY"
    )
    result = {
        "audited_at": now_iso(), "campaign_id": state.get("campaign_id", ""),
        "content_digest": brief_digest(state) if is_brief else content_digest(state),
        "artifact_level": "brief" if is_brief else "full", "validation": validation,
        "artifact_verification": verified, "errors": errors,
        "integrity_ok": integrity_ok, "execution_ready": execution_ready,
        "ok": integrity_ok and (strict_ready if args.strict else True),
    }
    if args.strict and integrity_ok and not strict_ready:
        result["errors"].append(
            "strict audit requires an EXECUTION-READY full campaign bundle"
        )
    write_json(campaign_working_dir(campaign_dir) / "audit.json", result)
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
    level = workflow_state(state).get("artifact_level", "full")
    soft_limit, hard_limit = question_limits(args.profile, level)
    state["interview"]["soft_limit"] = soft_limit
    state["interview"]["hard_limit"] = hard_limit
    state["content_version"] += 1
    mark_content_changed(state)
    state["reviews"] = {
        "frozen_content_digest": "", "rubric_digest": "", "records": [],
        "packet_metadata": {}, "current_packets": {},
    }
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
    p.add_argument("--entry-mode", choices=sorted(ENTRY_MODES), default="new-project",
                   help="start from a new idea or adopt an existing project")
    p.add_argument("--planning-mode", choices=sorted(PLANNING_MODES), default="full",
                   help="start Camp-auto/Camp-brief at brief level, or Camp-full directly")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("migrate", help="migrate an older campaign state to the current schema")
    p.add_argument("campaign")
    p.set_defaults(func=cmd_migrate)

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

    p = sub.add_parser("brief-finalize", help="validate and render a non-executable research brief")
    p.add_argument("campaign")
    p.set_defaults(func=cmd_brief_finalize)

    p = sub.add_parser("promotion", help="record the user's brief-to-full decision")
    p.add_argument("campaign")
    p.add_argument("--decision", choices=sorted(PROMOTION_DECISIONS), required=True)
    p.add_argument("--source", choices=sorted(PROMOTION_SOURCES), required=True)
    p.add_argument("--answer", required=True)
    p.set_defaults(func=cmd_promotion)

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
    try:
        args.func(args)
    except SystemExit:
        raise
    except (AttributeError, KeyError, IndexError, TypeError, ValueError, OSError, UnicodeError) as exc:
        # Public CLI inputs include dotted paths, JSON/@file payloads, and
        # hand-authored review records. Normalize malformed inputs to one concise
        # diagnostic instead of leaking a Python traceback or partially successful
        # command narrative to an agent harness.
        raise SystemExit(f"Invalid campaign input or state: {exc}") from None
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
