# Research Campaign Prompt: Can our computational pipeline design de novo miniprotein binders to the PD-1-binding face of human PD-L1 that clear frozen…

**Status:** EXECUTION-READY

**Campaign ID:** `pdl1-miniprotein-binders`  
**Content version:** 30  
**Content digest:** `sha256:1e86dcba1b89b17fe606eae042009dc1590f18e0e4d2e8aa1cfb9de225c9a195`  
**Profile:** standard  
**Archetypes:** computational, design-engineering

## 0. Coverage and standing caveats

You are executing a compiled research campaign. Read every section before acting; section 16 is the kickoff.

**Sections left empty:** none. Empty is legitimate when the section cannot change the research decision — an archival study has no production tools — but it is never evidence of coverage.

**Challenge applied:** sequential-pass. Independence is self-attested; agent review checks internal coherence and is not external validation.
**Pilot:** not required and not recorded; this is reviewed-static plan evidence only.

Deterministic validation checked presence, cross-references, and budgets. It did not judge whether any statement here is true, sufficient, or wise.

## 1. Campaign constitution

- Freeze before you look: the target definition, software environment, and scoring thresholds are frozen with digests before any campaign design is scored. A threshold changed after designs are visible is a labelled deviation, never a silent edit.
- Provenance: every structure, weight file, container image, seed, and score table is recorded with its source, version or accession, retrieval time, and digest.
- Controls before candidates: no design is scored until the positive and negative control sets have been run through the identical pipeline and their separation recorded.
- Fail closed on authority: no worker may order genes, commit synthesis spend, contact a vendor, or begin wet-lab work. The campaign terminates at a recommendation.
- Reporting: a no-go recommendation is reported with the same completeness as a go, including the full ranked design table and every failed filter.

Every worker inherits these rules. Local briefs may narrow scope but may not weaken them.

## 2. Mission, boundaries, and deliverables

**Decision or purpose:** Produce a defensible go/no-go recommendation to the principal investigator on whether to commit gene-synthesis and wet-lab budget to a set of computationally designed de novo miniprotein binders against the PD-1-binding face of human PD-L1.

**Scope:** Computational design and in-silico evaluation only. Generate de novo miniprotein backbones against a frozen PD-L1 epitope definition, design sequences onto them, predict complexes, and score them against a control-calibrated filter stack frozen before any campaign design is inspected. Deliver a ranked design table and a decision memo.

**Non-goals**
- Ordering synthetic genes, contacting a vendor, or committing any synthesis spend
- Any wet-lab work, including expression, purification, or binding measurement
- Claiming that any design binds PD-L1 — in-silico filters predict, they do not measure
- Optimizing thresholds until designs pass
- Retraining, fine-tuning, or modifying any design or structure-prediction model

**Intended users**
- Principal investigator, who receives the recommendation and holds the synthesis budget
- Computational design team executing the stages
- A downstream wet-lab campaign, if and only if the recommendation is go

**Completion definition:** Complete when the target definition, environment, and threshold table are frozen with digests; the positive and negative control sets have been scored through the identical pipeline and their separation reported; the campaign design set has been scored once against the frozen thresholds; and a decision memo states go or no-go with the ranked table, the control separation, and the residual uncertainty behind it.

**Deliverables**

### D-target — Frozen target definition

- **Path:** deliverables/target-definition.md
- **Schema:**
  - PDB accession, chain identifiers, experimental method, and resolution, each verified against RCSB with the retrieval timestamp
  - Coordinate file digest
  - Hotspot residue set in the deposited numbering, with the numbering convention stated
  - Interface density gaps and any unmodelled residues at the interface
  - Known conformational-state caveats recorded as a threat, not resolved
  - Freeze time and artifact digest
- **Acceptance test:** The accession resolves at RCSB to a PD-1:PD-L1 complex with the recorded chains, method, and resolution; the coordinate digest matches the retrieved file; every hotspot residue exists in the deposited numbering; and the artifact carries a freeze time and digest. An accession that does not verify fails the artifact rather than being footnoted.
- **Owner:** ROLE-comp-lead
- **Immutable after freeze:** yes

### D-environment — Frozen software environment

- **Path:** deliverables/environment.md
- **Schema:**
  - Per tool: identity, release tag, weight-file digest, container image digest, licence, and licence-compatibility determination
  - Exact invocation, flags, template and MSA policy, and seed policy for each tool
  - Generation parameters: length range, topology constraints, batch size
  - Canary manifests for all four canaries with their positive, negative, and reproducibility results
  - Freeze time and artifact digest
- **Acceptance test:** Every tool the pipeline invokes appears with a digest-pinned version and a licence determination; every generation parameter S3 uses appears here; all four canary manifests are present and passing; and re-running any canary from this artifact reproduces its recorded scores exactly at the same seed.
- **Owner:** ROLE-comp-lead
- **Immutable after freeze:** yes

### D-thresholds — Control calibration and frozen decision table

- **Path:** deliverables/thresholds-and-decision-table.md
- **Schema:**
  - Exact D-target and D-environment digests consumed
  - Positive control set of at least 8 members, each with a cited experimental measurement and its assay
  - Per positive control: deposition or publication date recorded against the training cutoff of every model in the stack, and the resulting post-cutoff subset identified (at least 3 members)
  - Negative control set, separating scrambles from composition-matched unrelated-fold decoys, with the automated matching procedure, its tolerances, and its random seed recorded
  - Per-filter score distributions for both sets, and AUROC plus the fraction of matched negatives above the positive median, computed on all positives and again on the post-cutoff subset
  - Threshold value per filter, with the calibration rule that produced it
  - Clustering metric, the frozen cut, and both pre-declared alternative cuts
  - The complete decision table mapping AUROC and cluster-corrected yield to go, revise, or no-go, with the revise cell's bounded scope stated
  - Attestation that no campaign design had been generated or scored at freeze time
  - Freeze time and artifact digest
- **Acceptance test:** The positive set has at least 8 members with citable measurements and at least 3 post-cutoff; every negative is produced by the recorded matching procedure within its stated tolerances; every threshold traces to the control distributions rather than to an authored number; separation is reported by both named statistics on both subsets; the decision table is total over the AUROC-by-yield space with no undefined cells and a bounded revise cell; the attestation is present; and the artifact consumes the exact prior D-target and D-environment digests.
- **Owner:** ROLE-methods
- **Immutable after freeze:** yes

### D-designs — Ranked design table

- **Path:** deliverables/ranked-designs.csv
- **Schema:**
  - Exact D-thresholds digest consumed, with a check that it is unchanged since G2
  - One row per campaign design: identifier, sequence, backbone reference, generation batch, seed
  - Every filter column the frozen threshold table references, populated, with no nulls
  - Pass or fail per filter and overall
  - Cluster assignment at the frozen cut and at both alternative cuts
  - Per-design compute cost
- **Acceptance test:** Every design has every filter column populated; the D-thresholds digest matches G2; pass/fail is derivable mechanically from the recorded scores and the frozen thresholds; and cluster counts are reported at all three cuts. Designs scoring below the negative control distribution appear in the table rather than being dropped.
- **Owner:** ROLE-comp-lead
- **Immutable after freeze:** yes

### D-memo — Go/no-go decision memo

- **Path:** deliverables/decision-memo.md
- **Schema:**
  - First paragraph: the cell reached on the frozen decision table and the two values that placed it
  - Control separation reported as a distribution comparison with its overlap
  - Contamination-adjusted separation on the post-cutoff positive subset, stated next to the all-positives figure
  - Cluster-corrected yield at all three cuts
  - Proximity to adjacent decision cells
  - Residual uncertainty and the least favourable defensible interpretation
  - Any numbered deviations and what they invalidate
  - Any principal-investigator override, recorded as an override with its reason
  - Consumed artifact digests for D-target, D-environment, D-thresholds, and D-designs
- **Acceptance test:** The stated recommendation equals the cell mechanically reached on the frozen table; the memo leads with the cell rather than with narrative; no sentence states or implies that any design binds PD-L1; and a no-go memo carries the same completeness as a go, including the full ranked table.
- **Owner:** ROLE-methods
- **Immutable after freeze:** no

## 3. Object and evidence dossier

**Objects, cases, corpus, population, or system**

### OBJ-target — The PD-1-binding face of the human PD-L1 (CD274) IgV domain, defined by hotspot residues read from a deposited PD-1:PD-L1 co-crystal structure.

- **Description:** The PD-1-binding face of the human PD-L1 (CD274) IgV domain, defined by hotspot residues read from a deposited PD-1:PD-L1 co-crystal structure.
- **Current state:** Not yet pinned. D-target is the first frozen artifact and the S1 gate blocks on it.
- **Boundary:** The epitope is defined by an explicit residue set on a named chain of a named accession, recorded in D-target. The plan does not assert an accession: the exact PDB id, chain, resolution, and residue numbering are pinned in D-target and verified against RCSB at freeze time. A design targeting any other surface is out of scope.

### OBJ-designs — De novo miniprotein binders, single chain, generated against OBJ-target.

- **Description:** De novo miniprotein binders, single chain, generated against OBJ-target.
- **Current state:** None generated.
- **Boundary:** Length range and backbone topology are fixed in D-environment before generation. Designs are computational objects only; no physical material exists at any point in this campaign.

### OBJ-controls — A positive control set of published, experimentally validated PD-L1 binders and a negative control set of sequence-scrambled and unrelated-fold decoys.

- **Description:** A positive control set of published, experimentally validated PD-L1 binders and a negative control set of sequence-scrambled and unrelated-fold decoys.
- **Current state:** Not yet selected.
- **Boundary:** Controls are selected and frozen in D-thresholds before any campaign design is generated. Positive controls must have published binding measurements; negatives must have no reported PD-L1 affinity. Set membership is never revised after freeze.

**Context**

### CTX-decision

- **Why it changes the design:** The PI will not release synthesis budget on a ranked list alone; the recommendation must state how well the filter stack separated known binders from known non-binders, because that is the only in-silico evidence that the ranking means anything.

### CTX-allocation

- **Why it changes the design:** The GPU allocation expires at quarter end and does not roll over. Under-spending it while design branches remain unexplored is an incomplete campaign, not a saving.

**Source hierarchy**

### SRC-structure

- **Tier:** Tier 1 — deposited experimental structures from the PDB, with accession, chain, method, and resolution recorded.
- **Admissibility:** Admissible for defining the epitope and for structural superposition. Resolution and any missing density at the interface must be recorded in D-target.
- **Known limitations:** A co-crystal captures one conformational state. Interface plasticity and crystallographic artefacts are not visible in a single structure.

### SRC-literature

- **Tier:** Tier 1 — peer-reviewed publications reporting experimental PD-L1 binding measurements, used to select positive controls.
- **Admissibility:** Admissible for control-set membership only. Each positive control must cite a specific reported measurement with its assay and conditions.
- **Known limitations:** Reported affinities differ by assay format and are not directly comparable across papers. Publication bias against non-binders is why the negative set is constructed, not collected.

### SRC-predictions

- **Tier:** Tier 3 — model outputs from structure prediction, sequence design, and energy scoring.
- **Admissibility:** Admissible as ranking and filtering evidence only. Never admissible as evidence that a design binds.
- **Known limitations:** Structure-prediction confidence correlates with, but does not establish, binding. Filter stacks of this class are known to pass designs that fail experimentally; the campaign's entire purpose is to decide whether the separation is good enough to pay to find out.

**Access and rights**

### ACC-compute

- **Rights:** 2,000 A100 GPU-hours on the existing institutional cluster allocation.
- **Approval:** Already granted under the standing group allocation; no further approval required.
- **Expiry:** End of the current quarter.

### ACC-models

- **Rights:** Design, sequence-design, structure-prediction, and energy-scoring software used under their published licences.
- **Approval:** Licence terms recorded per tool in D-environment; any tool whose licence forbids the intended use is excluded at S1 rather than used and disclosed later.
- **Expiry:** None.

### ACC-synthesis

- **Rights:** None. No gene-synthesis account, vendor relationship, or purchasing authority exists under this campaign.
- **Approval:** Not sought. Ordering is a prohibited action, not a pending approval.
- **Expiry:** Not applicable.

**Known alternatives**

### ALT-antibody

- **Existing evidence:** Clinically validated anti-PD-L1 antibodies exist. The miniprotein route is chosen for size, stability, and expression cost, not because antibodies fail. The decision memo must state that a negative result rejects this pipeline for this target, not the target itself.
- **Status:** Known alternative approach: an anti-PD-L1 antibody or antibody fragment rather than a de novo miniprotein.

### ALT-existing-binder

- **Existing evidence:** Published binders exist and serve as positive controls here. If campaign designs do not score above the positive control set under the frozen thresholds, that is itself decision-relevant and must be reported.
- **Status:** Known alternative: adapt a published de novo PD-L1 binder rather than generate new backbones.

## 4. Inquiry and evidence logic

Each inquiry must be evaluated against admissible support and explicit counterevidence, rival explanations/readings, counterexamples, or objections.

### INQ-separation — Under the frozen filter stack, do published PD-L1 binders separate from scrambled and unrelated-fold decoys well enough for the ranking to carry decision weight?

- **Why it matters:** This is the gating question of the campaign. If the stack cannot separate known binders from known non-binders, every score it assigns to a campaign design is uninterpretable and no amount of favourable-looking design scores can rescue it.
- **Admissible support:**
  - Score distributions for the frozen positive and negative control sets, computed through the identical pipeline, with the overlap between distributions reported and the per-filter contribution broken out.
- **Counterevidence, rival explanation, reading, or objection:**
  - Apparent separation driven by a confound rather than by binding: positive controls sharing a fold, a length range, or an amino-acid composition with each other and not with the negatives.
  - The rival explanation is that the stack is detecting 'looks like a designed protein', not 'binds this epitope'.
  - Training-set contamination: published binders are frequently deposited structures, and deposited structures are frequently in a structure-prediction model's training data. Their interface confidence would then be partly memorization, inflating separation in a way that does not transfer to novel designs — which is exactly the transfer the go decision assumes.
- **Discriminating prediction or interpretive implication:** If separation is real, negatives matched to the positives on length and composition still score below them. If it is a composition artefact, matched negatives score alongside the positives and the apparent separation collapses. If contamination is driving the result, positives deposited after every model's training cutoff separate materially worse than the contaminated subset; if it is not, the two subsets separate alike.
- **Verification or adjudication:** Separation is judged against the composition-matched negative subset by AUROC, not against scrambles and not by threshold pass rate. It is computed on all positives and again on the post-cutoff subset, and both are reported. Judged once, on the frozen thresholds, before any campaign design is scored.
- **Uncertainty and external-validity boundary:** A control set of 8 bounds discrimination coarsely, and the post-cutoff subset of 3 or more bounds it more coarsely still. The memo reports separation as an interval, states which subset each figure came from, and states that in-silico separation on published binders is a weaker guarantee than any experimental measurement.
- **Reporting rule:** Report the full distribution comparison and its overlap. Failure to separate is reported as a terminal result, never as a calibration step.

### INQ-yield — Does the design pipeline produce enough distinct designs clearing the frozen thresholds to make a synthesis order worth placing?

- **Why it matters:** A synthesis order has a fixed overhead cost. One passing design is not worth an order; a set of structurally diverse passing designs is. This question sets the go side of the recommendation.
- **Admissible support:**
  - Count of campaign designs clearing every frozen threshold, after clustering to remove near-duplicates, with the diversity of the passing set reported as structural and sequence distance.
- **Counterevidence, rival explanation, reading, or objection:**
  - A passing set that is one design and its near-copies.
  - Cluster count, not raw pass count, is the decision-relevant quantity; a rival reading of a large pass count is that the pipeline converged on a single solution and the redundancy is an artefact of sampling.
- **Discriminating prediction or interpretive implication:** If yield is real, passing designs occupy multiple sequence and structural clusters. If it is convergence, they collapse to one cluster under the pre-declared distance cut.
- **Verification or adjudication:** Counted after single-linkage clustering at 60 percent global sequence identity and 2.0 Angstrom interface backbone RMSD, declared before generation, with the 50 and 70 percent alternatives reported alongside. Raw pass counts are recorded but are not the criterion.
- **Uncertainty and external-validity boundary:** Cluster counts depend on the distance cut. The memo reports yield at the frozen cut and at two pre-declared alternatives so the reader can see the sensitivity.
- **Reporting rule:** Report cluster count, cluster occupancy, and the raw count separately. Never report the raw count alone.

### INQ-spend — Given the observed separation and yield, is committing gene-synthesis and wet-lab budget the right decision?

- **Why it matters:** This is the deliverable question. Separation and yield are inputs to it; neither answers it alone, and the campaign exists to make the trade-off explicit rather than leaving it to a glance at a ranked list.
- **Admissible support:**
  - The frozen decision table mapping observed separation and cluster-corrected yield to go, revise, or no-go, applied once, with the memo stating which cell was reached.
- **Counterevidence, rival explanation, reading, or objection:**
  - The rival reading is that a marginal result should be resolved by more computation rather than by spending.
  - The decision table must therefore contain a revise cell with an explicit bounded scope, so 'run more designs' is a declared outcome rather than an improvised escape from a no-go.
- **Discriminating prediction or interpretive implication:** A genuine go lands in the go cell on the frozen table without argument. A result requiring narrative to reach go is by construction a revise or a no-go.
- **Verification or adjudication:** The decision table is frozen in D-thresholds before any campaign design is scored, and is applied exactly once. Reaching a cell is mechanical; the memo may add context but may not move the cell.
- **Uncertainty and external-validity boundary:** The table converts two uncertain quantities into a discrete recommendation and therefore hides the uncertainty at the boundaries. The memo reports how close the result sits to an adjacent cell.
- **Reporting rule:** State the cell reached and the values that placed it there in the first paragraph of the memo, before any discussion.

## 5. Method portfolio

### M-target — Epitope definition from a deposited co-crystal structure

- **Purpose:** Convert 'the PD-1-binding face' from a phrase into an explicit, checkable residue set on a named structure, so that every later stage targets the same surface.
- **Answers inquiries:**
  - INQ-separation
  - INQ-yield
- **Inputs:**
  - A deposited PD-1:PD-L1 co-crystal structure retrieved from the PDB, with its accession, chain identifiers, method, resolution, and any missing interface density recorded.
- **Outputs:**
  - D-target: the accession and chain, the hotspot residue set in the deposited numbering, the coordinate file digest, the retrieval timestamp, and a note on interface density gaps.
- **Assumptions:**
  - That a single deposited state adequately represents the surface a binder must engage.
- **Limitations:**
  - One crystal form captures one conformation.
  - Interface plasticity, alternate rotamers, and crystallographic contacts are invisible here and are recorded as a threat rather than resolved.
- **Cost:** Negligible compute; roughly one working day.
- **Dependencies:** None. This is the first artifact and everything else consumes its digest.
- **Decision it can change:** Yes. A poorly chosen or wrongly numbered epitope invalidates every subsequent design and score, and the error would be invisible downstream because the pipeline would run happily against the wrong surface.

### M-controls — Control-calibrated threshold freezing

- **Purpose:** Set the filter thresholds from the separation between known binders and known non-binders, before any campaign design exists, so the thresholds cannot be tuned to the designs.
- **Answers inquiries:**
  - INQ-separation
- **Inputs:**
  - A positive control set of published, experimentally validated PD-L1 binders with cited measurements, and a negative control set containing both scrambles and composition-matched decoys of unrelated fold.
- **Outputs:**
  - D-thresholds: the control sets, their score distributions, the per-filter threshold values, the clustering distance cut, the decision table, and the digest of all of it.
- **Assumptions:**
  - That published binders are informative about the pipeline's ability to recognise binders it did not generate.
- **Limitations:**
  - Positive controls are few and were not produced by this pipeline; they may be easier or harder to score than campaign designs.
  - Published affinities come from heterogeneous assays.
  - This is why separation is reported as a distribution with overlap, not as an accuracy figure.
- **Cost:** Roughly 300 A100 GPU-hours.
- **Dependencies:** M-target, and both canaries passing.
- **Decision it can change:** Yes, and it is the only method that can end the campaign on its own. Failure to separate is a terminal no-go.

### M-generate — Backbone generation and fixed-backbone sequence design

- **Purpose:** Produce a diverse set of candidate de novo miniproteins directed at the frozen epitope.
- **Answers inquiries:**
  - INQ-yield
- **Inputs:**
  - D-target, the frozen environment in D-environment, and the generation parameters declared before generation begins.
- **Outputs:**
  - Backbone coordinates, designed sequences, and a generation manifest recording parameters, seeds, and cost per batch.
- **Assumptions:**
  - That the declared length range and topology constraints admit a solution for this epitope.
- **Limitations:**
  - Generative sampling is unbounded in principle and bounded in practice by allocation.
  - Absence of passing designs is evidence about this pipeline under this budget, never about the target's designability.
- **Cost:** Roughly 1,200 A100 GPU-hours, the campaign's largest line.
- **Dependencies:** M-target, M-controls frozen, canaries passed.
- **Decision it can change:** Yes. Yield after clustering is one of the two inputs to the decision table.

### M-score — Frozen-threshold scoring and clustering

- **Purpose:** Score every campaign design through the identical pipeline the controls passed through, apply the frozen thresholds once, and cluster the survivors.
- **Answers inquiries:**
  - INQ-yield
  - INQ-spend
- **Inputs:**
  - Designed sequences and backbones, D-thresholds, D-environment.
- **Outputs:**
  - The ranked design table with every filter column populated, the pass/fail per filter, cluster assignments at the frozen cut and at two pre-declared alternative cuts, and per-design provenance.
- **Assumptions:**
  - That the scoring pipeline is deterministic given a seed, as the canaries verify.
- **Limitations:**
  - The filter stack predicts; it does not measure.
  - Designs that clear it may fail experimentally, which is precisely the risk the recommendation is about.
- **Cost:** Roughly 400 A100 GPU-hours.
- **Dependencies:** M-generate, M-controls.
- **Decision it can change:** Yes. This produces the numbers the decision table consumes.

### M-decide — Mechanical application of the frozen decision table

- **Purpose:** Convert observed separation and cluster-corrected yield into a go, revise, or no-go recommendation without post-hoc judgement.
- **Answers inquiries:**
  - INQ-spend
- **Inputs:**
  - The control calibration table, the ranked design table, and the frozen decision table.
- **Outputs:**
  - D-memo: the cell reached, the two values that placed it, proximity to adjacent cells, the residual uncertainty, and the recommendation.
- **Assumptions:**
  - That the table's cells were drawn sensibly before the results were visible.
- **Limitations:**
  - A discrete table hides uncertainty at its boundaries; the memo reports proximity explicitly.
  - The PI may override, and an override is recorded as an override.
- **Cost:** Negligible compute; roughly two working days of writing.
- **Dependencies:** M-score, M-controls.
- **Decision it can change:** It is the decision.

## 6. Tools and production-like canaries

**Tools**

### TOOL-backbone

- **Identity and version:** Generative backbone design model. Exact model identity, release tag, weight-file digest, and container image digest are pinned in D-environment at S1; the plan deliberately names no version because an unpinned version string is worse than an explicit requirement to pin one.
- **Production use:** Used at production scale in S3 only after its canary passes at S1.
- **Purpose:** Generate de novo miniprotein backbones against the frozen epitope definition in D-target.
- **Access:** Institutional cluster, existing allocation.
- **License or rights:** Recorded per tool in D-environment. A tool whose licence forbids the intended use is excluded at S1.
- **Authoritative documentation:** Model card, published method paper, and the exact invocation recorded in D-environment.

### TOOL-sequence

- **Identity and version:** Fixed-backbone sequence design model, pinned identically in D-environment.
- **Production use:** S3 only, after canary.
- **Purpose:** Design amino-acid sequences onto generated backbones.
- **Access:** Institutional cluster, existing allocation.
- **License or rights:** Recorded in D-environment.
- **Authoritative documentation:** Model card and invocation recorded in D-environment.

### TOOL-predict

- **Identity and version:** Structure-prediction model used to predict the design-target complex, pinned with weights and any template or MSA settings in D-environment.
- **Production use:** S2 for controls and S3 for campaign designs, identical settings in both.
- **Purpose:** Predict the complex and produce the interface confidence measures the filter stack consumes.
- **Access:** Institutional cluster, existing allocation.
- **License or rights:** Recorded in D-environment.
- **Authoritative documentation:** Settings, template policy, and random seeds recorded per run.

### TOOL-energy

- **Identity and version:** Physics-based interface energy and biophysical-liability scoring package, pinned by version and commit in D-environment.
- **Production use:** S2 and S3, identical protocol in both.
- **Purpose:** Compute interface energy and biophysical liability terms used by the filter stack.
- **Access:** Institutional cluster, existing allocation.
- **License or rights:** Recorded in D-environment; academic licence terms checked at S1.
- **Authoritative documentation:** Protocol script and flags recorded in D-environment.

**Canaries**

A successful import or help command is not a canary.

### CAN-predict — Re-predict the deposited PD-1:PD-L1 complex named in D-target from sequence, using the exact production settings, container image, and seed policy that S2 and S3 will use.

- **Tool:** TOOL-predict
- **Expected artifacts and schema:**
  - Predicted complex coordinates, per-residue confidence, interface confidence measures, and a run manifest carrying the image digest, seed, and wall-clock cost.
- **Positive, negative, and sanity cases:**
  - Positive: the predicted complex recovers the deposited interface within a pre-declared coordinate deviation.
  - Negative: predicting the same target against a scrambled partner sequence yields interface confidence in the low-confidence regime.
  - Sanity: two runs at the same seed produce identical scores, and two runs at different seeds produce scores within a pre-declared spread.
- **Downstream acceptance:** The filter stack must ingest the run manifest and score the canary output end to end, producing the same numbers when re-run from the stored artifacts. A canary whose output the scorer cannot ingest fails the gate.
- **Quarantine triggers:** If the canary fails at any point, S3 does not start. Any campaign design already scored under a failed canary is quarantined and rescored after the fix; the deviation is recorded.

### CAN-energy — Score the deposited PD-1:PD-L1 interface and a deliberately disrupted variant of it through the exact production protocol.

- **Tool:** TOOL-energy
- **Expected artifacts and schema:**
  - Interface energy terms, biophysical liability terms, and a manifest with package version, commit, flags, and cost.
- **Positive, negative, and sanity cases:**
  - Positive: the native interface scores favourably.
  - Negative: the disrupted interface scores materially worse in the expected direction.
  - Sanity: rerunning the identical input reproduces the identical terms.
- **Downstream acceptance:** Terms must land in the score table under the exact column names the frozen threshold table references. A renamed or missing column fails the gate rather than silently dropping a filter.
- **Quarantine triggers:** Failure blocks S3. Scores produced under a failed canary are quarantined and recomputed.

### CAN-pipeline — Run a single miniature end-to-end pass — backbone generation, sequence design, prediction, scoring — on a handful of designs against the frozen target, at production settings, before any scale-up.

- **Tool:** TOOL-backbone
- **Expected artifacts and schema:**
  - A complete score table row for each design, with every column the frozen threshold table references populated and no nulls.
- **Positive, negative, and sanity cases:**
  - Positive: rows are complete and within physically plausible ranges.
  - Negative: a deliberately malformed backbone is rejected by the pipeline rather than producing a plausible-looking row.
  - Sanity: the miniature pass reproduces exactly when re-run from its manifest.
- **Downstream acceptance:** The decision table must be computable from the miniature output without manual editing. If the decision table cannot be applied mechanically to the canary output, the gate fails.
- **Quarantine triggers:** Failure blocks S3 scale-up and consumes no further allocation until fixed.

### CAN-sequence — Redesign sequences onto the backbone of the deposited PD-L1 binding partner named in D-target, at exact production settings, container image, and seed policy, then predict and score the redesigned complex through the same downstream stack S3 will use.

- **Tool:** TOOL-sequence
- **Expected artifacts and schema:**
  - Designed sequences with per-position confidence and the exact invocation recorded.
  - A run manifest carrying the model identity, weight digest, container image digest, seed, and wall-clock cost.
  - Downstream prediction and score rows for each redesigned sequence, populated in the columns the frozen threshold table references.
- **Positive, negative, and sanity cases:**
  - Positive: redesigned sequences recover the native fold in prediction within a pre-declared coordinate deviation, and recover a pre-declared fraction of the native interface residue identities.
  - Negative: sequence design run against a deliberately masked or absent target context yields interface confidence in the low-confidence regime rather than confident nonsense.
  - Sanity: two runs at the same seed produce identical sequences, and two runs at different seeds produce sequences within a pre-declared identity spread.
- **Downstream acceptance:** The redesigned sequences must flow end to end into the scorer and produce complete score rows under the exact column names the frozen threshold table references, reproducing when re-run from the stored manifest.
- **Quarantine triggers:** Failure blocks S3. Any sequence produced under a failed canary is quarantined and redesigned after the fix, with the deviation recorded.

## 7. Frozen evaluation or adjudication instrument

**Frozen before production (asserted, not verified):** The complete evaluation instrument — filter stack, per-filter thresholds, the named separation statistics, the composition-matching rule and its tolerances, the clustering metric and its three cuts, and the decision table mapping AUROC and cluster-corrected yield to go, revise, or no-go — is frozen in D-thresholds with a digest at G2, before any campaign design has been generated or scored. The statistics and matching rule are named in this campaign rather than left to D-thresholds' author, so they cannot be chosen after the control distributions are visible. D-thresholds carries an explicit attestation, and G3 re-checks the digest before accepting any design score.

**Criteria**
- Control separation, primary statistic: the area under the ROC curve for the combined filter rank, positive controls against composition-matched negative controls. Declared here, before S2, so it cannot be selected after the distributions are visible.
- Control separation, secondary statistic: the fraction of composition-matched negatives scoring above the positive-set median. Reported alongside AUROC because AUROC alone hides the shape of the overlap.
- Contamination-adjusted separation: both statistics recomputed on the subset of positive controls deposited after every model's training cutoff. Where that subset is too small to estimate, the all-positives figure is reported as an upper bound and labelled as one.
- Cluster-corrected yield: the number of distinct clusters among campaign designs clearing every frozen threshold. A cluster is a single-linkage group at 60 percent global sequence identity and 2.0 Angstrom interface backbone RMSD; the two pre-declared alternative cuts are 50 and 70 percent identity at the same RMSD.
- Provenance completeness: every scored design traceable to a seed, a batch manifest appended before compute was consumed, and the frozen artifact digests it consumed.
- Threshold integrity: the D-thresholds digest unchanged between G2 and G3.

**Comparators, controls, cases, or adjudication rules**
- Positive control set: published, experimentally validated PD-L1 binders, each citing a specific reported measurement and its assay. Minimum set size is 8; fewer is a terminal no-go.
- Contamination subset: of those 8, at least 3 must have been deposited or published after the training cutoff of every model in the stack, and each control's deposition date is recorded against each cutoff in D-thresholds.
- Negative control set, sequence scrambles: the coarse comparator, sufficient only to detect a stack that scores everything alike.
- Negative control set, composition-matched decoys of unrelated fold: the operative comparator. Matching is automated and declared before any control is scored — length within 10 percent of the paired positive, amino-acid composition within a Euclidean distance of 0.15 over the 20-dimensional frequency vector, and predicted helix/sheet content within 15 percentage points. The set is at least three times the size of the positive set.
- Campaign designs are scored through the identical pipeline as both control sets; a settings difference between control and design scoring invalidates the comparison and is a deviation.
- The frozen decision table then maps AUROC and cluster-corrected yield onto go, revise, or no-go.

**Missing-evidence policy:** A design missing any filter column is failed, not imputed and not dropped from the table. A control whose published measurement cannot be cited to a specific assay is excluded from the positive set before freeze and recorded as excluded. A filter that cannot be computed for the control sets is removed from the stack before freeze rather than applied only to campaign designs.

**Exploration versus confirmation:** S1 and S2 are exploratory with respect to method choice: filters may be added, removed, or reparameterized freely until D-thresholds is frozen at G2. From G2 onward the campaign is confirmatory: the filter stack, thresholds, clustering cuts, and decision table are fixed, and S3 produces a single scoring pass. Any post-G2 change is a numbered deviation that downgrades D-memo to exploratory.

**Stop, pivot, and no-go rules**
- Terminal no-go: positive and composition-matched negative controls fail to separate at G2 by the AUROC threshold frozen in D-thresholds. The campaign stops, the memo is written from the control calibration alone, and no design generation is funded. Retuning to manufacture separation is prohibited.
- Terminal no-go: fewer than 8 positive controls with citable experimental measurements can be assembled, or fewer than 3 of them post-date every model's training cutoff.
- Stop and escalate: a canary fails four times at G1.
- Revise, not go: a result landing in the decision table's revise cell triggers exactly the bounded additional work that cell names, and nothing beyond it.
- No-decision, not no-go: if the compute allocation lapses before the campaign design set is completely scored, D-memo records no-decision and states what fraction was scored. A partially scored set is never run through the decision table.
- Deviation downgrade: any change to a frozen artifact after its gate downgrades D-memo to exploratory and is stated in the memo's first paragraph.

## 8. Staged funnel and promotion gates

**Stages**

### S1 — Freeze the target and the environment

- **Purpose:** Pin what is being designed against and what is doing the designing, before anything is generated or scored.
- **Inputs:** Public structural data; installed software.
- **Activities:**
  - Retrieve and verify a PD-1:PD-L1 co-crystal structure against RCSB; record accession, chain, method, resolution, interface density gaps, and file digest
  - Define the hotspot residue set in the deposited numbering and record it in D-target
  - Pin every tool identity, version, weight-file digest, container image digest, and licence in D-environment
  - Run all four canaries (CAN-predict, CAN-energy, CAN-pipeline, CAN-sequence) at production settings and record their manifests
- **Outputs:**
  - D-target and D-environment, both frozen with digests; four canary manifests.
- **Owner:** ROLE-comp-lead
- **Budget:** 50 A100 GPU-hours; approximately one week.
- **Expected pace:** One week. If S1 is not frozen within two weeks, escalate to ROLE-pi rather than proceeding on an unpinned environment.
- **Promotion gate:** G1

### S2 — Calibrate on controls and freeze the thresholds

- **Purpose:** Establish whether the filter stack can tell known binders from known non-binders, and fix the thresholds and decision table before any campaign design exists.
- **Prerequisites:**
  - S1
- **Inputs:** D-target, D-environment, published binder literature.
- **Activities:**
  - Select the positive control set from published, experimentally measured PD-L1 binders, citing each measurement and its assay
  - Construct the negative set with both scrambles and composition-matched unrelated-fold decoys
  - Score both sets end to end through the production pipeline
  - Record the score distributions and their overlap, broken out per filter
  - Fix the threshold values, the clustering distance cut, the two alternative cuts, and the decision table, and freeze D-thresholds with a digest
  - Record each positive control's deposition or publication date against every model's training cutoff and identify the post-cutoff subset
  - Check cumulative elapsed calendar against the allocation expiry and scope the S3 design count to what the remaining allocation and calendar can complete
- **Outputs:**
  - D-thresholds, frozen with a digest, containing the control sets, distributions, thresholds, cuts, and decision table.
- **Owner:** ROLE-methods
- **Budget:** 300 A100 GPU-hours; approximately two weeks.
- **Expected pace:** Two weeks. Under-spend here is not a saving: an under-powered control set weakens every downstream claim.
- **Promotion gate:** G2

### S3 — Generate and score the campaign design set

- **Purpose:** Produce candidate designs and score them once against the frozen thresholds.
- **Prerequisites:**
  - S2
- **Inputs:** D-target, D-environment, D-thresholds.
- **Activities:**
  - Generate backbones against the frozen epitope in batches, recording parameters, seeds, and cost per batch
  - Design sequences onto the backbones
  - Predict complexes and compute interface and liability terms at the identical settings the controls used
  - Apply the frozen thresholds once and record pass/fail per filter per design
  - Cluster survivors at the frozen cut and at both pre-declared alternatives
- **Outputs:**
  - The ranked design table with full provenance, cluster assignments at three cuts, and a stage cost record.
- **Owner:** ROLE-comp-lead
- **Budget:** 1,600 A100 GPU-hours; approximately four weeks.
- **Expected pace:** Four weeks, with a mid-stage checkpoint at 800 GPU-hours. Reaching the checkpoint with the allocation largely unspent and design branches unexplored is an incomplete stage, and is escalated rather than declared efficient.
- **Promotion gate:** G3

### S4 — Decide and hand off

- **Purpose:** Apply the frozen decision table once and deliver the recommendation.
- **Prerequisites:**
  - S3
- **Inputs:** Control calibration table, ranked design table, frozen decision table.
- **Activities:**
  - Read the cell reached from the frozen decision table
  - Record proximity to adjacent cells and the residual uncertainty
  - Write D-memo leading with the least favourable defensible interpretation
  - Package all frozen artifacts and their digests for handoff
- **Outputs:**
  - D-memo and the complete frozen artifact set with digests.
- **Owner:** ROLE-methods
- **Budget:** 0 GPU-hours; approximately one week of writing.
- **Expected pace:** One week.
- **Promotion gate:** G4

**Gates**

### G1

- **Stage:** S1
- **Required evidence:**
  - D-target carrying a verified accession, chain, hotspot residue set, and file digest.
  - D-environment carrying every tool version, weight digest, image digest, and licence.
  - All four canary manifests showing their positive, negative, and reproducibility checks passed, and the scorer ingesting canary output end to end.
- **Owner:** ROLE-methods
- **On failure:** S2 does not start and no allocation beyond the S1 budget is consumed. A failed canary is fixed and rerun; a structure that cannot be verified against RCSB sends the epitope definition back for reselection.
- **Criteria:**
  - The target and environment are frozen and the pipeline demonstrably works end to end at production settings.

### G2

- **Stage:** S2
- **Required evidence:**
  - D-thresholds frozen with a digest, containing both control sets, their per-filter distributions, the overlap against composition-matched negatives, the threshold values, the three clustering cuts, and the complete decision table.
  - The post-cutoff positive subset with at least 3 members and its separately computed separation figures.
  - A cumulative calendar check against the allocation expiry date, with the S3 design count scoped to what the remaining allocation and calendar can complete.
- **Owner:** ROLE-comp-lead
- **On failure:** Failure to separate is a terminal no-go. The campaign stops at S2, D-memo is written from the control calibration alone, and no design generation is funded. Retuning thresholds to manufacture separation is prohibited.
- **Criteria:**
  - Thresholds and the decision table are frozen, and the control sets separate against the composition-matched negatives.

### G3

- **Stage:** S3
- **Required evidence:**
  - The ranked design table with every threshold column populated and no nulls, cluster assignments at all three cuts, per-design seeds and manifests, the stage cost record, and a digest check showing D-thresholds unchanged since G2.
  - A reconciliation report showing every batch manifest was appended before its compute was consumed, and that no batch consumed compute without a prior manifest.
- **Owner:** ROLE-methods
- **On failure:** If D-thresholds changed after G2, every affected score is quarantined and rescored under the frozen table, and the change is recorded as a numbered deviation that downgrades the memo to exploratory. If the mid-stage checkpoint shows large under-spend with unexplored branches, escalate to ROLE-pi.
- **Criteria:**
  - The campaign design set has been scored exactly once against the frozen thresholds, with complete provenance and no post-hoc threshold change.

### G4

- **Stage:** S4
- **Required evidence:**
  - D-memo stating the cell and the two values that placed it in its first paragraph, proximity to adjacent cells, residual uncertainty, and the least favourable defensible reading.
  - The complete frozen artifact set with digests, reproducing from stored manifests.
- **Owner:** ROLE-pi
- **On failure:** A memo whose recommendation does not match the table cell is returned. A PI override is permitted but is recorded as an override with its reason, and never presented as the table's output.
- **Criteria:**
  - The recommendation is the cell mechanically reached on the frozen decision table, and the handoff package is complete and reproducible.

## 9. Resources and fail-closed dispatch

**Budgets**
- Total compute: 2,000 A100 GPU-hours on the existing institutional allocation, expiring at quarter end.
- S1: 50 GPU-hours. S2: 300 GPU-hours. S3: 1,600 GPU-hours with a checkpoint at 800. S4: 0 GPU-hours.
- Cash: USD 0. The campaign authorizes no expenditure of any kind.
- Budget floor: reaching S3's mid-stage checkpoint with substantially unspent allocation and unexplored design branches is an incomplete stage and is escalated to ROLE-pi, not reported as efficiency.
- Calendar: approximately twelve weeks, bounded by the quarter-end allocation expiry.
- Calendar ceiling: work-unit calendar ceilings sum to twelve weeks against a hard quarter-end allocation expiry, leaving no slack. ROLE-methods records cumulative elapsed calendar against the expiry date at every gate.
- Expiry rule: at G2, the S3 design count is scoped to what the remaining allocation and remaining calendar can complete. If the allocation lapses before the design set is completely scored, the campaign reports no-decision rather than running the decision table on a partial set.

**Access constraints**
- Compute: existing institutional cluster allocation, already approved, no further authorization needed.
- Data: public structural data and published literature only. No proprietary, personal, or restricted data is used.
- Software: used under published licences, with each licence determination recorded in D-environment at S1.
- Synthesis and wet-lab: no access exists and none is sought. This is a prohibited action, not a pending approval.

**Concurrency:** Design batches within S3 may run concurrently up to the cluster allocation. Stages are strictly sequential: the freeze discipline depends on S2 completing before S3 begins, so no part of S3 overlaps S2 even when idle capacity exists.

**Dispatch rules**
- A work unit dispatches only when every work unit in its dependency_ids has been accepted at its gate. WU-freeze has no dependencies; WU-calibrate waits on WU-freeze; WU-generate on WU-calibrate; WU-decide on WU-generate.
- Dispatch is fail-closed: a work unit whose authoritative inputs are not present at their recorded digests does not start, and the condition is escalated rather than worked around.
- No work unit may exceed its resource_ceiling. Reaching the ceiling escalates to ROLE-pi; it does not silently continue.
- The stage owner is the single source of truth for stage status. A worker's self-report is evidence, not acceptance.
- External actions are prohibited campaign-wide. There is no dispatch path to a vendor, a purchase, or a wet-lab action.
- A batch manifest is appended to the event log before any compute is consumed. A batch that consumed compute without a prior manifest is a reconciliation error: the batch is quarantined and rerun, and the gap is recorded.

**Approvals**
- **APR-compute:** Standing institutional GPU allocation, already granted; recorded in ACC-compute.
- **APR-G1:** G1 acceptance: target and environment frozen, all four canaries passing.
- **APR-G2:** G2 acceptance: thresholds, clustering cuts, and decision table frozen; controls separate.
- **APR-G3:** G3 acceptance: design set scored once against unchanged thresholds, with full provenance.
- **APR-G4:** G4 acceptance: memo matches the table cell and the handoff package reproduces.
- **APR-deviation:** Approval of a numbered post-freeze deviation, which downgrades D-memo to exploratory.

## 10. Delegation

**Roles**

### ROLE-pi — Principal investigator

- **Description:** Holds the synthesis budget and receives the recommendation.
- **Responsibility:** Accepts G4. Decides whether to act on the recommendation.
- **Authority:** Sole authority to accept the recommendation, to override the decision table on the record, and to authorize any subsequent wet-lab campaign.
- **Limits:** Does not score designs, set thresholds, or edit any frozen artifact. An override is recorded as an override.

### ROLE-comp-lead — Computational design lead

- **Description:** Runs generation, prediction, and scoring.
- **Responsibility:** Owns S1 and S3 and maintains provenance and cost records. Accepts G2, a gate on a stage it does not execute.
- **Authority:** Allocates GPU-hours within the stage budgets; declares canary pass or fail.
- **Limits:** Cannot alter D-thresholds after G2, cannot order synthesis, cannot contact a vendor, and owns no gate on a stage it executes: G1 and G3 are accepted by ROLE-methods, and ROLE-comp-lead accepts G2, which it does not execute.

### ROLE-methods — Methods and calibration lead

- **Description:** Owns control selection, threshold calibration, and the decision table.
- **Responsibility:** Owns S2 and S4, and accepts G1 and G3 on stages it does not execute.
- **Authority:** Fixes the threshold values, clustering cuts, and decision table before freeze.
- **Limits:** May not change thresholds, cuts, or the decision table after G2 except by a numbered deviation approved by ROLE-pi, which downgrades the memo to exploratory. Does not accept G2, the gate on its own stage.

### ROLE-reviewer — Independent reviewer

- **Description:** Reviews the frozen campaign against its own rules.
- **Responsibility:** Reviews the plan and, at each gate, whether the required evidence is genuinely present.
- **Authority:** Records findings and verdicts.
- **Limits:** Never edits canonical state, never sets thresholds, and never approves a gate.

### ROLE-worker — Delegated stage worker

- **Description:** Executes a bounded brief within one stage.
- **Responsibility:** Produces the exact outputs named in its brief with full provenance.
- **Authority:** Only what its brief names.
- **Limits:** Inherits the constitution verbatim. No external action, no spend, no threshold change, no gate approval.

**Bounded work units**

Delegates return artifacts and concise findings, not unbounded narrative. A local brief may narrow scope but may not weaken the constitution.

### WU-freeze — Produce D-target and D-environment, frozen with digests, and pass all four canaries at production settings.

- **Authoritative inputs and hashes:**
  - The campaign constitution; the RCSB Protein Data Bank; the installed software stack and its licences.
- **Permitted actions:**
  - Retrieve public structural data and verify it against RCSB
  - Install, pin, and digest software, weights, and container images
  - Run the four canaries at production settings
  - Write D-target and D-environment
- **Prohibited actions:**
  - Generating any campaign design
  - Scoring anything other than the canary inputs
  - Setting or implying any filter threshold
  - Ordering synthesis, contacting a vendor, or committing any spend
  - Proceeding on an unverified accession or an unpinned tool version
- **Method and tool constraints:** M-target only. Canaries run at exactly the settings S2 and S3 will use; a canary run at reduced settings does not count.
- **Exact outputs:**
  - D-target, D-environment, and four canary manifests.
- **Verification and acceptance:** G1's required evidence is present in full: verified accession and digests, every tool pinned with a licence determination, and three passing canary manifests whose output the scorer ingests end to end.
- **Resource ceiling:** 50 A100 GPU-hours and two calendar weeks.
- **Retry and failure classes:** A failed canary may be fixed and rerun without escalation up to three times; the fourth failure escalates to ROLE-pi.
- **Escalation and handoff:** Escalate to ROLE-pi if no PD-1:PD-L1 structure verifies with adequate interface density, if a required tool's licence forbids the intended use, or if the two-week ceiling is reached.

### WU-calibrate — Select and freeze the control sets, score them, and freeze the threshold values, clustering cuts, and decision table before any campaign design exists.

- **Authoritative inputs and hashes:**
  - The constitution; frozen D-target and D-environment with their exact digests; peer-reviewed literature reporting experimental PD-L1 binding measurements.
- **Permitted actions:**
  - Select positive controls from published experimentally measured binders, citing each measurement and assay
  - Construct scramble and composition-matched negative controls
  - Score both control sets end to end at production settings
  - Fix thresholds, the three clustering cuts, and the decision table, and freeze D-thresholds
  - Record each positive control's deposition date against every model's training cutoff and compute separation on the post-cutoff subset
  - Scope the S3 design count to the remaining allocation and calendar
- **Prohibited actions:**
  - Generating or scoring any campaign design before D-thresholds is frozen
  - Authoring a threshold value that does not trace to the control distributions
  - Leaving any cell of the decision table undefined
  - Revising control-set membership after freeze
  - Ordering synthesis or committing any spend
  - Assembling fewer than 8 positive controls, or fewer than 3 post-cutoff, and proceeding anyway
  - Constructing composition-matched negatives by hand or outside the recorded automated procedure and its tolerances
- **Method and tool constraints:** M-controls only, at the exact settings recorded in D-environment.
- **Exact outputs:**
  - D-thresholds, frozen with a digest.
- **Verification and acceptance:** G2's required evidence is present: both control sets, per-filter distributions, overlap against the composition-matched subset, thresholds traceable to the distributions, three cuts, a total decision table with a bounded revise cell, and the no-designs-yet attestation.
- **Resource ceiling:** 300 A100 GPU-hours and three calendar weeks.
- **Retry and failure classes:** Scoring may be rerun on infrastructure failure. Control-set membership is selected once; reselection after seeing distributions is prohibited and is an escalation, not a retry.
- **Escalation and handoff:** Escalate to ROLE-pi if fewer than the pre-declared minimum number of positive controls can be found with citable measurements, or if the sets do not separate — the latter is a terminal no-go, not a retry.
- **Depends on work units:**
  - WU-freeze

### WU-generate — Generate and score the campaign design set once against the frozen thresholds, with complete provenance.

- **Authoritative inputs and hashes:**
  - The constitution; frozen D-target, D-environment, and D-thresholds with their exact digests.
- **Permitted actions:**
  - Generate backbones and design sequences within the frozen parameters
  - Predict complexes and compute interface and liability terms at the frozen settings
  - Apply the frozen thresholds once and record pass/fail per filter
  - Cluster survivors at all three declared cuts
  - Record seeds, manifests, and per-design cost
- **Prohibited actions:**
  - Changing any value in D-thresholds
  - Rescoring a design under different thresholds to improve its rank
  - Dropping designs that score below the negative control distribution
  - Reporting raw pass count without cluster count
  - Ordering synthesis, contacting a vendor, or committing any spend
  - Consuming compute for a batch whose manifest has not already been appended to the event log
- **Method and tool constraints:** M-generate and M-score, at exactly the settings the controls were scored under. A settings difference between control scoring and design scoring invalidates the comparison and is a deviation.
- **Exact outputs:**
  - D-designs: the ranked design table with cluster assignments at three cuts and full provenance.
- **Verification and acceptance:** G3's required evidence is present: all filter columns populated with no nulls, the D-thresholds digest unchanged since G2, cluster counts at three cuts, per-design seeds and manifests, and the stage cost record.
- **Resource ceiling:** 1,600 A100 GPU-hours and five calendar weeks.
- **Retry and failure classes:** Batches may be regenerated on infrastructure failure with the failure recorded. Scoring is applied once per design; a design is never rescored to obtain a better result.
- **Escalation and handoff:** Escalate to ROLE-pi at the 800 GPU-hour checkpoint if spend is far below pace with design branches unexplored, or if the allocation will expire before the stage completes.
- **Depends on work units:**
  - WU-calibrate

### WU-decide — Apply the frozen decision table once and write D-memo.

- **Authoritative inputs and hashes:**
  - The constitution; frozen D-thresholds and D-designs with their exact digests; the control calibration table.
- **Permitted actions:**
  - Read the cell reached from the frozen decision table
  - Compute proximity to adjacent cells
  - Write the memo leading with the cell and the least favourable defensible reading
  - Package all frozen artifacts and digests for handoff
- **Prohibited actions:**
  - Stating a recommendation other than the cell mechanically reached
  - Stating or implying that any design binds PD-L1
  - Omitting the ranked table or the control calibration from a no-go memo
  - Presenting a principal-investigator override as the table's output
  - Ordering synthesis or authorizing wet-lab work
  - Running the decision table on a partially scored design set; an incomplete set yields a no-decision memo
- **Method and tool constraints:** M-decide only. The table is applied exactly once.
- **Exact outputs:**
  - D-memo and the complete frozen artifact package.
- **Verification and acceptance:** G4's required evidence is present: the memo's recommendation equals the table cell, the cell and its two values appear in the first paragraph, proximity and residual uncertainty are stated, and the package reproduces from stored manifests.
- **Resource ceiling:** 0 GPU-hours and two calendar weeks.
- **Retry and failure classes:** A memo returned at G4 is rewritten. The table cell is not recomputed.
- **Escalation and handoff:** Escalate to ROLE-pi if the memo's author believes the table cell is wrong — as an override request on the record, never as a rewritten recommendation.
- **Depends on work units:**
  - WU-generate

## 11. Durable operations and recovery

**Continuous runtime enabled:** True

**Continuation trigger:** Work resumes from the campaign state directory and the append-only event log, never from chat history. A new session reads the last accepted gate and the frozen artifact digests, and starts the first work unit whose dependencies are accepted and whose outputs are absent.

**State store:** The campaign state directory holds canonical state; the deliverables directory holds frozen artifacts, each carrying its own digest. Frozen artifacts are the durable record; a session's working notes are not.

**Event log:** Append-only. Every artifact freeze, canary run, scoring batch, gate decision, deviation, and escalation is appended with its timestamp, actor, inputs consumed by digest, and cost. Events are never edited or removed.

**Checkpoint policy:** Checkpoint at every artifact freeze, at each gate decision, and after each S3 scoring batch. The batch manifest — parameters, seed, and the frozen digests it consumes — is appended to the event log before the batch consumes any compute, so an interrupted batch is always visible to reconciliation. A checkpoint records the manifest and cumulative cost so an interrupted stage resumes at batch granularity rather than restarting.

**Liveness:** A stage worker records a heartbeat with each batch. A stage with no batch event for more than one working day is treated as stalled and escalated to its stage owner. A chat session ending is not stage completion.

**Recovery:** On interruption, reconcile the event log against artifacts actually on disk. Because every manifest is appended before its compute runs, a batch with a manifest and no complete score row is an interrupted batch and is rerun from its recorded seed. A batch whose outputs exist with no prior manifest cannot have arisen from a compliant run: it is quarantined, not adopted. Artifacts present but not recorded as frozen are quarantined pending a digest check.

**Idempotency:** Every batch is keyed by its generation parameters and seed. Rerunning a completed batch reproduces its score rows and appends no duplicate event. Scoring is applied once per design; a rerun that would change a recorded score is a deviation, not a retry.

A conversational session is not a scheduler.

**Plan continuity and amendments**

Use `campaign.json` at `sha256:1e86dcba1b89b17fe606eae042009dc1590f18e0e4d2e8aa1cfb9de225c9a195` as the active contract. At every start or resume, load that contract, the latest checkpoint, open blockers, and the next bounded work unit; verify required inputs before acting.

Record material deviations at the next gate. If execution reveals a material plan change, pause affected future work and re-freeze the plan under a new digest before continuing — in ResCamp, the `revise` mode. Never rewrite a frozen plan in place: a pending brief carrying an older digest is stale, while completed artifacts remain bound to the version that produced them.

## 12. Ethics, safety, rights, and external actions

**Constraints**
- No human subjects, no personal data, no clinical material, and no animal work at any point.
- All structural data and literature used are public. No proprietary or restricted data enters the campaign.
- Software is used within its licence; a licence forbidding the intended use excludes the tool at S1 rather than being disclosed after the fact.
- PD-L1 is a human immuno-oncology target and the designs are candidate binders to a therapeutic target. The campaign produces sequences and scores only; it produces no physical material and authorizes no synthesis.
- No design sequence is transmitted to any external vendor, service, or synthesis provider under this campaign.
- Claim discipline is a safety constraint here, not only a reporting one: an in-silico score presented as evidence of binding could cause the PI to commit spend on a false premise.
- No external action is permitted under this campaign: ordering genes, contacting a synthesis vendor, transmitting any design sequence outside the institution, and initiating wet-lab work are prohibited for every role, including ROLE-pi acting under this campaign.
- Retrieving public structural data and published literature is read-only use of public resources and is not an external action in this sense.

**External actions**
- None recorded

**Human approval points**
- **HAP-freeze:** Freezing thresholds and the decision table at G2, after which the campaign is confirmatory.
- **HAP-accept:** Accepting the recommendation at G4.
- **HAP-deviation:** Approving any post-freeze deviation to a frozen artifact.
- **HAP-wetlab:** Authorizing a separate wet-lab campaign. This campaign authorizes it under no outcome.

## 13. Reporting and claim discipline

**Claim rules**
- Never state or imply that a design binds PD-L1. Permitted form: the design cleared the frozen in-silico filter stack at rank N.
- Every ranking claim cites the frozen threshold table digest it was scored against.
- Control separation is reported as a distribution comparison with its overlap, never as a single summary number.

**Negative/null/failed result policy:** A no-go recommendation is a complete deliverable, not a failure to deliver. The decision memo, ranked design table, control calibration table, and every filter a design failed are retained and reported identically to a go outcome. Designs scoring below the negative control distribution are reported, not dropped.

**Deviation policy:** Any change to the frozen target definition, environment, control sets, or threshold table after freeze is recorded as a numbered deviation carrying the reason, the digest before and after, the approver, and an explicit statement of which conclusions it invalidates. A deviation made after campaign designs were scored downgrades the memo's recommendation to exploratory.

Lead with the least favorable defensible interpretation.

**Recorded claims**

### CLM-separation — The frozen filter stack separates published PD-L1 binders from composition-matched decoys by a margin recorded in the control calibration table.

- **Inquiry:** INQ-separation
- **Support:**
  - Control score distributions from D-controls, computed through the identical pipeline used for campaign designs.
- **Counterevidence and objections:**
  - Composition or fold confounding; small positive-control set; published binders being unrepresentative of what this pipeline generates; assay heterogeneity across the papers supplying the positives.
- **Verification:** Compared against the composition-matched negative subset and reported as a distribution overlap, not a threshold pass rate.
- **Status:** unevaluated
- **Uncertainty:** Bounded by control-set size and by the fact that in-silico separation on known binders does not establish prospective accuracy on novel designs.
- **Reporting rule:** Reported whether the margin is large, small, or absent. An absent margin is the campaign's terminal result.

### CLM-recommendation — The recommendation delivered to the principal investigator is the cell reached on the frozen decision table, together with the evidence that placed it there.

- **Inquiry:** INQ-spend
- **Support:**
  - The frozen decision table in D-thresholds, the control calibration table, and the cluster-corrected yield from the ranked design table.
- **Counterevidence and objections:**
  - That a mechanical table oversimplifies a judgement the PI should make holistically.
  - The table's purpose is to prevent the judgement from being made after seeing which designs look attractive, not to remove the PI's authority; the PI may override it and the memo records the override as such.
- **Verification:** The cell is derived mechanically from two recorded numbers and is reproducible from the frozen table and the score files.
- **Status:** unevaluated
- **Uncertainty:** The table is a pre-commitment made under uncertainty about what the score distributions would look like; the memo reports proximity to adjacent cells.
- **Reporting rule:** The memo states the cell first and any narrative second. A PI override is recorded as an override with its reason, never folded into the recommendation.

## 14. Transactional closeout

Validate schemas and references, recompute judgments from raw artifacts where possible, verify every acceptance test below, disclose deviations and blockers, hash deliverables, and produce a reproducible handoff. Completion is fail-closed.

Once a ranked or selected deliverable is frozen there is no post-hoc re-ranking, re-selection, or quiet substitution; anything selected after close is reported separately and excluded from the primary result.

**Acceptance tests that must pass**

### D-target — Frozen target definition

- **Path:** deliverables/target-definition.md
- **Schema:**
  - PDB accession, chain identifiers, experimental method, and resolution, each verified against RCSB with the retrieval timestamp
  - Coordinate file digest
  - Hotspot residue set in the deposited numbering, with the numbering convention stated
  - Interface density gaps and any unmodelled residues at the interface
  - Known conformational-state caveats recorded as a threat, not resolved
  - Freeze time and artifact digest
- **Acceptance test:** The accession resolves at RCSB to a PD-1:PD-L1 complex with the recorded chains, method, and resolution; the coordinate digest matches the retrieved file; every hotspot residue exists in the deposited numbering; and the artifact carries a freeze time and digest. An accession that does not verify fails the artifact rather than being footnoted.
- **Owner:** ROLE-comp-lead
- **Immutable after freeze:** yes

### D-environment — Frozen software environment

- **Path:** deliverables/environment.md
- **Schema:**
  - Per tool: identity, release tag, weight-file digest, container image digest, licence, and licence-compatibility determination
  - Exact invocation, flags, template and MSA policy, and seed policy for each tool
  - Generation parameters: length range, topology constraints, batch size
  - Canary manifests for all four canaries with their positive, negative, and reproducibility results
  - Freeze time and artifact digest
- **Acceptance test:** Every tool the pipeline invokes appears with a digest-pinned version and a licence determination; every generation parameter S3 uses appears here; all four canary manifests are present and passing; and re-running any canary from this artifact reproduces its recorded scores exactly at the same seed.
- **Owner:** ROLE-comp-lead
- **Immutable after freeze:** yes

### D-thresholds — Control calibration and frozen decision table

- **Path:** deliverables/thresholds-and-decision-table.md
- **Schema:**
  - Exact D-target and D-environment digests consumed
  - Positive control set of at least 8 members, each with a cited experimental measurement and its assay
  - Per positive control: deposition or publication date recorded against the training cutoff of every model in the stack, and the resulting post-cutoff subset identified (at least 3 members)
  - Negative control set, separating scrambles from composition-matched unrelated-fold decoys, with the automated matching procedure, its tolerances, and its random seed recorded
  - Per-filter score distributions for both sets, and AUROC plus the fraction of matched negatives above the positive median, computed on all positives and again on the post-cutoff subset
  - Threshold value per filter, with the calibration rule that produced it
  - Clustering metric, the frozen cut, and both pre-declared alternative cuts
  - The complete decision table mapping AUROC and cluster-corrected yield to go, revise, or no-go, with the revise cell's bounded scope stated
  - Attestation that no campaign design had been generated or scored at freeze time
  - Freeze time and artifact digest
- **Acceptance test:** The positive set has at least 8 members with citable measurements and at least 3 post-cutoff; every negative is produced by the recorded matching procedure within its stated tolerances; every threshold traces to the control distributions rather than to an authored number; separation is reported by both named statistics on both subsets; the decision table is total over the AUROC-by-yield space with no undefined cells and a bounded revise cell; the attestation is present; and the artifact consumes the exact prior D-target and D-environment digests.
- **Owner:** ROLE-methods
- **Immutable after freeze:** yes

### D-designs — Ranked design table

- **Path:** deliverables/ranked-designs.csv
- **Schema:**
  - Exact D-thresholds digest consumed, with a check that it is unchanged since G2
  - One row per campaign design: identifier, sequence, backbone reference, generation batch, seed
  - Every filter column the frozen threshold table references, populated, with no nulls
  - Pass or fail per filter and overall
  - Cluster assignment at the frozen cut and at both alternative cuts
  - Per-design compute cost
- **Acceptance test:** Every design has every filter column populated; the D-thresholds digest matches G2; pass/fail is derivable mechanically from the recorded scores and the frozen thresholds; and cluster counts are reported at all three cuts. Designs scoring below the negative control distribution appear in the table rather than being dropped.
- **Owner:** ROLE-comp-lead
- **Immutable after freeze:** yes

### D-memo — Go/no-go decision memo

- **Path:** deliverables/decision-memo.md
- **Schema:**
  - First paragraph: the cell reached on the frozen decision table and the two values that placed it
  - Control separation reported as a distribution comparison with its overlap
  - Contamination-adjusted separation on the post-cutoff positive subset, stated next to the all-positives figure
  - Cluster-corrected yield at all three cuts
  - Proximity to adjacent decision cells
  - Residual uncertainty and the least favourable defensible interpretation
  - Any numbered deviations and what they invalidate
  - Any principal-investigator override, recorded as an override with its reason
  - Consumed artifact digests for D-target, D-environment, D-thresholds, and D-designs
- **Acceptance test:** The stated recommendation equals the cell mechanically reached on the frozen table; the memo leads with the cell rather than with narrative; no sentence states or implies that any design binds PD-L1; and a no-go memo carries the same completeness as a go, including the full ranked table.
- **Owner:** ROLE-methods
- **Immutable after freeze:** no

## 15. Independent challenge

Reviewers are read-only and bound to the frozen content and rubric digests.

**Weakest independence rung among required reviews:** 1 — sequential self-critique (no independence)

The weakest rung bounds the challenge, not the strongest: one sequential pass in the set means the set is only as independent as that pass.

Rungs: 1 sequential self-critique < 2 separate agent context < 3 separate agent blinded to conclusions < 4 human domain expert < 5 external adjudicator with its own data. Rungs 1–3 are agent review: they check internal coherence and are **not** external validation. The mode is self-attested — recorded for audit, never proven.

- **methods-evidence:** pass — Pass. All five round-1 methods findings are closed in the campaign itself rather than deferred to the artifact that was going to be written after the distributions were visible. AUROC is named as the primary separation statistic with the matched-negative-above-median fraction as its secondary; the composition-matching procedure is specified with numeric tolerances and a minimum set size; training-set contamination is now a named rival explanation with a discriminating implication, a recorded date check per control, and a post-cutoff subset that separation is recomputed on; the control-set floor is 8 with at least 3 post-cutoff, so the terminal stop rule can now fire; and the clustering metric is stated with its frozen cut and both alternatives. The residual limitation is inherent rather than a defect: 8 positives and 3 post-cutoff positives bound discrimination coarsely, and the campaign says so in its uncertainty boundary and requires the memo to report the post-cutoff figure as an upper bound where the subset is too small. In-silico separation on published binders remains a weaker guarantee than any measurement, which the reporting rules state plainly. (mode: sequential-pass, reviewer: sequential-methods-r2)
- **operations-reproducibility:** pass — Pass. The canary count is now consistent across G1's required evidence, S1's activities, WU-freeze's outputs and acceptance test, the APR-G1 approval record, and the kickoff backlog, which now names CAN-sequence alongside the other three. This was a counting error, not a control gap: the fourth canary existed and was enforced by the gate's own evidence requirement; the prose simply undercounted it, which would have let an executor present three manifests and believe G1 was satisfiable. Gate ownership, the manifest-before-compute rule, and the calendar-expiry rule are unaffected and remain as accepted at round 2. (mode: sequential-pass, reviewer: sequential-operations-r3)

## 16. Kickoff

**Command:** Begin WU-freeze. Read the campaign constitution and D-target's schema, then retrieve and verify a PD-1:PD-L1 co-crystal structure against RCSB, recording accession, chains, method, resolution, interface density gaps, and the coordinate file digest. Do not generate any design, do not score anything other than canary inputs, and do not set or imply any filter threshold. Stop at G1.

**First gate:** G1

**Initially unverified backlog**
- Verify a PD-1:PD-L1 co-crystal structure against RCSB and record its accession, chains, method, resolution, and file digest
- Define the hotspot residue set in the deposited numbering and write D-target
- Pin every tool identity, version, weight digest, image digest, and licence into D-environment
- Run CAN-predict, CAN-energy, CAN-pipeline, and CAN-sequence at production settings and record their manifests
- Confirm the scorer ingests canary output end to end, then present G1 evidence to ROLE-methods, which accepts G1 on a stage it does not execute
