# Generalization beyond STEM

The universal campaign architecture is about disciplined inquiry and operations, not laboratory vocabulary. ResCamp distinguishes universal requirements from archetype-specific requirements.

## Universal requirements

Every campaign must define:

- purpose or decision;
- scope and boundaries;
- evidence or reasons that count;
- contrary evidence, rival accounts, counterexamples, or objections;
- method and limitations;
- an evaluation or adjudication procedure frozen before final evidence selection;
- stages, gates, resources, authority, outputs, and review;
- claim provenance and uncertainty.

## Vocabulary translation

| Experimental term | Broader equivalent |
|---|---|
| hypothesis | inquiry, interpretive claim, legal proposition, design assumption, or normative thesis |
| prediction | discriminating implication, expected pattern, counterfactual consequence, or interpretive entailment |
| control | comparator, contrast case, negative case, rival reading, precedent, baseline, or calibration material |
| metric | criterion, coding rule, adjudication principle, source-criticism rule, or acceptance test |
| falsifier | counterevidence, counterexample, objection, conflicting source, rival explanation, or scope failure |
| replication | independent coding, source recheck, alternative analysis, triangulation, reproduction, or stakeholder validation |

The validator does not require numbers, p-values, experiments, or formal falsifiability. It requires the project to say how a claim could be challenged and how evidence will be judged.

## Tested archetypes

The deterministic suite exercises experimental, computational, observational, qualitative/field, humanities/interpretive, conceptual/normative, evidence-synthesis, policy/program evaluation, design/engineering, creative-practice, and mixed-methods campaigns.

`benchmark/scenarios/public/` holds 18 cases carrying 18 distinct domain labels. Count them carefully before quoting the number:

- `protein-binder-pilot.json` is the source domain of the architecture itself. It tests that the skill still fits where it came from, not that it travels.
- Three labels sit in one adjacent area (`law and public policy`, `public policy`, `political philosophy`), so 18 labels are not 18 independent fields.
- All 18 were written by the same author as the skill. They are calibration material, not holdouts.

The defensible claim is that the architecture has been exercised on roughly a dozen and a half constructed cases spanning eleven archetypes, and that none of them is evidence about live performance.

## The load-bearing gap outside STEM

This is a structural problem, not a missing round of testing.

The paper's architecture works because 1,320 designs were physically synthesized by two contract research organizations that never saw each other's data. Sections 6 (tools and canaries), 7 (frozen evaluation instrument), 8 (staged funnel), and 15 (independent challenge) exist to feed an expensive external adjudicator standing at the end of the funnel and to keep the plan honest until it gets there. A frozen instrument matters because something outside the campaign will later disagree with it. A gate matters because promotion costs money. Independence matters because the labs could contradict the agent and did.

In an archival, interpretive, or normative campaign there may be no such adjudicator at all. No measurement will arrive to contradict a reading of a nineteenth-century port ledger. Copying the funnel without asking what sits at its end produces ceremony.

ResCamp's answer is to require a campaign to name its adjudicator, and to accept partial substitutes explicitly rather than silently:

| Function in the binder campaign | Substitutes outside STEM |
|---|---|
| external measurement that can contradict the agent | peer review, examination, adversarial collaboration, stakeholder or community validation |
| two labs blind to each other | source triangulation across independent provenance, independent coding with agreement statistics, replication of an analysis by a second party |
| instrument frozen before evidence is inspected | preregistered coding scheme, adjudication rule, or interpretive criteria; sealed holdout material |
| off-target control | negative cases, rival readings, comparison to a source the claim should *not* explain |
| a combination rule written after both labs reported | a disagreement-resolution rule written before the disagreement is known |

Where nothing substitutes, the skill should say so instead of dressing up self-review. Two cases in particular:

- **Nothing external exists.** Some conceptual, normative, and creative work has no adjudicator outside the argument itself. There the only honest instrument is explicit criteria plus recorded objections and how they were answered. Gates then govern effort, not truth.
- **Agent review is not external validation.** A reviewer agent reading a frozen version catches defects in the plan. It shares the training, the context, and often the errors of the agent it reviews. It is closer to a second draft than to a second laboratory, and ResCamp must not let a passed review be read as a validated result.

## Remaining limitation

Structural generalization is not proof of expert performance. Private holdouts and domain experts must still evaluate whether live agents ask appropriate questions and produce warranted disciplinary plans. Public fixtures are calibration material only.
