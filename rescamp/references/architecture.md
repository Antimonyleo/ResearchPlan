# Campaign compilation architecture

Use this reference after the initial sketch and before rendering. It generalizes the architecture of Anthropic's multi-target protein-binder campaign prompt, described in "Autonomous de novo protein binder design with Claude" (Anthropic, 18 August 2026) with the released prompts at <https://huggingface.co/datasets/Anthropic/claude-protein-binder-design>, without importing biology-specific requirements.

## Proportion of the compiled prompt

That campaign measured its own protocol prompt at roughly 34% domain and science guidance, 35% orchestration and verification, and 31% operations. Roughly two thirds of the artifact was machinery for running the work, not content about the subject.

Use this as a rough target for the rendered `CAMPAIGN_PROMPT.md`. The common failure is a rich domain section attached to a thin orchestration section: deep subject expertise, then one line about who verifies what, one line about budget, nothing about recovery. Such a prompt reads well and cannot survive unattended execution. This is a heuristic measured on one campaign in one field, not a law; a short scoped campaign may justify different proportions, but state the reason when the rendered prompt departs far from it.

## Iterate, then freeze

The published protocol prompt was frozen only after test campaigns exposed failures in it. Static review of a document is not the same as watching it fail. For high-assurance or expensive campaigns, run a bounded cheap pilot of the compiled campaign, record what actually broke, repair, and only then freeze. See `quality-loop.md`, Phase E.

## 1. Constitution before local tasks

Create a short campaign constitution that every orchestrator, worker, reviewer, and recovery process inherits. It must define:

- the research purpose and decision authority;
- verification and provenance rules;
- what agents may decide versus what requires user or institutional approval;
- preservation of raw evidence, failures, nulls, contradictions, and deviations;
- budget, safety, privacy, and external-action limits;
- reporting from canonical artifacts rather than conversational memory.

A worker's local brief narrows its scope but cannot weaken the constitution.

## 2. Mission, boundary, and exact output

State the mission as a decision or knowledge purpose, not merely a topic. Define objects of study, jurisdiction/time/population/corpus/construct boundaries, non-goals, intended users, exact deliverables, and completion tests. Record excluded interpretations and dependencies.

## 3. Dossier before production

Build the minimum dossier needed to design the work:

- exact object/case/system/corpus/population;
- current state and relevant context;
- source hierarchy and admissibility;
- existing evidence and competing accounts;
- access, ownership, rights, approvals, and known data limitations;
- domain-specific vocabulary or construct definitions.

The dossier is not a literature dump. Every item must change scope, method, evaluation, risk, or interpretation.

## 4. Inquiry and evidence logic

Represent each central inquiry with:

- question, claim, hypothesis, or interpretive problem;
- why it matters to the mission;
- admissible supporting evidence;
- disconfirming evidence, counterexample, rival explanation, rival reading, or objection;
- expected discriminating implication when prediction is meaningful;
- uncertainty and external-validity boundary;
- verification or adjudication procedure;
- reporting rule.

Prediction is mandatory only when the inquiry supports one. Historical, qualitative, normative, or interpretive projects may instead use source criticism, rival explanations, negative cases, counter-readings, conceptual counterexamples, or explicit adjudication principles.

## 5. Method portfolio

Use complementary methods only when they address different failure modes or evidence gaps. For each method record inputs, outputs, assumptions, limitations, cost, dependencies, and the decision it can change. Define diversity floors or caps only when method monoculture is a material risk.

## 6. Tool qualification

For every production tool, model, database, instrument, coding pipeline, retrieval system, transcription process, or connector:

1. identify version, configuration, access, license/rights, and authoritative documentation;
2. run a production-like canary end to end;
3. require parseable artifacts and expected schemas;
4. include positive, negative, or sanity cases when meaningful;
5. verify downstream consumption;
6. quarantine suspicious constants, impossible runtimes, perfect outputs, missing counts, or silent fallbacks.

A successful import or help command is not a canary.

## 7. Freeze the evaluation instrument

Before inspecting production results, freeze:

- acceptance/adjudication criteria;
- comparators, controls, benchmark cases, counterexamples, or calibration materials;
- scoring formulas or judgment procedures;
- missing-evidence and conflict policy;
- sampling, replication, seed, coding, or source-selection rules;
- exploratory versus confirmatory status;
- stop, promote, pivot, and no-go rules.

For interpretive work, the instrument may be a source-criticism protocol or adjudication rubric rather than a numerical score. Changes after evidence inspection must be versioned and labeled exploratory unless independently justified.

### Calibration is stratum-local until proven otherwise

A frozen instrument can rank well inside a stratum and be worthless across strata. In the published campaign the automated confidence score separated successes from failures within a single target (mean average precision 0.52 against a 0.31 chance baseline) but barely transferred between targets: the three least successful targets shared a median band of 0.68–0.70, and one of them (MBP) produced 0 confirmed hits out of 90 candidates, while a target scoring 0.72 produced 54 out of 90. A confident score was a useful requirement for selection, not a guarantee of success.

Therefore:

- name the strata the instrument may be sensitive to — target, site, genre, jurisdiction, period, archive, language, coder, subpopulation, model version;
- declare every threshold as within-stratum unless cross-stratum calibration is demonstrated on held-out strata;
- do not use raw instrument scores to rank strata, forecast yield, or reallocate effort between strata without that demonstration;
- record the calibration evidence and its stratum alongside the threshold, so a later reader can see where the number is licensed.

A rubric calibrated on one genre, jurisdiction, or period does not transfer by default. Treat transfer as a claim requiring its own evidence.

## 8. Staged funnel and bounded adaptation

Order stages so that cheap, reversible checks precede expensive, irreversible work. Each stage must have inputs, activities, outputs, owner, budget, prerequisites, and a gate with evidence. Adaptive work must operate within frozen bounds and preserve every branch and decision. Confirmatory assessment uses a held-out or otherwise protected instrument where feasible.

For a broad campaign spanning multiple days, contexts, or teams, put an independent checkpoint review at each major execution stage that produces a decision-bearing artifact. Record it in the gate's `checkpoint_review`: reviewer role, frozen inputs, and the decision it controls. Eight major execution stages normally produce eight review gates, not a review after every task. This counts execution stages, not the sixteen architecture sections of the plan itself. Group small or low-risk steps, and add a further review only where it protects a distinct material decision.

The reviewer works in a fresh read-only context and receives only the active plan digest, relevant frozen sections, stage artifacts, and rubric. It returns `pass`, `revise`, or `block` and presents at most three material findings, highest priority first, each tied to its execution consequence and smallest repair.

The cap bounds cost, not disclosure. A reviewer that finds more than three material findings returns `block`, states the total it found and the highest severity among them, and presents only the top three. Silent truncation is the failure mode here: a capped review that reports three findings and nothing else is indistinguishable from a review that found exactly three, and the difference is the whole signal.

Repair once and recheck the affected scope. After two rounds, escalate any remaining blocker to the gate owner rather than continuing under it; minor or stylistic suggestions go to the backlog.

## 9. Resources and fail-closed dispatch

Define budget units, time, personnel, compute/materials, access, concurrency, and approval ceilings. A dispatcher must refuse new work when state is stale, budget is exhausted, approval is absent, or required artifacts are missing. Name the single canonical owner of each mutable record.

### Clock discipline: budget is a floor as well as a ceiling

Sustained autonomy depends as much on pace as on limits. A budget expressed only as a cap answers "when must this stop" and never "is this moving". Define both.

For each campaign state:

- the budget unit, in whatever currency the discipline actually spends — wall-clock hours, reading days, archive visits, interviews, coder-hours, compute, reagents, spend;
- the expected progress per unit: candidates screened, sources read, cases coded, interviews completed, branches closed;
- pace checkpoints at named fractions of the budget, each with the minimum progress that must exist by then;
- the action when a checkpoint is missed low — diagnose the blockage, widen the branch, raise concurrency, or escalate — not silent continuation.

Under-spend at a checkpoint is a defect and must be triaged like one. Common causes are a stalled dispatcher, an over-tight gate rejecting everything, a worker looping on one obstacle, an unreported access failure, or an agent that treats caution as thrift. A campaign that finishes far under budget with unexplored branches, unscreened candidates, or unread sources is incomplete, not efficient. Report residual budget together with the branches it could have bought, and state explicitly whether stopping early was a decision or a failure to advance.

## 10. Delegation contract

Every work unit contains:

- one objective;
- authoritative inputs and artifact hashes;
- permitted and prohibited actions;
- method and tool constraints;
- exact output path/schema;
- verification and acceptance tests;
- resource ceiling and deadline;
- retry limit and failure classes;
- escalation and handoff.

Delegates return artifacts and concise findings, not unbounded narrative.

The published campaign delegated through private host primitives — a `host.delegate` worker call, a `host.compute` resource path, a `submit_gate` promotion call — and read from an offline reference corpus supplied to the agent. None of those exist in a portable environment. A campaign compiled here must supply its own equivalents and name them: a written worker brief with a fixed schema in place of `host.delegate`, a declared resource governor and its refusal rules in place of `host.compute`, an explicit promotion gate with an owner and evidence in place of `submit_gate`, and a specified local reference corpus in place of the shipped one. Never render a campaign that calls a function the executing host does not have.

## 11. Durable operations

Long-running work requires a real trigger such as a queue worker, scheduled job, CI workflow, automation, or operator command. Record append-only events, atomic checkpoints, leases or dispatch tokens, heartbeats, stale-worker recovery, idempotency keys, retry policy, and restart reconciliation. A chat session is not a background service.

Long autonomy in the published campaign also depended on a host-supplied blocking wait (`wait_for_notification`) that let the orchestrator sleep until a result arrived. A portable campaign must replace it with a durable checkpoint plus a real re-entry trigger — a queue worker, scheduled job, CI run, or operator command — that reconstructs state from the ledger rather than from a live process. State which mechanism this campaign uses, or record that continuous execution is unavailable and deliver a runbook instead.

### Plan continuity and controlled amendments

Use the campaign digest as the active plan identity. At every start or resume, load that contract, the latest checkpoint, open blockers, and the next bounded work unit. Verify the required inputs before acting. Each major-gate checkpoint records the digest, completed work, evidence, gate result, deviations, remaining budget, and next action.

Classify change before continuing:

- **Operational:** retry, reorder, or substitute an equivalent tool inside frozen limits. Record it in the checkpoint; keep the current plan version.
- **Methodological:** change a method, intermediate criterion, sample, dependency, or stage design. Pause affected future work, re-freeze the plan under a new digest — in ResCamp, the `revise` mode — and rerun only affected reviewers.
- **Constitutional:** change the mission, primary evaluation or estimand, ethics or authority boundary, resource ceiling, stop rule, or permitted claim. Stop for user or institutional approval, version the plan, and re-review every affected section. When production outcomes motivated the change, preserve the prior result under its original version and label the affected inference exploratory.

Never rewrite a frozen plan or completed record in place. A pending work brief carrying an older digest is stale and must be regenerated; completed artifacts remain bound to the version that produced them.

## 12. Safety, ethics, rights, and authority

Specify human-subjects, privacy, data-rights, biosafety, field safety, legal, institutional, cultural, stakeholder, and public-communication constraints as applicable. Distinguish advice from authorized action. Require human approval for irreversible, external, regulated, sensitive, or high-impact actions.

## 13. Reporting discipline

Generate claims and summaries from canonical ledgers and artifacts. Preserve unfavorable results, alternative interpretations, deviations, and unresolved uncertainty. Distinguish observation, inference, assumption, and recommendation. Lead with the least favorable defensible interpretation.

## 14. Closeout

Validate schemas and cross-references, recompute scores or judgments from raw artifacts where possible, verify acceptance tests, disclose deviations, hash deliverables, and produce a reproducible handoff. Completion is transactional: either the required bundle passes or it remains explicitly blocked.

### Deliverable immutability

A ranked or selected deliverable means something only if nobody touched it after it was frozen. The published ranking result is interpretable because the order was fixed before submission, the items were produced exactly as delivered, and the evaluating labs saw them blinded and shuffled.

Once a shortlist, ranking, sample, coding set, or selection is frozen and hashed:

- no re-ranking, no reordering, no rescoring into the frozen order;
- no quiet substitution, addition, or removal of items, including "obvious" corrections;
- no retroactive change to the selection rule, threshold, or tie-break;
- anything selected, added, or re-scored after the freeze is reported as a separate secondary set and excluded from the primary result;
- where the evaluator is separate from the producer, deliver items blinded and in an order the evaluator controls.

This applies to a shortlist of archival cases, a set of coded excerpts, a sample of interviews, a ranked policy option list, or a citation set exactly as it does to a ranked set of designs. If the frozen deliverable is wrong, say so and rerun the selection as a new, labeled version. Do not repair it in place.

## 15. Independent challenge

An agent reviewer is not external validation. It reads the plan and can find only what the plan contains: incoherence, missing gates, unsupported claims, unverifiable steps, drift between sections. It cannot tell you whether the world agrees with the campaign. No number of agent reviewers, no separation of their contexts, and no severity of their verdicts substitutes for an external adjudicator — a measurement, a replication, a domain expert, an archive, a court, a peer reviewer, a stakeholder with their own record.

State this plainly in the rendered campaign. A plan that passes agent review is internally coherent and still unvalidated.

In the published campaign, independence was external and physical: two contract research organizations that never saw each other's data, blind labeling of each dataset, two independent human readers per trace with 96–98% agreement, off-target controls, plate positive controls, a combination rule written after both labs had reported, and a uniform post-hoc re-score run independently of the wet-lab work. That is the standard the word "independent" refers to.

### Ladder of independence

From weakest to strongest:

1. **Sequential self-critique** — same agent, same context, second pass. Catches typos and omissions. Never call it independent.
2. **Separate agent context** — fresh context, same rubric, no memory of the drafting. Catches internal incoherence.
3. **Separate agent, different rubric, blinded to conclusions** — reviews raw artifacts and recomputes rather than reading the summary. The strongest purely internal check.
4. **Human domain expert** — a person who can recognize a wrong premise the plan never questioned.
5. **External adjudicator with its own data** — measurement, replication, an independent lab or coder, an archive, a court, a regulator, peer review. Two such adjudicators that cannot see each other's results are stronger than one.

The rendered campaign must name the highest rung it actually reached, per claim class where they differ, and must not describe a lower rung in the language of a higher one. Where the reachable rung is below what the assurance profile requires, execution readiness stays blocked and the gap is written into the report.

### Practice within the internal rungs

Agent review remains useful and stays in the loop. Reviewers receive a frozen digest and an immutable rubric, and cannot edit state. One reviewer challenges methods and evidence; another challenges operations and reproducibility; high-assurance work adds ethics, safety, and claim integrity. Where practical, include a raw-artifact rescore and a reviewer blinded to conclusions. Where the design admits external checks — controls, held-out strata, a second coder, a second site, a rule fixed before results are combined — specify them here rather than deferring them to whoever executes.

## 16. Kickoff

End with a compact kickoff that identifies the frozen campaign contract, first executable gate, initial unverified backlog, resource/approval state, and required checkpoint location.
