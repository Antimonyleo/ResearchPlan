#!/usr/bin/env python3
"""Run one explicit ResCamp skill mode through Claude Code or Codex."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path


HOST_PREFIX = {"claude-code": "/rescamp", "codex": "$rescamp"}
HOST_EXECUTABLE = {"claude-code": "claude", "codex": "codex"}
HOST_SKILL = {"claude-code": ".claude/skills/rescamp/SKILL.md",
              "codex": ".agents/skills/rescamp/SKILL.md"}


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


def artifact_fingerprint(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    stat = path.stat()
    return {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def build_prompt(host: str, mode: str, goal: str | None, campaign: str | None) -> str:
    prefix = HOST_PREFIX[host]
    if mode == "start":
        if not goal:
            raise SystemExit("--goal is required for start")
        return f"{prefix} start {goal}"
    if mode in {"review", "test", "finalize"}:
        if not campaign:
            raise SystemExit(f"--campaign is required for {mode}")
        return f"{prefix} {mode} {campaign}"
    return f"{prefix} help"


def command_for(host: str, executable: str, project: Path, response_path: Path) -> list[str]:
    if host == "codex":
        return [executable, "exec", "--ephemeral", "--approve-for-me",
                "-C", str(project), "-o", str(response_path), "-"]
    return [executable, "-p", "--permission-mode", "auto", "--output-format", "json",
            "--no-session-persistence"]


def response_ok(host: str, response: str) -> bool:
    if not response.strip():
        return False
    if host == "claude-code":
        try:
            envelope = json.loads(response)
        except json.JSONDecodeError:
            return False
        if envelope.get("is_error") is True:
            return False
        result = str(envelope.get("result", "")).strip()
    else:
        result = response.strip()
    refusal_markers = (
        "skill is disabled", "can't invoke it", "cannot invoke it",
        "unknown skill", "skill not found", "no such skill",
    )
    lowered = result.lower()
    return (bool(result) and not lowered.startswith(("error:", "fatal:"))
            and not any(marker in lowered for marker in refusal_markers))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=sorted(HOST_PREFIX), required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--mode", choices=("start", "review", "test", "finalize", "help"), required=True)
    parser.add_argument("--goal")
    parser.add_argument("--campaign")
    parser.add_argument("--executable")
    parser.add_argument("--timeout", type=positive_int, default=900)
    parser.add_argument("--receipt")
    parser.add_argument("--expect", action="append", default=[],
                        help="project-relative artifact that must exist after the host exits; repeatable")
    parser.add_argument("--evidence-dir", help="store request, response, stderr, and receipt")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    prompt = build_prompt(args.host, args.mode, args.goal, args.campaign)
    if not args.dry_run and args.mode != "help" and not args.expect:
        raise SystemExit(
            "--expect is required for start/review/test/finalize so an exit-0 response "
            "alone cannot pass host acceptance"
        )
    executable = args.executable or HOST_EXECUTABLE[args.host]
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
            skill_path = project / HOST_SKILL[args.host]
            if not skill_path.is_file():
                raise SystemExit(f"ResCamp is not installed for {args.host} at {skill_path}")
            skill_root = skill_path.parent
            expected_paths: dict[str, Path] = {}
            expected_before: dict[str, dict[str, object] | None] = {}
            for relative in args.expect:
                candidate = (project / relative).resolve()
                if project not in candidate.parents and candidate != project:
                    raise SystemExit(f"--expect must stay inside the project: {relative}")
                expected_paths[relative] = candidate
            started = time.monotonic()
            timeout_stage = ""
            failure_stage = ""
            try:
                version_result = subprocess.run(
                    [executable, "--version"], cwd=project, text=True, capture_output=True,
                    timeout=min(args.timeout, 30), check=False,
                )
            except subprocess.TimeoutExpired as exc:
                timeout_stage = "version"
                stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
                stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
                version_result = subprocess.CompletedProcess(
                    [executable, "--version"], 124, stdout, stderr,
                )
            except OSError as exc:
                failure_stage = "version"
                version_result = subprocess.CompletedProcess(
                    [executable, "--version"], 127, "", str(exc),
                )
            host_version = (version_result.stdout or version_result.stderr).strip()
            # The version probe is not the accepted workflow. Snapshot only after it so
            # an ill-behaved executable cannot satisfy the artifact check from --version.
            expected_before = {
                relative: artifact_fingerprint(candidate)
                for relative, candidate in expected_paths.items()
            }
            if timeout_stage or failure_stage or version_result.returncode != 0:
                failure_stage = failure_stage or ("" if timeout_stage else "version")
                result = subprocess.CompletedProcess(
                    command, version_result.returncode, "", "host version check failed",
                )
            else:
                try:
                    result = subprocess.run(command, cwd=project, input=prompt, text=True,
                                            capture_output=True, timeout=args.timeout, check=False)
                except subprocess.TimeoutExpired as exc:
                    timeout_stage = "host"
                    stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
                    stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
                    result = subprocess.CompletedProcess(command, 124, stdout, stderr)
                except OSError as exc:
                    failure_stage = "host"
                    result = subprocess.CompletedProcess(command, 127, "", str(exc))
            response = response_path.read_text(encoding="utf-8") if response_path.exists() else result.stdout
            expected: dict[str, bool] = {}
            expected_after: dict[str, dict[str, object] | None] = {}
            for relative, candidate in expected_paths.items():
                after = artifact_fingerprint(candidate)
                expected_after[relative] = after
                expected[relative] = after is not None and after != expected_before[relative]
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
                "passed": result.returncode == 0 and version_result.returncode == 0
                and response_ok(args.host, response) and all(expected.values()),
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
