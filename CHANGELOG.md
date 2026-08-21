# Changelog

## 0.8.5

Findings from three independent reviewers — function, efficiency, and scientific precision — run against 0.8.4 immediately before first publication. The function reviewer's verdict was "do not publish as-is", and it was right.

### The 0.8.4 regression it caught

Per-section digests covered `campaign.*` only, so **every top-level field became unbound**: `goal_verbatim`, `sketch`, `assumptions`, `contradictions`, `blockers`, `intent_dimensions`, and `archetypes` could all be rewritten after review with both reviews still reported current and `finalize` returning `EXECUTION-READY`. Six of those are shipped inside review packets, and the reviewer prompt told reviewers the record bound "exactly the sections you were shown" — which it did not. So 0.8.4's headline claim, "tighter than the whole-campaign seal, not looser", was **false in the one place it mattered**.

Digests now cover every reviewable unit: campaign sections by name, top-level state keyed with `@`. Only `interview` and engine bookkeeping are deliberately unbound, which is the whole point of the feature. Verified field by field: rewriting the research goal or the assumptions now invalidates the reviews that were shown them; recording an interview turn still invalidates nothing.

### Other integrity holes closed

- **`set` was an unguarded door around `ingest-review`.** `set reviews.records '[...]'` wrote review records directly, skipping every check on mode, execution evidence, verdict, and findings shape — a demonstrated end-to-end forgery. `set`, `add`, and `apply` now refuse `reviews`, `status`, `outputs`, and `last_validation`. This does not make the state file a vault, and the README says so.
- **`audit` reported a clean bill of health on a deleted bundle.** An empty or missing `outputs/` skipped artifact verification entirely while state still recorded nine files. Now an error.
- **`SECTION_REFERENCES` was inert.** Every declared edge already terminated inside its own role's scope, so the closure widened nothing and could not justify the sentence written to defend it. The load-bearing edges were the undeclared ones: gate criteria name methods and inquiries by id, so gutting a method left the reviewer who approved the dependent gate none the wiser. Added `gates→methods,inquiries`, `stages→methods,tools`, `work_units→methods,gates,stages`, `evaluation→methods,inquiries`. This *reduces* the measured saving on inquiry repairs — correctness over efficiency — and a test now fails if the closure ever goes inert again.
- **A plain string in `blockers` or `contradictions` crashed every command** with a raw `AttributeError`. Plausible mistake, since three neighbouring sections are string lists. Now a validation error naming the path.
- A record's `content_digest` went unchecked once `reviewed_sections` was present. `workflow.py reconcile` reported clean on its second run after a tamper, because it scanned only `succeeded` units.

### Scientific precision

- **The fixture benchmark emitted 95% confidence intervals on hardcoded constants.** Team E ratings are constants selected by condition id, so the entire spread is scenario heterogeneity — yet the summary printed `[-52.2, -47.9]`, which reads as a measured effect with tight uncertainty. Intervals are now suppressed for any fixture-derived condition, and refused below n=5 where the bootstrap degenerates (at n=1 it returned a zero-width interval; at n=3, `[min, max]`).
- **`frozen_before_production` asserted a fact the tool cannot verify.** Renamed `frozen_before_production_asserted`, with a validator message that says plainly it is an attestation by whoever compiled the campaign.
- **Four factual defects** across the cited numbers: a 317-file corpus count the paper never gives; a 0.68–0.70 band attributed to one target when it describes three; a κ=0.71 presented as symmetric inter-lab agreement when the paper compares a classification against the presence of a fit; and the label-combination rule cited as warrant for the frozen-instrument section when the paper says it was written *after* both labs reported. It is now marked as a contrast case where ResCamp departs from the paper.
- The docs promised "hierarchical bootstrap intervals"; the code resamples runs i.i.d., which is anticonservative under within-scenario correlation. The docs now say what the code does.
- Non-STEM benchmark dimensions may declare `branch` explicitly. Keyword routing sent `rival-readings` and `objections` to `scope-object` by default, so one scope question could be credited with eliciting a philosopher's objections — swinging turn-discounted recall by 100% vs 36% on string luck.
- README now states that **the enforcement window closes where research misconduct begins**: ResCamp compiles a plan and stops, so its methodological safeguards are prescriptions in a prompt, not enforced properties.

### Efficiency

- **New `apply` command** writes many sections in one call with the same field checking `add` performs, and writes nothing if any object fails. Previously the only bulk path was `set campaign @whole.json`, which is one call and checks nothing. Takes a realistic campaign from ~45 calls to ~27 without losing validation.
- `quality-loop` emits `review_packets_to_execute` (stale roles only) alongside the full list; listing every packet invited a fan-out that erased the entire per-section saving.
- Validation stdout is capped, with the full findings left in `working/validation.json`. On a large campaign with a systematic mistake this was ~15k tokens per repair round.
- `substantive_state` no longer deep-copies for read-only callers (~6 copies per validate), and `platform` is imported lazily rather than costing ~6 ms on every call.

94 tests, up from 85.

## 0.8.4

Per-section review binding. Both the design and efficiency reviewers independently ranked whole-document digest granularity as the highest-leverage change outstanding; this is it.

### What changed

A review used to be bound to a digest of the entire campaign, so **any** change invalidated **every** review — including changes to sections the reviewer never saw, and including interview bookkeeping that touches no campaign content at all. Recording one interview turn threw away two completed high-assurance reviews.

Each campaign section now carries its own digest. A review record carries the digests of the sections it is responsible for: its packet sections, closed under a table of cross-section references, because a gate that names a method is reviewing that method too. Staleness is then per-review.

- A budget repair invalidates the operations review and leaves the methods review standing.
- An inquiry revision invalidates the methods review and leaves operations standing.
- Recording an interview turn invalidates nothing.

`quality-loop` and `stop` now report `reviews_still_current` and `roles_requiring_review`, and `next_action` names exactly which reviewers must run again. On the test campaign a repair round costs 49% of a full round; on a high-assurance campaign needing several rounds the saving compounds.

A record is valid only while every unit it is responsible for is byte-identical to what it reviewed, and it must cover exactly its role's required set — a record that drops a unit, pads its set, or forges a digest is rejected. Any rubric change still invalidates everything.

*(0.8.5 corrects an overclaim first made here: as shipped in 0.8.4 this was **looser** than the whole-campaign seal, because only `campaign.*` was digested and all top-level state went unbound. See 0.8.5.)*

### Coverage hole this exposed

At the `standard` profile, `ethics_rights_safety` was in **no** reviewer's scope. Under the old whole-document digest that was invisible, because every change invalidated everything anyway. Under per-section binding it would have meant a change to consent, rights, or approval boundaries invalidating nobody's review. It is now in the operations scope, and a test asserts every campaign section is covered at every profile.

### The eager wipe is gone

`set`, `add`, `dimension`, `turn`, and `stop` each unconditionally cleared all review records. That was redundant — staleness is computed from digests — and it destroyed the findings text the repairing agent was working from. Records are kept and filtered on validity instead.

### Also

- `review.schema.json` documents `reviewed_sections`; the reviewer prompt tells reviewers to copy it verbatim and not to report sections outside their scope as missing.
- Records written before this change keep the old all-or-nothing rule, which is strictly stronger, so nothing in flight silently expires.

85 tests, up from 71.

## 0.8.3

Findings from three independent reviewers, each given one dimension — function, efficiency, design — and no access to the others' conclusions.

### Integrity claims that outran the code

- **`audit` trusted the manifest it was auditing.** It verified artifacts against `outputs/MANIFEST.sha256`, a file inside the directory under audit, and ignored the copy in campaign state that also covers the manifest's own digest. Anyone who could run `sha256sum` could tamper an artifact, rewrite its one manifest line, and get a clean audit. It now verifies against the state record and detects a modified manifest. `audit` without `--strict` also exited 0 while printing `"ok": false`; it now exits non-zero.
- **The work queue dispatched from campaigns that were never finalized.** `workflow.py init` checked only `runtime.enabled`, so a campaign with no mission, no reviews, and a `NOT EXECUTION-READY` bundle initialized and claimed work. The one component that actually dispatches was the one skipping the readiness check. It now requires `status: execution-ready` unless forced, and rejects a work-unit dependency cycle at init rather than accepting the campaign and then silently never claiming anything.
- **A `pass` verdict laundered a critical finding.** A review could return `verdict: pass` while recording a `critical` finding — "no consent process is specified for minors" — and the campaign reached `EXECUTION-READY` with the finding visible only in `REVIEW_REPORT.md`. Unresolved critical findings now block, and a `pass` verdict recorded alongside one is reported as a conflict. Only an explicit `accepted-risk` classification clears it.

### Compiler and runtime disagreed about work units

`OBJECT_SPECS` declared `depends_on` and `retry_policy`; `workflow.py` reads `dependency_ids`, `approval_ids`, and `retry_limit`. `add` therefore rejected the exact three fields the queue enforces, so a campaign built through the sanctioned API produced a queue with no dependency graph and no approval gates. Aligned, with tests guarding both directions and one that goes through `add` rather than around it — the same bypass that hid the review-record bug in 0.8.2.

### Efficiency

A ~70-object campaign was measured at 45 engine calls batched versus 133 naive, with the longest unbroken run dropping from 114 calls to 26. There is no practical O(n²): per-call time is flat at ~89 ms up to 200 KB of state, and startup is ~80% of each call but irrelevant at this scale.

- **Review packets were byte-identical apart from the role string**, ~16k tokens each, so a methods reviewer read the runtime config and the whole interview transcript. Packets are now role-scoped, with a test asserting no section drops out of *all* review.
- **`add --json @file.json` is now the documented canonical form.** It always worked but appeared nowhere, while the documented inline form breaks on apostrophes — the failure that pushes a run onto the 133-call path.
- `schema` covers the nine dict sections, saving a forced ~4k-token read of `architecture.md`.
- `findings_by_action` emits codes and paths instead of repeating every finding verbatim; it was 39% of the largest stdout a driving agent sees.
- `--fail-fast` now actually fails fast: `pool.map` submitted every job eagerly, so a broken adapter cost the entire matrix before the error surfaced.

### Corrections

- **`campaign.claims` was never rendered into `CAMPAIGN_PROMPT.md`**, surviving only in the JSON matrix, despite `objects.md` promising every field reaches the prompt with three named exceptions. Now rendered in section 13.
- **Two documents inverted the actual `set` behaviour.** They warned that a misspelled field is "never rendered". The opposite is true and is the real hazard: it is rendered into the execution prompt as authoritative content, beside the real field it was meant to be.
- **`REVIEW_REPORT.md` over-claimed.** Its boilerplate said the engine checks that reviewer identities and executors are distinct; that check runs only at high-assurance. The text now says which checks run at which profile.
- The independence rung was a lexicographic `max` over display strings, so an unrecognized mode sorted above "human domain expert". It is an ordinal now, and reports the **weakest** rung among required reviews, since one sequential pass bounds the whole set.
- `workflow.py audit` inspected only `succeeded` units, so running `reconcile` after a tamper moved the unit to `blocked` and the audit then reported the run clean. It now covers blocked units and reports them.
- `SKILL.md` carries a mode↔CLI crosswalk: `resume`, `revise`, and `help` are documented modes with no subcommand, so an agent would reach for `rescamp.py revise` and fail.

### README

Added **Design principles** (ten, with the sources of each) and a **Known tensions** section naming what is genuinely unresolved: substance has no owner, digest granularity makes the mandated repair loop expensive, the staged funnel is mandatory even where it is ceremony, the independence ladder is half-encoded, `set` does not check field names, and live cross-harness benchmarking is unbuilt. Added a **What actually happens** section with the real automatic/manual split and the measured call-count guidance. The primary paper is now cited in the opening paragraph, framed around the one-third/two-thirds finding the tool is built on.

71 tests, up from 65.

## 0.8.2

Portability and honest-signalling pass, from an independent audit of how the tool actually behaves rather than how it is documented.

### Host portability

- `SKILL.md` no longer names a host. It previously hardcoded "Claude Code invokes `/rescamp`; Codex invokes `$rescamp`", which contradicted the claim that adding a host never touches the canonical instructions. Per-host paths, invocation syntax, and explicit-only policy now live only in `references/hosts.md`.
- `references/hosts.md` is now a registry and a capability contract rather than two install recipes: a host table, declared-not-guessed capabilities, and the rule that a new host adds a metadata file and a table row, never a `SKILL.md` line.
- `scripts/install.py` is table-driven via a `HOSTS` registry. `--host` accepts any registered host id plus `all`; `claude` remains an alias for `claude-code`. Unknown hosts fail with the list of known ones. A host that keeps explicit-only policy in host settings declares a settings writer; installing Codex alone no longer touches Claude settings.
- Fixed a tautological integrity check: under `--symlink` the installer compared the resolved destination against the source, which is the same directory and could never fail. It now verifies the link target.
- `digest_tree` includes the executable bit, so a copy that lost `0755` on `scripts/*.py` is no longer reported as identical.
- `guide` now fails loudly when `references/` is missing or empty instead of printing nothing and exiting 0, which made a truncated install look like a skill with no references.
- Review packets carry an absolute `required_output_schema` path, so a reviewer running as a separate process on any host can resolve it.
- Corrected the declared Python floor from 3.10+ to 3.9+, which is what the code actually runs on.

### Independence is attested, and now says so

- A review record could claim `mode: independent-subagent` with nothing corroborating it, and high-assurance would stamp `independence_ok: true`. Modes claiming independence now require `execution_evidence` with `executor_id`, `started_at`, and `completed_at`, and high-assurance additionally requires distinct executors — one process relabelled twice is a sequential pass wearing two hats.
- `REVIEW_REPORT.md` now states plainly that independence is self-attested and that an agent reviewer is not external validation. This is an audit trail, not proof; nothing inside the skill can observe another process.
- A clean review with `findings: []` was rejected as "missing findings", forcing reviewers to invent a filler finding to pass. The test suite missed it because fixtures inject records directly into state, bypassing `ingest-review`.

### Honest signalling of what ran

- `stop` and `quality-loop` printed `automatic_quality_loop: true` — a hardcoded literal that appeared even for a campaign with no interview turns and nineteen validation errors. Replaced with `completed_by_this_command` and `not_run_by_this_command`, an explicit `reviews_ingested` count, and `review_packets_are_inputs`. `phase` is now `awaiting-review-execution` / `awaiting-design-repair` rather than the ambiguous `review-required`.
- To be explicit about the division of labour: deterministic validation, the content freeze, packet preparation, and finding classification are automatic. Executing the reviewers and repairing defects are the model's job, enforced only by `finalize` refusing to produce an execution-ready bundle without ingested passing reviews. Comparative benchmarking remains manual and is unreachable from the interview path.

### Benchmark integrity

- `fixture_team_e` scored any unrecognized condition with hardcoded no-skill constants and reported a confident bootstrap CI. Plugging in a real system without a real evaluator produced a fabricated measurement. Unknown conditions are now refused with a pointer to the adapter protocol.
- Team S was handed the full condition record, including `user_adapter` and `evaluator_adapter` — telling an agentic system under test exactly where the hidden-user oracle and the grader live. The payload is now restricted to a visible-key whitelist.
- `scripts/create_benchmark_matrix.py` emitted `matched_controls` with every field hardcoded `true`, including `blinded_evaluation`, none of which the harness reads or checks. The block is now `matched_controls_declared_by_operator` and starts as `unverified`.

### Usability, from an end-to-end run of a humanities campaign

An auditor compiled a real oral-history campaign — 8 interview turns, 68 objects, all 16 sections, two rounds of genuinely separate reviewers — and reported ~111 CLI calls plus ~14 discovery calls. The findings below come from that run.

- **The CLI sequence was documented nowhere.** `SKILL.md` now carries the working `init → host-probe → turn/dimension → add/set → stop → ingest-review → finalize → audit` sequence, with the `add`-versus-`set` trade-off stated.
- **`set` silently created junk keys.** A one-character typo in a section name (`campaign.evalation.criteria`) returned success, created a junk key, discarded the content, and polluted the content digest — while the agent saw only "criteria is missing". `set` now rejects unknown path segments and lists the real keys; `--create-missing` restores the old behaviour deliberately. Out-of-range list indices give a message instead of an `IndexError` traceback.
- **`add` accepts an array**, so a campaign is populated in a handful of calls instead of one subprocess per object. Field checking still applies, and the error names which array item failed. `set` on a whole subtree remains the unchecked path and now says so.
- **The archetype names in `SKILL.md` were wrong** — it listed `qualitative/field` and `evidence synthesis` where the engine requires `qualitative-field` and `evidence-synthesis`, so the first command a fresh agent ran failed. Corrected, and the error now lists the valid values.
- **`rubric_digest` included the tool version**, so bumping 0.8.1 → 0.8.2 invalidated every frozen review of every in-flight campaign with the eleven rubric checks byte-identical. It now depends only on the checks. The stale-review error names which digest mismatched, expected versus actual, instead of six unhelpful words.
- **`TASK_BRIEF_TEMPLATE.md` ignored the campaign's actual work units** and shipped a generic stub — on a campaign whose defined unacceptable failure was an anonymity breach, the delegation brief carried none of its real prohibitions. It now instantiates one brief per defined work unit.
- **`KICKOFF.md` dropped `first_gate_id` and `initial_backlog`** and could ship empty. It now carries the first gate with its evidence and failure procedure, the backlog, and the standing constitution rules; an empty kickoff command is a validation error.
- **`CLAIMS_EVIDENCE_MATRIX.json` was a dump of `claims`**, which may legitimately be empty, so it often rendered as `[]` while the inquiries carrying exactly its columns were absent. It now includes both.
- **Sections 14 and 15 were static boilerplate identical for every campaign.** Section 14 renders the real acceptance tests and the deliverable-immutability rule; section 15 names the highest independence rung actually reached.
- **New section 0** discloses which sections were left empty and what challenge was applied. Deterministic validation checks presence and cross-references, never substance: an auditor built a campaign in which every field was the literal string `"x"`, self-attested two passing reviews, and got `EXECUTION-READY`. Kickoff command, first gate, and ethics constraints are now required, and the bundle states its own coverage rather than letting a thin campaign read as a complete one.
- **`host-probe` now exists.** `references/hosts.md` described it, a `host_profile` state key, and a gating system, none of which were implemented — fiction introduced in the same release that documented it. The subcommand probes what is testable, records declared capabilities as `unknown` unless stated, and a declared absence of subagents now rejects a review claiming `independent-subagent`.
- **`references/objects.md` claimed "nothing is dropped and nothing is summarized away."** That was false three ways; it now states the `set` gap and names the state that the prompt deliberately does not render.

### Tests

- Replaced the host-leak test, which was written with a token list that passed over the exact violation it claimed to catch, with assertions on the names a host is actually referred to.
- Renamed and rewrote `test_stop_automatically_runs_current_plan_quality_loop`, whose central assertion was a hardcoded `True`. It now asserts the load-bearing fact: `stop` runs no reviewer and leaves the campaign not execution-ready.
- Replaced a static check that grepped `install.py` for the literal line `hosts = ["claude", "codex"]` with a structural check of the host registry.
- Added coverage for review-record evidence, empty findings, host-registry/documentation agreement, typo'd `set` paths, batched `add`, rubric-digest stability across tool versions, host-capability gating, and the four bundle-content fixes. 59 tests, up from 44.

### Known and not fixed

- Deterministic validation still cannot judge substance. Section 0 discloses coverage; it does not enforce quality. The only substance gate remains a review the driving agent produces itself.
- Every mutation still clears all ingested reviews, so a repair round costs a full re-review. Per-finding disposition is not implemented.
- Phase E (bounded pilot) and the `reviewed-static` label are still instructions to the model with no state tracking behind them. Section 0 now says so in the rendered bundle rather than leaving it implicit.
- `revise` remains a documented skill mode with no CLI subcommand; the model performs it as `set`/`add` followed by `quality-loop`.
- The live benchmark path is still unbuilt: `live-template.json` names three adapter files that do not exist, the Team U fixture matches on an undocumented `branch` field and leaks dimension IDs into visible text, Team S is unsandboxed, and a Team S that writes an artifact de-blinds itself to the evaluator through the artifact path.

## 0.8.1

A repair pass. An audit found that the repository asserted a provenance it could not support from inside itself, and that several claims overstated what the code and fixtures do. Nothing in this release adds capability.

### Provenance

- Added `docs/PAPER_ANTHROPIC_BINDER.md`, the missing primary-source document: a reading of *Autonomous de novo protein binder design with Claude* (Anthropic, 18 August 2026), a section-by-section map from the paper to ResCamp's 16 architecture sections marked direct-translation or extrapolation, and an explicit list of what ResCamp does not reproduce — external wet-lab adjudication, the offline document corpus, the private host primitives, the 16,000-word domain content, live 24–48 hour autonomy, and any measured outcome. Cites the PDF and the HuggingFace release.
- Renamed `docs/PAPER_2608.16951.md` to `docs/PAPER_LITTLE_SCIENTIST.md` so the filename no longer implies it is the source paper, and added a header naming it as secondary. Its content is unchanged; it supplies the inquiry-and-evidence loop and nothing else.
- Rewrote `docs/DESIGN_BASIS.md`. Both papers are now named by title with URLs. Terms that are ResCamp coinages (canary, campaign constitution, independent challenge, assurance profile) are marked as such and no longer attributed to Anthropic; in the paper "independent" means two external contract research organizations, not an audit. Each of the four evidence streams now states whether it is a direct translation, an extrapolation, or uncited design judgment.
- Added a Sources section to `README.md` and corrected the architecture paragraph, which had claimed the whole architecture came from the binder campaign.

### Corrected overclaims

- `README.md`: the automatic quality loop was described as fixing agent-resolvable defects. The Python only classifies findings into `agent-fix`, `user-answer`, `external-approval`, and `accepted-risk`; the repair is done by the model following `SKILL.md`, and the rerun is what checks it. The division of labour is now stated.
- `docs/GENERALIZATION.md`: "18 cases across 18 domains" now notes that one case is the source domain, that three labels sit in one adjacent policy area, and that all 18 were written by the skill's author and are calibration material rather than holdouts.
- `docs/GENERALIZATION.md`: the non-STEM gap was framed as untested rather than structural. It now states that sections 6, 7, 8, and 15 are load-bearing only because an expensive external adjudicator sat at the end of the paper's funnel, gives the substitutes available in archival, interpretive, and normative work (peer review, source triangulation, independent coding, adversarial collaboration, preregistration, negative cases), and names the two situations where nothing substitutes.

### Concurrent fixes by other contributors

- Renderer: `CAMPAIGN_PROMPT.md` emitted raw JSON blobs where formatted sections were expected.
- Content digest: a successful finalize invalidated its own reviews.
- Benchmark: bootstrap seeds were nondeterministic.
- Campaign object field vocabulary was undocumented.
- Six fidelity gaps closed in the reference files: clock discipline and budget-as-floor; the 2:1 orchestration-to-science proportion heuristic read from the paper's 34.2 / 34.7 / 31.1 split; iterate-then-freeze pilots; deliverable immutability; within-stratum instrument calibration; and an independence ladder making explicit that agent review is not external validation.

## 0.8.0

- Replaced host-specific skill variants with one canonical `rescamp/SKILL.md` and one installable bundle.
- Added identical Claude Code and Codex installation with host policy configured outside the shared instructions.
- Generalized campaign objects and evaluation vocabulary across STEM, social science, humanities, law, policy, design, and creative practice.
- Made current-campaign validation and proportional reviewer preparation automatic at interview stop; retained manual `review`, `test`, and `benchmark` modes.
- Preserved the full Anthropic campaign architecture while reducing recurring skill context to 147 lines.
- Added process-separated Team U/S/E benchmark protocol, public calibration cases across 18 domains, critical-defect caps, matched comparison, and external-command adapters.
- Added durable state, digest-bound reviews, artifact rendering, hash audit, release validation, identical-install tests, and GitHub-ready packaging.
