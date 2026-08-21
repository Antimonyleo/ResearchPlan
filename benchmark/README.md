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
  --condition 'rescamp-0.9=python3 my_team_s.py --skill /path/to/v0.9/rescamp' \
  --condition 'rescamp-previous=python3 my_team_s.py --skill /path/to/previous/rescamp' \
  --condition 'neutral=python3 my_team_s.py --condition neutral' \
  --user-adapter 'python3 my_team_u.py' \
  --evaluator-adapter 'python3 my_team_e.py' \
  --model-id 'exact-model-id' \
  --host-version 'exact-host-version' \
  --output benchmark/conditions/live.json
```

Live comparative evidence requires a complete `matched_controls` declaration plus identical model, host, and capability pins across at least two live conditions. Otherwise the harness labels it `live-adapter-unmatched-controls`. Public fixtures remain synthetic harness checks only; use private holdouts, repeated runs, blinded domain experts, and downstream external outcomes for release claims.

The matrix generator writes every matched-control declaration as `false`; change a value only after the control is actually in place. Standalone `score` and `compare` inputs have no verifiable run/config provenance, so their output is always labeled `unspecified`. Preserve matrix-run manifests when making evidence claims.
