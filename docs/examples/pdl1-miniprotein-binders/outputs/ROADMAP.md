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
  - The target, environment, model provenance, exact allocation evidence, fixed S3 frame, and complete canary specification are frozen and independently checked; all four G1 canaries pass their semantic production-setting checks, raw schemas, and deterministic replays on labelled non-campaign fixtures; missing inputs, unverifiable provenance, missing tolerances, or a process-only canary pass fails G1. No threshold table is applied at G1.
- **On gate failure:** S2 does not start and no allocation beyond the S1 cap is consumed when any target, environment, allocation, model-provenance, sampling-frame, or canary requirement is missing or unverifiable. An allocation assertion is not evidence; an affected model may be used only for descriptive diagnostics under the provenance fallback and cannot authorize G2 or spend. A failed canary is fixed and rerun under the declared retry cap; the fourth failure escalates to ROLE-pi.

### S2 — Calibrate on controls and freeze the thresholds

- **Purpose:** Freeze and execute the control protocol, close and fully reconcile S2 batches, then branch before the one G2 adjudication. Direct scientific failure skips candidate artifacts and terminates no-go. Scientific candidate pass alone stages thresholds then compatibility; pass permits APR-G2 promotion and failure terminates no-go with diagnostics retained. Every nonaccepted branch has zero S3 authority.
- **Prerequisites:**
  - S1
- **Outputs:**
  - D-control-protocol, with eligibility rules frozen before screening, final-protocol.json binding the eligibility-rules digest, and the final file's exact-byte SHA-256 serving as the sole canonical deliverable digest before scoring.
  - Pre-adjudication candidate-pass only: immutable non-authoritative candidate threshold and candidate canary-compatibility diagnostics with detached digests and explicit zero S3 authority.
  - Accepted G2 only: APR-G2 promotion records binding the exact unchanged candidate digests as authoritative D-thresholds and D-canary-compat, plus the allocation-bound S3 capacity calculation.
  - Adjudicated nonaccepted G2: immutable failure record and zero-active reconciliation are common; compatibility failure retains candidate paths/digests, while direct scientific failure records both paths absent. APR-G2/APR-G3 and S3 authority are absent.
- **Owner:** ROLE-methods
- **Budget:** 300 A100 GPU-hours; approximately two weeks.
- **Expected pace:** Two weeks. Under-spend here is not a saving: an under-powered control set weakens every downstream claim.
- **Gate G2:** 
  - G2 is adjudicated exactly once only after D-control-protocol predates every score, its numeric operating point and complete decision table are explicit, dual curation and independent calibration evidence are complete, all control analyses report T_control coverage and false-go at the same point used for designs, S2 authorization is stopped, and complete authorized-to-terminal accounting proves one terminal event per control batch with zero active. A direct scientific failure is terminal nonacceptance with candidate paths absent; only a scientific candidate pass stages non-authoritative candidate thresholds and compatibility; compatibility pass permits accepted G2 and APR-G2; every nonaccepted branch has zero S3 authority.
- **On gate failure:** This is the authoritative control-gate outcome map. Before adjudication, an invalid non-run may be corrected and supplies no gate result. The dispatcher then closes S2 authorization, terminalizes every active control batch exactly once, and verifies complete zero-active accounting. ROLE-comp-lead adjudicates G2 exactly once: direct scientific failure is terminal_no_go with candidate thresholds/compatibility absent; scientific candidate pass alone stages both diagnostics, and compatibility failure is terminal_no_go with them retained. Every nonaccepted branch freezes `deliverables/control-failure.json` and the zero-active G2 reconciliation, appends g2_control_failure_terminal_no_go, omits APR-G2/APR-G3 and authoritative D-thresholds/D-canary-compat, grants zero S3 authority, and authorizes only WU-decide's no-go branch. Any retry is a new linked campaign with no inherited authorization.

### S3 — Generate and score the campaign design set

- **Purpose:** Produce candidate designs and score the complete set once against the frozen thresholds, or terminalize fail-closed without G3 acceptance if the complete set cannot finish within the frozen resource or expiry limit.
- **Prerequisites:**
  - S2
- **Outputs:**
  - On completion: D-designs, stage cost record, and immutable accepted-complete D-runtime G3 reconciliation. On incomplete/expiry: `deliverables/ranked-designs.partial.csv` plus any other available partial S3 artifacts labelled non-decision evidence, stage cost record, and immutable not-accepted-incomplete/expired D-runtime G3 reconciliation. The live event stream remains appendable only for S4/G4.
- **Owner:** ROLE-comp-lead
- **Budget:** 1,600 A100 GPU-hours hard cap for S3 (M-generate 1,200 plus M-score 400); no adaptive extension. The 50-hour reserve is contingency only and is not additional production capacity.
- **Expected pace:** Four weeks, with a mid-stage checkpoint at 800 GPU-hours. The checkpoint compares completed slots and remaining N_frame against the hard cap and expiry; unexplored branches or under-spend do not permit adaptive sampling. If the fixed frame cannot complete, execute the terminal no-decision branch.
- **Gate G3:** 
  - G3 is reachable and accepted only after accepted G2 and APR-G2, when every slot in the fixed S3 frame has been scored or terminally accounted for exactly once against unchanged D-thresholds with complete provenance, N_frame and K_clusters are reported under the frozen denominator and uncertainty rule, no active batch remains, and no post-hoc threshold, frame, denominator, or extension change occurred. Incomplete or expired S3 is G3 not accepted and can lead only to no-decision. Adjudicated nonaccepted G2 prohibits G3 entirely.
- **On gate failure:** A post-G2 change to D-thresholds, the S3 frame, denominator, or uncertainty rule is prohibited: stop new authorization, preserve all evidence under the producing digest, and require a new linked campaign with fresh review and authority. This campaign cannot apply the ordinary table or close through an invented deviation branch. If the complete unchanged frame cannot finish within the hard S3 cap, reserved contingency, or frozen allocation expiry, stop new authorization, terminalize every nonterminal slot/batch, append incomplete_or_expired, freeze the G3 non-acceptance reconciliation with N_frame accounting, and record G3 not accepted; this enables only WU-decide's no-decision branch and never satisfies APR-G3.

### S4 — Decide and hand off

- **Purpose:** Finalize exactly one decision branch, append-seal the log after its sole G4 event, and idempotently finish reconciliation and manifest finalization. Closure-in-progress recovery may complete only those deterministic writes; permanent campaign closure begins after they verify.
- **Prerequisites:**
  - S2
- **Outputs:**
  - Accepted immutable D-memo version, append-sealed event log ending in exactly one matching G4 event, deterministic final D-runtime reconciliation, complete detached manifest, and permanently_closed state.
- **Owner:** ROLE-methods
- **Budget:** 0 GPU-hours; approximately one week of writing.
- **Expected pace:** One week.
- **Gate G4:** 
  - After accepted G2 and G3, the recommendation is the ordinary cell mechanically reached on the frozen decision table. After accepted G2 but terminal incomplete/expired G3, the outcome is no-decision outside that table. After adjudicated nonaccepted G2, the outcome is terminal control-failure no-go bound to the complete control-failure record and zero-active G2 reconciliation. Every branch freezes one D-memo, appends exactly one matching G4 event as the last log line, completes idempotent closure reconciliation and manifest finalization, and only then becomes permanently closed.
- **On gate failure:** Return a branch-mismatched memo, a nonaccepted-G2 memo that treats candidate diagnostics as authoritative, or any result implying unauthorized G3/go. After the sole G4 event, later log bytes, a second G4 event, frozen-artifact mutation, or mismatched finalization fail closed. An interruption with that valid event last and no later bytes resumes only idempotent closure finalization; a PI override cannot reopen S3.

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
  - Per tool: identity, release tag, weight-file digest, container image digest, licence and licence-compatibility determination. For each learned model also record an independently verifiable training-data cutoff, update history, private/licensed/pre-release-data treatment, source or signed model-card evidence, and provenance-manifest digest. A public release or sequence-availability date alone is insufficient; unverifiable provenance is contamination-uncertain and cannot support prospective G2 or spend.
  - Exact invocation, flags, template and MSA policy, and seed policy for each tool
  - Generation parameters: length range, topology constraints, and batch size; plus the fixed S3 sampling frame with exact batch and slot counts, seed schedule, total authorized slots N_frame, deterministic duplicate and quality-exclusion rules, cluster unit and cuts, missing/failed-slot policy, and predeclared yield uncertainty calculation. Freeze these values before any S3 authorization; an absent value stops generation.
  - APR-compute approval identifier and independently verifiable evidence, allocation scope, hard stage caps, reserved contingency, available A100 GPU-hours, exact expiry timestamp with timezone, and record retrieval time. A standing-allocation assertion without the evidence digest is not compute authority.
  - Canary specification and result manifests for all four G1 canaries with immutable fixture input digests, expected raw fields, semantic assertions, units and tolerances or comparison rules, model/version/weight/image digests, invocation and seeds, same-seed replay and different-seed repeatability results, exact output digests, and typed failure status. Fixtures are labelled non-campaign and threshold-independent; a process exit code without semantic checks is a failure.
  - Freeze time and detached SHA-256 entry in `artifacts/MANIFEST.sha256`
- **Acceptance test:** Every tool appears with a pinned identity, release, weight and image digest, licence determination, and independently verifiable model-training provenance where applicable; the allocation scope, hard stage caps, reserved contingency, and exact expiry are recorded; the fixed S3 sampling frame is frozen; and all four G1 canaries pass their immutable semantic, raw-schema, replay, and compatibility checks on labelled non-campaign fixtures. Process exit status alone never establishes a canary pass.
- **Owner:** ROLE-comp-lead
- **Immutable after freeze:** yes

### D-control-protocol — Immutable pre-control protocol

- **Path:** deliverables/control-protocol/eligibility-rules.json; deliverables/control-protocol/final-protocol.json
- **Schema:**
  - Eligibility-rules component frozen before screening: exact D-target and D-environment digests; PD-1-facing positive evidence rule; numeric A_dec with units, assay basis, and cited rationale; NE1-NE4 assay, positive-control, format, condition, matching, and admissibility rules; freeze time and detached digest. Missing or unsupported values make the attempt a non-run.
  - Reproducible census frame with every named source, exact query, coverage dates, search timestamp, deduplication rule, complete retrieved-to-included flow and exclusion reasons, plus a dual-curation ledger recording both blinded pre-score decisions, evidence digests, disagreements, adjudicator, rule-based resolution, and unresolved exclusions.
  - Final positive and negative control registry with citations, epitope evidence, assay-validity fields, assay-format strata, negative connected-component identity, and unique governing-stratum assignment
  - Frozen scaffold groups, folds, earliest linked public dates, cutoff-clean classification, match distances and tolerances, and deterministic multi-match tie-breaker
  - Filter candidates, within-fold tuning and combination rules, raw-score direction, tie rule, training-only transformation, per-group estimator, the named T_control operating point with coverage and false-go denominators, candidate T_prod fitting rule, exact inferential or conservative method, inferential target, seed, code digest, and no-post-score-change rule.
  - Pre-score small-sample operating-characteristic artifact and independent methods review for the complete planned estimator and operating point, with the finite scenario family, planned group and negative minima, numeric cutoff, coverage, false-go probability, heterogeneity and dependence cases, model-contamination case, replication design, code/seed digests, and explicit calibrated-confidence versus descriptive classification. Absence or failure blocks G2.
  - Numeric A_dec, T_control, coverage and false-go requirements, production-threshold fitting rule, vetoes, clustering cuts, and every ordinary decision-table cell must be explicit with units, denominators, direction, rationale, and outcome before scoring; the incomplete/expiry rule is outside that table. The G2 lifecycle remains branch-conditional: direct-scientific-failure nonacceptance records both candidate paths explicitly absent; scientific candidate pass stages candidate paths/digests; compatibility-failure nonacceptance retains and binds those diagnostics; both nonaccepted branches require the immutable failure record and zero-active reconciliation; compatibility pass alone permits APR-G2; no in-campaign retry.
  - Final protocol freeze time; eligibility_rules_sha256 equal to the detached SHA-256 of the exact stored eligibility-rules.json bytes; detached SHA-256 of the exact stored final-protocol.json bytes as the sole canonical D-control-protocol digest used by every score authorization and downstream artifact; curation and calibration ledgers bound to that digest; and explicit attestation that no control score existed before that canonical digest.
- **Acceptance test:** The eligibility-rules digest predates screening and final-protocol.json predates every score. The protocol freezes the branch-conditional G2 lifecycle: direct scientific failure skips candidate artifacts; scientific candidate pass alone stages thresholds then compatibility; zero-active S2 reconciliation precedes exactly one adjudication; compatibility pass alone permits APR-G2; candidate diagnostics are retained only when staged. Numeric thresholds and vetoes are unchanged.
- **Owner:** ROLE-methods
- **Immutable after freeze:** yes

### D-thresholds — Post-score control results and frozen production thresholds

- **Path:** deliverables/thresholds-and-decision-table.candidate.md; deliverables/thresholds-and-decision-table.md
- **Schema:**
  - Candidate payload frozen before adjudication with state candidate_pass_non_authoritative, canonical D-control-protocol digest, exact D-target and D-environment digests, observed control-result digests, and explicit zero authority for S3 or downstream use
  - Byte-identical control registry, groups, folds, unique negative-component assignments, cutoff classification, numeric operating-point and production thresholds, vetoes, clustering cuts, complete ordinary decision table, fixed S3 frame reference, and exact denominator/uncertainty definitions from D-control-protocol.
  - Raw and training-only transformed held-out predictions with control identifiers, assay-format strata, negative-evidence classes, T_control outputs, positive-coverage and false-go indicators, and their denominators.
  - Per-group AUC values and positive/negative denominators; equal-group and observation-pooled results; T_control coverage and false-go counts and denominators; class, assay-format, leave-one-group-out, influence, heterogeneity, matching, and calibration sensitivities.
  - Exact declared inferential or conservative lower-limit calculation plus the pre-score calibration artifact and independent-review result, with the resulting calibrated-confidence or descriptive classification. A fixed seed proves replayability only; it does not turn an uncalibrated resampling output into a confidence bound.
  - Final production filter thresholds fitted on all eligible controls only after the protocol-valid held-out gate passes, using the rule frozen in D-control-protocol
  - Candidate canary-compatibility digest and complete zero-active S2 authorized-to-terminal accounting required before the one G2 adjudication
  - Accepted G2 and APR-G2 promotion record at `deliverables/thresholds-and-decision-table.md`, binding the exact unchanged candidate path and digest as authoritative D-thresholds; no promotion record on nonacceptance
  - Capacity calculation from the frozen allocation record, hard stage caps, reserved contingency, fixed S3 frame, N_frame denominator, expected completion status, and exact expiry; authoritative only after APR-G2.
  - Candidate freeze time, promotion time if accepted, and detached SHA-256 entries in `artifacts/MANIFEST.sha256`
- **Acceptance test:** Before G2 adjudication, `deliverables/thresholds-and-decision-table.candidate.md` may be frozen once as a candidate_pass_non_authoritative diagnostic binding the canonical D-control-protocol digest, observed control results, and production thresholds fitted by the frozen rule. It grants no APR-G2, S3, generation, scoring, or downstream decision authority and is consumed only by candidate canary-compatibility testing. After compatibility passes, S2 authorization is closed, every authorized control batch is terminal exactly once, and zero-active accounting is verified; ROLE-comp-lead then adjudicates G2 exactly once. Only accepted G2 issues APR-G2 and promotes the exact unchanged candidate bytes and digest through `deliverables/thresholds-and-decision-table.md` as authoritative D-thresholds. Adjudicated nonacceptance retains the staged candidate diagnostically but creates no authoritative D-thresholds and grants no S3 authority.
- **Owner:** ROLE-methods
- **Immutable after freeze:** yes

### D-designs — Ranked design table

- **Path:** deliverables/ranked-designs.csv
- **Schema:**
  - Accepted G2 and APR-G2 plus exact D-thresholds and canonical D-control-protocol digests consumed, with checks that all match
  - One row per frozen-frame production slot or its explicit terminal status: slot identifier, design identifier when present, sequence, backbone reference, generation batch, seed, and N_frame membership.
  - Every filter column the frozen threshold table references, populated, with no nulls
  - Pass or fail per filter and overall
  - Cluster assignment at the frozen cut and at both alternative cuts, plus K_clusters, N_frame, the cluster-corrected yield fraction, and its predeclared uncertainty; duplicates and failed or missing slots remain in the denominator.
  - Per-design compute cost and terminal status, including failed, invalid, duplicate, or missing-slot accounting rather than silently dropping a slot.
  - References to the corresponding authorized, started, and terminal events in D-runtime
  - Freeze time and detached SHA-256 entry in `artifacts/MANIFEST.sha256`
- **Acceptance test:** D-designs exists only after accepted G2 and APR-G2. Every frozen-frame slot is represented or explicitly terminalized; every design has every filter column populated; the D-thresholds and canonical D-control-protocol digests match G2; pass/fail is derivable mechanically; cluster counts are reported at all three cuts; N_frame and K_clusters are reported with the predeclared yield uncertainty; D-runtime reconciles every batch; and D-designs has a detached manifest entry. An incomplete or adaptively extended frame cannot be accepted as G3.
- **Owner:** ROLE-comp-lead
- **Immutable after freeze:** yes

### D-memo — Decision or no-decision memo

- **Path:** deliverables/decision-memo.md
- **Schema:**
  - First paragraph: after accepted G2 and G3, the ordinary cell and two values; after accepted G2 but terminal incomplete/expired G3, no-decision, G3 not accepted, table not run, and no cell; after adjudicated nonaccepted G2, terminal control-failure no-go, G2 nonaccepted, APR-G2 and APR-G3 absent, S3 prohibited, and no ordinary separation-by-yield cell claimed
  - Control separation reported as a distribution comparison with its overlap
  - Contamination-adjusted separation on the post-cutoff independent-group subset, stated next to the all-group figure
  - Only after accepted G2 plus accepted G3 and complete D-designs: cluster-corrected yield at all three cuts
  - Only after accepted G2 plus accepted G3 and complete D-designs: proximity to adjacent ordinary decision cells
  - Residual uncertainty and the least favourable defensible interpretation
  - Any prohibited post-G2 scientific change and the new linked-campaign requirement; no changed artifact supports a cell or recommendation in this campaign
  - Any principal-investigator override, recorded as an override with its reason
  - For accepted-G2 incomplete/expiry no-decision: allocation-record digest and expiry; authorized, completed, failed, interrupted, and unstarted S3 counts; every partial artifact labelled non-decision evidence; and explicit statements that no yield conclusion, cell proximity, table cell, or recommendation is admissible
  - For every terminal control failure: exact immutable `deliverables/control-failure.json` and zero-active G2 reconciliation digests, gate owner/time, failed criteria, observed result digests, no-go recommendation, absent APR-G2/APR-G3 and S3, and retry rule. Compatibility failure additionally binds retained candidate diagnostic paths and digests; direct scientific failure instead records both candidate paths explicitly absent and consumes no placeholder
  - Ordinary exact consumed evidence: accepted G2 and APR-G2 records; exact promoted authoritative D-thresholds and D-canary-compat paths and digests; accepted G3 and APR-G3 records; complete D-designs path and digest; immutable accepted_complete G3 reconciliation path and digest; D-target, D-environment, and canonical D-control-protocol digests
  - Incomplete/expiry no-decision exact consumed evidence: accepted G2 and APR-G2 records; exact promoted authoritative D-thresholds and D-canary-compat paths and digests; immutable terminal not_accepted_incomplete_or_expired G3 reconciliation path and digest; explicit absent APR-G3; every retained partial S3 evidence path and digest; D-target, D-environment, and canonical D-control-protocol digests
  - Failed-G2 exact consumed evidence: immutable control-failure-record path and digest plus zero-active G2 reconciliation path and digest on both branches; compatibility-failure nonacceptance additionally consumes retained candidate diagnostic paths and digests, while direct-scientific-failure nonacceptance consumes the failure record's explicit candidate-path absence attestation; both record absent APR-G2/APR-G3 and zero S3 authorization
  - Version identifier, predecessor candidate-memo digest if any, acceptance time, and detached SHA-256 entry; exactly one G4 decision_accepted, no_decision_accepted, or control_failure_no_go_accepted event names this digest and enters closure_in_progress before idempotent final reconciliation and manifest finalization establish permanent closure
- **Acceptance test:** The accepted immutable memo follows exactly one branch and is named by exactly one matching G4 event. Candidate corrections are permitted only before that event. Once the valid G4 event is appended as the last complete log line, D-memo and every frozen campaign artifact are immutable and closure_in_progress permits only idempotent final reconciliation and manifest finalization without event append. Permanent closure begins after both verify; every later correction requires a new linked campaign.
- **Owner:** ROLE-methods
- **Immutable after freeze:** yes

### D-runtime — Runtime event log and reconciliation

- **Path:** artifacts/runtime/events.ndjson; deliverables/control-failure.json; deliverables/runtime-g2-control-failure-reconciliation.md; deliverables/runtime-g3-reconciliation.md; deliverables/runtime-final-reconciliation.md
- **Schema:**
  - Live UTF-8 JSON Lines event stream at `artifacts/runtime/events.ndjson` using rescamp-runtime-event-v1
  - Each event records sequence, unique event_id, event_type, batch_id when applicable, status, timezone-aware timestamp, actor, frozen input digests, terminal output digests, cumulative cost, and predecessor event_id
  - Single-dispatcher exclusive append rule and one complete atomic line per transition
  - For every batch: authorization before compute, optional heartbeats, and exactly one completed, failed, or interrupted terminal event; a linked retry is authorized only after its predecessor is terminal and no batch with the same frozen inputs and seed remains nonterminal
  - Pre-adjudication candidate-pass records bind immutable non-authoritative threshold and canary-compatibility paths and digests and explicitly grant no APR-G2 or S3 authority
  - Before either G2 outcome: s2_authorization_closed; exactly one completed, failed, or interrupted terminal event for every authorized control batch; counts and IDs proving complete authorized-to-terminal accounting, no duplicate terminal event, and zero active control batch
  - Terminal G2 control-failure record at `deliverables/control-failure.json`: common campaign/gate/protocol identity, owner/time, observed-result digests, failed criteria, terminal_no_go, no-go recommendation, absent approvals/S3, retry rule, freeze and digest; plus exactly one diagnostic branch—compatibility failure binds retained candidate paths and digests, while direct scientific failure binds both candidate paths explicitly absent with no placeholders
  - Immutable G2 control-failure reconciliation recording highest sequence, exact byte length and SHA-256 of the log prefix through g2_control_failure_terminal_no_go; exact control-failure-record digest; complete authorized-to-terminal S2 control-batch accounting with zero active batch; proof of zero S3 authorization; allowed next action WU-decide control-failure branch only; and its own detached digest
  - Immutable G3 reconciliation snapshot recording highest sequence, exact byte length, SHA-256 of the event-log prefix through G3, batch accounting with no active batch, accepted-complete or not-accepted-incomplete/expired status, and its own detached digest; the live stream remains appendable only for S4/G4
  - Closure-in-progress state after exactly one valid decision_accepted, no_decision_accepted, or control_failure_no_go_accepted event is the last complete line: event stream append-sealed, accepted D-memo and all frozen artifacts immutable, final reconciliation or manifest possibly absent, and no second G4 event permitted
  - Idempotent closure finalization or recovery computes or verifies the digest of the unchanged log bytes through the sole G4 event, atomically creates or verifies deterministic final reconciliation and detached manifest entries, appends no event, and changes no frozen artifact; mismatched existing finalization bytes fail closed
  - Permanent closure begins only after final reconciliation and manifest finalization both verify the sole G4 event, complete event-log digest, and no later bytes; it prohibits every later append, retry, artifact correction, or in-campaign successor
- **Acceptance test:** Before the single G2 adjudication, D-runtime proves S2 authorization closed and complete zero-active accounting. Direct scientific-failure nonacceptance binds candidate-artifact absence; compatibility-failure nonacceptance binds retained staged diagnostics. Both bind failed criteria, terminal_no_go, absent APR-G2/APR-G3, and zero S3 authorization. Acceptance binds unchanged passing candidate digests through g2_accepted and APR-G2. G4 closure behavior remains unchanged.
- **Owner:** ROLE-comp-lead
- **Immutable after freeze:** yes

### D-canary-compat — Frozen threshold-to-canary compatibility record

- **Path:** deliverables/canary-compatibility.candidate.md; deliverables/canary-compatibility.md
- **Schema:**
  - Exact candidate threshold digest, candidate_pass_non_authoritative state, and canonical D-control-protocol digest consumed before G2 adjudication
  - Exact digests of every stored raw CAN-pipeline, CAN-energy, CAN-sequence, and CAN-predict fixture
  - For CAN-pipeline, CAN-energy, and CAN-sequence: every table-derived field, value, and pass/fail result produced mechanically without manual edits
  - For CAN-predict: field-to-table compatibility result and any table field not applicable to its raw schema
  - Execution time, tool identity, pass or fail result, zero-authority attestation, and attestation that candidate thresholds remained byte-identical during the checks
  - Candidate freeze time and detached digest; after accepted G2 only, APR-G2 promotion record binding the exact unchanged candidate path and digest as authoritative D-canary-compat
- **Acceptance test:** This deliverable exists only on scientific candidate pass. Then `deliverables/canary-compatibility.candidate.md` consumes the immutable candidate threshold and fixture digests and freezes once as pass or fail with zero authority. After complete zero-active S2 accounting, compatibility pass permits the single accepted G2 adjudication and APR-G2 promotion of unchanged bytes; compatibility failure permits only terminal nonacceptance with diagnostics retained. Direct scientific failure adjudicates without either candidate artifact.
- **Owner:** ROLE-methods
- **Immutable after freeze:** yes
