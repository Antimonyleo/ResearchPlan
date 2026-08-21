#!/usr/bin/env python3
"""Refresh comparable GitHub repository metadata without installing third-party code."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def github_slug(url: str) -> str | None:
    prefix = "https://github.com/"
    if not url.startswith(prefix):
        return None
    value = url[len(prefix):].strip("/")
    parts = value.split("/")
    return "/".join(parts[:2]) if len(parts) >= 2 else None


def get_json(url: str, token: str | None) -> dict:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "rescamp-repository-audit/0.9.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="benchmark/comparable_tools.json")
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    source = Path(args.manifest)
    payload = json.loads(source.read_text(encoding="utf-8"))
    token = os.environ.get("GITHUB_TOKEN")
    failures = []
    for system in payload.get("systems", []):
        slug = github_slug(str(system.get("repository", "")))
        if not slug:
            continue
        try:
            repo = get_json(f"https://api.github.com/repos/{slug}", token)
            commit = get_json(f"https://api.github.com/repos/{slug}/commits/{repo['default_branch']}", token)
            system["repository_snapshot"] = {
                "full_name": repo.get("full_name"),
                "default_branch": repo.get("default_branch"),
                "archived": repo.get("archived"),
                "pushed_at": repo.get("pushed_at"),
                "stars": repo.get("stargazers_count"),
                "license_spdx": (repo.get("license") or {}).get("spdx_id"),
                "commit": commit.get("sha"),
                "commit_date": ((commit.get("commit") or {}).get("committer") or {}).get("date"),
            }
        except (HTTPError, URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
            failures.append({"system": system.get("id"), "error": str(exc)})
    payload["metadata_refreshed_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    payload["metadata_failures"] = failures
    destination = Path(args.output) if args.output else source
    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(destination), "failures": failures}, indent=2))
    if failures and args.strict:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
