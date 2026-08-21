# Repository Instructions

## Scope

These instructions apply to the entire repository.

## Project constraints

- ResCamp supports Python 3.9+ and uses the standard library for its runtime.
- Keep `rescamp/` as the one canonical skill tree. Do not add host-specific copies or instruction forks.
- Put detailed guidance in focused, one-level references. Keep deterministic behavior in dependency-free scripts when practical.
- Preserve fail-closed validation, review-digest binding, and byte-identical Claude Code and Codex installations.

## Working principles

- Think before editing. State material assumptions and clarify genuine ambiguity.
- Choose the smallest change that fully solves the request. Do not add speculative features, abstractions, or configuration.
- Make surgical edits. Match the surrounding style and leave unrelated code, comments, and formatting alone.
- Remove only unused code created by your own change. Mention unrelated problems instead of fixing them silently.
- Define a concrete success check before implementation, then run it.
- Keep writing plain and concise. Prefer specific claims over promotional language, and do not repeat caveats unnecessarily.

## Code, tests, and evidence

- Add or update tests for behavior changes. Also add at least one relevant scenario that demonstrates the intended gain without excessive interview burden.
- Treat public scenarios as calibration cases, not sufficient evidence for performance claims.
- Treat `qa/*.json` as release evidence snapshots. Synthetic fixture scores and static checks do not establish live-model quality or reviewer independence.
- Do not edit `.git/` or ignored `.claude/` session metadata as part of repository work.
- Never commit credentials, private benchmark keys, restricted data, or human-subject information.

## Validation

Run the smallest relevant check first, then broaden in proportion to the change:

```bash
python3 -m unittest discover -s tests -p 'test_<area>.py' -v
make test
make skill-check
make validate
```

Use `make benchmark-smoke` for benchmark or harness changes. Before a pull request or release, run `make validate-full`.
