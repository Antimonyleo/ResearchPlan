import json
import tempfile
import unittest
from pathlib import Path
from common import engine, complete_state, add_passing_reviews


class EngineTests(unittest.TestCase):
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
            engine.append_event(campaign_dir, "test", {})
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


if __name__ == "__main__":
    unittest.main()
