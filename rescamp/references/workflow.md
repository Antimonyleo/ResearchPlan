# Optional continuous workflow

ResCamp is first a campaign compiler. Activate the workflow layer only when the user wants sustained execution across agents, sessions, machines, expensive resources, or external systems.

## Required runtime objects

### Runtime profile

Define trigger, environment, concurrency, worker limit, delegation depth, lease duration, heartbeat, stale threshold, checkpoint path, budget ledger, approval channel, retry policy, and shutdown behavior.

### Work unit

Each work unit has one objective, authoritative inputs, dependencies, allowed and prohibited actions, exact output schema/path, acceptance test, resource ceiling, retry limit, failure taxonomy, escalation target, and idempotency key.

### Canonical state

Use one durable database or atomic state file plus an append-only event log. Workers do not mutate each other's records. Every artifact is content-addressed or hashed.

## Dispatcher invariants

Do not dispatch when:

- prerequisites or approvals are absent;
- the content version is stale;
- the budget governor denies the request;
- another valid lease owns the work;
- required tools have not passed canaries;
- the output destination cannot be verified;
- a stop condition or safety boundary is active.

## Recovery

On restart:

1. read canonical state and event log;
2. verify artifact hashes;
3. expire stale leases;
4. reconcile running work against actual artifacts/processes;
5. avoid repeating irreversible actions;
6. requeue only idempotent or explicitly recoverable units;
7. record the recovery decision.

## Scientific loop records

Where iterative discovery is appropriate, preserve:

- inquiry or hypothesis;
- discriminating prediction or implication;
- test/analysis;
- observation;
- reconciliation;
- retain/revise/reject/branch decision;
- failure diagnosis;
- provenance and artifact hashes.

This loop is inspired by recent autonomous-science systems but does not prove scientific validity. Freeze evaluation holdouts, separate exploration from confirmation, log human interventions, and require external checks for consequential claims.


## Included queue utility

For a finalized campaign whose `runtime.enabled` is true, `scripts/workflow.py` provides a dependency-free SQLite state machine for `init`, `claim`, `heartbeat`, `complete`, `fail`, `approve`, `stop`, `reconcile`, `status`, and `audit`. It stores work-unit specs, lease tokens, approval records, append-only events, and artifact hashes. It does not execute worker commands or decide whether scientific acceptance criteria are substantively satisfied.
