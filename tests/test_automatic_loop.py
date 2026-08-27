import tempfile
import unittest
import argparse
import contextlib
import io
import json
from pathlib import Path
from unittest import mock
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
                self.assertRegex(packet["packet_digest"], r"^sha256:[0-9a-f]{64}$")
                self.assertTrue(packet["instructions"]["read_only"])
                self.assertIn("prospective campaign contract", packet["instructions"]["review_object"])
                self.assertIn("unstarted", packet["instructions"]["future_evidence_rule"])
                self.assertIn("intentionally omitted", packet["instructions"]["scope_boundary_rule"])
                self.assertIn("at most the three", packet["instructions"]["finding_policy"])
                self.assertIn(
                    "packet_digest",
                    packet["instructions"]["required_output_schema"]["required"],
                )

    def _campaign(self, temp):
        campaign_dir = Path(temp) / "campaign"
        for rel in ("state", "working", "outputs", "artifacts"):
            (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
        state = complete_state(profile="standard")
        engine.save_state(campaign_dir, state)
        return campaign_dir, state

    @staticmethod
    def _record(packet, reviewer_id):
        return {
            "role": packet["role"], "reviewer_id": reviewer_id,
            "mode": "separate-session", "verdict": "pass",
            "content_digest": packet["content_digest"],
            "rubric_digest": packet["rubric_digest"],
            "packet_digest": packet["packet_digest"],
            "reviewed_sections": packet["reviewed_sections"],
            "summary": "No blocking defect found.", "findings": [],
            "execution_evidence": {
                "executor_id": reviewer_id,
                "started_at": engine.now_iso(), "completed_at": engine.now_iso(),
            },
        }

    def test_ingest_requires_a_current_freeze_and_packet_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir, state = self._campaign(temp)
            forged = {
                "role": "methods-evidence", "reviewer_id": "forged",
                "mode": "sequential-pass", "verdict": "pass",
                "content_digest": engine.content_digest(state),
                "rubric_digest": engine.rubric_digest(state["profile"]),
                "summary": "Forged before freeze", "findings": [],
            }
            review_path = Path(temp) / "forged.json"
            engine.write_json(review_path, forged)

            with self.assertRaisesRegex(SystemExit, "current content freeze"):
                engine.cmd_ingest_review(argparse.Namespace(
                    campaign=str(campaign_dir), file=str(review_path),
                ))

            self.assertEqual(engine.load_state(campaign_dir)["reviews"]["records"], [])
            engine.freeze_and_packets(campaign_dir, engine.load_state(campaign_dir))
            self.assertEqual(engine.load_state(campaign_dir)["reviews"]["records"], [])

    def test_ingested_packet_binding_survives_unrelated_section_repair(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir, _ = self._campaign(temp)
            state = engine.load_state(campaign_dir)
            _, _, paths = engine.freeze_and_packets(campaign_dir, state)
            for index, path in enumerate(paths, 1):
                packet = engine.read_json(path)
                review_path = Path(temp) / f"{packet['role']}-review.json"
                engine.write_json(review_path, self._record(packet, f"reviewer-{index}"))
                engine.cmd_ingest_review(argparse.Namespace(
                    campaign=str(campaign_dir), file=str(review_path),
                ))

            state = engine.load_state(campaign_dir)
            old_methods_digest = next(
                item["packet_digest"] for item in state["reviews"]["records"]
                if item["role"] == "methods-evidence"
            )
            old_operations_digest = next(
                item["packet_digest"] for item in state["reviews"]["records"]
                if item["role"] == "operations-reproducibility"
            )
            state["campaign"]["resources_dispatch"]["budgets"] = ["Revised ceiling"]
            state["content_version"] += 1
            engine.save_state(campaign_dir, state)
            engine.freeze_and_packets(campaign_dir, engine.load_state(campaign_dir))

            after = engine.load_state(campaign_dir)
            roles = sorted(item["role"] for item in after["reviews"]["records"])
            self.assertEqual(roles, ["methods-evidence"])
            methods = after["reviews"]["records"][0]
            self.assertEqual(methods["packet_digest"], old_methods_digest)
            self.assertTrue(engine.record_is_current(methods, after))
            self.assertNotEqual(
                after["reviews"]["current_packets"]["methods-evidence"],
                old_methods_digest,
            )
            self.assertIn(old_methods_digest, after["reviews"]["packet_metadata"])
            self.assertNotIn(old_operations_digest, after["reviews"]["packet_metadata"])
            self.assertEqual(len(after["reviews"]["packet_metadata"]), 3)

    def test_packet_contract_change_invalidates_otherwise_current_reviews(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir, _ = self._campaign(temp)
            _, _, paths = engine.freeze_and_packets(campaign_dir, engine.load_state(campaign_dir))
            for index, path in enumerate(paths, 1):
                packet = engine.read_json(path)
                review_path = Path(temp) / f"{packet['role']}-review.json"
                engine.write_json(review_path, self._record(packet, f"reviewer-{index}"))
                engine.cmd_ingest_review(argparse.Namespace(
                    campaign=str(campaign_dir), file=str(review_path),
                ))

            original_contract = engine.packet_contract_identity
            original_packet = engine.packet_identity
            with mock.patch.object(
                engine,
                "packet_contract_identity",
                side_effect=lambda packet: {**original_contract(packet), "contract_revision": "changed"},
            ), mock.patch.object(
                engine,
                "packet_identity",
                side_effect=lambda packet: {**original_packet(packet), "contract_revision": "changed"},
            ):
                engine.freeze_and_packets(campaign_dir, engine.load_state(campaign_dir))

            after = engine.load_state(campaign_dir)
            self.assertEqual(after["reviews"]["records"], [])
            self.assertEqual(
                engine.review_status(after)[1],
                ["methods-evidence", "operations-reproducibility"],
            )

    def test_optional_sequential_execution_evidence_is_still_typed(self):
        record = self._record({
            "role": "skeptical",
            "content_digest": "sha256:" + "1" * 64,
            "rubric_digest": "sha256:" + "2" * 64,
            "packet_digest": "sha256:" + "3" * 64,
            "reviewed_sections": {"mission": "sha256:" + "4" * 64},
        }, "reviewer-1")
        record["mode"] = "sequential-pass"
        record["execution_evidence"]["host"] = []
        errors = engine.review_record_errors(record)
        self.assertIn("execution_evidence invalid host", errors)

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
        record["findings"] *= 4
        self.assertTrue(any("at most three" in item for item in engine.review_record_errors(record)))

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

    def test_duplicate_current_roles_cannot_bypass_a_blocking_review(self):
        state = add_passing_reviews(complete_state())
        duplicate = dict(state["reviews"]["records"][0])
        duplicate["reviewer_id"] = "second-reviewer"
        duplicate["verdict"] = "block"
        state["reviews"]["records"].append(duplicate)

        result = engine.validate_state(state, include_reviews=True)

        self.assertFalse(result["execution_ready"])
        self.assertTrue(any(item["code"] == "review.duplicate_role"
                            for item in result["errors"]), result["errors"])
        self.assertIn("methods-evidence", result["review"]["blocking"])

    def test_review_record_errors_require_typed_digests_and_independence_evidence(self):
        state = complete_state()
        record = {
            "role": ["methods-evidence"], "reviewer_id": {"id": "r1"},
            "mode": "separate-session", "verdict": "pass",
            "content_digest": [engine.content_digest(state)],
            "rubric_digest": engine.rubric_digest(state["profile"]),
            "summary": ["looks fine"], "findings": [],
            "evidence_inspected": ["packet", 7],
            "execution_evidence": {
                "executor_id": 7, "started_at": "yesterday", "completed_at": engine.now_iso(),
                "host": [],
            },
        }

        errors = engine.review_record_errors(record)

        self.assertTrue(any("role" in item for item in errors), errors)
        self.assertTrue(any("reviewer_id" in item for item in errors), errors)
        self.assertIn("invalid content_digest", errors)
        self.assertTrue(any("summary" in item for item in errors), errors)
        self.assertTrue(any("executor_id" in item for item in errors), errors)
        self.assertTrue(any("started_at" in item for item in errors), errors)
        self.assertTrue(any("evidence_inspected" in item for item in errors), errors)
        self.assertTrue(any("host" in item for item in errors), errors)

        record.update({
            "role": "methods-evidence", "reviewer_id": "r1", "summary": "Review",
            "content_digest": engine.content_digest(state),
            "evidence_inspected": ["packet"],
            "execution_evidence": {
                "executor_id": "executor-1", "started_at": engine.now_iso(),
                "completed_at": engine.now_iso(), "host": "test-host",
            },
            "findings": [{
                "severity": "minor", "action": "agent-fix", "description": "Finding",
                "affected_ids": [7], "recommended_remedy": [],
            }],
        })
        errors = engine.review_record_errors(record)
        self.assertTrue(any("affected_ids" in item for item in errors), errors)
        self.assertTrue(any("recommended_remedy" in item for item in errors), errors)

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
