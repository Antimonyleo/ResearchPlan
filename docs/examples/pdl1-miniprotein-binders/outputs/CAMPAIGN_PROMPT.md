# Research Campaign Prompt: Can our computational pipeline design de novo miniprotein binders to the PD-1-binding face of human PD-L1 that clear frozen…

**Status:** EXECUTION-READY

**Campaign ID:** `pdl1-miniprotein-binders`

**Content version:** 403

**Content digest:** `sha256:5027fd0be0557eb8d85df05f7cfaf0b401cb53b8d44e921242fd400e48948c39`

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
- Reporting: after accepted G2, a no-go recommendation is reported with the same completeness as go, including the full ranked design table and every failed filter. After adjudicated nonaccepted G2, the immutable terminal control-failure record is the complete evidence package; generation, scoring, D-designs, a ranked design table, and G3 are prohibited and therefore not required.

Every worker inherits these rules. Local briefs may narrow scope but may not weaken them.

## 2. Starting point, mission, boundaries, and deliverables

**Entry mode:** New project — no prior project state was supplied.

**Planning origin:** Camp-full selected directly.

**Decision or purpose:** Produce a defensible go/no-go recommendation to the principal investigator on whether to commit gene-synthesis and wet-lab budget to a set of computationally designed de novo miniprotein binders against the PD-1-binding face of human PD-L1.

**Scope:** Computational design and in-silico evaluation only. Scientific candidate pass alone may stage non-authoritative diagnostics with zero S3 authority. Compatibility failure retains and binds the staged candidate threshold and compatibility paths/digests. Direct scientific failure or adjudicated-invalid G2 requires both candidate artifact paths explicitly absent and prohibits placeholder diagnostics; correctable invalid pre-adjudication non-runs remain non-outcomes and are not this terminal branch. Every adjudicated failure requires the immutable failure record and zero-active reconciliation. Compatibility pass, accepted G2, and APR-G2 promotion of exact unchanged candidate digests remain required before downstream design work. G4 closure is unchanged.

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

**Completion definition:** Complete by exactly one G2 branch. Before adjudication, scientific candidate pass alone may freeze candidate thresholds and compatibility as non-authoritative diagnostics; every path then closes S2 authorization and reconciles each control batch terminal exactly once with zero active. Compatibility pass and accepted G2 issue APR-G2, which promotes the exact unchanged candidate digests as authoritative before S3. Nonaccepted G2 retains diagnostics only when staged after candidate pass; direct candidate-fail or adjudicated-invalid terminal no-go requires candidate artifact paths absent and prohibits placeholder diagnostics. Every nonaccepted path freezes complete control-failure evidence and zero-active reconciliation and records terminal no-go without authoritative thresholds or S3. Every decision branch freezes D-memo and appends one G4 event as the last log line; permanent closure begins only after idempotent final reconciliation and manifest finalization verify without changing frozen artifacts.

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

## 3. Object and evidence dossier

**Objects, cases, corpus, population, or system**

### OBJ-target — The PD-1-binding face of the human PD-L1 (CD274) IgV domain, defined by hotspot residues read from a deposited PD-1:PD-L1 co-crystal structure.

- **Description:** The PD-1-binding face of the human PD-L1 (CD274) IgV domain, defined by hotspot residues read from a deposited PD-1:PD-L1 co-crystal structure.
- **Current state:** Not yet pinned. D-target is the first frozen artifact and the S1 gate blocks on it.
- **Boundary:** The epitope is defined by an explicit residue set on a named chain of a named accession, recorded in D-target. The plan does not assert an accession: the exact PDB id, chain, resolution, and residue numbering are pinned in D-target and verified against RCSB at freeze time. For control eligibility, D-control-protocol freezes before screening which direct evidence qualifies a positive as binding at or competing with this PD-1-facing epitope: PD-1 competition, a complex interface overlapping the frozen hotspot set, or qualifying mutational epitope evidence. A design or governing positive targeting another surface is out of scope.

### OBJ-designs — De novo miniprotein binders, single chain, generated against OBJ-target.

- **Description:** De novo miniprotein binders, single chain, generated against OBJ-target.
- **Current state:** None generated.
- **Boundary:** Length range and backbone topology are fixed in D-environment before generation. Designs are computational objects only; no physical material exists at any point in this campaign.

### OBJ-controls — An enumerated pre-score census of epitope-valid PD-L1 binder controls and uniquely assigned NE1-NE4 negative components, with governing eligibility fixed in D-control-protocol.

- **Description:** An enumerated pre-score census of epitope-valid PD-L1 binder controls and uniquely assigned NE1-NE4 negative components, with governing eligibility fixed in D-control-protocol.
- **Current state:** Not yet selected.
- **Boundary:** Before screening, D-control-protocol freezes target- and assay-validity rules; before any score it freezes the complete reproducible census, exclusions, memberships, groups, folds, unique negative assignments, and eligibility classes. Governing positives require a cited PD-L1 measurement plus direct evidence for OBJ-target's PD-1-facing epitope. Governing NE1/NE2 negatives require the frozen A_dec sensitivity, functioning positive-control, target-construct, assay-format, condition-compatibility, and matching rules. Each negative connected component belongs to one governing stratum and counts once. NE3 presumed negatives and NE4 scrambles are descriptive only. No membership or class changes after scores are visible.

**Context**

### CTX-decision

- **Why it changes the design:** The PI will not release synthesis budget on a ranked list alone. Only after accepted G2 and APR-G2 may an ordinary recommendation use D-thresholds, generation, scoring, D-designs, a ranked table, G3, or the ordinary separation-by-yield table. Every adjudicated nonaccepted G2 is instead terminal no-go on the complete immutable control-failure record and G2 reconciliation; observation-pooled or presumed-negative separation alone carries no decision authority.

### CTX-allocation

- **Why it changes the design:** The claimed GPU allocation expires at quarter end and does not roll over; its exact evidence and timezone-aware expiry must be verified in D-environment before G1. After accepted G2 and APR-G2, only the frozen S3 frame may run within the hard cap and reserve. An adjudicated nonaccepted G2 prohibits S3 and records zero S3 authorization.

**Source hierarchy**

### SRC-structure

- **Tier:** Tier 1 — deposited experimental structures from the PDB, with accession, chain, method, and resolution recorded.
- **Admissibility:** Admissible for defining the epitope and for structural superposition. Resolution and any missing density at the interface must be recorded in D-target.
- **Known limitations:** A co-crystal captures one conformational state. Interface plasticity and crystallographic artefacts are not visible in a single structure.

### SRC-literature

- **Tier:** Tier 1 — peer-reviewed publications reporting experimental PD-L1 binding measurements, used to select positive controls.
- **Admissibility:** Admissible for the frozen control census only when the exact search source, query, date, screening disposition, citation, assay, and conditions are recorded. A governing positive also needs direct PD-1-facing epitope evidence; a governing NE1/NE2 negative must satisfy D-control-protocol's A_dec sensitivity, working-positive-control, target-construct, format, and condition rules.
- **Known limitations:** Reported affinities differ by assay format and are not directly comparable across papers. Publication bias against non-binders is why the negative set is constructed, not collected.

### SRC-predictions

- **Tier:** Tier 3 — model outputs from structure prediction, sequence design, and energy scoring.
- **Admissibility:** Admissible as ranking and filtering evidence only. Never admissible as evidence that a design binds.
- **Known limitations:** Structure-prediction confidence correlates with, but does not establish, binding. Filter stacks of this class are known to pass designs that fail experimentally; the campaign's entire purpose is to decide whether the separation is good enough to pay to find out.

**Access and rights**

### ACC-compute

- **Rights:** Claimed 2,000 A100 GPU-hours on the existing institutional cluster allocation; the claim is not usable authority until the evidence artifact is verified.
- **Approval:** A standing group allocation is claimed but not verified in this state. No campaign compute is authorized until D-environment records independently verifiable approval evidence, scope, hard caps, reserve, available hours, exact timezone-aware expiry, and a detached record digest.
- **Expiry:** Claimed end of the current quarter; the exact timezone-aware expiry must be independently verified in D-environment before G1.

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

### INQ-separation — Under the frozen D-control-protocol, do epitope-valid published PD-L1 binders separate from uniquely assigned, assay-valid topology-matched NE1/NE2 negatives well enough for the ranking to carry decision weight?

- **Why it matters:** This is the gating question of the campaign. If the stack cannot separate known binders from known non-binders, every score it assigns to a campaign design is uninterpretable and no amount of favourable-looking design scores can rescue it.
- **Admissible support:**
  - Every branch: the immutable pre-score D-control-protocol, complete census and inclusion flow, eligibility records, unique assignments, and exact observed control-result digests. After accepted G2 only: D-thresholds, per-group and assay-format results, equal-group estimate, and calibrated confidence bound. After adjudicated nonaccepted G2: the bound terminal control-failure record and immutable G2 reconciliation as complete control evidence and no-go recommendation.
- **Counterevidence, rival explanation, reading, or objection:**
  - Apparent separation driven by a confound rather than by binding: positive controls sharing a sequence family, design lineage, scaffold, or topology that the negatives do not share.
  - The rival explanation is that the stack is detecting a familiar scaffold or 'looks like a designed protein', not 'binds this epitope'.
  - Training-set contamination: published binders are frequently deposited structures, and deposited structures are frequently in a structure-prediction model's training data. Their interface confidence would then be partly memorization, inflating separation in a way that does not transfer to novel designs.
- **Discriminating prediction or interpretive implication:** If separation is binding-relevant, held-out epitope-valid scaffold groups outrank uniquely assigned, assay-valid NE1/NE2 negatives under equal group weighting and remain passing across compatible assay-format sensitivities. If label validity, scaffold recognition, negative reuse, format effects, or selection drives the result, census flow, per-group and per-format effects, pooled-versus-equal-group disagreement, leave-one-group-out influence, matching diagnostics, or NE1/NE2 versus NE3 sensitivity will expose it.
- **Verification or adjudication:** Verify protocol timing and reproduce control analyses. If scientific candidate pass was reached, verify candidate thresholds and compatibility were frozen before the one adjudication as non-authoritative diagnostics with zero S3 authority. After accepted G2, verify compatibility passed and APR-G2 promoted their exact unchanged digests. After nonacceptance, verify diagnostics only when staged after candidate pass; for direct candidate-fail or adjudicated-invalid terminal no-go, verify both candidate artifact paths are absent and no placeholder diagnostics exist. In every nonaccepted branch verify the terminal failure record, zero-active G2 reconciliation, absent APR-G2/APR-G3, zero S3 authorization, no authoritative D-thresholds or D-designs, and prohibited go.
- **Uncertainty and external-validity boundary:** The published-control census is vulnerable to publication and availability bias and does not by itself represent novel campaign designs. Five cutoff-clean groups and three unique negatives per group are decision-grade only if prospective operating-characteristic calibration and an exchangeability argument support them. Otherwise the group-bootstrap limit is descriptive for the enumerated controls and cannot authorize go. In-silico discrimination never establishes wet-lab binding.
- **Reporting rule:** Apply the authoritative G2 outcome map. Invalid pre-adjudication non-runs may be corrected before G2 and supply no gate outcome. Report the census, eligibility, unique components, observed results, sensitivities, point estimate, and lower-limit classification. Every adjudicated nonaccepted G2 is terminal no-go for this campaign, with the control-failure record as complete evidence; it is never an in-campaign revise or rerun.

### INQ-yield — Only after accepted G2, APR-G2, complete D-designs, and accepted G3, does the design pipeline produce enough distinct threshold-clearing designs to make synthesis worth considering; otherwise is yield explicitly not adjudicated or not evaluated under the applicable terminal branch?

- **Why it matters:** Cluster-corrected yield contributes to the ordinary decision only after accepted G2, APR-G2, complete D-designs, and accepted G3. Accepted G2 followed by terminal incomplete or expired S3 makes this inquiry not adjudicated and the campaign no-decision. Adjudicated nonaccepted G2 grants zero S3 authority and leaves this inquiry not evaluated.
- **Admissible support:**
  - Ordinary yield conclusion only: compatibility pass, accepted G2, APR-G2 promotion of the exact unchanged threshold and compatibility digests, complete D-designs, accepted G3, and the count of all designs clearing every frozen threshold after predeclared clustering, with raw counts and sequence and structural diversity.
  - Accepted-G2 terminal incomplete/expired S3: terminal S3 event, allocation and completeness accounting, immutable G3 non-acceptance reconciliation, G3 explicitly not accepted, and every retained partial artifact labelled non-decision evidence. These support only 'inquiry not adjudicated' and no-decision; they are inadmissible for any cluster-corrected yield conclusion.
  - Adjudicated nonaccepted G2: the control-failure record and zero-active G2 reconciliation establish zero S3 authorization and 'yield not evaluated'; no design or yield evidence is admissible.
- **Counterevidence, rival explanation, reading, or objection:**
  - A completed passing set may be one design and its near-copies; cluster count, not raw pass count, is the decision-relevant quantity.
  - A large raw pass count can reflect redundant sampling rather than independent design yield and must collapse under the predeclared sequence and structural cuts.
  - An incomplete or expired S3 can overstate or understate yield because unfinished or unstarted batches are not exchangeable with completed batches. Retained partial scores or clusters are non-decision evidence and cannot answer the inquiry.
- **Discriminating prediction or interpretive implication:** On the ordinary branch, accepted G2, APR-G2, complete D-designs, and accepted G3 reveal whether threshold-clearing designs occupy multiple sequence and structural clusters or collapse as near-duplicates. On accepted-G2 terminal incomplete or expired S3, completeness is unresolved, G3 is not accepted, the inquiry is not adjudicated, and no cluster-corrected yield conclusion is permitted. On adjudicated nonaccepted G2, zero S3 authority leaves yield not evaluated.
- **Verification or adjudication:** Ordinary branch: verify compatibility pass, accepted G2, APR-G2 promotion of exact unchanged digests, complete D-designs, accepted G3, and complete-set single-linkage clustering at 60 percent global sequence identity and 2.0 Angstrom interface backbone RMSD with 50 and 70 percent alternatives. Accepted-G2 terminal incomplete/expired S3: verify the terminal event, allocation and completeness accounting, immutable G3 non-acceptance reconciliation, G3 not accepted, every partial artifact labelled non-decision, inquiry not adjudicated, no table application, and no cluster-corrected yield conclusion. Adjudicated nonaccepted G2: verify the control-failure record, zero-active G2 reconciliation, and zero S3 authorization; record yield not evaluated.
- **Uncertainty and external-validity boundary:** Even on the ordinary complete branch, cluster counts depend on the distance cut, so report the frozen cut and both predeclared alternatives. Partial S3 evidence has additional non-random completeness and expiry uncertainty that cannot be repaired by sensitivity cuts; without complete D-designs and accepted G3 it supports no yield conclusion. A failed G2 provides no S3 sample at all.
- **Reporting rule:** Ordinary branch only—after accepted G2, APR-G2, complete D-designs, and accepted G3—report cluster count, cluster occupancy, raw pass count, and sensitivity at every predeclared cut. After accepted G2 but terminal incomplete or expired S3, report 'INQ-yield not adjudicated; no-decision', retain and inventory every partial artifact solely as non-decision evidence, and claim no cluster-corrected yield conclusion. After adjudicated nonaccepted G2, report 'INQ-yield not evaluated; zero S3 authority' and do not require or infer design or ranked-table evidence.

### INQ-spend — Does the eligible terminal branch support an ordinary synthesis-spend recommendation, require terminal control-failure no-go, or require no-decision because accepted-G2 production was incomplete or expired before G3 acceptance?

- **Why it matters:** After accepted G2, separation and yield jointly answer the ordinary deliverable question. After adjudicated nonaccepted G2, the failed control gate answers it terminally as no-go without generation or a ranked list.
- **Admissible support:**
  - Ordinary branch: accepted G2, APR-G2 promoting unchanged threshold and compatibility digests, accepted G3, the frozen ordinary decision table, authoritative D-thresholds, and cluster-corrected yield from complete D-designs.
  - Accepted-G2 no-decision branch: APR-G2, terminal incomplete_or_expired S3 evidence, allocation and completeness accounting, immutable G3 non-acceptance reconciliation, G3 not accepted, and retained partial S3 artifacts labelled non-decision evidence; no ordinary table cell or recommendation is admissible.
  - Failed-G2 branch: immutable failure record and zero-active G2 reconciliation are common. Compatibility failure binds retained staged candidate threshold and compatibility paths/digests. Direct scientific failure or adjudicated-invalid G2 requires both candidate artifact paths explicitly absent and no placeholder diagnostics. Correctable invalid pre-adjudication non-runs supply no gate outcome and are not this terminal branch. No APR-G2, S3 authority, D-designs, G3, or ordinary table applies.
- **Counterevidence, rival explanation, reading, or objection:**
  - After accepted G2, the rival reading is that a marginal separation-by-yield result should be resolved by the ordinary table's bounded revise outcome rather than spending.
  - An adjudicated nonaccepted G2 cannot use revise inside this campaign; any retry is a new linked campaign with fresh authorization and no inherited dispatch authority.
- **Discriminating prediction or interpretive implication:** An ordinary recommendation requires accepted G2, APR-G2, complete accepted G3, and the frozen table. Accepted G2 and APR-G2 followed by terminal incomplete or expired S3 yields no-decision: partial evidence is retained, G3 is not accepted, and no cell or recommendation may be claimed. Adjudicated nonaccepted G2 mechanically yields terminal control-failure no-go before S3.
- **Verification or adjudication:** Ordinary branch: verify accepted G2, APR-G2, accepted G3, authoritative D-thresholds, complete D-designs, and the ordinary cell mechanically. Accepted-G2 no-decision branch: verify APR-G2, terminal incomplete_or_expired S3 evidence, immutable G3 non-acceptance reconciliation, G3 not accepted, retained partial evidence labelled non-decision, table not run, no cell, no recommendation, and matching no_decision_accepted G4 event. Failed-G2 branch: verify the control-failure record, zero-active G2 reconciliation, absent APR-G2 and S3 authority, and matching control_failure_no_go_accepted G4 event.
- **Uncertainty and external-validity boundary:** Accepted G2 and APR-G2 establish control authority but do not make a partial or expired S3 decision-grade. Without accepted G3, partial design evidence cannot establish cluster-corrected yield or support an ordinary cell or recommendation, so the terminal outcome is no-decision. Every adjudicated nonaccepted G2 remains terminal no-go for this campaign.
- **Reporting rule:** After accepted G2, APR-G2, and accepted G3, state the ordinary cell and its two values first. After accepted G2 and APR-G2 but terminal incomplete or expired S3, state no-decision first, cite the terminal S3 and G3 non-acceptance evidence, report retained partial evidence only as non-decision evidence, and state explicitly that G3 was not accepted and no table cell or recommendation exists. After adjudicated nonaccepted G2, state terminal control-failure no-go first.

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

- **Purpose:** Freeze an auditable control protocol before scoring and estimate separation among enumerated valid independent controls. Scientific candidate pass alone stages production thresholds and canary compatibility as immutable non-authoritative diagnostics. Every path closes S2 authorization and reconciles zero active before exactly one G2 adjudication. Compatibility pass and accepted G2 permit APR-G2 to promote the exact unchanged candidate digests and authorize M-generate and M-score. Nonacceptance retains diagnostics only when staged; direct candidate-fail or adjudicated-invalid terminal no-go requires candidate artifact paths absent and prohibits placeholders. Every nonaccepted path closes with zero S3 authority.
- **Answers inquiries:**
  - INQ-separation
- **Inputs:**
  - D-target and D-environment with exact digests; passing CAN-predict, CAN-energy, CAN-pipeline, and CAN-sequence evidence; plus the eligibility-rules component of D-control-protocol frozen before control screening.
  - A reproducible census of the named literature and structure sources with exact queries, dates, deduplication, complete inclusion and exclusion flow, and two independent pre-score curation decisions with an adjudication ledger.
  - At least 8 positives satisfying the frozen PD-1-facing epitope-evidence rule and spanning at least 6 frozen sequence/structure scaffold groups; at least 5 groups must be cutoff-clean for any go.
  - For every governing group, at least three unique NE1 or NE2 negative components assigned to that group alone and satisfying campaign.evaluation's A_dec sensitivity, functioning-positive-control, assay-compatibility, and topology-matching rules.
  - The final immutable D-control-protocol, with final-protocol.json frozen before scoring, binding the exact eligibility-rules digest, T_control operating-point fields, decision cells, model-provenance dispositions, curation ledger, sampling-frame reference, and exact inferential/calibration method; its own exact stored-byte SHA-256 is canonical.
- **Outputs:**
  - D-control-protocol: immutable eligibility-rules predecessor, dual-curation/adjudication ledger, final pre-score census, memberships, assignments, complete T_control operating-point analysis and calibration protocol, explicit numeric rules and decision table, incomplete/expiry rule, freeze times, predecessor digest, and canonical final-protocol.json detached digest.
  - Pre-adjudication candidate-pass: immutable non-authoritative threshold and canary-compatibility diagnostics binding the canonical protocol and fixture digests and granting zero S3 authority.
  - Accepted-control branch only: g2_accepted and APR-G2 promotion records binding the exact unchanged candidate digests as authoritative D-thresholds and D-canary-compat and authorizing M-generate and M-score.
  - Adjudicated-nonaccepted branch only: candidate diagnostics retained only when staged after scientific candidate pass; direct candidate-fail or adjudicated-invalid terminal no-go requires both candidate artifact paths absent and prohibits placeholder diagnostics. Every such branch includes immutable `deliverables/control-failure.json` and G2 reconciliation binding complete zero-active control-batch accounting, every observed result digest, failed criteria, terminal_no_go, absent APR-G2/APR-G3, zero S3 authorization, complete no-go recommendation, and the sole WU-decide branch.
- **Assumptions:**
  - The reproducible published-control census and frozen inclusion flow are sufficiently complete for the explicitly bounded control frame; broader generalization requires the prospective exchangeability and small-sample calibration checks.
  - Direct epitope evidence and the frozen A_dec, working-positive-control, target-construct, assay-format, and condition rules yield decision-relevant binary labels.
  - Conservative sequence/structure/design-lineage grouping and unique negative-component assignment prevent related or reused controls from crossing folds.
  - The training-only transformation and equal-group estimator make independent scaffold groups, rather than observation multiplicity, the unit of analysis.
- **Limitations:**
  - Even a reproducible census of published controls is subject to publication and availability bias and may not represent novel campaign designs.
  - Eligible controls may remain heterogeneous across assay formats and conditions; the governing conclusion must survive the frozen format sensitivities.
  - Epitope-valid positives and assay-valid, uniquely assigned NE1/NE2 negatives may be too scarce to meet the frozen minima without reuse; NE3 and NE4 cannot repair that deficit.
  - With as few as five cutoff-clean groups and three negatives per group, a resampling lower limit is not automatically a confidence bound. The complete inferential procedure must pass the frozen pre-score calibration or an exact/conservative finite-sample review; otherwise it remains descriptive and cannot authorize go.
  - Final production thresholds are fitted on eligible controls only after the protocol-valid held-out evaluation passes; their prospective validity still requires wet-lab evidence outside this campaign.
- **Cost:** Hard cap 300 A100 GPU-hours, including control runs, dual curation, pre-score calibration, and permitted infrastructure reruns.
- **Dependencies:** M-target, and all four canaries passing: CAN-predict, CAN-energy, CAN-pipeline, and CAN-sequence.
- **Decision it can change:** Yes, under the authoritative G2 outcome map. An invalid pre-adjudication non-run may be corrected before G2 and supplies no gate outcome. Scientific candidate pass alone may stage candidate thresholds and compatibility as non-authoritative diagnostics. Compatibility pass, accepted G2, and APR-G2 alone promote their exact unchanged digests as authoritative D-thresholds/D-canary-compat and authorize M-generate and M-score. Every nonaccepted adjudication is terminal no-go and authorizes only bound closure; direct candidate-fail or adjudicated-invalid paths have no candidate artifacts or placeholders.

### M-generate — Backbone generation and fixed-backbone sequence design

- **Purpose:** Only after the control-separation gate is accepted and production thresholds are frozen, produce a diverse set of candidate de novo miniproteins directed at the frozen epitope.
- **Answers inquiries:**
  - INQ-yield
- **Inputs:**
  - D-target, D-environment, accepted G2 and APR-G2 records, authoritative D-thresholds promoted without byte changes from the frozen candidate payload, and the D-environment fixed S3 frame with batch/slot counts, seeds, N_frame denominator, quality rules, cluster cuts, uncertainty rule, hard cap, and expiry.
- **Outputs:**
  - Backbone coordinates, designed sequences, and a generation manifest recording the fixed-frame slot, parameters, seeds, model provenance, output status, and cost per batch; terminalized failed or missing slots remain in the N_frame accounting.
- **Assumptions:**
  - That the declared length range and topology constraints admit a solution for this epitope.
- **Limitations:**
  - Generative sampling is bounded by the frozen frame, hard cap, reserve, and expiry. No observed yield may trigger extra batches or shrink N_frame; absence of passing designs is evidence about this pipeline under this budget, never about the target's designability.
  - Absence of passing designs is evidence about this pipeline under this budget, never about the target's designability.
- **Cost:** Hard cap 1,200 A100 GPU-hours within the frozen S3 sampling frame; no adaptive extension or denominator change.
- **Dependencies:** M-target; production-setting canaries passed; and M-controls accepted at G2 with protocol-valid control separation and D-thresholds containing frozen production thresholds. A merely completed or frozen but unaccepted M-controls run does not satisfy this dependency.
- **Decision it can change:** Yes. Yield after clustering is one of the two inputs to the decision table.

### M-score — Frozen-threshold scoring and clustering

- **Purpose:** Only after accepted control separation authorized the branch, score every campaign design through the identical pipeline the controls passed through, apply the frozen production thresholds once, and cluster the survivors.
- **Answers inquiries:**
  - INQ-yield
  - INQ-spend
- **Inputs:**
  - Designed sequences and backbones from authorized fixed-frame M-generate slots, the accepted G2 control-gate record, D-thresholds with frozen production thresholds, D-environment, and the unchanged model/provenance manifests.
- **Outputs:**
  - The ranked design table with every filter column populated, pass/fail per filter, fixed-frame slot and N_frame status, cluster assignments at the frozen cut and at two pre-declared alternatives, K_clusters/N_frame yield with its predeclared uncertainty, and per-design provenance.
- **Assumptions:**
  - That the scoring pipeline is deterministic given a seed, as the canaries verify.
- **Limitations:**
  - The filter stack predicts; it does not measure.
  - Designs that clear it may fail experimentally, which is precisely the risk the recommendation is about.
- **Cost:** Hard cap 400 A100 GPU-hours within the frozen S3 sampling frame; no adaptive extension or denominator change.
- **Dependencies:** M-generate, plus accepted G2 and APR-G2 and the authoritative D-thresholds and D-canary-compat promoted from unchanged candidate digests.
- **Decision it can change:** Yes. This produces the numbers the decision table consumes.

### M-decide — Mechanical decision or no-decision finalization

- **Purpose:** Finalize exactly one mutually exclusive terminal branch from its exact evidence contract. For ordinary accepted-G2/G3, consume the compatibility-pass, accepted-G2, APR-G2 unchanged-digest promotion, authoritative threshold/compatibility, complete-design, accepted-G3, and frozen-table inputs and apply the ordinary table once. For accepted-G2 terminal incomplete/expired S3, consume the same valid G2/APR-G2 chain plus terminal S3, allocation/completeness, immutable G3 non-acceptance, G3-not-accepted, and retained partial non-decision evidence, and record no-decision without a table cell or recommendation. For compatibility-failed G2, consume retained staged candidate paths/digests with the failure record, zero-active reconciliation, and zero S3 authority. For direct-scientific-failure or adjudicated-invalid G2, consume the same failure and reconciliation closure with both candidate paths explicitly absent and no placeholders. Consume exactly one branch; no branch's inputs, authority, artifacts, or absence assertions may overwrite or satisfy another. Existing branch-matched D-memo output and G4 closure behavior remain unchanged.
- **Answers inquiries:**
  - INQ-spend
- **Inputs:**
  - Ordinary accepted-G2/G3 contract: compatibility-pass evidence; accepted G2; APR-G2 promotion record binding the exact unchanged candidate threshold and compatibility digests; authoritative D-thresholds and D-canary-compat; complete D-designs; accepted G3 and its immutable reconciliation; and the frozen ordinary decision table with its authoritative calibrated-control-separation and cluster-corrected-yield inputs.
  - Accepted-G2 terminal incomplete/expired no-decision contract: compatibility-pass evidence; accepted G2; APR-G2 promotion of the exact unchanged candidate threshold and compatibility digests; authoritative D-thresholds and D-canary-compat; terminal incomplete_or_expired S3 event and evidence; frozen allocation record and expiry; authorized, completed, failed, interrupted, and unstarted completeness accounting; immutable G3 non-acceptance reconciliation; G3 explicitly not accepted; and every retained partial S3 artifact labelled non-decision evidence. The ordinary table is not run, and no cell or recommendation is an input or output.
  - Compatibility-failed G2 contract: D-control-protocol; immutable control-failure record identifying compatibility failure; complete zero-active G2 reconciliation; exact observed-result digests; retained staged candidate threshold and candidate compatibility paths and digests; absent APR-G2 and APR-G3; and explicit zero S3 authorization.
  - Direct-scientific-failure or adjudicated-invalid G2 contract: D-control-protocol; immutable control-failure record identifying direct scientific failure or adjudicated invalidity; complete zero-active G2 reconciliation; exact observed-result digests; explicit absence of both candidate threshold and candidate compatibility paths; attestation that no placeholder diagnostics exist; absent APR-G2 and APR-G3; and explicit zero S3 authorization.
  - Branch exclusivity record: identify exactly one of the four contracts above before dispatch. Reject mixed evidence, cross-branch substitution, branch-input overwrite, or use of one branch's authorization or absence assertion to satisfy another.
- **Outputs:**
  - D-memo: after accepted G2 and accepted G3, the ordinary cell, its two values, proximity, residual uncertainty, recommendation, and complete ranked table; after accepted G2 but terminal incomplete/expired S3 with G3 not accepted, the exact reason, allocation and completeness accounting, retained partial artifacts labelled solely as non-decision evidence, table not run, no cluster-corrected yield conclusion, no ordinary cell, and no recommendation; after adjudicated nonaccepted G2, terminal control-failure no-go binding candidate diagnostics only when staged after scientific candidate pass, otherwise recording both candidate artifact paths absent and no placeholders, plus the complete failure record and zero-active G2 reconciliation, with no authoritative D-thresholds, generation, scoring, D-designs, ranked table, G3, APR-G3, or ordinary cell.
- **Assumptions:**
  - That the table's cells were drawn sensibly before the results were visible.
- **Limitations:**
  - A discrete table hides uncertainty at its boundaries; the memo reports proximity explicitly.
  - The PI may override, and an override is recorded as an override.
- **Cost:** Negligible compute; roughly two working days of writing.
- **Dependencies:** Exactly one mutually exclusive branch contract must be satisfied before M-decide starts. Ordinary accepted-G2/G3: compatibility pass; accepted G2; APR-G2 promotion of the exact unchanged candidate threshold and candidate compatibility digests; authoritative D-thresholds and D-canary-compat; complete D-designs; accepted G3; and the frozen ordinary decision-table inputs. Accepted-G2 terminal incomplete/expired no-decision: the same compatibility-pass, accepted-G2, APR-G2 exact-unchanged-digest promotion chain and authoritative D-thresholds/D-canary-compat, plus terminal incomplete_or_expired S3 evidence, allocation and completeness accounting, immutable G3 non-acceptance reconciliation, G3 explicitly not accepted, and retained partial evidence labelled non-decision; no table cell or recommendation exists. Compatibility-failed G2: immutable control-failure record, zero-active G2 reconciliation, zero S3 authority, and retained staged candidate threshold and compatibility paths and digests. Direct-scientific-failure or adjudicated-invalid G2: the same immutable failure record, zero-active reconciliation, and zero S3 authority, plus explicit absence of both candidate artifact paths and no placeholder diagnostics. Exactly one contract is consumed; evidence, authorization, or absence assertions from one branch cannot overwrite, substitute for, or satisfy another branch.
- **Decision it can change:** After accepted G2 and accepted G3 it applies the ordinary frozen decision table. After accepted G2 but terminal incomplete/expired S3 with G3 not accepted, it records no-decision outside that table; retained partial artifacts remain non-decision evidence and support no cluster-corrected yield conclusion, ordinary table cell, or recommendation. After adjudicated nonaccepted G2 it records terminal control-failure no-go without APR-G3, G3, or an ordinary table cell; no branch can reopen authorization after G4.

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

### CAN-predict — After D-target and the D-environment canary specification are frozen, predict the immutable native PD-1:PD-L1 fixture and its scrambled-partner negative with the exact production model, image, invocation, template/MSA policy, and seed policy that S2 and S3 will use.

- **Tool:** TOOL-predict
- **Expected artifacts and schema:**
  - Immutable fixture manifest with exact target/partner sequence and structure input digests, D-target chain/hotspot mapping, tool release/weight/image digests, invocation, seed policy, raw-schema version, and semantic assertions frozen in D-environment before execution.
  - Raw prediction records containing target and partner chain identifiers, residue mapping, coordinates, per-residue confidence, interface confidence, finite-value checks, and coordinate/confidence comparison tolerances from the pre-score canary specification.
  - Two same-seed replay outputs and one different-seed output with exact output digests and wall-clock cost, compared against the manifest's declared repeatability rule.
- **Positive, negative, and sanity cases:**
  - Positive semantic assertion: predicted chains map to the D-target chains and every frozen hotspot residue is represented in the predicted interface; coordinate and interface tolerances are the values frozen in D-environment, not values inferred from this run.
  - Negative semantic assertion: the scrambled-partner fixture fails the target/interface acceptance rule or remains below the predeclared low-confidence criterion; a post-hoc low-confidence cutoff is a failure.
  - Repeatability assertion: same-seed raw output is byte-identical and different-seed spread is within the predeclared band. Missing input/output digest, residue mapping, tolerance, or semantic result fails.
- **Downstream acceptance:** The filter stack must ingest the manifest and raw canary output end to end, preserve the declared chain/residue and field mapping, and reproduce the same semantic values from stored artifacts. Exit status without semantic checks, or an output the scorer cannot ingest, fails the gate.
- **Quarantine triggers:** A missing fixture or model digest, residue mapping, semantic assertion, tolerance, replay result, or downstream ingestion result fails G1. Any campaign design scored under a failed or semantically incomplete canary is quarantined and cannot be rescued by a process exit code; S3 does not start.

### CAN-energy — After D-environment freezes the energy specification, score the immutable native PD-1:PD-L1 interface and deliberately disrupted interface with the exact production package, version, flags, container, and seed policy that S2 and S3 will use, emitting raw terms before any threshold table is consulted.

- **Tool:** TOOL-energy
- **Expected artifacts and schema:**
  - Immutable native/disrupted fixture manifest with exact input digests, package release/commit, image digest, invocation, seed policy, raw-schema version, units, score direction, and native-versus-disrupted semantic comparison rule frozen in D-environment.
  - Raw interface-energy and liability rows with every required field finite and unit-labelled, a typed native/disrupted pairing, exact replay digest, and no threshold-derived columns.
  - Same-seed replay outputs with exact output digests and cost; the expected direction and minimum contrast are predeclared with a documented basis, not learned from the canary result.
- **Positive, negative, and sanity cases:**
  - Positive semantic assertion: the native row is complete, finite, and favourable under the predeclared energy direction and comparison rule.
  - Negative semantic assertion: the deliberately disrupted row fails the native acceptance relation by the predeclared direction/contrast rule; a post-hoc contrast is a failure.
  - Repeatability assertion: identical input and seed reproduce identical raw terms and schema bytes; missing units, direction, pairing, or replay digest fails.
- **Downstream acceptance:** At G1, raw terms, units, native/disrupted pairing, semantic direction, and exact replay validate without thresholds. On scientific candidate pass only, candidate compatibility binds the immutable non-authoritative candidate threshold digest; a missing derived-field mapping makes G2 terminally nonaccepted. APR-G2 alone promotes unchanged passing digests.
- **Quarantine triggers:** Raw-schema, unit, direction, native/disrupted semantic, or replay failure blocks S2. A missing pre-score comparison rule or digest is a failed canary, not a value to be chosen after scoring. Post-freeze table-compatibility failure blocks S3; canary rows remain fixtures and never enter D-designs.

### CAN-pipeline — After the raw schemas and fixture manifest are frozen, run a miniature valid-and-malformed generation-through-raw-score transport check at production settings before any control or campaign design is scored. Verify row identity, required raw fields, deterministic replay, and threshold-independent transport only.

- **Tool:** TOOL-backbone
- **Expected artifacts and schema:**
  - Immutable valid and malformed fixture manifest with exact backbone/sequence input digests, fixture labels, expected accept/reject status, row identifiers, raw-schema version, model/tool/image digests, invocation, and seed policy.
  - A versioned raw-score fixture table whose required raw fields and valid input-to-output mapping are complete, with no threshold-derived columns; malformed input has a typed schema-validation failure record and no plausible row.
  - Exact replay outputs and digests, plus a pre-score field-mapping record showing how every raw field is transported to the candidate table without manual edits.
- **Positive, negative, and sanity cases:**
  - Positive semantic assertion: the valid fixture preserves its identifier and every required raw field, unit, and value type through generation and scoring; no threshold column is consulted.
  - Negative semantic assertion: the malformed fixture is rejected with a typed validation failure and cannot produce a row, score, or downstream table entry.
  - Repeatability assertion: the valid miniature pass reproduces byte-identically from its manifest, including row order and field names.
  - Boundary assertion: valid and malformed fixtures are labelled non-campaign and are rejected by the campaign-result join; they cannot enter D-designs or any scientific result.
- **Downstream acceptance:** At G1, the versioned raw-score schema, row/field mapping, valid/reject semantics, and exact replay pass without a decision table. On scientific candidate pass only, candidate compatibility binds the immutable candidate threshold digest and proves every derived column from stored raw rows. Direct scientific failure skips candidate artifacts. Only APR-G2 promotion makes passing candidate digests authoritative.
- **Quarantine triggers:** Any missing fixture digest, label, row mapping, raw field, typed rejection, semantic transport check, or exact replay blocks S2. Failure of the post-freeze table-application check blocks S3. Canary fixtures are permanently excluded from campaign results.

### CAN-sequence — After D-target, D-environment, and the sequence-canary specification are frozen, redesign the immutable native-partner backbone and its masked/absent-target negative at production settings, then predict and emit deterministic raw downstream scores under versioned schemas independent of D-thresholds. Label every fixture non-campaign.

- **Tool:** TOOL-sequence
- **Expected artifacts and schema:**
  - Immutable backbone, native sequence, masked/absent-target negative, and target-context fixture digests; model release/weight/image digests; invocation, template/MSA policy, seed policy, raw-schema version, and semantic assertions frozen in D-environment.
  - Designed fixture sequences with alphabet, length/topology, backbone/target mapping, per-position confidence, raw prediction/score fields, and structure/interface comparison tolerances from the pre-score specification.
  - Same-seed replay outputs and different-seed output with exact digests, plus a manifest carrying model identity, weight digest, image digest, seed, exact replay digest, and cost.
- **Positive, negative, and sanity cases:**
  - Positive semantic assertion: the designed sequence satisfies the frozen alphabet, length, topology, backbone/target mapping, fold, and interface comparison rules; tolerances are predeclared and not fitted from the result.
  - Negative semantic assertion: the masked or absent-target fixture fails the positive target/interface rule or remains below the predeclared low-confidence criterion; confident output without the target context fails the canary.
  - Repeatability assertion: same-seed sequence and raw downstream output are byte-identical and different-seed identity spread is within the predeclared band. Missing digest, mapping, schema, tolerance, or replay result fails.
- **Downstream acceptance:** At G1, sequence, prediction, target-context, and raw-score schemas validate, preserve semantic mappings, and replay exactly without thresholds. On scientific candidate pass only, candidate compatibility records that the immutable candidate table consumes the stored rows and emits every required column. Direct scientific failure skips candidate artifacts. Only APR-G2 promotion makes passing candidate digests authoritative.
- **Quarantine triggers:** Raw-schema, sequence-constraint, target-context, semantic, or replay failure blocks S2. A missing pre-score tolerance or expected semantic relation is a failed canary. Post-freeze table-compatibility failure blocks S3; fixture sequences and rows are permanently excluded from D-designs.

## 7. Frozen evaluation or adjudication instrument

**Frozen before production (asserted, not verified):** Before screening, freeze eligibility. Before any control score, freeze final-protocol.json with the complete census, assignments, analysis, unchanged numeric thresholds and decision cells, authoritative G2 outcome map, and accepted-G2-only S3 incomplete/expiry rule. Its exact-byte SHA-256 is canonical. Before G2, scientific candidate pass alone may freeze candidate thresholds and compatibility as non-authoritative diagnostics with zero S3 authority; every adjudicated path requires zero-active S2 reconciliation. Compatibility pass, accepted G2, and APR-G2 promote the exact unchanged candidate digests as authoritative and permit production. Nonaccepted G2 retains diagnostics only when staged after candidate pass; direct candidate-fail or adjudicated-invalid terminal no-go requires candidate artifact paths absent and prohibits placeholder diagnostics.

**Criteria**
- Protocol integrity: the eligibility-rules digest predates screening decisions; final-protocol.json records that exact predecessor digest; and its exact-byte SHA-256 predates every control score authorization. An invalid pre-adjudication non-run may be corrected before G2. Only scientific candidate pass may stage immutable candidate thresholds and compatibility before adjudication, as non-authoritative diagnostics with zero S3 authority. Direct candidate-fail or adjudicated-invalid terminal no-go requires candidate artifact paths absent and prohibits placeholders. Once G2 is adjudicated nonaccepted, the campaign is terminal no-go. Authoritative D-thresholds and D-canary-compat exist only after compatibility pass, accepted G2, and APR-G2 promotion of exact unchanged candidate digests.
- Control validity: governing positives meet the frozen PD-1-facing epitope rule; governing NE1 and NE2 controls meet the frozen A_dec sensitivity, working-positive-control, target-construct, assay-format, and condition-compatibility rules. Ambiguous controls are descriptive or excluded.
- Sampling and independence: the complete reproducible census flow is reported, each positive belongs to one frozen scaffold group, and each negative connected component belongs to one governing stratum and fold and counts once.
- Primary separation statistic: the unweighted mean of cutoff-clean per-scaffold-group held-out AUROC values after the frozen training-only equal-group midrank-percentile transformation; each independent group has weight 1/G, and individual-positive holdout, resubstitution, or observation-weighted pooling is prohibited as decision evidence.
- Candidate uncertainty statistic: the fixed-seed group-bootstrap lower limit may govern and be labelled a one-sided 90 percent lower confidence bound only after the pre-score small-sample calibration and exchangeability checks in comparators_or_adjudication pass. Otherwise it is descriptive for the enumerated controls and cannot authorize go.
- Negative evidence: only unique, directly assayed NE1 and NE2 controls meeting the frozen support and assay-validity fields are go-eligible. NE3 presumed negatives and NE4 scrambles are reported separately and cannot enter or rescue the governing estimate.
- Sensitivity and heterogeneity: report per-group, assay-format, and evidence-class results, matching diagnostics, pooled-versus-equal-group disagreement, and leave-one-group-out influence. Failure prevents G2 acceptance; every adjudicated nonaccepted G2 is terminal no-go for this campaign.
- A go requires at least 6 independent scaffold groups overall and at least 5 cutoff-clean groups, each with at least 3 unique go-eligible negative components, and uses only the prospectively calibrated cutoff-clean equal-group lower confidence bound. If any census, validity, independence, minimum, calibration, coverage, false-go, sensitivity, influence, heterogeneity, or bound rule fails at adjudicated G2, the campaign is terminal no-go.
- Secondary statistics: the held-out fraction of topology-matched negatives scoring above the positive-group median, reported by NE1, NE2, and NE3 class for all groups and cutoff-clean groups; NE4 scramble performance is reported separately as a coarse check.
- Accepted-G2-only cluster-corrected yield: distinct clusters among campaign designs clearing every final frozen threshold, using single linkage at 60 percent global sequence identity and 2.0 Angstrom interface backbone RMSD, with 50 and 70 percent alternatives reported.
- Provenance completeness: every control records census disposition, eligibility, group, fold, unique assignment, diagnostics, stratum, scores, and frozen inputs. After accepted G2 only, every design additionally traces to a seed, pre-compute manifest, and consumed digests. After adjudicated nonaccepted G2, the control-failure record and G2 reconciliation prove zero S3 authorization.
- Artifact integrity: D-control-protocol remains immutable. Direct scientific failure has no candidate artifacts. Scientific candidate pass alone freezes non-authoritative thresholds and compatibility; accepted G2 promotes unchanged passing digests, while compatibility failure retains them without promotion. Every failure binds the zero-active G2 reconciliation.

**Comparators, controls, cases, or adjudication rules**
- Before screening controls, freeze the target- and assay-validity rules as eligibility-rules.json with its own timestamp and detached digest. Before any control score, final-protocol.json must name the numeric A_dec affinity ceiling with units and assay basis; the numeric control operating-point threshold T_control with score direction; the required held-out positive coverage and false-go rate at T_control; the deterministic rule for fitting each candidate production threshold T_prod (the candidate values are learned only after the held-out result); and every ordinary decision-table cell as explicit separation and S3-yield cutoffs with its outcome. Every declared number must have a denominator and a cited or otherwise recorded rationale. The same operating point used for designs must receive held-out coverage and false-go evaluation; AUC alone cannot authorize. A missing value, unit, direction, rationale, denominator, or cell is an invalid non-run: no control score, threshold fit, G2 adjudication, or go authority may proceed. The SHA-256 of the exact stored final-protocol.json bytes remains the sole canonical D-control-protocol digest.
- Use a reproducible control census, not convenience sampling: D-control-protocol names every searched bibliographic and structure source, exact query, coverage dates, search time, deduplication rule, and complete retrieved-to-included flow with exclusion reasons. Before any score is visible, two distinct curators independently screen and classify every record for eligibility, epitope, assay compatibility, scaffold component, fold, and negative assignment without seeing scores. The immutable curation ledger records both decisions, source-evidence digests, timestamps, disagreements, adjudicator identity, rule-based resolution, and any exclusion or descriptive-only disposition. An unresolved disagreement is excluded from governing evidence; no post-score reclassification is permitted.
- A go-eligible positive must have a cited PD-L1 binding measurement and direct evidence that it binds at or competes with OBJ-target's frozen PD-1-facing epitope: a PD-1 competition assay, a complex structure whose interface overlaps the frozen hotspot residue set, or mutational epitope evidence meeting the rule frozen in D-control-protocol. Other PD-L1 binders are descriptive only. At least 8 eligible positives must span at least 6 independent sequence/structure scaffold groups, with at least 5 cutoff-clean groups for a go result.
- Before scoring, freeze conservative connected-component groups: positives are linked by at least 30 percent global sequence identity, binder-domain TM-score at least 0.5, or shared published design lineage or parent scaffold. No connected group may cross folds.
- For each frozen group, record the earliest public date across every linked sequence, structure, design lineage, and parent scaffold. Public availability is not model-training provenance: D-environment must independently verify each learned model's exact release, weight and image digests, training-data cutoff, update history, and treatment of private, licensed, or pre-release data. Classify a group as cutoff-clean only against verified training-data cutoffs, not a release date. If provenance cannot be verified, mark the affected model results and controls contamination-uncertain; they are descriptive only and cannot make a group cutoff-clean, fit authoritative thresholds, satisfy G2, or authorize prospective spend. If no production model has verifiable provenance, G1 is a failed non-run.
- Assign each frozen scaffold group and its negative strata to one leave-one-group-out fold. Collapse duplicate or related negative structures into connected components under the protocol's sequence, structure, and lineage rule; one negative component may belong to exactly one governing group and fold and counts once. If it matches multiple groups, apply the frozen nearest-match metric and tie-breaker before scoring or exclude it.
- The final pre-score D-control-protocol contains complete control membership and exclusions; groups, folds, assignments, eligibility, model and statistical rules, unchanged numeric thresholds and vetoes, clustering cuts, total decision table, and authoritative G2 lifecycle. Invalid non-runs may be corrected before adjudication. Scientific candidate pass alone freezes candidate thresholds and compatibility as non-authoritative diagnostics with zero S3 authority; every path then closes S2 authorization and terminalizes all control batches before exactly one adjudication. Compatibility pass and accepted G2 permit APR-G2 promotion of the exact unchanged candidate digests. Nonacceptance retains diagnostics only when staged after candidate pass; direct candidate-fail or adjudicated-invalid terminal no-go requires candidate artifact paths absent and prohibits placeholder diagnostics. The canonical protocol digest precedes every control-score authorization.
- Within each fold, select or tune filters only on the other scaffold groups and their negatives. Score the held-out group and its negative strata once; no held-out label, score, distribution, or group size may alter that fold's stack, protocol, or transformation.
- Put fold outputs on a common held-out-information-free scale. For held-out raw combined score s in fold f, use the training-only equal-group midrank percentile T_f(s): for each training group, compute the fraction of that group's go-eligible control scores below s plus one half the fraction tied with s, then average those fractions equally across training groups. Freeze higher-is-better direction and the 0.5 tie rule. Held-out observations are evaluated with T_f but never enter its reference distribution.
- Freeze four negative-evidence classes in D-control-protocol. NE1 is an assayed same-scaffold nonbinder linked by the frozen scaffold rule. NE2 is an assayed topology-matched nonbinder outside the positive scaffold group. NE3 is an unassayed target-irrelevant presumed negative supported by a cited irrelevant-target assignment, a documented search finding no PD-L1 binding report, and the frozen topology match. NE4 is a sequence scramble.
- NE1 and NE2 are go-eligible only when the cited direct PD-L1 assay uses the frozen human PD-L1 construct and meets D-control-protocol's numeric sensitivity rule: before screening, define the decision-relevant affinity ceiling A_dec; require analyte exposure through at least 10 times A_dec, a detection limit capable of detecting binding at A_dec, an explicit negative result, and a functioning known PD-L1-binder positive control under the same assay format and conditions. Record target construct, format, immobilization or orientation, temperature, buffer, tested range, detection limit, positive-control identity and result, and compatibility stratum. Missing or incompatible evidence downgrades the record to NE3 if eligible, otherwise excludes it.
- Each governing group stratum requires at least three unique go-eligible NE1 or NE2 negative components; use NE1 where available and report its absence. NE3 is admissible only as a separately labelled descriptive stress test and must never be called a demonstrated nonbinder or enter the governing point estimate or lower limit. NE4 is a secondary coarse check only.
- For every group and negative-evidence class, report counts and provenance plus the frozen matching diagnostics for length, amino-acid composition, coarse topology, within-tolerance status, and match distance; exclude unmatched candidates rather than relaxing tolerances after scores are visible.
- For each cutoff-clean scaffold group g, compute AUC_g from that group's transformed held-out positive scores against its unique go-eligible NE1 and NE2 stratum, with pairwise ties worth 0.5. The governing point estimate is the arithmetic mean of AUC_g across eligible groups, so every independent scaffold group has weight 1/G regardless of positive or negative multiplicity. At the same frozen T_control used by the production decision, report held-out positive coverage or sensitivity and false-go rate with their denominators and uncertainty; these operating-point metrics, not AUC alone, are required for G2. Observation-pooled AUROC is descriptive only.
- Declare the inferential target before scoring: the mean cutoff-clean group AUC and the held-out operating-point coverage and false-go quantities that the decision uses. Use an exact/conservative finite-sample procedure or a pre-score nested calibration of the complete planned estimator, threshold-selection rule, and lower-limit calculation; resampling only stored AUC_g values is descriptive unless this calibration justifies it. The calibration artifact freezes the finite scenario family (null at T_control, group heterogeneity, within-group measurement or label error, assay-format strata, shared-target dependence, and model-contamination uncertainty), planned group and negative minima, code digest, seed, replication design, and acceptance criteria of at least 90 percent coverage and at most 10 percent false-go probability. An independent methods review must verify those operating characteristics before G2.
- If no exact/conservative procedure is justified, or the pre-score calibration, scenario coverage, exchangeability basis, or independent review is absent or fails, report any calculated limit only as a descriptive limit for the enumerated controls. It cannot enter a go cell, support a prospective spend claim, or make G2 accepted. If discovered before G2 adjudication, the attempt is an invalid non-run that may be corrected under the unchanged ceiling; if G2 is adjudicated on this failure, the campaign is terminal no-go and any retry requires a new linked campaign with fresh protocol, provenance, and approvals.
- Report every AUC_g and its positive, NE1, and NE2 denominators; the equal-group mean, standard deviation, range, and interquartile range; the held-out T_control coverage and false-go counts and denominators; observation-pooled AUROC and its difference from the equal-group mean; each leave-one-group-out mean; the complete census and curation flow; effective numbers of unique control components; class-specific analyses; and every compatible assay-format sensitivity. A go requires every frozen sensitivity and operating-point criterion to pass; an adjudicated G2 nonacceptance is terminal no-go for this campaign, never in-campaign revise.
- A pooled result is group-multiplicity-dependent if observation-pooled AUROC and the equal-group estimator fall on different sides of the frozen point threshold. Heterogeneity is decision-material if deleting one eligible group moves the equal-group mean across that threshold or by at least 0.05 AUROC, or if at least two eligible groups have AUC_g at or below 0.50 while the equal-group mean passes. Either condition prohibits G2 acceptance; once adjudicated nonaccepted, the campaign is terminal no-go and the pooled estimate cannot rescue it.
- After zero-active S2 accounting, direct scientific failure or adjudicated-invalid G2 adjudicates nonacceptance with both candidate threshold and compatibility paths explicitly absent and no placeholder diagnostics. Correctable invalid pre-adjudication non-runs remain non-outcomes that may be corrected before G2 and supply no gate evidence. Scientific candidate pass alone fits and freezes non-authoritative thresholds, then compatibility. Compatibility failure retains those staged diagnostics; compatibility pass permits accepted G2 and APR-G2 promotion of their exact unchanged digests. No branch may revise scientific rules.
- Only after accepted G2 may the ordinary decision table consume the prospectively calibrated cutoff-clean equal-group lower limit plus a fixed production-frame yield. Before G1, or at the latest before APR-G2 and before generation, D-environment must freeze the S3 frame: exact batch and slot counts, seed schedule, generation parameters, total authorized slots N_frame, deterministic duplicate and quality rules, cluster unit and cuts, missing/failed-slot treatment, and the uncertainty calculation. Define N_frame as every authorized production slot in that frame; duplicate, invalid, missing, or failed slots cannot be removed after inspection and count as nonpassing. Define K_clusters as distinct passing clusters at the frozen cut and report K_clusters/N_frame plus its predeclared uncertainty and the 50- and 70-percent sensitivity cuts. Any incomplete or adaptively extended frame is a no-decision, not a recalculated yield or ordinary table cell. Descriptive results can never override a failed G2.

**Missing-evidence policy:** Before G2 adjudication, missing or invalid evidence makes the attempt a non-run that may be corrected but supplies no gate evidence. A positive missing a cited PD-L1 assay or frozen PD-1-facing epitope evidence is descriptive or excluded. A purported NE1 or NE2 negative missing the frozen A_dec exposure and detection requirements, compatible target construct and assay conditions, functioning positive control, citation, or explicit negative result is NE3 if it meets the presumed-negative rule, otherwise excluded. A reused negative component is removed from every but its one prospectively assigned stratum; post-score reassignment is prohibited. A group with fewer than three unique go-eligible negatives is ineligible for G2 acceptance. Missing census, exchangeability, calibration, coverage, false-go, sensitivity, influence, heterogeneity, or bound support prevents G2 acceptance. Every adjudicated nonaccepted G2 is terminal no-go for this campaign. After accepted G2 only, a design missing any filter column is failed, not imputed or dropped. Any retry after terminal G2 nonacceptance requires a new linked campaign with no inherited authorization.

**Exploration versus confirmation:** After S2 authorization closure and zero-active accounting, G2 is adjudicated once. Direct scientific failure is terminal_no_go with candidate artifacts absent. Scientific candidate pass alone stages thresholds then compatibility; compatibility failure is terminal_no_go with diagnostics retained, and pass permits APR-G2 promotion. Every nonaccepted branch has zero S3 authority. Numeric rules are unchanged.

**Stop, pivot, and no-go rules**
- Invalid pre-adjudication non-run: if any required pre-score artifact or field is missing or unverifiable—including D-target, D-environment, model provenance, allocation evidence, canary semantics, A_dec, T_control, decision-cell values, curation ledger, or calibration design—or if an authorization predates the canonical protocol digest, quarantine the attempt and do not score or adjudicate G2. It may be corrected before G2 within the unchanged WU-calibrate ceiling and supplies no inherited gate evidence.
- Terminal G2 no-go: if the reproducible census or inclusion flow is absent; a governing positive lacks frozen epitope evidence; a governing NE1/NE2 record fails A_dec sensitivity, working-positive-control, or assay compatibility; or a negative component is reused, any adjudicated G2 is nonaccepted and terminal no-go for this campaign.
- Terminal G2 no-go: if the pre-score calibration artifact or independent methods review is absent, does not exercise the complete planned estimator and operating point, or fails the frozen finite scenario family's at-least-90-percent coverage and at-most-10-percent false-go criteria, report the lower limit as descriptive and adjudicate G2 nonaccepted.
- Terminal G2 no-go: if the prospectively calibrated lower limit, or the held-out T_control positive-coverage or false-go criterion at the same operating point used for designs, fails the unchanged numeric rule. Retuning, regrouping, retransformation, changing the operating point, or reselection after held-out scores are visible is prohibited.
- Terminal G2 no-go: if pooled and equal-group estimates cross opposite sides of the frozen point threshold, leave-one-group-out influence changes classification or moves the mean by at least 0.05 AUROC, at least two eligible groups have AUC_g at or below 0.50 while the mean passes, or any predeclared assay-format sensitivity changes the decision.
- Terminal G2 no-go: fewer than 8 epitope-valid positives spanning 6 independent scaffold groups, fewer than 5 cutoff-clean eligible groups, or fewer than 3 unique go-eligible NE1 or NE2 negative components in any governing group stratum prevents G2 acceptance.
- Terminal G2 no-go: assay-incompatible controls, NE3 presumed negatives, or NE4 scrambles cannot enter or rescue the governing result; an adjudicated result that depends on them is nonaccepted.
- Stop and escalate: a canary fails four times at G1.
- Accepted-G2-only no-decision: if the complete fixed S3 frame cannot finish within its hard stage cap, reserved contingency, or exact allocation expiry, stop new authorization, terminalize S3, record every authorized slot and its status against N_frame, record G3 not accepted, retain partial evidence as non-decision evidence, and do not apply the ordinary table or claim a yield.
- Retry boundary: after any adjudicated nonaccepted G2, retry is prohibited in this campaign and requires a new linked campaign with a new protocol digest, independently verified model provenance, and fresh approvals; retained evidence may be cited but conveys no authorization.
- Deviation downgrade: before G4, any change to a frozen artifact after its gate makes D-memo exploratory and must appear in its first paragraph; after G4, correction requires a new linked campaign record.

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

- **Purpose:** Freeze and execute the control protocol, close and fully reconcile S2 batches, then branch before the one G2 adjudication. Direct scientific failure skips candidate artifacts and terminates no-go. Scientific candidate pass alone stages thresholds then compatibility; pass permits APR-G2 promotion and failure terminates no-go with diagnostics retained. Every nonaccepted branch has zero S3 authority.
- **Prerequisites:**
  - S1
- **Inputs:** D-target, D-environment including the frozen allocation record, G1 raw canary fixtures, and published binder literature.
- **Activities:**
  - Freeze and digest target- and assay-validity eligibility rules before screening any control record
  - Run the predeclared literature and structure census; retain the complete deduplication, screening, exclusion, eligibility, and inclusion flow
  - Freeze groups, folds, unique negative-component assignments, model rules, numeric decision thresholds, small-sample calibration, sensitivities, vetoes, clustering cuts, the total decision table, and the incomplete/expiry no-decision rule outside that table as final D-control-protocol
  - Verify final-protocol.json binds the exact eligibility-rules digest and establish its own exact-byte SHA-256 as the sole canonical D-control-protocol digest before creating or authorizing any control score
  - Run each group fold once under that protocol, tuning only on training groups and preserving held-out predictions
  - Compute per-group, equal-group, class, assay-format, influence, heterogeneity, and pooled-descriptive results and the exact lower limit
  - If the completed control analysis is a candidate pass, fit production thresholds by the frozen rule and freeze them at the candidate path with candidate_pass_non_authoritative status and zero S3 authority
  - Before G2 adjudication, apply the candidate thresholds to stored CAN-pipeline, CAN-energy, and CAN-sequence fixtures, verify CAN-predict compatibility, and freeze the candidate compatibility record as pass or fail without APR-G2 or S3 authority
  - Stop new S2 control-batch authorization; terminalize every active control batch exactly once; verify complete authorized-to-terminal accounting, no duplicate terminal events, and zero active
  - After zero-active accounting, adjudicate G2 exactly once: direct scientific failure proceeds without candidate artifacts; only scientific candidate pass requires staged thresholds followed by compatibility; compatibility pass accepts and promotes unchanged digests, while compatibility failure is terminally nonaccepted
  - On nonacceptance, retain staged diagnostics when present, freeze `deliverables/control-failure.json`, append g2_control_failure_terminal_no_go, freeze the zero-active G2 reconciliation, grant no S3 authority, and authorize only WU-decide's control-failure no-go branch
  - Only after accepted G2 and APR-G2, use the exact allocation expiry and remaining GPU-hours from D-environment to scope S3 to what can complete
- **Outputs:**
  - D-control-protocol, with eligibility rules frozen before screening, final-protocol.json binding the eligibility-rules digest, and the final file's exact-byte SHA-256 serving as the sole canonical deliverable digest before scoring.
  - Pre-adjudication candidate-pass only: immutable non-authoritative candidate threshold and candidate canary-compatibility diagnostics with detached digests and explicit zero S3 authority.
  - Accepted G2 only: APR-G2 promotion records binding the exact unchanged candidate digests as authoritative D-thresholds and D-canary-compat, plus the allocation-bound S3 capacity calculation.
  - Adjudicated nonaccepted G2: immutable failure record and zero-active reconciliation are common; compatibility failure retains candidate paths/digests, while direct scientific failure records both paths absent. APR-G2/APR-G3 and S3 authority are absent.
- **Owner:** ROLE-methods
- **Budget:** 300 A100 GPU-hours; approximately two weeks.
- **Expected pace:** Two weeks. Under-spend here is not a saving: an under-powered control set weakens every downstream claim.
- **Promotion gate:** G2

### S3 — Generate and score the campaign design set

- **Purpose:** Produce candidate designs and score the complete set once against the frozen thresholds, or terminalize fail-closed without G3 acceptance if the complete set cannot finish within the frozen resource or expiry limit.
- **Prerequisites:**
  - S2
- **Inputs:** D-target, D-environment, D-thresholds.
- **Activities:**
  - Before generation, verify the accepted G2/APR-G2 contract and the frozen S3 frame: exact batch and slot counts, seed schedule, generation parameters, N_frame denominator, duplicate/quality rules, cluster cuts, uncertainty calculation, hard cap, reserved contingency, and expiry. Generate only those authorized slots; do not extend the frame after scores are visible.
  - Design sequences onto the backbones
  - Predict complexes and compute interface and liability terms at the identical settings the controls used
  - Apply the frozen thresholds once and record pass/fail per filter per design
  - Cluster survivors at the frozen cut and at both pre-declared alternatives
  - Before any linked retry, terminalize the predecessor as failed or interrupted and reject authorization while any batch with the same frozen inputs and seed remains nonterminal; a retry cannot enlarge the fixed frame or denominator.
  - If the complete fixed frame cannot finish by the hard resource cap, reserved contingency, or frozen allocation expiry, stop new authorization, terminalize every active slot/batch, append incomplete_or_expired, reconcile all N_frame slots, freeze the G3 non-acceptance reconciliation, and do not accept G3 or claim yield.
- **Outputs:**
  - On completion: D-designs, stage cost record, and immutable accepted-complete D-runtime G3 reconciliation. On incomplete/expiry: `deliverables/ranked-designs.partial.csv` plus any other available partial S3 artifacts labelled non-decision evidence, stage cost record, and immutable not-accepted-incomplete/expired D-runtime G3 reconciliation. The live event stream remains appendable only for S4/G4.
- **Owner:** ROLE-comp-lead
- **Budget:** 1,600 A100 GPU-hours hard cap for S3 (M-generate 1,200 plus M-score 400); no adaptive extension. The 50-hour reserve is contingency only and is not additional production capacity.
- **Expected pace:** Four weeks, with a mid-stage checkpoint at 800 GPU-hours. The checkpoint compares completed slots and remaining N_frame against the hard cap and expiry; unexplored branches or under-spend do not permit adaptive sampling. If the fixed frame cannot complete, execute the terminal no-decision branch.
- **Promotion gate:** G3

### S4 — Decide and hand off

- **Purpose:** Finalize exactly one decision branch, append-seal the log after its sole G4 event, and idempotently finish reconciliation and manifest finalization. Closure-in-progress recovery may complete only those deterministic writes; permanent campaign closure begins after they verify.
- **Prerequisites:**
  - S2
- **Inputs:** Ordinary: accepted G2, APR-G2, exact promoted D-thresholds/D-canary-compat digests, accepted G3, APR-G3, complete D-designs digest, and accepted_complete G3 reconciliation digest. Incomplete/expiry no-decision: accepted G2, APR-G2, exact promoted threshold/compatibility digests, terminal not_accepted_incomplete_or_expired G3 reconciliation digest, absent APR-G3, and all retained partial S3 evidence paths/digests. Failed G2: immutable failure record and zero-active reconciliation, plus retained candidate paths/digests for compatibility failure or explicit candidate-path absence for direct scientific failure. Closure recovery is unchanged.
- **Activities:**
  - Ordinary branch: verify and consume accepted G2, APR-G2, exact promoted D-thresholds/D-canary-compat digests, accepted G3, APR-G3, complete D-designs digest, and accepted_complete G3 reconciliation digest; then read the frozen-table cell and record proximity and uncertainty
  - Incomplete/expiry no-decision branch: verify and consume accepted G2, APR-G2, exact promoted D-thresholds/D-canary-compat digests, terminal not_accepted_incomplete_or_expired G3 reconciliation digest, absent APR-G3, and every retained partial S3 evidence path/digest; do not run the table or claim a cell/recommendation
  - After failed G2, consume the immutable control-failure record and zero-active reconciliation; for compatibility failure also consume retained candidate paths/digests, and for direct scientific failure consume their explicit absence; then write terminal no-go without APR-G3, G3, or an ordinary cell
  - Write D-memo leading with the branch outcome and least favourable defensible interpretation
  - Freeze the candidate D-memo version and detached digest; append exactly one matching G4 decision_accepted, no_decision_accepted, or control_failure_no_go_accepted event naming that path and digest as the last complete event-log line; append-seal the stream and enter closure_in_progress
  - Compute the unchanged final log digest, atomically create or verify deterministic final reconciliation and manifest entries without appending or changing frozen artifacts, then mark permanently_closed
  - If interrupted during closure_in_progress, resume only that same hash/reconciliation/manifest finalization; reject a second G4 event, later log bytes, artifact mutation, or mismatched published finalization
  - Package all frozen artifacts and their verified detached manifest for handoff
- **Outputs:**
  - Accepted immutable D-memo version, append-sealed event log ending in exactly one matching G4 event, deterministic final D-runtime reconciliation, complete detached manifest, and permanently_closed state.
- **Owner:** ROLE-methods
- **Budget:** 0 GPU-hours; approximately one week of writing.
- **Expected pace:** One week.
- **Promotion gate:** G4

**Gates**

### G1

- **Stage:** S1
- **Required evidence:**
  - D-target carrying a verified accession, chain, hotspot residue set, and detached manifest digest.
  - D-environment carrying every tool identity/version, weight and image digest, licence, independently verifiable model-training provenance or explicit contamination-uncertain fallback, APR-compute evidence digest, hard caps, reserved contingency, fixed S3 frame, allocation scope, and exact timezone-aware expiry.
  - All four G1 canary manifests showing immutable fixture digests, semantic positive/negative/schema/replay checks, declared units and tolerances or comparison rules, model and seed identity, exact output digests, typed failure status, and pass on labelled non-campaign fixtures; every canary ends at versioned raw output independent of D-thresholds.
- **Owner:** ROLE-methods
- **On failure:** S2 does not start and no allocation beyond the S1 cap is consumed when any target, environment, allocation, model-provenance, sampling-frame, or canary requirement is missing or unverifiable. An allocation assertion is not evidence; an affected model may be used only for descriptive diagnostics under the provenance fallback and cannot authorize G2 or spend. A failed canary is fixed and rerun under the declared retry cap; the fourth failure escalates to ROLE-pi.
- **Criteria:**
  - The target, environment, model provenance, exact allocation evidence, fixed S3 frame, and complete canary specification are frozen and independently checked; all four G1 canaries pass their semantic production-setting checks, raw schemas, and deterministic replays on labelled non-campaign fixtures; missing inputs, unverifiable provenance, missing tolerances, or a process-only canary pass fails G1. No threshold table is applied at G1.

### G2

- **Stage:** S2
- **Required evidence:**
  - D-control-protocol with eligibility-rules and final-protocol detached digests; the dual-curation/adjudication ledger; complete census and inclusion flow; verified model-provenance disposition; exact A_dec, T_control, coverage, false-go, threshold-fitting rule, ordinary decision cells and S3-frame references; exact inferential/calibration code and seed; unchanged vetoes and clustering cuts; authoritative G2 outcome map; and accepted-G2-only S3 no-decision rule. Timestamps prove all freezes occurred at their required boundaries.
  - Common to every adjudication: s2_authorization_closed plus complete authorized-to-terminal control-batch accounting proving exactly one terminal event per authorized batch and zero active.
  - Direct-scientific-failure branch: exact observed control-result digests and failed frozen criterion or veto; candidate threshold and compatibility paths are absent; the terminal failure record and G2 reconciliation attest absent APR-G2/APR-G3 and zero S3 authority.
  - Scientific-candidate-pass branch only: evidence that at least 8 epitope-valid positives span 6 independent groups, at least 5 groups are cutoff-clean under verifiable model provenance, each governing group has at least 3 unique assay-valid NE1/NE2 negative components, T_control coverage and false-go pass, the calibrated lower-limit rule passes, and every other frozen scientific criterion passes; then immutable candidate thresholds bind the canonical protocol digest with candidate_pass_non_authoritative status and zero S3 authority.
  - Scientific-candidate-pass branch only: immutable candidate compatibility binds the candidate threshold digest and records CAN-pipeline, CAN-energy, CAN-sequence, and CAN-predict checks. Compatibility failure supplies terminal-nonacceptance evidence; compatibility pass is required for the single accepted adjudication and APR-G2 promotion of unchanged candidate digests.
  - Accepted branch only: the allocation-record digest, remaining GPU-hours, and timezone-aware expiry bound S3 after APR-G2.
- **Owner:** ROLE-comp-lead
- **On failure:** This is the authoritative control-gate outcome map. Before adjudication, an invalid non-run may be corrected and supplies no gate result. The dispatcher then closes S2 authorization, terminalizes every active control batch exactly once, and verifies complete zero-active accounting. ROLE-comp-lead adjudicates G2 exactly once: direct scientific failure is terminal_no_go with candidate thresholds/compatibility absent; scientific candidate pass alone stages both diagnostics, and compatibility failure is terminal_no_go with them retained. Every nonaccepted branch freezes `deliverables/control-failure.json` and the zero-active G2 reconciliation, appends g2_control_failure_terminal_no_go, omits APR-G2/APR-G3 and authoritative D-thresholds/D-canary-compat, grants zero S3 authority, and authorizes only WU-decide's no-go branch. Any retry is a new linked campaign with no inherited authorization.
- **Criteria:**
  - G2 is adjudicated exactly once only after D-control-protocol predates every score, its numeric operating point and complete decision table are explicit, dual curation and independent calibration evidence are complete, all control analyses report T_control coverage and false-go at the same point used for designs, S2 authorization is stopped, and complete authorized-to-terminal accounting proves one terminal event per control batch with zero active. A direct scientific failure is terminal nonacceptance with candidate paths absent; only a scientific candidate pass stages non-authoritative candidate thresholds and compatibility; compatibility pass permits accepted G2 and APR-G2; every nonaccepted branch has zero S3 authority.

### G3

- **Stage:** S3
- **Required evidence:**
  - D-designs with every fixed-frame slot represented or terminally accounted for, complete threshold columns, cluster assignments and K_clusters/N_frame yield, predeclared uncertainty, per-design seeds and manifests, hard-cap cost ledger, and unchanged D-thresholds and canonical D-control-protocol digests.
  - D-runtime's immutable `deliverables/runtime-g3-reconciliation.md`, recording the highest sequence, exact byte length, and SHA-256 of the `artifacts/runtime/events.ndjson` prefix through G3.
  - G3 reconciliation proving every authorized S3 batch has exactly one completed, failed, or interrupted terminal event, no output lacks prior authorization, and no completed batch or frozen-input-and-seed retry lineage was dispatched concurrently or twice. The live stream remains open only for S4/G4.
- **Owner:** ROLE-methods
- **On failure:** A post-G2 change to D-thresholds, the S3 frame, denominator, or uncertainty rule is prohibited: stop new authorization, preserve all evidence under the producing digest, and require a new linked campaign with fresh review and authority. This campaign cannot apply the ordinary table or close through an invented deviation branch. If the complete unchanged frame cannot finish within the hard S3 cap, reserved contingency, or frozen allocation expiry, stop new authorization, terminalize every nonterminal slot/batch, append incomplete_or_expired, freeze the G3 non-acceptance reconciliation with N_frame accounting, and record G3 not accepted; this enables only WU-decide's no-decision branch and never satisfies APR-G3.
- **Criteria:**
  - G3 is reachable and accepted only after accepted G2 and APR-G2, when every slot in the fixed S3 frame has been scored or terminally accounted for exactly once against unchanged D-thresholds with complete provenance, N_frame and K_clusters are reported under the frozen denominator and uncertainty rule, no active batch remains, and no post-hoc threshold, frame, denominator, or extension change occurred. Incomplete or expired S3 is G3 not accepted and can lead only to no-decision. Adjudicated nonaccepted G2 prohibits G3 entirely.

### G4

- **Stage:** S4
- **Required evidence:**
  - The accepted immutable D-memo states the ordinary cell after accepted G2 and G3; no-decision after accepted G2 but terminal incomplete/expired G3; or terminal control-failure no-go after adjudicated nonaccepted G2, binding `deliverables/control-failure.json` and the immutable G2 reconciliation and recording absent APR-G2/APR-G3 and zero S3 authorization.
  - Exactly one G4 decision_accepted, no_decision_accepted, or control_failure_no_go_accepted event, matching the branch, naming the accepted memo path and detached SHA-256 digest, and forming the last complete event-log line with no later bytes.
  - D-runtime's deterministic final reconciliation and detached manifest cover the unchanged complete event-log bytes through the sole G4 event. If interrupted after that event, closure recovery only hashes and finalizes or verifies these records without appending or changing frozen artifacts; permanent closure begins only when both verify.
  - The complete accepted-G2 artifact set for an ordinary decision; retained partial S3 evidence for no-decision; or the complete terminal control-failure record and G2 reconciliation for control-failure no-go, with the detached manifest reproducing from stored artifacts.
- **Owner:** ROLE-pi
- **On failure:** Return a branch-mismatched memo, a nonaccepted-G2 memo that treats candidate diagnostics as authoritative, or any result implying unauthorized G3/go. After the sole G4 event, later log bytes, a second G4 event, frozen-artifact mutation, or mismatched finalization fail closed. An interruption with that valid event last and no later bytes resumes only idempotent closure finalization; a PI override cannot reopen S3.
- **Criteria:**
  - After accepted G2 and G3, the recommendation is the ordinary cell mechanically reached on the frozen decision table. After accepted G2 but terminal incomplete/expired G3, the outcome is no-decision outside that table. After adjudicated nonaccepted G2, the outcome is terminal control-failure no-go bound to the complete control-failure record and zero-active G2 reconciliation. Every branch freezes one D-memo, appends exactly one matching G4 event as the last log line, completes idempotent closure reconciliation and manifest finalization, and only then becomes permanently closed.

## 9. Resources and fail-closed dispatch

**Budgets**
- Total compute: at most 2,000 A100 GPU-hours under APR-compute. Hard ledger: S1 cap 50 (all four G1 canaries and reruns), S2 cap 300 (control runs, dual curation, calibration, and permitted infrastructure reruns), S3 cap 1,600 (M-generate 1,200 plus M-score 400), and S4 cap 0. Reserve exactly 50 GPU-hours as contingency for declared failed/repeated jobs and overhead; it is not production capacity and cannot be used without the pre-score contingency rule.
- Cash: USD 0. The campaign authorizes no expenditure of any kind.
- Budget floor: the 800 GPU-hour S3 checkpoint compares completed slots and remaining fixed-frame work; under-spend with unexplored branches is incomplete and escalates to ROLE-pi rather than permitting adaptive sampling.
- Calendar: approximately twelve weeks but never beyond the exact allocation expiry recorded in D-environment.
- Calendar ceiling: at every gate ROLE-methods computes cumulative elapsed time, slot completeness, hard-cap consumption, reserve use, and remaining capacity against the frozen allocation record.
- Expiry and overrun rule: no stage may exceed its hard cap, the shared reserve, or the exact expiry. If the complete fixed S3 frame cannot finish, stop new authorization, terminalize every authorized slot/batch, record incomplete_or_expired with N_frame accounting, and dispatch only WU-decide's no-decision branch without applying the table or claiming yield.

**Access constraints**
- Compute: a standing institutional allocation is asserted but is not usable until D-environment contains independently verified approval evidence, scope, hard stage caps, reserved contingency, available hours, and exact timezone-aware expiry. No compute or control score starts on the assertion alone.
- Data: public structural data and published literature only. No proprietary, personal, or restricted data is used.
- Software: used under published licences, with each licence determination recorded in D-environment at S1.
- Synthesis and wet-lab: no access exists and none is sought. This is a prohibited action, not a pending approval.

**Concurrency:** Only after accepted G2 and APR-G2 may design batches within S3 run concurrently up to the cluster allocation, never under more than one nonterminal batch ID for the same frozen inputs and seed. An adjudicated nonaccepted G2 permits zero S3 authorization. Stages are sequential, except S4 may follow S2 directly for the terminal control-failure branch.

**Dispatch rules**
- S2/WU-calibrate dispatch requires accepted G1 and APR-G1 plus exact current digests for D-target, D-environment, APR-compute evidence, the fixed S3 frame, and all four passing G1 canary manifests. WU-freeze completion, stored artifacts, or a worker self-report never authorize S2; a failed, missing, stale, or nonaccepted G1 rejects every S2 authorization.
- Every S3/WU-generate authorization requires accepted G2, APR-G2, exact promoted authoritative D-thresholds and D-canary-compat digests, the unchanged canonical D-control-protocol digest, fixed-frame capacity and expiry, and no nonterminal batch with the same frozen inputs and seed. WU-calibrate completion, candidate diagnostics, or a single nonconcurrent batch never suffice.
- Branch guards override WU-decide's structural WU-freeze dependency. Ordinary WU-decide dispatch requires accepted G2, APR-G2, exact promoted authoritative D-thresholds/D-canary-compat digests, accepted G3, APR-G3, complete D-designs digest, and immutable accepted_complete G3 reconciliation digest. Incomplete/expiry no-decision dispatch requires accepted G2, APR-G2, exact promoted threshold/compatibility digests, terminal not_accepted_incomplete_or_expired G3 reconciliation digest, absent APR-G3, and every retained partial S3 evidence path/digest. Failed-G2 dispatch requires terminal G2 nonacceptance, immutable failure record, zero-active G2 reconciliation, absent APR-G2/APR-G3, and zero S3 authorization; compatibility failure additionally requires retained candidate paths/digests, while direct scientific failure requires explicit candidate-path absence. No other predicate dispatches WU-decide.
- Dispatch is fail-closed: a work unit whose branch-specific authoritative inputs are not present at their recorded digests does not start. Before G2 only an invalid non-run may return to WU-calibrate. After adjudicated nonacceptance, any retry is a new linked campaign with no inherited gate, work-unit, compute, or dispatch authorization.
- No work unit may exceed its hard resource_ceiling or consume the shared 50-GPU-hour contingency outside the pre-score contingency rule. Reaching a stage cap, exhausting the reserve, or reaching exact expiry stops new authorization and executes the branch-specific terminal no-run/no-decision path; it does not silently continue.
- The stage owner is the single source of truth for stage status. A worker's self-report is evidence, not acceptance.
- External actions are prohibited campaign-wide. There is no dispatch path to a vendor, a purchase, or a wet-lab action.
- Only the single ROLE-comp-lead dispatcher may append runtime records or authorize batches. Before G2 adjudication it appends s2_authorization_closed, terminalizes every active control batch exactly once, and proves complete zero-active accounting. Before G3 it likewise accounts for every S3 batch. While holding the append lock, it rejects retry until the predecessor is terminal and no same-input-and-seed batch is nonterminal.
- After a sole valid G4 event becomes the last complete line, dispatch enters closure_in_progress: no work unit or event may dispatch. A resumed process may only hash unchanged log bytes and atomically create or verify deterministic final reconciliation and manifest entries; permanent closure begins after both verify.

**Approvals**
- **APR-compute:** Standing institutional GPU allocation is claimed. D-environment must freeze the independently verified approval record digest, scope, available GPU-hours, hard stage caps, reserved contingency, exact timezone-aware expiry, and retrieval time before G1 acceptance; absent evidence supplies no compute authority.
- **APR-G1:** G1 acceptance: target and environment frozen, all four canaries passing.
- **APR-G2:** Issued exactly once only after candidate thresholds and compatibility are frozen, compatibility passes, S2 authorization is closed, every authorized control batch is terminal exactly once, and G2 is accepted. APR-G2 promotes the exact unchanged candidate digests as authoritative D-thresholds/D-canary-compat and authorizes S3; it is absent on nonacceptance.
- **APR-G3:** Accepted-G2 branch only: G3 acceptance when the complete design set is scored once against unchanged thresholds with full provenance; incomplete or expired S3 is G3 not accepted. APR-G3 is absent after adjudicated nonaccepted G2.
- **APR-G4:** G4 accepts the branch-matching immutable memo and sole G4 event. That event enters closure_in_progress and append-seals the log; deterministic final reconciliation and manifest finalization must verify before permanent closure and reproducible handoff.
- **APR-deviation:** Approval of a numbered post-freeze deviation before G4 closure, which downgrades D-memo to exploratory. Post-G4 correction requires a new linked campaign record.

## 10. Delegation

**Roles**

### ROLE-pi — Principal investigator

- **Description:** Holds the synthesis budget and receives the recommendation.
- **Responsibility:** Accepts G4 for either a mechanically reached recommendation or a fail-closed no-decision outcome. Decides whether to act on a recommendation; no-decision carries no recommendation to act on.
- **Authority:** Sole authority to accept the recommendation, to override the decision table on the record, and to authorize any subsequent wet-lab campaign.
- **Limits:** Does not score designs, set thresholds, or edit any frozen artifact. An override is recorded as an override.

### ROLE-comp-lead — Computational design lead

- **Description:** Runs generation, prediction, and scoring.
- **Responsibility:** Owns S1 and S3 and maintains provenance, cost, and single-dispatcher runtime records. Accepts G2, a gate on a stage it does not execute.
- **Authority:** Allocates GPU-hours within the stage budgets; declares canary pass or fail.
- **Limits:** Cannot alter D-thresholds after G2, cannot order synthesis, cannot contact a vendor, and owns no gate on a stage it executes: G1 and G3 are accepted by ROLE-methods, and ROLE-comp-lead accepts G2, which it does not execute.

### ROLE-methods — Methods and calibration lead

- **Description:** Owns control selection, threshold calibration, and the decision table.
- **Responsibility:** Owns S2 and S4, accepts G1 and complete G3 on stages it does not execute, and records G3 not accepted when S3 terminalizes incomplete or expired.
- **Authority:** Fixes the threshold values, clustering cuts, and decision table before freeze.
- **Limits:** Before G4, may not change thresholds, cuts, or the decision table after G2 except by a numbered deviation approved by ROLE-pi, which downgrades the memo to exploratory. After G4, this campaign permits no correction; a new linked campaign record is required. Does not accept G2, the gate on its own stage.

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
- **Verification and acceptance:** G1 evidence is complete: verified target and detached digests, pinned tools and licences, independently verifiable model provenance or an explicit contamination-uncertain fallback that blocks prospective use, exact APR-compute evidence, hard caps and reserve, fixed S3 frame, and four passing semantic canary manifests. Every canary proves deterministic raw-schema transport on labelled non-campaign fixtures without consulting or applying D-thresholds; process exit status alone is insufficient.
- **Resource ceiling:** 50 A100 GPU-hours and two calendar weeks.
- **Retry and failure classes:** A failed canary may be fixed and rerun without escalation up to three times; the fourth failure escalates to ROLE-pi.
- **Escalation and handoff:** Escalate to ROLE-pi if no PD-1:PD-L1 structure verifies with adequate interface density, if a required tool's licence forbids the intended use, or if the two-week ceiling is reached.

### WU-calibrate — Freeze and execute D-control-protocol, close S2 authorization, and reconcile every control batch to one terminal event with zero active. Direct scientific failure then adjudicates terminal nonacceptance without candidate artifacts. Scientific candidate pass alone stages thresholds and compatibility; compatibility determines accepted promotion versus terminal nonacceptance. Every path adjudicates once and grants no S3 authority without APR-G2.

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

### WU-generate — Generate and score exactly the frozen S3 frame once against the frozen thresholds, with complete provenance, slot accounting, and no adaptive extension.

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

### WU-decide — Finalize the exact eligible decision branch, freeze D-memo, append exactly one matching G4 event as the last log line, then idempotently hash and finalize reconciliation plus manifest. If interrupted after the event, resume only finalization; mark permanent closure only after verification.

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

## 11. Durable operations and recovery

**Continuous runtime enabled:** True

**Continuation trigger:** Work resumes from canonical state and the event log, never chat history. Before permanent closure, a new session reads the last event and frozen digests. If exactly one valid G4 event is the last complete line with no later bytes and final reconciliation or manifest is absent, it resumes only closure_in_progress finalization from unchanged bytes. If both verify, the campaign is permanently closed. No resumed closure may append, rerun a decision branch, or change a frozen artifact.

**State store:** Canonical campaign state remains in the campaign state directory. Frozen research artifacts live at their declared deliverable paths. Exact-byte SHA-256 digests are stored separately in UTF-8 `artifacts/MANIFEST.sha256`; an artifact never embeds the digest that identifies itself.

**Event log:** Live path: `artifacts/runtime/events.ndjson`, UTF-8 JSON Lines schema rescamp-runtime-event-v1. G2 adjudication requires s2_authorization_closed and exactly one terminal event per authorized control batch with zero active. A single g2_accepted or g2_control_failure_terminal_no_go records the outcome. Exactly one branch-matching G4 event must be the last complete line; its durable append seals the event stream and sets closure_in_progress. Final reconciliation and manifest finalization are out-of-log deterministic records and append no bytes. Permanent closure starts only after they verify the exact sealed-log digest.

**Checkpoint policy:** Checkpoint every artifact freeze, gate decision, and batch transition. Before the single G2 adjudication, append s2_authorization_closed, terminalize every active control batch exactly once, and verify complete zero-active accounting. Direct scientific failure proceeds to terminal nonacceptance with candidate diagnostics absent. Scientific candidate pass alone freezes candidate thresholds and compatibility; compatibility failure is terminally nonaccepted, while compatibility pass permits g2_accepted and APR-G2 promotion. G4 closure behavior is unchanged.

**Liveness:** The single dispatcher records a timezone-aware heartbeat event for each active batch at least once per working day. A batch without a heartbeat or terminal event for more than one working day is stalled and escalated to its stage owner. A chat session ending is not stage completion.

**Recovery:** Before G2 adjudication, quarantine and identically rerun only an invalid non-run. For terminal G2 no-go, first stop S2 authorization and terminalize every active control batch exactly once; only zero-active complete accounting permits the failure event and reconciliation. After a sole valid G4 event with no later bytes, closure_in_progress recovery may only verify the frozen memo/event, hash the unchanged log, and atomically create or verify final reconciliation and manifest entries. It must not append, alter frozen artifacts, or repeat G4. Later bytes, a second G4 event, or mismatched published finalization fail closed. Permanent closure begins after successful verification.

**Idempotency:** Unique IDs and one dispatcher prevent duplicate dispatch and terminal events. G2 is adjudicated once after complete S2 accounting. Candidate artifacts are promoted only by APR-G2 and never rewritten. A valid last-line G4 event is unique: if finalization is interrupted, recovery recomputes the same log digest and atomically creates or verifies the same deterministic reconciliation and manifest entries without appending or mutating frozen artifacts. Existing matching finalization is success; mismatched bytes fail closed. Permanent closure follows verified finalization.

A conversational session is not a scheduler.

**Plan continuity and amendments**

Use `campaign.json` at `sha256:5027fd0be0557eb8d85df05f7cfaf0b401cb53b8d44e921242fd400e48948c39` as the active contract.

If execution reveals a material plan change, pause affected future work, apply the explicit state edits, and run the targeted quality loop to freeze a new digest before continuing. Never rewrite a frozen plan in place: a pending brief carrying an older digest is stale, while completed artifacts remain bound to the version that produced them.

## 12. Ethics, safety, rights, and external actions

**Constraints**
- No human subjects, no personal data, no clinical material, and no animal work at any point.
- All structural data and literature used are public. No proprietary or restricted data enters the campaign.
- Software is used within its licence; a licence forbidding the intended use excludes the tool at S1 rather than being disclosed after the fact.
- PD-L1 is a human immuno-oncology target and the designs are candidate binders to a therapeutic target. The campaign produces sequences and scores only; it produces no physical material and authorizes no synthesis.
- No design sequence is transmitted to any external vendor, service, or synthesis provider under this campaign.
- Claim discipline is a safety constraint here, not only a reporting one: an in-silico score presented as evidence of binding could cause the PI to commit spend on a false premise.
- No external action is permitted under this campaign: ordering genes, contacting a synthesis vendor, transmitting any design sequence outside the institution, and initiating wet-lab work are prohibited for every role, including ROLE-pi acting under this campaign. Any future linked wet-lab campaign must separately record institutional biosafety, sequence-screening, data/IP, and downstream-authority reviews before synthesis or transfer; those approvals are outside this computational campaign and cannot be inferred from its outcome.
- Retrieving public structural data and published literature is read-only use of public resources and is not an external action in this sense.

**External actions**
- None recorded

**Human approval points**
- **HAP-freeze:** Freezing thresholds and the decision table at G2, after which the campaign is confirmatory.
- **HAP-accept:** Accepting the recommendation or fail-closed no-decision outcome at G4.
- **HAP-deviation:** Approving any post-freeze deviation to a frozen artifact before G4 closure; after G4, any correction requires a new linked campaign record.
- **HAP-wetlab:** Authorizing a separate wet-lab campaign. This campaign authorizes it under no outcome.

## 13. Reporting and claim discipline

**Claim rules**
- Never state or imply that a design binds PD-L1. Permitted form: the design cleared the frozen in-silico filter stack at rank N.
- Only after accepted G2 and APR-G2 may a ranking exist; every such ranking claim cites the frozen D-thresholds digest it was scored against.
- Control separation is reported as a distribution comparison with overlap. Every failed G2 reports the immutable failure record and zero-active reconciliation. Compatibility failure also reports retained candidate paths/digests as non-authoritative; direct scientific failure reports both candidate paths explicitly absent and creates no placeholder. Neither branch claims downstream design evidence or an ordinary table cell.

**Negative/null/failed result policy:** Every failed G2 uses the immutable failure record plus zero-active reconciliation as complete no-go evidence. Compatibility failure retains and binds candidate diagnostic paths/digests as non-authoritative. Direct scientific failure records and consumes both candidate paths explicitly absent and forbids placeholders. Both omit authoritative threshold/compatibility promotion, S3, G3, and the ordinary table. Accepted-G2 negative branches are unchanged.

**Deviation policy:** Before G2, a permitted repair follows the numbered-deviation rule and frozen predecessors remain immutable. After accepted G2, thresholds, settings, the S3 frame, denominator, and uncertainty rule cannot change in this campaign; stop authorization and open a separately identified linked campaign with fresh review and authority. Before the sole G4 event, only memo wording that leaves consumed evidence and the mechanically derived branch unchanged may be corrected. Once G4 is appended, only deterministic final reconciliation and manifest finalization from unchanged bytes may resume; every later correction requires a new linked campaign.

Lead with the least favorable defensible interpretation.

**Recorded claims**

### CLM-separation — Under the immutable D-control-protocol, the leave-one-scaffold-group-out procedure either supplies protocol-valid control evidence accepted at G2 and then recorded in D-thresholds, or supplies the observed failed-control evidence bound in the terminal control-failure record when G2 is adjudicated nonaccepted.

- **Inquiry:** INQ-separation
- **Support:**
  - The pre-score D-control-protocol and its detached digest plus the complete census and eligibility flow; after accepted G2, D-thresholds binding that digest with observed held-out predictions, group-balanced estimates, assay-format sensitivities, and lower-limit classification; after adjudicated nonaccepted G2, the immutable terminal control-failure record and G2 reconciliation binding the protocol and all observed control-result digests.
- **Counterevidence and objections:**
  - Residual sequence, scaffold, or topology confounding; small numbers of independent positive groups; published binders being unrepresentative of what this pipeline generates; assay heterogeneity across the papers supplying the positives.
- **Verification:** Verify protocol timing, census, eligibility, unique components, and all observed result digests. If scientific candidate pass was reached, verify candidate thresholds and compatibility were frozen before adjudication as immutable non-authoritative diagnostics with zero S3 authority. After accepted G2, verify compatibility passed and APR-G2 promoted their exact unchanged digests. After nonacceptance, verify diagnostics only when staged after candidate pass; for direct candidate-fail or adjudicated-invalid terminal no-go, verify both candidate artifact paths are absent and no placeholder diagnostics exist. In every nonaccepted branch verify the terminal failure record, zero-active G2 reconciliation, absent APR-G2/APR-G3, zero S3 authorization, and no authoritative D-thresholds or D-designs.
- **Status:** unevaluated
- **Uncertainty:** This is a methodological claim about enumerated published controls, not evidence that campaign designs bind. Publication and availability bias, assay heterogeneity, small independent-group counts, and residual model-training contamination limit transfer. If any required control rule fails at adjudicated G2, the campaign terminates no-go before production thresholds, generation, scoring, D-designs, or G3.
- **Reporting rule:** Report the enumerated control frame, inclusion denominator, label-validity and independence checks, effect distribution, and whether the lower limit is calibrated-confidence or descriptive. An invalid pre-adjudication non-run may be corrected before G2 and supplies no gate evidence. Under the authoritative G2 outcome map, every adjudicated nonaccepted G2 is terminal no-go for this campaign; it is not bounded revise, and any retry requires a new linked campaign with no inherited authorization.

### CLM-recommendation — The outcome delivered to the principal investigator is exactly one branch: the ordinary frozen-table recommendation after accepted G2, APR-G2, and accepted G3; no-decision after accepted G2 and APR-G2 but terminal incomplete or expired S3 with G3 not accepted; or terminal no-go after adjudicated nonaccepted G2.

- **Inquiry:** INQ-spend
- **Support:**
  - Ordinary branch: accepted G2 and APR-G2 promoting the exact unchanged candidate threshold and compatibility digests, accepted G3, authoritative D-thresholds, complete D-designs, and cluster-corrected yield.
  - Accepted-G2 no-decision branch: APR-G2, immutable terminal incomplete_or_expired S3 event and G3 non-acceptance reconciliation, allocation and completeness accounting, and retained partial S3 evidence explicitly labelled non-decision evidence; G3 is not accepted and no ordinary table cell or recommendation exists.
  - Failed-G2 branch: immutable failure record and zero-active G2 reconciliation are common. Compatibility failure binds retained staged candidate threshold and compatibility paths/digests. Direct scientific failure or adjudicated-invalid G2 binds explicit absence of both candidate artifact paths and attests that no placeholder diagnostics exist. Correctable invalid pre-adjudication non-runs are not adjudicated outcomes and remain outside this terminal branch. APR-G2, S3 authority, D-designs, G3, and the ordinary table are absent.
- **Counterevidence and objections:**
  - That a mechanical table oversimplifies a judgement the PI should make holistically.
  - The table's purpose is to prevent the judgement from being made after seeing which designs look attractive, not to remove the PI's authority; the PI may override it and the memo records the override as such.
- **Verification:** Ordinary branch: verify accepted G2, APR-G2 promotion of unchanged candidate digests, accepted G3, D-thresholds, complete D-designs, and the mechanically derived cell. Accepted-G2 no-decision branch: verify APR-G2, terminal incomplete_or_expired S3 evidence, immutable G3 non-acceptance reconciliation, G3 not accepted, retained partial evidence labelled non-decision, table not run, no cell, no recommendation, and matching G4 no_decision_accepted event. Failed-G2 branch: verify the control-failure record, zero-active G2 reconciliation, absent APR-G2 and S3 authority, and matching G4 control_failure_no_go_accepted event.
- **Status:** unevaluated
- **Uncertainty:** The ordinary table is eligible only after accepted G2, APR-G2, and accepted G3. Accepted G2 does not resolve incomplete or expired S3: partial design evidence cannot support a cell or recommendation, so that branch remains no-decision. Adjudicated nonaccepted G2 makes every go path unreachable in this campaign; any future attempt requires a new linked campaign.
- **Reporting rule:** After accepted G2, APR-G2, and accepted G3, state the ordinary decision-table cell and recommendation first. After accepted G2 and APR-G2 but terminal incomplete or expired S3, state no-decision first, bind the terminal S3 evidence and G3 non-acceptance reconciliation, retain partial evidence as non-decision evidence, and claim neither an ordinary cell nor a recommendation. After adjudicated nonaccepted G2, state terminal control-failure no-go first. A PI override is recorded with its reason and cannot convert no-decision or failed-G2 evidence into go authorization.

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

## 15. Independent challenge

Reviewers are read-only and bound to the frozen content and rubric digests.

**Weakest independence rung among required reviews:** 2 — separate agent context

The weakest rung bounds the challenge, not the strongest: one sequential pass in the set means the set is only as independent as that pass.

Rungs: 1 sequential self-critique < 2 separate agent context < 3 separate agent blinded to conclusions < 4 human domain expert < 5 external adjudicator with its own data. Rungs 1–3 are agent review: they check internal coherence and are **not** external validation. The mode is self-attested — recorded for audit, never proven.

- **methods-evidence:** pass — Pass for the static methods-and-evidence design under the least-favorable defensible interpretation. This is a new-project plan: claims are explicitly unevaluated, D-target and controls are not yet pinned or selected, no designs exist, and the packet supplies no observed gate or binding evidence. That absence is not misrepresented as a result; instead, target, environment, allocation, model provenance, canaries, eligibility, census, protocol identity, operating-point rules, calibration, and the fixed production frame are prospective fail-closed prerequisites. The plan blocks post-score retuning, leakage, negative reuse, and unsupported binding claims; requires accepted G2 plus exact-unchanged APR-G2 promotion before production; makes adjudicated nonaccepted G2 terminal no-go with zero S3 authority; and makes accepted-G2 incomplete or expired S3 no-decision. No material methods/evidence finding remains. Operations sections were omitted by design and were not inferred absent. (mode: independent-subagent, reviewer: methods-evidence-final-independent-20260826-200429)
- **operations-reproducibility:** pass — Pass. This is a coherent prospective plan, not an execution record: starting_point explicitly has no accepted work or inherited artifacts, and kickoff and gate text condition authority on future frozen artifacts and semantic canary, control, and runtime evidence. Under the least-favorable defensible interpretation, the plan is fail-closed across G1 through G4, separates candidate diagnostics from authoritative promotion, binds exact-byte digests and event-log reconciliation, bounds compute, expiry, and retries, and prohibits synthesis, vendor, and wet-lab actions. No falsely claimed observed result was found. This pass does not attest that any target, tool, canary, allocation, control, design, or closure artifact exists or passed. (mode: independent-subagent, reviewer: ops-repro-independent-final-PaloVerde-20260827T030225Z)

## 16. Kickoff

**Command:** Begin WU-freeze. Read the campaign constitution and D-target's schema, then retrieve and verify a PD-1:PD-L1 co-crystal structure against RCSB, recording accession, chains, method, resolution, interface density gaps, and the coordinate file digest. Do not generate any design, do not score anything other than canary inputs, and do not set or imply any filter threshold. Stop at G1.

**First gate:** G1

**Initially unverified backlog**
- Verify a PD-1:PD-L1 co-crystal structure against RCSB and record its accession, chains, method, resolution, and file digest
- Define the hotspot residue set in the deposited numbering and write D-target
- Pin every tool identity, version, weight digest, image digest, and licence into D-environment
- Run CAN-predict, CAN-energy, CAN-pipeline, and CAN-sequence at production settings and record their manifests
- Confirm the scorer ingests canary output end to end, then present G1 evidence to ROLE-methods, which accepts G1 on a stage it does not execute
