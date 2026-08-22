from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from common import ROOT, add_passing_reviews, complete_state, engine


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
                snapshot["outputs"]["last_rendered_digest"], engine.content_digest(snapshot)
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
