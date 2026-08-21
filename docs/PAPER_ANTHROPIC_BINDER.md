# Primary source: *Autonomous de novo protein binder design with Claude*

Claude Science and Amir Shanehsazzadeh, Anthropic, 18 August 2026, 29 pp.

- Paper: <https://www-cdn.anthropic.com/30bf50e22a01388bb29bf077ee3f244531594b7a.pdf>
- Prompts, corpus, designs, and binding data: <https://huggingface.co/datasets/Anthropic/claude-protein-binder-design> (CC BY 4.0 for data, MIT for scripts)

This is the paper ResCamp's campaign architecture is translated from. The secondary source, which supplies the hypothesis/prediction/falsifier loop and nothing else, is `docs/PAPER_LITTLE_SCIENTIST.md`. Design provenance for the whole skill is in `docs/DESIGN_BASIS.md`.

Every number below is from the paper and can be checked against the PDF.

## What the campaign did

Claude Opus 4.8 and Claude Mythos Preview ran binder design campaigns against 16 targets from a single protocol prompt of about 16,000 words, loaded as the system prompt of every agent in a campaign, plus a short kickoff message. The prompt names no epitope, scaffold, target construct, or sequence for any target.

Two formats: multi-target campaigns of 48 hours against 14 targets at once with a USD $50,000 cloud GPU budget, and single-target campaigns of 24 hours per target with USD $10,000. Both deliver 30 ranked designs per target.

Within a campaign Claude researched each target's biology and structures, chose the target construct and epitope, selected and mixed public backbone-generation and sequence-design tools, filtered candidates for novelty, redundancy, and composition, screened with one prediction seed and ranked with five, ran further in silico optimization rounds when it expected them to help, and delivered 30 ranked designs with a record of its decisions.

Humans acted only at the ends. One operator chose the targets (given to Claude by name, UniProt accession, organism, and oligomeric state), funded a Modal GPU account with a container limit, supplied connectors, a network domain allowlist, credentials, and an offline reference corpus, loaded the protocol, sent the kickoff, and placed the synthesis orders. No design or prediction tool was pre-installed; the prompt has Claude build each one from its public repository into a container image and validate it in the first hour. The only human messages that entered any campaign were short, non-technical instructions to resume after a session died for infrastructure reasons.

## Outcome

One of the 16 targets (mature GDF-8) aggregated under assay conditions and gave no interpretable measurement at either lab; its 120 designs are excluded, leaving 1,320 designs on 15 targets.

- 354 of 1,320 designs bound: a hit rate of 26.8% (the abstract rounds to 27%).
- Binders against 14 of the 15 targets.
- Among designs ranked first for their target in a campaign, 49% bound; 44% over the top five, 39% over the top ten, 28% over all 30.
- Hit rates varied far more between targets (72/90 on TREM2 down to 0/90 on MBP) than between campaigns (22.6%, 26.7%, 35.1%).

## Anatomy of the prompt

Figure M2 divides the multi-target protocol prompt into 15 thematic blocks in three groups, with tile areas proportional to word counts:

| Group | Share | Contents named in the figure |
|---|---|---|
| Science and tooling | 34.2% | target dossiers and epitope selection, design tools and strategy, pre-scoring filters, the ranking score, in silico optimization, the 30-design deliverable |
| Orchestration and verification | 34.7% | sub-agent delegation, verification and ranking rules |
| Operations | 31.1% | clock discipline, the compute budget and its pacing governor, reporting |

The paper's own summary: "About a third of the prompt is scientific guidance." And: "The remaining two thirds of the prompt are what makes autonomy work at this scale: how to pace a fixed GPU budget against the wall clock, how to delegate work to a two-layer team of sub-agents and supervise it, how to verify results before reporting them, and when to report."

Those two-thirds "were iterated over test campaigns until Claude reliably sustained 24- to 48-hour campaigns and used the full budget as intended, and were then frozen before the campaigns reported here." The same frozen protocol served all 16 targets.

## External validation design

Validation was physical and external, and it is the load-bearing part of the paper.

- Two contract research organizations, Adaptyv Bio and Twist Bioscience, synthesized every design exactly as delivered and measured binding independently, in different formats. Adaptyv Bio received all 1,320 designs (cell-free expression, immobilized design, target as analyte, single-cycle SPR over five concentrations). Twist Bioscience received 1,260 (Fc fusions expressed in HEK293, captured on an anti-Fc SPR array, target titrated over six three-fold concentrations).
- Neither lab saw the other's data, the design models, or the model, campaign, or rank behind a sequence. Orders were placed with sequences shuffled.
- Each dataset was labeled blind to the other. Both blind passes combined objective trace metrics with two independent visual reads of every design that showed any response; reader agreement was 98% for Twist Bioscience and 96% for Adaptyv Bio on positive versus not. No label was changed on metrics alone.
- Off-target controls: five Twist Bioscience plates carried the unrelated protein CLEC12A on the same surface. It caught at least one false positive, a Nipah G design whose rectangular, linearly scaling responses recurred on the control and were read as a bulk refractive-index step.
- The combination rule that merges the two labels "was written after both CROs had reported and is applied identically to every design; every input it uses is a released column, so each label can be recomputed." Blind Twist positives that the rule could not reconcile were never promoted automatically: fourteen were reviewed one by one against both labs' raw traces, and six became binders.
- Agreement on the 1,235 designs measured at both labs was 1,099 (89%, Cohen's κ = 0.71). Note the asymmetry: the paper compares Adaptyv Bio's *classification* against the *presence of a Twist Bioscience fit*, so this is not a symmetric inter-lab reliability coefficient between two comparable labels.
- After the campaigns closed, and independently of the wet lab work, every ordered design was re-scored under one uniform protocol with ten public co-folding predictors, five runs each. Campaign-time confidence values were not treated as comparable across campaigns or targets.

## The key negative finding

The co-folding score that the campaign ranked on separates binders from non-binders **within** a target and is close to useless **across** targets.

- Within-target average precision beat chance on 12 of the 13 evaluable targets (sign test, n = 13, p = 0.003), mean AP 0.52 against a mean chance level of 0.31. The paper notes these values understate the available enrichment, because delivered designs had already been filtered on the same predictors.
- Across targets the median score rose with hit rate (Spearman ρ = 0.61 over 15 targets, p = 0.02) but "not steeply enough to have flagged the failures in advance." The three worst targets — MBP (0/90), BBF-14 (3/90), and 15-PGDH (1/30) — had median scores of 0.68 to 0.70, against 0.72 for both VEGF-A (54/90) and Nipah G (19/90).
- Among the 354 binders, score was only weakly related to affinity (Spearman ρ = 0.16 pooled, 0.25 standardized within target).

Claude's own delivered ranking scored AP 0.48 against 0.35 expected by chance, tracked the co-folding score closely (median Spearman ρ = 0.86 within a target), and "performed about as well as the co-folding score on which it was largely based, but not better."

The conclusion the paper draws is the one ResCamp inherits: a confident in silico score "was therefore a useful requirement for selection but not a guarantee of binding, and experimental screening remains the only way to learn which targets a campaign has succeeded on."

## Limitations the paper states about itself

Binding, not structure or function: no design was tested for activity or solved structurally, so every pose reported is a prediction, and affinities on the five oligomeric targets are apparent values. Designs are counted per sequence although sequence variants of one backbone are not independent (counting the best-ranked sequence per backbone gives 200 binders of 809, 24.7%). Each combination of model, format, and target ran once, so model, format, and run-to-run variation are confounded; the paper describes campaigns rather than models. Most targets are extensively characterized in the literature, and the reports or result collections of four of the six competition targets were on the prompt's reading list. No matched human-expert campaign was run.

## Which ResCamp sections derive from which part of the paper

ResCamp's campaign architecture has 16 sections (`rescamp/SKILL.md`, "Campaign architecture"). The paper's prompt has 15 blocks. The counts are unrelated; the mapping below is by content.

| ResCamp section | Basis in the paper | Kind |
|---|---|---|
| 1. Campaign constitution | one protocol prompt loaded as the system prompt of every agent in a campaign | direct translation |
| 2. Mission and deliverables | the stated objective: 30 novel single-chain miniproteins of 50–120 residues per target, plus two subordinate secondary objectives | direct translation |
| 3. Object and evidence dossier | target dossiers (name, accession, organism, oligomeric state, obligate cofactors), the reading list, and the offline document corpus | direct translation |
| 4. Inquiry logic | **not from this paper.** The campaign has no hypothesis/prediction/falsifier loop. This comes from `docs/PAPER_LITTLE_SCIENTIST.md` | not derived |
| 5. Method portfolio | the requirement that seven designated generators each contribute ≥50 backbones, that each target's 30 designs draw on ≥3 methods, and that no method supply more than half | direct translation |
| 6. Tools and canaries | build each tool from its public repository and validate it in the first hour; check that the ranking score recognizes known binders of the target before scoring candidates | direct translation |
| 7. Frozen evaluation instrument | the ranking score prescribed in the prompt and validated beforehand on a public benchmark; the supplementary TNFα rule fixed in advance | direct translation |
| — *contrast case, not a warrant* | the label-combination rule was written **after** both CROs reported (paper, line 274). It was applied identically to every design, which is fair, but a rule written after the evidence cannot support a freeze-before-evidence requirement. `GENERALIZATION.md` prescribes the stronger practice: write the disagreement-resolution rule before the disagreement is known. | ResCamp departs from the paper |
| 8. Staged funnel | pre-scoring filters, one seed to screen and five to rank, bounded further optimization rounds | direct translation |
| 9. Resources and dispatch | the operations third: clock discipline, the compute budget and its pacing governor, concurrency ceilings, the per-campaign container limit | direct translation |
| 10. Delegation | "a two-layer team of sub-agents" and its supervision | direct translation |
| 11. Durable operations | attested but not specified. The paper reports that Claude detected and worked around infrastructure incidents on its own and that humans sent short resume messages after session deaths; it does not describe the mechanism | extrapolation |
| 12. Ethics, safety, rights, external actions | the paper's analogues are narrow: license exclusions on tools, a network domain allowlist, operator approval of access prompts carrying no scientific content. The consent, privacy, and human-subjects material is ResCamp's | extrapolation |
| 13. Reporting and claim discipline | "how to verify results before reporting them, and when to report"; the release reports every delivered design including those from failed campaigns | direct translation |
| 14. Transactional closeout | closing a campaign by returning 30 ranked designs with a complete record of decisions and per-design provenance | direct translation |
| 15. Independent challenge | the paper's independence is two external wet labs, blind labeling, and independent readers — **not** agent or reviewer self-critique. ResCamp's plan-stage reviewers are a weaker substitute, and the skill must say so | extrapolation |
| 16. Kickoff | "a short kickoff message" sent after the protocol is loaded | direct translation |

The 2:1 proportion heuristic in ResCamp (roughly twice as much orchestration and operations content as domain science) is read off Figure M2's measured 34.2 / 34.7 / 31.1 split. It is a single observation from one prompt in one domain, not a validated rule.

## What ResCamp does not reproduce

Stated plainly, because the architecture is easier to copy than the things that made it mean something.

1. **External physical adjudication.** The paper's claims rest on 1,320 designs synthesized and measured by two labs that never saw each other's data. ResCamp has no equivalent. Its reviewers read a plan; nothing it produces has been checked against a measurement it could not influence. Agent review is not external validation.
2. **The offline corpus.** The release ships an offline document corpus (the paper states no file count; if you cite one, count it yourself in the HuggingFace archive and say so) — benchmark and competition reports, case studies, method papers for every named tool, and published binder sequences used in the novelty screen. ResCamp asks a campaign to declare its own sources; it supplies none.
3. **Host primitives.** Anthropic's runs used private host capabilities for delegation, compute, gating, and notification (`host.delegate`, `host.compute`, `submit_gate`, `wait_for_notification`). A portable skill cannot assume these exist, so ResCamp specifies equivalents in text and supplies an optional SQLite queue that no model drives.
4. **Content density.** The protocol prompt is about 16,000 words of specific, hard-won domain knowledge for one field. ResCamp's `SKILL.md` is under 150 lines and contains none of it. It compiles a structure that a domain expert must fill; it does not know any domain.
5. **Live long-horizon autonomy.** No ResCamp campaign has run unattended for 24 to 48 hours against a real budget and produced a physically tested deliverable. The 24–48 hour result belongs to the paper, not to this repository.
6. **Measured outcomes.** ResCamp reports no hit rate, because it has produced no outcome that anyone measured. The benchmark in this repository scores plan quality against a rubric, which is a different and much weaker thing.
