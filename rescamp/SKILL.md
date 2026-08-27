---
name: rescamp
description: Explicitly invoked research-campaign compiler. Turns an early idea or an in-progress project in any discipline into a proportionate, reviewed, auditable research plan and agent-execution prompt through project-state assessment and a strategic interview.
license: MIT
compatibility: Requires a coding agent with filesystem access; Python 3.9+ enables durable state, validation, review packets, rendering, and benchmarks.
disable-model-invocation: true
metadata:
  version: "0.11.0"
  invocation: "explicit"
---

# ResCamp

Compile an early research goal or an existing project into a valid research brief or a concrete, proportionate, auditable campaign. Work interactively with the user; do not silently launch research execution.

## Invocation and planning modes

ResCamp is one explicitly invoked skill. Invoke it through the host's wrapper, then pass one host-neutral planning token:

- `Camp-auto <goal>` — work brief-first, render a valid brief, then ask once whether to continue as `Camp-full`.
- `Camp-brief <goal>` — render a valid brief without an end promotion offer.
- `Camp-full <goal-or-campaign>` — begin full planning, or adopt an existing brief and continue the same state.

`references/hosts.md` is the registry for host paths, wrappers, structured controls, and acceptance; keep these skill instructions identical on every host.

After `Camp-auto` successfully runs `brief-finalize`, ask exactly once: **The research brief is ready. Promote it to `Camp-full`?** Use a structured question control when available, with `Promote to Camp-full` and `Keep brief` choices; otherwise ask the same question in plain prose. Persist the offer and answer. Acceptance applies the internal `promotion` transition to the same state; decline leaves it `brief-ready` and suppresses repeated offers for that unchanged brief. `Camp-brief` never makes this offer. A later explicit `Camp-full` may still adopt either brief. There is no public promote mode.

Planning mode controls artifact level and transition behavior. Assurance profile (`scoped`, `standard`, or `high-assurance`) controls interview and review rigor. Neither selects or implies the other.

Lifecycle commands are level-aware and never silently promote a brief. Briefs use `status`,
`brief-finalize`, and `audit`. Full campaigns use `status`, `draft`, `quality-loop`,
`finalize`, and `audit`. “Resume” means load status and continue the next unresolved branch;
“revise” means apply explicit state edits and rerun `quality-loop`. Comparative `benchmark`
is always manual.

Public modes are not necessarily engine subcommands. The crosswalk is:

| Public mode | Engine transition |
|---|---|
| `Camp-auto` | `init --planning-mode auto`; `brief-finalize`; accepted offer only: internal `promotion` |
| `Camp-brief` | `init --planning-mode brief`; `brief-finalize`; no offer |
| `Camp-full` | New: `init --planning-mode full`; existing brief: internal `promotion` |
| `resume`, `status` | `status <campaign>` — no separate resume; state is already durable |
| `draft` | Full only: `render --draft` |
| `finalize` | Brief: `brief-finalize`; full: `finalize` |
| `review`, `test` | `quality-loop` |
| `revise` | `set`/`add` the change, then `quality-loop` — there is no `revise` subcommand |
| `audit` | `audit --strict` |
| `benchmark` | `scripts/benchmark.py` |
| `help` | `--help` on any subcommand |

## Establish the starting point, then sketch

After reading the goal and supplied materials:

1. Choose `new-project` unless the request or supplied materials show that material work already exists. For an existing project, inspect the relevant files, logs, tests, outputs, decisions, and user-supplied status before planning. Initialize with the selected `--planning-mode` and `--entry-mode existing-project`.
2. For an existing project, present **Project baseline v0**: status as of now, assessment basis, accepted completed work, work in progress, inherited artifacts, decisions in force, deviations, items requiring recheck, and the decision frontier at adoption. Label each basis as inspected, user-reported, or inferred. Never infer completion from a filename or polished summary. Later `status` calls derive the live next branch from unresolved intent dimensions; the baseline remains historical provenance.
3. Preserve valid completed work and begin prospective stages at the current frontier. Recheck work only when its evidence, provenance, assumptions, or acceptance criteria are missing or no longer fit the goal. Keep prior artifacts under their original provenance.
4. Preserve the verbatim goal, planning mode, and provisional assurance profile.
5. Infer one or more research archetypes. These are the exact accepted values: `experimental`, `computational`, `observational`, `qualitative-field`, `humanities-interpretive`, `conceptual-normative`, `evidence-synthesis`, `policy-program-evaluation`, `design-engineering`, `creative-practice`, `mixed-methods`.
6. Present **Campaign sketch v0**: decision or purpose, scope, non-goals, core inquiries, likely evidence, rough methods/stages, success or adjudication criteria, major assumptions/risks, proposed outputs, and next action. For an existing project, show how the sketch continues, repairs, or supersedes the baseline.
7. State that the baseline and sketch are corrigible, save them, and ask the single highest-value question needed for the selected artifact level.

Evidence already observed before adoption is retrospective or exploratory unless a genuinely prior protocol governs it. Never relabel a newly written evaluation rule as preregistered or frozen before those results. Freeze rules prospectively for the remaining work and separate any new confirmatory stage from inherited results.

Do not force experimental vocabulary onto non-experimental work. “Hypothesis,” “control,” “metric,” and “falsifier” may instead be an interpretive claim, rival reading, comparison case, counterexample, source criticism rule, normative objection, or adjudication criterion.

## Minimum-sufficient interview

Ask one question per turn; ask two only when their answers are inseparable. Ask only when the answer can materially change scope, evidence, method, ethics/safety, authority, resources, acceptance criteria, or outputs.

For an existing project, ask first about undocumented decisions, disputed status, missing provenance, and whether the objective has changed. Do not ask the user to restate facts that can be verified from supplied artifacts.

For every answer:

1. Save the verbatim answer and a normalized decision.
2. Update assumptions, contradictions, dependencies, and confidence.
3. Convert resolved decisions into exact campaign objects.
4. Checkpoint before asking again.
5. Choose the next question by expected decision impact × uncertainty × answer utility ÷ user burden.

Use public research for publicly knowable facts. Never ask again for information already supplied. Accept “I do not know”: research it, offer a reversible default, or record a real blocker. Never invent access, data rights, consent, approval, credentials, budget, deadline, risk tolerance, or authority.

Treat unresolved shape as **fog**, not a blank to fill. When a material decision is not yet precise enough to encode, keep its intent dimension `unresolved` or `partial` and record the dependency or blocker. Never create placeholder campaign objects merely to satisfy validation. Drafts may remain incomplete; brief-ready and execution-ready artifacts must meet their respective gates.

Question budgets are safeguards, not targets. Camp-auto and Camp-brief target zero to three
questions and stop at four unless the user explicitly extends the brief interview. Camp-full
uses the assurance-profile budgets:

| Profile | Typical | Soft stop | Hard stop |
|---|---:|---:|---:|
| scoped | 3–5 | 6 | 8 |
| standard | 4–8 | 8 | 12 |
| high-assurance | 6–12 | 12 | 18 |

At the soft stop, explain what is resolved, what remains material, and why another question is worth the burden. Do not pass the hard stop without explicit user authorization. Stop early when every material decision is resolved, safely defaulted, defensibly deferred, not applicable with a reason, or exposed as a blocker, and the next question has low decision value.

Use this compact format:

**Question N — <decision branch>**

<one precise question>

**Why it matters:** <downstream consequence>

**Recommended default:** <reversible default and its assumptions, when useful>

When the host offers a structured question control, use it and put the recommended default first; keep the same fields. Fall back to plain prose when it does not. Never use a picker to force a choice where "I do not know" or a blocker is the honest answer.

## Artifact-level stopping rules

A valid brief records the decision or purpose, scope and non-goals, core inquiries, likely evidence and rough method, assumptions and material unknowns, blockers, proposed outputs, and next action. It is `brief-ready`, not execution-ready, and authorizes no research execution. In `Camp-auto` or `Camp-brief`, stop when those fields are resolved, safely defaulted, defensibly deferred, or exposed as blockers, then run `brief-finalize`.

`brief-finalize` writes `outputs/RESEARCH_BRIEF.md` and its small hash manifest. It does not
write the full campaign bundle.

`Camp-full` continues until the full architecture below is encoded and reviewed. Promotion is monotonic: preserve the brief, verbatim answers, normalized decisions, provenance, and digest; add only missing full-campaign requirements. Repeating an accepted internal promotion is harmless. Rendering a brief view of a full campaign never downgrades canonical state.

## Full-campaign compilation and QA orchestration

Load `references/architecture.md` only after the artifact level is full. Compile the mission,
evidence and inquiry logic, methods, frozen evaluation, tools and canaries, staged gates,
resources and approvals, delegation, durable operations, rights/safety, claims, deliverables,
closeout, and kickoff proportionately. Never add machinery that cannot change the decision or
protect integrity. Load `references/quality-loop.md` when freezing or reviewing.

The engine validates, freezes, and writes role-scoped review packets; it does not execute
reviewers or repair findings itself. The host agent executes each required packet in a fresh
read-only context when available, records the actual independence level, ingests the returned
record, repairs agent-fixable defects, and reruns only affected review scopes. User authority,
external approval, and accepted risk stay explicit. A required pilot must be genuinely run and
digest-bound. Finalize only after required gates pass; otherwise render a blocked draft.

For multi-day or multi-agent work, compile the continuity rules in
`references/architecture.md`: bind work to the active digest, review major decision-bearing
gates, preserve completed evidence under its producing version, and stop constitutional
changes for approval. ResCamp is a compiler and auditor, not a scheduler.

## Durable tools and selective references

When Python and filesystem access exist, use `scripts/rescamp.py` for state, validation, review packets, rendering, and audit. The working sequence is:

```text
init --planning-mode auto|brief|full --goal … --profile … --archetypes … [--entry-mode existing-project] [--id <slug>]
migrate <c>                                                # explicitly upgrade pre-3.2 state as Camp-full
dimension <c> --id <id> --status <status> [--value …]     # update one decision dimension
turn <c> --branch <b> --question … --answer … --normalized …
apply <c> --json @campaign.json                           # many sections at once, fields checked
add <c> <list-path> --json @section.json                  # one list section, fields checked
set <c> <dict-path> @section.json                         # replace an existing subtree
stop <c> --reason <stopping-reason>                       # brief: record stop; full: begin QA orchestration
brief-finalize <c>                                        # brief only, after stop
promotion <c> --decision accept|decline --source auto-prompt|camp-full --answer …
  → full only, after stop: execute each packet in working/review_packets/ as a separate read-only reviewer
ingest-review <c> <record.json>                           # once per required role
finalize <c>                                              # fail-closed; renders the bundle
audit <c> --strict                                        # re-verify hashes and state
```

**Write payloads to a file and pass `@file.json`.** `apply`, `add --json`, and `set` all accept `@file.json`. Inline JSON breaks on apostrophes, which research prose is full of, and one shell-quoting failure per payload pushes you back into adding objects one at a time.

**Prefer `apply` once the interview has resolved several sections.** It takes an object mapping dotted paths to values, writes them in one call, and applies the same field checking `add` does — if any object has an unknown field, nothing is written and the error names the path and the valid fields. `set` rejects unknown paths and malformed section containers, but replacing the whole `campaign` bypasses object-field checks; do not use it as a bulk shortcut.

`schema <path>` prints the exact field vocabulary; `references/objects.md` has the same tables for list sections. Prefer `add` or `apply` for object lists and use `set <list-path>.<index>.<field>` for a field of an existing object. Reviews are bound per section, so after a repair rerun only the roles named by `roles_requiring_review`. Use `scripts/benchmark.py` only for a deliberate comparative evaluation. Default workspace: `research-campaigns/<slug>/`.

Load only the reference needed for the current branch:

- `references/architecture.md` — campaign compilation and prompt structure;
- `references/interview.md` — question selection and stopping;
- `references/archetypes.md` — discipline-neutral and archetype-specific mappings;
- `references/objects.md` — exact field vocabulary for every campaign object;
- `references/quality-loop.md` — automatic validation/review/revision;
- `references/benchmark.md` — manual cross-version/tool evaluation;
- `references/hosts.md` — installation, invocation, and live acceptance.

Do not load every reference or schema into context. Prefer deterministic scripts for hashes, schemas, graph checks, state transitions, and scoring; use agents for interpretation, research design, synthesis, and challenge.

## Full campaign bundle

For `Camp-full`, render:

- `CAMPAIGN_PROMPT.md` — complete execution constitution and research scheme;
- `KICKOFF.md` — compact start command;
- `campaign.json` — machine-readable contract;
- `ROADMAP.md` — concise human-facing roadmap;
- `TASK_BRIEF_TEMPLATE.md` — bounded delegation template;
- `REVIEW_REPORT.md` — methods, operations, and integrity findings with review mode;
- `CLAIMS_EVIDENCE_MATRIX.json` — claims/questions, support, counterevidence, verification, and reporting status;
- `RUNBOOK.md` — continuation, checkpoints, budgets, failure recovery, and approvals when execution is in scope;
- `BLOCKERS.md` — only when unresolved;
- `MANIFEST.sha256` — artifact hashes.

Lead with the least favorable defensible interpretation. Never conceal uncertainty or unresolved work behind polished prose.
