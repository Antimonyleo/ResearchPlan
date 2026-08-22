# Bounded work-unit briefs

Campaign: `pdl1-miniprotein-binders`
Content digest: `sha256:2a21628f3efed539011947d8b30ace27c82d64dfeb23c4201bd12fbab767bb9e`

A local brief may narrow scope but may not weaken the campaign constitution.

## WU-freeze — Produce D-target and D-environment, frozen with digests, and pass all three canaries at production settings.

- **Authoritative inputs and hashes:**
  - The campaign constitution; the RCSB Protein Data Bank; the installed software stack and its licences.
- **Permitted actions:**
  - Retrieve public structural data and verify it against RCSB
  - Install, pin, and digest software, weights, and container images
  - Run the three canaries at production settings
  - Write D-target and D-environment
- **Prohibited actions:**
  - Generating any campaign design
  - Scoring anything other than the canary inputs
  - Setting or implying any filter threshold
  - Ordering synthesis, contacting a vendor, or committing any spend
  - Proceeding on an unverified accession or an unpinned tool version
- **Method and tool constraints:** M-target only. Canaries run at exactly the settings S2 and S3 will use; a canary run at reduced settings does not count.
- **Exact outputs:**
  - D-target, D-environment, and three canary manifests.
- **Verification and acceptance:** G1's required evidence is present in full: verified accession and digests, every tool pinned with a licence determination, and three passing canary manifests whose output the scorer ingests end to end.
- **Resource ceiling:** 50 A100 GPU-hours and two calendar weeks.
- **Retry and failure classes:** A failed canary may be fixed and rerun without escalation up to three times; the fourth failure escalates to ROLE-pi.
- **Escalation and handoff:** Escalate to ROLE-pi if no PD-1:PD-L1 structure verifies with adequate interface density, if a required tool's licence forbids the intended use, or if the two-week ceiling is reached.

## WU-calibrate — Select and freeze the control sets, score them, and freeze the threshold values, clustering cuts, and decision table before any campaign design exists.

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

## WU-generate — Generate and score the campaign design set once against the frozen thresholds, with complete provenance.

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

## WU-decide — Apply the frozen decision table once and write D-memo.

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
