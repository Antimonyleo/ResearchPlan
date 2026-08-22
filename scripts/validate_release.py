#!/usr/bin/env python3
"""Run the complete deterministic ResCamp validation suite."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

VERSION = "0.10.0"


def run(command: list[str], cwd: Path, timeout: int = 180, env: dict[str, str] | None = None) -> dict[str, Any]:
    started = time.monotonic()
    child_env = dict(os.environ if env is None else env)
    child_env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    proc = subprocess.run(
        command, cwd=cwd, text=True, capture_output=True, timeout=timeout,
        env=child_env, check=False,
    )
    return {
        "command": command,
        "returncode": proc.returncode,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "stdout": proc.stdout[-20000:],
        "stderr": proc.stderr[-20000:],
    }


def compile_python(root: Path) -> list[str]:
    errors = []
    for path in sorted(root.rglob("*.py")):
        if any(part in {".git", "benchmark/runs", "dist", ".dist"} for part in path.parts):
            continue
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as exc:
            errors.append(f"{path.relative_to(root)}:{exc.lineno}: {exc.msg}")
    return errors


def validate_json(root: Path) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings). Warnings cover checks that could not run at all."""
    errors: list[str] = []
    warnings: list[str] = []
    for path in sorted(root.rglob("*.json")):
        if "benchmark/runs" in path.as_posix():
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{path.relative_to(root)}: {exc}")
    try:
        import jsonschema  # type: ignore
    except ImportError:
        # Skipping silently reported `valid: true, warnings: 0` on a machine without
        # jsonschema, with every scenario and campaign left unchecked. Say so instead.
        warnings.append("jsonschema is not installed; scenario and campaign schema "
                        "validation did not run (pip install jsonschema)")
        return errors, warnings
    try:
        for name in ("campaign.schema.json", "review.schema.json", "scenario.schema.json"):
            schema = json.loads((root / "rescamp/assets" / name).read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator.check_schema(schema)
        scenario_schema = json.loads((root / "rescamp/assets/scenario.schema.json").read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(scenario_schema)
        for path in sorted((root / "benchmark/scenarios/public").glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for problem in validator.iter_errors(data):
                errors.append(f"{path.relative_to(root)} schema: {problem.message}")
        # `campaign.schema.json` ships as the contract for the published `campaign.json`.
        # Checking only that it is well-formed left it free to drift from the engine, so
        # validate it against real committed state.
        campaign_schema = json.loads((root / "rescamp/assets/campaign.schema.json").read_text(encoding="utf-8"))
        campaign_validator = jsonschema.Draft202012Validator(campaign_schema)
        states = sorted((root / "docs/examples").glob("*/state/campaign.json"))
        if not states:
            warnings.append("no committed example campaign state; campaign.schema.json "
                            "was checked for well-formedness only")
        for path in states:
            data = json.loads(path.read_text(encoding="utf-8"))
            for problem in campaign_validator.iter_errors(data):
                errors.append(f"{path.relative_to(root)} schema: {problem.message}")
    except Exception as exc:
        errors.append(f"JSON Schema validation: {exc}")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--output")
    parser.add_argument("--quick", action="store_true", help="skip process-isolated adapter smoke test")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    started = time.monotonic()
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, Any] = {}

    skill_files = sorted(root.rglob("SKILL.md"))
    checks["canonical_skill"] = {"count": len(skill_files), "paths": [str(p.relative_to(root)) for p in skill_files]}
    if skill_files != [root / "rescamp/SKILL.md"]:
        errors.append("repository must contain exactly rescamp/SKILL.md")

    checks["python_compile"] = {"errors": compile_python(root)}
    errors.extend(checks["python_compile"]["errors"])
    json_errors, json_warnings = validate_json(root)
    checks["json"] = {"errors": json_errors, "warnings": json_warnings}
    errors.extend(json_errors)
    warnings.extend(json_warnings)

    skill_check = run([sys.executable, "rescamp/scripts/validate_skill.py", "rescamp"], root)
    checks["skill_self_check"] = skill_check
    if skill_check["returncode"]:
        errors.append("skill self-check failed")

    tests = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], root)
    checks["unit_tests"] = tests
    if tests["returncode"]:
        errors.append("unit tests failed")

    scenarios = run([sys.executable, "rescamp/scripts/benchmark.py", "validate-scenarios", "benchmark/scenarios/public"], root)
    checks["scenario_validation"] = scenarios
    if scenarios["returncode"]:
        errors.append("scenario validation failed")

    with tempfile.TemporaryDirectory(prefix="rescamp-release-") as temp_str:
        temp = Path(temp_str)
        fixture_out = temp / "fixture"
        fixture = run([
            sys.executable, "rescamp/scripts/benchmark.py", "run",
            "--scenarios", "benchmark/scenarios/public",
            "--config", "benchmark/conditions/fixture.json",
            "--output", str(fixture_out), "--jobs", "6", "--timeout", "30",
        ], root, timeout=120)
        checks["full_fixture_matrix"] = fixture
        if fixture["returncode"]:
            errors.append("full fixture benchmark failed")
        elif (fixture_out / "summary.json").exists():
            checks["full_fixture_summary"] = json.loads((fixture_out / "summary.json").read_text(encoding="utf-8"))

        if not args.quick:
            subset = temp / "scenarios"
            subset.mkdir()
            for name in ("dna-colloid-photonics.json", "protein-binder-pilot.json", "port-city-archive.json", "remote-work-qualitative.json"):
                shutil.copy2(root / "benchmark/scenarios/public" / name, subset / name)
            process_out = temp / "process-fixture"
            process_run = run([
                sys.executable, "rescamp/scripts/benchmark.py", "run",
                "--scenarios", str(subset),
                "--config", "benchmark/conditions/process-isolated-fixture.json",
                "--output", str(process_out), "--jobs", "6", "--timeout", "30",
            ], root, timeout=180)
            checks["process_isolated_three_team_smoke"] = process_run
            if process_run["returncode"]:
                errors.append("process-isolated Team U/S/E smoke test failed")
            elif (process_out / "summary.json").exists():
                checks["process_fixture_summary"] = json.loads((process_out / "summary.json").read_text(encoding="utf-8"))

    result = {
        "release": f"rescamp-{VERSION}",
        "valid": not errors,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "root": str(root),
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
    }
    text = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
