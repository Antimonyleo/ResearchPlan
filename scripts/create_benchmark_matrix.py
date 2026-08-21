#!/usr/bin/env python3
"""Create a matched live benchmark configuration for versions or external tools."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_condition(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("condition must be ID=COMMAND")
    ident, command = value.split("=", 1)
    ident, command = ident.strip(), command.strip()
    if not ident or not command:
        raise argparse.ArgumentTypeError("condition ID and command must be non-empty")
    return ident, command


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--condition", action="append", type=parse_condition, required=True,
                        help="repeatable ID=TEAM_S_COMMAND; quote the whole value")
    parser.add_argument("--user-adapter", required=True)
    parser.add_argument("--evaluator-adapter", required=True)
    parser.add_argument("--model-id", required=True, help="exact shared model ID or 'varies-record-per-run'")
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
            "skill_commit": "record-exact-commit-or-none",
            "capabilities": capabilities,
        })
    payload = {
        "description": args.description,
        # Unverified operator declarations. The harness does not read or check these,
        # so they start as "unverified" rather than asserting controls on the
        # operator's behalf. Set each to true only after you have actually matched it,
        # and note that blinding is currently imperfect: a Team S that writes an
        # artifact leaks its condition to the evaluator through the artifact path.
        "matched_controls_declared_by_operator": {
            "same_model": "unverified",
            "same_tools_permissions_corpus": "unverified",
            "same_context_time_token_retry_budget": "unverified",
            "fresh_sessions": "unverified",
            "blinded_evaluation": "unverified",
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
