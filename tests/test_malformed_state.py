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
            "interview", "assurance", "campaign", "reviews", "outputs",
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
