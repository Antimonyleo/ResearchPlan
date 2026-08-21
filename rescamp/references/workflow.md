# Optional continuous workflow

ResCamp is first a campaign compiler. Activate the workflow layer only when the user wants sustained execution across agents, sessions, machines, expensive resources, or external systems.

## Required runtime objects

### Runtime profile

Define the continuation trigger, state store, event log, checkpoint policy, liveness mechanism, recovery rule, and idempotency rule. An enabled runtime also requires `resources_dispatch.max_concurrency` as a positive integer. Lease duration remains an operator/worker invocation choice bounded by any work-unit deadline.

### Work unit

Each work unit has one objective, authoritative inputs, dependencies, allowed and prohibited actions, outputs, an acceptance test, resource ceiling, retry policy and integer retry limit, escalation target, approval IDs, external-action IDs, and an optional timezone-aware deadline.

### Canonical state

Use one durable database or atomic state file plus an append-only event log. Workers do not mutate each other's records. Every artifact is content-addressed or hashed.

## Dispatcher invariants

The included queue mechanically refuses dispatch when:

- prerequisites or approvals are absent;
- the finalized campaign or its reviews are stale;
- another valid lease owns the work;
- the campaign concurrency ceiling is reached;
- a work-unit deadline or retry limit is exhausted;
- a dependency artifact no longer matches its recorded hash;
- a stop condition or safety boundary is active.

Budgets, prose resource ceilings, tool-use restrictions, and real-world approval authority are attestations. The queue reports them as such; it does not pretend to meter spend or verify a person's authority.

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

For a finalized campaign whose `runtime.enabled` is true, `scripts/workflow.py` provides a dependency-free SQLite state machine for `init`, `claim`, `heartbeat`, `complete`, `fail`, `approve`, `stop`, `reconcile`, `status`, and `audit`. Initialization reruns compiler and review validation. The queue stores work-unit specs, lease tokens, approval attestations, hash-chained events, and artifact hashes. It does not execute worker commands or decide whether scientific acceptance criteria are substantively satisfied.
