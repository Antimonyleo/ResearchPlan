# Architecture

ResCamp 0.10 has three parts.

## Campaign compiler

The skill assesses the starting point, conducts a minimum-sufficient interview, and writes one
canonical campaign contract. An existing project keeps accepted prior work and begins at its
current decision frontier. Unresolved decisions remain explicit fog or blockers; the compiler
does not invent values to make the plan look complete.

## Current-campaign quality loop

The Python engine validates structure and references, freezes content digests, prepares
role-specific review packets, records each review's stated execution mode and findings, and
renders either an execution-ready bundle or a clearly blocked draft. Reviews are invalidated
only when content inside their scope changes. Required pilots and accepted major or critical
risks are separately authorized and bound to the current digest.

The engine hashes rendered artifacts and verifies them with `audit`. These checks detect stale
or changed outputs; they are not a security boundary against someone who can rewrite the whole
workspace.

For broad long-running campaigns, the rendered prompt and runbook bind work to the active plan
digest, place fresh review at major decision gates, and route material changes through versioned
`revise`. This is an execution procedure; the compiler does not run the reviewers or scheduler.

## Manual comparative benchmark

The Team U/S/E harness compares versions, baselines, or external tools under matched conditions.
Public fixtures test the harness only. Real comparative claims require fresh sessions, private
holdouts, controlled conditions, and independent evaluation.

## Boundary

ResCamp compiles plans and prompts. It can describe work units, gates, approvals, checkpoints,
and recovery, but it does not schedule workers, spend resources, grant authority, or validate
the resulting scientific conclusion.
