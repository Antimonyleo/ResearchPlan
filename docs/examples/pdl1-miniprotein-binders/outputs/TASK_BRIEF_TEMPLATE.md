# Bounded work-unit briefs

Campaign: `pdl1-miniprotein-binders`
Content digest: `sha256:4201beff8f1a98084b0d9b8b80ddb4ac490d1443def126eee71540d5ae1401d8`

A local brief may narrow scope but may not weaken the campaign constitution.

## WU-freeze — Produce and freeze D-target plus the pre-canary D-environment under detached digests before any canary attempt, then produce D-g1-canary-results by passing four threshold-independent G1 raw-schema canaries bound to that specification.

- **Authoritative inputs and hashes:**
  - The campaign constitution; RCSB Protein Data Bank; installed software and licences; authoritative APR-compute allocation evidence.
- **Permitted actions:**
  - Retrieve public structural data and verify it against RCSB
  - Install, pin, and digest software, weights, and container images
  - Record APR-compute evidence, scope, available GPU-hours, and exact timezone-aware expiry
  - Write and freeze D-target and the pre-canary D-environment, including the complete four-canary specification and its detached digest
  - Run all four G1 canaries at production settings, binding every attempt to the frozen specification digest, and validate the threshold-independent numeric/semantic predicates, two same-seed replays, and one different-seed result on labelled non-campaign fixtures
  - Write D-g1-canary-results as separate immutable manifests and update the detached manifest without mutating D-environment
- **Prohibited actions:**
  - Generating or scoring any campaign design
  - Applying or implying a filter threshold or decision table at G1
  - Using G1 canary fixtures as scientific controls or campaign results
  - Ordering synthesis, contacting a vendor, or committing any spend
  - Proceeding on an unverified accession, unpinned tool version, or unrecorded allocation expiry
- **Method and tool constraints:** M-target only. Canaries run at exactly the settings S2 and S3 will use; a canary run at reduced settings does not count.
- **Exact outputs:**
  - D-target, immutable pre-canary D-environment, and D-g1-canary-results with four passing manifests including the CAN-pipeline raw fixture table.
- **Verification and acceptance:** G1 evidence is complete: verified target and detached digests, pinned tools and licences, independently verifiable model provenance or an explicit contamination-uncertain fallback that blocks prospective use, exact APR-compute evidence, hard caps and deterministic reserve policy, fixed S3 frame with a worst-case fit proof, and four passing semantic canary manifests. Every canary proves the same pre-score raw-schema/semantic contract with two same-seed replays and one different-seed predicate on labelled non-campaign fixtures without consulting or applying D-thresholds; the independent G1 review record is bound by digest; process exit status alone is insufficient.
- **Resource ceiling:** 60 A100 GPU-hours absolute and two calendar weeks: at most 50 normal first-attempt hours plus the fixed 10-hour S1 retry/reconciliation lane.
- **Retry and failure classes:** Canary attempt state is authorized -> leased -> started -> terminal with terminal status completed, infrastructure_failed, semantic_failed, schema_failed, provenance_failed, interrupted, duplicate_result, or invalid_non_run. attempt_index starts at 1 and max_attempts is 4. Only infrastructure_failed or lease-recovery interrupted may link an identical-input, identical-spec retry, and every retry records its predecessor event_id plus exact D-target, D-environment, fixture, tool, image, schema, criterion, and seed digests. Semantic, schema, provenance, duplicate-result, and invalid-non-run failures are terminal for that attempt; a changed fixture, tool, image, schema, or criterion requires a new frozen version and fresh independent G1 review. The fourth infrastructure failure or unresolved G1 prerequisite dispatches pre_g2_no_run; no S2 authority is granted.
- **Escalation and handoff:** If no PD-1:PD-L1 structure verifies with adequate interface density, a required tool's licence forbids the intended use, allocation evidence or environment remains unverified, a semantic/schema/provenance canary failure cannot be replaced by a new frozen version and fresh G1 review, or the two-week ceiling or typed attempt/reserve ceiling is reached, append the immutable pre_g2_no_run_terminal record and dispatch only WU-decide's no-run closure branch.

## WU-calibrate — Freeze and execute D-control-protocol, close S2 authorization, and reconcile every control batch to one terminal event with zero active. Direct scientific failure then adjudicates terminal nonacceptance without candidate artifacts. Scientific candidate pass alone stages thresholds and compatibility; compatibility determines accepted promotion versus terminal nonacceptance. Every path adjudicates once and grants no S3 authority without APR-G2.

- **Authoritative inputs and hashes:**
  - Accepted G1 and APR-G1 plus exact current digests for the constitution, D-target, D-environment, APR-compute evidence, fixed S3 sampling frame, all four passing G1 canary manifests, and the independent G1 review. WU-freeze completion or stored artifacts alone grant no S2 authority.
  - Peer-reviewed experimental PD-L1 binding literature admitted only through the frozen dual-curation and eligibility rules.
- **Permitted actions:**
  - Freeze and digest epitope and assay-validity eligibility rules before screening
  - Execute and document the exact control census and complete inclusion and exclusion flow
  - Assign each control component once; freeze groups, folds, matching, eligibility, analysis, numeric thresholds, calibration, vetoes, clustering cuts, the total decision table, and the incomplete/expiry no-decision rule outside that table as D-control-protocol before scoring
  - Assign each control component once through two independent pre-score curators; freeze groups, folds, matching, eligibility, analysis, numeric operating-point values, calibration, vetoes, clustering cuts, the total decision table, and the incomplete/expiry no-decision rule as D-control-protocol before scoring; record disagreements and rule-based adjudication, with unresolved records excluded.
  - Run the pre-score finite operating-characteristic calibration or exact/conservative method for the complete estimator and T_control operating point; freeze its finite scenario family, code, seed, replication design, and independent methods review before scoring. Missing or failed calibration supplies no G2 evidence.
  - Compute the frozen per-group estimator, exact lower limit, assay-format and evidence-class sensitivities, influence, heterogeneity, and descriptive pooled analyses
  - On candidate pass before adjudication, fit thresholds by the frozen rule and freeze candidate thresholds as immutable non-authoritative diagnostics with zero S3 authority
  - Apply candidate thresholds to all stored raw canary fixtures only after scientific candidate pass and freeze post-candidate compatibility as pass or fail before adjudication, without APR-G2 or S3 authority
  - Before either G2 outcome, stop new S2 authorization, terminalize every active control batch exactly once, and verify complete authorized-to-terminal accounting with zero active
  - If every frozen criterion and compatibility pass, adjudicate once as accepted, append g2_accepted, issue APR-G2, promote exact unchanged candidate digests, and consume the allocation record to scope S3
  - On direct scientific failure, skip candidate staging and freeze terminal nonacceptance evidence; on compatibility failure, retain staged diagnostics; on adjudicated-invalid failure, record the missing/inconsistent evidence and no candidate paths. In every case append g2_control_failure_terminal_no_go carrying the outcome enum, freeze zero-active G2 reconciliation, prove zero S3 authorization, and authorize only WU-decide's matching failure branch
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
  - Adjudicated-nonaccepted-G2 branch: immutable failure record and zero-active reconciliation are common; terminal_no_go_compatibility_failure retains candidate paths/digests, while terminal_no_go_direct_scientific_failure and terminal_no_go_adjudicated_invalid record both paths absent with no placeholders.
- **Verification and acceptance:** Dispatch first verifies accepted G1, APR-G1, every exact G1 evidence digest, and the independent G1 review record; otherwise WU-calibrate never starts. Exactly one typed G2 outcome is then frozen after S2 authorization closure and complete zero-active reconciliation. D-control-protocol must contain the dual-curation ledger, explicit T_control/T_prod operating-point metrics and decision cells, the independent methods-review record, and an independently reviewed pre-score calibration or exact/conservative method. Direct scientific failure and adjudicated-invalid failure are terminal nonacceptance with candidate paths absent; candidate pass stages non-authoritative diagnostics; compatibility pass permits accepted promotion; pre-adjudication invalid_non_run remains a non-outcome only until its typed correction ceiling closes.
- **Resource ceiling:** 320 A100 GPU-hours absolute and three calendar weeks: at most 300 normal first-attempt hours for control runs, curation, and calibration plus the fixed 20-hour S2 retry/reconciliation lane.
- **Retry and failure classes:** Before G2 adjudication, only infrastructure_failed or lease-recovery interrupted attempts may rerun under the same canonical protocol and all-input digests after predecessor terminalization and partial-output reconciliation; invalid_non_run correction creates a new frozen predecessor and supplies no gate evidence. Semantic, schema, provenance, scientific, duplicate-result, and adjudicated-invalid outcomes are not in-campaign retries. Once G2 is adjudicated, every nonaccepted outcome is terminal no-go and any retry requires a separately identified linked campaign with fresh protocol, provenance, approvals, and no inherited gate, work-unit, compute, or dispatch authorization.
- **Escalation and handoff:** Before G2, quarantine and correct only an invalid_non_run under a new frozen predecessor and the unchanged work-unit/reserve ceiling; it supplies no gate evidence. At G2, ROLE-comp-lead adjudicates once using the explicit outcome enum. If required evidence remains absent, unverifiable, or internally inconsistent after S2 closure, adjudicate terminal_no_go_adjudicated_invalid with candidate paths absent. Every nonaccepted outcome freezes terminal control-failure no-go and may not be repaired or rerun in this campaign. Any retry is a new linked campaign with fresh approvals and no inherited authorization.
- **Depends on work units:**
  - WU-freeze

## WU-generate — Generate and score exactly the frozen S3 frame once against the frozen thresholds, with complete provenance, typed slot/attempt accounting, deterministic partial-batch reconciliation, and no adaptive extension.

- **Authoritative inputs and hashes:**
  - Accepted G2 and APR-G2 plus exact promoted authoritative D-thresholds and D-canary-compat paths and digests, the unchanged canonical D-control-protocol digest, explicit constitution, D-target, D-environment, APR-compute, fixed-frame, separate generation/scoring/overhead cost-proof and ledger digests, and zero-active predecessor digests, fixed-frame capacity and expiry, and proof that no same-input-and-seed batch is nonterminal. Candidate diagnostics, aggregate fit without subcap fit, and WU-calibrate completion grant no S3 authority.
- **Permitted actions:**
  - Through the single dispatcher, verify separate projected generation and scoring costs against their remaining subledgers, append an authorized batch event carrying the complete S3 dependency- and subledger-digest map before compute, acquire a durable lease, then append started and exactly one completed, failed, or interrupted terminal event
  - Generate backbones and design sequences only for the preauthorized fixed-frame slots, within frozen parameters, seed schedule, deduplication/quality rules, hard cap, reserve, and expiry.
  - Predict complexes and compute interface and liability terms at frozen settings
  - Apply the frozen thresholds once and record pass/fail per filter
  - Cluster survivors at all three declared cuts and report K_clusters, N_frame, the cluster-corrected yield fraction, and its predeclared uncertainty; failed, invalid, duplicate, and missing slots remain accounted for in N_frame.
  - Record immutable slot_attempt_id, slot_id, attempt_index, result identity, seeds, manifests, output digests, timestamps, actor, typed status, lease transitions, and per-attempt/per-slot cost
  - Reconcile a failed or interrupted batch by preserving every valid partial slot result, selecting the lowest attempt_index then event-sequence valid result per slot, rejecting duplicate result identities without overwrite, and terminalizing unresolved slots explicitly; charge every attempt once to the normal stage or authorized reserve ledger
  - Generate and digest the immutable g3_accepted reconciliation only when every N_frame slot is scored; otherwise append g3_not_accepted and digest the immutable G3 non-acceptance reconciliation while leaving the event stream open only for S4/G4
  - If completion becomes impossible within the normal resource ceiling, fixed reserve lane, or frozen expiry, stop new authorization, terminalize every active batch, slot, and lease, append g3_not_accepted, and digest the immutable G3 non-acceptance reconciliation while leaving the stream open only for S4/G4
- **Prohibited actions:**
  - Changing any value in D-thresholds
  - Rescoring a design under different thresholds to improve its rank
  - Dropping designs that score below the negative control distribution
  - Reporting raw pass count without cluster count
  - Ordering synthesis, contacting a vendor, or committing any spend
  - Consuming compute for a batch whose manifest, dependency-digest map, and lease have not already been appended to the event log
  - Authorizing a linked retry before its predecessor has exactly one infrastructure_failed or interrupted terminal event, its partial outputs and slots are reconciled, its lease is released, or while any batch with the same frozen inputs and seed remains nonterminal
  - Overwriting a canonical slot result, accepting a duplicate result identity, dropping a failed/invalid/duplicate/missing/quality-excluded slot, or changing N_frame
- **Method and tool constraints:** M-generate and M-score, at exactly the settings the controls were scored under. Any post-G2 change to a threshold, setting, frame, denominator, or uncertainty rule is prohibited in this campaign: stop authorization, preserve evidence, and open a new linked campaign rather than treating changed outputs as a deviation branch.
- **Exact outputs:**
  - On completion, D-designs with cluster assignments and full provenance; on incomplete/expiry, `deliverables/ranked-designs.partial.csv` and all other available partial S3 artifacts retained and labelled non-decision evidence.
  - D-runtime G3 reconciliation snapshot at `deliverables/runtime-g3-reconciliation.md`, with the exact prefix length and digest for `artifacts/runtime/events.ndjson` and status accepted_complete or not_accepted.
- **Verification and acceptance:** Each authorization event first verifies the complete S3 dependency closure: accepted G2, APR-G2, the exact promoted authoritative D-thresholds and D-canary-compat digests, the unchanged canonical protocol digest, explicit constitution/D-target/D-environment/APR-compute/fixed-frame/zero-active predecessor digests, separate generation/scoring/overhead cost-proof and ledger digests, fixed-frame capacity and expiry, and no competing same-input-and-seed batch. Projected work must independently fit the remaining 1,200-hour M-generate, 400-hour M-score, and aggregate 1,600-hour normal S3 ledgers. WU-generate and G3 are accepted only when every fixed-frame slot has one canonical scored result; terminal accounting alone is sufficient only for the explicit g3_not_accepted branch. Evidence includes typed slot/attempt reconciliation, complete D-designs, N_frame, K_clusters, predeclared uncertainty, separate subledger and reserve costs, and an immutable G3 reconciliation. A terminal incomplete/expired reconciliation records WU-generate and G3 as not accepted and enables only WU-decide's no-decision branch.
- **Resource ceiling:** 1,620 A100 GPU-hours absolute and five calendar weeks: at most 1,200 normal M-generate hours and 400 normal M-score hours for the fixed S3 frame, with no transfer between subledgers, plus only the fixed 20-hour S3 retry/reconciliation lane under its frozen per-purpose allocation. The lane cannot add production slots or enlarge N_frame.
- **Retry and failure classes:** A batch/slot attempt has one typed terminal status. While holding the exclusive recovery lock, the dispatcher must terminalize infrastructure_failed or lease-recovery interrupted predecessors, persist and reconcile partial slot outputs, release the lease, and verify that no batch with the same frozen inputs and seed remains nonterminal before authorizing one linked retry under a new batch/attempt ID with identical inputs and seed. The retry may preserve successful canonical slots and cannot enlarge N_frame; unresolved slots become explicit terminal statuses at the ceiling. A completed batch is never dispatched again, concurrent duplicate retry is rejected, duplicate result identities are rejected without overwrite, every retry predecessor and digest is retained, and a design is never rescored to improve its result.
- **Escalation and handoff:** At exactly 800 GPU-hours on the normal S3 ledger and after each later batch, compare declared worst-case remaining generation, scoring, and batch-overhead cost separately with the remaining M-generate 1,200-hour ledger, M-score 400-hour ledger, aggregate normal S3 capacity, and time to exact expiry. Escalate to ROLE-pi when any inequality fails; no subledger transfer is allowed. If the complete set cannot finish within every subcap, the aggregate cap, fixed reserve lane, or frozen expiry, execute the terminal incomplete/expired reconciliation and no-decision path; do not accept G3 or seek permission to run the table on partial results.
- **Depends on work units:**
  - WU-calibrate

## WU-decide — Finalize the exact eligible decision branch, freeze D-memo and handoff, obtain ROLE-pi's digest-bound APR-G4, append exactly one matching G4 event as the last log line, then idempotently hash and finalize reconciliation plus manifest. If interrupted after the event, resume only finalization; mark permanent closure only after verification.

- **Authoritative inputs and hashes:**
  - Common: explicit constitution, D-target, D-environment, APR-compute, canonical D-control-protocol when applicable, and independent-review digests from the G4 dependency closure.
  - Ordinary branch: accepted G2, APR-G2, exact promoted authoritative D-thresholds and D-canary-compat paths and digests, accepted G3, APR-G3, complete D-designs path and digest, and immutable accepted_complete G3 reconciliation path and digest.
  - G3-nonacceptance no-decision branch: accepted G2, APR-G2, exact promoted authoritative D-thresholds and D-canary-compat paths and digests, g3_not_accepted event and typed reason, immutable terminal G3 reconciliation path and digest, absent APR-G3, terminal accounting, and every available S3 evidence path and digest labelled non-decision.
  - Failed-G2 branch: one typed terminal G2 outcome, immutable `deliverables/control-failure.json` path and digest, zero-active G2 reconciliation path and digest, absent APR-G2/APR-G3, and zero S3 authorization; compatibility failure additionally requires retained candidate paths/digests, while direct scientific failure and adjudicated-invalid failure require the failure record's explicit candidate-path absence attestation.
  - Pre-G2 no-run branch: immutable `deliverables/pre-g2-no-run.json` and `deliverables/runtime-pre-g2-no-run-reconciliation.md` paths and digests, no G1/G2/APR-G2/APR-G3/S3 authority, and no candidate artifacts or ordinary recommendation.
  - Internal handoff branch evidence: `deliverables/internal-handoff.json` with identified institutional recipient, access-controlled storage, transfer event, package digest, and explicit no-export/no-sequence condition.
  - Branch acceptance evidence: immutable ROLE-pi-signed APR-G4 record binding the campaign id, exact branch, D-memo digest, internal-handoff digest, approver identity, decision, and timestamp; it must predate and be named by the sole G4 event.
  - Closure recovery: sole last-line G4 event and unchanged frozen bytes.
- **Permitted actions:**
  - For the ordinary branch, verify and consume accepted G2, APR-G2, exact promoted D-thresholds/D-canary-compat digests, accepted G3, APR-G3, complete D-designs digest, and accepted_complete G3 reconciliation digest before applying the frozen table
  - For G3-nonacceptance no-decision, verify and consume accepted G2, APR-G2, exact promoted D-thresholds/D-canary-compat digests, g3_not_accepted with one typed reason, terminal G3 reconciliation digest, absent APR-G3, terminal accounting, and every available S3 evidence path/digest labelled non-decision; do not run the table or claim a cell/recommendation
  - After failed G2, consume the common immutable failure record and zero-active reconciliation plus its typed g2_outcome; additionally consume retained candidate paths/digests for compatibility failure or explicit candidate-path absence for direct scientific or adjudicated-invalid failure; then write terminal no-go without APR-G3, G3, or an ordinary cell
  - After pre-G2 failure, consume the immutable no-run record and reconciliation, write terminal no-run without a gate result or recommendation, and do not manufacture G2 or candidate evidence
  - Write the memo leading with the branch outcome and least favourable defensible reading, referencing only the corresponding immutable G2 or G3 runtime snapshot
  - Create and verify the internal-only handoff record and append internal_handoff_recorded before G4; freeze the memo candidate and its detached digest; present the exact branch and both digests to ROLE-pi; obtain immutable APR-G4 binding them; then have the dispatcher verify that approval under the append lock and append exactly one matching G4 decision_accepted, no_decision_accepted, control_failure_no_go_accepted, or no_run_accepted event naming all three digests as the last complete line, append-seal the stream, and enter closure_in_progress
  - During initial finalization or resumed closure_in_progress, verify that sole event and no later bytes, compute the unchanged log digest, and atomically create or verify deterministic final reconciliation and manifest entries without appending or changing frozen artifacts
  - Mark permanently_closed only after final reconciliation, manifest finalization, and internal-only handoff verification succeed, then retain sequences only in access-controlled institutional storage; any redacted package contains no design sequence and no outbound transfer is authorized
- **Prohibited actions:**
  - Stating a recommendation other than the cell mechanically reached
  - Stating or implying that any design binds PD-L1
  - Omitting the ranked table from an ordinary accepted-G2 no-go memo, or requiring a ranked table on the adjudicated-nonaccepted-G2 control-failure branch
  - Presenting a principal-investigator override as the table's output
  - Ordering synthesis or authorizing wet-lab work
  - Signing APR-G4 as ROLE-methods, appending G4 before ROLE-pi's matching digest-bound APR-G4 exists, or accepting an approval for a different branch, memo, or handoff
  - Running the ordinary decision table after any G3 nonacceptance or adjudicated nonaccepted G2; claiming a cell or recommendation in a no-decision or pre-G2 no-run memo; treating g3_not_accepted as accepted; reopening S3/go authorization from the control-failure branch; or exporting a package containing a design sequence
- **Method and tool constraints:** M-decide only. The ordinary table is applied exactly once only after accepted G2 and G3. It is not applied after any typed G3 nonacceptance or adjudicated nonaccepted G2.
- **Exact outputs:**
  - Accepted immutable D-memo version, D-runtime final reconciliation, complete event log through G4, and detached manifest.
- **Verification and acceptance:** Exactly one branch is accepted at G4 with an immutable D-memo, immutable internal handoff, ROLE-pi-signed APR-G4 binding their exact digests and branch, and one matching G4 event as the last complete log line: ordinary decision, accepted-G2 G3-nonacceptance no-decision, terminal G2 control-failure no-go, or pre-G2 no-run. The dispatcher rejects the event unless APR-G4 predates it and matches byte-for-byte. That event enters closure_in_progress and append-seals the stream; it does not by itself establish permanent closure. Acceptance completes only when deterministic final reconciliation and detached manifest verify the unchanged event-log digest. A resumed closure may only perform or verify those idempotent finalization steps, never append or change frozen artifacts.
- **Resource ceiling:** 0 GPU-hours and two calendar weeks.
- **Retry and failure classes:** A candidate memo may be rewritten only before the sole G4 event and only when consumed evidence and the branch are byte-identical. After G2, every substantive input change requires a new linked campaign; after G4 no memo or frozen artifact may change and no event may append. If closure is interrupted, the same closure_in_progress operation may idempotently compute or verify only final reconciliation, manifest, and already-recorded internal handoff entries from unchanged bytes. After they verify, permanent closure permits no correction or successor memo; any correction requires a new linked campaign.
- **Escalation and handoff:** Escalate to ROLE-pi if the memo's author believes the table cell is wrong — as an override request on the record, never as a rewritten recommendation.
- **Depends on work units:**
  - WU-freeze
