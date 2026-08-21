#!/usr/bin/env python3
"""Process-isolated deterministic hidden-user fixture; not a real user study."""
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
print(json.dumps(bench.fixture_team_u(payload["hidden_scenario"], payload["assistant_question"], payload["history"]), ensure_ascii=False))
