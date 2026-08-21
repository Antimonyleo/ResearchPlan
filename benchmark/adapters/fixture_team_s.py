#!/usr/bin/env python3
"""Process-isolated deterministic Team S fixture; not a model-quality baseline."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("bench", ROOT / "rescamp/scripts/benchmark.py")
bench = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(bench)

parser = argparse.ArgumentParser()
parser.add_argument("--condition", required=True)
args = parser.parse_args()
payload = json.loads(sys.stdin.read())
history = payload["history"]
state = {
    "asked_branches": [event.get("branch") for event in history if event.get("role") == "assistant" and event.get("action") == "ask" and event.get("branch") not in {None, "", "multi"}],
}
for event in history:
    if event.get("role") == "assistant" and event.get("action") == "ask":
        state["asked_branches"].extend(event.get("branches", []))
response = bench.fixture_team_s(args.condition, payload["public_scenario"], history, state)
response.pop("state", None)
print(json.dumps(response, ensure_ascii=False))
