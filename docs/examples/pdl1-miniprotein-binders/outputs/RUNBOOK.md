# Operator runbook

**Continuous runtime enabled:** True

## Start/resume trigger

Work resumes from the campaign state directory and the append-only event log, never from chat history. A new session reads the last accepted gate and the frozen artifact digests, and starts the first work unit whose dependencies are accepted and whose outputs are absent.

## Canonical state and events

- State: Canonical campaign state remains in the campaign state directory. Frozen research artifacts live at their declared deliverable paths. Exact-byte SHA-256 digests are stored separately in UTF-8 `artifacts/MANIFEST.sha256`; an artifact never embeds the digest that identifies itself.
- Events: Live path: `artifacts/runtime/events.ndjson`, UTF-8 JSON Lines schema rescamp-runtime-event-v1. Records carry sequence, unique event_id, type, batch_id where applicable, status, timezone-aware timestamp, actor, frozen input digests, terminal output digests, cumulative cost, and predecessor event_id. One ROLE-comp-lead dispatcher owns an exclusive append lock and writes complete lines atomically. At G3, snapshot and hash the exact prefix but keep the stream open only for S4/G4; after the G4 acceptance event, close it and record its final detached digest.
- Checkpoints: Checkpoint every artifact freeze, gate decision, and S3 batch transition. Before compute, the single dispatcher appends authorization with batch ID, parameters, seed, and frozen inputs; it then appends started and exactly one terminal event. G3 freezes an immutable prefix reconciliation. S4 freezes D-memo, appends G4 acceptance naming its digest, then closes and hashes the final stream.

## Plan continuity and amendments

Use `campaign.json` at `sha256:cec061c58fca6136d0d70765c7c307fa82692a7020455fdb2ce8691f7230bb2d` as the active contract.

If execution reveals a material plan change, pause affected future work and re-freeze the plan under a new digest before continuing — in ResCamp, the `revise` mode. Never rewrite a frozen plan in place: a pending brief carrying an older digest is stale, while completed artifacts remain bound to the version that produced them.

## Liveness and recovery

- Liveness: The single dispatcher records a timezone-aware heartbeat event for each active batch at least once per working day. A batch without a heartbeat or terminal event for more than one working day is stalled and escalated to its stage owner. A chat session ending is not stage completion.
- Recovery: Before G3, reconcile batches against the live log. After G3, verify the immutable prefix snapshot before S4 and allow only S4/G4 event types. An authorized or started batch without a terminal event may retry under a linked new ID and identical inputs. Output without authorization, mismatched digests, duplicate terminal events, changes to the G3 prefix, or any append after final G4 reconciliation blocks acceptance.
- Idempotency: Unique IDs and the single dispatcher prevent duplicate dispatch. Terminal events bind output digests. A completed batch is never rerun; a failed or interrupted batch retries only under a linked new ID with identical inputs and seed. G3 binds an immutable prefix; G4 is appended once; final reconciliation closes the stream.

## Resource governor

- Total compute: at most 2,000 A100 GPU-hours under APR-compute; D-environment records the authoritative remaining hours and exact timezone-aware expiry before G1.
- S1: 50 GPU-hours. S2: 300 GPU-hours. S3: 1,600 GPU-hours with a checkpoint at 800. S4: 0 GPU-hours.
- Cash: USD 0. The campaign authorizes no expenditure of any kind.
- Budget floor: reaching S3's mid-stage checkpoint with substantially unspent allocation and unexplored design branches is incomplete and escalates to ROLE-pi.
- Calendar: approximately twelve weeks but never beyond the exact allocation expiry recorded in D-environment.
- Calendar ceiling: at every gate ROLE-methods computes cumulative elapsed time and remaining capacity against the frozen allocation record.
- Expiry rule: at G2, scope S3 from the allocation-record digest, remaining hours, and exact expiry. If the complete design set cannot be scored before expiry, report no-decision rather than apply the table to a partial set.

## Fail-closed dispatch

- A work unit dispatches only when every work unit in its dependency_ids has been accepted at its gate. WU-freeze has no dependencies; WU-calibrate waits on WU-freeze; WU-generate on WU-calibrate; WU-decide on WU-generate.
- Dispatch is fail-closed: a work unit whose authoritative inputs are not present at their recorded digests does not start, and the condition is escalated rather than worked around.
- No work unit may exceed its resource_ceiling. Reaching the ceiling escalates to ROLE-pi; it does not silently continue.
- The stage owner is the single source of truth for stage status. A worker's self-report is evidence, not acceptance.
- External actions are prohibited campaign-wide. There is no dispatch path to a vendor, a purchase, or a wet-lab action.
- Only the single ROLE-comp-lead dispatcher may append runtime records or authorize batches. It atomically appends an authorized event before compute, and every started batch receives exactly one completed or failed terminal event before G3.

## Approvals

- **APR-compute:** Standing institutional GPU allocation, already granted. D-environment must freeze the approval evidence, scope, available GPU-hours, exact timezone-aware expiry, and detached record digest before G1 acceptance.
- **APR-G1:** G1 acceptance: target and environment frozen, all four canaries passing.
- **APR-G2:** G2 acceptance: thresholds, clustering cuts, and decision table frozen; controls separate.
- **APR-G3:** G3 acceptance: design set scored once against unchanged thresholds, with full provenance.
- **APR-G4:** G4 acceptance: memo matches the table cell and the handoff package reproduces.
- **APR-deviation:** Approval of a numbered post-freeze deviation, which downgrades D-memo to exploratory.
