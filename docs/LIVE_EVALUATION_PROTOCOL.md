# Live evaluation protocol

This repository cannot manufacture independent model evidence. Use this protocol with authenticated Claude Code, Codex, or external agents.

1. Freeze a private scenario set and preregister primary metrics, budgets, exclusion rules, and analysis.
2. Create fresh Team U, Team S, and Team E sessions for every run. Do not reuse authoring context.
3. Randomize and blind condition labels. Keep model, host, tools, network, corpus, permissions, time, tokens, and retries constant.
4. Run ResCamp 0.9, the previous version, and a no-skill baseline. Add external tools only on matched capabilities.
5. Store complete transcripts, model/host IDs, tool traces, output artifacts, hashes, elapsed time, token use, and cost.
6. Use two domain/method reviewers for material campaigns and adjudicate high-impact disagreements.
7. Report paired differences, uncertainty intervals, critical-defect rates, burden, cost, and failures. Do not publish only successful runs.
8. For downstream claims, execute a subset and evaluate against external scientific, scholarly, policy, legal, design, or stakeholder anchors.
