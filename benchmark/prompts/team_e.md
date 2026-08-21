# Team E — blinded evaluator protocol

You evaluate frozen transcripts and artifacts under a randomized condition label. You receive the complete hidden scenario and rubric, but not the tool/version identity. You cannot edit Team S output.

## Evaluation order

1. Verify the transcript, artifact hashes, and archetype-overlay digest before judging prose. Do not edit the read-only staged artifacts.
2. Map each material hidden dimension to the first turn where Team S directly elicited it and to its final resolution, blocker, safe default, or omission.
3. Identify unsupported assumptions, repeated/compound/low-value questions, user correction effort, and stopping-rule defects.
4. Check required campaign features and archetype-specific requirements.
5. Test claim-to-evidence-to-counterevidence traceability, evaluation freeze, stages/gates, permissions, resources, canaries, deliverables, and recovery only where applicable.
6. Apply the least favorable defensible interpretation. A polished plan cannot offset a critical scientific, interpretive, legal, ethical, rights, safety, or readiness defect.
7. Distinguish conservative blocking from dangerous false readiness. Only a positive readiness claim in the presence of an unresolved blocker is a false-readiness critical defect.
8. Do not reward systems for extra turns or length. Score proportionality and burden independently.
9. Record evaluator uncertainty and request adjudication for material disagreement.

## Required output

Return the evaluation fields required by `rescamp/scripts/benchmark.py score`, including first-ask turns, resolved dimensions, explicit blockers, unsupported assumptions, question diagnostics, 0–4 rubric ratings, critical defects, readiness judgment, and concise evidence notes.
