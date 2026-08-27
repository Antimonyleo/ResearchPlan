# Automatic quality loop

The automatic loop runs for Camp-full after the interview stopping rule and whenever
`finalize` runs or an explicit revision is applied. Camp-auto and Camp-brief use brief validation and render
`RESEARCH_BRIEF.md`; they enter this loop only after an accepted promotion. This is
current-campaign quality assurance, not a full comparative benchmark.

These reviews approve a plan version before execution. A broad long-running campaign may also require fresh reviews at major execution checkpoints; those inspect stage artifacts and decide whether the current plan remains usable. They do not reuse or replace the records here. See `architecture.md`, sections 8 and 11.

Phases A–D inspect a static artifact. They can show that the campaign is coherent, complete, and internally consistent; they cannot show that it survives contact with the work. That is a weaker guarantee than it appears, and the campaign must say so. Phase E is how a campaign earns the stronger one.

## Phase A — freeze

1. Normalize and save the campaign.
2. Compute a canonical SHA-256 digest over substantive state.
3. Freeze the review rubric and compute its digest.
4. Recompute one digest per campaign section, plus the whole-campaign digest that seals the rendered bundle. A prior review stays valid while every section it is responsible for is unchanged, and goes stale when one moves. A review is responsible for the sections in its packet plus the sections those reference — a gate that names a method is reviewing that method too. Any rubric change stales everything.

## Phase B — deterministic validation

Check:

- required architecture sections proportional to profile;
- unresolved critical intent dimensions;
- duplicate IDs and broken references;
- stage graph cycles and gate ownership;
- claims/questions linked to support and disconfirming evidence or objections;
- production tools linked to canaries;
- deliverables linked to acceptance tests;
- budget, approval, and external-action boundaries;
- question-budget compliance and stopping reason;
- long-running work linked to a real continuation mechanism;
- review records bound to the current content and rubric digests.

## Phase C — proportional challenge

Create immutable review packets. Prefer separately executed, read-only reviewers.

- `scoped`: skeptical completeness and proportionality.
- `standard`: methods/evidence plus operations/reproducibility.
- `high-assurance`: methods/evidence, operations/reproducibility, and ethics/safety/claim integrity.

A host without independent subagents may perform labeled sequential challenge for scoped or provisional work. It must not satisfy a high-assurance independence requirement.

Every reviewer here sits on an internal rung of the independence ladder in `architecture.md`, section 15. None of them is external validation. Record which rung each review reached and carry it into the release decision unchanged.

Review the prospective campaign contract and its current-state claims, not an imagined
completed execution. A future artifact is not missing evidence when the campaign is candidly
unstarted and makes that artifact a prerequisite. It is a finding when the prerequisite itself
is missing or ambiguous, a current claim is unsupported, or authority is granted before the
future evidence is verified. Return at most the three highest-priority findings. If more exist,
return `block` and disclose the total count and highest severity in the summary; the cap limits
detail, not disclosure. Review only the concerns assigned by the packet's scope note; a section
or operational detail assigned to another reviewer is not missing merely because that packet
intentionally omits it.

Reviewer output contains verdict (`pass`, `revise`, `block`), findings, affected object IDs, evidence inspected, severity, recommended remedy, reviewer identity, execution mode, both content/rubric digests, and the packet's `packet_digest` and `reviewed_sections` copied verbatim. Ingestion rejects a record that is not bound to the current role packet.
Records using `independent-subagent`, `separate-session`, or `external-human` must also
include `execution_evidence`; a `sequential-pass` record cannot imply independence.

## Phase D — repair and re-interview

Classify findings:

- `agent-fix`: synthesis, missing cross-reference, wording, formatting, or derivation resolvable from existing evidence;
- `user-answer`: private intent, authority, tradeoff, access, or acceptance decision;
- `external-approval`: ethics, legal, institutional, data, safety, or stakeholder approval;
- `accepted-risk`: explicit, bounded risk accepted by an authorized person.

Apply agent fixes first. If user answers are needed, ask at most one question, or two when inseparable, selected by downstream impact. Re-freeze after every substantive change and rerun all affected checks.

## Phase E — bounded pilot, then freeze

Reading a plan is not the same as watching it fail. Before freezing a high-assurance or expensive campaign, run a bounded pilot of the compiled campaign itself and repair what actually breaks.

A pilot is:

- cheap and explicitly capped — a small fraction of the budget, one stage, one stratum, a handful of objects, a short window;
- run against the rendered artifacts, not a paraphrase, so that a defect in the prompt is a defect the pilot can expose;
- exploratory by declaration; nothing it produces enters a confirmatory result;
- instrumented to record failures, not just outcomes.

Record for each failure: what broke, which section of the campaign permitted or caused it, whether it was a plan defect, a tool defect, an access defect, or an unstated assumption, and the repair. Failures worth hunting are gates nothing can pass, gates everything passes, an instrument that will not discriminate on real material, worker briefs that produce unusable returns, missing inputs the plan assumed, a dispatcher that stalls, and pace that misses the first checkpoint.

Feed every finding back through Phase D and re-freeze. Repeat only while a pilot round is still exposing new defect classes.

Then freeze. Record the pilot's scope, cost, failures, and repairs in the campaign, and label a campaign frozen without a pilot as reviewed-static so no reader mistakes plan coherence for tested behavior.

The machine-readable record lives at `assurance.pilot`. A passing record names its
`content_digest`, `authorized_by`, `authority`, `executor_id`, `executed_at`, `scope`,
`resource_cap`, `evidence`, `failures`, and `repairs`. Any substantive campaign change
makes that digest stale. `assurance.pilot_required` explicitly applies this gate outside
the high-assurance profile.

A pilot is required for `high-assurance` and for any campaign whose first irreversible stage is expensive. It is optional for `scoped` work. It is not available when execution authority has not been granted; in that case record it as an unmet condition rather than skipping it silently.

## Phase F — release decision

Final status is one of:

- `execution-ready` — all profile-required gates pass;
- `plan-ready-execution-blocked` — the roadmap is useful but an approval, access, resource, or independent review blocks execution;
- `draft` — material design decisions remain unresolved.

Every status must state the highest independence rung reached and whether a pilot was run. `execution-ready` never means validated.

A reviewer may recommend `accepted-risk`, but cannot authorize it. A major or critical
finding remains blocking until a separate record in `assurance.risk_acceptances` binds
the exact finding digest and current campaign digest to an identified authority and
evidence of the decision.

Never average away a required blocking reviewer. Never allow polished prose to override a critical defect.
