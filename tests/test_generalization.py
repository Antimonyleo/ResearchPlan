import re
import unittest
from common import engine, complete_state, add_passing_reviews


class GeneralizationTests(unittest.TestCase):
    def test_all_archetypes_validate_without_numeric_metrics(self):
        for archetype in sorted(engine.ARCHETYPES):
            with self.subTest(archetype=archetype):
                state = complete_state(archetype, "standard")
                result = engine.validate_state(state, include_reviews=False)
                self.assertTrue(result["valid"], result["errors"])
                self.assertEqual(state["intent_dimensions"][2]["status"], "not-applicable")

    def test_non_stem_adjudication_is_accepted(self):
        for archetype in ("humanities-interpretive", "conceptual-normative", "qualitative-field", "creative-practice"):
            state = complete_state(archetype, "scoped")
            state["campaign"]["evaluation"]["criteria"] = ["source criticism", "coherence", "rival interpretation", "scope conditions"]
            self.assertTrue(engine.validate_state(state, include_reviews=False)["valid"])

    def test_high_assurance_sequential_review_is_rejected(self):
        state = add_passing_reviews(complete_state("observational", "high-assurance"), mode="sequential-pass")
        result = engine.validate_state(state, include_reviews=True)
        self.assertFalse(result["valid"])
        self.assertTrue(any(item["code"] == "review.independence" for item in result["errors"]))

    def test_high_assurance_independent_review_passes(self):
        state = add_passing_reviews(complete_state("observational", "high-assurance"))
        result = engine.validate_state(state, include_reviews=True)
        self.assertTrue(result["valid"], result["errors"])

    def test_question_budget_is_enforced_not_merely_declared(self):
        """Exceeding the hard limit must fail validation unless the user authorized it."""
        for profile in ("scoped", "standard", "high-assurance"):
            with self.subTest(profile=profile):
                limits = engine.PROFILES[profile]
                self.assertLess(limits["soft"], limits["hard"], "soft stop must precede the hard stop")
                state = complete_state("observational", profile)
                turn = state["interview"]["turns"][0]
                state["interview"]["turns"] = [dict(turn, number=i + 1) for i in range(limits["hard"] + 1)]
                state["interview"]["hard_limit"] = limits["hard"]
                errors = engine.validate_state(state, include_reviews=False)["errors"]
                self.assertTrue(any(item["code"] == "interview.hard_limit" for item in errors),
                                f"{profile} hard limit is declared but not enforced")

                state["interview"]["extension_authorized"] = True
                errors = engine.validate_state(state, include_reviews=False)["errors"]
                self.assertFalse(any(item["code"] == "interview.hard_limit" for item in errors),
                                 "explicit user authorization must lift the hard limit")

    def test_skill_budget_table_matches_the_engine(self):
        """The table users read and the limit the engine enforces must not drift apart."""
        skill = (engine.SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        for profile in ("scoped", "standard", "high-assurance"):
            row = re.search(rf"^\| {profile} \|[^\n]*$", skill, re.MULTILINE)
            self.assertIsNotNone(row, f"SKILL.md has no budget row for {profile}")
            numbers = [int(value) for value in re.findall(r"\d+", row.group(0))]
            self.assertEqual(numbers[-1], engine.PROFILES[profile]["hard"],
                             f"SKILL.md hard stop for {profile} disagrees with the engine")
            self.assertEqual(numbers[-2], engine.PROFILES[profile]["soft"],
                             f"SKILL.md soft stop for {profile} disagrees with the engine")


if __name__ == "__main__":
    unittest.main()
