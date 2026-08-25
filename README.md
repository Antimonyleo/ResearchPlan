# ResCamp

Turn a new research idea or an in-progress project into a plan a person or an agent team can actually execute.

Ask an agent a research question and it will usually just answer. But a request like:

> Does a four-day workweek reduce burnout in software companies?

leaves consequential decisions unstated: which companies and workers, what comparison, how
burnout is measured, whether the goal is causal or descriptive, what evidence would change
the conclusion, and what approvals are needed. An agent that starts immediately answers
those questions on your behalf and hides the assumptions inside polished work.

ResCamp is an explicitly invoked skill for Claude Code and Codex that closes that gap. For a
new idea, it sketches a first draft. For a project already underway, it first inspects the
available files, logs, outputs, and decisions; records what is complete, active, uncertain, or
in need of repair; and starts the prospective plan at the current decision frontier. It then
asks only the questions whose answers change the plan, compiles a research contract, prepares
role-scoped review packets, and tells you plainly whether the plan is executable or blocked.

It is not limited to STEM. Eleven research archetypes are supported — experimental,
computational, observational, qualitative-field, humanities-interpretive,
conceptual-normative, evidence-synthesis, policy-program-evaluation, design-engineering,
creative-practice, and mixed-methods — and the vocabulary follows: where an experiment has a
hypothesis and a control, an interpretive project has a claim, a rival reading, and a source
criticism rule.

## See what it produces

A complete worked campaign plan, compiled by ResCamp and committed unedited:
[**de novo PD-L1 miniprotein binders**](docs/examples/pdl1-miniprotein-binders/) — 7 interview
turns, four original review rounds, a current independent maintenance review, and
`EXECUTION-READY`.

The first question it asked was not about proteins:

> **Question 1 — decision-use.** What decision does this campaign have to support, and who
> makes it? *Why it matters:* a campaign that ends in "designs that look good" cannot be
> finished; one that ends in a go/no-go on spending money can. *Recommended default:* a
> go/no-go on ordering synthetic genes for wet-lab testing.

That answer set the scope of everything after it. What review then found was not
boilerplate:

> **major** — The separation statistic is never named. The campaign says thresholds will be
> "calibrated on controls and frozen", but whoever writes the calibration artifact is still
> choosing between AUROC, overlap coefficient and median-crossing rate *after* seeing the
> distributions. The instrument is not frozen until the statistic is named.

> **major** — Training-set contamination of the positive controls is unaddressed. Published
> binders are frequently deposited structures, and deposited structures are frequently in a
> prediction model's training data. Their scores would be partly memorization, inflating
> separation in a way that does not transfer to novel designs.

> **major** — Reconciliation is written for a failure it cannot detect. Nothing requires a
> batch manifest to exist *before* the batch runs, so an interrupted batch is invisible and
> silently dropped — producing a design set that looks complete and is not.

Eight first-round findings were repaired; later rounds caught three cross-reference defects,
including one introduced by the first repair. A fresh maintenance review then found and
closed additional control-leakage and execution-lifecycle defects. The full plan, review
history, and honest limitations are in the
[example](docs/examples/pdl1-miniprotein-binders/).

## Install

Requires Python 3.9+ and only the standard library at runtime. The installer needs Node 18+;
the installed skill does not.

```bash
npx skills add Antimonyleo/ResearchPlan --skill rescamp -g -a claude-code -a codex -y
```

One canonical tree serves both hosts — Claude Code's explicit-only policy travels in the
skill's own frontmatter and Codex's in `agents/openai.yaml`, so each host ignores the
other's metadata and installation rewrites no user settings. Drop `-g` for a project-local
install, add `--copy` if you would rather have files than symlinks.

Then invoke it with your idea. Plain invocation means `start`:

```text
Claude Code: /rescamp Does a four-day workweek reduce self-reported burnout in mid-size software firms?
Codex:       $rescamp Does a four-day workweek reduce self-reported burnout in mid-size software firms?
```

For work already underway, name the current objective and point the agent at the project
materials. ResCamp will inspect them before asking you to confirm its status baseline:

```text
Claude Code: /rescamp start Finish the reading-intervention review in this repository without repeating valid completed work.
Codex:       $rescamp start Finish the reading-intervention review in this repository without repeating valid completed work.
```

Campaigns live in `research-campaigns/<name>/` and survive across sessions.

## How it works

**1. Establish the starting point, then sketch.** A new project opens with a corrigible
*Campaign sketch v0* — purpose, scope, inquiries, evidence, methods, risks, outputs. An
existing project first gets a *Project baseline v0*: the evidence used to assess status,
accepted completed work, active work, inherited artifacts and decisions, deviations, recheck
needs, and the next decision. The sketch then continues from that frontier instead of
restarting valid work. Prior results retain their original provenance; a new plan cannot
retroactively call an evaluation preregistered or prospectively frozen.

**2. Ask only what changes the plan.** One question per turn, asked only when the answer can
move scope, evidence, method, ethics, authority, resources, acceptance criteria, or outputs.
Both your verbatim answer and the normalized decision are recorded, so later agents can
trace what the plan rests on.

Typical interviews run 3–5 questions on `scoped`, 4–8 on `standard`, and 6–12 on
`high-assurance`. The enforced ceilings sit well above that — 8, 12 and 18 — and are
stopping safeguards, not targets. The profile also scales review depth: `scoped` gets one
skeptical pass, `standard` separates methods/evidence from operations/reproducibility, and
`high-assurance` adds ethics/claim-integrity plus pilot evidence.

**3. Leave what you don't know as fog.** If you don't have an answer, ResCamp does not
invent one. The decision stays unresolved or partial and is linked to a dependency or a
blocker. A draft may carry fog; an execution-ready campaign may not.

**4. Compile a research contract.** Resolved decisions become a durable structure covering
mission and boundaries, research objects and evidence hierarchy, inquiries and rival
explanations, methods and tools, a frozen evaluation instrument, staged gates, budgets and
approvals, ethics and rights, deliverables with acceptance tests, and the first authorized
action. Proportionally: a literature question satisfies a section in a few lines; a costly
autonomous campaign needs exact controls.

**5. Review, repair, and label readiness honestly.** When the interview stops, ResCamp
freezes the content and runs deterministic checks — missing structure, broken references,
stage cycles, unsupported external actions, incomplete deliverables. Then it writes
role-scoped packets for fresh reviewer contexts when available; sequential review remains
allowed but is labeled weaker. Reviews bind to the exact sections they inspected: a later
edit invalidates only what it touched. Agent-fixable defects get repaired; anything needing
your authority, an external approval, or an accepted risk stays visible.

`finalize` then produces either an `EXECUTION-READY` bundle or a `NOT EXECUTION-READY` draft
with exact blockers. It fails closed — no reviews, stale reviews, an unapproved external
action, or an open critical blocker all stop it.

**6. Keep a long campaign aligned.** A broad multi-day plan carries its active digest into
every work brief and checkpoint. Each major decision-bearing execution stage can name a
fresh, read-only reviewer in its gate; eight such stages normally produce eight review
gates, not one review after every task. Each review presents at most three material findings
— and must say so when it found more, so a capped review is never mistaken for a clean one.
After two rounds, remaining blockers escalate to the gate owner. Operational changes are
logged in place, method changes create a new version and targeted re-review, and changes to
the mission, primary evaluation, ethics, authority, budget ceiling, stop rules, or permitted
claims pause for approval. Old pending briefs become stale; completed evidence stays attached
to the plan version that produced it.

Unlike steps 1–5, this step is **compiled into the plan as instructions to whoever executes
it**. ResCamp renders the procedure into `CAMPAIGN_PROMPT.md` and `RUNBOOK.md`; it does not
schedule checkpoints, count review rounds, or enforce the finding cap. A chat is not a
scheduler, and neither is a plan.

## Reference

<details>
<summary><strong>Modes</strong></summary>

| Mode | When to use it |
|---|---|
| `start <goal>` | Beginning a new idea or adopting an existing project. Assesses supplied project state when present, creates the sketch, and starts the interview. |
| `resume [campaign]` | Returning to a ResCamp campaign. Continues from the highest-value unresolved branch. |
| `status [campaign]` | Read-only: decisions, assumptions, blockers, question budget, review freshness, next action. |
| `draft [campaign]` | Renders the current material as a clearly non-final bundle, missing decisions visible. |
| `finalize [campaign]` | Runs validation and review, repairs what it can, asks any remaining material question, renders. |
| `review` / `test` | Re-runs the checks and reviewer passes on demand. |
| `revise [campaign] <change>` | Versions a plan change, invalidates affected reviews, and reruns only the relevant checks. Use it for material changes discovered during execution. |
| `audit [campaign]` | Verifies state, references, rendered artifacts, and hashes before handoff. |
| `benchmark <config>` | Manual comparative evaluation. Never triggered by finalizing. |

Use `revise` rather than editing rendered outputs — canonical state is what review and audit
track.

</details>

<details>
<summary><strong>What ends up in <code>outputs/</code></strong></summary>

| Artifact | What it is for |
|---|---|
| `CAMPAIGN_PROMPT.md` | The execution prompt. Hand it to a lead agent or use it as a team's shared constitution. |
| `KICKOFF.md` | The first authorized action and its gate, so execution starts without reinterpreting the plan. |
| `ROADMAP.md` | Human-facing summary for collaborators and decision owners. |
| `campaign.json` | The machine-readable contract, for continuation or integration. |
| `TASK_BRIEF_TEMPLATE.md` | Bounded worker instructions derived from the declared work units. |
| `REVIEW_REPORT.md` | Reviewer modes, verdicts, and findings. |
| `CLAIMS_EVIDENCE_MATRIX.json` | Claims linked to support, counterevidence, verification, and reporting rules. |
| `BLOCKERS.md` | Present only when execution is blocked. |
| `RUNBOOK.md` | Resume procedure, major-stage reviews, controlled amendments, recovery, budgets, and approvals. |
| `MANIFEST.sha256` | Artifact hashes; `audit` uses them to catch stale or edited outputs. |

ResCamp does not schedule workers, spend resources, or grant authority. The bundle is the
handoff from planning to whoever executes.

</details>

<details>
<summary><strong>Benchmarks</strong></summary>

The quality loop asks whether one campaign is internally sound. The optional benchmark asks
a different question: whether ResCamp beats a previous version, a no-skill prompt, or
another system under matched conditions. It separates three roles — Team U holds a hidden
brief and answers only what it is asked, Team S is the system under test, Team E scores
frozen artifacts under an opaque label.

```bash
make benchmark-smoke
python3 rescamp/scripts/benchmark.py validate-scenarios benchmark/scenarios/public
```

Its 18 public scenarios span every archetype, but they are calibration fixtures written
inside this project. **Fixture scores test the harness; they are not evidence that ResCamp
improves live model performance.** See the [benchmark guide](docs/BENCHMARKING.md).

</details>

<details>
<summary><strong>Development</strong></summary>

```bash
make test           # unit and end-to-end tests
make skill-check    # skill structure and metadata
make validate-full  # compiles scripts, validates schemas and scenarios, runs everything
```

`scripts/host_acceptance.py` checks that an installed host can invoke ResCamp and create or
update the expected artifacts. It tests transport, not research quality.

</details>

## What this does not prove

ResCamp catches structural omissions, inconsistent references, stale reviews, unsupported
readiness claims, and modified artifacts. Agent review can surface unclear instructions and
weak research logic — as it did in the example above. Its current records came from separate
subagent contexts; that independence is self-attested, not blinded or external validation.

It cannot tell you whether the proposed science is true. It cannot authenticate a real-world
approval, guarantee that a later agent obeys the prompt, or substitute for data, replication,
domain expertise, ethics review, peer review, or external adjudication. `EXECUTION-READY`
means the plan passed its own declared gates and nothing more. Agent review checks internal
coherence; it is not external validation.

This repository has not established superiority over a plain prompt on a private matched
holdout, and has not measured downstream research outcomes.

## Design inspirations

- Claude Science and Amir Shanehsazzadeh, [*Autonomous de novo protein binder design with
  Claude*](https://www-cdn.anthropic.com/30bf50e22a01388bb29bf077ee3f244531594b7a.pdf),
  Anthropic, 18 August 2026. ResCamp generalizes the campaign's structure — explicit
  orchestration, frozen verification, staged evaluation, operations, external checks. It
  inherits none of the paper's protein knowledge, host capabilities, laboratory validation,
  or measured outcomes. [Mapping](docs/PAPER_ANTHROPIC_BINDER.md).
- Travis Smith, [*The Little Scientist: LLM Agent-Driven Discovery via the Scientific
  Method*](https://arxiv.org/abs/2608.16951), 16 August 2026 — the inquiry → prediction →
  test → evidence → revise/retain/reject loop, used as a discipline-neutral pattern.
- Matt Pocock, [*Wayfinder*](https://github.com/mattpocock/skills/blob/main/skills/engineering/wayfinder/SKILL.md)
  — leaving premature decisions in the fog rather than filling them with false precision.
  Unlike Wayfinder's rolling frontier, ResCamp requires every material unknown to be
  resolved or exposed before it will claim execution readiness.

Full provenance in the [design basis](docs/DESIGN_BASIS.md) and
[generalization notes](docs/GENERALIZATION.md).

## License

[MIT](LICENSE). Third-party papers, tools, and models retain their own licenses.
