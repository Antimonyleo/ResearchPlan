# ResCamp

ResCamp turns a research idea into either a concise decision brief or a reviewed campaign
plan that a person or an agent team can execute. Consider a protein-design question:

> Can de novo miniproteins bind the PD-1-binding face of human PD-L1 well enough to justify
> synthesis?

The question sounds specific, but it leaves the consequential choices open: the target
construct, positive and negative controls, model provenance, ranking statistic, acceptance
thresholds, compute ceiling, and the evidence required for a go/no-go decision. An agent that
starts designing immediately will choose many of these silently. ResCamp makes the choices
explicit, preserves unresolved decisions as blockers, and binds review to the exact plan that
was inspected.

ResCamp is one explicitly invoked skill for Claude Code, Codex, and compatible agent
harnesses. It uses the same canonical `rescamp/` tree and the same three planning modes on
every host.

## Start here

Install globally for both supported hosts:

```bash
npx skills add Antimonyleo/ResearchPlan --skill rescamp -g -a claude-code -a codex -y
```

The installer needs Node.js 18+. The installed skill needs Python 3.9+ and uses only the
standard library at runtime. Omit `-g` for a project-local install, or add `--copy` when
symlinks are undesirable.

Claude Code and Codex use the same explicit commands:

```text
/rescamp Camp-auto Plan a computational campaign to decide whether candidate de novo miniprotein binders against PD-L1 justify synthesis.
/rescamp Camp-brief Map the evidence, uncertainties, and key design choices for a PD-L1 miniprotein-binder campaign.
/rescamp Camp-full Build a reviewed, execution-ready computational campaign for selecting PD-L1 miniprotein binders for synthesis.
```

For an existing project, point ResCamp at the current materials instead of restating the
work from scratch:

```text
/rescamp Camp-full Continue the PD-L1 binder campaign in this repository without repeating accepted work.
```

See the [host guide](rescamp/references/hosts.md) for installation scopes, acceptance checks,
and adapter requirements.

## Choose the planning depth

| Mode | Result |
|---|---|
| `Camp-auto <goal>` | Builds a brief first, then asks once whether to promote that same state to a full campaign. |
| `Camp-brief <goal>` | Builds a concise, non-executable brief and stops without a promotion prompt. |
| `Camp-full <goal-or-campaign>` | Starts full planning immediately or adopts an existing brief without repeating resolved questions. |

Use `Camp-auto` when the right level of effort is not yet clear. Accepting its promotion
prompt continues from the validated brief; declining leaves the brief ready and does not
keep asking while the brief is unchanged. A later `Camp-full` invocation can still adopt it.

Planning depth and assurance are separate. A brief can use high-assurance questioning, while
a full campaign can remain scoped. The assurance profile controls question and review depth;
the mode controls which artifact is produced.

## What the protein-design example shows

The repository includes a complete [PD-L1 miniprotein-binder campaign](docs/examples/pdl1-miniprotein-binders/).
Its decision is deliberately narrower than “does the binder work?” because that requires a
wet lab. The plan asks whether frozen computational evidence is strong enough to justify the
cost of synthesis.

Seven interview turns established the decision owner, target, controls, evaluation rules,
compute budget, approval boundaries, and stopping conditions. Review then exposed defects
that polished prose could hide, including:

- an unnamed control-separation statistic that could be selected after seeing results;
- positive-control leakage through deposited structures used in model training;
- recovery logic that could not detect a batch missing its pre-run manifest; and
- circular or unreachable gate transitions in the execution lifecycle.

The repaired campaign is `EXECUTION-READY` and passes strict audit. That label means the plan
satisfies its declared contract. It does not mean any binder will work, and no design,
structure retrieval, compute job, or wet-lab experiment was executed for the example.

## How ResCamp works

1. **Establish the starting point.** A new project begins with a corrigible campaign sketch.
   An existing project first gets an evidence-based baseline of completed, active, uncertain,
   and invalid work, then continues from the current decision frontier.
2. **Ask only plan-changing questions.** Each question must be capable of changing scope,
   evidence, method, ethics, authority, resources, acceptance criteria, or outputs. ResCamp
   stores both the user's words and the normalized decision.
3. **Stop at the requested artifact.** A brief captures purpose, boundaries, likely evidence,
   rough method, assumptions, blockers, outputs, and the next action. It is `brief-ready`, not
   execution-ready, and authorizes no research execution.
4. **Compile and review full campaigns.** Full mode adds methods, frozen evaluation, gates,
   budgets, approvals, ethics, deliverables, and acceptance tests. Deterministic checks run
   before role-scoped review packets are handed to fresh reviewer contexts when the host can
   provide them.
5. **Bind readiness to evidence.** Reviews cover exact sections and become stale when those
   sections change. Finalization reports `EXECUTION-READY`, `PLAN-READY; EXECUTION BLOCKED`,
   or a draft with named blockers. Strict audit verifies state, references, rendered outputs,
   and hashes.

Unknowns are not filled with plausible guesses. A draft may carry unresolved decisions; an
execution-ready campaign may not. For a long campaign, the rendered prompt and runbook also
define digest checks, major-stage reviews, amendment rules, and escalation. These are
instructions for the executor, not a scheduler hidden inside ResCamp.

## Outputs

A ready brief writes `outputs/RESEARCH_BRIEF.md` and its hash manifest. A full campaign adds:

| Artifact | Purpose |
|---|---|
| `CAMPAIGN_PROMPT.md` | Execution contract for the lead agent or team. |
| `KICKOFF.md` | First authorized action and its gate. |
| `ROADMAP.md` | Human-facing plan and decision summary. |
| `campaign.json` | Machine-readable campaign contract. |
| `TASK_BRIEF_TEMPLATE.md` | Bounded instructions for delegated work. |
| `REVIEW_REPORT.md` | Review modes, verdicts, and findings. |
| `CLAIMS_EVIDENCE_MATRIX.json` | Claims linked to support, counterevidence, and verification. |
| `RUNBOOK.md` | Resume, recovery, amendment, budget, and approval procedures. |
| `MANIFEST.sha256` | Hashes used to detect stale or edited outputs. |

`BLOCKERS.md` is added when execution is blocked. Campaigns live under
`research-campaigns/<name>/` and can be resumed across sessions. Rendered outputs are derived;
use ResCamp's state-changing modes instead of editing them by hand.

## Validation and benchmarking

```bash
make test
make skill-check
make benchmark-smoke
make validate-full
```

The optional benchmark compares matched planning conditions through separate user, system,
and evaluator roles. Its 18 public scenarios cover all supported research archetypes, but
they are synthetic fixtures created in this repository. Their scores test the harness, not
live-model quality or reviewer independence. See the [benchmark guide](docs/BENCHMARKING.md).

The host acceptance script checks whether an installed host can invoke ResCamp and create or
update expected artifacts. It tests transport and installation integrity, not research
quality.

## Limits

ResCamp can catch structural omissions, inconsistent references, stale reviews, unsupported
readiness claims, and modified artifacts. It cannot establish that a scientific claim is
true, authenticate a real-world approval, guarantee that an executor follows the plan, or
replace data, replication, domain expertise, ethics review, peer review, or external
adjudication.

The repository has not demonstrated superiority over a plain prompt on a private matched
holdout or measured downstream research outcomes. Reviewer independence is self-attested
unless an external process supplies stronger evidence.

## Documentation

- [Architecture](docs/ARCHITECTURE.md): state model, validation, review binding, and host seam.
- [Benchmarking](docs/BENCHMARKING.md): protocol, fixtures, metrics, and evidence boundaries.
- [Design basis](docs/DESIGN_BASIS.md): provenance and source-by-source design choices.
- [Generalization](docs/GENERALIZATION.md): how the workflow adapts beyond computational STEM.
- [Worked example](docs/examples/pdl1-miniprotein-binders/): full state, outputs, review record,
  limitations, and reproduction commands.

## License

[MIT](LICENSE). Third-party papers, tools, and models retain their own licenses.
