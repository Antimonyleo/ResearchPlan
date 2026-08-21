#!/usr/bin/env python3
"""Process-isolated deterministic blinded evaluator fixture; not expert review."""
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("bench", ROOT / "rescamp/scripts/benchmark.py")
bench = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(bench)
payload = json.loads(sys.stdin.read())
condition = payload.get("condition_for_fixture", "rescamp-0.8-fixture")
# The harness intentionally omits the condition in a real blinded evaluation. The
# process fixture infers behavior class from the transcript only.
transcript = payload["transcript"]
max_q = max([event.get("question_count", 0) for event in transcript if event.get("role") == "assistant"] or [0])
turns = sum(1 for event in transcript if event.get("role") == "assistant" and event.get("action") == "ask")
if max_q > 1:
    inferred = "exhaustive-form-fixture"
elif turns <= 2:
    inferred = "no-skill-fixture"
else:
    inferred = "rescamp-0.8-fixture"
result = bench.fixture_team_e(payload["hidden_scenario"], transcript, payload["final_response"], inferred)
print(json.dumps(result, ensure_ascii=False))
