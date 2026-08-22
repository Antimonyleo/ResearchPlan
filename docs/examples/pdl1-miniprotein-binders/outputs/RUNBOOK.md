# Operator runbook

**Continuous runtime enabled:** True

## Start/resume trigger

Work resumes from the campaign state directory and the append-only event log, never from chat history. A new session reads the last accepted gate and the frozen artifact digests, and starts the first work unit whose dependencies are accepted and whose outputs are absent.

## Canonical state and events

- State: The campaign state directory holds canonical state; the deliverables directory holds frozen artifacts, each carrying its own digest. Frozen artifacts are the durable record; a session's working notes are not.
- Events: Append-only. Every artifact freeze, canary run, scoring batch, gate decision, deviation, and escalation is appended with its timestamp, actor, inputs consumed by digest, and cost. Events are never edited or removed.
- Checkpoints: Checkpoint at every artifact freeze, at each gate decision, and after each S3 scoring batch. The batch manifest — parameters, seed, and the frozen digests it consumes — is appended to the event log before the batch consumes any compute, so an interrupted batch is always visible to reconciliation. A checkpoint records the manifest and cumulative cost so an interrupted stage resumes at batch granularity rather than restarting.

## Plan continuity and amendments

Use `campaign.json` at `sha256:1e86dcba1b89b17fe606eae042009dc1590f18e0e4d2e8aa1cfb9de225c9a195` as the active contract. At every start or resume, load that contract, the latest checkpoint, open blockers, and the next bounded work unit; verify required inputs before acting.

Record material deviations at the next gate. If execution reveals a material plan change, pause affected future work and re-freeze the plan under a new digest before continuing — in ResCamp, the `revise` mode. Never rewrite a frozen plan in place: a pending brief carrying an older digest is stale, while completed artifacts remain bound to the version that produced them.

## Liveness and recovery

- Liveness: A stage worker records a heartbeat with each batch. A stage with no batch event for more than one working day is treated as stalled and escalated to its stage owner. A chat session ending is not stage completion.
- Recovery: On interruption, reconcile the event log against artifacts actually on disk. Because every manifest is appended before its compute runs, a batch with a manifest and no complete score row is an interrupted batch and is rerun from its recorded seed. A batch whose outputs exist with no prior manifest cannot have arisen from a compliant run: it is quarantined, not adopted. Artifacts present but not recorded as frozen are quarantined pending a digest check.
- Idempotency: Every batch is keyed by its generation parameters and seed. Rerunning a completed batch reproduces its score rows and appends no duplicate event. Scoring is applied once per design; a rerun that would change a recorded score is a deviation, not a retry.

## Resource governor

- Total compute: 2,000 A100 GPU-hours on the existing institutional allocation, expiring at quarter end.
- S1: 50 GPU-hours. S2: 300 GPU-hours. S3: 1,600 GPU-hours with a checkpoint at 800. S4: 0 GPU-hours.
- Cash: USD 0. The campaign authorizes no expenditure of any kind.
- Budget floor: reaching S3's mid-stage checkpoint with substantially unspent allocation and unexplored design branches is an incomplete stage and is escalated to ROLE-pi, not reported as efficiency.
- Calendar: approximately twelve weeks, bounded by the quarter-end allocation expiry.
- Calendar ceiling: work-unit calendar ceilings sum to twelve weeks against a hard quarter-end allocation expiry, leaving no slack. ROLE-methods records cumulative elapsed calendar against the expiry date at every gate.
- Expiry rule: at G2, the S3 design count is scoped to what the remaining allocation and remaining calendar can complete. If the allocation lapses before the design set is completely scored, the campaign reports no-decision rather than running the decision table on a partial set.

## Fail-closed dispatch

- A work unit dispatches only when every work unit in its dependency_ids has been accepted at its gate. WU-freeze has no dependencies; WU-calibrate waits on WU-freeze; WU-generate on WU-calibrate; WU-decide on WU-generate.
- Dispatch is fail-closed: a work unit whose authoritative inputs are not present at their recorded digests does not start, and the condition is escalated rather than worked around.
- No work unit may exceed its resource_ceiling. Reaching the ceiling escalates to ROLE-pi; it does not silently continue.
- The stage owner is the single source of truth for stage status. A worker's self-report is evidence, not acceptance.
- External actions are prohibited campaign-wide. There is no dispatch path to a vendor, a purchase, or a wet-lab action.
- A batch manifest is appended to the event log before any compute is consumed. A batch that consumed compute without a prior manifest is a reconciliation error: the batch is quarantined and rerun, and the gap is recorded.

## Approvals

- **APR-compute:** Standing institutional GPU allocation, already granted; recorded in ACC-compute.
- **APR-G1:** G1 acceptance: target and environment frozen, all four canaries passing.
- **APR-G2:** G2 acceptance: thresholds, clustering cuts, and decision table frozen; controls separate.
- **APR-G3:** G3 acceptance: design set scored once against unchanged thresholds, with full provenance.
- **APR-G4:** G4 acceptance: memo matches the table cell and the handoff package reproduces.
- **APR-deviation:** Approval of a numbered post-freeze deviation, which downgrades D-memo to exploratory.
