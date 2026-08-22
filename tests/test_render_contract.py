"""Regression tests for the rendered bundle and the object field vocabulary.

These cover three defects found in 0.8.0:
  1. CAMPAIGN_PROMPT.md rendered structured objects as raw JSON blobs.
  2. A successful finalize mutated `status`, which was inside the content digest,
     so the render invalidated the very reviews that authorized it.
  3. `add` silently accepted misspelled field names, which then failed validation
     under their correct names while the wrong keys persisted in canonical state.
"""

import argparse
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from common import ROOT, engine, complete_state, add_passing_reviews

ENGINE = ROOT / "rescamp/scripts/rescamp.py"


def render(state):
    validation = engine.validate_state(state, include_reviews=True)
    return engine.render_campaign_prompt(state, "EXECUTION-READY"), validation


class RenderContractTests(unittest.TestCase):
    def test_campaign_prompt_contains_no_raw_json_blobs(self):
        prompt, _ = render(add_passing_reviews(complete_state()))
        offenders = [line for line in prompt.splitlines() if ":**" in line and line.rstrip().endswith("}")]
        self.assertEqual(offenders, [], f"raw JSON leaked into the campaign prompt: {offenders[:3]}")
        self.assertNotIn('{"', prompt)

    def test_campaign_prompt_contains_no_python_reprs(self):
        state = add_passing_reviews(complete_state())
        prompt, _ = render(state)
        roadmap = engine.render_roadmap(state, "EXECUTION-READY")
        for name, text in (("prompt", prompt), ("roadmap", roadmap)):
            self.assertNotIn("['", text, f"python list repr leaked into the {name}")
            self.assertNotIn("{'", text, f"python dict repr leaked into the {name}")

    def test_inquiry_fields_survive_rendering(self):
        """Every field of a validated inquiry must reach the rendered prompt."""
        state = add_passing_reviews(complete_state())
        inquiry = state["campaign"]["inquiries"][0]
        prompt, _ = render(state)
        for key in ("question_or_claim", "importance", "verification_or_adjudication", "reporting_rule"):
            self.assertIn(str(inquiry[key]), prompt, f"inquiry field {key} was dropped by the renderer")
        for value in inquiry["admissible_support"] + inquiry["counterevidence_or_rival"]:
            self.assertIn(value, prompt, "inquiry evidence list was dropped by the renderer")

    def test_incomplete_object_is_flagged_not_dumped(self):
        state = complete_state()
        del state["campaign"]["inquiries"][0]["reporting_rule"]
        prompt, _ = render(state)
        self.assertIn("INCOMPLETE", prompt)
        self.assertNotIn('{"', prompt)


class DigestStabilityTests(unittest.TestCase):
    def test_status_is_outside_the_content_digest(self):
        state = complete_state()
        before = engine.content_digest(state)
        state["status"] = "execution-ready"
        self.assertEqual(before, engine.content_digest(state))

    def test_finalize_does_not_invalidate_its_own_reviews(self):
        """finalize -> audit --strict -> finalize must all succeed on unchanged content."""
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = Path(temp) / "campaign"
            for rel in ("state", "working", "working/review_packets", "outputs", "artifacts"):
                (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
            state = add_passing_reviews(complete_state())
            engine.write_json(campaign_dir / engine.STATE_REL, state)

            first = engine.render_outputs(campaign_dir, engine.load_state(campaign_dir))
            self.assertEqual(first["status"], "EXECUTION-READY", first["validation"]["errors"])

            after = engine.load_state(campaign_dir)
            self.assertTrue(
                engine.validate_state(after, include_reviews=True)["execution_ready"],
                "rendering invalidated the reviews that authorized it",
            )
            self.assertEqual(after["status"], "execution-ready")

            snapshot = json.loads((campaign_dir / "outputs/campaign.json").read_text())
            self.assertEqual(snapshot["status"], after["status"], "snapshot disagrees with canonical state")

            second = engine.render_outputs(campaign_dir, engine.load_state(campaign_dir))
            self.assertEqual(second["status"], "EXECUTION-READY")

    def test_missing_required_pilot_is_plan_ready_but_execution_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = Path(temp) / "campaign"
            for rel in ("state", "working", "working/review_packets", "outputs", "artifacts"):
                (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
            state = add_passing_reviews(complete_state("observational", "high-assurance"))
            state["assurance"]["pilot"] = {}
            engine.write_json(campaign_dir / engine.STATE_REL, state)
            result = engine.render_outputs(campaign_dir, state)
            self.assertEqual(result["status"], "PLAN-READY; EXECUTION BLOCKED")
            self.assertEqual(engine.load_state(campaign_dir)["status"], "plan-ready-execution-blocked")


class ReviewIngestTests(unittest.TestCase):
    def _record(self, state, **overrides):
        record = {
            "role": engine.PROFILES[state["profile"]]["review_roles"][0],
            "reviewer_id": "reviewer-1", "mode": "separate-session", "verdict": "pass",
            "content_digest": engine.content_digest(state),
            "rubric_digest": engine.rubric_digest(state["profile"]),
            "summary": "No blocking defect found.", "findings": [],
            "execution_evidence": {"executor_id": "session-a", "started_at": engine.now_iso(),
                                   "completed_at": engine.now_iso()},
        }
        record.update(overrides)
        return record

    def test_clean_review_with_no_findings_is_accepted(self):
        """A reviewer that found nothing must not have to invent a filler finding."""
        state = complete_state()
        self.assertEqual(engine.review_record_errors(self._record(state)), [])

    def test_absent_findings_key_is_still_rejected(self):
        state = complete_state()
        record = self._record(state)
        del record["findings"]
        self.assertIn("missing findings", engine.review_record_errors(record))

    def test_malformed_findings_are_rejected(self):
        state = complete_state()
        bad = self._record(state, findings=[{"severity": "catastrophic", "action": "agent-fix", "description": "x"}])
        self.assertTrue(any("severity" in item for item in engine.review_record_errors(bad)))
        self.assertEqual(engine.review_record_errors(self._record(state, verdict="maybe"))[0], "invalid verdict")


class BundleContentTests(unittest.TestCase):
    def test_task_brief_instantiates_real_work_units(self):
        """A generic stub would strip a delegated worker of its real prohibitions."""
        state = complete_state()
        state["campaign"]["work_units"] = [{
            "id": "wu1", "objective": "Code the interview set",
            "authoritative_inputs": ["transcripts@hash"], "permitted_actions": ["Run the coding pass"],
            "prohibited_actions": ["Do not send identifying text to a hosted model"],
            "outputs": ["codes.json"], "acceptance_test": "Two coders agree above threshold",
            "resource_ceiling": "4 days", "retry_policy": "One retry", "escalation": "Escalate to the PI",
        }]
        brief = engine.task_brief_template(state)
        self.assertIn("Do not send identifying text to a hosted model", brief)
        self.assertIn("wu1", brief)
        self.assertNotIn("<one objective>", brief)

    def test_kickoff_carries_first_gate_and_backlog(self):
        state = complete_state()
        kickoff = engine.render_kickoff(state, "EXECUTION-READY")
        self.assertIn(state["campaign"]["kickoff"]["command"], kickoff)
        self.assertIn(state["campaign"]["kickoff"]["first_gate_id"], kickoff)
        for item in state["campaign"]["kickoff"]["initial_backlog"]:
            self.assertIn(item, kickoff)

    def test_long_campaign_outputs_carry_checkpoint_and_amendment_protocol(self):
        state = complete_state()
        prompt = engine.render_campaign_prompt(state, "EXECUTION-READY")
        roadmap = engine.render_roadmap(state, "EXECUTION-READY")
        runbook = engine.runbook(state)

        self.assertIn(state["campaign"]["gates"][0]["checkpoint_review"], prompt)
        self.assertIn(state["campaign"]["gates"][0]["checkpoint_review"], roadmap)
        for text in (prompt, runbook):
            self.assertIn(engine.content_digest(state), text)
            self.assertIn("at most three material findings", text)
            self.assertIn("Methodological", text)
            self.assertIn("Constitutional", text)
            self.assertIn("older digest is stale", text)

    def test_short_campaign_omits_the_large_checkpoint_review_protocol(self):
        state = complete_state()
        for gate in state["campaign"]["gates"]:
            gate.pop("checkpoint_review", None)

        protocol = engine.plan_continuity_protocol(state)

        self.assertIn(engine.content_digest(state), protocol)
        self.assertIn("older digest is stale", protocol)
        self.assertNotIn("eight major execution stages", protocol)
        self.assertNotIn("at most three material findings", protocol)

    def test_kickoff_carries_the_first_gates_checkpoint_review(self):
        """The kickoff exists so execution starts without rereading the plan.

        Omitting `checkpoint_review` let the first gate look executable without the
        independent review it requires — the one artifact where that omission is
        least recoverable, because it is the only one an executor may have read.
        """
        state = complete_state()
        review = state["campaign"]["gates"][0]["checkpoint_review"]
        self.assertIn(review, engine.render_kickoff(state, "EXECUTION-READY"))

        for gate in state["campaign"]["gates"]:
            gate.pop("checkpoint_review", None)
        self.assertNotIn("Independent checkpoint review",
                         engine.render_kickoff(state, "EXECUTION-READY"),
                         "a gate without a checkpoint review must not grow an empty heading")

    def test_kickoff_renders_every_gate_criterion_at_the_same_level(self):
        """All criteria are siblings; none is a sub-point of the first."""
        state = complete_state()
        state["campaign"]["gates"][0]["criteria"] = ["first criterion", "second criterion"]
        first_gate = engine.render_kickoff(state, "EXECUTION-READY").split("## First gate", 1)[1]
        for criterion in ("first criterion", "second criterion"):
            self.assertIn(f"- {criterion}", first_gate)
            self.assertNotIn(f"  - {criterion}", first_gate,
                             "a later criterion must not be indented under the first")

    def test_the_finding_cap_requires_disclosure_rather_than_silent_truncation(self):
        """A cap that hides its own truncation reports three findings as a clean result."""
        protocol = engine.plan_continuity_protocol(complete_state())
        self.assertIn("at most three material findings", protocol)
        for obligation in ("returns `block`", "how many it found", "highest severity",
                           "never reported as a clean result"):
            self.assertIn(obligation, protocol,
                          f"the cap must oblige the reviewer to disclose: {obligation!r}")
        self.assertIn("escalate any remaining blocker to the gate owner", protocol,
                      "two exhausted rounds must name an escalation target, not a passive")

    def test_claims_matrix_includes_inquiries(self):
        state = complete_state()
        rows = engine.claims_evidence_matrix(state)["rows"]
        kinds = {row["kind"] for row in rows}
        self.assertIn("inquiry", kinds, "inquiries carry this matrix's columns and must appear")
        self.assertIn(state["campaign"]["inquiries"][0]["question_or_claim"],
                      [row["statement"] for row in rows])

    def test_prompt_discloses_empty_sections_and_challenge_level(self):
        state = complete_state()
        state["campaign"]["tools"] = []
        state["campaign"]["canaries"] = []
        prompt = engine.render_campaign_prompt(state, "EXECUTION-READY")
        self.assertIn("production tools", prompt)
        self.assertIn("not external validation", prompt)

    def test_prompt_reports_digest_bound_pilot_status(self):
        state = add_passing_reviews(complete_state("observational", "high-assurance"))
        prompt = engine.render_campaign_prompt(state, "EXECUTION-READY")
        self.assertIn("**Pilot:** passed", prompt)
        self.assertIn("one representative item", prompt)
        self.assertIn(state["assurance"]["pilot"]["content_digest"], prompt)
        self.assertNotIn("No pilot run is recorded", prompt)


class ObjectVocabularyTests(unittest.TestCase):
    def test_specs_accept_every_field_used_by_a_valid_campaign(self):
        """A spec that rejects a legitimate field would make `add` unusable."""
        state = complete_state()
        for path, spec in engine.OBJECT_SPECS.items():
            items = engine.get_by_path(state, path) if path.startswith("campaign.") else state.get(path, [])
            for item in items or []:
                if not isinstance(item, dict):
                    continue
                unknown = sorted(set(item) - engine.allowed_keys(spec))
                self.assertEqual(unknown, [], f"{path} spec rejects valid field(s) {unknown}")

    def test_declared_required_fields_are_enforced_by_the_validator(self):
        """Guards against OBJECT_SPECS drifting away from validate_state."""
        for path, spec in engine.OBJECT_SPECS.items():
            for field in spec["required"]:
                state = complete_state()
                items = engine.get_by_path(state, path)
                if not items:
                    continue
                items[0].pop(field, None)
                result = engine.validate_state(state, include_reviews=False)
                self.assertTrue(
                    any(field in item["message"] or path in item.get("path", "") for item in result["errors"]),
                    f"{path}.{field} is declared required but the validator does not enforce it",
                )

    def test_add_rejects_unknown_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            subprocess.run(
                [sys.executable, str(ENGINE), "init", "--goal", "A bounded question",
                 "--profile", "standard", "--archetypes", "evidence-synthesis", "--root", temp],
                check=True, capture_output=True, text=True,
            )
            campaign = next(Path(temp).iterdir())
            bad = subprocess.run(
                [sys.executable, str(ENGINE), "add", str(campaign), "campaign.inquiries",
                 "--json", json.dumps({"id": "q1", "question": "typo", "support": ["x"]})],
                capture_output=True, text=True,
            )
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn("unknown inquiry field", bad.stderr + bad.stdout)
            self.assertIn("question_or_claim", bad.stderr + bad.stdout, "error should name the correct field")

            good = subprocess.run(
                [sys.executable, str(ENGINE), "add", str(campaign), "campaign.inquiries",
                 "--json", json.dumps({"id": "q1", "question_or_claim": "correct"})],
                capture_output=True, text=True,
            )
            self.assertEqual(good.returncode, 0, good.stderr)

    def test_objects_reference_documents_every_field(self):
        """references/objects.md is what the agent reads; it must not drift from the spec."""
        doc = (ROOT / "rescamp/references/objects.md").read_text(encoding="utf-8")
        for path, spec in engine.OBJECT_SPECS.items():
            self.assertIn(f"`{path}`", doc, f"objects.md does not document {path}")
            for field in spec["required"]:
                self.assertIn(f"`{field}`", doc, f"objects.md omits required field {path}.{field}")

    def test_schema_command_documents_required_fields(self):
        result = subprocess.run(
            [sys.executable, str(ENGINE), "schema", "campaign.canaries"],
            capture_output=True, text=True, check=True,
        )
        payload = json.loads(result.stdout)
        self.assertIn("production_like_test", payload["required"])
        self.assertIn("downstream_acceptance", payload["all_keys"])



class CliSafetyTests(unittest.TestCase):
    """Regressions for silent-failure modes that an LLM driver hits constantly."""

    def _campaign(self, temp):
        subprocess.run(
            [sys.executable, str(ENGINE), "init", "--goal", "A bounded question",
             "--profile", "standard", "--archetypes", "evidence-synthesis", "--root", temp],
            check=True, capture_output=True, text=True,
        )
        return next(Path(temp).iterdir())

    def test_set_rejects_a_typod_path_instead_of_creating_junk(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign = self._campaign(temp)
            bad = subprocess.run(
                [sys.executable, str(ENGINE), "set", str(campaign), "campaign.evalation.criteria", '["x"]'],
                capture_output=True, text=True,
            )
            self.assertNotEqual(bad.returncode, 0, "a typo'd section name must not silently succeed")
            self.assertIn("evaluation", bad.stderr + bad.stdout, "error should list the real keys")
            state = json.loads((campaign / engine.STATE_REL).read_text())
            self.assertNotIn("evalation", state["campaign"])

            good = subprocess.run(
                [sys.executable, str(ENGINE), "set", str(campaign), "campaign.evaluation.criteria", '["x"]'],
                capture_output=True, text=True,
            )
            self.assertEqual(good.returncode, 0, good.stderr)

    def test_set_rejects_an_unknown_final_dict_field(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign = self._campaign(temp)
            bad = subprocess.run(
                [sys.executable, str(ENGINE), "set", str(campaign), "campaign.mission.scop", "Bounded"],
                capture_output=True, text=True,
            )
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn("scope", bad.stderr + bad.stdout)
            state = json.loads((campaign / engine.STATE_REL).read_text())
            self.assertNotIn("scop", state["campaign"]["mission"])

    def test_add_accepts_an_array_and_still_checks_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign = self._campaign(temp)
            ok = subprocess.run(
                [sys.executable, str(ENGINE), "add", str(campaign), "campaign.inquiries", "--json",
                 json.dumps([{"id": "q1", "question_or_claim": "one"}, {"id": "q2", "question_or_claim": "two"}])],
                capture_output=True, text=True,
            )
            self.assertEqual(ok.returncode, 0, ok.stderr)
            state = json.loads((campaign / engine.STATE_REL).read_text())
            self.assertEqual([item["id"] for item in state["campaign"]["inquiries"]], ["q1", "q2"])

            bad = subprocess.run(
                [sys.executable, str(ENGINE), "add", str(campaign), "campaign.inquiries", "--json",
                 json.dumps([{"id": "q3", "question_or_claim": "ok"}, {"id": "q4", "typo_field": "x"}])],
                capture_output=True, text=True,
            )
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn("item 1", bad.stderr + bad.stdout, "error should say which array item failed")

    def test_stale_review_error_names_the_mismatched_digest(self):
        state = complete_state()
        record = {
            "role": "methods-evidence", "reviewer_id": "r1", "mode": "sequential-pass", "verdict": "pass",
            "content_digest": "sha256:" + "0" * 64, "rubric_digest": engine.rubric_digest(state["profile"]),
            "summary": "s", "findings": [],
        }
        self.assertEqual(engine.review_record_errors(record), [])

    def test_rubric_digest_is_stable_across_tool_versions(self):
        original = engine.VERSION
        try:
            before = engine.rubric_digest("standard")
            engine.VERSION = original + "-patched"
            self.assertEqual(before, engine.rubric_digest("standard"),
                             "a patch release must not invalidate in-flight reviews")
        finally:
            engine.VERSION = original


class WorkUnitContractTests(unittest.TestCase):
    def test_work_units_keep_plan_dependencies_but_reject_removed_queue_fields(self):
        allowed = engine.allowed_keys(engine.OBJECT_SPECS["campaign.work_units"])
        self.assertIn("dependency_ids", allowed)
        for field in ("approval_ids", "external_action_ids", "retry_limit", "deadline_at"):
            self.assertNotIn(field, allowed)

class IntegrityClaimTests(unittest.TestCase):
    """The three claims a function review found outrunning the code."""

    def test_audit_detects_a_manifest_rewritten_to_match_a_tampered_artifact(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = Path(temp) / "campaign"
            for rel in ("state", "working", "working/review_packets", "outputs", "artifacts"):
                (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
            engine.write_json(campaign_dir / engine.STATE_REL, add_passing_reviews(complete_state()))
            engine.render_outputs(campaign_dir, engine.load_state(campaign_dir))

            target = campaign_dir / "outputs/CAMPAIGN_PROMPT.md"
            target.write_text(target.read_text() + "\nINJECTED\n", encoding="utf-8")
            new_digest = engine.sha256_bytes(target.read_bytes())
            manifest = campaign_dir / "outputs/MANIFEST.sha256"
            manifest.write_text("\n".join(
                f"{new_digest}  CAMPAIGN_PROMPT.md" if line.endswith("  CAMPAIGN_PROMPT.md") else line
                for line in manifest.read_text().splitlines() if line.strip()
            ) + "\n", encoding="utf-8")

            args = argparse.Namespace(campaign=str(campaign_dir), strict=True)
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    engine.cmd_audit(args)
            self.assertEqual(caught.exception.code, 5, "a self-consistent manifest must not pass audit")

    def test_pass_verdict_cannot_launder_a_critical_finding(self):
        state = add_passing_reviews(complete_state())
        self.assertTrue(engine.validate_state(state, include_reviews=True)["execution_ready"])
        state["reviews"]["records"][0]["findings"] = [{
            "severity": "critical", "action": "user-answer",
            "description": "No consent process is specified for minors.",
        }]
        result = engine.validate_state(state, include_reviews=True)
        self.assertFalse(result["execution_ready"])
        self.assertTrue(any(item["code"] == "review.unresolved_critical" for item in result["errors"]))

    def test_reviewer_cannot_accept_their_own_critical_risk(self):
        state = add_passing_reviews(complete_state())
        state["reviews"]["records"][0]["findings"] = [{
            "severity": "critical", "action": "accepted-risk",
            "description": "Bounded risk the reviewer recommends accepting.",
        }]
        result = engine.validate_state(state, include_reviews=True)
        self.assertFalse(result["execution_ready"])
        self.assertTrue(any(item["code"] == "risk_acceptance.missing" for item in result["errors"]))

    def test_separate_authority_can_accept_an_exact_digest_bound_finding(self):
        state = add_passing_reviews(complete_state())
        role = state["reviews"]["records"][0]["role"]
        finding = {
            "severity": "major", "action": "accepted-risk",
            "description": "A bounded residual risk remains after mitigation.",
        }
        state["reviews"]["records"][0]["findings"] = [finding]
        state["assurance"]["risk_acceptances"] = [{
            "finding_digest": engine.finding_digest(role, finding),
            "content_digest": engine.content_digest(state),
            "accepted_by": "principal-investigator", "authority": "campaign owner",
            "accepted_at": engine.now_iso(), "scope": "this campaign only",
            "evidence": "signed risk decision RA-1",
        }]
        result = engine.validate_state(state, include_reviews=True)
        self.assertTrue(result["execution_ready"], result["errors"])

    def test_claims_reach_the_execution_prompt(self):
        state = add_passing_reviews(complete_state())
        prompt = engine.render_campaign_prompt(state, "EXECUTION-READY")
        for claim in state["campaign"]["claims"]:
            self.assertIn(claim["statement"], prompt, "claims survived only in the JSON matrix")


class ReviewPacketScopeTests(unittest.TestCase):
    """Packets used to be byte-identical apart from the role string, so a methods
    reviewer read the runtime config and the interview transcript for no reason."""

    def test_packets_are_role_scoped_and_distinct(self):
        frozen = engine.substantive_state(complete_state("observational", "standard"))
        methods = engine.scope_packet_for_role(frozen, "methods-evidence")
        operations = engine.scope_packet_for_role(frozen, "operations-reproducibility")
        self.assertNotEqual(methods, operations)
        self.assertIn("inquiries", methods["campaign"])
        self.assertNotIn("runtime", methods["campaign"])
        self.assertIn("runtime", operations["campaign"])
        self.assertNotIn("inquiries", operations["campaign"])

    def test_every_campaign_section_is_reviewed_by_someone(self):
        """Scoping must not silently drop a section out of all review."""
        frozen = engine.substantive_state(complete_state("observational", "high-assurance"))
        covered = set()
        for role in engine.PROFILES["high-assurance"]["review_roles"]:
            covered |= set(engine.scope_packet_for_role(frozen, role)["campaign"])
        missing = sorted(set(frozen["campaign"]) - covered)
        self.assertEqual(missing, [], f"no reviewer sees {missing}")

    def test_unknown_role_receives_the_whole_campaign(self):
        frozen = engine.substantive_state(complete_state("observational", "scoped"))
        self.assertEqual(engine.scope_packet_for_role(frozen, "skeptical"), frozen)



class ApplyCommandTests(unittest.TestCase):
    """`apply` exists so an agent never has to choose between field checking and turns."""

    def _campaign(self, temp):
        subprocess.run(
            [sys.executable, str(ENGINE), "init", "--goal", "A bounded question",
             "--profile", "standard", "--archetypes", "evidence-synthesis", "--root", temp],
            check=True, capture_output=True, text=True,
        )
        return next(Path(temp).iterdir())

    def test_applies_several_sections_in_one_call(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign = self._campaign(temp)
            payload = {
                "campaign.mission": {"decision_or_purpose": "Decide", "scope": "Bounded",
                                     "completion_definition": "Memo"},
                "campaign.methods": [{"id": "m1", "purpose": "p", "outputs": ["o"], "limitations": ["l"]}],
            }
            result = subprocess.run(
                [sys.executable, str(ENGINE), "apply", str(campaign), "--json", json.dumps(payload)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            state = json.loads((campaign / engine.STATE_REL).read_text())
            self.assertEqual(state["campaign"]["mission"]["scope"], "Bounded")
            self.assertEqual(state["campaign"]["methods"][0]["id"], "m1")

    def test_one_bad_field_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign = self._campaign(temp)
            payload = {
                "campaign.methods": [{"id": "m1", "purpose": "p", "outputs": ["o"], "limitations": ["l"]}],
                "campaign.inquiries": [{"id": "q1", "question": "typo"}],
            }
            result = subprocess.run(
                [sys.executable, str(ENGINE), "apply", str(campaign), "--json", json.dumps(payload)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Nothing was written", result.stderr + result.stdout)
            state = json.loads((campaign / engine.STATE_REL).read_text())
            self.assertEqual(state["campaign"]["methods"], [],
                             "a partial write would leave the campaign in a state nobody intended")

    def test_unknown_dict_field_makes_apply_atomic(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign = self._campaign(temp)
            payload = {
                "campaign.methods": [{"id": "m1", "purpose": "p", "outputs": ["o"], "limitations": ["l"]}],
                "campaign.mission": {"decision_or_purpose": "Decide", "scop": "typo",
                                     "completion_definition": "Memo"},
            }
            result = subprocess.run(
                [sys.executable, str(ENGINE), "apply", str(campaign), "--json", json.dumps(payload)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Nothing was written", result.stderr + result.stdout)
            state = json.loads((campaign / engine.STATE_REL).read_text())
            self.assertEqual(state["campaign"]["methods"], [])
            self.assertEqual(state["campaign"]["mission"]["scope"], "")


if __name__ == "__main__":
    unittest.main()
