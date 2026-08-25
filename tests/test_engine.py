import argparse
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from common import engine, complete_state, add_passing_reviews


class EngineTests(unittest.TestCase):
    def test_init_records_existing_project_entry_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            args = argparse.Namespace(
                profile="standard", archetypes="evidence-synthesis", root=temp,
                id="existing-case", goal="Finish an existing review", force=False,
                entry_mode="existing-project",
            )
            with contextlib.redirect_stdout(io.StringIO()):
                engine.cmd_init(args)
            state = engine.load_state(Path(temp) / "existing-case")
            self.assertEqual(
                state["campaign"]["starting_point"]["entry_mode"], "existing-project"
            )

    def test_existing_project_requires_an_evidence_based_starting_point(self):
        state = complete_state()
        state["campaign"]["starting_point"]["entry_mode"] = "existing-project"
        result = engine.validate_state(state, include_reviews=False)
        finding = next(item for item in result["errors"]
                       if item["code"] == "starting_point.incomplete")
        self.assertIn("assessment_basis", finding["message"])
        self.assertIn("next_decision", finding["message"])

    def test_explicit_empty_starting_point_is_not_treated_as_new_project(self):
        state = complete_state()
        state["campaign"]["starting_point"] = {}
        result = engine.validate_state(state, include_reviews=False)
        self.assertTrue(any(item["code"] == "starting_point.mode"
                            for item in result["errors"]), result["errors"])
        self.assertIn("Not recorded or invalid", engine._starting_point_block(state))

    def test_campaign_sketch_is_required_before_release(self):
        state = complete_state()
        state["sketch"] = engine.default_state(
            "goal", "standard", ["evidence-synthesis"], "empty-sketch"
        )["sketch"]
        result = engine.validate_state(state, include_reviews=False)
        self.assertTrue(any(item["code"] == "sketch.incomplete"
                            for item in result["errors"]), result["errors"])

    def test_complete_existing_project_can_continue_from_its_frontier(self):
        state = complete_state()
        state["campaign"]["starting_point"].update({
            "entry_mode": "existing-project",
            "status_as_of": "2026-08-24",
            "status_summary": "Collection is complete; analysis has not started.",
            "assessment_basis": ["inspected: data/manifest.json and collection.log"],
            "accepted_completed_work": ["Collection manifest passes its checksum check"],
            "work_in_progress": [],
            "inherited_artifacts": ["data/manifest.json @ sha256:example"],
            "decisions_in_force": ["The bounded corpus is fixed"],
            "known_deviations": [],
            "requires_recheck": ["Audit a sample of extraction records"],
            "next_decision": "Decide whether extraction quality supports analysis",
        })
        result = engine.validate_state(state, include_reviews=False)
        self.assertTrue(result["valid"], result["errors"])

    def test_legacy_new_project_without_starting_point_keeps_current_reviews(self):
        state = complete_state()
        del state["campaign"]["starting_point"]
        state = add_passing_reviews(state)
        result = engine.validate_state(state, include_reviews=True)
        self.assertTrue(result["execution_ready"], result["errors"])

    def test_init_rejects_a_campaign_id_that_escapes_the_root(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "campaigns"
            args = argparse.Namespace(
                profile="standard", archetypes="evidence-synthesis", root=str(root),
                id="../escaped", goal="test goal", force=False,
            )
            with self.assertRaisesRegex(SystemExit, "--id must"):
                engine.cmd_init(args)
            self.assertFalse((Path(temp) / "escaped").exists())

    def test_complete_standard_campaign_validates(self):
        state = add_passing_reviews(complete_state())
        result = engine.validate_state(state, include_reviews=True)
        self.assertTrue(result["execution_ready"], result["errors"])

    def test_tool_requires_canary(self):
        state = complete_state()
        state["campaign"]["canaries"] = []
        result = engine.validate_state(state, include_reviews=False)
        self.assertTrue(any(item["code"] == "tool.no_canary" for item in result["errors"]))

    def test_stage_cycle_is_detected(self):
        state = complete_state()
        state["campaign"]["stages"][0]["prerequisite_stage_ids"] = ["stage-2"]
        result = engine.validate_state(state, include_reviews=False)
        self.assertTrue(any(item["code"] == "stage.cycle" for item in result["errors"]))

    def test_content_change_stales_review(self):
        state = add_passing_reviews(complete_state())
        self.assertTrue(engine.validate_state(state, include_reviews=True)["valid"])
        state["campaign"]["mission"]["scope"] += " changed"
        result = engine.validate_state(state, include_reviews=True)
        self.assertTrue(any(item["code"] == "review.missing" for item in result["errors"]))

    def test_render_and_audit_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = Path(temp) / "campaign"
            for rel in ("state", "working", "outputs", "artifacts"):
                (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
            state = add_passing_reviews(complete_state())
            engine.write_json(campaign_dir / engine.STATE_REL, state)
            rendered = engine.render_outputs(campaign_dir, state)
            self.assertEqual(rendered["status"], "EXECUTION-READY")
            manifest = (campaign_dir / "outputs/MANIFEST.sha256").read_text()
            self.assertIn("CAMPAIGN_PROMPT.md", manifest)
            self.assertIn("16. Kickoff", (campaign_dir / "outputs/CAMPAIGN_PROMPT.md").read_text())

    def test_scoped_campaign_does_not_require_budget_list(self):
        state = complete_state("humanities-interpretive", "scoped")
        state["campaign"]["resources_dispatch"]["budgets"] = []
        result = engine.validate_state(state, include_reviews=False)
        self.assertTrue(result["valid"], result["errors"])

    def test_enabled_runtime_requires_operational_details(self):
        state = complete_state()
        state["campaign"]["runtime"]["enabled"] = True
        state["campaign"]["work_units"] = [{
            "id": "u1", "objective": "Analyze one batch", "authoritative_inputs": ["batch@sha256"],
            "permitted_actions": ["read"], "prohibited_actions": ["no external writes"],
            "outputs": ["result.json"], "acceptance_test": "schema validates",
            "resource_ceiling": "one agent-hour", "retry_policy": "no retry", "escalation": "lead",
        }]
        result = engine.validate_state(state, include_reviews=False)
        self.assertTrue(any(item["code"] == "runtime.incomplete" for item in result["errors"]))

    def test_execution_ready_methods_and_stages_require_operational_fields(self):
        state = complete_state()
        state["campaign"]["methods"][0].pop("inputs")
        state["campaign"]["stages"][0].pop("owner")
        result = engine.validate_state(state, include_reviews=False)
        missing = {(item["code"], item["path"]) for item in result["errors"]}
        self.assertIn(("method.incomplete", "campaign.methods.0"), missing)
        self.assertIn(("stage.incomplete", "campaign.stages.0"), missing)

    def test_high_assurance_campaign_cannot_release_without_a_current_pilot(self):
        state = add_passing_reviews(complete_state("observational", "high-assurance"))
        state["assurance"]["pilot"] = {}
        result = engine.validate_state(state, include_reviews=True)
        self.assertFalse(result["execution_ready"])
        self.assertTrue(any(item["code"] == "pilot.missing" for item in result["errors"]))

    def test_explicit_pilot_requirement_applies_to_standard_campaigns(self):
        state = add_passing_reviews(complete_state())
        state["assurance"]["pilot_required"] = True
        state["assurance"]["pilot"] = {}
        result = engine.validate_state(state, include_reviews=True)
        self.assertTrue(any(item["code"] == "pilot.missing" for item in result["errors"]))

    def test_pilot_without_execution_authority_cannot_release(self):
        state = add_passing_reviews(complete_state("observational", "high-assurance"))
        state["assurance"]["pilot"] = {
            "status": "passed", "content_digest": engine.content_digest(state),
            "scope": "one representative item", "resource_cap": "one agent-hour",
            "executed_at": engine.now_iso(), "evidence": ["pilot-log@sha256"],
            "failures": [], "repairs": [],
        }
        result = engine.validate_state(state, include_reviews=True)
        self.assertTrue(any(item["code"] == "pilot.authority" for item in result["errors"]))

    def test_campaign_repair_stales_the_pilot(self):
        state = complete_state("observational", "high-assurance")
        state["assurance"]["pilot"] = {
            "status": "passed", "content_digest": engine.content_digest(state),
            "authorized_by": "principal-investigator", "authority": "campaign owner",
            "executor_id": "pilot-session-1", "executed_at": engine.now_iso(),
            "scope": "one representative item", "resource_cap": "one agent-hour",
            "evidence": ["pilot-log@sha256"], "failures": [], "repairs": [],
        }
        state["campaign"]["mission"]["scope"] += " repaired"
        result = engine.validate_state(state, include_reviews=False)
        self.assertTrue(any(item["code"] == "pilot.stale" for item in result["errors"]))

    def test_passing_pilot_requires_scope_limits_executor_and_evidence(self):
        state = complete_state("observational", "high-assurance")
        state["assurance"]["pilot"] = {
            "status": "passed", "content_digest": engine.content_digest(state),
            "authorized_by": "principal-investigator", "authority": "campaign owner",
        }
        result = engine.validate_state(state, include_reviews=False)
        self.assertTrue(any(item["code"] == "pilot.incomplete" for item in result["errors"]))

    def test_engine_state_conforms_to_the_published_campaign_schema(self):
        """`campaign.schema.json` is the contract for the published `campaign.json`.

        It is shipped for integrators, so it has to track the engine rather than sit
        beside it. Release validation checks the committed example; this checks every
        profile's freshly built state, which is faster feedback on the same drift.
        """
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema is not installed")
        schema = json.loads((engine.SKILL_DIR / "assets/campaign.schema.json").read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        for profile in ("scoped", "standard", "high-assurance"):
            with self.subTest(profile=profile):
                problems = [item.message for item in validator.iter_errors(complete_state(profile=profile))]
                self.assertEqual(problems, [])

    def test_existing_project_intake_and_draft_are_structurally_schema_valid(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema is not installed")
        schema = json.loads((engine.SKILL_DIR / "assets/campaign.schema.json").read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        state = engine.default_state(
            "Continue an existing project", "standard", ["evidence-synthesis"],
            "existing-intake", "existing-project",
        )
        self.assertEqual([item.message for item in validator.iter_errors(state)], [])
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = Path(temp) / "existing-intake"
            for rel in ("state", "working", "outputs", "artifacts"):
                (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
            engine.save_state(campaign_dir, state)
            rendered = engine.render_outputs(campaign_dir, state, force_draft=True)
            self.assertTrue(rendered["rendered"])
            snapshot = json.loads((campaign_dir / "outputs/campaign.json").read_text())
            self.assertEqual([item.message for item in validator.iter_errors(snapshot)], [])

    def test_legacy_schema_cannot_silently_release(self):
        state = add_passing_reviews(complete_state())
        state["schema_version"] = "3.0"
        result = engine.validate_state(state, include_reviews=True)
        self.assertFalse(result["execution_ready"])
        self.assertTrue(any(item["code"] == "schema.unsupported" for item in result["errors"]))

if __name__ == "__main__":
    unittest.main()
