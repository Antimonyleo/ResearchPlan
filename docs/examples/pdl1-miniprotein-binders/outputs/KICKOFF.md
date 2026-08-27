# Kickoff: Can our computational pipeline design de novo miniprotein binders to the PD-1-binding face of human PD-L1 that clear frozen…

**Status:** EXECUTION-READY

**Campaign contract:** `campaign.json` @ `sha256:4201beff8f1a98084b0d9b8b80ddb4ac490d1443def126eee71540d5ae1401d8`

## Start here

Begin WU-freeze. Read the campaign constitution and D-target's schema, then retrieve and verify a PD-1:PD-L1 co-crystal structure against RCSB, recording accession, chains, method, resolution, interface density gaps, and the coordinate file digest. Do not generate any design, do not score anything other than canary inputs, and do not set or imply any filter threshold. Stop at G1.

## First gate

**G1**

- The target, environment, model provenance, exact allocation evidence, deterministic reserve policy, fixed S3 frame with a worst-case fit proof, and complete canary specification are frozen and independently checked; all four G1 canaries pass the same threshold-independent semantic, raw-schema, two-same-seed/one-different-seed replay contract on labelled non-campaign fixtures; the distinct independent G1 review record is complete and bound by digest; missing inputs, unverifiable provenance, missing numeric predicates, or a process-only canary pass fails G1. No threshold table or D-canary-compatibility check is applied at G1.
- **Required evidence:**
  - D-target carrying a verified accession, chain, hotspot residue set, and detached manifest digest.
  - D-environment carrying every tool identity/version, weight and image digest, licence, independently verifiable model-training provenance or explicit contamination-uncertain fallback, APR-compute evidence digest, hard caps, deterministic reserve policy, fixed S3 frame and worst-case fit proof, allocation scope, and exact timezone-aware expiry.
  - All four G1 canary manifests showing immutable fixture digests, threshold-independent semantic positive/negative/schema checks, two same-seed and one different-seed replay checks, declared numeric units/tolerances or comparison rules, model and seed identity, exact output digests, typed failure status, and pass on labelled non-campaign fixtures; every canary ends at versioned raw output independent of D-thresholds.
  - Independent G1 review record with distinct reviewer and executor/session identities, timestamps before APR-G1, exact consumed digests, findings/verdict, artifact path, and detached digest.
- **Owner:** ROLE-methods
- **On failure:** S2 does not start and no allocation beyond the S1 cap is consumed when any target, environment, allocation, model-provenance, sampling-frame, canary, numeric-predicate, or independent-review requirement is missing or unverifiable. An allocation assertion is not evidence; an affected model may be used only for descriptive diagnostics under the provenance fallback and cannot authorize G2 or spend. Only a typed infrastructure non-run may receive an identical-input, identical-spec retry under the attempt ceiling. A semantic, schema, or provenance failure is terminal for that attempt; a changed fixture, tool, image, schema, or criterion requires a new frozen version and fresh independent G1 review. After the fourth infrastructure failure or any unresolved G1 prerequisite, append the pre_g2_no_run_terminal record and grant no S2/G2/S3 authority.

## Initially unverified backlog

- Verify a PD-1:PD-L1 co-crystal structure against RCSB and record its accession, chains, method, resolution, and file digest
- Define the hotspot residue set in the deposited numbering and write D-target
- Pin every tool identity, version, weight digest, image digest, and licence into D-environment
- Run CAN-predict, CAN-energy, CAN-pipeline, and CAN-sequence at production settings and record their manifests
- Confirm the scorer ingests canary output end to end, then present G1 evidence to ROLE-methods, which accepts G1 on a stage it does not execute

## Standing rules

- Freeze before you look: the target definition, software environment, protocol, thresholds, cuts, decision table, frame, denominator, uncertainty rule, and branch evidence are frozen with digests before their authority boundary. After G2 adjudication, no substantive change to any of those inputs, settings, tools, models, images, or approvals is permitted in this campaign; preserve the evidence and open a new linked campaign with fresh review and authority. Before the sole G4 event, only non-substantive memo wording may be corrected when consumed evidence and the branch are byte-identical.
- Provenance: every structure, weight file, container image, seed, score table, and runtime record is recorded with its source, version or accession, retrieval time, and digest. Artifact digests are SHA-256 over the exact stored bytes; digests are written to the detached UTF-8 `artifacts/MANIFEST.sha256`, never embedded in the bytes they identify.
- Controls before candidates: no design is scored until the positive and negative control sets have been run through the identical pipeline and their separation recorded.
- Fail closed on authority: no worker may order genes, commit synthesis spend, contact a vendor, or begin wet-lab work. The campaign terminates at a mechanically supported recommendation only on an eligible branch, or at an explicit no-decision, control-failure no-go, or pre-G2 no-run with zero downstream authority.
- Reporting: after accepted G2, a no-go recommendation is reported with the same completeness as go, including the full ranked design table and every failed filter. After adjudicated nonaccepted G2, the immutable terminal control-failure record is the complete evidence package; generation, scoring, D-designs, a ranked design table, and G3 are prohibited and therefore not required.

Read `CAMPAIGN_PROMPT.md` for the full campaign constitution before acting.
