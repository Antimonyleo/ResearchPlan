---
name: rescamp
description: Explicitly invoked research-campaign compiler. Turns a vague inquiry in any discipline into a proportionate, reviewed, auditable research plan and agent-execution prompt through a strategic interview.
license: MIT
compatibility: Requires a coding agent with filesystem access; Python 3.9+ enables durable state, validation, review packets, rendering, and benchmarks.
disable-model-invocation: true
metadata:
  version: "0.10.0"
  invocation: "explicit"
---

# ResCamp

Compile a vague research goal into a concrete, proportionate, auditable campaign that people and agents can execute. Work interactively with the user; do not silently launch the research campaign.

## Invocation and modes

Treat plain invocation text as `start <goal>`.

- `start <goal>` — sketch and interview.
- `resume [campaign]` — continue from durable state.
- `status [campaign]` — show decisions, assumptions, blockers, question budget, and next branch.
- `draft [campaign]` — render a clearly marked non-final draft.
- `finalize [campaign]` — run the automatic quality loop, ask any remaining material questions, and render the final campaign bundle.
- `review [campaign]` or `test [campaign]` — manually rerun validation and proportional review on the current campaign.
- `benchmark <config>` — manually run a comparative benchmark; never run a full cross-system benchmark merely because an interview ended.
- `revise [campaign] <change>` — update the campaign, invalidate affected reviews, and rerun quality checks.
- `audit [campaign]` — verify state, references, artifacts, and hashes.
- `help` — show concise usage.

Invoke this skill through the host's explicit-invocation syntax. `references/hosts.md` is the registry of per-host paths, syntax, and explicit-only policy; these instructions are identical on every host and name none of them.

Modes are what the user types; they are not all subcommands. The crosswalk:

| Mode | Engine command |
|---|---|
| `start` | `init`, then `turn`/`dimension`/`add`/`set` |
| `resume`, `status` | `status <campaign>` — no separate resume; state is already durable |
| `draft` | `render --draft` |
| `finalize` | `finalize` |
| `review`, `test` | `quality-loop` |
| `revise` | `set`/`add` the change, then `quality-loop` — there is no `revise` subcommand |
| `audit` | `audit --strict` |
| `benchmark` | `scripts/benchmark.py` |
| `help` | `--help` on any subcommand |

## Start with value, not a questionnaire

After reading the goal and supplied materials:

1. Preserve the verbatim goal and choose a provisional assurance profile: `scoped`, `standard`, or `high-assurance`.
2. Infer one or more research archetypes. These are the exact accepted values: `experimental`, `computational`, `observational`, `qualitative-field`, `humanities-interpretive`, `conceptual-normative`, `evidence-synthesis`, `policy-program-evaluation`, `design-engineering`, `creative-practice`, `mixed-methods`.
3. Present **Campaign sketch v0**: decision or purpose, scope, core inquiries, likely evidence, rough methods/stages, success or adjudication criteria, major assumptions/risks, and proposed outputs.
4. State that the sketch is corrigible, save it, and ask the single highest-value unresolved question.

Do not force experimental vocabulary onto non-experimental work. “Hypothesis,” “control,” “metric,” and “falsifier” may instead be an interpretive claim, rival reading, comparison case, counterexample, source criticism rule, normative objection, or adjudication criterion.

## Minimum-sufficient interview

Ask one question per turn; ask two only when their answers are inseparable. Ask only when the answer can materially change scope, evidence, method, ethics/safety, authority, resources, acceptance criteria, or outputs.

For every answer:

1. Save the verbatim answer and a normalized decision.
2. Update assumptions, contradictions, dependencies, and confidence.
3. Convert resolved decisions into exact campaign objects.
4. Checkpoint before asking again.
5. Choose the next question by expected decision impact × uncertainty × answer utility ÷ user burden.

Use public research for publicly knowable facts. Never ask again for information already supplied. Accept “I do not know”: research it, offer a reversible default, or record a real blocker. Never invent access, data rights, consent, approval, credentials, budget, deadline, risk tolerance, or authority.

Treat unresolved shape as **fog**, not a blank to fill. When a material decision is not yet precise enough to encode, keep its intent dimension `unresolved` or `partial` and record the dependency or blocker. Never create placeholder campaign objects merely to satisfy validation. Drafts may remain incomplete; execution-ready campaigns may not.

Question budgets are safeguards, not targets:

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

## Campaign architecture

The final plan and execution prompt must preserve the governing architecture of the Anthropic protein-design campaign while translating it to the user’s field:

1. **Campaign constitution** — authority, non-negotiable verification, provenance, safety, and reporting rules inherited by every worker.
2. **Mission and deliverables** — decision/purpose, exact outputs, boundaries, non-goals, and completion definition.
3. **Object and evidence dossier** — exact system, population, corpus, case, construct, historical frame, stakeholders, source hierarchy, and known alternatives.
4. **Inquiry logic** — questions, claims or hypotheses, discriminating predictions or interpretive implications, rival explanations/readings, counterevidence, and uncertainty.
5. **Method portfolio** — complementary methods, diversity rules, dependencies, limitations, and why each method can change the decision.
6. **Tools and canaries** — identities/versions, access, real production-like smoke tests, schemas, sanity checks, and downstream acceptance before scale-up.
7. **Frozen evaluation instrument** — criteria, controls/comparators or adjudication rules, positive/negative cases where meaningful, scoring or judgment procedures, missing-evidence policy, and stop/no-go rules fixed before production evidence is inspected.
8. **Staged funnel** — cheap checks before expensive work, promotion gates, iterative refinement, bounded adaptation, and confirmatory work separated from exploration.
9. **Resources and dispatch** — time, budget, access, compute/materials, concurrency, fail-closed dispatch, approvals, and a single source of truth. Budget is a floor as well as a ceiling: declare an expected pace and checkpoints, and treat large under-spend with unexplored branches as an incomplete campaign rather than a thrifty one.
10. **Delegation** — bounded worker briefs with objective, authoritative inputs, permitted/prohibited actions, exact outputs, verification, resource ceiling, retry, and escalation.
11. **Durable operations** — append-only events, atomic checkpoints, liveness, interruption recovery, idempotency, restart reconciliation, and artifact-based completion. A chat is not a scheduler.
12. **Ethics, safety, rights, and external actions** — consent, privacy, legal or institutional constraints, permissions, reversible boundaries, and human approval points.
13. **Reporting and claim discipline** — claims linked to admissible support and disconfirming evidence; preserve null, negative, failed, contradictory, and deviating results.
14. **Transactional closeout** — schema-checked deliverables, acceptance tests, unresolved deviations, hashes, and reproducible handoff.
15. **Independent challenge** — frozen-version reviewers or auditors appropriate to risk; no reviewer edits canonical state. Name the highest rung of independence actually reached: sequential self-critique < separate agent context < separate agent blinded to conclusions < human domain expert < external adjudicator with its own data. An agent reviewer checks internal coherence; it is not external validation, and no amount of it substitutes for measurement, replication, an archive, or peer review.
16. **Kickoff** — a compact command that starts execution from the frozen campaign contract.

In Anthropic's campaign roughly a third of the prompt was domain guidance and the remaining two thirds were orchestration, verification, and operations. Treat that as a heuristic, not a law: a rich dossier attached to a thin orchestration section is the common failure.

Apply this architecture proportionately. A small archival question may satisfy a section in a few lines; a costly autonomous experiment requires exact registries and operational controls. Never add machinery that cannot change the research decision or protect integrity.

## Automatic quality loop after interviewing

When the interview stopping rule is met, automatically:

1. Freeze a candidate content version and digest.
2. Run deterministic architecture, reference, graph, budget, permission, and deliverable checks.
3. Run proportional plan review:
   - `scoped`: deterministic checks plus one skeptical completeness pass;
   - `standard`: separate methods/evidence and operations/reproducibility passes when the host supports them;
   - `high-assurance`: separate methods, operations, and ethics/claim-integrity reviewers; execution readiness remains blocked if required independence is unavailable.
4. Classify every finding as `agent-fix`, `user-answer`, `external-approval`, or `accepted-risk`.
5. Fix agent-resolvable defects. Ask the user only the highest-value one or two remaining questions, then re-freeze and rerun the loop.
6. For expensive or high-assurance campaigns, run a bounded pilot of the rendered campaign before freezing, record what actually failed, and repair. Reviewing a static document is a weaker guarantee than watching it run; label a campaign frozen without a pilot as `reviewed-static`.
7. Render a final bundle only when required gates pass. Otherwise render a useful draft labeled **NOT EXECUTION-READY** with exact blockers. `execution-ready` means the plan passed its gates, never that a conclusion is validated.

This automatic loop evaluates the current campaign. The manual `benchmark` mode is the broader matched comparison across versions, baselines, or external tools.

## Durable tools and selective references

When Python and filesystem access exist, use `scripts/rescamp.py` for state, validation, review packets, rendering, and audit. The working sequence is:

```text
init --goal … --profile … --archetypes … [--id <slug>]
turn / dimension                                          # one per interview exchange
apply <c> --json @campaign.json                           # many sections at once, fields checked
add <c> <list-path> --json @section.json                  # one list section, fields checked
set <c> <dict-path> @section.json                         # replace an existing subtree
stop <c> --reason <stopping-reason>                       # validates, freezes, writes review packets
  → execute each packet in working/review_packets/ as a separate read-only reviewer
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

## Final bundle

Render:

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
