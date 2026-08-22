# Design basis

ResCamp combines five evidence streams. The first three are documents you can read; the last two are bodies of practice, and claims drawn from them are weaker.

## 1. Anthropic's protein-binder campaign

*Autonomous de novo protein binder design with Claude* (Claude Science and Amir Shanehsazzadeh, Anthropic, 18 August 2026). [PDF](https://www-cdn.anthropic.com/30bf50e22a01388bb29bf077ee3f244531594b7a.pdf) · [prompts and data](https://huggingface.co/datasets/Anthropic/claude-protein-binder-design) · reading and full section mapping in `docs/PAPER_ANTHROPIC_BINDER.md`.

Direct translations, where the paper or its released prompt has a named counterpart: a single protocol prompt inherited by every agent in a campaign; an exact mission and deliverable; a target and source dossier; a method-diversity requirement with per-method floors and ceilings; building and validating each tool before scaling; checking that the scoring instrument recognizes known positives; a ranking instrument fixed before production evidence is inspected; a screen-cheap-then-rank-expensive funnel; a compute budget with a pacing governor and clock discipline; a two-layer sub-agent team; verify-before-reporting; and closing by returning the deliverable with a complete decision record.

Plausible extrapolation, where ResCamp went beyond the source: durable event logs, checkpointing, and restart reconciliation (the paper attests that Claude recovered from infrastructure incidents but does not describe the mechanism); consent, privacy, and human-subjects boundaries (the paper's analogues are only tool licensing and a network allowlist); and plan-stage independent review.

Vocabulary. These are ResCamp coinages, not the paper's words: **canary**, **campaign constitution**, **independent challenge**, **assurance profile**, **agent-fix**, and **quality loop**. The word "independent" in the paper means two external contract research organizations measuring 1,320 physical designs blind to each other — not an audit, and not a reviewer agent. ResCamp's reviewers are a weaker substitute and the skill says so. The paper's own vocabulary for the same region is "verification", "reporting", "sub-agents", "pacing governor", and "clock discipline".

Proportion. ResCamp's heuristic that orchestration and operations should outweigh domain science roughly two to one comes from Figure M2's measured split of the 16,000-word prompt: 34.2% science and tooling, 34.7% orchestration and verification, 31.1% operations. One prompt, one domain, one measurement.

What is not taken: the protein-specific numerical instrument, and the domain content itself. ResCamp preserves the campaign architecture and requires every field to define its own warranted evaluation or adjudication instrument.

## 2. *The Little Scientist*

Travis Smith, *The Little Scientist: LLM Agent-Driven Discovery via the Scientific Method* (arXiv:2608.16951, 16 August 2026). Critical reading in `docs/PAPER_LITTLE_SCIENTIST.md`.

This is the source of the hypothesis → discriminating prediction → test → observation → reconciliation → retain/revise/reject/branch loop in ResCamp's "Inquiry logic" section. The binder campaign contains no such loop; do not attribute it there. The paper is a two-case-study preprint with confounded infrastructure changes and no external validation, so it is treated as workflow inspiration only.

## 3. Long-horizon agents and living protocols

Recent long-horizon work converges on a narrow operational pattern: keep the governing plan outside conversational memory, reconstruct each session from bounded canonical state, refine tactics at the frontier, and trigger replanning when evidence invalidates an assumption. Anthropic's [long-running-agent harness](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) uses progress artifacts, tests, and version history; [InfiAgent](https://aclanthology.org/2026.findings-acl.1787/) reconstructs bounded context from file-backed state; [AdaPlan-H](https://aclanthology.org/2026.findings-acl.77/) progressively refines a coarse plan; and [ARC](https://aclanthology.org/2026.findings-acl.930/) actively revises context rather than passively accumulating it.

ResCamp translates that pattern into active plan digests, stage checkpoints, fresh review at major decision boundaries, and controlled amendments. This goes beyond the binder paper: its protocol was iterated in test campaigns and then frozen, but the paper does not describe material plan amendments inside a reported campaign. For research involving people, the amendment model also follows [SPIRIT 2025](https://doi.org/10.1038/s41591-025-03668-w): keep dated protocol versions, an amendment trail, and explicit approval or communication for important changes.

These sources do not establish a universal checkpoint frequency. ResCamp's default of one review per major decision-bearing stage, capped at eight without a specific reason, is a cost-control design judgment.

## 4. Scientific-agent benchmarks

Practice, not a single citation: separate task-level engineering, planning, execution, and externally checked outcomes; preserve artifacts and costs; do not equate a polished report with valid science. This is the basis for the Team U / Team S / Team E separation in `docs/BENCHMARKING.md`.

## 5. Interactive intent research

Practice, not a single citation: map material decision dimensions, present an early corrigible sketch, ask high-information questions, stop by value rather than by exhausting a checklist, and never infer consequential authority from weak preference evidence. This is the basis for the minimum-sufficient interview.

## Status of the whole

Streams 1 and 2 are checkable against their sources. Streams 3 and 4 are design judgment, and the skill's shape reflects them without being able to prove them. Nothing in this repository has been validated against an external measurement the way the binder campaign was; `docs/PAPER_ANTHROPIC_BINDER.md` lists what ResCamp does not reproduce.
