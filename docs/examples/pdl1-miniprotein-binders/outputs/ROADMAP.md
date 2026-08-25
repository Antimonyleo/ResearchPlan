# Roadmap: Can our computational pipeline design de novo miniprotein binders to the PD-1-binding face of human PD-L1 that clear frozen…

**Status:** EXECUTION-READY

**Purpose:** Produce a defensible go/no-go recommendation to the principal investigator on whether to commit gene-synthesis and wet-lab budget to a set of computationally designed de novo miniprotein binders against the PD-1-binding face of human PD-L1.

## Stages

### S1 — Freeze the target and the environment

- **Purpose:** Pin the target, software, compute authority, and raw pipeline interfaces before controls are calibrated or campaign designs exist.
- **Outputs:**
  - D-target and D-environment, both frozen with detached SHA-256 manifest entries; four G1 canary manifests.
- **Owner:** ROLE-comp-lead
- **Budget:** 50 A100 GPU-hours; approximately one week.
- **Expected pace:** One week. If S1 is not frozen within two weeks, escalate to ROLE-pi rather than proceeding on an unpinned environment.
- **Gate G1:** 
  - The target, environment, and exact compute-allocation record are frozen; all four tool canaries pass deterministic production-setting checks against versioned raw schemas independent of D-thresholds; no threshold table is applied at G1.
- **On gate failure:** S2 does not start and no allocation beyond the S1 budget is consumed. A failed canary is fixed and rerun; a structure that cannot be verified against RCSB sends the epitope definition back for reselection.

### S2 — Calibrate on controls and freeze the thresholds

- **Purpose:** Estimate held-out control discrimination without scaffold or tuning leakage, then freeze the final thresholds and decision table before any campaign design exists.
- **Prerequisites:**
  - S1
- **Outputs:**
  - D-thresholds, frozen before compatibility testing, containing control results, thresholds, cuts, decision table, and detached digest.
  - D-canary-compat, frozen after testing, binding the D-thresholds digest and recording every raw-fixture compatibility/application result.
- **Owner:** ROLE-methods
- **Budget:** 300 A100 GPU-hours; approximately two weeks.
- **Expected pace:** Two weeks. Under-spend here is not a saving: an under-powered control set weakens every downstream claim.
- **Gate G2:** 
  - The cutoff-clean leave-one-scaffold-group-out procedure passes its governing lower bound; D-thresholds is frozen; and separate D-canary-compat proves the frozen table mechanically consumes every stored raw canary fixture before S3 dispatch.
- **On gate failure:** Failure of the governing group-held-out separation rule is a terminal no-go. Too few independent groups, fewer than 5 cutoff-clean groups under the earliest-public-provenance rule, or missing defensible hard negatives prohibits go. Do not retune, regroup, redate, or reselect controls after held-out scores are visible.

### S3 — Generate and score the campaign design set

- **Purpose:** Produce candidate designs and score them once against the frozen thresholds.
- **Prerequisites:**
  - S2
- **Outputs:**
  - D-designs; the immutable D-runtime G3 reconciliation snapshot and event-log prefix digest; the stage cost record. The live event stream remains appendable only for S4/G4.
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
  - Accepted immutable D-memo version, final D-runtime event log and reconciliation, and the complete detached manifest.
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
