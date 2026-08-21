# ResCamp

ResCamp is an explicitly invoked research-campaign compiler for Claude Code, Codex, and other Agent Skills hosts. It turns a vague goal into a proportionate, reviewed, auditable research plan and execution prompt through a short strategic interview.

It is a generalization of one specific result. In August 2026 Anthropic published [*Autonomous de novo protein binder design with Claude*](https://www-cdn.anthropic.com/30bf50e22a01388bb29bf077ee3f244531594b7a.pdf), in which Claude ran 24–48 hour autonomous design campaigns against 16 protein targets from a single ~16,000-word protocol prompt; 354 of 1,320 resulting designs bound in the wet lab. The paper's own measurement of that prompt is the idea ResCamp is built on: **about a third of it was domain science, and the remaining two thirds were orchestration, verification, and operations.** ResCamp takes that second two thirds — the part that is not about proteins — and compiles it for any research field. That measurement is of word-count shares, and the paper ran no prompt ablation, so treat the two-thirds figure as a composition finding from one campaign in one field rather than a demonstrated causal contribution. See [Design principles](#design-principles) and [Sources](#sources).

**Version:** 0.8.6  
**Runtime:** Python 3.9+ (standard library only) for durable state, validation, rendering, and benchmarks. The instructions remain usable without Python, at the cost of every guarantee the engine provides.

## Design principles

**1. The transferable part of a research campaign is the contract, not the science.** The binder paper's protocol prompt was about one third domain guidance and two thirds orchestration, verification, and operations, and the paper attributes the campaign's ability to run unattended for 48 hours to that second part. ResCamp compiles the second part. Everything domain-specific comes from you in the interview; everything structural comes from the architecture.

**2. The engine never calls a model, and has no dependencies.** `rescamp/scripts/rescamp.py` is standard-library Python that keeps state, checks references, computes digests, freezes reviews, and renders. It cannot judge whether your research is any good, and it does not pretend to. This one decision is why the content digest means something, why a reviewer can run as a genuinely separate process, why the same tree installs byte-identically on two hosts, and why `audit --strict` is worth running at all.

**3. The split is between what can be proven and what must be judged.** The script proves presence, cross-reference integrity, graph acyclicity, budget declaration, and digest binding. A model judges substance. The interface between them is a four-way classification of every finding — `agent-fix`, `user-answer`, `external-approval`, `accepted-risk` — and the script only ever *classifies*. It never repairs. A finding marked `agent-fix` is one the model is expected to resolve without asking you, not one already resolved.

**4. Proportionality over ceremony.** A scoped archival question satisfies a section in two lines; a costly autonomous experiment needs registries and operational controls. Question budgets are 3–5, 4–8, and 6–12 by assurance profile, with hard stops that require your explicit authorization to pass. The rule is that no machinery earns its place unless it can change the research decision or protect integrity.

**5. Discipline-neutral by construction, not by search-and-replace.** There are no hypotheses, p-values, controls, or metrics in the object model. There are `inquiries` with `admissible_support` and `counterevidence_or_rival`, and a `verification_or_adjudication` step that may be a statistical test, a source-criticism protocol, a rival reading, or a stated adjudication rule. Eleven archetypes span experimental through creative practice; the safeguards in `rescamp/references/archetypes.md` explicitly forbid inventing a quantitative metric where reasoned adjudication is correct, or demanding falsifiability of an interpretive claim.

**6. Fail closed, and say what failed.** `finalize` returns distinct exit codes for design blockers (2), a stale freeze (3), and missing or failing reviews (4). It always renders something useful and always labels it. There is no path to an `EXECUTION-READY` bundle that skips review.

**7. Disclose limits in the artifact, not just the docs.** Independence is self-attested — nothing inside a Python script can watch another process and prove a separate reviewer ran — so review records carry `execution_evidence`, and `REVIEW_REPORT.md` says plainly that this is an attestation with an audit trail rather than proof, and states exactly which checks run at which profile. Section 0 of every rendered campaign states which sections were left empty and what challenge was actually applied. Benchmark fixtures stamp `evidence_class: synthetic-fixture` on their own output so a constant can never be mistaken for a measurement.

**8. A summary must not override a judgment.** A reviewer's `pass` verdict cannot launder an unresolved `critical` finding: the finding blocks, and the contradiction is reported. Only an explicit `accepted-risk` classification clears it, because that is a person taking responsibility rather than a verdict smoothing it over.

**9. A review is bound to what it reviewed.** Each reviewable unit — every campaign section, and every piece of top-level state a packet ships — has its own digest. A review record carries the digests of the units it is responsible for: its packet contents, plus whatever those reference, since a gate that names a method is reviewing that method too. So a budget repair invalidates the operations review and leaves methods standing, while an inquiry change reaches both, because gates depend on inquiries. Only `interview` and the engine's own bookkeeping are deliberately unbound — recording a turn must not discard a methodology review. After a re-freeze, `roles_requiring_review` names exactly who must run again.

**10. Integrity checks must not trust the thing they are checking.** `audit` verifies rendered artifacts against the hashes recorded in campaign state, not against the manifest sitting in the directory being audited — otherwise anyone who can run `sha256sum` can tamper an artifact and rewrite its manifest line. The work queue refuses to dispatch from a campaign that was never finalized, and rejects a dependency cycle at `init` rather than deadlocking silently at runtime.

**11. Honest degradation beats silent degradation.** Capabilities are declared, not guessed: `host-probe` records what it can test and marks the rest `unknown`, and `unknown` is treated as absent. A host that declares no subagents cannot file a review claiming one. High-assurance stays blocked when the required independence is unavailable, rather than quietly lowering the bar.

### Known tensions

These are real and unresolved, and named here rather than in a footnote:

- **Substance has no owner.** Deterministic checks verify presence and cross-references. The literal string `"x"` satisfies every required field, so bundle quality is a function of the driving agent's diligence. Section 0 discloses coverage; it does not enforce quality.
- **The enforcement window closes where research misconduct begins.** ResCamp compiles a plan and stops. It has no command to record an observation, no outcome ledger, and no reconciliation of final claims against the frozen inquiries. So the four methodological safeguards it is proudest of — freeze the instrument before evidence, separate exploratory from confirmatory, preserve null results, force counterevidence — are **prescriptions written into a prompt**, enforced only insofar as whoever executes the research obeys them. `frozen_before_production_asserted` is an attestation by the person compiling the campaign; nothing here can verify when a freeze actually happened, and nothing detects hypothesizing after results are known. What *is* enforced is that the compiled plan cannot drift after review.
- **A pre-review deletion leaves no usable trace.** `set campaign.inquiries '[]'` works, and the event log records the path that changed but not the value, so prior state is unreconstructible. After review, the section digest moves and `finalize` fails — but an inquiry dropped before any review is invisible.
- **Cross-section dependencies are declared, not derived.** Reviews are bound per unit and closed under a hand-maintained table of which sections reference which (`SECTION_REFERENCES`). Gate criteria and work-unit briefs reference other sections in free text, so the table cannot be derived from the object model; a new kind of cross-reference added without a matching entry would let a change slip past a reviewer who should have seen it. Tests assert the closure is non-trivial and that declared edges stay in scope, but an *absent* edge is invisible to them.
- **`set` and `apply` refuse engine-owned paths, but the state file is not a vault.** Anything that can write `state/campaign.json` directly can forge a review record, and no in-process check can prevent that. The CLI closes the sanctioned doors; it does not make the campaign tamper-proof against its own operator.
- **The staged funnel is mandatory.** Every stage needs a gate with an owner and a failure procedure, even for a one-researcher archival study where that is ceremony. Campaign sections have no `not-applicable` + `reason` vocabulary, though intent dimensions do.
- **The independence ladder is only half encoded.** Rungs 3 (agent blinded to conclusions) and 5 (external adjudicator with its own data) have no representation in the state model, and those are the two that matter most outside STEM. Distinct reviewer and executor identities are enforced only at the high-assurance profile.
- **`set` does not check field names.** It is the only bulk path for dict sections, and a misspelled field is stored and then rendered into the execution prompt beside the real one. Prefer `add`, which checks.
- **Live cross-harness benchmarking is unbuilt.** The harness runs fixtures correctly; comparing a real Claude Code session against a real Codex session needs a model-backed hidden user and evaluator that do not exist yet.

## One canonical skill

The repository contains exactly one installable skill directory:

```text
rescamp/
├── SKILL.md
├── agents/openai.yaml
├── assets/
├── references/
└── scripts/               # compiler, optional queue, benchmark, self-check
```

Claude Code and Codex read the same `SKILL.md` and supporting files. Only the installation path and invocation syntax differ.

## Install

Clone or unzip the repository, then run:

```bash
python3 scripts/install.py --host all --scope user
```

This copies the same `rescamp/` directory to:

```text
~/.claude/skills/rescamp      # claude-code
~/.agents/skills/rescamp      # codex
```

`--host` accepts any registered host id (`claude-code`, `codex`; `claude` and `both` remain aliases) or `all`. The host registry lives in `HOSTS` in `scripts/install.py` and is documented in `rescamp/references/hosts.md`; adding a harness is a registry entry and a table row, never an edit to `SKILL.md`.

The installer sets Claude Code's `skillOverrides.rescamp` to `user-invocable-only`. Codex uses the shared `agents/openai.yaml` policy (`allow_implicit_invocation: false`) to the same end. Each host ignores the other's metadata, which is why one byte-identical tree serves both.

Project-local installation:

```bash
python3 scripts/install.py --host all --scope project --project /path/to/repo
```

Manual installation is also valid:

```bash
cp -R rescamp ~/.claude/skills/rescamp
cp -R rescamp ~/.agents/skills/rescamp
```

The copied contents must remain byte-identical. For a manual Claude installation, also add this to `~/.claude/settings.json` (or the project-local `.claude/settings.local.json`) so ResCamp remains explicit-only:

```json
{
  "skillOverrides": {
    "rescamp": "user-invocable-only"
  }
}
```

## Invoke

Claude Code:

```text
/rescamp I want to determine whether ...
```

Codex:

```text
$rescamp I want to determine whether ...
```

ResCamp first presents a corrigible Campaign sketch v0, then asks one high-value question at a time. Typical interviews are 3–5 questions for scoped work, 4–8 for standard work, and 6–12 for high-assurance work. Hard limits require explicit extension authority.

### What actually happens

The model drives the engine. You are interviewed; it compiles. The sequence:

```text
init                    create the campaign and pick a profile and archetypes
host-probe              record what this host can and cannot do
turn / dimension        one per interview exchange, saved verbatim
add / set               compile answers into campaign objects
stop                    validate, freeze a digest, write reviewer packets, classify findings
  ↓ the model executes each packet as a separate read-only reviewer
ingest-review           one record per required role, bound to the frozen digest
finalize                fail-closed; renders the bundle or an honest blocked draft
audit --strict          re-verify state and artifact hashes
```

What is automatic and what is not, precisely: validation, the content freeze, packet preparation, and finding classification happen when the interview stops. **Executing the reviewers and repairing defects are the model's work, not the script's.** `finalize` is what makes that non-optional — it refuses an execution-ready bundle without ingested passing reviews bound to the current digest. Comparative benchmarking is never automatic and is unreachable from the interview path.

A realistic campaign of ~70 objects costs about **45 engine calls** when payloads are batched from files, and about **133** when objects are added one at a time. Write payloads to a file and pass `@file.json`: inline JSON breaks on apostrophes, which research prose is full of, and each such failure pushes the run toward the slow path. `schema <path>` prints the exact field vocabulary for any section.

### Working with the output

`CAMPAIGN_PROMPT.md` is the execution brief — hand it to whoever or whatever does the research. `KICKOFF.md` starts the first gate. `TASK_BRIEF_TEMPLATE.md` instantiates one bounded contract per work unit, carrying that unit's real permitted and prohibited actions. `REVIEW_REPORT.md` records what challenge was applied and states that its independence is attested rather than proven. Read section 0 of the campaign prompt first: it tells you what the campaign left empty.

## Automatic quality loop

When the interview stops, ResCamp automatically:

1. freezes a candidate campaign digest;
2. runs deterministic architecture and integrity checks;
3. prepares proportional read-only reviewer packets;
4. sorts every finding into `agent-fix`, `user-answer`, `external-approval`, or `accepted-risk`;
5. repairs the `agent-fix` findings and asks at most one or two additional material user questions when necessary;
6. reruns checks and renders either an execution-ready bundle or an honest blocked draft.

The division of labour matters. The Python only classifies (`rescamp/scripts/rescamp.py`, `classify_validation_findings`): it decides which bucket a finding belongs in and never edits a campaign. The repair in step 5 is done by the model following `SKILL.md`, and the rerun in step 6 is what checks whether the repair worked. A finding classified `agent-fix` is a finding the model is expected to be able to resolve without asking, not a finding the script has resolved.

This checks the **current campaign**. It does not automatically run an expensive comparison against old versions or unrelated tools.

Manual checks remain available:

```text
/rescamp review <campaign>
/rescamp test <campaign>
/rescamp benchmark <config>
```

Use the Codex `$rescamp` prefix for the same modes.

## Output bundle

A finalized campaign includes:

- `CAMPAIGN_PROMPT.md` — full campaign constitution and execution scheme;
- `KICKOFF.md` — compact execution start;
- `campaign.json` — machine-readable contract;
- `ROADMAP.md` — concise human roadmap;
- `TASK_BRIEF_TEMPLATE.md` — bounded worker contract;
- `REVIEW_REPORT.md` — validation and reviewer evidence;
- `CLAIMS_EVIDENCE_MATRIX.json` — support, counterevidence, and verification links;
- `RUNBOOK.md` — resources, continuation, recovery, and approvals;
- `BLOCKERS.md` — only when unresolved;
- `MANIFEST.sha256` — artifact hashes.

The campaign prompt is translated from the architecture of Anthropic's protein-binder campaign (see `docs/PAPER_ANTHROPIC_BINDER.md` for the section-by-section mapping). Most of it is a direct translation: one constitution inherited by every worker, an exact mission, a dossier, method diversity with floors and ceilings, production-like tool canaries, an evaluation instrument frozen before production evidence is inspected, staged promotion gates, a resource governor with clock discipline, bounded delegation, verify-before-reporting, and a compact kickoff. Some of it is extrapolation the paper does not support: durable recovery, rights and safety controls, and plan-stage independent challenge. One section, the inquiry-and-evidence loop, comes from a different paper (`docs/PAPER_LITTLE_SCIENTIST.md`) and not from the binder campaign, which has no such loop.

What is not translated is the thing that made the paper's numbers mean anything: two external laboratories that physically measured 1,320 designs. ResCamp has no adjudicator of that kind. Non-STEM research can use rival interpretations, negative cases, objections, source criticism, or adjudication rules instead of artificial numerical metrics — `docs/GENERALIZATION.md` sets out which of those substitute for what, and where nothing does.

## Durable engine

```bash
python3 rescamp/scripts/rescamp.py --help
python3 rescamp/scripts/rescamp.py init \
  --goal "Determine whether ..." \
  --profile standard \
  --archetypes evidence-synthesis
```

The agent normally drives these commands. State is stored under `research-campaigns/<campaign>/` with an append-only event log, review packets, rendered outputs, and hashes.

### Optional continuous workflow

A finalized campaign with `runtime.enabled: true` and bounded work units can use the included SQLite queue:

```bash
python3 rescamp/scripts/workflow.py init --campaign outputs/campaign.json --db workflow.sqlite
python3 rescamp/scripts/workflow.py claim --db workflow.sqlite --worker worker-1
python3 rescamp/scripts/workflow.py status --db workflow.sqlite
```

The queue persists leases, approvals, retries, events, and artifact hashes. It never calls a model, runs scientific tools, or grants approval; a real scheduler or operator must invoke workers.

## Benchmark

The manual benchmark separates Team U (hidden user), Team S (tested system), and Team E (blinded evaluator). Public calibration cases cover 18 domains and all supported research archetypes, including humanities, law, qualitative research, public policy, design, and creative practice.

Harness smoke test:

```bash
python3 rescamp/scripts/benchmark.py validate-scenarios benchmark/scenarios/public
python3 rescamp/scripts/benchmark.py run \
  --scenarios benchmark/scenarios/public \
  --config benchmark/conditions/fixture.json \
  --output benchmark/runs/fixture
```

The fixture verifies information boundaries, scoring, manifests, and aggregation. It is not evidence that one live model or tool is superior.

For a real comparison, generate or adapt a matched matrix with `scripts/create_benchmark_matrix.py` or `benchmark/conditions/live-template.json` and follow `benchmark/adapters/external_command_protocol.md`. Match the model, host, tools, corpus, permissions, context, token/time budget, retries, and hardware. Compare ResCamp 0.8 with the previous version and a neutral no-skill baseline before adding external systems. Compare external tools only on capabilities they claim.

## Validate the repository

```bash
python3 scripts/validate_release.py --root .
```

This compiles scripts, validates JSON/scenarios, runs all unit and generalization tests, executes the three-team fixture matrix, tests identical dual-host installation, and audits release structure.

## Scope and limits

ResCamp compiles and reviews a campaign. It does not turn a chat session into a scheduler, grant permissions, substitute for ethics or legal approval, or make an AI-generated scientific result valid. Continuous work requires a real queue, CI job, scheduler, automation, or operator trigger. High-assurance review is blocked when genuinely separate reviewers are unavailable.

See `docs/` for architecture, generalization, benchmarking, source readings, and release evidence.

## Sources

- **Primary.** *Autonomous de novo protein binder design with Claude*, Claude Science and Amir Shanehsazzadeh, Anthropic, 18 August 2026. [PDF](https://www-cdn.anthropic.com/30bf50e22a01388bb29bf077ee3f244531594b7a.pdf) · [prompts, corpus, and binding data](https://huggingface.co/datasets/Anthropic/claude-protein-binder-design). Reading, section mapping, and an explicit list of what ResCamp does not reproduce: `docs/PAPER_ANTHROPIC_BINDER.md`.
- **Secondary.** *The Little Scientist: LLM Agent-Driven Discovery via the Scientific Method*, Travis Smith, [arXiv:2608.16951](https://arxiv.org/abs/2608.16951), 16 August 2026. Source of the inquiry-and-evidence loop only. Critical reading: `docs/PAPER_LITTLE_SCIENTIST.md`.
- How the two combine with the skill's non-cited design judgment: `docs/DESIGN_BASIS.md`.

## License

MIT. Third-party systems listed for benchmarking retain their own licenses and must be installed and evaluated separately.
