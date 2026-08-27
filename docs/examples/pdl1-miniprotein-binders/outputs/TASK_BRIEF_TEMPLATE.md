# Bounded work-unit briefs

Campaign: `pdl1-miniprotein-binders`
Content digest: `sha256:5027fd0be0557eb8d85df05f7cfaf0b401cb53b8d44e921242fd400e48948c39`

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
- **Verification and acceptance:** G1 evidence is complete: verified target and detached digests, pinned tools and licences, independently verifiable model provenance or an explicit contamination-uncertain fallback that blocks prospective use, exact APR-compute evidence, hard caps and reserve, fixed S3 frame, and four passing semantic canary manifests. Every canary proves deterministic raw-schema transport on labelled non-campaign fixtures without consulting or applying D-thresholds; process exit status alone is insufficient.
- **Resource ceiling:** 50 A100 GPU-hours and two calendar weeks.
- **Retry and failure classes:** A failed canary may be fixed and rerun without escalation up to three times; the fourth failure escalates to ROLE-pi.
- **Escalation and handoff:** Escalate to ROLE-pi if no PD-1:PD-L1 structure verifies with adequate interface density, if a required tool's licence forbids the intended use, or if the two-week ceiling is reached.

## WU-calibrate — Freeze and execute D-control-protocol, close S2 authorization, and reconcile every control batch to one terminal event with zero active. Direct scientific failure then adjudicates terminal nonacceptance without candidate artifacts. Scientific candidate pass alone stages thresholds and compatibility; compatibility determines accepted promotion versus terminal nonacceptance. Every path adjudicates once and grants no S3 authority without APR-G2.

- **Authoritative inputs and hashes:**
  - Accepted G1 and APR-G1 plus exact current digests for the constitution, D-target, D-environment, APR-compute evidence, fixed S3 sampling frame, and all four passing G1 canary manifests. WU-freeze completion or stored artifacts alone grant no S2 authority.
  - Peer-reviewed experimental PD-L1 binding literature admitted only through the frozen dual-curation and eligibility rules.
- **Permitted actions:**
  - Freeze and digest epitope and assay-validity eligibility rules before screening
  - Execute and document the exact control census and complete inclusion and exclusion flow
  - Assign each control component once; freeze groups, folds, matching, eligibility, analysis, numeric thresholds, calibration, vetoes, clustering cuts, the total decision table, and the incomplete/expiry no-decision rule outside that table as D-control-protocol before scoring
  - Assign each control component once through two independent pre-score curators; freeze groups, folds, matching, eligibility, analysis, numeric operating-point values, calibration, vetoes, clustering cuts, the total decision table, and the incomplete/expiry no-decision rule as D-control-protocol before scoring; record disagreements and rule-based adjudication, with unresolved records excluded.
  - Run the pre-score finite operating-characteristic calibration or exact/conservative method for the complete estimator and T_control operating point; freeze its finite scenario family, code, seed, replication design, and independent methods review before scoring. Missing or failed calibration supplies no G2 evidence.
  - Compute the frozen per-group estimator, exact lower limit, assay-format and evidence-class sensitivities, influence, heterogeneity, and descriptive pooled analyses
  - On candidate pass before adjudication, fit thresholds by the frozen rule and freeze candidate thresholds as immutable non-authoritative diagnostics with zero S3 authority
  - Apply candidate thresholds to all stored raw canary fixtures and freeze candidate compatibility as pass or fail before adjudication, without APR-G2 or S3 authority
  - Before either G2 outcome, stop new S2 authorization, terminalize every active control batch exactly once, and verify complete authorized-to-terminal accounting with zero active
  - If every frozen criterion and compatibility pass, adjudicate once as accepted, append g2_accepted, issue APR-G2, promote exact unchanged candidate digests, and consume the allocation record to scope S3
  - On direct scientific failure, skip candidate staging and freeze terminal nonacceptance evidence; on compatibility failure, retain staged diagnostics. In either case append g2_control_failure_terminal_no_go, freeze zero-active G2 reconciliation, prove zero S3 authorization, and authorize only WU-decide's failure branch
- **Prohibited actions:**
  - Creating or authorizing any control score before the canonical final-protocol.json D-control-protocol digest exists
  - Changing eligibility, census membership, groups, folds, assignments, analysis, numeric thresholds, vetoes, clustering cuts, or decision cells after any score is visible
  - Using an off-epitope positive, an under-sensitive or assay-incompatible NE1/NE2 label, or a negative component in more than one governing stratum
  - Calling an uncalibrated bootstrap limit a confidence bound or allowing a descriptive limit to enter a go cell
  - Treating candidate thresholds or compatibility as authoritative, or generating or scoring campaign designs, creating D-designs or a ranked table, reaching G3, or applying the ordinary decision table without accepted G2 and APR-G2
  - Using held-out scores to alter that fold's filters, weights, transformation, or inputs
  - Reporting individual-positive holdout, resubstitution, observation-pooled, NE3, or NE4 performance as governing decision evidence
  - Hand-building matched negatives outside the frozen rule
  - Ordering synthesis or committing spend
- **Method and tool constraints:** M-controls only, at the exact settings recorded in D-environment.
- **Exact outputs:**
  - D-control-protocol with immutable eligibility-rules and final pre-score protocol components, final-protocol.json binding the exact eligibility-rules digest, and its own exact-byte detached SHA-256 as the canonical deliverable digest.
  - Candidate-pass staging: immutable non-authoritative threshold and canary-compatibility diagnostics with matching canonical protocol and fixture digests and zero S3 authority.
  - Accepted-G2 branch only: APR-G2 promotion records binding the exact unchanged candidate digests as authoritative D-thresholds and D-canary-compat.
  - Adjudicated-nonaccepted-G2 branch: immutable failure record and zero-active reconciliation are common; compatibility failure retains candidate paths/digests, while direct scientific failure records both paths absent.
- **Verification and acceptance:** Dispatch first verifies accepted G1, APR-G1, and every exact G1 evidence digest; otherwise WU-calibrate never starts. Exactly one G2 outcome is then frozen after S2 authorization closure and complete zero-active reconciliation. D-control-protocol must contain the dual-curation ledger, explicit T_control operating-point metrics and decision cells, and an independently reviewed pre-score calibration or exact/conservative method. Direct scientific failure is terminal nonacceptance with candidate paths absent; candidate pass stages non-authoritative diagnostics; compatibility pass permits accepted promotion; invalid non-runs remain non-outcomes.
- **Resource ceiling:** 300 A100 GPU-hours hard cap and three calendar weeks, including control runs, dual curation, calibration, and permitted infrastructure reruns.
- **Retry and failure classes:** Before G2 adjudication, an invalid infrastructure non-run may rerun identically under the same canonical protocol digest and unchanged ceiling; it supplies no gate outcome. Once G2 is adjudicated, every nonaccepted outcome is terminal no-go and no in-campaign control retry or protocol revision is permitted. Any retry requires a separately identified linked campaign with fresh approvals and no inherited gate, work-unit, compute, or dispatch authorization.
- **Escalation and handoff:** Before G2, quarantine and correct an invalid non-run within the unchanged work-unit ceiling; it supplies no gate evidence. At G2, ROLE-comp-lead adjudicates once. Every nonaccepted outcome, including one whose frozen diagnostic cell says revise, freezes terminal control-failure no-go and may not be repaired or rerun in this campaign. Any retry is a new linked campaign with fresh approvals and no inherited authorization.
- **Depends on work units:**
  - WU-freeze

## WU-generate — Generate and score exactly the frozen S3 frame once against the frozen thresholds, with complete provenance, slot accounting, and no adaptive extension.

- **Authoritative inputs and hashes:**
  - Accepted G2 and APR-G2 plus exact promoted authoritative D-thresholds and D-canary-compat paths and digests, the unchanged canonical D-control-protocol digest, frozen D-target and D-environment digests, fixed-frame capacity and expiry, and proof that no same-input-and-seed batch is nonterminal. Candidate diagnostics and WU-calibrate completion grant no S3 authority.
- **Permitted actions:**
  - Through the single dispatcher, append an authorized batch event carrying the canonical D-control-protocol digest before compute, then started and exactly one completed, failed, or interrupted terminal event
  - Generate backbones and design sequences only for the preauthorized fixed-frame slots, within frozen parameters, seed schedule, deduplication/quality rules, hard cap, reserve, and expiry.
  - Predict complexes and compute interface and liability terms at frozen settings
  - Apply the frozen thresholds once and record pass/fail per filter
  - Cluster survivors at all three declared cuts and report K_clusters, N_frame, the cluster-corrected yield fraction, and its predeclared uncertainty; failed, invalid, duplicate, and missing slots remain accounted for in N_frame.
  - Record seeds, manifests, output digests, timestamps, actor, status, and per-design cost
  - Generate and digest the immutable accepted-complete G3 reconciliation snapshot while leaving the event stream open only for S4/G4
  - If completion becomes impossible within the resource ceiling or frozen expiry, stop new authorization, terminalize every active batch, append incomplete_or_expired, and digest the immutable G3 non-acceptance reconciliation while leaving the stream open only for S4/G4
- **Prohibited actions:**
  - Changing any value in D-thresholds
  - Rescoring a design under different thresholds to improve its rank
  - Dropping designs that score below the negative control distribution
  - Reporting raw pass count without cluster count
  - Ordering synthesis, contacting a vendor, or committing any spend
  - Consuming compute for a batch whose manifest has not already been appended to the event log
  - Authorizing a linked retry before its predecessor has exactly one failed or interrupted terminal event, or while any batch with the same frozen inputs and seed remains nonterminal
- **Method and tool constraints:** M-generate and M-score, at exactly the settings the controls were scored under. Any post-G2 change to a threshold, setting, frame, denominator, or uncertainty rule is prohibited in this campaign: stop authorization, preserve evidence, and open a new linked campaign rather than treating changed outputs as a deviation branch.
- **Exact outputs:**
  - On completion, D-designs with cluster assignments and full provenance; on incomplete/expiry, `deliverables/ranked-designs.partial.csv` and all other available partial S3 artifacts retained and labelled non-decision evidence.
  - D-runtime G3 reconciliation snapshot at `deliverables/runtime-g3-reconciliation.md`, with the exact prefix length and digest for `artifacts/runtime/events.ndjson` and status accepted_complete or not_accepted_incomplete_or_expired.
- **Verification and acceptance:** Each authorization event first verifies accepted G2, APR-G2, the exact promoted authoritative D-thresholds and D-canary-compat digests, the unchanged canonical protocol digest, fixed-frame capacity and expiry, and no competing same-input-and-seed batch. WU-generate and G3 are accepted only when every fixed-frame slot is complete or terminally accounted for, evidence includes complete D-designs, N_frame, K_clusters, predeclared uncertainty, hard-cap costs, and an immutable accepted-complete G3 reconciliation. A terminal incomplete/expired reconciliation records WU-generate and G3 as not accepted and enables only WU-decide's no-decision branch.
- **Resource ceiling:** 1,600 A100 GPU-hours hard cap and five calendar weeks; 50 GPU-hours is a shared contingency reserve, not additional S3 capacity.
- **Retry and failure classes:** An infrastructure failure ends with exactly one failed or interrupted terminal event. While holding the exclusive append lock, the dispatcher must make that predecessor terminal and verify that no batch with the same frozen inputs and seed remains nonterminal before authorizing one linked retry under a new batch ID with identical inputs and seed. A completed batch is never dispatched again, concurrent duplicate retry is rejected, and a design is never rescored to improve its result.
- **Escalation and handoff:** Escalate to ROLE-pi at the 800 GPU-hour checkpoint if spend is far below pace with design branches unexplored. If the complete set cannot finish by the resource ceiling or frozen allocation expiry, execute the terminal incomplete/expired reconciliation and no-decision path; do not accept G3 or seek permission to run the table on partial results.
- **Depends on work units:**
  - WU-calibrate

## WU-decide — Finalize the exact eligible decision branch, freeze D-memo, append exactly one matching G4 event as the last log line, then idempotently hash and finalize reconciliation plus manifest. If interrupted after the event, resume only finalization; mark permanent closure only after verification.

- **Authoritative inputs and hashes:**
  - Common: constitution and canonical D-control-protocol digest.
  - Ordinary branch: accepted G2, APR-G2, exact promoted authoritative D-thresholds and D-canary-compat paths and digests, accepted G3, APR-G3, complete D-designs path and digest, and immutable accepted_complete G3 reconciliation path and digest.
  - Incomplete/expiry no-decision branch: accepted G2, APR-G2, exact promoted authoritative D-thresholds and D-canary-compat paths and digests, immutable terminal not_accepted_incomplete_or_expired G3 reconciliation path and digest, absent APR-G3, and every retained partial S3 evidence path and digest.
  - Failed-G2 branch: terminal G2 nonacceptance, immutable `deliverables/control-failure.json` path and digest, zero-active G2 reconciliation path and digest, absent APR-G2/APR-G3, and zero S3 authorization; compatibility failure additionally requires retained candidate paths/digests, while direct scientific failure requires the failure record's explicit candidate-path absence attestation.
  - Closure recovery: sole last-line G4 event and unchanged frozen bytes.
- **Permitted actions:**
  - For the ordinary branch, verify and consume accepted G2, APR-G2, exact promoted D-thresholds/D-canary-compat digests, accepted G3, APR-G3, complete D-designs digest, and accepted_complete G3 reconciliation digest before applying the frozen table
  - For incomplete/expiry no-decision, verify and consume accepted G2, APR-G2, exact promoted D-thresholds/D-canary-compat digests, terminal not_accepted_incomplete_or_expired G3 reconciliation digest, absent APR-G3, and every retained partial S3 evidence path/digest; do not run the table or claim a cell/recommendation
  - After failed G2, consume the common immutable failure record and zero-active reconciliation; additionally consume retained candidate paths/digests for compatibility failure or explicit candidate-path absence for direct scientific failure; then write terminal no-go without APR-G3, G3, or an ordinary cell
  - Write the memo leading with the branch outcome and least favourable defensible reading, referencing only the corresponding immutable G2 or G3 runtime snapshot
  - Freeze the memo candidate and its detached digest, append exactly one matching G4 decision_accepted, no_decision_accepted, or control_failure_no_go_accepted event naming both as the last complete line, append-seal the stream, and enter closure_in_progress
  - During initial finalization or resumed closure_in_progress, verify that sole event and no later bytes, compute the unchanged log digest, and atomically create or verify deterministic final reconciliation and manifest entries without appending or changing frozen artifacts
  - Mark permanently_closed only after final reconciliation and manifest finalization verify, then package the detached manifest
- **Prohibited actions:**
  - Stating a recommendation other than the cell mechanically reached
  - Stating or implying that any design binds PD-L1
  - Omitting the ranked table from an ordinary accepted-G2 no-go memo, or requiring a ranked table on the adjudicated-nonaccepted-G2 control-failure branch
  - Presenting a principal-investigator override as the table's output
  - Ordering synthesis or authorizing wet-lab work
  - Running the ordinary decision table on a partially scored design set or after adjudicated nonaccepted G2; claiming a cell or recommendation in a no-decision memo; treating terminal incomplete/expired G3 as accepted; or reopening S3/go authorization from the control-failure branch
- **Method and tool constraints:** M-decide only. The ordinary table is applied exactly once only after accepted G2 and G3. It is not applied after terminal incomplete/expired G3 or adjudicated nonaccepted G2.
- **Exact outputs:**
  - Accepted immutable D-memo version, D-runtime final reconciliation, complete event log through G4, and detached manifest.
- **Verification and acceptance:** Exactly one branch is accepted at G4 with an immutable D-memo and one matching G4 event as the last complete log line. That event enters closure_in_progress and append-seals the stream; it does not by itself establish permanent closure. Acceptance completes only when deterministic final reconciliation and detached manifest entries verify the unchanged event-log digest. A resumed closure may only perform or verify those idempotent finalization steps, never append or change frozen artifacts.
- **Resource ceiling:** 0 GPU-hours and two calendar weeks.
- **Retry and failure classes:** A candidate memo may be rewritten only before the sole G4 event. After that event, no memo or frozen artifact may change and no event may append. If closure is interrupted, the same closure_in_progress operation may idempotently compute or verify only final reconciliation and manifest entries from unchanged bytes. After they verify, permanent closure permits no correction or successor memo; any correction requires a new linked campaign.
- **Escalation and handoff:** Escalate to ROLE-pi if the memo's author believes the table cell is wrong — as an override request on the record, never as a rewritten recommendation.
- **Depends on work units:**
  - WU-freeze
