# ResCamp benchmark

The benchmark separates hidden-user Team U, tested-system Team S, and blinded-evaluator Team E.

- `scenarios/public/`: 18 calibration/regression cases across 18 domains and 11 research archetypes.
- `prompts/`: live Team U/S/E role contracts.
- `rubrics/`: universal rubric and archetype overlays.
- `conditions/`: deterministic fixtures plus live/cross-version templates.
- `adapters/`: stateless JSON command protocol and process-isolated fixtures.
- `comparable_tools.json`: capability-matched discovery manifest, not an endorsement or installed dependency list.

Validate and run the deterministic harness:

```bash
python3 rescamp/scripts/benchmark.py validate-scenarios benchmark/scenarios/public
python3 rescamp/scripts/benchmark.py run \
  --scenarios benchmark/scenarios/public \
  --config benchmark/conditions/fixture.json \
  --output benchmark/runs/fixture \
  --jobs 6
```

Generate a live matrix:

```bash
python3 scripts/create_benchmark_matrix.py \
  --condition 'rescamp-0.8=python3 my_team_s.py --skill /path/to/v0.8/rescamp' \
  --condition 'rescamp-previous=python3 my_team_s.py --skill /path/to/previous/rescamp' \
  --condition 'neutral=python3 my_team_s.py --condition neutral' \
  --user-adapter 'python3 my_team_u.py' \
  --evaluator-adapter 'python3 my_team_e.py' \
  --model-id 'exact-model-id' \
  --host-version 'exact-host-version' \
  --output benchmark/conditions/live.json
```

Public fixtures verify harness behavior only. Use private holdouts, fresh sessions, matched budgets, exact commits, repeated runs, blinded domain experts, and downstream external outcomes for release claims.
