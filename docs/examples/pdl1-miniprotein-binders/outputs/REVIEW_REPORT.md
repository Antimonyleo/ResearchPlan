# Review report

**Content digest:** `sha256:2a21628f3efed539011947d8b30ace27c82d64dfeb23c4201bd12fbab767bb9e`

**Rubric digest:** `sha256:ec51920cf40375c68cedf1b95bb6dc25306b0304d242805d3f4695330e3afd06`

**Execution ready:** True

## Deterministic findings

- **WARNING review.sequential:** Standard review used sequential passes; disclose limited independence (`reviews.records`)

## Reviewer records

**Independence below is self-attested.** `mode` and `execution_evidence` are claims made
by whoever produced each record. This engine checks that the values are legal and that
records are bound to the frozen content digest; distinct reviewer identities and distinct
executors are enforced only at the high-assurance profile. It cannot observe another
process and prove a separate reviewer ran. An agent reviewer checks internal coherence
and is not external validation.

### methods-evidence — pass

Reviewer: `sequential-methods-r2`; attested mode: `sequential-pass`

Pass. All five round-1 methods findings are closed in the campaign itself rather than deferred to the artifact that was going to be written after the distributions were visible. AUROC is named as the primary separation statistic with the matched-negative-above-median fraction as its secondary; the composition-matching procedure is specified with numeric tolerances and a minimum set size; training-set contamination is now a named rival explanation with a discriminating implication, a recorded date check per control, and a post-cutoff subset that separation is recomputed on; the control-set floor is 8 with at least 3 post-cutoff, so the terminal stop rule can now fire; and the clustering metric is stated with its frozen cut and both alternatives. The residual limitation is inherent rather than a defect: 8 positives and 3 post-cutoff positives bound discrimination coarsely, and the campaign says so in its uncertainty boundary and requires the memo to report the post-cutoff figure as an upper bound where the subset is too small. In-silico separation on published binders remains a weaker guarantee than any measurement, which the reporting rules state plainly.


### operations-reproducibility — pass

Reviewer: `sequential-operations-r2`; attested mode: `sequential-pass`

Pass for beginning WU-freeze. All three round-1 operations findings are closed, and one defect the round-1 repair itself introduced has been closed with them: reassigning the gate owners left the kickoff backlog routing G1 evidence to ROLE-comp-lead and left three approval records naming the old authorities, both of which now match the gate table. No gate is owned by the role that executes its stage. A batch manifest must be appended before compute is consumed, which makes an interrupted batch visible to reconciliation and makes an output with no prior manifest a quarantine case rather than a silent adoption. The calendar now has a named owner, a check at every gate, an S3 scoping rule at G2, and an explicit no-decision outcome if the allocation lapses mid-scoring, so a partial design set can no longer reach the decision table. A fresh executor has an exact reversible first action — verify a PD-1:PD-L1 structure against RCSB and write D-target — with no missing material user decision, no spend, and no external action available to it.


