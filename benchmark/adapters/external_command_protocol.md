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
  "condition": {"id": "rescamp-current-live"},
  "run_dir": "/absolute/path"
}
```

Team S returns one of:

```json
{"action":"ask","message":"one question","branch":"scope-object","question_count":1,"usage":{"tokens":123,"cost_usd":0.01}}
```

```json
{"action":"final","message":"summary","declared_features":["frozen-evaluation"],"readiness_claimed":false,"artifacts":["CAMPAIGN_PROMPT.md"],"usage":{"tokens":999,"cost_usd":0.1}}
```

Artifacts must be regular files inside `run_dir`. Team S receives only the public transcript; hidden dimension IDs and Team U's private annotations never return in a later Team S request.

## Team U request

```json
{
  "protocol":"rescamp-team-u-v1",
  "hidden_scenario": {"...":"complete private brief"},
  "assistant_question": {"message":"...","branch":"scope-object"},
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
  "final_response": {"artifacts":["artifact-001.md"]},
  "artifact_manifest": [{"id":"artifact-001","name":"artifact-001.md","path":"/opaque/candidate/path/artifact-001.md","bytes":123,"sha256":"sha256:..."}],
  "rubric": {},
  "archetype_overlays": {},
  "archetype_overlays_digest": "sha256:..."
}
```

The harness replaces Team S paths with read-only copies under a random candidate ID in a temporary directory outside the condition-bearing run tree. It verifies the source and copy hashes again after evaluation, then persists a verified copy, and rejects missing, outside-run, or changed files. Team E must not receive the condition or run name through its payload or artifact path. This is protocol-level blinding, not an OS security boundary: run Team E in a separate account, container, or remote service without access to benchmark run directories before claiming strong blinding. Return all fields required by `benchmark.py score`: asked/resolved dimensions, unsupported assumptions, question diagnostics, 0–4 rubric ratings, critical defects, and readiness truthfulness.

## Isolation requirements

Use fresh sessions or processes. Pin model and host versions. Hold tools, network, context, retries, time, and token budgets constant. The harness randomizes job order and blinded labels, records request digests and raw adapter stdout/stderr in `adapter_calls.json`, and hashes persisted artifacts. Keep private raw requests separately only when permissions allow. A sequential role simulation is a smoke test, not independent evidence.

Adapter timeouts use a bounded pipe-drain window. On Linux, the harness tracks `/proc` descendants while the adapter is running so a child that calls `setsid()` can still be terminated if the adapter root exits first. This tracking is best effort. On non-Linux POSIX systems, cleanup can terminate only the adapter's process group; an escaped `setsid()` descendant may survive, so use an external account, container, or equivalent process boundary for live runs.
