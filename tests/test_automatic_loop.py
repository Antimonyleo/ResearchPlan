import json
import tempfile
import unittest
import argparse
import contextlib
import io
from pathlib import Path
from common import engine, complete_state, add_passing_reviews


class AutomaticLoopTests(unittest.TestCase):
    def test_quality_loop_creates_frozen_packets(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = Path(temp) / "campaign"
            for rel in ("state", "working", "outputs", "artifacts"):
                (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
            state = complete_state(profile="standard")
            engine.save_state(campaign_dir, state, "test")
            digest, rubric, paths = engine.freeze_and_packets(campaign_dir, state)
            self.assertEqual(len(paths), 2)
            for path in paths:
                packet = engine.read_json(path)
                self.assertEqual(packet["content_digest"], digest)
                self.assertEqual(packet["rubric_digest"], rubric)
                self.assertTrue(packet["instructions"]["read_only"])

    def test_agent_fix_does_not_replace_user_authority(self):
        state = complete_state()
        state["intent_dimensions"].append({
            "id": "publication-authority", "label": "Publication authority", "status": "unresolved",
            "value": "", "importance": "critical", "source": "user", "confidence": "low",
            "reason": "", "dependencies": [],
        })
        result = engine.validate_state(state, include_reviews=False)
        self.assertTrue(any(item["code"] == "dimension.unresolved" for item in result["errors"]))


    def test_stop_validates_and_freezes_but_runs_no_reviewer(self):
        """`stop` prepares review inputs. It must not imply a review happened."""
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = Path(temp) / "campaign"
            for rel in ("state", "working", "outputs", "artifacts"):
                (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
            state = complete_state(profile="standard")
            state["interview"]["stopping_reason"] = ""
            state["interview"]["stopping_note"] = ""
            engine.save_state(campaign_dir, state, "test")
            args = argparse.Namespace(campaign=str(campaign_dir), reason="material-completeness", note="resolved", no_auto_quality=False)
            with contextlib.redirect_stdout(io.StringIO()):
                engine.cmd_stop(args)
            payload = engine.read_json(campaign_dir / "working/quality_loop.json")
            self.assertEqual(payload["phase"], "awaiting-review-execution")
            self.assertEqual(len(payload["review_packets_all"]), 2)
            # Only the roles that actually need running are offered for execution.
            self.assertEqual(len(payload["review_packets_to_execute"]), 2)
            self.assertEqual(payload["roles_requiring_review"],
                             sorted(engine.PROFILES["standard"]["review_roles"]))
            self.assertIn("deterministic_validation", payload["completed_by_this_command"])
            self.assertIn("reviewer_execution", payload["not_run_by_this_command"])

            # The load-bearing assertion the old test was missing: `stop` runs no reviewer.
            after = engine.load_state(campaign_dir)
            self.assertEqual(after["reviews"]["records"], [], "stop must not fabricate review records")
            self.assertEqual(payload["reviews_ingested"], 0)
            result = engine.validate_state(after, include_reviews=True)
            self.assertFalse(result["execution_ready"])
            self.assertTrue(any(item["code"] == "review.missing" for item in result["errors"]))

    def test_review_record_schema_logic(self):
        state = complete_state()
        digest = engine.content_digest(state)
        rubric = engine.rubric_digest(state["profile"])
        evidence = {"executor_id": "session-a", "started_at": engine.now_iso(), "completed_at": engine.now_iso()}
        record = {"role":"methods-evidence","reviewer_id":"r1","mode":"separate-session","verdict":"revise","content_digest":digest,"rubric_digest":rubric,"summary":"Need one user answer","execution_evidence":evidence,"findings":[{"severity":"major","action":"user-answer","description":"Clarify authority"}]}
        self.assertEqual(engine.review_record_errors(record), [])

    def test_independence_claim_requires_execution_evidence(self):
        """A record cannot claim independence by writing a bare mode string."""
        state = complete_state()
        record = {
            "role": "methods-evidence", "reviewer_id": "r1", "mode": "independent-subagent",
            "verdict": "pass", "content_digest": engine.content_digest(state),
            "rubric_digest": engine.rubric_digest(state["profile"]),
            "summary": "Looks fine", "findings": [],
        }
        errors = engine.review_record_errors(record)
        self.assertTrue(any("execution_evidence" in item for item in errors), errors)

        record["mode"] = "sequential-pass"
        self.assertEqual(engine.review_record_errors(record), [],
                         "a sequential pass claims no independence and needs no evidence")


if __name__ == "__main__":
    unittest.main()
