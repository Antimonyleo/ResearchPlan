#!/usr/bin/env python3
"""Run one explicit ResCamp skill mode through Claude Code or Codex."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import tempfile
import time
from pathlib import Path
from typing import NamedTuple


CANONICAL_MODES = ("Camp-auto", "Camp-brief", "Camp-full")
REQUIRED_SKILL_FILES = (
    "SKILL.md",
    "VERSION",
    "LICENSE",
    "agents/openai.yaml",
    "assets/archetype_overlays.json",
    "assets/campaign.schema.json",
    "assets/review.schema.json",
    "assets/scenario.schema.json",
    "assets/universal_rubric.json",
    "references/archetypes.md",
    "references/architecture.md",
    "references/benchmark.md",
    "references/hosts.md",
    "references/interview.md",
    "references/objects.md",
    "references/quality-loop.md",
    "scripts/benchmark.py",
    "scripts/rescamp.py",
    "scripts/validate_skill.py",
)


def has_symlink_component(root: Path, path: Path) -> bool:
    current = root
    for part in path.relative_to(root).parts:
        current /= part
        if current.is_symlink():
            return True
    return False


def required_skill_errors(project: Path, skill_root: Path) -> list[str]:
    errors: list[str] = []
    if not skill_root.is_dir() or has_symlink_component(project, skill_root):
        return ["skill root is missing or uses symlinks"]
    for relative in REQUIRED_SKILL_FILES:
        path = skill_root / relative
        if has_symlink_component(skill_root, path):
            errors.append(f"required path uses a symlink: {relative}")
        elif not path.is_file():
            errors.append(f"missing: {relative}")
    return errors


class HostAdapter(NamedTuple):
    prompt_prefix: str
    executable: str
    skill_path: str
    command_args: tuple[str, ...]
    json_response: bool = False

    def command(self, executable: str, project: Path, response_path: Path) -> list[str]:
        values = {"project": str(project), "response": str(response_path)}
        return [executable, *(argument.format(**values) for argument in self.command_args)]

    def response_ok(self, response: str) -> bool:
        if not response.strip():
            return False
        if self.json_response:
            try:
                envelope = json.loads(response)
            except json.JSONDecodeError:
                return False
            if not isinstance(envelope, dict) or envelope.get("is_error") is not False:
                return False
            raw_result = envelope.get("result")
            if not isinstance(raw_result, str):
                return False
            result = raw_result.strip()
        else:
            result = response.strip()
        refusal_markers = (
            "skill is disabled", "can't invoke it", "cannot invoke it",
            "unknown skill", "skill not found", "no such skill",
        )
        lowered = result.lower()
        return (bool(result) and not lowered.startswith(("error:", "fatal:"))
                and not any(marker in lowered for marker in refusal_markers))


HOST_ADAPTERS = {
    "claude-code": HostAdapter(
        prompt_prefix="/rescamp",
        executable="claude",
        skill_path=".claude/skills/rescamp/SKILL.md",
        command_args=("-p", "--permission-mode", "auto", "--output-format", "json",
                      "--no-session-persistence"),
        json_response=True,
    ),
    "codex": HostAdapter(
        prompt_prefix="/rescamp",
        executable="codex",
        skill_path=".agents/skills/rescamp/SKILL.md",
        command_args=("exec", "--ephemeral", "--approve-for-me",
                      "--skip-git-repo-check", "-C", "{project}",
                      "-o", "{response}", "-"),
    ),
}


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def digest_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*")
                       if item.is_file() and "__pycache__" not in item.parts):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(b"x" if os.access(path, os.X_OK) else b"-")
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _process_group_kwargs() -> dict[str, object]:
    if os.name == "posix":
        return {"start_new_session": True}
    if os.name == "nt":
        return {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
    return {}


def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    """Kill a timed-out host and descendants, tolerating exit races."""
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
        except OSError:
            pass
    try:
        process.kill()
    except ProcessLookupError:
        pass


def artifact_fingerprint(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    return {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size": path.stat().st_size,
    }


def project_fingerprint(project: Path, path: Path) -> dict[str, object] | None:
    """Fingerprint one project-contained file, resolving symlinks at observation time."""
    resolved = path.resolve()
    if project not in resolved.parents and resolved != project:
        raise ValueError(f"artifact resolved outside the project: {path}")
    return artifact_fingerprint(resolved)


def glob_fingerprints(project: Path, pattern: str) -> dict[str, dict[str, object]]:
    candidate = Path(pattern)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise SystemExit(f"--expect-glob must stay inside the project: {pattern}")
    fingerprints: dict[str, dict[str, object]] = {}
    for path in sorted(project.glob(pattern)):
        resolved = path.resolve()
        if project not in resolved.parents and resolved != project:
            raise SystemExit(f"--expect-glob matched outside the project: {path}")
        fingerprint = artifact_fingerprint(resolved)
        if fingerprint is not None:
            fingerprints[path.relative_to(project).as_posix()] = fingerprint
    return fingerprints


def build_prompt(host: str, mode: str, goal: str | None, campaign: str | None) -> str:
    prefix = HOST_ADAPTERS[host].prompt_prefix
    if mode in CANONICAL_MODES:
        if goal and campaign:
            raise SystemExit("pass either --goal or --campaign, not both")
        if campaign:
            if mode != "Camp-full":
                raise SystemExit("--campaign is supported only for Camp-full promotion")
            return f"{prefix} {mode} {campaign}"
        if not goal:
            raise SystemExit(f"--goal is required for {mode}")
        return f"{prefix} {mode} {goal}"
    if goal or campaign:
        raise SystemExit("help does not accept --goal or --campaign")
    return f"{prefix} help"


def command_for(host: str, executable: str, project: Path, response_path: Path) -> list[str]:
    return HOST_ADAPTERS[host].command(executable, project, response_path)


def response_ok(host: str, response: str) -> bool:
    return HOST_ADAPTERS[host].response_ok(response)


def run_process(command: list[str], project: Path, timeout: int,
                input_text: str | None = None) -> tuple[subprocess.CompletedProcess[str], bool]:
    """Run a host command and terminate its process group on timeout."""
    try:
        process = subprocess.Popen(
            command, cwd=project, stdin=subprocess.PIPE if input_text is not None else None,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            **_process_group_kwargs(),
        )
    except OSError as exc:
        return subprocess.CompletedProcess(command, 127, "", str(exc)), False
    try:
        stdout, stderr = process.communicate(input_text, timeout=timeout)
        return subprocess.CompletedProcess(command, process.returncode, stdout, stderr), False
    except subprocess.TimeoutExpired:
        _terminate_process_group(process)
        stdout, stderr = process.communicate()
        return subprocess.CompletedProcess(command, 124, stdout, stderr), True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=sorted(HOST_ADAPTERS), required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument(
        "--mode", choices=(*CANONICAL_MODES, "help"), required=True,
    )
    parser.add_argument("--goal")
    parser.add_argument("--campaign")
    parser.add_argument("--executable")
    parser.add_argument("--timeout", type=positive_int, default=900)
    parser.add_argument("--receipt")
    parser.add_argument("--expect", action="append", default=[],
                        help="project-relative artifact that must exist after the host exits; repeatable")
    parser.add_argument(
        "--expect-glob", action="append", default=[],
        help="project-relative artifact pattern when the host chooses an identifier; repeatable",
    )
    parser.add_argument("--evidence-dir", help="store request, response, stderr, and receipt")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    prompt = build_prompt(args.host, args.mode, args.goal, args.campaign)
    if not args.dry_run and args.mode != "help" and not (args.expect or args.expect_glob):
        raise SystemExit(
            "--expect or --expect-glob is required for every non-help live run so an "
            "exit-0 response alone cannot pass host acceptance"
        )
    adapter = HOST_ADAPTERS[args.host]
    executable = args.executable or adapter.executable
    with tempfile.TemporaryDirectory(prefix="rescamp-host-") as temp_str:
        response_path = Path(temp_str) / "last-message.txt"
        command = command_for(args.host, executable, project, response_path)
        receipt: dict[str, object] = {
            "host": args.host,
            "mode": args.mode,
            "project": str(project),
            "command": command,
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "dry_run": bool(args.dry_run),
            "acceptance_scope": "transport-response-and-artifact-change",
        }
        if args.dry_run:
            receipt["prompt"] = prompt
        else:
            skill_path = project / adapter.skill_path
            if not skill_path.is_file() or skill_path.is_symlink():
                raise SystemExit(f"ResCamp is not installed for {args.host} at {skill_path}")
            skill_root = skill_path.parent
            skill_errors = required_skill_errors(project, skill_root)
            if skill_errors:
                raise SystemExit(
                    "ResCamp installation is incomplete; "
                    + "; ".join(skill_errors)
                )
            expected_paths: dict[str, Path] = {}
            expected_before: dict[str, dict[str, object] | None] = {}
            expected_glob_before: dict[str, dict[str, dict[str, object]]] = {}
            for relative in args.expect:
                candidate = project / relative
                resolved = candidate.resolve()
                if project not in resolved.parents and resolved != project:
                    raise SystemExit(f"--expect must stay inside the project: {relative}")
                expected_paths[relative] = candidate
            expected_glob_before = {
                pattern: glob_fingerprints(project, pattern)
                for pattern in args.expect_glob
            }
            started = time.monotonic()
            timeout_stage = ""
            failure_stage = ""
            version_result, version_timed_out = run_process(
                [executable, "--version"], project, min(args.timeout, 30),
            )
            if version_timed_out:
                timeout_stage = "version"
            elif version_result.returncode == 127:
                failure_stage = "version"
            host_version = (version_result.stdout or version_result.stderr).strip()
            # The version probe is not the accepted workflow. Snapshot only after it so
            # an ill-behaved executable cannot satisfy the artifact check from --version.
            expected_before = {
                relative: project_fingerprint(project, candidate)
                for relative, candidate in expected_paths.items()
            }
            if timeout_stage or failure_stage or version_result.returncode != 0:
                failure_stage = failure_stage or ("" if timeout_stage else "version")
                result = subprocess.CompletedProcess(
                    command, version_result.returncode, "", "host version check failed",
                )
            else:
                result, host_timed_out = run_process(command, project, args.timeout, prompt)
                if host_timed_out:
                    timeout_stage = "host"
                elif result.returncode == 127:
                    failure_stage = "host"
            response = response_path.read_text(encoding="utf-8") if response_path.exists() else result.stdout
            expected: dict[str, bool] = {}
            expected_after: dict[str, dict[str, object] | None] = {}
            artifact_errors: dict[str, str] = {}
            for relative, candidate in expected_paths.items():
                try:
                    after = project_fingerprint(project, candidate)
                except ValueError as exc:
                    after = None
                    artifact_errors[relative] = str(exc)
                expected_after[relative] = after
                expected[relative] = after is not None and after != expected_before[relative]
            expected_globs: dict[str, bool] = {}
            expected_glob_after: dict[str, dict[str, dict[str, object]]] = {}
            for pattern, before in expected_glob_before.items():
                after = glob_fingerprints(project, pattern)
                expected_glob_after[pattern] = after
                expected_globs[pattern] = any(
                    fingerprint != before.get(path)
                    for path, fingerprint in after.items()
                )
            receipt.update({
                "returncode": result.returncode,
                "host_version": host_version,
                "host_version_returncode": version_result.returncode,
                "skill_tree_sha256": digest_tree(skill_root),
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "timed_out": bool(timeout_stage),
                "timeout_stage": timeout_stage or None,
                "failure_stage": failure_stage or None,
                "response_sha256": hashlib.sha256(response.encode("utf-8")).hexdigest(),
                "stderr_sha256": hashlib.sha256(result.stderr.encode("utf-8")).hexdigest(),
                "response_nonempty": bool(response.strip()),
                "expected_artifacts": expected,
                "expected_artifact_before": expected_before,
                "expected_artifact_after": expected_after,
                "expected_artifact_globs": expected_globs,
                "expected_artifact_glob_before": expected_glob_before,
                "expected_artifact_glob_after": expected_glob_after,
                "artifact_errors": artifact_errors,
                "passed": result.returncode == 0 and version_result.returncode == 0
                and response_ok(args.host, response) and all(expected.values())
                and all(expected_globs.values()),
            })
        text = json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        if args.evidence_dir and not args.dry_run:
            evidence = Path(args.evidence_dir).resolve()
            evidence.mkdir(parents=True, exist_ok=True)
            (evidence / "request.txt").write_text(prompt, encoding="utf-8")
            (evidence / "response.txt").write_text(response, encoding="utf-8")
            (evidence / "stderr.txt").write_text(result.stderr, encoding="utf-8")
            (evidence / "receipt.json").write_text(text, encoding="utf-8")
        if args.receipt:
            path = Path(args.receipt).resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        print(text, end="")
        return 0 if args.dry_run or receipt.get("passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
