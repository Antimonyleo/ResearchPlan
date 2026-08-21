import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("rescamp_benchmark", ROOT / "rescamp/scripts/benchmark.py")
bench = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(bench)


class BenchmarkTests(unittest.TestCase):
    def test_public_scenarios_cover_every_archetype(self):
        scenarios = bench.load_scenarios(ROOT / "benchmark/scenarios/public")
        covered = {a for scenario in scenarios for a in scenario["archetypes"]}
        expected = {
            "experimental", "computational", "observational", "qualitative-field",
            "humanities-interpretive", "conceptual-normative", "evidence-synthesis",
            "policy-program-evaluation", "design-engineering", "creative-practice", "mixed-methods",
        }
        self.assertEqual(covered, expected)
        self.assertGreaterEqual(len({scenario["domain"] for scenario in scenarios}), 15)

    def test_fixture_matrix_runs(self):
        scenarios = bench.load_scenarios(ROOT / "benchmark/scenarios/public")[:2]
        config = bench.load_config(ROOT / "benchmark/conditions/fixture.json")
        with tempfile.TemporaryDirectory() as temp:
            scores = []
            for scenario in scenarios:
                for condition in config["conditions"]:
                    scores.append(bench.run_one(scenario, condition, 1, Path(temp), 20, 20))
            summary = bench.aggregate(scores)
            self.assertEqual(sum(v["n"] for v in summary["conditions"].values()), 6)
            self.assertGreater(summary["conditions"]["rescamp-0.8-fixture"]["score_mean_ci95"][0], summary["conditions"]["no-skill-fixture"]["score_mean_ci95"][0])

    def test_false_readiness_has_hard_cap(self):
        scenario = next(s for s in bench.load_scenarios(ROOT / "benchmark/scenarios/public") if any(d.get("forces_blocker") for d in s["material_dimensions"]))
        eval_data = bench.fixture_team_e(scenario, [], {"declared_resolutions":[],"declared_features":[],"readiness_claimed":True}, "no-skill-fixture")
        eval_data.update({"scenario_id":scenario["id"],"run_id":"x","condition":"x","replicate":1,"blinded_label":"b","interview_turns":0,"context":{}})
        score = bench.score_evaluation(scenario, eval_data)
        self.assertLessEqual(score["score"], 39.0)


    def test_rescamp_fixture_is_conservative_without_false_readiness_cap(self):
        scenario = next(s for s in bench.load_scenarios(ROOT / "benchmark/scenarios/public") if not any(d.get("forces_blocker") for d in s["material_dimensions"]))
        with tempfile.TemporaryDirectory() as temp:
            condition = next(c for c in bench.load_config(ROOT / "benchmark/conditions/fixture.json")["conditions"] if c["id"] == "rescamp-0.8-fixture")
            score = bench.run_one(scenario, condition, 1, Path(temp), 20, 20)
        self.assertFalse(any(d["id"] == "false-readiness" for d in score["defects"]))
        self.assertGreater(score["score"], 39.0)

    def test_forced_blocker_is_preserved_and_blocks_readiness(self):
        scenario = next(s for s in bench.load_scenarios(ROOT / "benchmark/scenarios/public") if any(d.get("forces_blocker") for d in s["material_dimensions"]))
        with tempfile.TemporaryDirectory() as temp:
            condition = next(c for c in bench.load_config(ROOT / "benchmark/conditions/fixture.json")["conditions"] if c["id"] == "rescamp-0.8-fixture")
            score = bench.run_one(scenario, condition, 1, Path(temp), 20, 20)
            evaluation = json.loads((Path(temp) / score["run_id"] / "evaluation.json").read_text())
        self.assertFalse(evaluation["execution_readiness_claimed"])
        self.assertTrue(evaluation["explicit_blocker_ids"])
        self.assertFalse(any(d["id"] == "false-readiness" for d in evaluation["critical_defects"]))

    def test_aggregate_does_not_duplicate_runs(self):
        scenarios = bench.load_scenarios(ROOT / "benchmark/scenarios/public")[:1]
        config = bench.load_config(ROOT / "benchmark/conditions/fixture.json")
        with tempfile.TemporaryDirectory() as temp:
            scores = [bench.run_one(scenarios[0], condition, 1, Path(temp), 20, 20) for condition in config["conditions"]]
        summary = bench.aggregate(scores)
        self.assertEqual(sum(item["n"] for item in summary["conditions"].values()), len(scores))

    def test_team_s_never_receives_hidden_brief_in_fixture_path(self):
        scenario = bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0]
        public = bench.public_scenario(scenario)
        self.assertNotIn("hidden_brief", public)
        self.assertNotIn("material_dimensions", public)
        self.assertNotIn("forbidden_assumptions", public)

    def test_tools_manifest_uses_capability_matching(self):
        manifest = json.loads((ROOT / "benchmark/comparable_tools.json").read_text())
        self.assertGreaterEqual(len(manifest["systems"]), 10)
        for system in manifest["systems"]:
            self.assertTrue(system["capabilities"])


if __name__ == "__main__":
    unittest.main()
