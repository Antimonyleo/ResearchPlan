# Architecture

ResCamp 0.8 separates four concerns.

## 1. Campaign compiler

The skill conducts a minimum-sufficient interview and compiles a canonical campaign contract. The recurring `SKILL.md` is deliberately concise; focused references are loaded only when a branch needs them.

## 2. Automatic current-campaign quality loop

Interview completion triggers deterministic validation and proportional review preparation. Findings are classified by who can resolve them:

- `agent-fix`;
- `user-answer`;
- `external-approval`;
- `accepted-risk`.

The agent applies its fixes first and asks only the highest-value remaining user question. Every material change creates a new digest and invalidates stale reviews.

## 3. Optional workflow execution

Long-running work is not implemented by prompt persistence. The campaign must name a real continuation trigger and define bounded work units, durable state, events, checkpoints, liveness, recovery, idempotency, budgets, permissions, and stop rules. The bundled engine maintains campaign artifacts but does not call arbitrary external systems.

## 4. Manual comparative benchmark

A separate harness compares versions, baselines, and external tools under matched conditions. This avoids spending benchmark resources after every ordinary interview and prevents the campaign agent from seeing hidden evaluator data.

## Canonical-source invariant

There is one `rescamp/` directory and one `SKILL.md`. The installer copies or symlinks that exact directory into Claude Code and Codex discovery paths. Host-specific invocation policy lives in host settings or optional standard metadata, not divergent skill instructions.
