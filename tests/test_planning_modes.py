from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from common import ROOT, complete_state


ENGINE = ROOT / "rescamp/scripts/rescamp.py"
GOAL = "Decide whether a bounded evidence review should become a full research campaign"
BRIEF_SKETCH = {
    "decision_or_purpose": "Decide whether to commission a full research campaign",
    "scope": "A bounded evidence review using authorized primary and secondary sources",
    "non_goals": ["No execution, delegation, or external action from the brief"],
    "core_inquiries": ["Is the available evidence sufficient to justify a full campaign?"],
    "likely_evidence": ["Authorized primary evidence", "Relevant secondary synthesis"],
    "rough_methods_stages": ["Bound the question", "Inspect representative evidence"],
    "success_or_adjudication": "Recommend a full campaign only when the evidence gap warrants it",
    "assumptions_risks": ["The initial evidence sample may not represent the full corpus"],
    "proposed_outputs": ["Research brief", "Promotion recommendation"],
    "next_action": "Decide whether the evidence gap warrants Camp-full",
}


class PlanningModeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_cli(self, *args: object, check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(ENGINE), *(str(arg) for arg in args)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if check and result.returncode:
            self.fail(
                f"command failed ({result.returncode}): {' '.join(str(arg) for arg in args)}\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        return result

    def init_campaign(self, ident: str, mode: str) -> Path:
        result = self.run_cli(
            "init",
            "--goal",
            GOAL,
            "--root",
            self.root,
            "--id",
            ident,
            "--planning-mode",
            mode,
        )
        return Path(result.stdout.strip())

    def load_state(self, campaign_dir: Path) -> dict:
        return json.loads(
            (campaign_dir / "state/campaign.json").read_text(encoding="utf-8")
        )

    def write_state(self, campaign_dir: Path, state: dict) -> None:
        (campaign_dir / "state/campaign.json").write_text(
            json.dumps(state, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def rendered_brief_digest(self, campaign_dir: Path) -> str:
        content = (campaign_dir / "outputs/RESEARCH_BRIEF.md").read_text(
            encoding="utf-8"
        )
        marker = "**Brief digest:** `"
        line = next((item for item in content.splitlines() if item.startswith(marker)), "")
        self.assertTrue(line.endswith("`"), "rendered brief must disclose its bound digest")
        return line[len(marker):-1]

    def prepare_brief(self, ident: str, mode: str) -> Path:
        campaign_dir = self.init_campaign(ident, mode)
        self.run_cli("set", campaign_dir, "sketch", json.dumps(BRIEF_SKETCH))
        self.run_cli(
            "turn",
            campaign_dir,
            "--branch",
            "decision",
            "--question",
            "What decision must this brief support?",
            "--answer",
            "Decide whether to promote this work to a full campaign.",
            "--normalized",
            "Decide whether to promote the brief to a full campaign",
            "--dimensions",
            "decision",
            "--impact",
            "critical",
            "--utility",
            "high",
        )
        self.run_cli(
            "stop",
            campaign_dir,
            "--reason",
            "material-completeness",
            "--note",
            "The brief has enough information for the promotion decision",
            "--no-auto-quality",
        )
        return campaign_dir

    def finalize_brief(self, ident: str, mode: str) -> Path:
        campaign_dir = self.prepare_brief(ident, mode)
        self.run_cli("brief-finalize", campaign_dir)
        return campaign_dir

    def test_init_records_requested_mode_and_initial_artifact_level(self):
        cases = (
            ("auto", "brief", "pending"),
            ("brief", "brief", "not-offered"),
            ("full", "full", "not-applicable"),
        )
        for requested_mode, artifact_level, promotion_status in cases:
            with self.subTest(requested_mode=requested_mode):
                campaign_dir = self.init_campaign(
                    f"init-{requested_mode}", requested_mode
                )
                workflow = self.load_state(campaign_dir)["workflow"]
                interview = self.load_state(campaign_dir)["interview"]
                self.assertEqual(workflow["requested_mode"], requested_mode)
                self.assertEqual(workflow["artifact_level"], artifact_level)
                self.assertIsInstance(workflow["promotion"], dict)
                self.assertEqual(workflow["promotion"]["status"], promotion_status)
                expected_limits = (8, 12) if requested_mode == "full" else (3, 4)
                self.assertEqual(
                    (interview["soft_limit"], interview["hard_limit"]),
                    expected_limits,
                )

    def test_brief_finalize_renders_brief_and_only_auto_records_an_offer(self):
        for mode, expected_promotion_status in (
            ("auto", "offered"),
            ("brief", "not-offered"),
        ):
            with self.subTest(mode=mode):
                campaign_dir = self.finalize_brief(f"finalize-{mode}", mode)
                brief = campaign_dir / "outputs/RESEARCH_BRIEF.md"
                state = self.load_state(campaign_dir)
                promotion = state["workflow"]["promotion"]

                self.assertTrue(brief.is_file())
                self.assertIn(GOAL, brief.read_text(encoding="utf-8"))
                self.assertFalse((campaign_dir / "outputs/CAMPAIGN_PROMPT.md").exists())
                self.assertEqual(state["status"], "brief-ready")
                self.assertEqual(state["workflow"]["artifact_level"], "brief")
                self.assertEqual(promotion["status"], expected_promotion_status)
                self.assertNotIn("recommendation", promotion)
                self.assertNotIn("reason", promotion)
                self.assertNotIn("promoted_at", promotion)

    def test_auto_finalize_emits_the_exact_single_promotion_prompt(self):
        campaign_dir = self.prepare_brief("exact-auto-prompt", "auto")

        payload = json.loads(self.run_cli("brief-finalize", campaign_dir).stdout)

        self.assertEqual(payload["promotion_prompt"], {
            "question": "The research brief is ready. Promote it to Camp-full?",
            "choices": ["Promote to Camp-full", "Keep brief"],
        })

    def test_brief_finalize_fails_closed_when_the_brief_is_incomplete(self):
        campaign_dir = self.init_campaign("incomplete-brief", "brief")

        result = self.run_cli("brief-finalize", campaign_dir, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((campaign_dir / "outputs/RESEARCH_BRIEF.md").exists())
        self.assertEqual(
            self.load_state(campaign_dir)["workflow"]["artifact_level"], "brief"
        )

    def test_failed_refinalize_removes_the_previously_ready_brief(self):
        campaign_dir = self.finalize_brief("stale-ready-brief", "brief")
        self.assertTrue((campaign_dir / "outputs/RESEARCH_BRIEF.md").exists())
        broken = dict(BRIEF_SKETCH)
        broken["next_action"] = ""
        self.run_cli("set", campaign_dir, "sketch", json.dumps(broken))

        result = self.run_cli("brief-finalize", campaign_dir, check=False)

        self.assertEqual(result.returncode, 2)
        self.assertFalse((campaign_dir / "outputs").exists())
        self.assertEqual(self.load_state(campaign_dir)["outputs"]["manifest"], {})

    def test_complete_sketch_is_not_brief_ready_before_an_explicit_stop(self):
        campaign_dir = self.init_campaign("unstopped-brief", "brief")
        self.run_cli("set", campaign_dir, "sketch", json.dumps(BRIEF_SKETCH))

        result = self.run_cli("brief-finalize", campaign_dir, check=False)
        payload = json.loads(result.stdout)

        self.assertEqual(result.returncode, 2)
        self.assertTrue(any(
            item["code"] == "interview.no_stop_reason"
            for item in payload["validation"]["errors"]
        ))
        self.assertFalse((campaign_dir / "outputs/RESEARCH_BRIEF.md").exists())

    def test_accepting_auto_offer_promotes_in_place_and_preserves_provenance(self):
        campaign_dir = self.finalize_brief("accept-auto", "auto")
        brief_path = campaign_dir / "outputs/RESEARCH_BRIEF.md"
        brief_bytes = brief_path.read_bytes()
        expected_digest = self.rendered_brief_digest(campaign_dir)
        before = self.load_state(campaign_dir)
        answer = "Yes, promote this brief and retain its decisions."

        self.run_cli(
            "promotion",
            campaign_dir,
            "--decision",
            "accept",
            "--source",
            "auto-prompt",
            "--answer",
            answer,
        )

        after = self.load_state(campaign_dir)
        promotion = after["workflow"]["promotion"]
        self.assertEqual(after["workflow"]["artifact_level"], "full")
        self.assertEqual(promotion["status"], "accepted")
        self.assertEqual(promotion["source"], "auto-prompt")
        self.assertEqual(promotion["answer_verbatim"], answer)
        self.assertEqual(promotion["brief_digest"], expected_digest)
        self.assertIsInstance(promotion["accepted_brief"], dict)
        self.assertEqual(promotion["accepted_brief"]["goal_verbatim"], GOAL)
        self.assertEqual(brief_path.read_bytes(), brief_bytes)
        for key in ("campaign_id", "created_at", "goal_verbatim"):
            self.assertEqual(after[key], before[key], f"promotion changed {key}")
        for key in ("turns", "stopping_reason", "stopping_note"):
            self.assertEqual(
                after["interview"][key],
                before["interview"][key],
                f"promotion changed interview.{key}",
            )

    def test_declining_auto_offer_stays_brief_ready_and_is_not_offered_again(self):
        campaign_dir = self.finalize_brief("decline-auto", "auto")
        answer = "Keep this as a brief for now."
        self.run_cli(
            "promotion",
            campaign_dir,
            "--decision",
            "decline",
            "--source",
            "auto-prompt",
            "--answer",
            answer,
        )
        declined = self.load_state(campaign_dir)
        self.assertEqual(declined["workflow"]["artifact_level"], "brief")
        self.assertEqual(declined["status"], "brief-ready")
        declined_promotion = declined["workflow"]["promotion"]
        self.assertEqual(declined_promotion["status"], "declined")
        self.assertEqual(declined_promotion["answer_verbatim"], answer)

        self.run_cli("brief-finalize", campaign_dir)
        repeated = self.load_state(campaign_dir)["workflow"]["promotion"]
        self.assertEqual(repeated, declined_promotion)

    def test_changing_stop_record_invalidates_and_reissues_the_auto_offer(self):
        campaign_dir = self.finalize_brief("changed-stop", "auto")
        first = self.load_state(campaign_dir)["workflow"]["promotion"]

        self.run_cli(
            "stop", campaign_dir, "--reason", "low-next-question-value",
            "--note", "A revised stopping rationale",
        )

        pending = self.load_state(campaign_dir)["workflow"]["promotion"]
        self.assertEqual(pending["status"], "pending")
        self.assertEqual(pending["brief_digest"], "")
        self.run_cli("brief-finalize", campaign_dir)
        second = self.load_state(campaign_dir)["workflow"]["promotion"]
        self.assertEqual(second["status"], "offered")
        self.assertNotEqual(second["brief_digest"], first["brief_digest"])

    def test_stale_offer_cannot_record_a_decision(self):
        campaign_dir = self.finalize_brief("stale-decision", "auto")
        state = self.load_state(campaign_dir)
        state["interview"]["stopping_note"] = "tampered after offer"
        self.write_state(campaign_dir, state)

        result = self.run_cli(
            "promotion", campaign_dir, "--decision", "decline",
            "--source", "auto-prompt", "--answer", "Keep the brief.",
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("older brief", result.stderr)

    def test_full_only_edit_does_not_reopen_an_unchanged_auto_offer(self):
        campaign_dir = self.finalize_brief("full-only-edit", "auto")
        offered = self.load_state(campaign_dir)["workflow"]["promotion"]
        self.run_cli(
            "set", campaign_dir, "campaign.mission",
            json.dumps({
                "decision_or_purpose": "A future full-only purpose",
                "scope": "Future full work",
                "non_goals": [],
                "intended_users": [],
                "completion_definition": "Not part of the brief",
            }),
        )
        self.assertEqual(
            self.load_state(campaign_dir)["workflow"]["promotion"], offered,
        )

    def test_full_finalize_fails_closed_for_a_brief(self):
        campaign_dir = self.finalize_brief("brief-cannot-finalize-full", "brief")

        result = self.run_cli("finalize", campaign_dir, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("brief", (result.stdout + result.stderr).lower())
        self.assertFalse((campaign_dir / "outputs/CAMPAIGN_PROMPT.md").exists())
        self.assertEqual(
            self.load_state(campaign_dir)["workflow"]["artifact_level"], "brief"
        )

    def test_status_derives_brief_readiness_instead_of_trusting_stale_status(self):
        campaign_dir = self.finalize_brief("derived-status", "brief")
        state = self.load_state(campaign_dir)
        state["status"] = "execution-ready"
        self.write_state(campaign_dir, state)

        payload = json.loads(self.run_cli("status", campaign_dir).stdout)

        self.assertEqual(payload["status"], "brief-ready")
        self.assertFalse(payload["execution_ready"])

    def test_camp_full_can_promote_an_explicit_brief_without_an_auto_offer(self):
        campaign_dir = self.finalize_brief("explicit-brief-to-full", "brief")
        before = self.load_state(campaign_dir)
        self.assertEqual(before["workflow"]["promotion"]["status"], "not-offered")
        expected_digest = self.rendered_brief_digest(campaign_dir)
        answer = "Camp-full requested after reviewing the explicit brief."

        self.run_cli(
            "promotion",
            campaign_dir,
            "--decision",
            "accept",
            "--source",
            "camp-full",
            "--answer",
            answer,
        )

        after = self.load_state(campaign_dir)
        promotion = after["workflow"]["promotion"]
        self.assertEqual(after["workflow"]["artifact_level"], "full")
        self.assertEqual(promotion["status"], "accepted")
        self.assertEqual(promotion["source"], "camp-full")
        self.assertEqual(promotion["answer_verbatim"], answer)
        self.assertEqual(promotion["brief_digest"], expected_digest)

    def test_brief_strict_audit_verifies_its_small_bundle(self):
        campaign_dir = self.finalize_brief("audited-brief", "brief")

        result = self.run_cli("audit", campaign_dir, "--strict")
        payload = json.loads(result.stdout)

        self.assertTrue(payload["ok"], payload["errors"])
        self.assertEqual(payload["artifact_level"], "brief")
        self.assertEqual(
            sorted(payload["artifact_verification"]),
            ["MANIFEST.sha256", "RESEARCH_BRIEF.md"],
        )

    def test_brief_renders_interview_decisions_and_stopping_rationale(self):
        campaign_dir = self.finalize_brief("brief-interview", "brief")
        rendered = (campaign_dir / "outputs/RESEARCH_BRIEF.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Decide whether to promote this work to a full campaign.", rendered)
        self.assertIn("The brief has enough information for the promotion decision", rendered)

    def test_brief_validation_rejects_malformed_metadata_entries(self):
        for field in ("intent_dimensions", "contradictions", "blockers"):
            with self.subTest(field=field):
                campaign_dir = self.prepare_brief(
                    f"malformed-{field.replace('_', '-')}", "brief"
                )
                state = self.load_state(campaign_dir)
                state[field] = [1]
                self.write_state(campaign_dir, state)
                result = self.run_cli("brief-finalize", campaign_dir, check=False)
                self.assertEqual(result.returncode, 2)
                errors = json.loads(result.stdout)["validation"]["errors"]
                self.assertTrue(any(item["path"] == field for item in errors), errors)

    def test_non_boolean_extension_cannot_bypass_brief_hard_limit(self):
        campaign_dir = self.prepare_brief("bad-extension", "brief")
        state = self.load_state(campaign_dir)
        state["interview"]["extension_authorized"] = "yes"
        state["interview"]["turns"] = [dict(state["interview"]["turns"][0], number=i)
                                         for i in range(1, 6)]
        self.write_state(campaign_dir, state)

        result = self.run_cli("brief-finalize", campaign_dir, check=False)
        errors = json.loads(result.stdout)["validation"]["errors"]

        self.assertEqual(result.returncode, 2)
        self.assertTrue(any(item["code"] == "interview.extension_type" for item in errors))
        self.assertTrue(any(item["code"] == "brief.question_hard_limit" for item in errors))

    def test_profile_change_preserves_brief_question_limits(self):
        campaign_dir = self.init_campaign("brief-profile", "brief")

        self.run_cli("profile", campaign_dir, "high-assurance")

        interview = self.load_state(campaign_dir)["interview"]
        self.assertEqual((interview["soft_limit"], interview["hard_limit"]), (3, 4))

    def test_brief_state_omits_full_campaign_sections_until_promotion(self):
        campaign_dir = self.init_campaign("lazy-full", "brief")
        campaign = self.load_state(campaign_dir)["campaign"]
        self.assertEqual(set(campaign), {"starting_point"})

        campaign_dir = self.finalize_brief("lazy-promoted", "brief")
        self.run_cli(
            "promotion", campaign_dir, "--decision", "accept", "--source", "camp-full",
            "--answer", "Build the full campaign.",
        )
        promoted = self.load_state(campaign_dir)["campaign"]
        self.assertIn("methods", promoted)
        self.assertIn("runtime", promoted)

    def test_ready_brief_matches_the_published_json_schema(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema is not installed")
        campaign_dir = self.finalize_brief("schema-valid-brief", "brief")
        schema = json.loads(
            (ROOT / "rescamp/assets/campaign.schema.json").read_text(encoding="utf-8")
        )

        jsonschema.validate(self.load_state(campaign_dir), schema)

    def test_init_has_no_destructive_force_escape_hatch(self):
        result = self.run_cli(
            "init", "--goal", GOAL, "--root", self.root, "--id", "forced",
            "--planning-mode", "brief", "--force", check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unrecognized arguments: --force", result.stderr)

    def test_brief_strict_audit_rejects_ready_content_that_was_not_rendered(self):
        campaign_dir = self.prepare_brief("unrendered-brief", "brief")

        result = self.run_cli("audit", campaign_dir, "--strict", check=False)
        payload = json.loads(result.stdout)

        self.assertEqual(result.returncode, 5)
        self.assertFalse(payload["ok"])
        self.assertIn(
            "no rendered output manifest exists; finalize the artifact before auditing",
            payload["errors"],
        )

    def test_migrate_records_legacy_campaigns_as_full(self):
        campaign_dir = self.init_campaign("legacy-full", "full")
        state = self.load_state(campaign_dir)
        state["schema_version"] = "3.1"
        del state["workflow"]
        del state["campaign"]["starting_point"]
        self.write_state(campaign_dir, state)

        payload = json.loads(self.run_cli("migrate", campaign_dir).stdout)
        migrated = self.load_state(campaign_dir)

        self.assertTrue(payload["changed"])
        self.assertEqual(migrated["schema_version"], "3.2")
        self.assertEqual(migrated["workflow"]["requested_mode"], "full")
        self.assertEqual(migrated["workflow"]["artifact_level"], "full")
        self.assertEqual(
            migrated["campaign"]["starting_point"], {"entry_mode": "new-project"}
        )

    def test_validate_without_reviews_never_claims_execution_readiness(self):
        campaign_dir = self.init_campaign("design-only", "full")
        state = self.load_state(campaign_dir)
        complete = complete_state()
        complete["campaign_id"] = state["campaign_id"]
        self.write_state(campaign_dir, complete)

        payload = json.loads(
            self.run_cli("validate", campaign_dir, "--no-reviews").stdout
        )

        self.assertTrue(payload["valid"])
        self.assertFalse(payload["execution_ready"])
        self.assertEqual(payload["release_status"], "plan-ready-execution-blocked")
        self.assertTrue(any(
            item["code"] == "review.not_checked" for item in payload["warnings"]
        ))

    def test_edit_after_decline_reopens_auto_offer_for_changed_brief(self):
        campaign_dir = self.finalize_brief("changed-after-decline", "auto")
        self.run_cli(
            "promotion", campaign_dir, "--decision", "decline",
            "--source", "auto-prompt", "--answer", "Keep the first brief.",
        )
        changed = dict(BRIEF_SKETCH)
        changed["scope"] = "A changed but still bounded evidence review"

        self.run_cli("set", campaign_dir, "sketch", json.dumps(changed))

        promotion = self.load_state(campaign_dir)["workflow"]["promotion"]
        self.assertEqual(promotion["status"], "pending")
        self.assertEqual(promotion["brief_digest"], "")

    def test_full_validation_detects_tampered_accepted_brief_payload(self):
        campaign_dir = self.finalize_brief("tampered-accepted-brief", "auto")
        self.run_cli(
            "promotion", campaign_dir, "--decision", "accept",
            "--source", "auto-prompt", "--answer", "Promote this brief.",
        )
        state = self.load_state(campaign_dir)
        state["workflow"]["promotion"]["accepted_brief"]["goal_verbatim"] = "tampered"
        self.write_state(campaign_dir, state)

        payload = json.loads(
            self.run_cli("validate", campaign_dir, "--no-reviews").stdout
        )

        self.assertTrue(
            any(item["code"] == "promotion.brief_mismatch" for item in payload["errors"]),
            payload["errors"],
        )


if __name__ == "__main__":
    unittest.main()
