# Architecture

ResCamp has one canonical skill tree with a portable interface, two artifact levels, a
full-campaign quality loop, and an optional comparative benchmark.

## Portable interface and host seam

`Camp-auto`, `Camp-brief`, and `Camp-full` are host-neutral public tokens. A host adapter only
translates its explicit skill wrapper and presents questions; the canonical skill and Python
engine own campaign state, validation, rendering, and transitions. Hosts with structured
question controls use them, while every host has the same plain-prose fallback. This seam keeps
Claude Code, Codex, and future harnesses behaviorally equivalent without skill forks.

| Public entry | Engine path |
|---|---|
| `Camp-auto` | `init --planning-mode auto` → `brief-finalize` → optional internal `promotion` |
| `Camp-brief` | `init --planning-mode brief` → `brief-finalize` |
| `Camp-full` | New state: `init --planning-mode full`; existing brief: internal `promotion` |

`promotion` is an engine transition, not a public mode.

## Artifact levels and promotion

The compiler maintains one durable campaign state. A valid brief records the research purpose,
scope, inquiries, likely evidence and method, assumptions, blockers, and next decision. It may
be `brief-ready`, but it is never execution-ready and authorizes no research execution. A full
campaign preserves the brief's answers and provenance while adding the operational contract.

`Camp-auto` is brief-first. Only after `brief-finalize` succeeds does the skill persist and
present one promotion offer. Acceptance applies `promotion` to the same state; decline persists
`brief-ready` and suppresses repeats for that unchanged brief. `Camp-brief` never creates an
offer. A later explicit `Camp-full` can promote either kind of brief. Promotion is monotonic and
idempotent: it does not erase brief provenance, repeat resolved questions, or duplicate an
accepted transition. The accepted brief payload is preserved under its SHA-256 digest in the
promotion record, and `workflow` is included in the methods/evidence review scope.

Schema 3.2 introduces this workflow record. `migrate` upgrades a 3.1 campaign explicitly as a
direct `Camp-full` state; validation continues to reject unsupported schemas until migration.

Planning mode and assurance profile are orthogonal. Mode selects artifact level and transition
behavior; `scoped`, `standard`, and `high-assurance` select interview and review rigor within
that level.

## Campaign compiler

The skill assesses the starting point and conducts a minimum-sufficient interview for the
selected artifact. An existing project keeps accepted prior work and begins at its current
decision frontier. Unresolved decisions remain explicit fog or blockers; the compiler does not
invent values to make an artifact look complete.

## Full-campaign quality loop

For full campaigns, the Python engine validates structure and references, freezes content
digests, prepares role-specific review packets, records each review's stated execution mode and
findings, and renders either an execution-ready bundle or a clearly blocked draft. Reviews are invalidated
only when content inside their scope changes. Required pilots and accepted major or critical
risks are separately authorized and bound to the current digest.

The engine hashes rendered artifacts and verifies them with `audit`. These checks detect stale
or changed outputs; they are not a security boundary against someone who can rewrite the whole
workspace.

For broad long-running campaigns, the rendered prompt and runbook bind work to the active plan
digest, place fresh review at major decision gates, and route material changes through explicit
state edits and targeted re-freezing. This is an execution procedure; the compiler does not run
the reviewers or scheduler.

## Manual comparative benchmark

The Team U/S/E harness compares versions, baselines, or external tools under matched conditions.
Public fixtures test the harness only. Real comparative claims require fresh sessions, private
holdouts, controlled conditions, and independent evaluation.

## Boundary

ResCamp compiles briefs, full plans, and execution prompts. It can describe work units, gates,
approvals, checkpoints, and recovery, but it does not schedule workers, spend resources, grant
authority, or validate the resulting scientific conclusion.
