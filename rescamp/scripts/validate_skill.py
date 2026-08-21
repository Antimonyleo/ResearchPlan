#!/usr/bin/env python3
"""Self-check the canonical ResCamp skill bundle using only the Python standard library."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md lacks YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("SKILL.md frontmatter is not closed")
    result: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if line and not line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip('"')
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=str(Path(__file__).resolve().parent.parent))
    args = parser.parse_args()
    root = Path(args.path).resolve()
    errors: list[str] = []
    warnings: list[str] = []
    skill = root / "SKILL.md"
    if not skill.is_file():
        errors.append("missing SKILL.md")
        text = ""
    else:
        text = skill.read_text(encoding="utf-8")
        try:
            meta = parse_frontmatter(text)
            if meta.get("name") != "rescamp":
                errors.append("frontmatter name must be rescamp")
            if not meta.get("description"):
                errors.append("frontmatter description is missing")
        except ValueError as exc:
            errors.append(str(exc))
        lines = text.count("\n") + 1
        words = len(re.findall(r"\S+", text))
        conservative_tokens = int(words * 1.55)
        if lines > 500:
            errors.append(f"SKILL.md exceeds 500 lines ({lines})")
        if conservative_tokens > 5000:
            errors.append(f"SKILL.md exceeds conservative 5000-token budget ({conservative_tokens})")
    for rel in ("references", "assets", "scripts"):
        if not (root / rel).is_dir():
            errors.append(f"missing {rel}/")
    for path in sorted((root / "assets").glob("*.json")) if (root / "assets").is_dir() else []:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"invalid JSON {path.name}: {exc}")
    referenced = set(re.findall(r"`((?:references|assets|scripts)/[^`]+)`", text))
    for rel in sorted(referenced):
        # Commands may append arguments after a script path.
        candidate = rel.split()[0].rstrip(".,;:")
        if not (root / candidate).exists():
            errors.append(f"SKILL.md references missing path: {candidate}")
    py_files = list((root / "scripts").glob("*.py")) if (root / "scripts").is_dir() else []
    for path in py_files:
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as exc:
            errors.append(f"syntax error {path.name}:{exc.lineno}: {exc.msg}")
    result = {
        "valid": not errors,
        "skill_dir": str(root),
        "skill_md_lines": text.count("\n") + 1 if text else 0,
        "skill_md_words": len(re.findall(r"\S+", text)),
        "conservative_token_estimate": int(len(re.findall(r"\S+", text)) * 1.55),
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
