#!/usr/bin/env python3
"""Run deterministic and process-isolated release checks for ResCamp."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

VERSION = "0.9.0"
REPOSITORY_INPUT_ROOTS = ("rescamp", "benchmark", "scripts", "tests", "docs")
REPOSITORY_INPUT_FILES = (
    ".gitignore", "AGENTS.md", "CHANGELOG.md", "CONTRIBUTING.md",
    "LICENSE", "Makefile", "README.md", "SECURITY.md",
)


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


def digest_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and path_allowed(p)):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(b"x" if os.access(path, os.X_OK) else b"-")
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def path_allowed(path: Path) -> bool:
    return path.suffix not in {".pyc", ".pyo"}


def repository_input_digest(root: Path) -> str:
    """Bind release evidence to every maintained input, excluding generated QA output."""
    paths: list[Path] = []
    for name in REPOSITORY_INPUT_ROOTS:
        base = root / name
        if base.exists():
            paths.extend(path for path in base.rglob("*")
                         if path.is_file()
                         and "__pycache__" not in path.parts
                         and "benchmark/runs" not in path.relative_to(root).as_posix()
                         and path.relative_to(root).as_posix() != "docs/RELEASE_REPORT.md"
                         and path_allowed(path))
    paths.extend(root / name for name in REPOSITORY_INPUT_FILES if (root / name).is_file())
    digest = hashlib.sha256()
    for path in sorted(set(paths)):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def repository_provenance(root: Path) -> dict[str, Any]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=False
    )
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=root, text=True, capture_output=True, check=False,
    )
    dirty_paths = [line[3:] for line in status.stdout.splitlines() if len(line) >= 4]
    return {
        "repository_input_sha256": repository_input_digest(root),
        "git_commit": commit.stdout.strip() if commit.returncode == 0 else None,
        "git_dirty": bool(dirty_paths) if status.returncode == 0 else None,
        "dirty_paths": dirty_paths,
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


def validate_json(root: Path) -> list[str]:
    errors = []
    for path in sorted(root.rglob("*.json")):
        if "benchmark/runs" in path.as_posix():
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{path.relative_to(root)}: {exc}")
    try:
        import jsonschema  # type: ignore
        for name in ("campaign.schema.json", "review.schema.json", "scenario.schema.json"):
            schema = json.loads((root / "rescamp/assets" / name).read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator.check_schema(schema)
        scenario_schema = json.loads((root / "rescamp/assets/scenario.schema.json").read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(scenario_schema)
        for path in sorted((root / "benchmark/scenarios/public").glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for problem in validator.iter_errors(data):
                errors.append(f"{path.relative_to(root)} schema: {problem.message}")
    except ImportError:
        pass
    except Exception as exc:
        errors.append(f"JSON Schema validation: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--output")
    parser.add_argument("--quick", action="store_true", help="skip process-isolated adapter smoke test")
    parser.add_argument("--evidence-dir", help="copy selected machine-readable QA evidence here")
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

    cache_files = [p for p in root.rglob("*") if p.is_file() and (p.suffix in {".pyc", ".pyo"} or "__pycache__" in p.parts)]
    if cache_files:
        warnings.append(f"working tree contains {len(cache_files)} cache files; release builder excludes them")

    checks["python_compile"] = {"errors": compile_python(root)}
    errors.extend(checks["python_compile"]["errors"])
    checks["json"] = {"errors": validate_json(root)}
    errors.extend(checks["json"]["errors"])

    reviewer_roles = ["architecture", "generalization", "usability", "quality-workflow", "packaging-integrity"]
    def run_reviewer(role: str) -> dict[str, Any]:
        return run([sys.executable, "scripts/static_reviewer.py", "--role", role, "--root", str(root)], root)
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(reviewer_roles)) as pool:
        reviewer_runs = dict(zip(reviewer_roles, pool.map(run_reviewer, reviewer_roles)))
    checks["process_isolated_static_reviewers"] = reviewer_runs
    if any(item["returncode"] for item in reviewer_runs.values()):
        errors.append("one or more process-isolated static reviewer roles failed")

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

        home = temp / "home"
        home.mkdir()
        env = dict(os.environ)
        env["HOME"] = str(home)
        install = run([sys.executable, "scripts/install.py", "--host", "both", "--scope", "user"], root, env=env)
        checks["dual_host_install"] = install
        if install["returncode"]:
            errors.append("dual-host installation test failed")
        else:
            claude = home / ".claude/skills/rescamp"
            codex = home / ".agents/skills/rescamp"
            source_digest = digest_tree(root / "rescamp")
            installed = {"source": source_digest, "claude": digest_tree(claude), "codex": digest_tree(codex)}
            checks["installed_tree_digests"] = installed
            if len(set(installed.values())) != 1:
                errors.append("Claude and Codex installed skill trees are not byte-identical")

        if args.evidence_dir:
            evidence = Path(args.evidence_dir).resolve()
            evidence.mkdir(parents=True, exist_ok=True)
            if fixture_out.exists():
                shutil.copy2(fixture_out / "summary.json", evidence / "full_fixture_summary.json")
                shutil.copy2(fixture_out / "scores.json", evidence / "full_fixture_scores.json")
            if not args.quick and process_out.exists():
                shutil.copytree(process_out, evidence / "process_isolated_three_team_runs", dirs_exist_ok=True)
            (evidence / "unit_tests.stdout.txt").write_text(tests["stdout"], encoding="utf-8")
            (evidence / "unit_tests.stderr.txt").write_text(tests["stderr"], encoding="utf-8")
            (evidence / "scenario_validation.json").write_text(scenarios["stdout"], encoding="utf-8")
            (evidence / "static_reviewer_runs.json").write_text(json.dumps(reviewer_runs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    result = {
        "release": f"rescamp-{VERSION}",
        "valid": not errors,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "root": str(root),
        "skill_tree_sha256": digest_tree(root / "rescamp") if (root / "rescamp").exists() else None,
        "repository_provenance": repository_provenance(root),
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
    }
    text = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    if args.evidence_dir:
        Path(args.evidence_dir).resolve().mkdir(parents=True, exist_ok=True)
        (Path(args.evidence_dir).resolve() / "release_check.json").write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
