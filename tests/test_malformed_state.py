import argparse
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from common import add_passing_reviews, complete_state, engine


def replace_path(state, dotted, value):
    current = state
    parts = dotted.split(".")
    for part in parts[:-1]:
        current = current[part]
    current[parts[-1]] = value


class MalformedStateTests(unittest.TestCase):
    def assert_rejected_without_exception(self, dotted, value):
        state = complete_state()
        replace_path(state, dotted, value)

        result = engine.validate_state(state, include_reviews=False)

        self.assertFalse(result["valid"])
        self.assertTrue(
            any(item["code"] == "structure.type"
                and (item["path"] == dotted or item["path"].startswith(dotted + "."))
                for item in result["errors"]),
            result["errors"],
        )

    def test_wrong_container_types_return_structured_errors(self):
        object_paths = (
            "interview", "assurance", "sketch", "campaign", "reviews", "outputs",
            "campaign.constitution", "campaign.mission", "campaign.dossier",
            "campaign.evaluation", "campaign.resources_dispatch", "campaign.runtime",
            "campaign.ethics_rights_safety", "campaign.reporting", "campaign.kickoff",
        )
        list_paths = (
            "archetypes", "intent_dimensions", "contradictions", "blockers",
            "campaign.inquiries", "campaign.methods", "campaign.tools",
            "campaign.canaries", "campaign.stages", "campaign.gates",
            "campaign.work_units", "campaign.claims", "campaign.deliverables",
        )
        for dotted in object_paths + list_paths:
            with self.subTest(path=dotted):
                self.assert_rejected_without_exception(dotted, "not-the-required-container")

    def test_enum_and_optional_collection_types_never_raise(self):
        cases = (
            lambda state: state.update(profile=[]),
            lambda state: state["workflow"].update(requested_mode={}),
            lambda state: state["workflow"].update(artifact_level=[]),
            lambda state: state["workflow"]["promotion"].update(status={}),
            lambda state: state["interview"].update(stopping_reason={}),
            lambda state: state["intent_dimensions"][0].update(status=[]),
            lambda state: state["campaign"]["ethics_rights_safety"].update(
                external_actions=None
            ),
        )
        for mutate in cases:
            with self.subTest(mutate=mutate):
                state = complete_state()
                mutate(state)
                result = engine.validate_state(state, include_reviews=False)
                self.assertFalse(result["valid"])
                self.assertTrue(result["errors"])

    def test_empty_interview_turn_is_not_valid_provenance(self):
        state = complete_state()
        state["interview"]["turns"] = [{}]

        result = engine.validate_state(state, include_reviews=False)

        self.assertFalse(result["valid"])
        self.assertTrue(any(
            item["code"] == "interview.turn_malformed" for item in result["errors"]
        ))

    def test_public_commands_reject_non_object_state_without_tracebacks(self):
        for command in ("status", "validate", "audit"):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as temp:
                campaign_dir = Path(temp) / "campaign"
                (campaign_dir / "state").mkdir(parents=True)
                engine.write_json(campaign_dir / engine.STATE_REL, [])

                result = subprocess.run(
                    [sys.executable, str(engine.__file__), command, str(campaign_dir)],
                    capture_output=True, text=True,
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("Traceback", result.stderr)
                self.assertIn("Campaign state must be a JSON object", result.stderr)

    def test_public_commands_reject_invalid_json_without_tracebacks(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = Path(temp) / "campaign"
            state_path = campaign_dir / engine.STATE_REL
            state_path.parent.mkdir(parents=True)
            state_path.write_text("{not-json\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(engine.__file__), "status", str(campaign_dir)],
                capture_output=True, text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("Traceback", result.stderr)
            self.assertIn("Could not read campaign state", result.stderr)

    def test_symlinked_state_is_rejected_without_touching_its_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            campaign_dir = root / "campaign"
            state_path = campaign_dir / engine.STATE_REL
            state_path.parent.mkdir(parents=True)
            outside = root / "outside.json"
            outside.write_text('{"sentinel": true}\n', encoding="utf-8")
            state_path.symlink_to(outside)

            result = subprocess.run(
                [sys.executable, str(engine.__file__), "validate", str(campaign_dir)],
                capture_output=True, text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("Traceback", result.stderr)
            self.assertIn("must not be a symlink", result.stderr)
            self.assertEqual(outside.read_text(encoding="utf-8"), '{"sentinel": true}\n')

    def test_malformed_review_record_is_rejected_without_mutating_state(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = Path(temp) / "campaign"
            (campaign_dir / "state").mkdir(parents=True)
            state = complete_state()
            engine.write_json(campaign_dir / engine.STATE_REL, state)
            review = Path(temp) / "review.json"
            engine.write_json(review, None)

            result = subprocess.run(
                [sys.executable, str(engine.__file__), "ingest-review",
                 str(campaign_dir), str(review)],
                capture_output=True, text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("Traceback", result.stderr)
            self.assertEqual(engine.load_state(campaign_dir), state)

    def test_non_object_collection_entries_return_structured_errors(self):
        paths = (
            "intent_dimensions", "contradictions", "blockers", "reviews.records",
            "campaign.inquiries", "campaign.methods", "campaign.tools",
            "campaign.canaries", "campaign.stages", "campaign.gates",
            "campaign.work_units", "campaign.claims", "campaign.deliverables",
        )
        for dotted in paths:
            with self.subTest(path=dotted):
                self.assert_rejected_without_exception(dotted, ["not-an-object"])

    def test_set_rejects_malformed_object_list_replacements_atomically(self):
        malformed_values = ("not-a-list", [{"id": "valid-shape"}, "not-an-object"])
        for dotted in engine.OBJECT_SPECS:
            for value in malformed_values:
                with self.subTest(path=dotted, value=value):
                    with tempfile.TemporaryDirectory() as temp:
                        campaign_dir = Path(temp) / "campaign"
                        (campaign_dir / "state").mkdir(parents=True)
                        state = complete_state()
                        engine.write_json(campaign_dir / engine.STATE_REL, state)
                        before = copy.deepcopy(state)
                        args = argparse.Namespace(
                            campaign=str(campaign_dir), path=dotted,
                            value=engine.canonical_json(value), create_missing=False,
                        )

                        with self.assertRaises(SystemExit):
                            engine.cmd_set(args)

                        self.assertEqual(engine.load_state(campaign_dir), before)

    def test_nested_reference_and_review_types_return_errors(self):
        cases = (
            ("campaign.methods.0.inquiry_ids", False,
             lambda state: state["campaign"]["methods"][0].update(inquiry_ids=[{}])),
            ("campaign.stages.0.prerequisite_stage_ids", False,
             lambda state: state["campaign"]["stages"][0].update(prerequisite_stage_ids=[{}])),
            ("campaign.gates.0.checkpoint_review", False,
             lambda state: state["campaign"]["gates"][0].update(checkpoint_review=False)),
            ("campaign.work_units.0.dependency_ids", False,
             lambda state: state["campaign"].update(work_units=[{"id": "unit-1", "dependency_ids": [{}]}])),
            ("campaign.canaries.0.tool_id", False,
             lambda state: state["campaign"]["canaries"][0].update(tool_id={})),
            ("campaign.tools.0.id", False,
             lambda state: state["campaign"]["tools"][0].update(id={})),
            ("reviews.records.0.reviewed_sections", True,
             lambda state: state["reviews"]["records"][0].update(reviewed_sections="bad")),
            ("reviews.records.0.findings.0.severity", True,
             lambda state: state["reviews"]["records"][0].update(findings=[{
                 "severity": {}, "action": [], "description": [],
             }])),
            ("reviews.records.0.execution_evidence", True,
             lambda state: state["reviews"]["records"][0].update(execution_evidence="bad")),
        )
        for expected_path, include_reviews, mutate in cases:
            with self.subTest(path=expected_path):
                state = complete_state()
                if include_reviews:
                    add_passing_reviews(state)
                mutate(state)

                result = engine.validate_state(state, include_reviews=include_reviews)

                self.assertFalse(result["valid"])
                self.assertTrue(
                    any(item["code"] == "structure.type"
                        and (item["path"] == expected_path
                             or item["path"].startswith(expected_path + "."))
                        for item in result["errors"]),
                    result["errors"],
                )

    def test_public_render_commands_refuse_malformed_sections_without_tracebacks(self):
        with tempfile.TemporaryDirectory() as temp:
            initialized = subprocess.run(
                [sys.executable, str(engine.__file__), "init", "--goal", "Bounded idea",
                 "--root", temp], capture_output=True, text=True, check=True,
            )
            campaign_dir = Path(initialized.stdout.strip())
            state = engine.load_state(campaign_dir)
            state["campaign"]["mission"] = "not-an-object"
            engine.write_json(campaign_dir / engine.STATE_REL, state)

            for command in ("finalize", "render", "draft"):
                with self.subTest(command=command):
                    result = subprocess.run(
                        [sys.executable, str(engine.__file__), command, str(campaign_dir)],
                        capture_output=True, text=True,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertNotIn("Traceback", result.stderr)
                    payload = json.loads(result.stdout)
                    self.assertFalse(payload["rendered"])
                    self.assertTrue(any(
                        item["code"] == "structure.type"
                        and item["path"] == "campaign.mission"
                        for item in payload["validation"]["errors"]
                    ))
                    self.assertEqual(list((campaign_dir / "outputs").iterdir()), [])

    def test_public_render_refuses_semantically_malformed_review_without_traceback(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = Path(temp) / "campaign"
            (campaign_dir / "state").mkdir(parents=True)
            state = add_passing_reviews(complete_state())
            state["reviews"]["records"][0]["execution_evidence"]["started_at"] = "not-an-iso-time"
            engine.write_json(campaign_dir / engine.STATE_REL, state)

            result = subprocess.run(
                [sys.executable, str(engine.__file__), "render", str(campaign_dir)],
                capture_output=True, text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("Traceback", result.stderr)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["rendered"])
            self.assertTrue(any(item["code"] == "review.record_invalid"
                                for item in payload["validation"]["errors"]),
                            payload["validation"]["errors"])

    def test_structurally_valid_incomplete_draft_still_renders(self):
        with tempfile.TemporaryDirectory() as temp:
            initialized = subprocess.run(
                [sys.executable, str(engine.__file__), "init", "--goal", "Bounded idea",
                 "--root", temp], capture_output=True, text=True, check=True,
            )
            campaign_dir = Path(initialized.stdout.strip())

            result = subprocess.run(
                [sys.executable, str(engine.__file__), "draft", str(campaign_dir)],
                capture_output=True, text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["rendered"])
            self.assertTrue((campaign_dir / "outputs/CAMPAIGN_PROMPT.md").is_file())

    def test_status_reports_malformed_collections_without_a_traceback(self):
        cases = (("intent_dimensions", ["not-an-object"]),
                 ("contradictions", ["not-an-object"]),
                 ("contradictions", 3),
                 ("blockers", ["not-an-object"]))
        for field, malformed in cases:
            with self.subTest(field=field, malformed=malformed), tempfile.TemporaryDirectory() as temp:
                campaign_dir = Path(temp) / "campaign"
                for rel in ("state", "working", "outputs", "artifacts"):
                    (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
                state = complete_state()
                state[field] = malformed
                engine.write_json(campaign_dir / engine.STATE_REL, state)

                result = subprocess.run(
                    [sys.executable, str(engine.__file__), "status", str(campaign_dir)],
                    capture_output=True, text=True,
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                payload = json.loads(result.stdout)
                self.assertFalse(payload["design_valid"])

    def test_status_handles_missing_identity_and_invalid_profile(self):
        cases = (("campaign_id", None), ("profile", "not-a-profile"))
        for field, value in cases:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                campaign_dir = Path(temp) / "campaign"
                (campaign_dir / "state").mkdir(parents=True)
                state = complete_state()
                if value is None:
                    state.pop(field)
                else:
                    state[field] = value
                engine.write_json(campaign_dir / engine.STATE_REL, state)

                result = subprocess.run(
                    [sys.executable, str(engine.__file__), "status", str(campaign_dir)],
                    capture_output=True, text=True,
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                payload = json.loads(result.stdout)
                self.assertFalse(payload["design_valid"])
                self.assertFalse(payload["execution_ready"])

    def test_audit_handles_malformed_outputs_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = Path(temp) / "campaign"
            for rel in ("state", "working", "outputs"):
                (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
            state = complete_state()
            state["outputs"] = ["not-an-object"]
            engine.write_json(campaign_dir / engine.STATE_REL, state)

            result = subprocess.run(
                [sys.executable, str(engine.__file__), "audit", str(campaign_dir), "--strict"],
                capture_output=True, text=True,
            )

            self.assertEqual(result.returncode, 5, result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            self.assertFalse(payload["validation"]["valid"])

    def test_numeric_required_prose_is_rejected(self):
        cases = (
            ("mission.missing", lambda state: state["campaign"]["mission"].update(decision_or_purpose=0)),
            ("mission.missing", lambda state: state["campaign"]["mission"].update(scope=0)),
            ("mission.missing", lambda state: state["campaign"]["mission"].update(completion_definition=0)),
            ("inquiry.incomplete", lambda state: state["campaign"]["inquiries"][0].update(question_or_claim=0)),
            ("method.incomplete", lambda state: state["campaign"]["methods"][0].update(purpose=0)),
            ("deliverable.incomplete", lambda state: state["campaign"]["deliverables"][0].update(name=0)),
        )
        for expected_code, mutate in cases:
            with self.subTest(code=expected_code, mutate=mutate):
                state = complete_state()
                mutate(state)
                result = engine.validate_state(state, include_reviews=False)
                self.assertTrue(any(item["code"] == expected_code for item in result["errors"]), result)

    def test_blank_only_required_lists_are_rejected(self):
        cases = (
            ("constitution.weak", lambda state: state["campaign"]["constitution"].update(rules=["", "", ""])),
            ("dossier.objects", lambda state: state["campaign"]["dossier"].update(objects=[""])),
            ("dossier.sources", lambda state: state["campaign"]["dossier"].update(source_hierarchy=[""])),
            ("inquiry.incomplete", lambda state: state["campaign"]["inquiries"][0].update(admissible_support=[""])),
            ("method.incomplete", lambda state: state["campaign"]["methods"][0].update(inputs=[""])),
            ("canary.incomplete", lambda state: state["campaign"]["canaries"][0].update(expected_artifacts=[""])),
            ("evaluation.incomplete", lambda state: state["campaign"]["evaluation"].update(criteria=[""])),
            ("stage.incomplete", lambda state: state["campaign"]["stages"][0].update(activities=[""])),
            ("gate.incomplete", lambda state: state["campaign"]["gates"][0].update(criteria=[""])),
            ("dispatch.rules", lambda state: state["campaign"]["resources_dispatch"].update(dispatch_rules=[""])),
            ("claim.incomplete", lambda state: state["campaign"]["claims"][0].update(support=[""])),
            ("ethics.none", lambda state: state["campaign"]["ethics_rights_safety"].update(constraints=[""])),
        )
        for expected_code, mutate in cases:
            with self.subTest(code=expected_code, mutate=mutate):
                state = complete_state()
                mutate(state)
                result = engine.validate_state(state, include_reviews=False)
                self.assertTrue(any(item["code"] == expected_code for item in result["errors"]), result)


if __name__ == "__main__":
    unittest.main()
