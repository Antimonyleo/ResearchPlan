# Bounded work-unit briefs

Campaign: `pdl1-miniprotein-binders`
Content digest: `sha256:cec061c58fca6136d0d70765c7c307fa82692a7020455fdb2ce8691f7230bb2d`

A local brief may narrow scope but may not weaken the campaign constitution.

## WU-freeze — Produce D-target and D-environment with the allocation record, freeze them under detached digests, and pass four threshold-independent G1 raw-schema canaries.

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

## WU-calibrate — Freeze controls, groups, held-out results, thresholds, clustering cuts, and the decision table as D-thresholds; then test that immutable table against stored raw canary fixtures and freeze the separate D-canary-compat artifact before G2.

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

## WU-generate — Generate and score the campaign design set once against the frozen thresholds, with complete provenance.

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

## WU-decide — Apply the decision table, freeze the candidate D-memo, append its G4 acceptance event, then close and reconcile the final runtime stream without creating a memo/log digest cycle.

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
