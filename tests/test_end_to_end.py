from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from common import ROOT, add_passing_pilot, add_passing_reviews, complete_state, engine


ENGINE = ROOT / "rescamp/scripts/rescamp.py"


def run_cli(*args: object, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, *(str(arg) for arg in args)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if check and result.returncode:
        raise AssertionError(
            f"command failed ({result.returncode}): {' '.join(str(arg) for arg in args)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


class EndToEndTests(unittest.TestCase):
    def finalized_campaign(self, root: Path, ident: str) -> Path:
        campaign_dir = Path(run_cli(
            ENGINE, "init", "--goal", f"Audit integrity {ident}",
            "--root", root, "--id", ident,
        ).stdout.strip())
        engine.save_state(campaign_dir, add_passing_reviews(complete_state()))
        result = json.loads(run_cli(ENGINE, "finalize", campaign_dir).stdout)
        self.assertEqual(result["status"], "EXECUTION-READY")
        return campaign_dir

    def test_finalize_and_audit_through_public_clis(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = self.finalized_campaign(Path(temp), "campaign")
            contract = campaign_dir / "outputs/campaign.json"
            snapshot = json.loads(contract.read_text(encoding="utf-8"))
            self.assertEqual(snapshot["status"], "execution-ready")
            self.assertEqual(
                snapshot["outputs"]["last_rendered_digest"], engine.render_digest(snapshot)
            )
            self.assertEqual(snapshot["outputs"]["manifest_path"], "MANIFEST.sha256")
            self.assertNotIn("manifest", snapshot["outputs"])
            self.assertTrue(snapshot["last_validation"]["execution_ready"])

            audited = json.loads(run_cli(
                ENGINE, "audit", campaign_dir, "--strict"
            ).stdout)
            self.assertTrue(audited["ok"], audited)

    def test_audit_detects_changed_and_unexpected_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            campaign_dir = self.finalized_campaign(root, "artifact-tamper")
            target = campaign_dir / "outputs/CAMPAIGN_PROMPT.md"
            target.write_text(target.read_text(encoding="utf-8") + "\nCHANGED\n",
                              encoding="utf-8")
            tampered = json.loads(run_cli(
                ENGINE, "audit", campaign_dir, "--strict", check=False,
            ).stdout)
            self.assertIn("artifact hash mismatch: CAMPAIGN_PROMPT.md", tampered["errors"])

            clean_dir = self.finalized_campaign(root, "extra-output")
            (clean_dir / "outputs/UNTRACKED.txt").write_text("not manifested\n", encoding="utf-8")
            extra = json.loads(run_cli(
                ENGINE, "audit", clean_dir, "--strict", check=False,
            ).stdout)
            self.assertIn(
                "unexpected output artifact not recorded in state: UNTRACKED.txt",
                extra["errors"],
            )

    def test_audit_rejects_symlinked_and_non_file_manifest_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            campaign_dir = self.finalized_campaign(root, "symlink-output")
            target = campaign_dir / "outputs/KICKOFF.md"
            outside = root / "outside.md"
            outside.write_bytes(target.read_bytes())
            target.unlink()
            target.symlink_to(outside)

            result = run_cli(ENGINE, "audit", campaign_dir, "--strict", check=False)

            self.assertEqual(result.returncode, 5)
            payload = json.loads(result.stdout)
            self.assertIn(
                "manifest artifact must be a regular file inside outputs: KICKOFF.md",
                payload["errors"],
            )

    def test_strict_audit_does_not_accept_a_forced_draft_as_ready(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = Path(temp) / "draft"
            for rel in ("state", "working", "outputs", "artifacts"):
                (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
            state = add_passing_reviews(complete_state())
            engine.save_state(campaign_dir, state)
            engine.render_outputs(campaign_dir, state, force_draft=True)

            result = run_cli(ENGINE, "audit", campaign_dir, "--strict", check=False)
            payload = json.loads(result.stdout)

            self.assertEqual(result.returncode, 5)
            self.assertTrue(payload["integrity_ok"])
            self.assertFalse(payload["ok"])
            self.assertIn("strict audit requires", payload["errors"][0])

    def test_failed_render_preserves_the_previous_complete_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = self.finalized_campaign(Path(temp), "transactional-render")
            out_dir = campaign_dir / "outputs"
            before = {
                path.name: path.read_bytes() for path in out_dir.iterdir() if path.is_file()
            }
            state_before = (campaign_dir / engine.STATE_REL).read_bytes()
            state = engine.load_state(campaign_dir)
            original = engine.atomic_write
            staged_writes = 0

            def fail_second_staged_write(path, content):
                nonlocal staged_writes
                if ".outputs.staged-" in str(path):
                    staged_writes += 1
                    if staged_writes == 2:
                        raise OSError("injected render failure")
                return original(path, content)

            with mock.patch.object(engine, "atomic_write", side_effect=fail_second_staged_write):
                with self.assertRaisesRegex(OSError, "injected render failure"):
                    engine.render_outputs(campaign_dir, state)

            after = {
                path.name: path.read_bytes() for path in out_dir.iterdir() if path.is_file()
            }
            self.assertEqual(after, before)
            self.assertEqual((campaign_dir / engine.STATE_REL).read_bytes(), state_before)
            self.assertFalse(any(
                path.name.startswith(".outputs.staged-")
                for path in campaign_dir.iterdir()
            ))

    def test_state_commit_failure_restores_previous_output_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = self.finalized_campaign(Path(temp), "rollback-render")
            out_dir = campaign_dir / "outputs"
            bundle_before = {
                path.name: path.read_bytes() for path in out_dir.iterdir() if path.is_file()
            }
            state_before = (campaign_dir / engine.STATE_REL).read_bytes()
            state = engine.load_state(campaign_dir)

            with mock.patch.object(
                engine, "save_state", side_effect=SystemExit("injected stale writer")
            ):
                with self.assertRaisesRegex(SystemExit, "injected stale writer"):
                    engine.render_outputs(campaign_dir, state)

            bundle_after = {
                path.name: path.read_bytes() for path in out_dir.iterdir() if path.is_file()
            }
            self.assertEqual(bundle_after, bundle_before)
            self.assertEqual((campaign_dir / engine.STATE_REL).read_bytes(), state_before)

    def test_audit_rejects_symlinked_outputs_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            campaign_dir = self.finalized_campaign(root, "symlinked-output-dir")
            real_outputs = root / "external-outputs"
            (campaign_dir / "outputs").rename(real_outputs)
            (campaign_dir / "outputs").symlink_to(real_outputs, target_is_directory=True)

            result = run_cli(ENGINE, "audit", campaign_dir, "--strict", check=False)
            payload = json.loads(result.stdout)

            self.assertEqual(result.returncode, 5)
            self.assertIn(
                "outputs must be a real directory inside the campaign, not a symlink",
                payload["errors"],
            )

    def test_audit_rejects_symlinked_entries_inside_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            campaign_dir = self.finalized_campaign(root, "nested-output-symlink")
            outside = root / "outside"
            outside.mkdir()
            (outside / "private.txt").write_text("private", encoding="utf-8")
            (campaign_dir / "outputs/private-dir").symlink_to(outside, target_is_directory=True)

            result = run_cli(ENGINE, "audit", campaign_dir, "--strict", check=False)
            payload = json.loads(result.stdout)

            self.assertEqual(result.returncode, 5)
            self.assertIn("outputs contains a symlink entry: private-dir", payload["errors"])

    def test_audit_rejects_manifest_directory_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = self.finalized_campaign(Path(temp), "manifest-directory")
            manifest = campaign_dir / "outputs/MANIFEST.sha256"
            manifest.unlink()
            manifest.mkdir()

            result = run_cli(ENGINE, "audit", campaign_dir, "--strict", check=False)
            payload = json.loads(result.stdout)

            self.assertEqual(result.returncode, 5)
            self.assertNotIn("Traceback", result.stderr)
            self.assertIn(
                "MANIFEST.sha256 must be a regular file inside outputs", payload["errors"]
            )

    def test_pilot_evidence_change_stales_the_rendered_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = Path(temp) / "pilot-tamper"
            for rel in ("state", "working", "outputs", "artifacts"):
                (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
            state = complete_state()
            state["assurance"]["pilot_required"] = True
            add_passing_pilot(state)
            add_passing_reviews(state)
            engine.save_state(campaign_dir, state)
            engine.render_outputs(campaign_dir, state)
            changed = engine.load_state(campaign_dir)
            changed["assurance"]["pilot"]["authorized_by"] = "different-authority"
            engine.save_state(campaign_dir, changed)

            audit = run_cli(ENGINE, "audit", campaign_dir, "--strict", check=False)
            payload = json.loads(audit.stdout)

            self.assertEqual(audit.returncode, 5)
            self.assertTrue(any(
                item["code"] == "outputs.stale"
                for item in payload["validation"]["errors"]
            ))

    def test_empty_operational_fields_fail_closed(self):
        state = complete_state()
        state["campaign"]["mission"]["scope"] = "  "
        state["campaign"]["methods"][0]["inputs"] = []
        state["campaign"]["stages"][0]["activities"] = []
        state["campaign"]["claims"][0]["statement"] = True
        result = engine.validate_state(state, include_reviews=False)
        codes = [item["code"] for item in result["errors"]]
        self.assertIn("mission.missing", codes)
        self.assertIn("method.incomplete", codes)
        self.assertIn("stage.incomplete", codes)
        self.assertIn("claim.incomplete", codes)

        visible_boolean = complete_state()
        visible_boolean["campaign"]["tools"][0]["production"] = False
        prompt = engine.render_campaign_prompt(visible_boolean, "DRAFT")
        self.assertIn("**Production use:** no", prompt)

    def test_external_actions_require_exact_structured_approvals(self):
        state = complete_state()
        state["campaign"]["ethics_rights_safety"]["external_actions"] = [{
            "id": "publish-result", "description": "Publish the accepted result",
            "approval_id": "publication-signoff",
        }]
        state["campaign"]["resources_dispatch"]["approvals"] = [{
            "id": "publication-signoff", "description": "Campaign owner approval",
        }]
        state["campaign"]["ethics_rights_safety"]["human_approval_points"] = []
        self.assertTrue(engine.validate_state(state, include_reviews=False)["valid"])

        malformed = complete_state()
        malformed["campaign"]["ethics_rights_safety"]["external_actions"] = [{
            "id": "publish-result", "approval_id": "publication-signoff",
        }]
        malformed["campaign"]["resources_dispatch"]["approvals"] = ["probably approved"]
        result = engine.validate_state(malformed, include_reviews=False)
        self.assertTrue(any(item["code"] == "approval.malformed" for item in result["errors"]))


if __name__ == "__main__":
    unittest.main()
