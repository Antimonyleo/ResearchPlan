"""Per-section review binding.

A review used to be bound to a digest of the whole campaign, so any change invalidated
every review — including changes to sections the reviewer never saw, and including
interview bookkeeping that touches no campaign content at all. Records are now bound to
the sections they actually reviewed, closed under cross-section references.

The security property must not weaken: a review is valid only while every section it is
responsible for is byte-identical to what it reviewed.
"""

import unittest

from common import engine, complete_state


def bind_reviews(state, roles=None):
    """Build records the way a review packet now hands them to a reviewer."""
    leaves = engine.section_digests(state)
    campaign = engine.substantive_state(state)["campaign"]
    records = []
    for index, role in enumerate(roles or engine.PROFILES[state["profile"]]["review_roles"], 1):
        records.append({
            "role": role, "reviewer_id": f"reviewer-{index}", "mode": "separate-session",
            "verdict": "pass", "content_digest": engine.content_digest(state),
            "rubric_digest": engine.rubric_digest(state["profile"]),
            "reviewed_sections": {name: leaves[name]
                                  for name in sorted(engine.invalidation_sections(role, campaign, leaves))},
            "summary": "No blocking defect found.", "findings": [],
            "execution_evidence": {"executor_id": f"executor-{index}",
                                   "started_at": engine.now_iso(), "completed_at": engine.now_iso()},
        })
    state["reviews"] = {"records": records}
    return state


def surviving(state):
    leaves = engine.section_digests(state)
    return sorted(r["role"] for r in state["reviews"]["records"] if engine.record_is_current(r, state, leaves))


class CoverageInvariantTests(unittest.TestCase):
    """If a section sits in no reviewer's scope, changing it invalidates nothing."""

    def test_every_campaign_section_is_covered_at_every_profile(self):
        for profile in engine.PROFILES:
            with self.subTest(profile=profile):
                state = complete_state("observational", profile)
                campaign = engine.substantive_state(state)["campaign"]
                covered = set()
                for role in engine.PROFILES[profile]["review_roles"]:
                    covered |= engine.invalidation_sections(role, campaign)
                missing = sorted(set(campaign) - covered)
                self.assertEqual(missing, [], f"{profile}: no reviewer is responsible for {missing}")

    def test_reference_targets_are_inside_the_referring_roles_scope(self):
        """A gate naming a method means a methods change must reach that reviewer."""
        state = complete_state("observational", "high-assurance")
        campaign = engine.substantive_state(state)["campaign"]
        for role in engine.PROFILES["high-assurance"]["review_roles"]:
            sections = engine.invalidation_sections(role, campaign)
            for name in sections:
                for target in engine.SECTION_REFERENCES.get(name, ()):
                    if target in campaign:
                        self.assertIn(target, sections,
                                      f"{role} reviews {name} which references {target}, but {target} "
                                      "is outside its invalidation set")


class StalenessScopeTests(unittest.TestCase):
    def test_all_reviews_valid_before_any_change(self):
        state = bind_reviews(complete_state())
        self.assertTrue(engine.validate_state(state, include_reviews=True)["execution_ready"])

    def test_interview_bookkeeping_invalidates_nothing(self):
        state = bind_reviews(complete_state())
        state["interview"]["turns"].append({
            "number": 99, "branch": "scope", "question": "Which years?", "answer_verbatim": "1990-2005",
            "normalized_decision": "1990-2005", "linked_dimensions": [], "decision_impact": "material",
            "answer_utility": "high", "asked_at": engine.now_iso(),
        })
        self.assertEqual(surviving(state), sorted(engine.PROFILES["standard"]["review_roles"]))
        self.assertTrue(engine.validate_state(state, include_reviews=True)["execution_ready"])

    def test_operations_repair_spares_the_methods_review(self):
        state = bind_reviews(complete_state())
        state["campaign"]["resources_dispatch"]["budgets"] = ["Revised ceiling"]
        self.assertEqual(surviving(state), ["methods-evidence"])

    def test_a_methods_repair_reaches_whoever_approved_the_dependent_gates(self):
        """Gate criteria name methods and inquiries by id, so an inquiry change is not
        confined to the methods reviewer. Correctness beats the saving here: the
        operations reviewer approved a gate whose meaning just moved."""
        state = bind_reviews(complete_state())
        state["campaign"]["inquiries"][0]["reporting_rule"] = "Revised reporting rule"
        self.assertEqual(surviving(state), [])

    def test_an_operations_only_repair_still_spares_methods(self):
        for section, field, value in (("resources_dispatch", "budgets", ["Revised ceiling"]),
                                      ("runtime", "recovery", "Revised recovery"),
                                      ("gates", None, None)):
            with self.subTest(section=section):
                state = bind_reviews(complete_state())
                if field is None:
                    state["campaign"]["gates"][0]["criteria"] = ["Revised gate criteria"]
                else:
                    state["campaign"][section][field] = value
                self.assertEqual(surviving(state), ["methods-evidence"])

    def test_declared_references_actually_cross_role_scopes(self):
        """A closure that adds nothing is not a safeguard, it is decoration."""
        state = complete_state("observational", "standard")
        campaign = engine.substantive_state(state)["campaign"]
        leaves = engine.section_digests(state)
        widened = []
        for role in engine.PROFILES["standard"]["review_roles"]:
            own = set(engine.ROLE_SCOPES[role]["sections"])
            closed = {n for n in engine.invalidation_sections(role, campaign, leaves) if not n.startswith("@")}
            widened.extend(sorted(closed - own))
        self.assertTrue(widened, "SECTION_REFERENCES adds no section to any role's scope; "
                                 "the closure is inert and cannot justify itself")

    def test_ethics_change_invalidates_a_reviewer_at_standard(self):
        """Regression: ethics_rights_safety was in no standard-profile scope."""
        state = bind_reviews(complete_state())
        state["campaign"]["ethics_rights_safety"]["constraints"] = ["Revised consent constraint"]
        self.assertNotEqual(surviving(state), sorted(engine.PROFILES["standard"]["review_roles"]),
                            "an ethics change must invalidate at least one review")

    def test_a_referenced_section_still_invalidates(self):
        """Methods references inquiries, so an inquiry change reaches the methods reviewer."""
        state = bind_reviews(complete_state())
        state["campaign"]["inquiries"][0]["admissible_support"] = ["different evidence"]
        self.assertNotIn("methods-evidence", surviving(state))


class RecordIntegrityTests(unittest.TestCase):
    def test_a_record_cannot_shrink_its_own_responsibility(self):
        """Dropping a section would make the record immune to changes in it."""
        state = bind_reviews(complete_state())
        record = state["reviews"]["records"][0]
        record["reviewed_sections"].pop("evaluation", None)
        self.assertFalse(engine.record_is_current(record, state),
                         "a record covering fewer sections than its role requires must be rejected")

    def test_a_record_cannot_pad_its_responsibility(self):
        state = bind_reviews(complete_state())
        record = state["reviews"]["records"][0]
        record["reviewed_sections"]["runtime"] = "sha256:" + "0" * 64
        self.assertFalse(engine.record_is_current(record, state))

    def test_a_forged_section_digest_is_rejected(self):
        state = bind_reviews(complete_state())
        record = state["reviews"]["records"][0]
        record["reviewed_sections"]["mission"] = "sha256:" + "0" * 64
        self.assertFalse(engine.record_is_current(record, state))

    def test_rubric_change_still_invalidates_everything(self):
        state = bind_reviews(complete_state())
        for record in state["reviews"]["records"]:
            record["rubric_digest"] = "sha256:" + "0" * 64
        self.assertEqual(surviving(state), [])

    def test_legacy_whole_campaign_records_still_work(self):
        """Records written before per-section binding keep the old all-or-nothing rule."""
        state = complete_state()
        legacy = {
            "role": "methods-evidence", "reviewer_id": "r1", "mode": "sequential-pass", "verdict": "pass",
            "content_digest": engine.content_digest(state),
            "rubric_digest": engine.rubric_digest(state["profile"]),
            "summary": "ok", "findings": [],
        }
        self.assertTrue(engine.record_is_current(legacy, state))
        state["campaign"]["mission"]["scope"] += " changed"
        self.assertFalse(engine.record_is_current(legacy, state))


class ReviewStatusTests(unittest.TestCase):
    def test_status_names_only_the_roles_that_must_re_run(self):
        state = bind_reviews(complete_state())
        state["campaign"]["resources_dispatch"]["budgets"] = ["Revised ceiling"]
        state["reviews"]["records"] = [r for r in state["reviews"]["records"]
                                       if engine.record_is_current(r, state)]
        current, needed = engine.review_status(state)
        self.assertEqual(current, ["methods-evidence"])
        self.assertEqual(needed, ["operations-reproducibility"])


class EventLedgerTests(unittest.TestCase):
    def test_every_event_records_the_section_digests(self):
        """Without these the log names the path that changed but not what it became, so a
        section emptied before any review left no recoverable trace."""
        import json
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temp:
            campaign_dir = Path(temp) / "campaign"
            for rel in ("state", "working", "outputs", "artifacts"):
                (campaign_dir / rel).mkdir(parents=True, exist_ok=True)
            state = complete_state()
            engine.write_json(campaign_dir / engine.STATE_REL, state)
            before = engine.section_digests(state)

            engine.save_state(campaign_dir, state, "test.baseline", {})
            state["campaign"]["inquiries"] = []
            engine.save_state(campaign_dir, state, "test.dropped", {"path": "campaign.inquiries"})

            events = [json.loads(line) for line in
                      (campaign_dir / engine.EVENTS_REL).read_text().splitlines() if line.strip()]
            self.assertTrue(all("section_digests" in e["payload"] for e in events))
            self.assertEqual(events[0]["payload"]["section_digests"]["inquiries"], before["inquiries"])
            self.assertNotEqual(events[1]["payload"]["section_digests"]["inquiries"], before["inquiries"],
                                "the deletion must be visible as a digest change in the log")


class BenchmarkHonestyTests(unittest.TestCase):
    """Statistical claims must not imply precision the design does not support."""

    def setUp(self):
        import importlib.util
        from common import ROOT
        spec = importlib.util.spec_from_file_location("bench", ROOT / "rescamp/scripts/benchmark.py")
        self.bench = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.bench)

    def test_no_interval_below_the_minimum_sample(self):
        for values in ([73.4], [73.4, 73.4], [50.0, 60.0, 70.0]):
            mean, lo, hi = self.bench.bootstrap_mean_ci(values, seed=1)
            self.assertIsNotNone(mean)
            self.assertIsNone(lo, f"n={len(values)} must not report an interval")
            self.assertIsNone(hi)

    def test_interval_returns_once_the_sample_is_adequate(self):
        mean, lo, hi = self.bench.bootstrap_mean_ci([10.0, 20.0, 30.0, 40.0, 50.0, 60.0], seed=1)
        self.assertIsNotNone(lo)
        self.assertLessEqual(lo, mean)
        self.assertLessEqual(mean, hi)

    def test_fixture_conditions_report_no_interval_at_all(self):
        """Fixture ratings are constants; the spread is scenario heterogeneity, not uncertainty."""
        values = [float(v) for v in range(40, 60)]
        mean, lo, hi = self.bench.bootstrap_mean_ci(values, seed=1, suppress=True)
        self.assertEqual(mean, round(sum(values) / len(values), 3))
        self.assertIsNone(lo)
        self.assertIsNone(hi)

    def test_explicit_branch_beats_keyword_routing(self):
        """`rival-readings` and `objections` match no keyword and silently route to scope."""
        self.assertEqual(self.bench.branch_for_dimension("rival-readings"), "scope-object")
        self.assertEqual(
            self.bench.branch_for_dimension("rival-readings", {"branch": "methods-comparison"}),
            "methods-comparison",
        )


if __name__ == "__main__":
    unittest.main()
