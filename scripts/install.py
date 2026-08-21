#!/usr/bin/env python3
"""Install the exact same ResCamp skill directory for Claude Code and/or Codex."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "rescamp"


def digest_tree(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        h.update(path.relative_to(root).as_posix().encode())
        h.update(b"\0")
        # Include the executable bit: a copy that lost 0755 on scripts/*.py is not identical.
        h.update(b"x" if os.access(path, os.X_OK) else b"-")
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def update_claude_override(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Refusing to modify invalid JSON settings file {path}: {exc}")
    else:
        data = {}
    overrides = data.setdefault("skillOverrides", {})
    overrides["rescamp"] = "user-invocable-only"
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


# Host registry. Adding a harness is a data change here plus a row in
# rescamp/references/hosts.md — never an edit to the canonical SKILL.md.
# `settings_writer` is for hosts that keep explicit-only policy in host settings
# rather than in a metadata file inside the bundle.
HOSTS: dict[str, dict[str, object]] = {
    "claude-code": {
        "user_path": ".claude/skills/rescamp",
        "project_path": ".claude/skills/rescamp",
        "settings_writer": "claude_override",
        "user_settings": ".claude/settings.json",
        "project_settings": ".claude/settings.local.json",
    },
    "codex": {
        "user_path": ".agents/skills/rescamp",
        "project_path": ".agents/skills/rescamp",
        "settings_writer": None,
    },
}
HOST_ALIASES = {"claude": "claude-code"}


def resolve_host(name: str) -> str:
    host = HOST_ALIASES.get(name, name)
    if host not in HOSTS:
        raise SystemExit(f"Unknown host {name!r}; known hosts: {', '.join(sorted(HOSTS))}")
    return host


def destination(host: str, scope: str, project: Path) -> Path:
    entry = HOSTS[resolve_host(host)]
    rel = str(entry["user_path"] if scope == "user" else entry["project_path"])
    return (Path.home() / rel) if scope == "user" else (project / rel)


def install_one(host: str, scope: str, project: Path, force: bool, symlink: bool) -> Path:
    dest = destination(host, scope, project)
    if dest.exists() or dest.is_symlink():
        if not force:
            raise SystemExit(f"Destination exists; use --force: {dest}")
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
        else:
            shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if symlink:
        dest.symlink_to(SOURCE, target_is_directory=True)
        # Comparing digest_tree(dest.resolve()) here would resolve back to SOURCE and
        # compare it with itself, which can never fail. Check the link target instead.
        if dest.resolve() != SOURCE.resolve():
            raise SystemExit(f"Symlink target mismatch for {dest}: {dest.resolve()} != {SOURCE.resolve()}")
    else:
        shutil.copytree(SOURCE, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        if digest_tree(dest) != digest_tree(SOURCE):
            raise SystemExit(f"Installed tree hash mismatch for {dest}")
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="all",
                        help="host id, 'all', or 'both'; known: " + ", ".join(sorted(HOSTS)))
    parser.add_argument("--scope", choices=["user", "project"], default="user")
    parser.add_argument("--project", default=".", help="project root for project scope")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--symlink", action="store_true", help="link both hosts to this canonical source instead of copying")
    parser.add_argument("--no-claude-override", action="store_true", help="do not set Claude user-only invocation policy")
    args = parser.parse_args()
    project = Path(args.project).expanduser().resolve()
    hosts = sorted(HOSTS) if args.host in {"all", "both"} else [resolve_host(args.host)]
    installed = []
    for host in hosts:
        installed.append((host, install_one(host, args.scope, project, args.force, args.symlink)))
    for host in hosts:
        entry = HOSTS[host]
        if entry.get("settings_writer") != "claude_override" or args.no_claude_override:
            continue
        rel = str(entry["user_settings"] if args.scope == "user" else entry["project_settings"])
        settings = (Path.home() / rel) if args.scope == "user" else (project / rel)
        update_claude_override(settings)
        print(f"{host} explicit-only override: {settings}")
    source_hash = digest_tree(SOURCE)
    print(f"Canonical skill tree SHA-256: {source_hash}")
    for host, path in installed:
        print(f"Installed identical skill for {host}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
