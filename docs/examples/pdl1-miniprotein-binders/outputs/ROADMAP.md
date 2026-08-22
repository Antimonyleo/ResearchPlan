# Roadmap: Can our computational pipeline design de novo miniprotein binders to the PD-1-binding face of human PD-L1 that clear frozen…

**Status:** EXECUTION-READY

**Purpose:** Produce a defensible go/no-go recommendation to the principal investigator on whether to commit gene-synthesis and wet-lab budget to a set of computationally designed de novo miniprotein binders against the PD-1-binding face of human PD-L1.

## Stages

### S1 — Freeze the target and the environment

- **Purpose:** Pin what is being designed against and what is doing the designing, before anything is generated or scored.
- **Outputs:**
  - D-target and D-environment, both frozen with digests; three canary manifests.
- **Owner:** ROLE-comp-lead
- **Budget:** 50 A100 GPU-hours; approximately one week.
- **Expected pace:** One week. If S1 is not frozen within two weeks, escalate to ROLE-pi rather than proceeding on an unpinned environment.
- **Gate G1:** 
  - The target and environment are frozen and the pipeline demonstrably works end to end at production settings.
- **On gate failure:** S2 does not start and no allocation beyond the S1 budget is consumed. A failed canary is fixed and rerun; a structure that cannot be verified against RCSB sends the epitope definition back for reselection.

### S2 — Calibrate on controls and freeze the thresholds

- **Purpose:** Establish whether the filter stack can tell known binders from known non-binders, and fix the thresholds and decision table before any campaign design exists.
- **Prerequisites:**
  - S1
- **Outputs:**
  - D-thresholds, frozen with a digest, containing the control sets, distributions, thresholds, cuts, and decision table.
- **Owner:** ROLE-methods
- **Budget:** 300 A100 GPU-hours; approximately two weeks.
- **Expected pace:** Two weeks. Under-spend here is not a saving: an under-powered control set weakens every downstream claim.
- **Gate G2:** 
  - Thresholds and the decision table are frozen, and the control sets separate against the composition-matched negatives.
- **On gate failure:** Failure to separate is a terminal no-go. The campaign stops at S2, D-memo is written from the control calibration alone, and no design generation is funded. Retuning thresholds to manufacture separation is prohibited.

### S3 — Generate and score the campaign design set

- **Purpose:** Produce candidate designs and score them once against the frozen thresholds.
- **Prerequisites:**
  - S2
- **Outputs:**
  - The ranked design table with full provenance, cluster assignments at three cuts, and a stage cost record.
- **Owner:** ROLE-comp-lead
- **Budget:** 1,600 A100 GPU-hours; approximately four weeks.
- **Expected pace:** Four weeks, with a mid-stage checkpoint at 800 GPU-hours. Reaching the checkpoint with the allocation largely unspent and design branches unexplored is an incomplete stage, and is escalated rather than declared efficient.
- **Gate G3:** 
  - The campaign design set has been scored exactly once against the frozen thresholds, with complete provenance and no post-hoc threshold change.
- **On gate failure:** If D-thresholds changed after G2, every affected score is quarantined and rescored under the frozen table, and the change is recorded as a numbered deviation that downgrades the memo to exploratory. If the mid-stage checkpoint shows large under-spend with unexplored branches, escalate to ROLE-pi.

### S4 — Decide and hand off

- **Purpose:** Apply the frozen decision table once and deliver the recommendation.
- **Prerequisites:**
  - S3
- **Outputs:**
  - D-memo and the complete frozen artifact set with digests.
- **Owner:** ROLE-methods
- **Budget:** 0 GPU-hours; approximately one week of writing.
- **Expected pace:** One week.
- **Gate G4:** 
  - The recommendation is the cell mechanically reached on the frozen decision table, and the handoff package is complete and reproducible.
- **On gate failure:** A memo whose recommendation does not match the table cell is returned. A PI override is permitted but is recorded as an override with its reason, and never presented as the table's output.

## Major blockers

*None recorded.*

## Final deliverables

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
  - Canary manifests for all three canaries with their positive, negative, and reproducibility results
  - Freeze time and artifact digest
- **Acceptance test:** Every tool the pipeline invokes appears with a digest-pinned version and a licence determination; every generation parameter S3 uses appears here; all three canary manifests are present and passing; and re-running any canary from this artifact reproduces its recorded scores exactly at the same seed.
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
