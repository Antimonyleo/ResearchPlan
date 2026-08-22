# Worked example: de novo PD-L1 miniprotein binders

A complete campaign, compiled by ResCamp 0.10.0 and committed here unedited. Every file in
`outputs/` was rendered by `rescamp.py finalize`; nothing was written by hand afterwards.

**Goal given to the skill**

> Can our computational pipeline design de novo miniprotein binders to the PD-1-binding face
> of human PD-L1 that clear frozen in-silico filters well enough to justify ordering genes
> for wet-lab testing?

**Result:** `EXECUTION-READY`, `audit --strict` exit 0, 7 interview turns, 2 review rounds.

## What it demonstrates

The decision this campaign supports is not *does the binder work* — that needs a wet lab.
It is *is the computational evidence strong enough to justify the spend*. That framing is
what makes the campaign finishable, and it came out of the first interview question.

The architecture that follows is the one from the Anthropic binder paper, translated:
controls before candidates, an evaluation instrument frozen before any campaign design is
scored, cheap stages gating expensive ones, and an authority boundary that no worker can
cross. The campaign spends 50 GPU-hours proving the pipeline runs before it spends 1,600
generating designs, and it cannot order a gene under any outcome.

## What review actually found

Two rounds, both recorded in `state/campaign.json` and summarised in
`outputs/REVIEW_REPORT.md`.

**Round 1 — 7 major, 1 minor.** The methods pass rejected the plan on one theme: the
evaluation instrument was frozen in name only. The campaign said thresholds would be
"calibrated on controls and frozen", but never named the separation *statistic* — so
whoever wrote the calibration artifact would still be choosing between AUROC, overlap
coefficient and median-crossing rate *after* seeing the distributions. Same defect in the
composition-matching rule and the clustering metric. It also found that a terminal stop
rule fired on a control-set minimum that appeared nowhere in the plan, and that
training-set contamination of the positive controls — published binders are often
deposited structures, and deposited structures are often in a prediction model's training
data — was unaddressed, which is the most likely way the separation estimate is inflated.

The operations pass found the schedule had zero slack against a hard allocation expiry
with nobody assigned to watch it, that the recovery rule could not detect the failure it
was written for (nothing required a batch manifest to exist *before* the batch ran), and
that the executing role approved its own work at half the gates.

**Round 2 — pass.** It also caught a defect the round-1 repair introduced: reassigning
gate owners left the kickoff backlog routing G1 evidence to the old owner and three
approval records naming the wrong authorities.

## Honest limitations of this example

- **The reviews are `sequential-pass`, the weakest rung on the independence ladder.** The
  same session authored the plan and reviewed it. `REVIEW_REPORT.md` carries the engine's
  own `WARNING review.sequential` saying so, and independence is self-attested throughout.
  A separate-context or blinded reviewer would be stronger evidence.
- **No pilot was run.** This is `reviewed-static` plan evidence: a document that was read,
  not a campaign that was watched running.
- **`EXECUTION-READY` means the plan passed its declared gates.** It does not mean the
  designs will bind, that the filter stack will separate, or that the science is right.
- **Nothing here was executed.** No structure was retrieved, no design generated, no
  GPU-hour spent. The campaign is a plan; the numbers in it are commitments, not results.
- Concrete identifiers the plan deliberately refuses to guess — the PDB accession, the
  model versions — are required to be pinned in a frozen artifact at S1 and verified
  against RCSB, rather than asserted here.

## Reproducing the checks

```bash
python3 rescamp/scripts/rescamp.py audit docs/examples/pdl1-miniprotein-binders --strict
cd docs/examples/pdl1-miniprotein-binders/outputs && sha256sum -c MANIFEST.sha256
```

To see per-section review binding, copy the campaign, change `title` (reviews stay
current), then change a method's `limitations` (the methods review goes stale and
`review.missing` appears).
