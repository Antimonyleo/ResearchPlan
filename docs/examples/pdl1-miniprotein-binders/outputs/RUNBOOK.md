# Operator runbook

**Continuous runtime enabled:** True

## Start/resume trigger

Work resumes from canonical state and the event log, never chat history. Before permanent closure, a new session reads the last event and frozen digests. If exactly one valid G4 event is the last complete line with no later bytes and final reconciliation or manifest is absent, it resumes only closure_in_progress finalization from unchanged bytes. If both verify, the campaign is permanently closed. No resumed closure may append, rerun a decision branch, or change a frozen artifact.

## Canonical state and events

- State: Canonical campaign state remains in the campaign state directory. Frozen research artifacts live at their declared deliverable paths. Exact-byte SHA-256 digests are stored separately in UTF-8 `artifacts/MANIFEST.sha256`; an artifact never embeds the digest that identifies itself.
- Events: Live path: `artifacts/runtime/events.ndjson`, UTF-8 JSON Lines schema rescamp-runtime-event-v1. G2 adjudication requires s2_authorization_closed and exactly one terminal event per authorized control batch with zero active. A single g2_accepted or g2_control_failure_terminal_no_go records the outcome. Exactly one branch-matching G4 event must be the last complete line; its durable append seals the event stream and sets closure_in_progress. Final reconciliation and manifest finalization are out-of-log deterministic records and append no bytes. Permanent closure starts only after they verify the exact sealed-log digest.
- Checkpoints: Checkpoint every artifact freeze, gate decision, and batch transition. Before the single G2 adjudication, append s2_authorization_closed, terminalize every active control batch exactly once, and verify complete zero-active accounting. Direct scientific failure proceeds to terminal nonacceptance with candidate diagnostics absent. Scientific candidate pass alone freezes candidate thresholds and compatibility; compatibility failure is terminally nonaccepted, while compatibility pass permits g2_accepted and APR-G2 promotion. G4 closure behavior is unchanged.

## Plan continuity and amendments

Use `campaign.json` at `sha256:5027fd0be0557eb8d85df05f7cfaf0b401cb53b8d44e921242fd400e48948c39` as the active contract.

If execution reveals a material plan change, pause affected future work, apply the explicit state edits, and run the targeted quality loop to freeze a new digest before continuing. Never rewrite a frozen plan in place: a pending brief carrying an older digest is stale, while completed artifacts remain bound to the version that produced them.

## Liveness and recovery

- Liveness: The single dispatcher records a timezone-aware heartbeat event for each active batch at least once per working day. A batch without a heartbeat or terminal event for more than one working day is stalled and escalated to its stage owner. A chat session ending is not stage completion.
- Recovery: Before G2 adjudication, quarantine and identically rerun only an invalid non-run. For terminal G2 no-go, first stop S2 authorization and terminalize every active control batch exactly once; only zero-active complete accounting permits the failure event and reconciliation. After a sole valid G4 event with no later bytes, closure_in_progress recovery may only verify the frozen memo/event, hash the unchanged log, and atomically create or verify final reconciliation and manifest entries. It must not append, alter frozen artifacts, or repeat G4. Later bytes, a second G4 event, or mismatched published finalization fail closed. Permanent closure begins after successful verification.
- Idempotency: Unique IDs and one dispatcher prevent duplicate dispatch and terminal events. G2 is adjudicated once after complete S2 accounting. Candidate artifacts are promoted only by APR-G2 and never rewritten. A valid last-line G4 event is unique: if finalization is interrupted, recovery recomputes the same log digest and atomically creates or verifies the same deterministic reconciliation and manifest entries without appending or mutating frozen artifacts. Existing matching finalization is success; mismatched bytes fail closed. Permanent closure follows verified finalization.

## Resource governor

- Total compute: at most 2,000 A100 GPU-hours under APR-compute. Hard ledger: S1 cap 50 (all four G1 canaries and reruns), S2 cap 300 (control runs, dual curation, calibration, and permitted infrastructure reruns), S3 cap 1,600 (M-generate 1,200 plus M-score 400), and S4 cap 0. Reserve exactly 50 GPU-hours as contingency for declared failed/repeated jobs and overhead; it is not production capacity and cannot be used without the pre-score contingency rule.
- Cash: USD 0. The campaign authorizes no expenditure of any kind.
- Budget floor: the 800 GPU-hour S3 checkpoint compares completed slots and remaining fixed-frame work; under-spend with unexplored branches is incomplete and escalates to ROLE-pi rather than permitting adaptive sampling.
- Calendar: approximately twelve weeks but never beyond the exact allocation expiry recorded in D-environment.
- Calendar ceiling: at every gate ROLE-methods computes cumulative elapsed time, slot completeness, hard-cap consumption, reserve use, and remaining capacity against the frozen allocation record.
- Expiry and overrun rule: no stage may exceed its hard cap, the shared reserve, or the exact expiry. If the complete fixed S3 frame cannot finish, stop new authorization, terminalize every authorized slot/batch, record incomplete_or_expired with N_frame accounting, and dispatch only WU-decide's no-decision branch without applying the table or claiming yield.

## Fail-closed dispatch

- S2/WU-calibrate dispatch requires accepted G1 and APR-G1 plus exact current digests for D-target, D-environment, APR-compute evidence, the fixed S3 frame, and all four passing G1 canary manifests. WU-freeze completion, stored artifacts, or a worker self-report never authorize S2; a failed, missing, stale, or nonaccepted G1 rejects every S2 authorization.
- Every S3/WU-generate authorization requires accepted G2, APR-G2, exact promoted authoritative D-thresholds and D-canary-compat digests, the unchanged canonical D-control-protocol digest, fixed-frame capacity and expiry, and no nonterminal batch with the same frozen inputs and seed. WU-calibrate completion, candidate diagnostics, or a single nonconcurrent batch never suffice.
- Branch guards override WU-decide's structural WU-freeze dependency. Ordinary WU-decide dispatch requires accepted G2, APR-G2, exact promoted authoritative D-thresholds/D-canary-compat digests, accepted G3, APR-G3, complete D-designs digest, and immutable accepted_complete G3 reconciliation digest. Incomplete/expiry no-decision dispatch requires accepted G2, APR-G2, exact promoted threshold/compatibility digests, terminal not_accepted_incomplete_or_expired G3 reconciliation digest, absent APR-G3, and every retained partial S3 evidence path/digest. Failed-G2 dispatch requires terminal G2 nonacceptance, immutable failure record, zero-active G2 reconciliation, absent APR-G2/APR-G3, and zero S3 authorization; compatibility failure additionally requires retained candidate paths/digests, while direct scientific failure requires explicit candidate-path absence. No other predicate dispatches WU-decide.
- Dispatch is fail-closed: a work unit whose branch-specific authoritative inputs are not present at their recorded digests does not start. Before G2 only an invalid non-run may return to WU-calibrate. After adjudicated nonacceptance, any retry is a new linked campaign with no inherited gate, work-unit, compute, or dispatch authorization.
- No work unit may exceed its hard resource_ceiling or consume the shared 50-GPU-hour contingency outside the pre-score contingency rule. Reaching a stage cap, exhausting the reserve, or reaching exact expiry stops new authorization and executes the branch-specific terminal no-run/no-decision path; it does not silently continue.
- The stage owner is the single source of truth for stage status. A worker's self-report is evidence, not acceptance.
- External actions are prohibited campaign-wide. There is no dispatch path to a vendor, a purchase, or a wet-lab action.
- Only the single ROLE-comp-lead dispatcher may append runtime records or authorize batches. Before G2 adjudication it appends s2_authorization_closed, terminalizes every active control batch exactly once, and proves complete zero-active accounting. Before G3 it likewise accounts for every S3 batch. While holding the append lock, it rejects retry until the predecessor is terminal and no same-input-and-seed batch is nonterminal.
- After a sole valid G4 event becomes the last complete line, dispatch enters closure_in_progress: no work unit or event may dispatch. A resumed process may only hash unchanged log bytes and atomically create or verify deterministic final reconciliation and manifest entries; permanent closure begins after both verify.

## Approvals

- **APR-compute:** Standing institutional GPU allocation is claimed. D-environment must freeze the independently verified approval record digest, scope, available GPU-hours, hard stage caps, reserved contingency, exact timezone-aware expiry, and retrieval time before G1 acceptance; absent evidence supplies no compute authority.
- **APR-G1:** G1 acceptance: target and environment frozen, all four canaries passing.
- **APR-G2:** Issued exactly once only after candidate thresholds and compatibility are frozen, compatibility passes, S2 authorization is closed, every authorized control batch is terminal exactly once, and G2 is accepted. APR-G2 promotes the exact unchanged candidate digests as authoritative D-thresholds/D-canary-compat and authorizes S3; it is absent on nonacceptance.
- **APR-G3:** Accepted-G2 branch only: G3 acceptance when the complete design set is scored once against unchanged thresholds with full provenance; incomplete or expired S3 is G3 not accepted. APR-G3 is absent after adjudicated nonaccepted G2.
- **APR-G4:** G4 accepts the branch-matching immutable memo and sole G4 event. That event enters closure_in_progress and append-seals the log; deterministic final reconciliation and manifest finalization must verify before permanent closure and reproducible handoff.
- **APR-deviation:** Approval of a numbered post-freeze deviation before G4 closure, which downgrades D-memo to exploratory. Post-G4 correction requires a new linked campaign record.
