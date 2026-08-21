# Manual comparative benchmarking

Use `benchmark` only when the user asks to compare versions, models, skills, agents, or workflows. The automatic post-interview loop evaluates the current campaign but does not consume the resources required for a full benchmark.

## Claims and levels

Evaluate separately:

1. engineering correctness;
2. elicitation efficiency and fidelity;
3. campaign quality and integrity;
4. downstream research execution and externally checked outcomes.

Do not infer level 4 from a polished plan.

## Three-team protocol

- **Team U** receives the hidden brief and answers only what is asked.
- **Team S** receives the vague initial goal and tested condition.
- **Team E** receives frozen, protocol-blinded transcripts and artifacts plus a rubric. It must not edit them. Strong filesystem blinding requires a separate account, container, or remote evaluator; a same-user process is not an OS security boundary.

Use separate processes or sessions. A single sequential model run is a harness smoke test, not independent evidence.

## Matched conditions

Hold constant model, host, system instructions outside the skill, tools, network, corpus, token/time budget, retries, hardware, and scenario. Compare at least the current version with a no-skill baseline and the previous version. External tools are compared only on capabilities they claim.

## Scenario design

A scenario contains:

- vague initial request;
- hidden user facts and knowledge limits;
- material intent dimensions with importance and expected ask-by turn;
- answer map and contradiction/evolution rules;
- forbidden assumptions;
- required campaign features;
- critical defects;
- assurance profile and archetypes.

Use public cases for calibration and private holdouts for release claims. Include STEM, social science, humanities, policy, design, and mixed-methods cases.

## Elicitation metrics

Measure weighted decision recall, turn-discounted recall, material decisions per user turn, unsupported assumptions, repetitions, compound questions, low-value questions, correction effort, time to first useful sketch, question-budget compliance, stopping validity, and user-rated burden/trust.

## Campaign metrics

Score mission/scope, inquiry logic, evidence and counterevidence, methods, evaluation freeze, staged gates, tools/canaries, resources, delegation, operations/recovery, ethics/rights, claim discipline, deliverables/acceptance, proportionality, and readiness truthfulness. Critical scientific, ethical, safety, or approval defects impose hard caps.

## Execution metrics

Test interruption, duplicate dispatch, malformed artifacts, suspicious tools, budget exhaustion, absent approval, stale state, retries, and prohibited actions. Check for no duplicate irreversible action, deterministic recovery, full provenance, and no unsupported completion claim.

## Analysis

Use matched scenario differences, repeated runs, bootstrap intervals (currently a flat percentile bootstrap over pooled runs, not a scenario-clustered resample, so intervals are anticonservative when replicates within a scenario are correlated), domain/profile strata, cost and context measurements, critical-defect rates, and human adjudication of high-impact disagreements. Publish raw blinded artifacts and exact commits when permissions permit.
