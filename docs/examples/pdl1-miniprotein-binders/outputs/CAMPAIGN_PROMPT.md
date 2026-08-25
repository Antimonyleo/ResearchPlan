# Research Campaign Prompt: Can our computational pipeline design de novo miniprotein binders to the PD-1-binding face of human PD-L1 that clear frozen…

**Status:** EXECUTION-READY

**Campaign ID:** `pdl1-miniprotein-binders`

**Content version:** 284

**Content digest:** `sha256:cec061c58fca6136d0d70765c7c307fa82692a7020455fdb2ce8691f7230bb2d`

**Profile:** standard

**Archetypes:** computational, design-engineering

## 0. Coverage and standing caveats

You are executing a compiled research campaign. Read every section before acting; section 16 is the kickoff.

**Sections left empty:** none. Empty is legitimate when the section cannot change the research decision — an archival study has no production tools — but it is never evidence of coverage.

**Challenge applied:** independent-subagent. Independence is self-attested; agent review checks internal coherence and is not external validation.
**Pilot:** not required and not recorded; this is reviewed-static plan evidence only.

Deterministic validation checked presence, cross-references, and budgets. It did not judge whether any statement here is true, sufficient, or wise.

## 1. Campaign constitution

- Freeze before you look: the target definition, software environment, and scoring thresholds are frozen with digests before any campaign design is scored. A threshold changed after designs are visible is a labelled deviation, never a silent edit.
- Provenance: every structure, weight file, container image, seed, score table, and runtime record is recorded with its source, version or accession, retrieval time, and digest. Artifact digests are SHA-256 over the exact stored bytes; digests are written to the detached UTF-8 `artifacts/MANIFEST.sha256`, never embedded in the bytes they identify.
- Controls before candidates: no design is scored until the positive and negative control sets have been run through the identical pipeline and their separation recorded.
- Fail closed on authority: no worker may order genes, commit synthesis spend, contact a vendor, or begin wet-lab work. The campaign terminates at a recommendation.
- Reporting: a no-go recommendation is reported with the same completeness as a go, including the full ranked design table and every failed filter.

Every worker inherits these rules. Local briefs may narrow scope but may not weaken them.

## 2. Starting point, mission, boundaries, and deliverables

**Entry mode:** New project — no prior project state was supplied.

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
  - Freeze time and detached SHA-256 entry in `artifacts/MANIFEST.sha256`
- **Acceptance test:** The accession resolves at RCSB to a PD-1:PD-L1 complex with the recorded chains, method, and resolution; the coordinate digest matches the retrieved file; every hotspot residue exists in the deposited numbering; and the artifact carries a freeze time and digest. An accession that does not verify fails the artifact rather than being footnoted.
- **Owner:** ROLE-comp-lead
- **Immutable after freeze:** yes

### D-environment — Frozen software environment

- **Path:** deliverables/environment.md
- **Schema:**
  - Per tool: identity, release tag, weight-file digest, container image digest, licence, and licence-compatibility determination
  - Exact invocation, flags, template and MSA policy, and seed policy for each tool
  - Generation parameters: length range, topology constraints, batch size
  - APR-compute approval identifier and evidence, allocation scope, available A100 GPU-hours, exact expiry timestamp with timezone, and record retrieval time
  - Canary manifests for all four G1 canaries with positive, negative, raw-schema, and reproducibility results; fixtures are labelled non-campaign and threshold-independent
  - Freeze time and detached SHA-256 entry in `artifacts/MANIFEST.sha256`
- **Acceptance test:** Every tool appears with a pinned version and licence determination; APR-compute scope/hours/expiry are recorded; all four G1 canaries validate deterministic production-setting raw outputs against versioned schemas independent of D-thresholds; and each reproduces from its manifest.
- **Owner:** ROLE-comp-lead
- **Immutable after freeze:** yes

### D-thresholds — Control calibration and frozen decision table

- **Path:** deliverables/thresholds-and-decision-table.md
- **Schema:**
  - Exact D-target and D-environment digests consumed
  - At least 8 positive controls with cited assays spanning at least 6 independent scaffold groups; every production-model cutoff recorded; at least 5 cutoff-clean groups identified
  - Frozen connected-component grouping evidence and, for each group, the earliest public date across every linked sequence, structure, design lineage, and parent scaffold plus its cutoff-clean classification
  - Frozen leave-one-scaffold-group-out membership linking each group to topology-matched hard negatives, with provenance and evidential class
  - Pre-score filter candidates, within-fold tuning rule, combination rule, matching procedure, tolerances, and random seed
  - Per-group held-out predictions plus pooled all-group and post-cutoff-group AUROC and hard-negative-above-median statistics
  - Fixed-seed 10,000-resample independent-group bootstrap intervals and the post-cutoff one-sided 90 percent lower bound
  - Final filter thresholds fitted on all controls only after group-held-out evaluation passes
  - Clustering metric and the 50, 60, and 70 percent identity cuts
  - A total decision table using the cutoff-clean-group lower bound and cluster-corrected yield, including bounded revise cells and all sample/provenance minimums
  - Attestations that grouping and folds preceded control scoring and final thresholds preceded campaign-design generation or scoring
  - Freeze time and detached SHA-256 entry in `artifacts/MANIFEST.sha256`
- **Acceptance test:** Every control has citable provenance and a frozen scaffold group; no related group crosses folds; every group records its earliest linked public sequence/structure/lineage/scaffold date and cutoff-clean classification; every hard negative has recorded provenance; held-out statistics reproduce; at least 8 positives span 6 groups and go requires 5 cutoff-clean groups with defensible hard negatives; final thresholds were fitted only after held-out evaluation; the decision table has no undefined cell; all digests are present.
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
  - References to the corresponding authorized, started, and terminal events in D-runtime
  - Freeze time and detached SHA-256 entry in `artifacts/MANIFEST.sha256`
- **Acceptance test:** Every design has every filter column populated; the D-thresholds digest matches G2; pass/fail is derivable mechanically from recorded scores and frozen thresholds; cluster counts are reported at all three cuts; D-runtime reconciles every batch; and D-designs has a detached manifest entry. Designs below the negative-control distribution remain in the table.
- **Owner:** ROLE-comp-lead
- **Immutable after freeze:** yes

### D-memo — Go/no-go decision memo

- **Path:** deliverables/decision-memo.md
- **Schema:**
  - First paragraph: the cell reached on the frozen decision table and the two values that placed it
  - Control separation reported as a distribution comparison with its overlap
  - Contamination-adjusted separation on the post-cutoff independent-group subset, stated next to the all-group figure
  - Cluster-corrected yield at all three cuts
  - Proximity to adjacent decision cells
  - Residual uncertainty and the least favourable defensible interpretation
  - Any numbered deviations and what they invalidate
  - Any principal-investigator override, recorded as an override with its reason
  - Consumed artifact digests for D-target, D-environment, D-thresholds, D-designs, and the immutable D-runtime G3 reconciliation snapshot
  - Version identifier, predecessor memo digest if any, acceptance time, and detached SHA-256 entry; the G4 event names this digest before the runtime stream is finalized
- **Acceptance test:** The accepted immutable memo version states the cell mechanically reached on the frozen table; leads with the cell; never implies that a design binds PD-L1; includes the full ranked table even for no-go; and is referenced by path and detached SHA-256 digest in the accepting G4 event. Corrections create new versions and retain the accepted predecessor.
- **Owner:** ROLE-methods
- **Immutable after freeze:** yes

### D-runtime — Runtime event log and reconciliation

- **Path:** artifacts/runtime/events.ndjson; deliverables/runtime-g3-reconciliation.md; deliverables/runtime-final-reconciliation.md
- **Schema:**
  - Live UTF-8 JSON Lines event stream at `artifacts/runtime/events.ndjson` using rescamp-runtime-event-v1
  - Each event records sequence, unique event_id, event_type, batch_id when applicable, status, timezone-aware timestamp, actor, frozen input digests, terminal output digests, cumulative cost, and predecessor event_id
  - Single-dispatcher exclusive append rule and one complete atomic line per transition
  - For every batch: authorization before compute, optional heartbeats, and exactly one completed or failed terminal event
  - Immutable G3 reconciliation snapshot recording highest sequence, exact byte length, SHA-256 of the event-log prefix through G3, batch accounting, and its own detached digest; the live stream remains appendable only for S4/G4
  - Final G4 reconciliation after the acceptance event, covering the complete event-log digest and proving no later append; detached SHA-256 entries for the final log and both reconciliation artifacts
- **Acceptance test:** At G3, an immutable reconciliation snapshot validates the log prefix and accounts for every S3 batch while the D-runtime stream remains open only for S4/G4. At G4, the acceptance event names D-memo's digest, final reconciliation validates the complete stream, and D-runtime freezes permanently with detached digests for the final log and both snapshots.
- **Owner:** ROLE-comp-lead
- **Immutable after freeze:** yes

### D-canary-compat — Frozen threshold-to-canary compatibility record

- **Path:** deliverables/canary-compatibility.md
- **Schema:**
  - Exact D-thresholds digest consumed after D-thresholds was frozen
  - Exact digests of every stored raw CAN-pipeline, CAN-energy, CAN-sequence, and CAN-predict fixture
  - For CAN-pipeline, CAN-energy, and CAN-sequence: every table-derived field, value, and pass/fail result produced mechanically without manual edits
  - For CAN-predict: field-to-table compatibility result and any table field not applicable to its raw schema
  - Execution time, tool identity, and attestation that D-thresholds remained byte-identical during the checks
  - Freeze time and detached SHA-256 entry in artifacts/MANIFEST.sha256
- **Acceptance test:** The artifact binds the frozen D-thresholds digest and all raw-fixture digests; every required table field resolves; mechanical applications reproduce; no source fixture or D-thresholds changes during testing; and the detached digest verifies. Any incompatibility blocks G2 without modifying D-thresholds.
- **Owner:** ROLE-methods
- **Immutable after freeze:** yes

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
  - Predeclared leave-one-scaffold-group-out predictions for positives and topology-matched hard-negative strata, with group provenance, all-group and post-cutoff-group AUROC, fixed-seed interval estimates, and per-filter diagnostics.
- **Counterevidence, rival explanation, reading, or objection:**
  - Apparent separation driven by a confound rather than by binding: positive controls sharing a sequence family, design lineage, scaffold, or topology that the negatives do not share.
  - The rival explanation is that the stack is detecting a familiar scaffold or 'looks like a designed protein', not 'binds this epitope'.
  - Training-set contamination: published binders are frequently deposited structures, and deposited structures are frequently in a structure-prediction model's training data. Their interface confidence would then be partly memorization, inflating separation in a way that does not transfer to novel designs.
- **Discriminating prediction or interpretive implication:** If separation is binding-relevant, an entirely held-out positive scaffold group still outranks topology-matched hard negatives. If it is scaffold recognition, performance collapses when related sequences, structures, and design lineages are kept in one group. If contamination is driving the result, cutoff-clean groups — whose earliest linked public sequence, structure, lineage, or parent scaffold post-dates every production-model cutoff — separate materially worse than the older groups.
- **Verification or adjudication:** Use only pooled held-out scaffold-group predictions. Freeze each group's earliest public date across every linked sequence, structure, design lineage, and parent scaffold; the group is cutoff-clean only if that date is later than every production model's training cutoff. The decision table consumes the one-sided 90 percent lower confidence bound for at least 5 cutoff-clean groups with defensible topology-matched hard negatives. All-group AUROC is descriptive only.
- **Uncertainty and external-validity boundary:** Eight positives spanning six independent scaffold groups provide only coarse discrimination evidence, and five cutoff-clean groups remain imprecise. A mixed-age group is classified by its earliest linked public precursor, never its newest binder. Report fixed-seed group-bootstrap intervals, disclose hard-negative limitations, and state that held-out in-silico discrimination does not establish wet-lab binding.
- **Reporting rule:** Report group-level held-out results, pooled point estimates, intervals, and all-group versus post-cutoff-group disagreement. Failure of the post-cutoff-group lower bound, independent-group minimum, or hard-negative requirement is a revise or terminal no-go, never a calibration opportunity.

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
- **Verification or adjudication:** Freeze the decision table in D-thresholds before campaign designs are generated. Apply it once using the one-sided 90 percent lower bound of post-cutoff out-of-fold AUROC and cluster-corrected yield. All-positive AUROC is descriptive only. The memo may add context but cannot move the mechanically reached cell.
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

- **Purpose:** Estimate discrimination from held-out scaffold-group predictions without sequence, structure, design-lineage, or tuning leakage, then fit and freeze the final stack on all controls before any campaign design is generated or scored.
- **Answers inquiries:**
  - INQ-separation
- **Inputs:**
  - At least 8 published, experimentally validated PD-L1 binders spanning at least 6 frozen sequence/structure scaffold groups; at least 5 groups must be cutoff-clean for any go decision.
  - Before scoring, form conservative connected-component groups: two positives share a group if they have at least 30 percent global sequence identity, binder-domain TM-score at least 0.5, or a shared published design lineage or parent scaffold.
  - For each group, record the earliest public date among every linked sequence, structure, design lineage, and parent scaffold. A group is cutoff-clean only when that earliest date post-dates every production model's training cutoff; a mixed-age group is not cutoff-clean.
  - For every evaluated group, at least three topology-matched hard negatives with recorded provenance: experimentally supported same-scaffold nonbinders where available, otherwise target-irrelevant structures matched on length, composition, and coarse topology. Scrambles remain a secondary coarse check.
- **Outputs:**
  - D-thresholds: frozen scaffold-group definitions and folds, hard-negative provenance, group-held-out predictions, all-group and post-cutoff-group separation with intervals, final filter thresholds fitted only after held-out evaluation, clustering cuts, decision table, and artifact digest.
- **Assumptions:**
  - Published binders are informative about the pipeline's ability to recognize binders it did not generate.
  - Conservative sequence/structure/design-lineage grouping prevents related binders from crossing evaluation folds.
  - Topology-matched hard negatives are sufficiently well supported to test whether the stack recognizes binding rather than scaffold class.
- **Limitations:**
  - Positive controls and independent scaffold groups are few and were not produced by this pipeline; held-out discrimination may still transfer poorly to campaign designs.
  - Published affinities come from heterogeneous assays.
  - Some hard negatives may lack direct nonbinding assays; their provenance and evidential class must be reported, and five defensible post-cutoff group strata are required for go.
  - The cutoff-clean independent-group subset is small, and grouping by the earliest linked precursor is intentionally conservative, so its one-sided lower confidence bound may force revise or no-go.
  - Final thresholds are fitted on all controls only after group-held-out evaluation passes; their prospective validity still requires wet-lab evidence outside this campaign.
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

### CAN-energy — At G1, score the deposited PD-1:PD-L1 interface and a deliberately disrupted variant through the production protocol and emit deterministic raw energy/liability terms under a versioned schema independent of D-thresholds.

- **Tool:** TOOL-energy
- **Expected artifacts and schema:**
  - Raw interface-energy and liability rows under the versioned G1 schema, plus a manifest with package version, commit, flags, seed, exact replay digest, and cost.
- **Positive, negative, and sanity cases:**
  - Positive: the native interface scores favourably.
  - Negative: the disrupted interface scores materially worse in the expected direction.
  - Sanity: rerunning the identical input reproduces the identical terms.
- **Downstream acceptance:** At G1, raw terms validate and reproduce without D-thresholds. After D-thresholds freezes, G2 writes a separate D-canary-compat artifact that binds the threshold digest and proves the table mechanically consumes the stored rows; a missing or renamed field fails G2.
- **Quarantine triggers:** Raw-schema or replay failure blocks S2. Post-freeze table-compatibility failure blocks S3. Canary rows are fixtures and never enter D-designs.

### CAN-pipeline — Before any control or campaign design is scored, run a miniature generation-through-raw-score transport check on explicitly labelled non-campaign fixtures at production settings. It verifies interfaces, schemas, deterministic replay, and raw score transport only; it does not apply thresholds or supply binding evidence.

- **Tool:** TOOL-backbone
- **Expected artifacts and schema:**
  - A versioned raw-score fixture table with every predeclared score field populated, no threshold-derived columns, a manifest, and an exact replay digest.
- **Positive, negative, and sanity cases:**
  - Positive: raw fixture rows are complete and within physically plausible ranges.
  - Negative: a deliberately malformed backbone is rejected rather than producing a plausible-looking row.
  - Sanity: the raw miniature pass reproduces exactly from its manifest.
  - Boundary: fixtures are labelled non-campaign and cannot enter D-designs or any scientific result.
- **Downstream acceptance:** At G1, the versioned raw-score schema and exact replay pass without a decision table. After D-thresholds freezes, G2 writes D-canary-compat, binding the threshold digest and proving the real table emits every required derived column from this stored fixture before S3 dispatch.
- **Quarantine triggers:** Raw transport failure blocks S2. Failure of the post-freeze table-application check blocks S3. Canary fixtures are permanently excluded from campaign results.

### CAN-sequence — At G1, redesign sequences on the deposited binding-partner backbone at production settings, then predict and emit deterministic raw downstream scores under versioned schemas independent of D-thresholds. These are labelled non-campaign fixtures.

- **Tool:** TOOL-sequence
- **Expected artifacts and schema:**
  - Designed fixture sequences with per-position confidence and exact invocation.
  - A run manifest carrying model identity, weight digest, container image digest, seed, exact replay digest, and cost.
  - Raw prediction and score rows under the versioned G1 schemas, with no threshold-derived columns.
- **Positive, negative, and sanity cases:**
  - Positive: redesigned sequences recover the native fold in prediction within a pre-declared coordinate deviation, and recover a pre-declared fraction of the native interface residue identities.
  - Negative: sequence design run against a deliberately masked or absent target context yields interface confidence in the low-confidence regime rather than confident nonsense.
  - Sanity: two runs at the same seed produce identical sequences, and two runs at different seeds produce sequences within a pre-declared identity spread.
- **Downstream acceptance:** At G1, sequence, prediction, and raw-score schemas validate and replay without D-thresholds. After D-thresholds freezes, G2 records in D-canary-compat that the table consumes the stored rows and emits every required derived column before S3 dispatch.
- **Quarantine triggers:** Raw-schema or replay failure blocks S2. Post-freeze table-compatibility failure blocks S3. Fixture sequences and rows are permanently excluded from D-designs.

## 7. Frozen evaluation or adjudication instrument

**Frozen before production (asserted, not verified):** Before any control is scored, freeze the scaffold grouping, every group's earliest linked public provenance date, the cutoff-clean classification against every production-model cutoff, leave-one-group-out folds, hard-negative rule, matching tolerances, filters, tuning, statistics, bootstrap seed and group-resampling rule, five-group minimum, and governing decision statistic. After held-out evaluation passes, fit final thresholds, clustering cuts, and the complete decision table once on all controls; freeze D-thresholds with its detached digest before any campaign design is generated or scored, and recheck it at G3.

**Criteria**
- Primary separation statistic: out-of-fold AUROC for the combined filter rank against topology-matched hard negatives, pooled from predeclared leave-one-scaffold-group-out folds; individual-positive holdout and resubstitution AUROC are prohibited as decision evidence.
- Governing uncertainty statistic: the one-sided 90 percent lower confidence bound for cutoff-clean group-held-out AUROC, from 10,000 fixed-seed bootstrap resamples of independent cutoff-clean scaffold groups together with their associated negative strata.
- Secondary statistics: the held-out fraction of topology-matched hard negatives scoring above the positive-group median, reported for all groups and the post-cutoff groups; scramble performance is reported separately as a coarse check.
- A go requires at least 6 independent scaffold groups overall and at least 5 cutoff-clean groups with defensible hard-negative strata, and uses only the cutoff-clean-group lower bound. If any minimum or the bound fails, the result is revise or no-go; the all-group estimate cannot carry go eligibility.
- Cluster-corrected yield: distinct clusters among campaign designs clearing every final frozen threshold, using single linkage at 60 percent global sequence identity and 2.0 Angstrom interface backbone RMSD, with 50 and 70 percent alternatives reported.
- Provenance completeness: every control prediction records its scaffold group, fold, hard-negative provenance, and frozen training inputs; every design traces to a seed, a pre-compute batch manifest, and the frozen artifact digests it consumed.
- Threshold integrity: D-thresholds remains byte-identical from G2 through G3.

**Comparators, controls, cases, or adjudication rules**
- Positive controls: at least 8 published, experimentally validated PD-L1 binders spanning at least 6 independent sequence/structure scaffold groups; at least 5 groups must be cutoff-clean for a go result.
- Before scoring, freeze conservative connected-component groups: positives are linked by at least 30 percent global sequence identity, binder-domain TM-score at least 0.5, or shared published design lineage or parent scaffold. No connected group may cross folds.
- For each frozen group, record the earliest public date across every linked sequence, structure, design lineage, and parent scaffold. Classify the group as cutoff-clean only if that earliest date post-dates every production model's training cutoff; a post-cutoff binder cannot make an older group cutoff-clean.
- Assign each frozen scaffold group and its hard-negative stratum to one leave-one-group-out fold. Freeze membership, provenance, matching tolerances, random seed, filter candidates, tuning rule, and combination rule before any score is computed.
- Within each fold, select or tune filters only on the other scaffold groups and their negatives. Score the held-out group and its negative stratum once; their scores cannot alter that fold's stack.
- The operative negative stratum contains at least three topology-matched hard negatives per group: experimentally supported same-scaffold nonbinders where available, otherwise target-irrelevant structures matched on length, amino-acid composition, and coarse topology. Record provenance and evidential class. Scrambles are secondary only.
- Pool only held-out group predictions for separation estimates. After the group-held-out gate passes, fit the final thresholds on all controls once and freeze them before generating or scoring campaign designs.
- Campaign designs use the final frozen stack and settings. Any control/design settings difference invalidates the comparison.
- The decision table consumes the one-sided 90 percent lower confidence bound of cutoff-clean group-held-out AUROC plus cluster-corrected yield. All-group AUROC is descriptive and can never override the cutoff-clean-group result.

**Missing-evidence policy:** A design missing any filter column is failed, not imputed and not dropped from the table. A control whose published measurement cannot be cited to a specific assay is excluded from the positive set before freeze and recorded as excluded. A filter that cannot be computed for the control sets is removed from the stack before freeze rather than applied only to campaign designs.

**Exploration versus confirmation:** Control membership, scaffold-group definition, group assignment, hard-negative provenance, filter candidates, tuning rule, combination rule, statistics, interval method, and decision rule are fixed before any control is scored. Filter selection or tuning may occur only inside each fold's training groups; held-out scores cannot change that fold. If group-held-out evaluation passes, the final stack is fitted once on all controls and frozen in D-thresholds before any campaign design is generated or scored. Any later change is a numbered deviation and makes the design result exploratory.

**Stop, pivot, and no-go rules**
- Terminal no-go: the one-sided 90 percent lower bound of post-cutoff group-held-out AUROC fails the threshold frozen in the decision table. Retuning, regrouping, or reselection after held-out scores are visible is prohibited.
- Terminal no-go: fewer than 8 citable positives spanning 6 independent scaffold groups can be assembled. A go is additionally prohibited with fewer than 5 cutoff-clean groups under the frozen earliest-public-provenance rule or without defensible topology-matched hard negatives; the decision table maps those cases to revise or no-go.
- Stop and escalate: a canary fails four times at G1.
- Revise, not go: a result in a revise cell triggers exactly the bounded work named by that cell.
- No-decision: if the compute allocation lapses before the complete campaign set is scored, report the scored fraction and do not apply the decision table.
- Deviation downgrade: any change to a frozen artifact after its gate makes D-memo exploratory and must appear in its first paragraph.

## 8. Staged funnel and promotion gates

**Stages**

### S1 — Freeze the target and the environment

- **Purpose:** Pin the target, software, compute authority, and raw pipeline interfaces before controls are calibrated or campaign designs exist.
- **Inputs:** Public structural data; installed software.
- **Activities:**
  - Retrieve and verify a PD-1:PD-L1 co-crystal structure against RCSB; record accession, chain, method, resolution, interface density gaps, and file digest
  - Define the hotspot residue set in the deposited numbering and record it in D-target
  - Pin every tool identity, version, weight-file digest, container image digest, and licence in D-environment
  - Record APR-compute evidence, allocation scope, available GPU-hours, and exact timezone-aware expiry in D-environment
  - Run all four G1 canaries at production settings; every canary ends at deterministic versioned raw outputs independent of D-thresholds, and all canary inputs are labelled non-campaign fixtures
- **Outputs:**
  - D-target and D-environment, both frozen with detached SHA-256 manifest entries; four G1 canary manifests.
- **Owner:** ROLE-comp-lead
- **Budget:** 50 A100 GPU-hours; approximately one week.
- **Expected pace:** One week. If S1 is not frozen within two weeks, escalate to ROLE-pi rather than proceeding on an unpinned environment.
- **Promotion gate:** G1

### S2 — Calibrate on controls and freeze the thresholds

- **Purpose:** Estimate held-out control discrimination without scaffold or tuning leakage, then freeze the final thresholds and decision table before any campaign design exists.
- **Prerequisites:**
  - S1
- **Inputs:** D-target, D-environment including the frozen allocation record, G1 raw canary fixtures, and published binder literature.
- **Activities:**
  - Select at least 8 citable positives spanning at least 6 independent scaffold groups; freeze earliest linked public provenance dates and require at least 5 cutoff-clean groups for go eligibility
  - Freeze conservative sequence/structure/design-lineage groups and construct each group's topology-matched hard-negative stratum plus secondary scrambles
  - Freeze leave-one-scaffold-group-out folds, negative provenance, candidate filters, within-fold tuning, combination, statistics, interval method, and decision rule before scoring
  - Run each group fold once, tuning only on training groups and preserving held-out predictions
  - Compute pooled all-group and post-cutoff-group held-out statistics and fixed-seed group-bootstrap intervals
  - If the group-held-out gate passes, fit final thresholds on all controls and freeze D-thresholds with clustering cuts and the total decision table
  - After D-thresholds is frozen, apply its table to the stored CAN-pipeline, CAN-energy, and CAN-sequence raw fixtures; verify CAN-predict field compatibility; write and freeze the separate D-canary-compat artifact before G2 acceptance
  - Use the exact allocation expiry and remaining GPU-hours from D-environment to scope S3 to what can complete
- **Outputs:**
  - D-thresholds, frozen before compatibility testing, containing control results, thresholds, cuts, decision table, and detached digest.
  - D-canary-compat, frozen after testing, binding the D-thresholds digest and recording every raw-fixture compatibility/application result.
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
  - D-designs; the immutable D-runtime G3 reconciliation snapshot and event-log prefix digest; the stage cost record. The live event stream remains appendable only for S4/G4.
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
  - Freeze the candidate D-memo version and detached digest; append the G4 acceptance event naming that path and digest; then close and hash the final event stream and write D-runtime's final reconciliation
  - Package all frozen artifacts and their detached manifest for handoff
- **Outputs:**
  - Accepted immutable D-memo version, final D-runtime event log and reconciliation, and the complete detached manifest.
- **Owner:** ROLE-methods
- **Budget:** 0 GPU-hours; approximately one week of writing.
- **Expected pace:** One week.
- **Promotion gate:** G4

**Gates**

### G1

- **Stage:** S1
- **Required evidence:**
  - D-target carrying a verified accession, chain, hotspot residue set, and detached manifest digest.
  - D-environment carrying every tool version, weight digest, image digest, licence, APR-compute evidence, available GPU-hours, allocation scope, and exact timezone-aware expiry.
  - All four G1 canary manifests showing positive, negative, schema, and reproducibility checks passed on labelled non-campaign fixtures; every canary ends at versioned raw output independent of D-thresholds.
- **Owner:** ROLE-methods
- **On failure:** S2 does not start and no allocation beyond the S1 budget is consumed. A failed canary is fixed and rerun; a structure that cannot be verified against RCSB sends the epitope definition back for reselection.
- **Criteria:**
  - The target, environment, and exact compute-allocation record are frozen; all four tool canaries pass deterministic production-setting checks against versioned raw schemas independent of D-thresholds; no threshold table is applied at G1.

### G2

- **Stage:** S2
- **Required evidence:**
  - D-thresholds with frozen scaffold groups and folds, hard-negative provenance, held-out predictions, all-group and post-cutoff-group statistics and intervals, final thresholds, clustering cuts, complete decision table, exact predecessor digests, and detached manifest entry.
  - At least 8 citable positives spanning 6 independent groups; frozen earliest linked public provenance per group; at least 5 cutoff-clean groups with defensible topology-matched hard negatives for any go.
  - D-canary-compat, frozen separately after D-thresholds, binding its exact digest and recording successful CAN-pipeline, CAN-energy, CAN-sequence table applications plus CAN-predict field compatibility without manual editing.
  - Attestations that grouping and fold definitions preceded control scoring and final thresholds preceded campaign-design generation or scoring.
  - A capacity calculation consuming the exact D-environment allocation-record digest, remaining GPU-hours, and timezone-aware expiry to bound the S3 design count.
- **Owner:** ROLE-comp-lead
- **On failure:** Failure of the governing group-held-out separation rule is a terminal no-go. Too few independent groups, fewer than 5 cutoff-clean groups under the earliest-public-provenance rule, or missing defensible hard negatives prohibits go. Do not retune, regroup, redate, or reselect controls after held-out scores are visible.
- **Criteria:**
  - The cutoff-clean leave-one-scaffold-group-out procedure passes its governing lower bound; D-thresholds is frozen; and separate D-canary-compat proves the frozen table mechanically consumes every stored raw canary fixture before S3 dispatch.

### G3

- **Stage:** S3
- **Required evidence:**
  - D-designs with complete threshold columns, cluster assignments, per-design seeds and manifests, stage cost, and unchanged D-thresholds digest.
  - D-runtime's immutable `deliverables/runtime-g3-reconciliation.md`, recording the highest sequence, exact byte length, and SHA-256 of the `artifacts/runtime/events.ndjson` prefix through G3.
  - G3 reconciliation proving every authorized S3 batch has one terminal completion or recorded failure, no output lacks prior authorization, and no completed batch was dispatched twice. The live stream remains open only for S4/G4.
- **Owner:** ROLE-methods
- **On failure:** If D-thresholds changed after G2, every affected score is quarantined and rescored under the frozen table, and the change is recorded as a numbered deviation that downgrades the memo to exploratory. If the mid-stage checkpoint shows large under-spend with unexplored branches, escalate to ROLE-pi.
- **Criteria:**
  - The campaign design set has been scored exactly once against the frozen thresholds, with complete provenance and no post-hoc threshold change.

### G4

- **Stage:** S4
- **Required evidence:**
  - The accepted immutable D-memo version stating the decision cell and its two values in the first paragraph; it references the immutable G3 runtime-snapshot digest, not the later final log.
  - The G4 event naming the accepted memo path and detached SHA-256 digest.
  - D-runtime's final reconciliation and the complete event log through G4, both covered by the detached manifest, with the stream closed against further append.
  - The complete frozen artifact set and detached manifest, reproducing from stored manifests.
- **Owner:** ROLE-pi
- **On failure:** A memo whose recommendation does not match the table cell is returned. A PI override is permitted but is recorded as an override with its reason, and never presented as the table's output.
- **Criteria:**
  - The recommendation is the cell mechanically reached on the frozen decision table, and the handoff package is complete and reproducible.

## 9. Resources and fail-closed dispatch

**Budgets**
- Total compute: at most 2,000 A100 GPU-hours under APR-compute; D-environment records the authoritative remaining hours and exact timezone-aware expiry before G1.
- S1: 50 GPU-hours. S2: 300 GPU-hours. S3: 1,600 GPU-hours with a checkpoint at 800. S4: 0 GPU-hours.
- Cash: USD 0. The campaign authorizes no expenditure of any kind.
- Budget floor: reaching S3's mid-stage checkpoint with substantially unspent allocation and unexplored design branches is incomplete and escalates to ROLE-pi.
- Calendar: approximately twelve weeks but never beyond the exact allocation expiry recorded in D-environment.
- Calendar ceiling: at every gate ROLE-methods computes cumulative elapsed time and remaining capacity against the frozen allocation record.
- Expiry rule: at G2, scope S3 from the allocation-record digest, remaining hours, and exact expiry. If the complete design set cannot be scored before expiry, report no-decision rather than apply the table to a partial set.

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
- Only the single ROLE-comp-lead dispatcher may append runtime records or authorize batches. It atomically appends an authorized event before compute, and every started batch receives exactly one completed or failed terminal event before G3.

**Approvals**
- **APR-compute:** Standing institutional GPU allocation, already granted. D-environment must freeze the approval evidence, scope, available GPU-hours, exact timezone-aware expiry, and detached record digest before G1 acceptance.
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

### WU-freeze — Produce D-target and D-environment with the allocation record, freeze them under detached digests, and pass four threshold-independent G1 raw-schema canaries.

- **Authoritative inputs and hashes:**
  - The campaign constitution; RCSB Protein Data Bank; installed software and licences; authoritative APR-compute allocation evidence.
- **Permitted actions:**
  - Retrieve public structural data and verify it against RCSB
  - Install, pin, and digest software, weights, and container images
  - Record APR-compute evidence, scope, available GPU-hours, and exact timezone-aware expiry
  - Run all four G1 canaries at production settings and validate only deterministic versioned raw outputs on labelled non-campaign fixtures
  - Write D-target and D-environment and update the detached manifest
- **Prohibited actions:**
  - Generating or scoring any campaign design
  - Applying or implying a filter threshold or decision table at G1
  - Using G1 canary fixtures as scientific controls or campaign results
  - Ordering synthesis, contacting a vendor, or committing any spend
  - Proceeding on an unverified accession, unpinned tool version, or unrecorded allocation expiry
- **Method and tool constraints:** M-target only. Canaries run at exactly the settings S2 and S3 will use; a canary run at reduced settings does not count.
- **Exact outputs:**
  - D-target, D-environment, and four G1 canary manifests including the CAN-pipeline raw fixture table.
- **Verification and acceptance:** G1 evidence is complete: verified target and detached digests, pinned tools and licences, exact APR-compute scope/hours/expiry, and four passing canary manifests. Every canary proves deterministic raw-schema transport on labelled non-campaign fixtures without consulting or applying D-thresholds.
- **Resource ceiling:** 50 A100 GPU-hours and two calendar weeks.
- **Retry and failure classes:** A failed canary may be fixed and rerun without escalation up to three times; the fourth failure escalates to ROLE-pi.
- **Escalation and handoff:** Escalate to ROLE-pi if no PD-1:PD-L1 structure verifies with adequate interface density, if a required tool's licence forbids the intended use, or if the two-week ceiling is reached.

### WU-calibrate — Freeze controls, groups, held-out results, thresholds, clustering cuts, and the decision table as D-thresholds; then test that immutable table against stored raw canary fixtures and freeze the separate D-canary-compat artifact before G2.

- **Authoritative inputs and hashes:**
  - The constitution; frozen D-target and D-environment with exact digests; D-environment's APR-compute allocation record; stored G1 raw canary fixture; peer-reviewed experimental PD-L1 binding literature.
- **Permitted actions:**
  - Select citable positive controls, freeze conservative scaffold groups, and construct topology-matched hard-negative strata
  - Freeze group-fold membership, negative provenance, and the complete fitting/evaluation procedure before scoring
  - Tune only inside each fold's training groups and score each held-out group once
  - Compute fixed-seed group-held-out estimates and intervals
  - After the held-out gate passes, fit final thresholds on all controls and freeze D-thresholds
  - After D-thresholds freezes, apply it to stored CAN-pipeline, CAN-energy, and CAN-sequence raw fixtures and verify CAN-predict fields; record results only in separate D-canary-compat
  - Consume the allocation-record digest to scope S3 to the remaining hours and exact expiry
  - Freeze clustering cuts and a total decision table governed by the post-cutoff-group lower bound
- **Prohibited actions:**
  - Generating or scoring campaign designs before D-thresholds is frozen
  - Allowing related sequences, structures, design lineages, or parent scaffolds to cross evaluation folds
  - Using held-out scores to alter that fold's filters, weights, thresholds, groups, or membership
  - Reporting individual-positive holdout or resubstitution performance as decision evidence
  - Letting all-group AUROC override the post-cutoff-group governing statistic
  - Regrouping or reselecting controls after any score is visible
  - Claiming go without 8 positives spanning 6 groups, 5 cutoff-clean groups under the earliest-public-provenance rule, and defensible topology-matched hard-negative strata
  - Hand-building matched negatives outside the frozen rule
  - Ordering synthesis or committing spend
- **Method and tool constraints:** M-controls only, at the exact settings recorded in D-environment.
- **Exact outputs:**
  - D-thresholds, frozen with a detached digest before compatibility testing.
  - D-canary-compat, frozen afterward with the consumed D-thresholds digest and all fixture results.
- **Verification and acceptance:** G2 evidence includes cutoff-clean group-held-out results, governing intervals, immutable D-thresholds, separate immutable D-canary-compat binding that threshold digest, clustering cuts, total decision table, predecessor digests, timing attestations, and an allocation-bound capacity calculation.
- **Resource ceiling:** 300 A100 GPU-hours and three calendar weeks.
- **Retry and failure classes:** Infrastructure failures may rerun an identical group fold from its frozen inputs. Control membership, scaffold groups, folds, hard-negative strata, fitting rules, and evaluation rules cannot change after any score is visible.
- **Escalation and handoff:** Escalate if 8 citable positives spanning 6 independent groups or 5 cutoff-clean groups cannot be found, if linked precursor dates or defensible topology-matched hard negatives cannot be established, if groups cannot be formed without leakage, or if the governing rule fails. Follow the frozen revise/no-go cell; never redate or regroup after scoring.
- **Depends on work units:**
  - WU-freeze

### WU-generate — Generate and score the campaign design set once against the frozen thresholds, with complete provenance.

- **Authoritative inputs and hashes:**
  - The constitution; frozen D-target, D-environment, and D-thresholds with their exact digests.
- **Permitted actions:**
  - Through the single dispatcher, append an authorized batch event before compute, then started and exactly one completed or failed terminal event
  - Generate backbones and design sequences within the frozen parameters
  - Predict complexes and compute interface and liability terms at frozen settings
  - Apply the frozen thresholds once and record pass/fail per filter
  - Cluster survivors at all three declared cuts
  - Record seeds, manifests, output digests, timestamps, actor, status, and per-design cost
  - Generate and digest the immutable G3 reconciliation snapshot while leaving the event stream open only for S4/G4
- **Prohibited actions:**
  - Changing any value in D-thresholds
  - Rescoring a design under different thresholds to improve its rank
  - Dropping designs that score below the negative control distribution
  - Reporting raw pass count without cluster count
  - Ordering synthesis, contacting a vendor, or committing any spend
  - Consuming compute for a batch whose manifest has not already been appended to the event log
- **Method and tool constraints:** M-generate and M-score, at exactly the settings the controls were scored under. A settings difference between control scoring and design scoring invalidates the comparison and is a deviation.
- **Exact outputs:**
  - D-designs with cluster assignments and full provenance.
  - D-runtime G3 reconciliation snapshot at `deliverables/runtime-g3-reconciliation.md`, with the exact prefix length and digest for `artifacts/runtime/events.ndjson`.
- **Verification and acceptance:** G3 evidence includes complete D-designs, unchanged D-thresholds, costs, and an immutable D-runtime G3 reconciliation snapshot that binds the exact event-log prefix and proves authorized-to-terminal batch accounting without duplicate completion.
- **Resource ceiling:** 1,600 A100 GPU-hours and five calendar weeks.
- **Retry and failure classes:** An infrastructure failure ends with a failed event. A retry receives a new batch ID linked to the failed predecessor and reuses its frozen inputs and seed. A completed batch is never dispatched again, and a design is never rescored to improve its result.
- **Escalation and handoff:** Escalate to ROLE-pi at the 800 GPU-hour checkpoint if spend is far below pace with design branches unexplored, or if the allocation will expire before the stage completes.
- **Depends on work units:**
  - WU-calibrate

### WU-decide — Apply the decision table, freeze the candidate D-memo, append its G4 acceptance event, then close and reconcile the final runtime stream without creating a memo/log digest cycle.

- **Authoritative inputs and hashes:**
  - The constitution; frozen D-thresholds and D-designs with their exact digests; the control calibration table.
- **Permitted actions:**
  - Read the cell reached from the frozen decision table
  - Compute proximity to adjacent cells
  - Write the memo leading with the cell and least favourable defensible reading, referencing only the immutable G3 runtime snapshot
  - Freeze the memo candidate and its detached digest, then append one G4 acceptance event naming both
  - Close and hash the complete runtime log, write final reconciliation, and package the detached manifest
- **Prohibited actions:**
  - Stating a recommendation other than the cell mechanically reached
  - Stating or implying that any design binds PD-L1
  - Omitting the ranked table or the control calibration from a no-go memo
  - Presenting a principal-investigator override as the table's output
  - Ordering synthesis or authorizing wet-lab work
  - Running the decision table on a partially scored design set; an incomplete set yields a no-decision memo
- **Method and tool constraints:** M-decide only. The table is applied exactly once.
- **Exact outputs:**
  - Accepted immutable D-memo version, D-runtime final reconciliation, complete event log through G4, and detached manifest.
- **Verification and acceptance:** G4 evidence includes the mechanically reached recommendation, an immutable D-memo version referencing the G3 runtime snapshot, a G4 event naming the memo path and digest, and final reconciliation/digests for the closed event stream.
- **Resource ceiling:** 0 GPU-hours and two calendar weeks.
- **Retry and failure classes:** A memo returned before G4 acceptance may be rewritten. After acceptance, any correction creates a new immutable version that references and retains the accepted predecessor; the table cell is not recomputed.
- **Escalation and handoff:** Escalate to ROLE-pi if the memo's author believes the table cell is wrong — as an override request on the record, never as a rewritten recommendation.
- **Depends on work units:**
  - WU-generate

## 11. Durable operations and recovery

**Continuous runtime enabled:** True

**Continuation trigger:** Work resumes from the campaign state directory and the append-only event log, never from chat history. A new session reads the last accepted gate and the frozen artifact digests, and starts the first work unit whose dependencies are accepted and whose outputs are absent.

**State store:** Canonical campaign state remains in the campaign state directory. Frozen research artifacts live at their declared deliverable paths. Exact-byte SHA-256 digests are stored separately in UTF-8 `artifacts/MANIFEST.sha256`; an artifact never embeds the digest that identifies itself.

**Event log:** Live path: `artifacts/runtime/events.ndjson`, UTF-8 JSON Lines schema rescamp-runtime-event-v1. Records carry sequence, unique event_id, type, batch_id where applicable, status, timezone-aware timestamp, actor, frozen input digests, terminal output digests, cumulative cost, and predecessor event_id. One ROLE-comp-lead dispatcher owns an exclusive append lock and writes complete lines atomically. At G3, snapshot and hash the exact prefix but keep the stream open only for S4/G4; after the G4 acceptance event, close it and record its final detached digest.

**Checkpoint policy:** Checkpoint every artifact freeze, gate decision, and S3 batch transition. Before compute, the single dispatcher appends authorization with batch ID, parameters, seed, and frozen inputs; it then appends started and exactly one terminal event. G3 freezes an immutable prefix reconciliation. S4 freezes D-memo, appends G4 acceptance naming its digest, then closes and hashes the final stream.

**Liveness:** The single dispatcher records a timezone-aware heartbeat event for each active batch at least once per working day. A batch without a heartbeat or terminal event for more than one working day is stalled and escalated to its stage owner. A chat session ending is not stage completion.

**Recovery:** Before G3, reconcile batches against the live log. After G3, verify the immutable prefix snapshot before S4 and allow only S4/G4 event types. An authorized or started batch without a terminal event may retry under a linked new ID and identical inputs. Output without authorization, mismatched digests, duplicate terminal events, changes to the G3 prefix, or any append after final G4 reconciliation blocks acceptance.

**Idempotency:** Unique IDs and the single dispatcher prevent duplicate dispatch. Terminal events bind output digests. A completed batch is never rerun; a failed or interrupted batch retries only under a linked new ID with identical inputs and seed. G3 binds an immutable prefix; G4 is appended once; final reconciliation closes the stream.

A conversational session is not a scheduler.

**Plan continuity and amendments**

Use `campaign.json` at `sha256:cec061c58fca6136d0d70765c7c307fa82692a7020455fdb2ce8691f7230bb2d` as the active contract.

If execution reveals a material plan change, pause affected future work and re-freeze the plan under a new digest before continuing — in ResCamp, the `revise` mode. Never rewrite a frozen plan in place: a pending brief carrying an older digest is stale, while completed artifacts remain bound to the version that produced them.

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

**Deviation policy:** Any change to a frozen target, environment, control set, threshold table, design table, runtime record, or accepted memo version is recorded as a numbered deviation with the reason, predecessor and successor paths and detached digests, approver, and invalidated conclusions. Accepted artifacts remain immutable; corrections create new versions and retain predecessors. A deviation after campaign designs were scored downgrades the recommendation to exploratory.

Lead with the least favorable defensible interpretation.

**Recorded claims**

### CLM-separation — The predeclared leave-one-scaffold-group-out control procedure separates published PD-L1 binders from topology-matched hard negatives by the held-out margin recorded in D-thresholds.

- **Inquiry:** INQ-separation
- **Support:**
  - Held-out scaffold-group control predictions and separation estimates in D-thresholds, computed under predeclared groups and the same production implementation later frozen for campaign designs.
- **Counterevidence and objections:**
  - Residual sequence, scaffold, or topology confounding; small numbers of independent positive groups; published binders being unrepresentative of what this pipeline generates; assay heterogeneity across the papers supplying the positives.
- **Verification:** Recompute pooled leave-one-scaffold-group-out AUROC and its fixed-seed confidence bound from D-thresholds; verify that no sequence/structure scaffold group crosses folds and never substitute in-sample or individual-positive resubstitution performance.
- **Status:** unevaluated
- **Uncertainty:** Bounded by small control sets, heterogeneous assays, residual model-training contamination, imperfect hard negatives, and the lack of wet-lab validation. Only groups whose earliest linked public sequence, structure, design lineage, or parent scaffold post-dates every production-model cutoff enter the governing lower bound.
- **Reporting rule:** Reported whether the margin is large, small, or absent. An absent margin is the campaign's terminal result.

### CLM-recommendation — The recommendation delivered to the principal investigator is the cell reached on the frozen decision table, together with the evidence that placed it there.

- **Inquiry:** INQ-spend
- **Support:**
  - The frozen decision table in D-thresholds, the scaffold-group control calibration table, and the cluster-corrected yield from the ranked design table.
- **Counterevidence and objections:**
  - That a mechanical table oversimplifies a judgement the PI should make holistically.
  - The table's purpose is to prevent the judgement from being made after seeing which designs look attractive, not to remove the PI's authority; the PI may override it and the memo records the override as such.
- **Verification:** Derive the cell mechanically from the governing cutoff-clean leave-one-scaffold-group-out AUROC lower bound and cluster-corrected yield recorded in the frozen artifacts; verify each qualifying group's earliest linked public provenance date.
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
  - Freeze time and detached SHA-256 entry in `artifacts/MANIFEST.sha256`
- **Acceptance test:** The accession resolves at RCSB to a PD-1:PD-L1 complex with the recorded chains, method, and resolution; the coordinate digest matches the retrieved file; every hotspot residue exists in the deposited numbering; and the artifact carries a freeze time and digest. An accession that does not verify fails the artifact rather than being footnoted.
- **Owner:** ROLE-comp-lead
- **Immutable after freeze:** yes

### D-environment — Frozen software environment

- **Path:** deliverables/environment.md
- **Schema:**
  - Per tool: identity, release tag, weight-file digest, container image digest, licence, and licence-compatibility determination
  - Exact invocation, flags, template and MSA policy, and seed policy for each tool
  - Generation parameters: length range, topology constraints, batch size
  - APR-compute approval identifier and evidence, allocation scope, available A100 GPU-hours, exact expiry timestamp with timezone, and record retrieval time
  - Canary manifests for all four G1 canaries with positive, negative, raw-schema, and reproducibility results; fixtures are labelled non-campaign and threshold-independent
  - Freeze time and detached SHA-256 entry in `artifacts/MANIFEST.sha256`
- **Acceptance test:** Every tool appears with a pinned version and licence determination; APR-compute scope/hours/expiry are recorded; all four G1 canaries validate deterministic production-setting raw outputs against versioned schemas independent of D-thresholds; and each reproduces from its manifest.
- **Owner:** ROLE-comp-lead
- **Immutable after freeze:** yes

### D-thresholds — Control calibration and frozen decision table

- **Path:** deliverables/thresholds-and-decision-table.md
- **Schema:**
  - Exact D-target and D-environment digests consumed
  - At least 8 positive controls with cited assays spanning at least 6 independent scaffold groups; every production-model cutoff recorded; at least 5 cutoff-clean groups identified
  - Frozen connected-component grouping evidence and, for each group, the earliest public date across every linked sequence, structure, design lineage, and parent scaffold plus its cutoff-clean classification
  - Frozen leave-one-scaffold-group-out membership linking each group to topology-matched hard negatives, with provenance and evidential class
  - Pre-score filter candidates, within-fold tuning rule, combination rule, matching procedure, tolerances, and random seed
  - Per-group held-out predictions plus pooled all-group and post-cutoff-group AUROC and hard-negative-above-median statistics
  - Fixed-seed 10,000-resample independent-group bootstrap intervals and the post-cutoff one-sided 90 percent lower bound
  - Final filter thresholds fitted on all controls only after group-held-out evaluation passes
  - Clustering metric and the 50, 60, and 70 percent identity cuts
  - A total decision table using the cutoff-clean-group lower bound and cluster-corrected yield, including bounded revise cells and all sample/provenance minimums
  - Attestations that grouping and folds preceded control scoring and final thresholds preceded campaign-design generation or scoring
  - Freeze time and detached SHA-256 entry in `artifacts/MANIFEST.sha256`
- **Acceptance test:** Every control has citable provenance and a frozen scaffold group; no related group crosses folds; every group records its earliest linked public sequence/structure/lineage/scaffold date and cutoff-clean classification; every hard negative has recorded provenance; held-out statistics reproduce; at least 8 positives span 6 groups and go requires 5 cutoff-clean groups with defensible hard negatives; final thresholds were fitted only after held-out evaluation; the decision table has no undefined cell; all digests are present.
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
  - References to the corresponding authorized, started, and terminal events in D-runtime
  - Freeze time and detached SHA-256 entry in `artifacts/MANIFEST.sha256`
- **Acceptance test:** Every design has every filter column populated; the D-thresholds digest matches G2; pass/fail is derivable mechanically from recorded scores and frozen thresholds; cluster counts are reported at all three cuts; D-runtime reconciles every batch; and D-designs has a detached manifest entry. Designs below the negative-control distribution remain in the table.
- **Owner:** ROLE-comp-lead
- **Immutable after freeze:** yes

### D-memo — Go/no-go decision memo

- **Path:** deliverables/decision-memo.md
- **Schema:**
  - First paragraph: the cell reached on the frozen decision table and the two values that placed it
  - Control separation reported as a distribution comparison with its overlap
  - Contamination-adjusted separation on the post-cutoff independent-group subset, stated next to the all-group figure
  - Cluster-corrected yield at all three cuts
  - Proximity to adjacent decision cells
  - Residual uncertainty and the least favourable defensible interpretation
  - Any numbered deviations and what they invalidate
  - Any principal-investigator override, recorded as an override with its reason
  - Consumed artifact digests for D-target, D-environment, D-thresholds, D-designs, and the immutable D-runtime G3 reconciliation snapshot
  - Version identifier, predecessor memo digest if any, acceptance time, and detached SHA-256 entry; the G4 event names this digest before the runtime stream is finalized
- **Acceptance test:** The accepted immutable memo version states the cell mechanically reached on the frozen table; leads with the cell; never implies that a design binds PD-L1; includes the full ranked table even for no-go; and is referenced by path and detached SHA-256 digest in the accepting G4 event. Corrections create new versions and retain the accepted predecessor.
- **Owner:** ROLE-methods
- **Immutable after freeze:** yes

### D-runtime — Runtime event log and reconciliation

- **Path:** artifacts/runtime/events.ndjson; deliverables/runtime-g3-reconciliation.md; deliverables/runtime-final-reconciliation.md
- **Schema:**
  - Live UTF-8 JSON Lines event stream at `artifacts/runtime/events.ndjson` using rescamp-runtime-event-v1
  - Each event records sequence, unique event_id, event_type, batch_id when applicable, status, timezone-aware timestamp, actor, frozen input digests, terminal output digests, cumulative cost, and predecessor event_id
  - Single-dispatcher exclusive append rule and one complete atomic line per transition
  - For every batch: authorization before compute, optional heartbeats, and exactly one completed or failed terminal event
  - Immutable G3 reconciliation snapshot recording highest sequence, exact byte length, SHA-256 of the event-log prefix through G3, batch accounting, and its own detached digest; the live stream remains appendable only for S4/G4
  - Final G4 reconciliation after the acceptance event, covering the complete event-log digest and proving no later append; detached SHA-256 entries for the final log and both reconciliation artifacts
- **Acceptance test:** At G3, an immutable reconciliation snapshot validates the log prefix and accounts for every S3 batch while the D-runtime stream remains open only for S4/G4. At G4, the acceptance event names D-memo's digest, final reconciliation validates the complete stream, and D-runtime freezes permanently with detached digests for the final log and both snapshots.
- **Owner:** ROLE-comp-lead
- **Immutable after freeze:** yes

### D-canary-compat — Frozen threshold-to-canary compatibility record

- **Path:** deliverables/canary-compatibility.md
- **Schema:**
  - Exact D-thresholds digest consumed after D-thresholds was frozen
  - Exact digests of every stored raw CAN-pipeline, CAN-energy, CAN-sequence, and CAN-predict fixture
  - For CAN-pipeline, CAN-energy, and CAN-sequence: every table-derived field, value, and pass/fail result produced mechanically without manual edits
  - For CAN-predict: field-to-table compatibility result and any table field not applicable to its raw schema
  - Execution time, tool identity, and attestation that D-thresholds remained byte-identical during the checks
  - Freeze time and detached SHA-256 entry in artifacts/MANIFEST.sha256
- **Acceptance test:** The artifact binds the frozen D-thresholds digest and all raw-fixture digests; every required table field resolves; mechanical applications reproduce; no source fixture or D-thresholds changes during testing; and the detached digest verifies. Any incompatibility blocks G2 without modifying D-thresholds.
- **Owner:** ROLE-methods
- **Immutable after freeze:** yes

## 15. Independent challenge

Reviewers are read-only and bound to the frozen content and rubric digests.

**Weakest independence rung among required reviews:** 2 — separate agent context

The weakest rung bounds the challenge, not the strongest: one sequential pass in the set means the set is only as independent as that pass.

Rungs: 1 sequential self-critique < 2 separate agent context < 3 separate agent blinded to conclusions < 4 human domain expert < 5 external adjudicator with its own data. Rungs 1–3 are agent review: they check internal coherence and are **not** external validation. The mode is self-attested — recorded for audit, never proven.

- **methods-evidence:** pass — The earliest-linked-public-provenance rule closes the prior finding. A mixed-age group is explicitly not cutoff-clean; eligibility uses the earliest public date across every linked sequence, structure, design lineage, and parent scaffold; the governing AUROC includes only cutoff-clean groups; provenance and classification are frozen before scoring; and fewer than five qualifying groups cannot produce a go. No remaining major or critical execution defect was found in the bounded scope. (mode: independent-subagent, reviewer: subagent-copernicus)
- **operations-reproducibility:** pass — Pass for the bounded closure review. D-canary-compat now records post-freeze compatibility results separately while binding the immutable D-thresholds digest. D-runtime freezes only its prefix snapshot at G3, remains appendable solely for S4/G4, and freezes permanently after the G4 event and final reconciliation. No remaining major or critical execution defect was found in these lifecycles. (mode: independent-subagent, reviewer: subagent-euclid)

## 16. Kickoff

**Command:** Begin WU-freeze. Read the campaign constitution and D-target's schema, then retrieve and verify a PD-1:PD-L1 co-crystal structure against RCSB, recording accession, chains, method, resolution, interface density gaps, and the coordinate file digest. Do not generate any design, do not score anything other than canary inputs, and do not set or imply any filter threshold. Stop at G1.

**First gate:** G1

**Initially unverified backlog**
- Verify a PD-1:PD-L1 co-crystal structure against RCSB and record its accession, chains, method, resolution, and file digest
- Define the hotspot residue set in the deposited numbering and write D-target
- Pin every tool identity, version, weight digest, image digest, and licence into D-environment
- Run CAN-predict, CAN-energy, CAN-pipeline, and CAN-sequence at production settings and record their manifests
- Confirm the scorer ingests canary output end to end, then present G1 evidence to ROLE-methods, which accepts G1 on a stage it does not execute
