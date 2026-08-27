# Minimum-sufficient interview

## Material intent model

Map the vague goal into only the dimensions that can change the campaign:

- starting point for an existing project: assessed status, accepted completed work, active work, inherited artifacts and decisions, deviations, recheck needs, and the next decision frontier;
- decision or purpose;
- audience and use;
- scope and exclusions;
- objects/cases/populations/corpus/constructs;
- central inquiries and rival possibilities;
- evidence admissibility and source constraints;
- method preferences or prohibitions;
- evaluation/adjudication and success criteria;
- uncertainty and acceptable failure;
- resources, access, schedule, and dependencies;
- expected pace and the checkpoints at which too little progress is itself a problem;
- what independence is reachable — agent review only, a second human, or an external adjudicator with its own evidence;
- ethics, rights, safety, privacy, and approvals;
- authority for autonomous or external actions;
- outputs, format, and handoff.

Do not turn this list into a form. Many dimensions will be inferable, safely defaultable, not applicable, or discoverable from public sources.

## Existing-project intake

Inspect supplied artifacts before asking for status. Separate inspected evidence from user-reported status and inference. Accept prior work as complete only when its artifact, provenance, and relevant acceptance basis are available; otherwise place it under `requires_recheck` rather than silently discarding or trusting it.

Plan from the current frontier. Preserve valid completed work, identify the smallest reconciliation or repair step, and omit stages that would merely repeat accepted work. Evidence observed before the new plan remains retrospective or exploratory unless it was governed by a genuinely prior protocol. Freeze evaluation rules only for future evidence and keep any new confirmatory stage separate.

## Selecting the next question

Estimate for each unresolved dimension:

`priority = decision impact × uncertainty × answer utility ÷ burden`

Ask only the highest-priority question. Favor questions that resolve several downstream dependencies without becoming compound. Ask the user about preferences, tacit constraints, undocumented project decisions, authority, private access, and irreversible tradeoffs. Research public facts and inspect supplied project facts yourself.

A question is low value when every plausible answer produces the same stage, method, evidence rule, approval boundary, or deliverable.

## Strategic defaults

Use a default only when it is:

- reversible;
- low impact;
- clearly labeled;
- compatible with known constraints;
- easy for the user to correct.

Never default consent, legal authority, data rights, sensitive-data handling, publication permission, external communication, costly purchasing, irreversible experiments, or a scientific conclusion.

Never default the reachable independence rung upward. If it is unknown whether an external adjudicator exists, ask or record it as a blocker; do not assume one and do not let agent review stand in for it.

## Contradictions and changing goals

Preserve both statements, explain the conflict, identify affected decisions, and ask a focused resolution question only when the conflict is material. A substantive change invalidates dependent decisions and frozen reviews.

## Stopping

Stop when all material dimensions are resolved, explicitly defaulted, defensibly deferred, not applicable with a reason, or recorded as blockers, and another question has low expected value. Record one stopping reason:

- `material-completeness`;
- `low-next-question-value`;
- `user-budget-reached`;
- `blocked-by-external-dependency`;
- `user-requested-draft`.

A blocker does not require endless interviewing. It requires an honest non-ready plan.

For Camp-auto and Camp-brief, target zero to three questions and stop at four unless the
user explicitly extends the brief interview. A brief may expose a material unknown instead
of resolving every full-campaign decision. Camp-full uses the assurance-profile budgets in
the main skill.

## Burden diagnostics

Flag:

- repeated questions;
- more than two interrogatives in one turn;
- questions whose answer was already supplied;
- public-fact questions that should have been researched;
- cosmetic questions before scientific/interpretive blockers;
- questions beyond the hard budget without authorization;
- failure to provide an early sketch.
