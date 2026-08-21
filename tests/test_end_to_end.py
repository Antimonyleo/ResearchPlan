from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from common import ROOT, add_passing_reviews, complete_state, engine


ENGINE = ROOT / "rescamp/scripts/rescamp.py"
WORKFLOW = ROOT / "rescamp/scripts/workflow.py"


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


def runtime_state() -> dict:
    state = complete_state()
    campaign = state["campaign"]
    campaign["runtime"].update({
        "enabled": True,
        "continuation_trigger": "An operator initializes and resumes the durable queue",
        "state_store": "workflow.sqlite3",
        "event_log": "workflow.sqlite3 events table",
        "checkpoint_policy": "Checkpoint after every queue transition",
        "liveness": "A bounded lease must be renewed before expiry",
        "recovery": "One retry, then fail closed and escalate",
        "idempotency": "Artifact hashes identify completed outputs",
    })
    campaign["resources_dispatch"].update({
        "max_concurrency": 1,
        "approvals": [{
            "id": "publication-signoff",
            "description": "Campaign owner approves the bounded external publication action",
        }],
    })
    # The fixture already declares this approval under human_approval_points. Keep one
    # canonical declaration so compiler and dispatcher see the same contract.
    campaign["ethics_rights_safety"]["human_approval_points"] = []
    campaign["ethics_rights_safety"]["external_actions"] = [{
        "id": "publish-result",
        "description": "Publish the accepted result to the named external destination",
        "approval_id": "publication-signoff",
    }]
    campaign["work_units"] = [{
        "id": "unit-1",
        "objective": "Produce and verify one bounded result artifact",
        "authoritative_inputs": ["campaign.json at its recorded content digest"],
        "permitted_actions": ["read campaign inputs", "write the declared artifact", "publish after approval"],
        "prohibited_actions": ["no undeclared external action", "no scope expansion"],
        "outputs": ["result.txt"],
        "acceptance_test": "The artifact exists and its recorded hash verifies",
        "resource_ceiling": "One worker and one agent-hour",
        "retry_policy": "No retries after a failed attempt",
        "escalation": "Return failure to the campaign lead",
        "dependency_ids": [],
        "external_action_ids": ["publish-result"],
        "approval_ids": ["publication-signoff"],
        "retry_limit": 0,
    }]
    return add_passing_reviews(state)


class EndToEndTests(unittest.TestCase):
    def finalized_campaign(self, root: Path, ident: str) -> Path:
        campaign_dir = Path(run_cli(
            ENGINE, "init", "--goal", f"Audit integrity {ident}",
            "--root", root, "--id", ident,
        ).stdout.strip())
        engine.save_state(campaign_dir, add_passing_reviews(complete_state()), "fixture.prepared")
        result = json.loads(run_cli(ENGINE, "finalize", campaign_dir).stdout)
        self.assertEqual(result["status"], "EXECUTION-READY")
        return campaign_dir

    def test_finalize_dispatch_complete_and_audit_through_public_clis(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            initialized = run_cli(
                ENGINE, "init", "--goal", "A bounded queue integration campaign",
                "--root", root, "--id", "campaign",
            )
            campaign_dir = Path(initialized.stdout.strip())
            engine.save_state(campaign_dir, runtime_state(), "fixture.prepared")

            finalized = json.loads(run_cli(ENGINE, "finalize", campaign_dir).stdout)
            self.assertEqual(finalized["status"], "EXECUTION-READY")
            contract = campaign_dir / "outputs/campaign.json"
            snapshot = json.loads(contract.read_text(encoding="utf-8"))
            self.assertEqual(snapshot["status"], "execution-ready")
            self.assertEqual(snapshot["outputs"]["last_rendered_digest"], engine.content_digest(snapshot))
            self.assertEqual(snapshot["outputs"]["manifest_path"], "MANIFEST.sha256")
            self.assertNotIn("manifest", snapshot["outputs"])
            self.assertTrue(snapshot["last_validation"]["execution_ready"])
            self.assertEqual(
                snapshot["last_validation"]["content_digest"], engine.content_digest(snapshot)
            )

            engine_audit = json.loads(
                run_cli(ENGINE, "audit", campaign_dir, "--strict").stdout
            )
            self.assertTrue(engine_audit["ok"], engine_audit)

            db = root / "workflow.sqlite3"
            initialized_queue = json.loads(
                run_cli(WORKFLOW, "init", "--campaign", contract, "--db", db).stdout
            )
            self.assertEqual(initialized_queue["work_units"], 1)
            run_cli(
                WORKFLOW, "approve", "--db", db, "--approval", "publication-signoff",
                "--by", "campaign-owner", "--evidence", "approval-record-1",
            )
            claim = json.loads(
                run_cli(WORKFLOW, "claim", "--db", db, "--worker", "worker-1").stdout
            )
            self.assertTrue(claim["claimed"])
            artifact = root / "result.txt"
            artifact.write_text("bounded result\n", encoding="utf-8")
            run_cli(
                WORKFLOW, "complete", "--db", db, "--unit", "unit-1",
                "--token", claim["lease_token"], "--artifact", artifact,
                "--acceptance-evidence", "artifact read back and matched the expected content",
            )
            queue_audit = json.loads(run_cli(WORKFLOW, "audit", "--db", db).stdout)
            self.assertTrue(queue_audit["valid"], queue_audit)

    def test_campaign_audit_detects_event_log_truncation_and_reordering(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            campaign_dir = Path(run_cli(
                ENGINE, "init", "--goal", "Event integrity", "--root", root, "--id", "campaign",
            ).stdout.strip())
            state = engine.load_state(campaign_dir)
            state["title"] = "Event integrity updated"
            engine.save_state(campaign_dir, state, "campaign.updated")
            state = engine.load_state(campaign_dir)
            state["title"] = "Event integrity updated twice"
            engine.save_state(campaign_dir, state, "campaign.updated-again")

            event_path = campaign_dir / engine.EVENTS_REL
            original = event_path.read_text(encoding="utf-8").splitlines()
            event_path.write_text("\n".join(original[:-1]) + "\n", encoding="utf-8")
            truncated = json.loads(run_cli(
                ENGINE, "audit", campaign_dir, check=False
            ).stdout)
            self.assertIn("event log anchor does not match canonical state", truncated["errors"])

            event_path.write_text("\n".join([original[0], original[2], original[1]]) + "\n", encoding="utf-8")
            reordered = json.loads(run_cli(
                ENGINE, "audit", campaign_dir, check=False
            ).stdout)
            self.assertTrue(any("event log hash chain" in item for item in reordered["errors"]))

    def test_campaign_audit_binds_output_state_and_rejects_unexpected_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            campaign_dir = self.finalized_campaign(root, "manifest-tamper")
            target = campaign_dir / "outputs/CAMPAIGN_PROMPT.md"
            target.write_text(target.read_text(encoding="utf-8") + "\nMALICIOUS\n",
                              encoding="utf-8")
            target_digest = engine.sha256_bytes(target.read_bytes())
            manifest_path = campaign_dir / "outputs/MANIFEST.sha256"
            manifest_text = "\n".join(
                f"{target_digest}  CAMPAIGN_PROMPT.md"
                if line.endswith("  CAMPAIGN_PROMPT.md") else line
                for line in manifest_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ) + "\n"
            manifest_path.write_text(manifest_text, encoding="utf-8")
            state = engine.load_state(campaign_dir)
            state["outputs"]["manifest"]["CAMPAIGN_PROMPT.md"] = target_digest
            state["outputs"]["manifest"]["MANIFEST.sha256"] = engine.sha256_bytes(
                manifest_text.encode("utf-8")
            )
            engine.write_json(campaign_dir / engine.STATE_REL, state)

            tampered = json.loads(run_cli(
                ENGINE, "audit", campaign_dir, "--strict", check=False,
            ).stdout)
            self.assertIn("canonical state does not match the final event", tampered["errors"])

            clean_dir = self.finalized_campaign(root, "extra-output")
            (clean_dir / "outputs/UNTRACKED.txt").write_text("not manifested\n", encoding="utf-8")
            extra = json.loads(run_cli(
                ENGINE, "audit", clean_dir, "--strict", check=False,
            ).stdout)
            self.assertIn(
                "unexpected output artifact not recorded in state: UNTRACKED.txt",
                extra["errors"],
            )

    def test_campaign_commands_refuse_to_launder_unlogged_state_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            campaign_dir = Path(run_cli(
                ENGINE, "init", "--goal", "No state laundering",
                "--root", root, "--id", "campaign",
            ).stdout.strip())
            state_path = campaign_dir / engine.STATE_REL
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["title"] = "direct unlogged edit"
            engine.write_json(state_path, state)
            event_path = campaign_dir / engine.EVENTS_REL
            before = event_path.read_bytes()

            refused = run_cli(
                ENGINE, "set", campaign_dir, "campaign.mission", "{}", check=False,
            )
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("does not match its event history", refused.stderr)
            self.assertEqual(event_path.read_bytes(), before)

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

    def test_runtime_approval_contract_matches_dispatcher(self):
        cases = []

        malformed = runtime_state()
        malformed["campaign"]["resources_dispatch"]["approvals"] = ["probably approved"]
        cases.append((malformed, "approval.malformed"))

        duplicate = runtime_state()
        duplicate["campaign"]["ethics_rights_safety"]["human_approval_points"] = [{
            "id": "publication-signoff", "description": "duplicate declaration",
        }]
        cases.append((duplicate, "approval.duplicate"))

        malformed_refs = runtime_state()
        malformed_refs["campaign"]["work_units"][0]["approval_ids"] = [{"id": "publication-signoff"}]
        cases.append((malformed_refs, "work_unit.bad_approvals"))

        duplicate_action_refs = runtime_state()
        duplicate_action_refs["campaign"]["work_units"][0]["external_action_ids"] = [
            "publish-result", "publish-result",
        ]
        cases.append((duplicate_action_refs, "work_unit.duplicate_external_actions"))

        duplicate_approval_refs = runtime_state()
        duplicate_approval_refs["campaign"]["work_units"][0]["approval_ids"] = [
            "publication-signoff", "publication-signoff",
        ]
        cases.append((duplicate_approval_refs, "work_unit.duplicate_approvals"))

        for state, expected in cases:
            with self.subTest(expected=expected):
                result = engine.validate_state(state, include_reviews=False)
                self.assertTrue(any(item["code"] == expected for item in result["errors"]), result)


if __name__ == "__main__":
    unittest.main()
