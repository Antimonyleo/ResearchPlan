# ResCamp

ResCamp is an explicitly invoked skill for Claude Code, Codex, and compatible Agent Skills hosts. It turns a vague research goal into a structured, reviewed research plan and an execution prompt through a short strategic interview. It plans first and never silently starts the research.

Version 0.9.0 requires only Python 3.9+ and the standard library for durable state, validation, review packets, rendering, and benchmarks.

## Why it exists

ResCamp generalizes the campaign structure described in Anthropic's 2026 protein-binder study. That campaign used a single protocol prompt for 24–48 hour autonomous runs across 16 targets; 354 of 1,320 designs later bound in laboratory tests. About one third of the prompt was domain science and two thirds covered orchestration, verification, and operations.

ResCamp translates that operational structure, not the protein science or the laboratory validation. The paper did not ablate the prompt, so the two-thirds split is a description of one successful campaign, not proof that the structure caused its results. See [the paper mapping](docs/PAPER_ANTHROPIC_BINDER.md) and [design basis](docs/DESIGN_BASIS.md).

## Workflow

```text
vague goal
  → corrigible campaign sketch
  → short, one-question-at-a-time interview
  → structured campaign contract
  → deterministic checks and independent review packets
  → targeted repair
  → execution-ready bundle or an honest blocked draft
```

ResCamp asks only questions that can change the scope, evidence, method, ethics, authority, resources, acceptance criteria, or outputs. Typical budgets are 3–5 questions for `scoped`, 4–8 for `standard`, and 6–12 for `high-assurance` work.

Unclear decisions remain **fog**: mark them unresolved or partial and record the dependency or blocker. Do not invent placeholder content to make validation pass. Drafts may remain incomplete; execution-ready campaigns may not.

When the interview stops, the engine freezes the current content, checks its structure and references, and prepares proportional review packets. Separate agents judge the research substance. After repair, `finalize` either produces an execution-ready bundle or a draft labeled `NOT EXECUTION-READY` with exact blockers.

## Install

Clone or unzip the repository, then install the same canonical `rescamp/` tree for both hosts:

```bash
python3 scripts/install.py --host all --scope user
```

For a project-local installation:

```bash
python3 scripts/install.py --host all --scope project --project /path/to/project
```

The installer configures explicit-only invocation for each host. Host paths, syntax, and policy are documented in [hosts.md](rescamp/references/hosts.md).

## Use

Claude Code:

```text
/rescamp I want to determine whether ...
```

Codex:

```text
$rescamp I want to determine whether ...
```

Common modes:

- `start <goal>` — create a sketch and begin the interview.
- `resume` or `status` — continue from durable state or inspect progress.
- `draft` — render the current plan without claiming readiness.
- `finalize` — run the quality loop and render the final or blocked bundle.
- `review` or `test` — rerun validation and proportional reviews.
- `revise <change>` — update the campaign and invalidate affected reviews.
- `audit` — verify state, references, outputs, and hashes.

The agent normally drives `rescamp/scripts/rescamp.py`. Run its `--help` command for the low-level interface.

## Output

The main artifact is `CAMPAIGN_PROMPT.md`, the complete execution brief. A finalized bundle also includes:

- `KICKOFF.md` — the first authorized action;
- `ROADMAP.md` — a concise human plan;
- `campaign.json` — the machine-readable contract;
- `TASK_BRIEF_TEMPLATE.md` — bounded worker instructions;
- `REVIEW_REPORT.md` and `BLOCKERS.md` — review evidence and unresolved work;
- `CLAIMS_EVIDENCE_MATRIX.json` — claims, support, counterevidence, and verification;
- `RUNBOOK.md` and `MANIFEST.sha256` — continuation guidance and artifact hashes.

## What the engine enforces

The dependency-free Python engine checks required structure, reference integrity, acyclic stages, approval bindings, review freshness, campaign and artifact digests, and readiness gates. It refuses to finalize around known blockers or unresolved major findings.

It cannot judge whether the research is scientifically good, verify that a claimed real-world approval is authentic, enforce conduct after the prompt is handed off, or validate the resulting scientific conclusion. Independent agent review checks coherence and likely executability; it is not a substitute for data, replication, domain experts, ethics review, or external adjudication.

See [architecture](docs/ARCHITECTURE.md), [generalization limits](docs/GENERALIZATION.md), and the [release report](docs/RELEASE_REPORT.md) for the full boundary.

## Optional tools

These are separate from the normal idea-to-plan path:

- `rescamp/scripts/workflow.py` provides a SQLite work-unit queue for explicitly authorized long-running execution. It enforces declared approvals, dependencies, concurrency, deadlines, retries, leases, event integrity, and artifact hashes; it does not run models or grant authority.
- `rescamp/scripts/benchmark.py` runs manual Team U/S/E comparisons across versions, baselines, or external systems. Public fixture scores test the harness and are not model-performance evidence. See [benchmarking](docs/BENCHMARKING.md).
- `scripts/host_acceptance.py` records opt-in live-host invocation receipts. Those receipts establish transport and expected artifact presence, not plan quality.

## Validate

```bash
make test
make skill-check
make validate-full
```

The full validator compiles scripts, validates schemas and public scenarios, runs unit and end-to-end tests, executes deterministic Team U/S/E smoke tests, checks byte-identical dual-host installation, and records repository provenance.

## Evidence boundary

Release evidence is deterministic and primarily self-generated. Public benchmark fixtures are synthetic. ResCamp has not been shown superior to a plain prompt on a private matched holdout, and it has no downstream research-outcome validation. Independent agent review can expose prompt defects and test interpretability; it does not establish scientific validity.

## Sources

- Claude Science and Amir Shanehsazzadeh, [*Autonomous de novo protein binder design with Claude*](https://www-cdn.anthropic.com/30bf50e22a01388bb29bf077ee3f244531594b7a.pdf), Anthropic, 18 August 2026. Released [prompts, corpus, and binding data](https://huggingface.co/datasets/Anthropic/claude-protein-binder-design).
- Travis Smith, [*The Little Scientist: LLM Agent-Driven Discovery via the Scientific Method*](https://arxiv.org/abs/2608.16951), 16 August 2026. ResCamp uses its inquiry-and-evidence loop; that loop is not from the binder paper.

## License

MIT. Third-party systems used for comparison retain their own licenses.
