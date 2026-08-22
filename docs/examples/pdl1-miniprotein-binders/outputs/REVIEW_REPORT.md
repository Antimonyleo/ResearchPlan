# Review report

**Content digest:** `sha256:1e86dcba1b89b17fe606eae042009dc1590f18e0e4d2e8aa1cfb9de225c9a195`

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

Reviewer: `sequential-operations-r3`; attested mode: `sequential-pass`

Pass. The canary count is now consistent across G1's required evidence, S1's activities, WU-freeze's outputs and acceptance test, the APR-G1 approval record, and the kickoff backlog, which now names CAN-sequence alongside the other three. This was a counting error, not a control gap: the fourth canary existed and was enforced by the gate's own evidence requirement; the prose simply undercounted it, which would have let an executor present three manifests and believe G1 was satisfiable. Gate ownership, the manifest-before-compute rule, and the calendar-expiry rule are unaffected and remain as accepted at round 2.


