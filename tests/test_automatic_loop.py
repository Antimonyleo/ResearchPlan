import tempfile
import unittest
import argparse
import contextlib
import io
import json
from pathlib import Path
from common import add_passing_reviews, engine, complete_state


class AutomaticLoopTests(unittest.TestCase):
    def test_quality_loop_creates_frozen_packets(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = Path(temp) / "campaign"
            for rel in ("state", "working", "outputs", "artifacts"):
                (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
            state = complete_state(profile="standard")
            engine.save_state(campaign_dir, state)
            digest, rubric, paths = engine.freeze_and_packets(campaign_dir, state)
            self.assertEqual(len(paths), 2)
            for path in paths:
                packet = engine.read_json(path)
                self.assertEqual(packet["content_digest"], digest)
                self.assertEqual(packet["rubric_digest"], rubric)
                self.assertTrue(packet["instructions"]["read_only"])

    def test_invalid_design_does_not_offer_stale_review_work(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = Path(temp) / "campaign"
            for rel in ("state", "working", "outputs", "artifacts"):
                (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
            state = complete_state(profile="scoped")
            state["sketch"]["scope"] = ""
            engine.save_state(campaign_dir, state)

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                engine.cmd_quality_loop(argparse.Namespace(campaign=str(campaign_dir)))
            payload = json.loads(output.getvalue())

            self.assertEqual(payload["phase"], "awaiting-design-repair")
            self.assertEqual(payload["review_packets_to_execute"], [])
            self.assertEqual(payload["roles_requiring_review"], [])
            self.assertEqual(payload["roles_pending_after_design_repair"], ["skeptical"])

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
            engine.save_state(campaign_dir, state)
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

    def test_quality_loop_ignores_replaceable_stale_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = Path(temp) / "campaign"
            for rel in ("state", "working", "outputs", "artifacts"):
                (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
            state = complete_state(profile="standard")
            engine.save_state(campaign_dir, state)
            engine.render_outputs(campaign_dir, state, force_draft=True)
            state = engine.load_state(campaign_dir)
            state["campaign"]["mission"]["scope"] = "A refined bounded scope"
            state["content_version"] += 1
            engine.save_state(campaign_dir, state)

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                engine.cmd_quality_loop(argparse.Namespace(campaign=str(campaign_dir)))
            payload = json.loads(output.getvalue())

            self.assertEqual(payload["phase"], "awaiting-review-execution")
            self.assertFalse(any(item["code"] == "outputs.stale"
                                 for item in payload["deterministic_validation"]["errors"]))

    def test_replacement_draft_does_not_report_its_old_bundle_as_a_blocker(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = Path(temp) / "campaign"
            for rel in ("state", "working", "outputs", "artifacts"):
                (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
            state = complete_state(profile="standard")
            engine.save_state(campaign_dir, state)
            engine.render_outputs(campaign_dir, state, force_draft=True)
            state = engine.load_state(campaign_dir)
            state["campaign"]["mission"]["scope"] = "A refined bounded scope"
            state["content_version"] += 1
            engine.save_state(campaign_dir, state)

            result = engine.render_outputs(campaign_dir, state, force_draft=True)
            blockers = (campaign_dir / "outputs/BLOCKERS.md").read_text(encoding="utf-8")

            self.assertTrue(result["rendered"])
            self.assertNotIn("outputs.stale", blockers)

    def test_status_exposes_resume_decisions_assumptions_blockers_and_next_branch(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = Path(temp) / "campaign"
            for rel in ("state", "working", "outputs", "artifacts"):
                (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
            state = complete_state(profile="standard")
            state["assumptions"] = ["The inherited manifest is authoritative"]
            state["blockers"] = [{
                "id": "source-access", "severity": "major", "status": "open",
                "description": "Primary source access is not confirmed", "owner": "lead",
            }]
            state["intent_dimensions"].append({
                "id": "source-boundary", "label": "Source boundary",
                "status": "unresolved", "value": "", "importance": "critical",
                "reason": "Awaiting an access decision", "dependencies": ["source-access"],
            })
            engine.save_state(campaign_dir, state)

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                engine.cmd_status(argparse.Namespace(campaign=str(campaign_dir)))
            payload = json.loads(output.getvalue())

            self.assertEqual(payload["interview"]["next_branch"], "source-boundary")
            self.assertIn("bounded decision", [item["value"] for item in payload["decisions"]])
            self.assertEqual(payload["assumptions"], state["assumptions"])
            self.assertEqual(payload["open_blockers"][0]["description"],
                             "Primary source access is not confirmed")

    def test_status_prioritizes_critical_resume_branch_over_storage_order(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = Path(temp) / "campaign"
            for rel in ("state", "working", "outputs", "artifacts"):
                (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
            state = complete_state(profile="standard")
            for ident, importance in (("minor-detail", "low"), ("critical-scope", "critical")):
                state["intent_dimensions"].append({
                    "id": ident, "label": ident, "status": "unresolved", "value": "",
                    "importance": importance, "reason": "", "dependencies": [],
                })
            engine.save_state(campaign_dir, state)

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                engine.cmd_status(argparse.Namespace(campaign=str(campaign_dir)))

            self.assertEqual(json.loads(output.getvalue())["interview"]["next_branch"],
                             "critical-scope")

    def test_status_separates_stale_outputs_from_design_validity(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = Path(temp) / "campaign"
            for rel in ("state", "working", "outputs", "artifacts"):
                (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
            state = complete_state(profile="standard")
            engine.save_state(campaign_dir, state)
            engine.render_outputs(campaign_dir, state, force_draft=True)
            state = engine.load_state(campaign_dir)
            state["campaign"]["mission"]["scope"] = "A refined bounded scope"
            state["content_version"] += 1
            engine.save_state(campaign_dir, state)

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                engine.cmd_status(argparse.Namespace(campaign=str(campaign_dir)))
            payload = json.loads(output.getvalue())

            self.assertTrue(payload["design_valid"])
            self.assertEqual(payload["design_errors"], 0)
            self.assertTrue(payload["output_stale"])

    def test_status_derives_full_readiness_after_an_execution_ready_campaign_is_edited(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = Path(temp) / "campaign"
            for rel in ("state", "working", "outputs", "artifacts"):
                (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
            state = add_passing_reviews(complete_state(profile="standard"))
            engine.save_state(campaign_dir, state)
            engine.render_outputs(campaign_dir, state)
            self.assertEqual(engine.load_state(campaign_dir)["status"], "execution-ready")

            with contextlib.redirect_stdout(io.StringIO()):
                engine.cmd_set(argparse.Namespace(
                    campaign=str(campaign_dir), path="campaign.mission.scope",
                    value="A materially revised scope", create_missing=False,
                ))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                engine.cmd_status(argparse.Namespace(campaign=str(campaign_dir)))
            payload = json.loads(output.getvalue())

            self.assertEqual(payload["status"], "plan-ready-execution-blocked")
            self.assertFalse(payload["execution_ready"])
            self.assertTrue(payload["output_stale"])

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

    def test_semantically_invalid_stored_review_cannot_satisfy_readiness(self):
        state = add_passing_reviews(complete_state())
        state["reviews"]["records"][0]["mode"] = "invented-mode"
        state["reviews"]["records"][0]["summary"] = ""

        result = engine.validate_state(state, include_reviews=True)

        self.assertFalse(result["execution_ready"])
        self.assertTrue(any(
            item["code"] == "review.record_invalid" for item in result["errors"]
        ), result["errors"])

    def test_review_digests_require_exact_sha256_format(self):
        state = complete_state()
        record = {
            "role": "methods-evidence", "reviewer_id": "r1",
            "mode": "sequential-pass", "verdict": "pass",
            "content_digest": "sha256:not-a-digest",
            "rubric_digest": engine.rubric_digest(state["profile"]),
            "summary": "No findings", "findings": [],
        }

        self.assertIn("invalid content_digest", engine.review_record_errors(record))
        self.assertFalse(engine.record_is_current(record, state))


if __name__ == "__main__":
    unittest.main()
