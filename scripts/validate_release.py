#!/usr/bin/env python3
"""Run the complete deterministic ResCamp validation suite."""
from __future__ import annotations

import argparse
import json
import os
import signal
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterator


EXCLUDED_TOP_LEVEL = frozenset({
    ".agents", ".claude", ".codex", ".dist", ".git", ".pytest_cache",
    ".venv", "dist", "node_modules", "research-campaigns", "venv",
})
EXCLUDED_EXAMPLE_DIRS = frozenset({"artifacts", "private", "transient", "working"})


def repository_files(root: Path, pattern: str) -> Iterator[Path]:
    """Yield source files, excluding local installs, caches, and generated runs."""
    for path in root.rglob(pattern):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if (not relative.parts
                or relative.parts[0] in EXCLUDED_TOP_LEVEL
                or "__pycache__" in relative.parts
                or relative.parts[:2] == ("benchmark", "runs")
                or (relative.parts[:2] == ("docs", "examples")
                    and any(part in EXCLUDED_EXAMPLE_DIRS
                            for part in relative.parts[2:-1]))):
            continue
        yield path


def _captured_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return str(value)


def _process_group_kwargs() -> dict[str, Any]:
    if os.name == "posix":
        return {"start_new_session": True}
    if os.name == "nt":
        return {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
    return {}


def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    """Kill a timed-out process and descendants, tolerating exit races."""
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        return
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, check=False,
            )
            return
        except (OSError, ProcessLookupError):
            pass
    try:
        process.kill()
    except ProcessLookupError:
        pass


def run(command: list[str], cwd: Path, timeout: int = 180, env: dict[str, str] | None = None) -> dict[str, Any]:
    started = time.monotonic()
    child_env = dict(os.environ if env is None else env)
    child_env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    proc = subprocess.Popen(
        command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=child_env, **_process_group_kwargs(),
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        _terminate_process_group(proc)
        stdout, stderr = proc.communicate()
        timeout_message = f"command timed out after {timeout} seconds"
        captured_stderr = _captured_text(stderr or exc.stderr)
        if captured_stderr:
            captured_stderr = f"{captured_stderr.rstrip()}\n{timeout_message}"
        else:
            captured_stderr = timeout_message
        return {
            "command": command,
            "returncode": 124,
            "timed_out": True,
            "timeout_seconds": timeout,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "stdout": _captured_text(stdout or exc.stdout)[-20000:],
            "stderr": captured_stderr[-20000:],
        }
    return {
        "command": command,
        "returncode": proc.returncode,
        "timed_out": False,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "stdout": _captured_text(stdout)[-20000:],
        "stderr": _captured_text(stderr)[-20000:],
    }


def compile_python(root: Path) -> list[str]:
    errors = []
    for path in sorted(repository_files(root, "*.py")):
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as exc:
            errors.append(f"{path.relative_to(root)}:{exc.lineno}: {exc.msg}")
    return errors


def validate_json(root: Path) -> tuple[list[str], list[str]]:
    """Return JSON and schema errors plus non-blocking release warnings."""
    errors: list[str] = []
    warnings: list[str] = []
    for path in sorted(repository_files(root, "*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{path.relative_to(root)}: {exc}")
    try:
        import jsonschema  # type: ignore
    except ImportError:
        errors.append("jsonschema is not installed; schema validation cannot run "
                      "(pip install jsonschema)")
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


def ignore_example_transients(_directory: str, names: list[str]) -> list[str]:
    """Keep copied examples limited to release inputs and published outputs."""
    return [
        name for name in names
        if name in EXCLUDED_EXAMPLE_DIRS
        or name == "__pycache__"
        or name.endswith(".cover")
    ]


def audit_examples(root: Path, temp: Path) -> dict[str, dict[str, Any]]:
    """Audit committed examples in copies so release validation never mutates source."""
    results: dict[str, dict[str, Any]] = {}
    for state_path in sorted((root / "docs/examples").glob("*/state/campaign.json")):
        source = state_path.parent.parent
        target = temp / "examples" / source.name
        shutil.copytree(source, target, ignore=ignore_example_transients)
        results[source.name] = run([
            sys.executable, "rescamp/scripts/rescamp.py", "audit", str(target), "--strict",
        ], root)
    return results


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

    skill_files = sorted(repository_files(root, "SKILL.md"))
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
        example_audits = audit_examples(root, temp)
        checks["committed_example_audits"] = example_audits
        for name, audit in example_audits.items():
            if audit["returncode"]:
                errors.append(f"committed example audit failed: {name}")
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

    version_path = root / "rescamp/VERSION"
    if not version_path.is_file():
        errors.append("rescamp/VERSION is missing")
        release_version = "unknown"
    else:
        release_version = version_path.read_text(encoding="utf-8").strip()
    result = {
        "release": f"rescamp-{release_version}",
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
