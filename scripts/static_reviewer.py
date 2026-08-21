#!/usr/bin/env python3
"""Static structural checks over one ResCamp release concern.

This is NOT a review and produces no independent judgement. Every check below is a
substring test, a file-existence test, a regex extraction, or a count threshold applied
to files in the repository tree. It runs in its own process only so that a crash in one
check group cannot take down the others; process isolation is not independence.

Output: one JSON object with `check_id`, `method`, `independence`, an explicit `checks`
list recording each assertion and its observed value, and `findings` derived from the
failing assertions. Exit code 0 when no critical/major finding was produced, else 2.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

ARCHETYPES = {
    "experimental", "computational", "observational", "qualitative-field",
    "humanities-interpretive", "conceptual-normative", "evidence-synthesis",
    "policy-program-evaluation", "design-engineering", "creative-practice", "mixed-methods",
}

METHOD = "static-substring-and-structure-check"
INDEPENDENCE = "none"
DISCLAIMER = (
    "Automated static assertions over repository files: substring presence, file existence, "
    "regex extraction, and counts. No reviewer, no model, and no independent assessment; "
    "these are regression guards, not evidence of quality."
)

CHECK_IDS = ["architecture", "generalization", "usability", "quality-workflow", "packaging-integrity"]


class CheckLog:
    """Records every assertion actually performed, with its observed value."""

    def __init__(self) -> None:
        self.checks: list[dict[str, Any]] = []
        self.findings: list[dict[str, str]] = []

    def assertion(self, name: str, kind: str, target: str, expected: str, observed: str, passed: bool,
                  severity: str = "major", message: str = "") -> bool:
        self.checks.append({
            "check": name, "kind": kind, "target": target,
            "expected": expected, "observed": observed,
            "result": "pass" if passed else "fail",
        })
        if not passed:
            self.findings.append({
                "severity": severity, "message": message or f"{name}: expected {expected}, observed {observed}",
                "target": target, "failed_check": name,
            })
        return passed

    def measurement(self, name: str, target: str, observed: str) -> None:
        """A value read off the tree with no pass/fail threshold attached to it."""
        self.checks.append({
            "check": name, "kind": "measurement", "target": target,
            "expected": "not gated", "observed": observed, "result": "observed",
        })


def substring_set(log: CheckLog, name: str, target: str, text: str, required: list[str],
                  severity: str, message_prefix: str) -> None:
    missing = [item for item in required if item not in text]
    log.assertion(
        name, "substring-presence", target,
        f"all {len(required)} literal strings present",
        f"{len(required) - len(missing)}/{len(required)} present"
        + (f"; missing: {missing}" if missing else ""),
        not missing, severity, f"{message_prefix}: {missing}" if missing else "",
    )


def run_checks(check_id: str, root: Path) -> CheckLog:
    log = CheckLog()
    skill_path = root / "rescamp/SKILL.md"
    skill = skill_path.read_text(encoding="utf-8")

    if check_id == "architecture":
        required = [
            "Campaign constitution", "Mission and deliverables", "Object and evidence dossier",
            "Inquiry logic", "Method portfolio", "Tools and canaries", "Frozen evaluation instrument",
            "Staged funnel", "Resources and dispatch", "Delegation", "Durable operations",
            "Ethics, safety, rights, and external actions", "Reporting and claim discipline",
            "Transactional closeout", "Independent challenge", "Kickoff",
        ]
        substring_set(log, "campaign_architecture_sections", "rescamp/SKILL.md", skill, required,
                      "critical", "missing campaign architecture sections")
        log.measurement("skill_bytes", "rescamp/SKILL.md", str(len(skill.encode("utf-8"))))
        for token in ("digest", "automatically", "delegation", "closeout"):
            log.measurement(f"literal_occurrences[{token}]", "rescamp/SKILL.md",
                            str(skill.lower().count(token)))

    elif check_id == "generalization":
        scenario_dir = root / "benchmark/scenarios/public"
        scenarios = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(scenario_dir.glob("*.json"))]
        covered = {item for scenario in scenarios for item in scenario["archetypes"]}
        domains = {scenario["domain"] for scenario in scenarios}
        log.measurement("public_scenario_files", "benchmark/scenarios/public", str(len(scenarios)))
        log.assertion(
            "archetype_coverage", "set-equality", "benchmark/scenarios/public",
            f"{len(ARCHETYPES)} archetypes covered",
            f"{len(covered)} covered; uncovered: {sorted(ARCHETYPES - covered)}; unexpected: {sorted(covered - ARCHETYPES)}",
            covered == ARCHETYPES, "critical",
            f"archetype coverage mismatch: {sorted(ARCHETYPES - covered)}",
        )
        log.assertion(
            "distinct_domain_count", "count-threshold", "benchmark/scenarios/public",
            ">= 15 distinct domains", f"{len(domains)} distinct domains",
            len(domains) >= 15, "major", f"only {len(domains)} distinct domains",
        )
        overlay_path = root / "benchmark/rubrics/archetype_overlays.json"
        overlay = json.loads(overlay_path.read_text(encoding="utf-8"))["overlays"]
        log.assertion(
            "archetype_overlay_keys", "set-equality", "benchmark/rubrics/archetype_overlays.json",
            f"overlay keys equal the {len(ARCHETYPES)} archetypes",
            f"{len(overlay)} keys; missing: {sorted(ARCHETYPES - set(overlay))}; extra: {sorted(set(overlay) - ARCHETYPES)}",
            set(overlay) == ARCHETYPES, "major", "archetype rubric overlays are incomplete",
        )
        substring_set(log, "non_experimental_vocabulary_safeguard", "rescamp/SKILL.md", skill,
                      ["Do not force experimental vocabulary"], "major",
                      "non-experimental vocabulary safeguard missing")

    elif check_id == "usability":
        lines = skill.count("\n") + 1
        words = len(re.findall(r"\S+", skill))
        estimated_tokens = int(words * 1.55)
        log.assertion(
            "context_budget", "count-threshold", "rescamp/SKILL.md",
            "<= 500 lines and <= 5000 estimated tokens (words * 1.55)",
            f"{lines} lines, {words} words, {estimated_tokens} estimated tokens",
            not (lines > 500 or estimated_tokens > 5000), "critical", "skill exceeds context budget",
        )
        for phrase in ("Ask one question per turn", "Soft stop", "Hard stop",
                       "Question budgets are safeguards, not targets",
                       "Never ask again for information already supplied"):
            log.assertion(
                f"usability_rule[{phrase}]", "substring-presence", "rescamp/SKILL.md",
                "literal string present", "present" if phrase in skill else "absent",
                phrase in skill, "major", f"missing usability rule: {phrase}",
            )
        hard_values = [int(value) for value in re.findall(r"\| (?:scoped|standard|high-assurance) \|[^\n]*\| (\d+) \|", skill)]
        log.assertion(
            "hard_interview_limit", "regex-extraction", "rescamp/SKILL.md",
            "every hard stop value in the profile table <= 18",
            f"extracted {hard_values or 'no'} value(s)"
            + (f"; maximum {max(hard_values)}" if hard_values else ""),
            not (hard_values and max(hard_values) > 18), "critical", "hard interview limit exceeds 18",
        )

    elif check_id == "quality-workflow":
        required_paths = [
            "rescamp/scripts/rescamp.py", "rescamp/scripts/workflow.py", "rescamp/scripts/benchmark.py",
            "benchmark/prompts/team_u.md", "benchmark/prompts/team_s.md", "benchmark/prompts/team_e.md",
        ]
        for rel in required_paths:
            exists = (root / rel).is_file()
            log.assertion(
                f"file_exists[{rel}]", "file-existence", rel, "file exists",
                "exists" if exists else "missing", exists, "critical", f"missing {rel}",
            )
        auto = "automatically" in skill.lower()
        manual = "manual `benchmark`" in skill
        log.assertion(
            "automatic_vs_manual_qa_wording", "substring-presence", "rescamp/SKILL.md",
            "'automatically' (any case) and 'manual `benchmark`' both present",
            f"'automatically': {'present' if auto else 'absent'}; 'manual `benchmark`': {'present' if manual else 'absent'}",
            auto and manual, "major",
            "automatic current-plan QA and manual comparative benchmark are not clearly separated",
        )
        workflow_rel = "rescamp/scripts/workflow.py"
        workflow = (root / workflow_rel).read_text(encoding="utf-8")
        for command in ("claim", "heartbeat", "complete", "approve", "reconcile", "audit"):
            token = f'add_parser("{command}")'
            found = token in workflow
            log.assertion(
                f"workflow_subcommand[{command}]", "substring-presence", workflow_rel,
                f"{token} present", "present" if found else "absent",
                found, "major", f"workflow command missing: {command}",
            )

    elif check_id == "packaging-integrity":
        skills = sorted(root.rglob("SKILL.md"))
        relative = [path.relative_to(root).as_posix() for path in skills]
        log.assertion(
            "canonical_skill_file", "file-inventory", "repository tree",
            "exactly ['rescamp/SKILL.md']", str(relative),
            skills == [skill_path], "critical",
            f"expected one canonical SKILL.md, found {len(skills)}",
        )
        installer_rel = "scripts/install.py"
        # Check the property, not a source line. The previous version grepped for the
        # literal `hosts = ["claude", "codex"]`, which pinned an implementation detail
        # and broke the moment the installer became table-driven.
        spec = importlib.util.spec_from_file_location("rescamp_installer", root / installer_rel)
        installer_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer_mod)
        expected_hosts = {"claude-code", "codex"}
        registered = set(getattr(installer_mod, "HOSTS", {}))
        verifies = callable(getattr(installer_mod, "digest_tree", None))
        log.assertion(
            "installer_verifies_host_trees", "structural-check", installer_rel,
            f"digest_tree callable and HOSTS covers {sorted(expected_hosts)}",
            f"digest_tree={'yes' if verifies else 'no'}; HOSTS={sorted(registered)}",
            verifies and expected_hosts <= registered,
            "major", "installer does not verify identical host trees",
        )
        for host_id in sorted(registered):
            entry = installer_mod.HOSTS[host_id]
            log.assertion(
                f"host_paths_declared:{host_id}", "structural-check", installer_rel,
                "user_path and project_path declared",
                f"user={entry.get('user_path')}; project={entry.get('project_path')}",
                bool(entry.get("user_path") and entry.get("project_path")),
                "major", f"host {host_id} has incomplete install paths",
            )

    else:
        raise ValueError(check_id)

    return log


def run_check_group(check_id: str, root: Path) -> dict[str, Any]:
    log = run_checks(check_id, root)
    executed = [item for item in log.checks if item["result"] != "observed"]
    failed = [item for item in executed if item["result"] == "fail"]
    blocking = any(item["severity"] in {"critical", "major"} for item in log.findings)
    return {
        "check_id": check_id,
        "method": METHOD,
        "independence": INDEPENDENCE,
        "execution": "separate process (isolation only; not an independent assessment)",
        "not_a_review": DISCLAIMER,
        "status": "fail" if blocking else "pass",
        "assertions_run": len(executed),
        "assertions_failed": len(failed),
        "checks": log.checks,
        "findings": log.findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, choices=CHECK_IDS,
                        help="check group to run (flag name kept for the release script's CLI contract)")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    result = run_check_group(args.role, Path(args.root).resolve())
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
