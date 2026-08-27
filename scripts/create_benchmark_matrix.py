#!/usr/bin/env python3
"""Create a matched live benchmark configuration for versions or external tools."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def parse_condition(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("condition must be ID=COMMAND")
    ident, command = value.split("=", 1)
    ident, command = ident.strip(), command.strip()
    if not ident or not command:
        raise argparse.ArgumentTypeError("condition ID and command must be non-empty")
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]*", ident):
        raise argparse.ArgumentTypeError(
            "condition ID must contain lowercase letters, digits, dots, and hyphens"
        )
    return ident, command


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--condition", action="append", type=parse_condition, required=True,
                        help="repeatable ID=TEAM_S_COMMAND; quote the whole value")
    parser.add_argument("--user-adapter", required=True)
    parser.add_argument("--evaluator-adapter", required=True)
    parser.add_argument("--model-id", required=True, help="exact shared model ID")
    parser.add_argument("--host-version", required=True)
    parser.add_argument("--capabilities", default="elicitation,campaign-compilation")
    parser.add_argument("--output", required=True)
    parser.add_argument("--description", default="Matched live ResCamp/external-system comparison")
    args = parser.parse_args()

    identifiers = [ident for ident, _ in args.condition]
    if len(identifiers) != len(set(identifiers)):
        raise SystemExit("Condition IDs must be unique")
    capabilities = [item.strip() for item in args.capabilities.split(",") if item.strip()]
    conditions = []
    for ident, command in args.condition:
        conditions.append({
            "id": ident,
            "adapter": "external-command",
            "command": command,
            "user_adapter": args.user_adapter,
            "evaluator_adapter": args.evaluator_adapter,
            "model_id": args.model_id,
            "host_version": args.host_version,
            # Replace this with the exact 40-character commit, or `none` only when
            # the condition genuinely has no skill. The harness otherwise downgrades
            # the run to unmatched evidence even if every control is marked true.
            "skill_commit": "record-exact-commit-or-none",
            "capabilities": capabilities,
        })
    payload = {
        "description": args.description,
        # These are operator declarations consumed by benchmark.load_config. Start
        # fail-closed; set a value true only after that control is actually in place.
        "matched_controls": {
            "same_model": False,
            "same_tools_permissions_corpus": False,
            "same_context_time_token_retry_budget": False,
            "fresh_sessions": False,
            "blinded_evaluation": False,
        },
        "conditions": conditions,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
