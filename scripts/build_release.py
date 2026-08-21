#!/usr/bin/env python3
"""Validate and build deterministic ResCamp 0.8.5 release archives."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Iterable

VERSION = "0.8.5"
TOP = f"rescamp-v{VERSION}"
FIXED_ZIP_TIME = (2026, 8, 20, 0, 0, 0)


def excluded(relative: Path) -> bool:
    parts = set(relative.parts)
    if parts & {".git", "__pycache__", "dist", ".dist"}:
        return True
    if len(relative.parts) >= 2 and relative.parts[0:2] == ("benchmark", "runs"):
        return True
    if relative.suffix in {".pyc", ".pyo"} or relative.name == ".DS_Store":
        return True
    return False


def copy_source(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.rglob("*")):
        rel = path.relative_to(source)
        if excluded(rel):
            continue
        target = destination / rel
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def zip_paths(output: Path, roots: Iterable[tuple[Path, str]]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for root, prefix in roots:
            for path in sorted(p for p in root.rglob("*") if p.is_file() and not excluded(p.relative_to(root))):
                arcname = (Path(prefix) / path.relative_to(root)).as_posix()
                info = zipfile.ZipInfo(arcname, FIXED_ZIP_TIME)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = ((0o755 if os.access(path, os.X_OK) else 0o644) & 0xFFFF) << 16
                archive.writestr(info, path.read_bytes())
    with zipfile.ZipFile(output) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"corrupt archive member {bad} in {output}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and not excluded(p.relative_to(root))):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def parse_json_stdout(check: dict, key: str) -> dict:
    text = check["checks"][key]["stdout"].strip()
    return json.loads(text) if text else {}


def release_report(check: dict) -> str:
    skill = parse_json_stdout(check, "skill_self_check")
    scenario = parse_json_stdout(check, "scenario_validation")
    tests_text = check["checks"]["unit_tests"]["stderr"] + check["checks"]["unit_tests"]["stdout"]
    match = re.search(r"Ran (\d+) tests", tests_text)
    test_count = int(match.group(1)) if match else None
    static_runs = check["checks"]["process_isolated_static_reviewers"]
    static_verdicts = {}
    for role, run in static_runs.items():
        try:
            payload = json.loads(run["stdout"])
            static_verdicts[role] = payload.get("status") or payload.get("verdict") or "unreadable"
        except Exception:
            static_verdicts[role] = "unreadable"
    fixture = check["checks"].get("full_fixture_summary", {})
    process = check["checks"].get("process_fixture_summary", {})
    fixture_lines = []
    for condition, values in fixture.get("conditions", {}).items():
        fixture_lines.append(f"- `{condition}`: n={values['n']}, mean={values['score_mean_ci95'][0]}, turns={values['mean_interview_turns']}, critical-defect rate={values['critical_defect_rate']}")
    process_lines = []
    for condition, values in process.get("conditions", {}).items():
        process_lines.append(f"- `{condition}`: n={values['n']}, mean={values['score_mean_ci95'][0]}, turns={values['mean_interview_turns']}, critical-defect rate={values['critical_defect_rate']}")
    return f"""# ResCamp {VERSION} release and QA report

## Release decision

**Deterministic release status:** {'PASS' if check['valid'] else 'FAIL'}

ResCamp {VERSION} uses one canonical `rescamp/SKILL.md` and one portable supporting tree. Claude Code and Codex installation differs only by destination and invocation syntax. The installer verified byte-identical source, Claude, and Codex tree digests.

## Scope of this evidence

The checks establish packaging, state-machine, validator, benchmark-harness, workflow-queue, information-boundary, and regression behavior. They do **not** establish that a live model using ResCamp is superior to another agent. No authenticated Claude or Codex subagent runtime was available during release construction; process-isolated deterministic Team U/S/E fixtures and static reviewer roles are labeled accordingly.

## Results

- Unit/generalization/workflow tests: **{test_count} passed**.
- Public benchmark scenarios: **{scenario.get('count')}** across **{len(scenario.get('domains', []))} domains** and **{len(scenario.get('archetypes', []))} research archetypes**.
- Canonical `SKILL.md`: **{skill.get('skill_md_lines')} lines**, **{skill.get('skill_md_words')} words**, conservative estimate **{skill.get('conservative_token_estimate')} tokens**.
- Canonical skill tree SHA-256: `{check.get('skill_tree_sha256')}`.
- Static structural checks (substring, existence, and count assertions; not reviews and not independent): {', '.join(f'`{role}`={verdict}' for role, verdict in sorted(static_verdicts.items()))}.
- Release errors: **{len(check.get('errors', []))}**; warnings: **{len(check.get('warnings', []))}**.

### Full 18-scenario deterministic harness smoke

These fixture scores test the harness and deliberately encoded policies; they are not model-performance estimates.

{chr(10).join(fixture_lines) or '- Not run.'}

### Process-isolated Team U/S/E smoke

The selected cases span experimental/computational, humanities, and qualitative work and include approval blockers. The roles ran in separate OS processes, but they were deterministic fixtures rather than independent AI agents.

{chr(10).join(process_lines) or '- Not run.'}

## Design findings

1. **One canonical skill:** the repository contains exactly one `SKILL.md`; both hosts receive the same bytes.
2. **Proportionate interviewing:** one question per turn by default; typical 3–5, 4–8, or 6–12 by assurance profile; hard limits 8, 12, and 18 require explicit extension authority.
3. **Current-plan QA, and who does what:** interview completion automatically freezes a digest, runs deterministic checks, writes proportional reviewer *input* packets, and classifies findings. Executing those reviewers and repairing defects are the model's work, not the script's; `finalize` is the fail-closed gate that refuses an execution-ready bundle without ingested passing reviews bound to the current digest. Reviewer independence is self-attested and recorded for audit, never proven.
4. **Manual comparative benchmark:** version, baseline, model, or external-tool comparisons are deliberate commands with matched Team U/S/E boundaries.
5. **Discipline-neutral research logic:** experimental controls and predictions are translated to rival interpretations, negative cases, objections, source criticism, counterfactuals, or adjudication rules where appropriate.
6. **Optional continuous workflow:** the SQLite queue persists work units, leases, approvals, retries, events, and artifact hashes but never launches models, grants approvals, or substitutes for a real scheduler.
7. **Anthropic campaign architecture translated, not preserved wholesale:** the shared constitution, exact mission, dossier, method diversity, tool qualification, frozen evaluation, staged gates, resource governor, bounded delegation, claim discipline, closeout, and kickoff are translations of the released binder-design campaign. Durable recovery and the challenge stage are extrapolations. The inquiry/prediction/reconciliation loop derives from the Little Scientist paper, not the binder campaign. The paper's external adjudicator — two independent contract labs — has no equivalent here; agent review checks internal coherence only. See `docs/PAPER_ANTHROPIC_BINDER.md` and `docs/DESIGN_BASIS.md`.

## Remaining validation required for strong behavioral claims

Run the preregistered live matrix using fresh, separate Team U, Team S, and Team E sessions; private holdouts; exact model/host/tool commits; matched budgets; multiple stochastic replicates; blinded domain experts; and downstream execution outcomes. Public fixtures and self-authored rubrics cannot establish external validity.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    out = Path(args.output_dir).resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    evidence = out / "evidence"
    check_path = out / f"rescamp-v{VERSION}-RELEASE_CHECK.json"

    proc = subprocess.run([
        sys.executable, "scripts/validate_release.py", "--root", str(root),
        "--output", str(check_path), "--evidence-dir", str(evidence),
    ], cwd=root, text=True, capture_output=True, timeout=300, check=False)
    (out / "validation.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (out / "validation.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        raise SystemExit(f"release validation failed; inspect {check_path}")
    check = json.loads(check_path.read_text(encoding="utf-8"))
    if not check.get("valid"):
        raise SystemExit("release validation reported invalid")

    report_text = release_report(check)
    report_path = out / f"rescamp-v{VERSION}-RELEASE_REPORT.md"
    report_path.write_text(report_text, encoding="utf-8")
    (evidence / "RELEASE_REPORT.md").write_text(report_text, encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix="rescamp-build-") as temp_str:
        temp = Path(temp_str)
        stage = temp / TOP
        copy_source(root, stage)
        qa = stage / "qa"
        qa.mkdir(exist_ok=True)
        shutil.copy2(check_path, qa / "RELEASE_CHECK.json")
        shutil.copy2(report_path, stage / "docs/RELEASE_REPORT.md")
        for source_name, target_name in (
            ("full_fixture_summary.json", "FIXTURE_SUMMARY.json"),
            ("static_reviewer_runs.json", "STATIC_REVIEWERS.json"),
        ):
            source = evidence / source_name
            if source.exists():
                shutil.copy2(source, qa / target_name)
        process_summary = evidence / "process_isolated_three_team_runs/summary.json"
        if process_summary.exists():
            shutil.copy2(process_summary, qa / "PROCESS_THREE_TEAM_SUMMARY.json")
        (qa / "README.md").write_text(
            "# QA evidence\n\nMachine-readable release check and smoke-test summaries. Deterministic fixtures verify the harness; they are not live-model performance evidence.\n",
            encoding="utf-8",
        )

        github_zip = out / f"rescamp-github-v{VERSION}.zip"
        skill_zip = out / f"rescamp-skill-v{VERSION}.zip"
        skill_file = out / f"rescamp-v{VERSION}.skill"
        evidence_zip = out / f"rescamp-v{VERSION}-EVALUATION_EVIDENCE.zip"
        zip_paths(github_zip, [(stage, TOP)])
        zip_paths(skill_zip, [(stage / "rescamp", "rescamp")])
        shutil.copy2(skill_zip, skill_file)
        evidence_root = temp / f"rescamp-v{VERSION}-evidence"
        shutil.copytree(evidence, evidence_root)
        shutil.copy2(check_path, evidence_root / "RELEASE_CHECK.json")
        shutil.copy2(report_path, evidence_root / "RELEASE_REPORT.md")
        shutil.copy2(out / "validation.stdout.txt", evidence_root / "validation.stdout.txt")
        shutil.copy2(out / "validation.stderr.txt", evidence_root / "validation.stderr.txt")
        zip_paths(evidence_zip, [(evidence_root, evidence_root.name)])

        # Extract and prove that GitHub and standalone skill packages contain identical skill bytes.
        extract_a, extract_b = temp / "extract-github", temp / "extract-skill"
        with zipfile.ZipFile(github_zip) as zf:
            zf.extractall(extract_a)
        with zipfile.ZipFile(skill_zip) as zf:
            zf.extractall(extract_b)
        github_skill_digest = tree_digest(extract_a / TOP / "rescamp")
        standalone_skill_digest = tree_digest(extract_b / "rescamp")
        source_skill_digest = tree_digest(root / "rescamp")
        if len({github_skill_digest, standalone_skill_digest, source_skill_digest}) != 1:
            raise SystemExit("skill tree mismatch across source/GitHub/standalone packages")

    primary_artifacts = [
        out / f"rescamp-github-v{VERSION}.zip",
        out / f"rescamp-skill-v{VERSION}.zip",
        out / f"rescamp-v{VERSION}.skill",
        out / f"rescamp-v{VERSION}-EVALUATION_EVIDENCE.zip",
        report_path,
        check_path,
    ]
    packaging_path = out / f"rescamp-v{VERSION}-PACKAGING_CHECK.json"
    sums_path = out / f"rescamp-v{VERSION}-SHA256SUMS.txt"
    packaging = {
        "version": VERSION,
        "valid": True,
        "source_skill_tree_sha256": source_skill_digest,
        "github_skill_tree_sha256": github_skill_digest,
        "standalone_skill_tree_sha256": standalone_skill_digest,
        "archives": {
            path.name: {"sha256": sha256(path), "bytes": path.stat().st_size}
            for path in primary_artifacts
            if path.suffix in {".zip", ".skill"}
        },
        "files": [path.name for path in primary_artifacts] + [packaging_path.name, sums_path.name],
    }
    packaging_path.write_text(json.dumps(packaging, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checksum_artifacts = primary_artifacts + [packaging_path]
    sums_path.write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in checksum_artifacts),
        encoding="utf-8",
    )
    print(json.dumps(packaging, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
