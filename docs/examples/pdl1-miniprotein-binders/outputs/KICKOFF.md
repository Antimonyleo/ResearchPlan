# Kickoff: Can our computational pipeline design de novo miniprotein binders to the PD-1-binding face of human PD-L1 that clear frozen…

**Status:** EXECUTION-READY

**Campaign contract:** `campaign.json` @ `sha256:5027fd0be0557eb8d85df05f7cfaf0b401cb53b8d44e921242fd400e48948c39`

## Start here

Begin WU-freeze. Read the campaign constitution and D-target's schema, then retrieve and verify a PD-1:PD-L1 co-crystal structure against RCSB, recording accession, chains, method, resolution, interface density gaps, and the coordinate file digest. Do not generate any design, do not score anything other than canary inputs, and do not set or imply any filter threshold. Stop at G1.

## First gate

**G1**

- The target, environment, model provenance, exact allocation evidence, fixed S3 frame, and complete canary specification are frozen and independently checked; all four G1 canaries pass their semantic production-setting checks, raw schemas, and deterministic replays on labelled non-campaign fixtures; missing inputs, unverifiable provenance, missing tolerances, or a process-only canary pass fails G1. No threshold table is applied at G1.
- **Required evidence:**
  - D-target carrying a verified accession, chain, hotspot residue set, and detached manifest digest.
  - D-environment carrying every tool identity/version, weight and image digest, licence, independently verifiable model-training provenance or explicit contamination-uncertain fallback, APR-compute evidence digest, hard caps, reserved contingency, fixed S3 frame, allocation scope, and exact timezone-aware expiry.
  - All four G1 canary manifests showing immutable fixture digests, semantic positive/negative/schema/replay checks, declared units and tolerances or comparison rules, model and seed identity, exact output digests, typed failure status, and pass on labelled non-campaign fixtures; every canary ends at versioned raw output independent of D-thresholds.
- **Owner:** ROLE-methods
- **On failure:** S2 does not start and no allocation beyond the S1 cap is consumed when any target, environment, allocation, model-provenance, sampling-frame, or canary requirement is missing or unverifiable. An allocation assertion is not evidence; an affected model may be used only for descriptive diagnostics under the provenance fallback and cannot authorize G2 or spend. A failed canary is fixed and rerun under the declared retry cap; the fourth failure escalates to ROLE-pi.

## Initially unverified backlog

- Verify a PD-1:PD-L1 co-crystal structure against RCSB and record its accession, chains, method, resolution, and file digest
- Define the hotspot residue set in the deposited numbering and write D-target
- Pin every tool identity, version, weight digest, image digest, and licence into D-environment
- Run CAN-predict, CAN-energy, CAN-pipeline, and CAN-sequence at production settings and record their manifests
- Confirm the scorer ingests canary output end to end, then present G1 evidence to ROLE-methods, which accepts G1 on a stage it does not execute

## Standing rules

- Freeze before you look: the target definition, software environment, and scoring thresholds are frozen with digests before any campaign design is scored. A threshold changed after designs are visible is a labelled deviation, never a silent edit.
- Provenance: every structure, weight file, container image, seed, score table, and runtime record is recorded with its source, version or accession, retrieval time, and digest. Artifact digests are SHA-256 over the exact stored bytes; digests are written to the detached UTF-8 `artifacts/MANIFEST.sha256`, never embedded in the bytes they identify.
- Controls before candidates: no design is scored until the positive and negative control sets have been run through the identical pipeline and their separation recorded.
- Fail closed on authority: no worker may order genes, commit synthesis spend, contact a vendor, or begin wet-lab work. The campaign terminates at a recommendation.
- Reporting: after accepted G2, a no-go recommendation is reported with the same completeness as go, including the full ranked design table and every failed filter. After adjudicated nonaccepted G2, the immutable terminal control-failure record is the complete evidence package; generation, scoring, D-designs, a ranked design table, and G3 are prohibited and therefore not required.

Read `CAMPAIGN_PROMPT.md` for the full campaign constitution before acting.
