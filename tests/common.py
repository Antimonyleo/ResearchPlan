from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE_PATH = ROOT / "rescamp/scripts/rescamp.py"
spec = importlib.util.spec_from_file_location("rescamp_engine", ENGINE_PATH)
engine = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(engine)


def complete_state(archetype: str = "evidence-synthesis", profile: str = "standard"):
    state = engine.default_state("A generalized research question", profile, [archetype], f"case-{archetype}")
    state["title"] = f"Generalized {archetype} campaign"
    state["sketch"].update({
        "decision_or_purpose": "Support a bounded research decision",
        "scope": "Defined case and evidence boundary",
        "core_inquiries": ["What conclusion is warranted?"],
        "likely_evidence": ["Primary and appropriate secondary evidence"],
        "rough_methods_stages": ["Dossier", "analysis", "challenge", "closeout"],
        "success_or_adjudication": "Predefined evidence and adjudication criteria",
        "assumptions_risks": ["Evidence may remain inconclusive"],
        "proposed_outputs": ["Campaign prompt", "roadmap"],
    })
    state["intent_dimensions"] = [
        {"id": "decision", "label": "Decision", "status": "resolved", "value": "bounded decision", "importance": "critical", "source": "user", "confidence": "high", "reason": "", "dependencies": []},
        {"id": "scope", "label": "Scope", "status": "resolved", "value": "bounded corpus/case", "importance": "material", "source": "user", "confidence": "high", "reason": "", "dependencies": []},
        {"id": "numeric-metrics", "label": "Numeric metrics", "status": "not-applicable", "value": "", "importance": "low", "source": "inferred", "confidence": "high", "reason": "Qualitative adjudication is appropriate", "dependencies": []},
    ]
    state["interview"].update({
        "turns": [
            {"number": 1, "branch": "decision", "question": "What decision?", "answer_verbatim": "A bounded decision", "normalized_decision": "bounded decision", "linked_dimensions": ["decision"], "decision_impact": "critical", "answer_utility": "high", "asked_at": engine.now_iso()},
            {"number": 2, "branch": "scope", "question": "What scope?", "answer_verbatim": "A bounded case", "normalized_decision": "bounded case", "linked_dimensions": ["scope"], "decision_impact": "material", "answer_utility": "high", "asked_at": engine.now_iso()},
        ],
        "stopping_reason": "material-completeness", "stopping_note": "All material dimensions resolved",
    })
    camp = state["campaign"]
    camp["constitution"] = {"worker_inheritance": True, "rules": [
        "Preserve evidence and provenance", "Do not exceed authority or approvals", "Report uncertainty, failures, and alternatives", "Verify artifacts before claims",
    ]}
    camp["mission"] = {
        "decision_or_purpose": "Determine the least overstated conclusion warranted by the evidence",
        "scope": "One bounded case/corpus/population and declared period",
        "non_goals": ["No unsupported generalization"], "intended_users": ["Research team"],
        "completion_definition": "Frozen criteria are applied, challenges addressed, and deliverables pass acceptance tests",
    }
    camp["dossier"] = {
        "objects": [{"id": "object-1", "description": "The defined research object or corpus"}],
        "context": ["Relevant disciplinary context"],
        "source_hierarchy": ["Primary evidence", "authoritative contextual evidence", "secondary synthesis"],
        "access_rights": ["Use only authorized materials"],
        "alternatives": ["At least one credible rival account"],
    }
    camp["inquiries"] = [{
        "id": "inq-1", "question_or_claim": "What conclusion is warranted within scope?",
        "importance": "It determines the campaign decision", "admissible_support": ["traceable evidence"],
        "counterevidence_or_rival": ["contrary evidence, rival explanation, counter-reading, or objection"],
        "discriminating_implication": "Evidence patterns should differentiate the accounts where possible",
        "verification_or_adjudication": "Apply the frozen discipline-appropriate rubric",
        "uncertainty_boundary": "Do not generalize beyond the declared scope",
        "reporting_rule": "Report support, counterevidence, and residual ambiguity",
    }]
    camp["methods"] = [{
        "id": "method-1", "inquiry_ids": ["inq-1"], "purpose": "Collect and analyze admissible evidence",
        "inputs": ["authorized sources"], "outputs": ["analysis artifact"],
        "assumptions": ["sources are authentic within documented limits"],
        "limitations": ["incomplete evidence may prevent adjudication"], "cost": "bounded",
        "dependencies": {"status": "not-applicable", "reason": "The method has no upstream method"},
        "can_change_decision": "Whether the evidence warrants the bounded conclusion",
    }]
    camp["tools"] = [{
        "id": "tool-1", "name": "Evidence processing workflow", "identity_version": "documented-v1",
        "production": True, "access_license": "authorized", "purpose": "Produce traceable analysis artifacts",
    }]
    camp["canaries"] = [{
        "id": "canary-1", "tool_id": "tool-1", "production_like_test": "Process one representative item end to end",
        "expected_artifacts": ["parseable output with provenance"],
        "sanity_checks": ["counts and citations match input"],
        "downstream_acceptance": "The analysis stage consumes the artifact without manual repair",
    }]
    camp["evaluation"] = {
        "frozen_before_production_asserted": True,
        "criteria": ["relevance", "source quality", "coherence", "counterevidence handling"],
        "comparators_or_adjudication": ["credible rival account", "negative or contrary case"],
        "missing_evidence_policy": "Mark inconclusive; do not impute decisive evidence",
        "exploration_confirmation_policy": "Exploration may revise questions; final adjudication uses the frozen version",
        "stop_pivot_no_go_rules": ["Stop if rights are absent", "Report inconclusive when evidence cannot adjudicate"],
    }
    camp["stages"] = [
        {"id": "stage-1", "purpose": "Dossier and canary", "activities": ["verify scope", "test tool"],
         "outputs": ["dossier", "canary artifact"], "owner": "campaign lead", "budget": "two agent-hours",
         "pace": "one checkpoint", "gate_id": "gate-1", "prerequisite_stage_ids": []},
        {"id": "stage-2", "purpose": "Evidence analysis and challenge", "activities": ["analyze evidence", "test rival account"],
         "outputs": ["analysis", "claims matrix"], "owner": "campaign lead", "budget": "six agent-hours",
         "pace": "complete after stage-1", "gate_id": "gate-2", "prerequisite_stage_ids": ["stage-1"]},
    ]
    camp["gates"] = [
        {"id": "gate-1", "stage_id": "stage-1", "criteria": ["scope and rights verified", "canary passes"], "required_evidence": ["dossier", "canary log"], "owner": "campaign lead", "on_fail": "repair or stop", "checkpoint_review": "Fresh operations reviewer inspects the frozen dossier and canary log; pass, revise, or block."},
        {"id": "gate-2", "stage_id": "stage-2", "criteria": ["claims trace to support and counterevidence"], "required_evidence": ["claims matrix"], "owner": "campaign lead", "on_fail": "revise conclusion or report inconclusive", "checkpoint_review": "Fresh methods reviewer inspects the frozen analysis and claims matrix; pass, revise, or block."},
    ]
    camp["resources_dispatch"] = {
        "budgets": ["Maximum eight agent-hours and no external spend without approval"],
        "access_constraints": ["Authorized sources only"], "concurrency": "At most two read-only workers",
        "dispatch_rules": ["Fail closed on missing prerequisite, stale state, absent approval, or failed canary"],
        "approvals": ["User approval before any external action"],
    }
    camp["roles"] = [{"id": "lead", "description": "Own canonical state and decisions"}, {"id": "reviewer", "description": "Read-only challenge"}]
    camp["runtime"] = {"enabled": False, "continuation_trigger": "", "state_store": "", "event_log": "", "checkpoint_policy": "", "liveness": "", "recovery": "", "idempotency": ""}
    camp["work_units"] = []
    camp["ethics_rights_safety"] = {
        "constraints": ["Respect applicable rights, privacy, consent, and disciplinary ethics"],
        "external_actions": [],
        "human_approval_points": [{"id": "publication-signoff", "description": "Approval before publication or external action where applicable"}],
    }
    camp["reporting"] = {
        "claim_rules": ["Separate observation, inference, assumption, and recommendation"],
        "negative_result_policy": "Preserve null, negative, failed, contradictory, and ambiguous evidence",
        "deviation_policy": "Version and disclose deviations from the frozen campaign",
        "least_favorable_interpretation": True,
    }
    camp["claims"] = [{
        "id": "claim-1", "inquiry_id": "inq-1", "statement": "A conclusion will be reported only if warranted",
        "support": ["analysis artifact"], "counterevidence_or_objections": ["rival account"],
        "verification": "Review against frozen rubric", "status": "planned",
        "reporting_rule": "Report inconclusive when support is insufficient",
    }]
    camp["deliverables"] = [{
        "id": "deliverable-1", "name": "Research campaign bundle", "path": "outputs/",
        "acceptance_test": "Required files exist, parse, cross-reference, and match manifest hashes", "owner": "campaign lead",
    }]
    camp["kickoff"] = {"command": "Open the frozen campaign and execute stage-1 only", "first_gate_id": "gate-1", "initial_backlog": ["Verify dossier", "Run tool canary"]}
    state["status"] = "candidate"
    return state


def add_passing_pilot(state):
    state["assurance"]["pilot"] = {
        "status": "passed", "content_digest": engine.content_digest(state),
        "authorized_by": "principal-investigator", "authority": "campaign owner",
        "executor_id": "pilot-session-1", "executed_at": engine.now_iso(),
        "scope": "one representative item", "resource_cap": "one agent-hour",
        "evidence": ["pilot-log@sha256"], "failures": [], "repairs": [],
    }
    return state


def add_passing_reviews(state, mode="independent-subagent"):
    if state["profile"] == "high-assurance" or state.get("assurance", {}).get("pilot_required") is True:
        add_passing_pilot(state)
    digest = engine.content_digest(state)
    rubric = engine.rubric_digest(state["profile"])
    records = []
    for index, role in enumerate(engine.PROFILES[state["profile"]]["review_roles"], 1):
        record = {
            "role": role, "reviewer_id": f"reviewer-{index}", "mode": mode,
            "verdict": "pass", "content_digest": digest, "rubric_digest": rubric,
            "summary": "No blocking defect found in the frozen campaign",
            "evidence_inspected": ["complete campaign state"], "findings": [],
        }
        if mode in engine.INDEPENDENCE_CLAIMING_MODES:
            record["execution_evidence"] = {
                "executor_id": f"executor-{index}",
                "started_at": engine.now_iso(), "completed_at": engine.now_iso(),
            }
        records.append(record)
    state["reviews"] = {"frozen_content_digest": digest, "rubric_digest": rubric, "records": records}
    return state
