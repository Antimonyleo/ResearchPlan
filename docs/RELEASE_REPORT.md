# ResCamp 0.9.0 release and QA report

## Release decision

**Deterministic release status:** PASS

ResCamp 0.9.0 uses one canonical `rescamp/SKILL.md` and one portable supporting tree. Claude Code and Codex installation differs only by destination and invocation syntax. The installer verified byte-identical source, Claude, and Codex tree digests.

## Scope of this evidence

The automated release checks establish packaging, state-machine, validator, benchmark-harness, workflow-queue, information-boundary, and regression behavior. They do **not** establish that a live model using ResCamp is superior to another agent. Authenticated host acceptance is opt-in and separate from this deterministic release check; its receipts are not consumed by this report. Process-isolated Team U/S/E fixtures and static reviewer roles are labeled accordingly.

## Results

- Unit/generalization/workflow tests: **175 passed**.
- Public benchmark scenarios: **18** across **18 domains** and **11 research archetypes**.
- Canonical `SKILL.md`: **192 lines**, **2156 words**, conservative estimate **3341 tokens**.
- Canonical skill tree SHA-256: `44ec89c8a444608b765ec2479eb1af5ea16474ade637f241a0ada1bea3a20077`.
- Repository input SHA-256: `f2be8e4ce1047216750e533ec2b3e8496268ada7c97c0ea0ecb0a31373fcaffb` at git commit `2fa6be068c578f0cea906e958913c924292a5371`; dirty=True.
- Static structural checks (substring, existence, and count assertions; not reviews and not independent): `architecture`=pass, `generalization`=pass, `packaging-integrity`=pass, `quality-workflow`=pass, `usability`=pass.
- Release errors: **0**; warnings: **0**.

### Full 18-scenario deterministic harness smoke

These fixture scores test the harness and deliberately encoded policies; they are not model-performance estimates.

- `exhaustive-form-fixture`: n=18, mean=80.005, turns=2.889, critical-defect rate=0.0
- `no-skill-fixture`: n=18, mean=35.222, turns=2.0, critical-defect rate=0.3889
- `rescamp-current-fixture`: n=18, mean=85.272, turns=7.167, critical-defect rate=0.0

### Process-isolated Team U/S/E smoke

The selected cases span experimental/computational, humanities, and qualitative work and include approval blockers. The roles ran in separate OS processes, but they were deterministic fixtures rather than independent AI agents.

- `exhaustive-process-fixture`: n=4, mean=80.463, turns=3.0, critical-defect rate=0.0
- `no-skill-process-fixture`: n=4, mean=35.901, turns=2.0, critical-defect rate=0.5
- `rescamp-current-process-fixture`: n=4, mean=85.443, turns=7.25, critical-defect rate=0.0

## Design findings

1. **One canonical skill:** the repository contains exactly one `SKILL.md`; both hosts receive the same bytes.
2. **Proportionate interviewing:** one question per turn by default; typical 3–5, 4–8, or 6–12 by assurance profile; hard limits 8, 12, and 18 require explicit extension authority.
3. **Current-plan QA, and who does what:** interview completion automatically freezes a digest, runs deterministic checks, writes proportional reviewer *input* packets, and classifies findings. Executing those reviewers and repairing defects are the model's work, not the script's; `finalize` is the fail-closed gate that refuses an execution-ready bundle without ingested passing reviews bound to the current digest. Reviewer independence is self-attested and recorded for audit, never proven.
4. **Manual comparative benchmark:** version, baseline, model, or external-tool comparisons are deliberate commands with matched Team U/S/E boundaries.
5. **Discipline-neutral research logic:** experimental controls and predictions are translated to rival interpretations, negative cases, objections, source criticism, counterfactuals, or adjudication rules where appropriate.
6. **Optional continuous workflow:** the SQLite queue revalidates finalized campaigns and enforces structured approvals, dependencies, concurrency, deadlines, retries, leases, event integrity, and artifact hashes. It never launches models, grants real-world authority, or substitutes for a scheduler.
7. **Pilots and risks are explicit contracts:** required pilots and major/critical risk acceptances are separately authorized and digest-bound. Authority remains attested rather than independently proven.
8. **Anthropic campaign architecture translated, not preserved wholesale:** the shared constitution, exact mission, dossier, method diversity, tool qualification, frozen evaluation, staged gates, resource governor, bounded delegation, claim discipline, closeout, and kickoff are translations of the released binder-design campaign. Durable recovery and the challenge stage are extrapolations. The inquiry/prediction/reconciliation loop derives from the Little Scientist paper, not the binder campaign. The paper's external adjudicator — two independent contract labs — has no equivalent here; agent review checks internal coherence only. See `docs/PAPER_ANTHROPIC_BINDER.md` and `docs/DESIGN_BASIS.md`.

## Remaining validation required for strong behavioral claims

Run the preregistered live matrix using fresh, separate Team U, Team S, and Team E sessions; private holdouts; exact model/host/tool commits; matched budgets; multiple stochastic replicates; blinded domain experts; and downstream execution outcomes. Public fixtures and self-authored rubrics cannot establish external validity.
