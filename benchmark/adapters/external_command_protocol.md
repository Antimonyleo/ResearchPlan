# External-command adapter protocol

Each adapter is a stateless command. The harness writes one JSON object to stdin and reads the final non-empty stdout line as one JSON object. Use stderr for logs. Exit nonzero on failure.

## Team S request

```json
{
  "protocol": "rescamp-team-s-v1",
  "public_scenario": {
    "id": "...",
    "title": "...",
    "domain": "...",
    "archetypes": ["..."],
    "profile": "standard",
    "initial_request": "..."
  },
  "history": [{"role": "user", "message": "..."}],
  "condition": {"id": "rescamp-0.8-live"},
  "run_dir": "/absolute/path"
}
```

Team S returns one of:

```json
{"action":"ask","message":"one question","dimension_ids":["scope"],"question_count":1,"usage":{"tokens":123,"cost_usd":0.01}}
```

```json
{"action":"final","message":"summary","declared_resolutions":["scope"],"declared_features":["frozen-evaluation"],"readiness_claimed":false,"artifacts":["/path/to/CAMPAIGN_PROMPT.md"],"usage":{"tokens":999,"cost_usd":0.1}}
```

`dimension_ids` are evaluator annotations supplied by the adapter; the tested agent need not see hidden answer keys. A postprocessor may assign them from the transcript.

## Team U request

```json
{
  "protocol":"rescamp-team-u-v1",
  "hidden_scenario": {"...":"complete private brief"},
  "assistant_question": {"message":"...","dimension_ids":["scope"]},
  "history": []
}
```

Return:

```json
{"message":"user answer","answered_dimension_ids":["scope"]}
```

Team U must answer only what was asked, obey knowledge limits, and not rescue weak questions.

## Team E request

```json
{
  "protocol":"rescamp-team-e-v1",
  "blinded_label":"8a9d...",
  "hidden_scenario": {"...":"complete brief and rubric anchors"},
  "transcript": [],
  "final_response": {},
  "rubric": {}
}
```

Return all fields required by `benchmark.py score`: asked/resolved dimensions, unsupported assumptions, question diagnostics, 0–4 rubric ratings, critical defects, and readiness truthfulness. Team E must not edit Team S artifacts and should not receive the condition name.

## Isolation requirements

Use fresh sessions or processes. Pin model and host versions. Hold tools, network, context, retries, time, and token budgets constant. Randomize blinded labels. Store raw requests, responses, logs, and artifact hashes. A sequential role simulation is a smoke test, not independent evidence.
