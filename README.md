# ResCamp

ResCamp turns an early research idea into a research plan that a person or agent team can actually execute.

A request such as:

> Does a four-day workweek reduce burnout in software companies?

sounds clear, but it leaves consequential decisions unstated: which companies and workers, what comparison, how burnout is measured, whether the goal is causal or descriptive, what data are available, what evidence would change the conclusion, and what approvals are needed. An agent that begins immediately will often answer those questions for the user and hide the assumptions inside polished work.

ResCamp handles that gap. It proposes a useful first sketch, asks a small number of high-value questions, and compiles the answers into a structured research plan and execution prompt. It then checks the plan, prepares focused packets for separate reviewers, repairs material defects, and clearly distinguishes an execution-ready plan from a draft that still has blockers.

The result is not just an outline. It specifies the research question, evidence, methods, evaluation rules, stages, gates, resources, permissions, deliverables, review record, and first authorized action. It can support experimental, computational, observational, qualitative, humanities, policy, design, evidence-synthesis, conceptual, creative-practice, and mixed-methods work.

ResCamp is an explicitly invoked skill for Claude Code and Codex. It plans the research; it does not silently start the campaign or claim that the eventual scientific conclusion is valid.

## How it works

### 1. Sketch before interrogation

ResCamp begins by translating the vague idea into a corrigible **Campaign sketch v0**. The sketch gives the user something concrete to react to: the likely purpose, scope, central inquiries, evidence, methods, risks, success criteria, and outputs. It is explicitly provisional.

This avoids two common failures: asking the user to fill out a long form before providing any value, and treating the first plausible interpretation as settled fact.

### 2. Ask only decision-changing questions

The interview proceeds one question at a time. A question is worth asking only if its answer can materially change the scope, evidence, method, ethics, authority, resources, acceptance criteria, or outputs. ResCamp records both the user's original answer and the normalized decision so later agents can trace what the plan is based on.

Typical interview budgets are 3–5 questions for `scoped`, 4–8 for `standard`, and 6–12 for `high-assurance` work. These are ceilings and stopping safeguards, not targets. The profile also scales review depth: `scoped` uses a skeptical completeness pass, `standard` separates methods/evidence from operations/reproducibility, and `high-assurance` adds ethics/claim-integrity review and pilot evidence.

If the user does not yet know an answer, ResCamp does not fabricate one. The unresolved decision remains **fog**: it is marked unresolved or partial and linked to a dependency or blocker. A draft may contain fog; an execution-ready campaign must resolve it or expose it as a real blocker.

### 3. Compile a complete research contract

Resolved decisions are compiled into a durable campaign contract. The contract connects:

- the mission, boundaries, research objects, and intended decisions;
- inquiries or claims, admissible evidence, rival explanations, and counterevidence;
- methods, tools, canaries, evaluation criteria, stages, and promotion gates;
- budgets, access, delegation, recovery, ethics, rights, and human approvals;
- deliverables, acceptance tests, claim discipline, review, and kickoff.

The structure is proportional. A focused literature question can satisfy a section in a few lines; a costly experiment or autonomous campaign needs more exact controls.

### 4. Review, repair, and label readiness honestly

When the interview stops, ResCamp freezes the current content and runs deterministic checks for missing structure, broken references, stage cycles, stale reviews, unsupported external actions, and incomplete deliverables. It then prepares role-specific packets for separate reviewer agents—for example, methods/evidence and operations/reproducibility—so review is not just the author rereading its own answer. If the host cannot provide the required independence, ResCamp reports that limitation instead of claiming it was achieved.

Reviews are bound to the exact sections they inspected. A later change invalidates only the affected reviews. Agent-fixable defects are repaired; questions requiring user authority, external approval, or accepted risk remain visible.

`finalize` produces either an `EXECUTION-READY` bundle or a useful `NOT EXECUTION-READY` draft with exact blockers. Readiness means the plan passed its stated gates. It does not mean that the research result has been measured, replicated, or externally validated.

## Installation

ResCamp 0.10.0 requires Python 3.9+ and only the standard library at runtime. The standard Skills CLI installs the same canonical tree for both supported hosts:

```bash
npx skills add Antimonyleo/ResearchPlan --skill rescamp -g \
  -a claude-code -a codex -y
```

This installs at user scope. For a project-local installation, omit `-g`:

```bash
npx skills add Antimonyleo/ResearchPlan --skill rescamp \
  -a claude-code -a codex -y
```

The installer requires Node.js 18+, but the installed skill does not. Add `--copy` if symlinks are undesirable. Claude Code's manual-only policy and Codex's explicit-only policy ship inside the same skill tree, so installation does not need to rewrite user settings. See [host paths and acceptance checks](rescamp/references/hosts.md).

## Using ResCamp

Start by invoking the skill with the research idea. Plain invocation is treated as `start`.

Claude Code:

```text
/rescamp Does a four-day workweek reduce self-reported burnout in mid-size software firms?
```

Codex:

```text
$rescamp Does a four-day workweek reduce self-reported burnout in mid-size software firms?
```

ResCamp stores campaigns under `research-campaigns/<campaign-name>/` by default, so the work can continue across sessions.

### Modes

| Mode | When to use it | What happens |
|---|---|---|
| `start <goal>` | Beginning a new idea | Creates Campaign sketch v0, initializes durable state, and starts the minimum-sufficient interview. |
| `resume [campaign]` | Returning in a later session | Loads the saved decisions and continues from the highest-value unresolved branch. |
| `status [campaign]` | Checking progress | Shows resolved decisions, assumptions, blockers, interview budget, review freshness, and the next likely action. It does not change the campaign. |
| `draft [campaign]` | Needing an early plan for discussion | Renders the current material as a clearly non-final bundle. Missing decisions remain visible. |
| `finalize [campaign]` | The interview appears complete | Runs validation and proportional review, repairs agent-fixable findings, asks only material remaining questions, and renders the final or blocked bundle. |
| `review [campaign]` or `test [campaign]` | Manually checking the current plan | Re-runs deterministic checks and the required reviewer passes without running a comparative benchmark. |
| `revise [campaign] <change>` | Requirements, evidence, access, or scope changed | Updates canonical state, invalidates affected reviews, and reruns the relevant checks. |
| `audit [campaign]` | Before handoff or execution | Verifies canonical state, review freshness, references, rendered artifacts, and recorded hashes. |
| `benchmark <config>` | Comparing versions, a no-skill baseline, or another tool | Runs the separate Team U/S/E evaluation harness. It is manual and never starts merely because a campaign was finalized. |
| `help` | Looking up syntax | Shows concise skill usage. |

A common lifecycle is:

```text
start → interview → status → finalize → audit
                         ↘ revise → review → finalize
```

Use `draft` at any point when a stakeholder needs to inspect the current direction. Use `revise` rather than editing rendered outputs directly; the canonical campaign state is what review and audit track.

The agent normally drives `rescamp/scripts/rescamp.py`. Developers integrating the engine directly can run its `--help` command for the low-level CLI.

## Outputs and follow-up use

The final bundle is written under the campaign's `outputs/` directory.

| Artifact | Purpose and follow-up use |
|---|---|
| `CAMPAIGN_PROMPT.md` | The main execution prompt. Give it to the lead research agent or use it as the shared constitution for an agent team. |
| `KICKOFF.md` | The first authorized action and gate. Use it to begin execution without asking a new agent to reinterpret the whole plan. |
| `ROADMAP.md` | A concise human-facing summary. Share it with collaborators, decision owners, or reviewers. |
| `campaign.json` | The machine-readable contract. Use it for continuation, integration, or programmatic inspection. |
| `TASK_BRIEF_TEMPLATE.md` | Bounded worker instructions derived from declared work units. Use it when delegating stages or analyses. |
| `REVIEW_REPORT.md` | Reviewer modes, verdicts, and findings. Use it to understand what was challenged and what still needs attention. |
| `BLOCKERS.md` | Present only when execution is blocked. Resolve these items, record approvals, or deliberately revise the scope before finalizing again. |
| `CLAIMS_EVIDENCE_MATRIX.json` | Links inquiries and claims to support, counterevidence, verification, uncertainty, and reporting rules. Use it during analysis and final writing. |
| `RUNBOOK.md` | Checkpoints, continuation, recovery, budgets, and approvals. Use it to resume long or multi-stage work. |
| `MANIFEST.sha256` | Hashes of rendered artifacts. Run `audit` before handoff to detect stale or changed outputs. |

ResCamp does not schedule workers, spend resources, or grant authority. The bundle is the handoff from planning to an execution agent, human team, workflow system, or domain-specific tool. During execution, failed checks, new evidence, changed constraints, or unresolved approvals should flow back through `revise`, targeted review, and `finalize` rather than being hidden in an ad hoc copy of the prompt.

## Benchmarks and evidence

The ordinary quality loop asks whether one campaign is internally complete, coherent, and likely executable. The optional benchmark asks a different question: whether ResCamp performs better than a previous version, a neutral no-skill prompt, or another system under matched conditions.

The benchmark separates three roles:

- **Team U** knows a hidden research brief and answers only what the tested system asks.
- **Team S** sees the vague request and public interview. This is the system or condition being tested.
- **Team E** sees frozen artifacts and an evaluator transcript under an opaque label, then scores the result against universal and archetype-specific criteria.

The harness measures decision recall, question efficiency, unsupported assumptions, interaction burden, campaign quality, critical defects, false readiness, cost, and tool use. Its 18 public scenarios span all supported archetypes, but they are calibration fixtures written inside this project. Synthetic fixture scores test the harness; they are not evidence that ResCamp improves live model performance.

Useful commands:

```bash
make benchmark-smoke
python3 rescamp/scripts/benchmark.py validate-scenarios benchmark/scenarios/public
```

Live comparative claims require fresh sessions, matched models and permissions, private holdouts, repeated runs, blinded evaluation, and—when claiming better research outcomes—external evidence from execution. See the [benchmark guide](docs/BENCHMARKING.md) and [adapter protocol](benchmark/adapters/external_command_protocol.md).

The separate `scripts/host_acceptance.py` checks that an installed Claude Code or Codex host can invoke ResCamp and create expected artifacts. It tests transport and artifact presence, not research quality.

## What the checks do not prove

ResCamp can detect structural omissions, inconsistent references, stale reviews, unsupported readiness claims, and modified rendered artifacts. Independent agent review can reveal unclear instructions and weak research logic.

It cannot determine whether the proposed science is true, authenticate real-world approvals, guarantee that later agents obey the prompt, or replace data, replication, domain expertise, ethics review, peer review, or external adjudication. The repository has not yet established superiority over a plain prompt on a private matched holdout or measured better downstream research outcomes.

## Development validation

```bash
make test
make skill-check
make validate-full
```

The full validator compiles the scripts, validates schemas and public scenarios, runs unit and end-to-end tests, and exercises deterministic and process-isolated Team U/S/E fixtures.

## Design inspirations

ResCamp combines three ideas while keeping their evidence boundaries explicit:

- Claude Science and Amir Shanehsazzadeh, [*Autonomous de novo protein binder design with Claude*](https://www-cdn.anthropic.com/30bf50e22a01388bb29bf077ee3f244531594b7a.pdf), Anthropic, 18 August 2026. ResCamp translates the campaign's emphasis on explicit orchestration, verification, staged evaluation, operations, and external checks. It does not inherit the paper's protein knowledge, private host capabilities, laboratory validation, or measured outcomes. See the [paper mapping](docs/PAPER_ANTHROPIC_BINDER.md).
- Travis Smith, [*The Little Scientist: LLM Agent-Driven Discovery via the Scientific Method*](https://arxiv.org/abs/2608.16951), 16 August 2026. ResCamp uses its inquiry → prediction or implication → test → evidence → revise/retain/reject loop as a discipline-neutral pattern for research reasoning.
- Matt Pocock, [*Wayfinder*](https://github.com/mattpocock/skills/blob/main/skills/engineering/wayfinder/SKILL.md). ResCamp borrows the practice of leaving premature decisions in the fog rather than filling them with false precision. Unlike Wayfinder's rolling frontier, ResCamp requires every material unknown to be resolved or exposed before claiming execution readiness.

The full provenance and generalization discussion is in the [design basis](docs/DESIGN_BASIS.md) and [generalization notes](docs/GENERALIZATION.md).

## License

ResCamp is released under the [MIT License](LICENSE). Third-party papers, tools, models, and comparison systems retain their own licenses.
