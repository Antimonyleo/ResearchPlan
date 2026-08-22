# ResCamp

ResCamp is an explicitly invoked skill for Claude Code and Codex. It turns a vague research idea into a structured, reviewed plan and an agent-ready execution prompt. It plans first and never silently starts the research.

Version 0.10.0 requires Python 3.9+ and only the standard library at runtime.

## How it works

```text
vague goal
  → corrigible sketch
  → short, one-question-at-a-time interview
  → structured campaign contract
  → deterministic checks and independent agent review
  → targeted repair
  → execution-ready bundle or honest blocked draft
```

Questions are limited to decisions that can change scope, evidence, method, ethics, authority, resources, acceptance criteria, or outputs. Typical budgets are 3–5 questions for `scoped`, 4–8 for `standard`, and 6–12 for `high-assurance` work.

Unclear decisions remain **fog**: ResCamp records them as unresolved, partial, or blocked instead of inventing precision to satisfy the validator. Drafts may remain incomplete; execution-ready plans may not. This practice is adapted from Matt Pocock's [Wayfinder skill](https://github.com/mattpocock/skills/blob/main/skills/engineering/wayfinder/SKILL.md).

After the interview, ResCamp freezes the plan, checks its structure and references, and prepares proportional review packets for separate agents. `finalize` then produces either an execution-ready bundle or a draft labeled `NOT EXECUTION-READY` with exact blockers.

## Install

The standard Skills CLI installs the same tree for both hosts:

```bash
npx skills add Antimonyleo/ResearchPlan --skill rescamp -g \
  -a claude-code -a codex -y
```

Omit `-g` for project scope. Add `--copy` if symlinks are undesirable. The installer needs Node.js 18+; the installed skill does not. Claude Code and Codex explicit-only policies ship inside the same tree. See [host details](rescamp/references/hosts.md).

## Use

Claude Code:

```text
/rescamp I want to determine whether ...
```

Codex:

```text
$rescamp I want to determine whether ...
```

Useful modes:

- `start <goal>` — sketch and interview;
- `resume` or `status` — continue or inspect progress;
- `draft` — render without claiming readiness;
- `finalize` — review, repair, and render;
- `review` or `test` — rerun quality checks;
- `revise <change>` — update and invalidate affected reviews;
- `audit` — verify state, references, outputs, and hashes.

The agent normally drives `rescamp/scripts/rescamp.py`; its `--help` output documents the low-level interface.

## Output and boundaries

The main artifact is `CAMPAIGN_PROMPT.md`. The bundle also contains a kickoff, roadmap, machine-readable contract, worker brief, review report, blocker list, claims/evidence matrix, runbook, and artifact manifest.

The engine checks required structure, cross-references, stage cycles, exact approval bindings for external actions, review freshness, campaign digests, output hashes, and readiness gates. It refuses to finalize around known blockers or unresolved major findings.

It cannot judge whether the research is scientifically good, authenticate a claimed real-world approval, enforce conduct after handoff, or validate a resulting conclusion. Agent review tests coherence and likely executability; it does not replace data, replication, domain experts, ethics review, or external adjudication. ResCamp describes work units and recovery when useful, but it is not a scheduler.

See [architecture](docs/ARCHITECTURE.md) and [generalization limits](docs/GENERALIZATION.md).

## Optional evaluation

`rescamp/scripts/benchmark.py` runs deliberate Team U/S/E comparisons across versions, baselines, or external systems. `scripts/host_acceptance.py` checks live Claude Code or Codex invocation and expected artifact presence. Neither runs automatically after an ordinary interview.

Public benchmark fixtures test the harness only. ResCamp has not been shown superior to a plain prompt on a private matched holdout and has no downstream research-outcome validation. See [benchmarking](docs/BENCHMARKING.md).

## Validate

```bash
make test
make skill-check
make validate-full
```

## Design sources

- Claude Science and Amir Shanehsazzadeh, [*Autonomous de novo protein binder design with Claude*](https://www-cdn.anthropic.com/30bf50e22a01388bb29bf077ee3f244531594b7a.pdf), Anthropic, 18 August 2026. ResCamp translates its campaign structure, not its protein science or laboratory validation. See the [paper mapping](docs/PAPER_ANTHROPIC_BINDER.md) and [design basis](docs/DESIGN_BASIS.md).
- Travis Smith, [*The Little Scientist: LLM Agent-Driven Discovery via the Scientific Method*](https://arxiv.org/abs/2608.16951), 16 August 2026. ResCamp uses its inquiry-and-evidence loop.
- Matt Pocock, [*Wayfinder*](https://github.com/mattpocock/skills/blob/main/skills/engineering/wayfinder/SKILL.md). ResCamp borrows its treatment of premature decisions as fog.

## License

MIT.
