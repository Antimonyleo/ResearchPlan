# Kickoff: Can our computational pipeline design de novo miniprotein binders to the PD-1-binding face of human PD-L1 that clear frozen…

**Status:** EXECUTION-READY

**Campaign contract:** `campaign.json` @ `sha256:1e86dcba1b89b17fe606eae042009dc1590f18e0e4d2e8aa1cfb9de225c9a195`

## Start here

Begin WU-freeze. Read the campaign constitution and D-target's schema, then retrieve and verify a PD-1:PD-L1 co-crystal structure against RCSB, recording accession, chains, method, resolution, interface density gaps, and the coordinate file digest. Do not generate any design, do not score anything other than canary inputs, and do not set or imply any filter threshold. Stop at G1.

## First gate

**G1**

- The target and environment are frozen and the pipeline demonstrably works end to end at production settings.
- **Required evidence:**
  - D-target carrying a verified accession, chain, hotspot residue set, and file digest.
  - D-environment carrying every tool version, weight digest, image digest, and licence.
  - All four canary manifests showing their positive, negative, and reproducibility checks passed, and the scorer ingesting canary output end to end.
- **Owner:** ROLE-methods
- **On failure:** S2 does not start and no allocation beyond the S1 budget is consumed. A failed canary is fixed and rerun; a structure that cannot be verified against RCSB sends the epitope definition back for reselection.

## Initially unverified backlog

- Verify a PD-1:PD-L1 co-crystal structure against RCSB and record its accession, chains, method, resolution, and file digest
- Define the hotspot residue set in the deposited numbering and write D-target
- Pin every tool identity, version, weight digest, image digest, and licence into D-environment
- Run CAN-predict, CAN-energy, CAN-pipeline, and CAN-sequence at production settings and record their manifests
- Confirm the scorer ingests canary output end to end, then present G1 evidence to ROLE-methods, which accepts G1 on a stage it does not execute

## Standing rules

- Freeze before you look: the target definition, software environment, and scoring thresholds are frozen with digests before any campaign design is scored. A threshold changed after designs are visible is a labelled deviation, never a silent edit.
- Provenance: every structure, weight file, container image, seed, and score table is recorded with its source, version or accession, retrieval time, and digest.
- Controls before candidates: no design is scored until the positive and negative control sets have been run through the identical pipeline and their separation recorded.
- Fail closed on authority: no worker may order genes, commit synthesis spend, contact a vendor, or begin wet-lab work. The campaign terminates at a recommendation.
- Reporting: a no-go recommendation is reported with the same completeness as a go, including the full ranked design table and every failed filter.

Read `CAMPAIGN_PROMPT.md` for the full campaign constitution before acting.
