import importlib.util
import argparse
import contextlib
import copy
import io
import json
import os
import random
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("rescamp_benchmark", ROOT / "rescamp/scripts/benchmark.py")
bench = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(bench)


class BenchmarkTests(unittest.TestCase):
    def test_benchmark_runs_from_the_installed_skill_tree(self):
        with tempfile.TemporaryDirectory() as temp:
            installed = Path(temp) / "rescamp"
            shutil.copytree(ROOT / "rescamp", installed)
            result = subprocess.run(
                [sys.executable, str(installed / "scripts/benchmark.py"), "--version"],
                cwd=temp, text=True, capture_output=True, check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), bench.VERSION)

    def test_mode_profile_measures_a_materially_lighter_brief_state(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            bench.cmd_profile_modes(argparse.Namespace(iterations=2))
        profile = json.loads(output.getvalue())

        self.assertFalse(profile["quality_claim_allowed"])
        self.assertLess(profile["brief_state_fraction_of_full"], 0.65)
        self.assertEqual(profile["modes"]["brief"]["campaign_section_count"], 1)
        self.assertGreater(profile["modes"]["full"]["campaign_section_count"], 10)

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

    def test_scenario_validation_rejects_empty_or_unknown_archetypes(self):
        scenario = copy.deepcopy(bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0])
        scenario["archetypes"] = []
        self.assertTrue(any("archetypes" in item for item in bench.scenario_errors(scenario)))
        scenario["archetypes"] = ["not-a-real-archetype"]
        self.assertTrue(any("archetypes" in item for item in bench.scenario_errors(scenario)))

    def test_scenario_validation_rejects_ambiguous_run_id_delimiters(self):
        scenario = copy.deepcopy(bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0])
        scenario["id"] = "double--hyphen"
        self.assertTrue(any("id must" in item for item in bench.scenario_errors(scenario)))

    def test_validate_scenarios_help_describes_contract_and_release_schema_boundary(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit):
            bench.build_parser().parse_args(["validate-scenarios", "--help"])
        help_text = " ".join(output.getvalue().split())
        self.assertIn("scenario contract and semantic invariants", help_text)
        self.assertIn("release validation separately applies the JSON Schema", help_text)

    def test_scenario_validation_rejects_malformed_nested_values(self):
        baseline = bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0]
        cases = {
            "profile": [],
            "hidden_brief": [],
            "material_dimensions": "not-a-list",
            "forbidden_assumptions": ["not-an-object"],
            "critical_defects": [{"id": [], "description": "bad id", "severity": "major"}],
            "question_budget": {"soft": True, "hard": 8},
        }
        for field, value in cases.items():
            with self.subTest(field=field):
                scenario = copy.deepcopy(baseline)
                scenario[field] = value
                self.assertTrue(bench.scenario_errors(scenario))

    def test_scenario_loader_rejects_duplicate_run_id_inputs(self):
        scenario = copy.deepcopy(bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0])
        scenario.pop("_source", None)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "one.json").write_text(json.dumps(scenario), encoding="utf-8")
            (root / "two.json").write_text(json.dumps(scenario), encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "duplicate scenario IDs"):
                bench.load_scenarios(root)

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
            self.assertGreater(summary["conditions"]["rescamp-current-fixture"]["score_mean_ci95"][0], summary["conditions"]["no-skill-fixture"]["score_mean_ci95"][0])

    def test_write_json_does_not_follow_predictable_temp_symlinks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            destination = root / "nested" / "state.json"
            destination.parent.mkdir()
            outside = root / "outside.txt"
            outside.write_text("must remain unchanged", encoding="utf-8")
            predictable = destination.with_suffix(destination.suffix + ".tmp")
            predictable.symlink_to(outside)

            bench.write_json(destination, {"safe": True})

            self.assertEqual(outside.read_text(encoding="utf-8"), "must remain unchanged")
            self.assertTrue(predictable.is_symlink())
            self.assertEqual(json.loads(destination.read_text(encoding="utf-8")), {"safe": True})

    def test_false_readiness_has_hard_cap(self):
        scenario = next(s for s in bench.load_scenarios(ROOT / "benchmark/scenarios/public") if any(d.get("forces_blocker") for d in s["material_dimensions"]))
        eval_data = bench.fixture_team_e(scenario, [], {"declared_resolutions":[],"declared_features":[],"readiness_claimed":True}, "no-skill-fixture")
        eval_data.update({"scenario_id":scenario["id"],"run_id":"x","condition":"x","replicate":1,"blinded_label":"b","interview_turns":0,"context":{}})
        score = bench.score_evaluation(scenario, eval_data)
        self.assertLessEqual(score["score"], 39.0)

    def test_evaluation_validation_rejects_invalid_nested_values_and_unknown_ids(self):
        scenario = bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0]
        baseline = bench.fixture_team_e(
            scenario, [], {"declared_resolutions": [], "declared_features": [], "readiness_claimed": False},
            "rescamp-current-fixture",
        )
        baseline.update({
            "scenario_id": scenario["id"], "run_id": "run", "condition": "condition",
            "replicate": 1, "interview_turns": 0, "context": {},
        })
        cases = {
            "unknown asked ID": ("asked_dimension_turns", {"not-a-dimension": 1}),
            "negative diagnostic": ("question_diagnostics", dict(baseline["question_diagnostics"], correction_effort=-1)),
            "non-finite rating": ("ratings", dict(baseline["ratings"], **{bench.RATING_IDS[0]: float("nan")})),
            "malformed defect ID": ("critical_defects", [{"id": [], "severity": "major", "description": "bad"}]),
            "malformed defect severity": ("critical_defects", [{"id": "false-readiness", "severity": [], "description": "bad"}]),
            "malformed assumption severity": ("unsupported_assumptions", [{"statement": "bad", "severity": []}]),
            "wrong scenario": ("scenario_id", "another-scenario"),
            "boolean replicate": ("replicate", True),
        }
        for label, (field, value) in cases.items():
            with self.subTest(label=label):
                evaluation = copy.deepcopy(baseline)
                evaluation[field] = value
                self.assertTrue(bench.evaluation_errors(scenario, evaluation))

    def test_manual_score_cannot_promote_evaluator_claim_to_live_evidence(self):
        scenario = bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0]
        evaluation = bench.fixture_team_e(
            scenario, [],
            {"declared_resolutions": [], "declared_features": [], "readiness_claimed": False},
            "rescamp-current-fixture",
        )
        evaluation.update({
            "scenario_id": scenario["id"], "run_id": "manual-score", "condition": "manual",
            "replicate": 1, "interview_turns": 0, "context": {},
            "evidence_class": bench.LIVE_EVIDENCE_CLASS,
        })
        with tempfile.TemporaryDirectory() as temp:
            evaluation_path = Path(temp) / "evaluation.json"
            evaluation_path.write_text(json.dumps(evaluation), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                bench.cmd_score(argparse.Namespace(
                    scenario=scenario["_source"], evaluation=str(evaluation_path), output=None,
                ))
        score = json.loads(output.getvalue())
        self.assertEqual(score["evidence_class"], bench.UNSPECIFIED_EVIDENCE_CLASS)
    def test_manual_score_rejects_malformed_input_without_a_traceback(self):
        scenario = bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0]
        with tempfile.TemporaryDirectory() as temp:
            for index, (value, message) in enumerate((([], "must be a JSON object"),
                                                       ({}, "Invalid evaluation"))):
                with self.subTest(value=value):
                    evaluation_path = Path(temp) / f"evaluation-{index}.json"
                    evaluation_path.write_text(json.dumps(value), encoding="utf-8")
                    with self.assertRaisesRegex(SystemExit, message):
                        bench.cmd_score(argparse.Namespace(
                            scenario=scenario["_source"], evaluation=str(evaluation_path), output=None,
                        ))

    def test_manual_score_rejects_unreadable_or_invalid_json(self):
        scenario = bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0]
        with tempfile.TemporaryDirectory() as temp:
            invalid = Path(temp) / "invalid.json"
            invalid.write_text("{not json", encoding="utf-8")
            for path in (invalid, Path(temp) / "missing.json"):
                with self.subTest(path=path), self.assertRaisesRegex(
                    SystemExit, "Could not read score input"
                ):
                    bench.cmd_score(argparse.Namespace(
                        scenario=scenario["_source"], evaluation=str(path), output=None,
                    ))


    def test_rescamp_fixture_is_conservative_without_false_readiness_cap(self):
        scenario = next(s for s in bench.load_scenarios(ROOT / "benchmark/scenarios/public") if not any(d.get("forces_blocker") for d in s["material_dimensions"]))
        with tempfile.TemporaryDirectory() as temp:
            condition = next(c for c in bench.load_config(ROOT / "benchmark/conditions/fixture.json")["conditions"] if c["id"] == "rescamp-current-fixture")
            score = bench.run_one(scenario, condition, 1, Path(temp), 20, 20)
        self.assertFalse(any(d["id"] == "false-readiness" for d in score["defects"]))
        self.assertGreater(score["score"], 39.0)

    def test_forced_blocker_is_preserved_and_blocks_readiness(self):
        scenario = next(s for s in bench.load_scenarios(ROOT / "benchmark/scenarios/public") if any(d.get("forces_blocker") for d in s["material_dimensions"]))
        with tempfile.TemporaryDirectory() as temp:
            condition = next(c for c in bench.load_config(ROOT / "benchmark/conditions/fixture.json")["conditions"] if c["id"] == "rescamp-current-fixture")
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
        with self.assertRaisesRegex(RuntimeError, "duplicate run identity"):
            bench.aggregate(scores + [scores[0]])

    def test_run_rejects_an_existing_run_identity(self):
        scenario = bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0]
        condition = bench.load_config(ROOT / "benchmark/conditions/fixture.json")["conditions"][0]
        with tempfile.TemporaryDirectory() as temp:
            bench.run_one(scenario, condition, 1, Path(temp), 20, 20)
            with self.assertRaisesRegex(RuntimeError, "already exists"):
                bench.run_one(scenario, condition, 1, Path(temp), 20, 20)

    def test_team_s_never_receives_hidden_brief_in_fixture_path(self):
        scenario = bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0]
        public = bench.public_scenario(scenario)
        self.assertNotIn("hidden_brief", public)
        self.assertNotIn("material_dimensions", public)
        self.assertNotIn("forbidden_assumptions", public)

    def test_fixture_user_keeps_private_dimension_ids_out_of_visible_prose(self):
        scenario = copy.deepcopy(bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0])
        dimension = scenario["material_dimensions"][0]
        dimension["id"] = "private-dimension-sentinel"
        dimension["branch"] = "decision-purpose"
        answer = bench.fixture_team_u(
            scenario,
            {"branch": "decision-purpose"},
            [{"role": "user", "message": scenario["initial_request"]}],
        )
        self.assertNotIn("private-dimension-sentinel", answer["message"])
        self.assertEqual(answer["answered_dimension_ids"], ["private-dimension-sentinel"])

    def test_multiturn_team_s_capture_contains_only_public_conversation(self):
        scenario = copy.deepcopy(bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0])
        scenario["id"] = "capture-boundary"
        scenario["hidden_brief"]["facts"]["private_sentinel"] = "HIDDEN-BRIEF-SENTINEL"
        scenario["material_dimensions"][0].update({
            "id": "PRIVATE-DIMENSION-SENTINEL",
            "branch": "decision-purpose",
        })
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            capture = root / "team-s-inputs.jsonl"
            adapter = root / "capture_team_s.py"
            adapter.write_text(
                "import json,sys\n"
                "from pathlib import Path\n"
                "payload=json.loads(sys.stdin.read())\n"
                "with Path(sys.argv[1]).open('a',encoding='utf-8') as f: f.write(json.dumps(payload)+'\\n')\n"
                "asks=sum(e.get('role')=='assistant' and e.get('action')=='ask' for e in payload['history'])\n"
                "if asks < 2:\n"
                " print(json.dumps({'action':'ask','message':'Please clarify the next decision.','branch':['decision-purpose','scope-object'][asks],'question_count':1,'usage':{'tokens':1,'cost_usd':0.01}}))\n"
                "else:\n"
                " print(json.dumps({'action':'final','message':'Draft complete.','declared_resolutions':[],'declared_blockers':[],'declared_features':[],'readiness_claimed':False,'usage':{'tokens':1,'cost_usd':0.01}}))\n",
                encoding="utf-8",
            )
            condition = {
                "id": "capture-condition",
                "adapter": "external-command",
                "command": f"{sys.executable} {adapter} {capture}",
                "user_adapter": f"{sys.executable} {ROOT / 'benchmark/adapters/fixture_team_u.py'}",
                "evaluator_adapter": f"{sys.executable} {ROOT / 'benchmark/adapters/fixture_team_e.py'}",
                "model_id": "fixture", "host_version": "fixture", "capabilities": ["elicitation"],
            }
            score = bench.run_one(scenario, condition, 1, root / "runs", 20, 5)
            captured = capture.read_text(encoding="utf-8")
            for secret in (
                "HIDDEN-BRIEF-SENTINEL", "PRIVATE-DIMENSION-SENTINEL",
                "answered_dimension_ids", "blocker_ids", "fixture_team_u.py", "fixture_team_e.py",
            ):
                self.assertNotIn(secret, captured)
            run_dir = root / "runs" / score["run_id"]
            public_transcript = json.loads((run_dir / "transcript.json").read_text())
            self.assertFalse(any("answered_dimension_ids" in event for event in public_transcript))
            evaluator_transcript = json.loads((run_dir / "evaluator_transcript.json").read_text())
            self.assertTrue(any("answered_dimension_ids" in event for event in evaluator_transcript))
            calls = json.loads((run_dir / "adapter_calls.json").read_text())
            self.assertEqual([item["sequence"] for item in calls], list(range(1, len(calls) + 1)))
            self.assertEqual({item["role"] for item in calls}, {"team_s", "team_u", "team_e"})
            self.assertTrue(all("stdout" in item and "stderr" in item for item in calls))
            evaluation = json.loads((run_dir / "evaluation.json").read_text())
            self.assertEqual(evaluation["context"]["tokens"], 3.0)
            self.assertEqual(evaluation["context"]["usage_by_role"]["team_s"]["calls"], 3)

    def test_config_validation_rejects_malformed_nested_values(self):
        cases = [
            {"conditions": []},
            {"conditions": ["not-an-object"]},
            {"conditions": [{"id": [], "adapter": "fixture"}]},
            {"conditions": [{"id": "../../../escape", "adapter": "fixture"}]},
            {"conditions": [{"id": "double--hyphen", "adapter": "fixture"}]},
            {"conditions": [{"id": "x", "adapter": []}]},
            {"conditions": [{"id": "x", "adapter": "unknown", "command": "cmd"}]},
            {"conditions": [{"id": "x", "adapter": "external-command", "command": "cmd",
                             "user_adapter": "u", "evaluator_adapter": "e", "capabilities": "all"}]},
        ]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            for index, config in enumerate(cases):
                with self.subTest(index=index):
                    path.write_text(json.dumps(config), encoding="utf-8")
                    with self.assertRaises(SystemExit):
                        bench.load_config(path)

    def test_config_validation_fails_closed_without_jsonschema(self):
        config = {"conditions": [{"id": "x", "adapter": "external-command"}]}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            previous = sys.modules.get("jsonschema")
            sys.modules["jsonschema"] = None
            try:
                with self.assertRaisesRegex(SystemExit, "nonempty command"):
                    bench.load_config(path)
            finally:
                if previous is None:
                    sys.modules.pop("jsonschema", None)
                else:
                    sys.modules["jsonschema"] = previous

    def test_live_evidence_is_downgraded_when_matched_controls_are_not_enforced(self):
        config = {
            "conditions": [{
                "id": "live-a", "adapter": "external-command", "command": "team-s",
                "user_adapter": "team-u", "evaluator_adapter": "team-e",
                "model_id": "model", "host_version": "host", "capabilities": ["elicitation"],
            }]
        }
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            condition = bench.load_config(path)["conditions"][0]
        self.assertEqual(
            bench.evidence_class_for(condition, {"evidence_class": bench.LIVE_EVIDENCE_CLASS}),
            bench.UNMATCHED_LIVE_EVIDENCE_CLASS,
        )

    def test_live_evidence_requires_a_complete_identical_control_matrix(self):
        shared = {
            "adapter": "external-command", "command": "team-s", "user_adapter": "team-u",
            "evaluator_adapter": "team-e", "model_id": "exact-model", "host_version": "exact-host",
            "capabilities": ["campaign-compilation", "elicitation"],
            "skill_commit": "a" * 40,
        }
        config = {
            "matched_controls": {
                "same_model": True, "same_tools_permissions_corpus": True,
                "same_context_time_token_retry_budget": True, "fresh_sessions": True,
                "blinded_evaluation": True,
            },
            "conditions": [dict(shared, id="live-a"), dict(shared, id="live-b")],
        }
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            conditions = bench.load_config(path)["conditions"]
        self.assertTrue(all(item["_matched_controls"] for item in conditions))
        self.assertTrue(all(
            bench.evidence_class_for(item) == bench.LIVE_EVIDENCE_CLASS for item in conditions
        ))
        config["conditions"][1]["evaluator_adapter"] = "different-team-e"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            conditions = bench.load_config(path)["conditions"]
        self.assertFalse(any(item["_matched_controls"] for item in conditions))

    def test_aggregate_suppresses_intervals_without_verified_live_matched_controls(self):
        base = {
            "metrics": {"critical_defect_count": 0, "interview_turns": 1,
                        "interaction_burden_score": 80.0},
        }
        scores = []
        attempts = []
        for index in range(1, 6):
            scenario_id = f"scenario-{index}"
            for condition, evidence_class, score in (
                ("verified-a", bench.LIVE_EVIDENCE_CLASS, 60.0 + index),
                ("verified-b", bench.LIVE_EVIDENCE_CLASS, 55.0 + index),
                ("unspecified", bench.UNSPECIFIED_EVIDENCE_CLASS, 50.0 + index),
                ("unmatched", bench.UNMATCHED_LIVE_EVIDENCE_CLASS, 40.0 + index),
            ):
                scores.append(dict(
                    base, run_id=f"{scenario_id}-{condition}", scenario_id=scenario_id,
                    condition=condition, replicate=1, score=score,
                    evidence_class=evidence_class,
                ))
                attempts.append({
                    "scenario_id": scenario_id, "condition": condition, "replicate": 1,
                    "attempted": True, "succeeded": True,
                })

        summary = bench.aggregate(scores, attempts)

        self.assertIsNotNone(summary["conditions"]["verified-a"]["score_mean_ci95"][1])
        verified_pair = summary["pairwise_matched"]["verified-a minus verified-b"]
        self.assertIsNotNone(verified_pair["difference_mean_ci95"][1])
        self.assertIsNone(verified_pair["suppressed_because"])
        for condition in ("unspecified", "unmatched"):
            with self.subTest(condition=condition):
                self.assertEqual(
                    summary["conditions"][condition]["score_mean_ci95"],
                    [summary["conditions"][condition]["score_mean_ci95"][0], None, None],
                )
                self.assertTrue(summary["conditions"][condition]["interval_suppressed_because"])

        for pair_name, pair in summary["pairwise_matched"].items():
            if pair_name == "verified-a minus verified-b":
                continue
            self.assertIsNotNone(pair["difference_mean_ci95"][0])
            self.assertEqual(pair["difference_mean_ci95"][1:], [None, None])
            self.assertTrue(pair["suppressed_because"])

    def test_timeout_cleanup_ignores_process_group_exit_race(self):
        class AlreadyExitedProcess:
            pid = 123
            returncode = -9

            def __init__(self):
                self.kill_calls = 0
                self.communications = 0

            def communicate(self, input=None, timeout=None):
                self.communications += 1
                if timeout is not None:
                    raise subprocess.TimeoutExpired("adapter", timeout)
                return "", ""

            def kill(self):
                self.kill_calls += 1
                raise AssertionError("the already-exited process must not be killed again")

        process = AlreadyExitedProcess()
        with mock.patch.object(bench.subprocess, "Popen", return_value=process), \
                mock.patch.object(bench.os, "killpg", side_effect=ProcessLookupError):
            with self.assertRaisesRegex(RuntimeError, "timed out"):
                bench.call_adapter("adapter", {"request": "value"}, 1)
        self.assertEqual(process.kill_calls, 0)
        self.assertEqual(process.communications, 2)

    @unittest.skipUnless(os.name == "posix", "POSIX process groups are required")
    def test_timeout_cleanup_does_not_wait_for_an_escaped_descendant_pipe(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            script = root / "escaped_child.py"
            child_pid = root / "child.pid"
            child_code = (
                "import os,sys,time\n"
                "os.setsid()\n"
                "with open(sys.argv[1], 'w', encoding='utf-8') as handle:\n"
                "    handle.write(str(os.getpid()))\n"
                "time.sleep(30)\n"
            )
            script.write_text(
                "import subprocess,sys,time\n"
                f"subprocess.Popen([{sys.executable!r}, '-c', {child_code!r}, sys.argv[1]])\n"
                "for _ in range(100):\n"
                "    if __import__('os').path.exists(sys.argv[1]): break\n"
                "    time.sleep(0.01)\n"
                "time.sleep(30)\n",
                encoding="utf-8",
            )
            started = time.monotonic()
            try:
                with self.assertRaisesRegex(RuntimeError, "timed out"):
                    bench.call_adapter(
                        f"{sys.executable} {script} {child_pid}", {"request": "value"}, 1
                    )
            finally:
                if child_pid.is_file():
                    pid = int(child_pid.read_text(encoding="utf-8"))
                    deadline = time.monotonic() + 1.0
                    while Path(f"/proc/{pid}").exists() and time.monotonic() < deadline:
                        time.sleep(0.01)
                    try:
                        os.kill(pid, 0)
                    except (OSError, ValueError, ProcessLookupError):
                        pass
                    else:
                        self.fail("escaped adapter descendant survived timeout cleanup")
            self.assertLess(time.monotonic() - started, 3.0)

    @unittest.skipUnless(os.name == "posix" and sys.platform.startswith("linux"),
                         "Linux /proc process tracking is required")
    def test_timeout_cleanup_tracks_escaped_descendant_after_root_exits(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            script = root / "root_exits.py"
            child_pid = root / "child.pid"
            child_code = (
                "import os,sys,time\n"
                "os.setsid()\n"
                "with open(sys.argv[1], 'w', encoding='utf-8') as handle:\n"
                "    handle.write(str(os.getpid()))\n"
                "time.sleep(30)\n"
            )
            script.write_text(
                "import os,subprocess,sys,time\n"
                f"subprocess.Popen([{sys.executable!r}, '-c', {child_code!r}, sys.argv[1]])\n"
                "for _ in range(100):\n"
                "    if os.path.exists(sys.argv[1]): break\n"
                "    time.sleep(0.01)\n"
                "time.sleep(0.2)\n"
                "os._exit(0)\n",
                encoding="utf-8",
            )
            try:
                with self.assertRaisesRegex(RuntimeError, "timed out"):
                    bench.call_adapter(
                        f"{sys.executable} {script} {child_pid}", {"request": "value"}, 1
                    )
            finally:
                if child_pid.is_file():
                    pid = int(child_pid.read_text(encoding="utf-8"))
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except (OSError, ProcessLookupError):
                        pass

    def test_timeout_cleanup_uses_windows_process_tree_termination(self):
        process = mock.Mock(pid=321)
        with mock.patch.object(bench.os, "name", "nt"), \
                mock.patch.object(bench.subprocess, "run") as run:
            bench._terminate_adapter_tree(process)
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0], ["taskkill", "/PID", "321", "/T", "/F"])
        process.kill.assert_called_once_with()

    def test_parallel_fail_fast_collects_results_from_running_futures(self):
        scenarios = [{"id": "scenario", "title": "title", "domain": "domain",
                      "archetypes": ["experimental"], "profile": "profile",
                      "initial_request": "request"}]
        conditions = [{"id": ident} for ident in ("failure", "running", "queued")]
        running_started = threading.Event()

        def fake_run_one(scenario, condition, replicate, output_dir, timeout, max_turns):
            if condition["id"] == "failure":
                running_started.wait(1)
                raise RuntimeError("expected failure")
            if condition["id"] == "running":
                running_started.set()
                time.sleep(0.05)
            return {
                "run_id": f"{scenario['id']}-{condition['id']}-{replicate}",
                "scenario_id": scenario["id"], "condition": condition["id"],
                "replicate": replicate, "score": 50.0,
                "evidence_class": bench.SYNTHETIC_EVIDENCE_CLASS,
                "metrics": {"critical_defect_count": 0, "interview_turns": 1,
                            "interaction_burden_score": 80.0},
            }

        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "runs"
            args = argparse.Namespace(
                scenarios="unused", config="unused", output=str(output), replicates=1,
                jobs=2, max_turns=20, timeout=20, fail_fast=True,
            )
            with mock.patch.object(bench, "load_scenarios", return_value=scenarios), \
                    mock.patch.object(bench, "load_config", return_value={"conditions": conditions}), \
                    mock.patch.object(bench, "run_one", side_effect=fake_run_one), \
                    mock.patch.object(bench.secrets, "SystemRandom", return_value=mock.Mock(shuffle=lambda jobs: None)), \
                    contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    bench.cmd_run(args)

            self.assertEqual(raised.exception.code, 6)
            summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["score_count"], 1)
            self.assertEqual(summary["attempted_sample_count"], 2)
            self.assertEqual(summary["planned_sample_count"], 3)
            self.assertEqual(len(summary["attempts"]), 3)
            self.assertEqual(
                [item["condition"] for item in summary["attempts"] if not item["attempted"]],
                ["queued"],
            )
            self.assertEqual(summary["failures"][0]["condition"], "failure")
            self.assertEqual(summary["conditions"]["queued"]["planned_n"], 1)
            self.assertEqual(summary["conditions"]["queued"]["attempted_n"], 0)
            self.assertEqual(summary["conditions"]["queued"]["unstarted_n"], 1)
            self.assertFalse(summary["conditions"]["queued"]["complete"])

    def test_generated_live_matrix_uses_the_loadable_conservative_control_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "live.json"
            result = subprocess.run([
                sys.executable, str(ROOT / "scripts/create_benchmark_matrix.py"),
                "--condition", "rescamp-live=run-rescamp",
                "--condition", "neutral-live=run-neutral",
                "--user-adapter", "team-u", "--evaluator-adapter", "team-e",
                "--model-id", "model", "--host-version", "host", "--output", str(output),
            ], cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            raw = json.loads(output.read_text(encoding="utf-8"))
            self.assertIn("matched_controls", raw)
            self.assertNotIn("matched_controls_declared_by_operator", raw)
            self.assertTrue(raw["matched_controls"])
            self.assertTrue(all(value is False for value in raw["matched_controls"].values()))
            loaded = bench.load_config(output)
            for key in raw["matched_controls"]:
                raw["matched_controls"][key] = True
            output.write_text(json.dumps(raw), encoding="utf-8")
            placeholder_loaded = bench.load_config(output)
        self.assertFalse(any(item["_matched_controls"] for item in loaded["conditions"]))
        self.assertFalse(any(item["_matched_controls"]
                             for item in placeholder_loaded["conditions"]))

    def test_matrix_generator_rejects_an_invalid_condition_id(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "live.json"
            result = subprocess.run([
                sys.executable, str(ROOT / "scripts/create_benchmark_matrix.py"),
                "--condition", "../escaped=run-rescamp",
                "--user-adapter", "team-u", "--evaluator-adapter", "team-e",
                "--model-id", "model", "--host-version", "host", "--output", str(output),
            ], cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertFalse(output.exists())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("condition ID must", result.stderr)

        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "live.json"
            result = subprocess.run([
                sys.executable, str(ROOT / "scripts/create_benchmark_matrix.py"),
                "--condition", "double--hyphen=run-rescamp",
                "--user-adapter", "team-u", "--evaluator-adapter", "team-e",
                "--model-id", "model", "--host-version", "host", "--output", str(output),
            ], cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertFalse(output.exists())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("condition ID must", result.stderr)

    def test_team_e_receives_only_relevant_archetype_overlays_and_their_digest(self):
        scenario = copy.deepcopy(bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            team_s = root / "team_s.py"
            team_s.write_text(
                "import json\n"
                "print(json.dumps({'action':'final','message':'done','declared_resolutions':[],"
                "'declared_blockers':[],'declared_features':[],'readiness_claimed':False}))\n",
                encoding="utf-8",
            )
            capture = root / "team_e_payload.json"
            team_e = root / "team_e.py"
            team_e.write_text(
                "import json,sys\nfrom pathlib import Path\n"
                "p=json.loads(sys.stdin.read()); Path(sys.argv[1]).write_text(json.dumps(p))\n"
                "z={'repeated_question_count':0,'low_value_question_count':0,'multi_question_turn_count':0,'maximum_questions_in_turn':0,'correction_effort':0}\n"
                "r={d['id']:2 for d in p['rubric']['dimensions']}\n"
                "print(json.dumps({'asked_dimension_turns':{},'resolved_dimension_ids':[],'explicit_blocker_ids':[],'unsupported_assumptions':[],'question_diagnostics':z,'ratings':r,'critical_defects':[],'execution_readiness_claimed':False,'should_be_execution_ready':False,'required_feature_ids_present':[]}))\n",
                encoding="utf-8",
            )
            condition = {
                "id": "overlay-capture", "adapter": "external-command",
                "command": f"{sys.executable} {team_s}", "user_adapter": "unused",
                "evaluator_adapter": f"{sys.executable} {team_e} {capture}",
                "model_id": "fixture", "host_version": "fixture", "capabilities": [],
            }
            bench.run_one(scenario, condition, 1, root / "runs", 20, 2)
            payload = json.loads(capture.read_text())
        self.assertEqual(set(payload["archetype_overlays"]["overlays"]), set(scenario["archetypes"]))
        self.assertEqual(payload["archetype_overlays_digest"], bench.sha256_json(payload["archetype_overlays"]))
        self.assertRegex(payload["blinded_label"], r"^[0-9a-f]{32}$")
        self.assertNotIn(condition["id"], json.dumps(payload))

    def test_evaluator_receives_hashed_opaque_artifact_copies_not_condition_paths(self):
        scenario = copy.deepcopy(bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0])
        scenario["id"] = "artifact-blinding"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            team_s = root / "artifact_team_s.py"
            team_s.write_text(
                "import json,sys\nfrom pathlib import Path\n"
                "p=json.loads(sys.stdin.read()); a=Path(p['run_dir'])/'condition-secret-result.md'; a.write_text('frozen bytes')\n"
                "print(json.dumps({'action':'final','message':'done','declared_resolutions':[],'declared_blockers':[],'declared_features':[],'readiness_claimed':False,'artifacts':[str(a)]}))\n",
                encoding="utf-8",
            )
            capture = root / "team_e_payload.json"
            team_e = root / "team_e.py"
            team_e.write_text(
                "import json,sys\nfrom pathlib import Path\n"
                "p=json.loads(sys.stdin.read()); a=Path(p['artifact_manifest'][0]['path']); "
                "p['artifact_parent_entries']=[x.name for x in a.parent.parent.iterdir()]; "
                "Path(sys.argv[1]).write_text(json.dumps(p))\n"
                "z={'repeated_question_count':0,'low_value_question_count':0,'multi_question_turn_count':0,'maximum_questions_in_turn':0,'correction_effort':0}\n"
                "r={d['id']:2 for d in p['rubric']['dimensions']}\n"
                "print(json.dumps({'asked_dimension_turns':{},'resolved_dimension_ids':[],'explicit_blocker_ids':[],'unsupported_assumptions':[],'question_diagnostics':z,'ratings':r,'critical_defects':[],'execution_readiness_claimed':False,'should_be_execution_ready':False,'required_feature_ids_present':[]}))\n",
                encoding="utf-8",
            )
            condition = {
                "id": "condition-secret-label", "adapter": "external-command",
                "command": f"{sys.executable} {team_s}", "user_adapter": "unused",
                "evaluator_adapter": f"{sys.executable} {team_e} {capture}",
                "model_id": "fixture", "host_version": "fixture", "capabilities": [],
            }
            score = bench.run_one(scenario, condition, 1, root / "runs", 20, 2)
            payload = json.loads(capture.read_text())
            run_dir = root / "runs" / score["run_id"]
            manifest = json.loads((run_dir / "manifest.json").read_text())
            serialized = json.dumps(payload)
            self.assertNotIn(condition["id"], serialized)
            self.assertNotIn(str(run_dir), serialized)
            self.assertNotIn(run_dir.name, payload["artifact_parent_entries"])
            self.assertEqual(payload["final_response"]["artifacts"], ["artifact-001.md"])
            record = payload["artifact_manifest"][0]
            self.assertFalse(Path(record["path"]).exists(),
                             "the evaluator-only temporary path should be removed")
            staged = Path(manifest["evaluator_artifacts"][0]["staged_path"])
            self.assertTrue(staged.is_relative_to(run_dir))
            self.assertEqual(staged.read_bytes(), b"frozen bytes")
            self.assertEqual(staged.stat().st_mode & 0o222, 0)
            self.assertEqual(record["sha256"], bench.sha256_file(staged))
            self.assertEqual(
                manifest["evaluator_artifacts"][0]["staged_sha256_before"],
                manifest["evaluator_artifacts"][0]["staged_sha256_after"],
            )

    def test_evaluator_artifacts_must_exist_inside_the_run_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_dir = root / "runs" / "run"
            run_dir.mkdir(parents=True)
            outside = root / "outside.md"
            outside.write_text("not eligible", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "outside the run directory"):
                bench.stage_evaluator_artifacts(
                    {"artifacts": [str(outside)]}, run_dir, root / "runs", "candidate-a",
                )
            with self.assertRaisesRegex(RuntimeError, "missing or not a file"):
                bench.stage_evaluator_artifacts(
                    {"artifacts": ["missing.md"]}, run_dir, root / "runs", "candidate-b",
                )

    def test_evaluator_artifact_mutation_rejects_the_run(self):
        scenario = copy.deepcopy(bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0])
        scenario["id"] = "artifact-mutation"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            team_s = root / "artifact_team_s.py"
            team_s.write_text(
                "import json,sys\nfrom pathlib import Path\n"
                "p=json.loads(sys.stdin.read()); a=Path(p['run_dir'])/'result.md'; a.write_text('original')\n"
                "print(json.dumps({'action':'final','message':'done','declared_resolutions':[],'declared_blockers':[],'declared_features':[],'readiness_claimed':False,'artifacts':[str(a)]}))\n",
                encoding="utf-8",
            )
            team_e = root / "mutating_team_e.py"
            team_e.write_text(
                "import json,sys\nfrom pathlib import Path\n"
                "p=json.loads(sys.stdin.read()); a=Path(p['artifact_manifest'][0]['path']); a.chmod(0o644); a.write_text('mutated')\n"
                "z={'repeated_question_count':0,'low_value_question_count':0,'multi_question_turn_count':0,'maximum_questions_in_turn':0,'correction_effort':0}\n"
                "r={d['id']:2 for d in p['rubric']['dimensions']}\n"
                "print(json.dumps({'asked_dimension_turns':{},'resolved_dimension_ids':[],'explicit_blocker_ids':[],'unsupported_assumptions':[],'question_diagnostics':z,'ratings':r,'critical_defects':[],'execution_readiness_claimed':False,'should_be_execution_ready':False,'required_feature_ids_present':[]}))\n",
                encoding="utf-8",
            )
            condition = {
                "id": "mutation-condition", "adapter": "external-command",
                "command": f"{sys.executable} {team_s}", "user_adapter": "unused",
                "evaluator_adapter": f"{sys.executable} {team_e}",
                "model_id": "fixture", "host_version": "fixture", "capabilities": [],
            }
            with self.assertRaisesRegex(RuntimeError, "staged artifact changed"):
                bench.run_one(scenario, condition, 1, root / "runs", 20, 2)

    def test_team_s_run_dir_symlink_is_rejected_without_outside_writes(self):
        scenario = copy.deepcopy(bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0])
        scenario["id"] = "run-dir-boundary"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            outside = root / "outside"
            outside.mkdir()
            sentinel = outside / "sentinel.txt"
            sentinel.write_text("untouched", encoding="utf-8")
            team_s = root / "replace_run_dir.py"
            team_s.write_text(
                "import json,sys\n"
                "from pathlib import Path\n"
                "payload=json.loads(sys.stdin.read())\n"
                "run_dir=Path(payload['run_dir'])\n"
                "run_dir.rmdir()\n"
                "run_dir.symlink_to(Path(sys.argv[1]), target_is_directory=True)\n"
                "print(json.dumps({'action':'final','message':'done','declared_resolutions':[],"
                "'declared_blockers':[],'declared_features':[],'readiness_claimed':False}))\n",
                encoding="utf-8",
            )
            condition = {
                "id": "symlink-condition", "adapter": "external-command",
                "command": f"{sys.executable} {team_s} {outside}",
            }
            with self.assertRaisesRegex(RuntimeError, "must not be a symlink"):
                bench.run_one(scenario, condition, 1, root / "runs", 20, 2)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "untouched")
            self.assertFalse((outside / "evaluator-candidates").exists())
            self.assertFalse((root / "runs" / "run-dir-boundary--symlink-condition--r1").exists())

    def test_team_s_workspace_cannot_read_sibling_retained_transcripts(self):
        scenario = copy.deepcopy(bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0])
        scenario["id"] = "workspace-isolation"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "runs"
            sibling = output / "retained-sibling--condition--r1"
            sibling.mkdir(parents=True)
            (sibling / "evaluator_transcript.json").write_text(
                "SIBLING-PRIVATE-TRANSCRIPT", encoding="utf-8"
            )
            observed_workspace = root / "workspace.txt"
            team_s = root / "inspect_workspace.py"
            team_s.write_text(
                "import json,sys\n"
                "from pathlib import Path\n"
                "payload=json.loads(sys.stdin.read())\n"
                "workspace=Path(payload['run_dir'])\n"
                "Path(sys.argv[1]).write_text(str(workspace), encoding='utf-8')\n"
                "saw_sibling=any('SIBLING-PRIVATE-TRANSCRIPT' in p.read_text(encoding='utf-8')\n"
                "    for p in workspace.parent.rglob('evaluator_transcript.json'))\n"
                "message='saw sibling' if saw_sibling else 'isolated'\n"
                "print(json.dumps({'action':'final','message':message,'declared_resolutions':[],\n"
                "'declared_blockers':[],'declared_features':[],'readiness_claimed':False}))\n",
                encoding="utf-8",
            )
            condition = {
                "id": "rescamp-current-fixture", "adapter": "external-command",
                "command": f"{sys.executable} {team_s} {observed_workspace}",
            }

            score = bench.run_one(scenario, condition, 1, output, 20, 2)

            workspace = Path(observed_workspace.read_text(encoding="utf-8"))
            self.assertNotEqual(workspace.parent, output.resolve())
            transcript = json.loads(
                (output / score["run_id"] / "evaluator_transcript.json").read_text(encoding="utf-8")
            )
            self.assertEqual(transcript[1]["message"], "isolated")

    def test_manifest_hashes_every_persisted_run_file(self):
        scenario = bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0]
        condition = bench.load_config(ROOT / "benchmark/conditions/fixture.json")["conditions"][0]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            score = bench.run_one(scenario, condition, 1, root, 20, 20)
            run_dir = root / score["run_id"]
            manifest = json.loads((run_dir / "manifest.json").read_text())
            required = {
                "public_scenario.json", "transcript.json", "evaluator_transcript.json",
                "adapter_calls.json", "evaluation.json", "score.json",
            }
            persisted = {
                path.relative_to(run_dir).as_posix()
                for path in run_dir.rglob("*")
                if path.is_file() and path.name != "manifest.json"
            }
            self.assertTrue(required <= set(manifest["files"]))
            self.assertEqual(set(manifest["files"]), persisted)
            for name in persisted:
                path = run_dir / name
                self.assertEqual(manifest["files"][name]["bytes"], path.stat().st_size)
                self.assertEqual(manifest["files"][name]["sha256"], bench.sha256_file(path))

    def test_run_cli_rejects_nonpositive_execution_limits(self):
        base = [
            "run", "--scenarios", "scenarios", "--config", "config.json",
            "--output", "runs",
        ]
        for option in ("--replicates", "--jobs", "--max-turns", "--timeout"):
            with self.subTest(option=option), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    bench.build_parser().parse_args(base + [option, "0"])

    def test_turn_limit_is_a_failed_run_and_can_be_retried(self):
        scenario = bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0]
        condition = bench.load_config(ROOT / "benchmark/conditions/fixture.json")["conditions"][0]
        original = bench.fixture_team_s
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            try:
                bench.fixture_team_s = lambda *_args, **_kwargs: {
                    "action": "ask", "message": "Another question?",
                    "branch": "decision-purpose", "question_count": 1,
                }
                with self.assertRaisesRegex(RuntimeError, "exceeded the 1-turn"):
                    bench.run_one(scenario, condition, 1, root, 20, 1)
                expected = root / f"{scenario['id']}--{condition['id']}--r1"
                self.assertFalse(expected.exists())
            finally:
                bench.fixture_team_s = original
            score = bench.run_one(scenario, condition, 1, root, 20, 20)
            self.assertTrue((root / score["run_id"] / "score.json").is_file())

    def test_fixture_scores_feature_breadth_and_exact_blocker_prose(self):
        scenario = copy.deepcopy(next(
            item for item in bench.load_scenarios(ROOT / "benchmark/scenarios/public")
            if any(dim.get("forces_blocker") for dim in item["material_dimensions"])
        ))
        transcript = [
            {"role": "assistant", "action": "ask", "branch": "ethics-authority",
             "question_count": 1},
            {"role": "user", "message": bench.BLOCKER_PHRASE,
             "answered_dimension_ids": [],
             "blocker_ids": [next(dim["id"] for dim in scenario["material_dimensions"]
                              if dim.get("forces_blocker"))]},
        ]
        final = {
            "declared_resolutions": [],
            "declared_features": ["invented-feature"] * 20,
            "declared_blockers": ["some unrelated blocker"],
            "readiness_claimed": False,
        }

        evaluation = bench.fixture_team_e(
            scenario, transcript, final, "rescamp-current-fixture"
        )
        broad = bench.fixture_team_e(
            scenario, transcript,
            dict(final, declared_features=[
                "mission-scope", "inquiry-evidence", "frozen-evaluation",
                "stages-gates", "claims-traceability", "rights-approvals",
            ]),
            "rescamp-current-fixture",
        )

        self.assertLess(evaluation["ratings"]["operations"], broad["ratings"]["operations"])
        self.assertEqual(evaluation["required_feature_ids_present"], [])
        self.assertEqual(evaluation["explicit_blocker_ids"], [])
        self.assertTrue(any(
            item["id"] == "missing-explicit-blocker"
            for item in evaluation["critical_defects"]
        ))

    def test_scenario_branch_outside_the_interview_vocabulary_is_rejected(self):
        scenario = copy.deepcopy(next(
            item for item in bench.load_scenarios(ROOT / "benchmark/scenarios/public")
            if item["id"] == "ai-procurement-legal"
        ))
        target = next(dim for dim in scenario["material_dimensions"]
                      if dim["branch"] == "scope-object")
        matched_before = bench.fixture_team_u(
            scenario, {"branch": "scope-object"}, [],
        )["answered_dimension_ids"]
        target["branch"] = "scope-objct"

        errors = bench.scenario_errors(scenario)

        self.assertIn(target["id"], matched_before)
        self.assertNotIn(
            target["id"],
            bench.fixture_team_u(scenario, {"branch": "scope-object"}, [])["answered_dimension_ids"],
        )
        self.assertTrue(
            any("scope-objct" in error for error in errors), errors,
        )

    def test_every_asked_branch_is_in_the_scenario_branch_vocabulary(self):
        asked = {
            branch
            for profile in ("scoped", "standard", "high-assurance")
            for archetypes in ([], ["humanities-interpretive"])
            for branch, _ in bench.branch_questions(profile, archetypes)
        }

        self.assertTrue(asked)
        self.assertEqual(asked - set(bench.BRANCH_IDS), set())

    def test_confidence_bounds_do_not_depend_on_score_arrival_order(self):
        scores = []
        rng = random.Random(11)
        for scenario in range(6):
            for replicate in range(3):
                scores.append({
                    "run_id": f"s{scenario}-c-{replicate}", "scenario_id": f"s{scenario}",
                    "condition": "c", "replicate": replicate,
                    "score": 60.0 + rng.random() * 30.0,
                    "evidence_class": bench.LIVE_EVIDENCE_CLASS,
                    "metrics": {"critical_defect_count": 0, "interview_turns": 3,
                                "interaction_burden_score": 80.0},
                })
        attempts = [
            {"scenario_id": item["scenario_id"], "condition": "c",
             "replicate": item["replicate"], "succeeded": True}
            for item in scores
        ]
        shuffled = list(scores)
        random.Random(99).shuffle(shuffled)

        first = bench.aggregate(list(scores), list(attempts))
        second = bench.aggregate(shuffled, list(attempts))

        self.assertNotEqual([item["run_id"] for item in scores],
                            [item["run_id"] for item in shuffled])
        self.assertIsNotNone(first["conditions"]["c"]["score_mean_ci95"][1])
        self.assertEqual(first["conditions"]["c"]["score_mean_ci95"],
                         second["conditions"]["c"]["score_mean_ci95"])

    def test_context_usage_totals_report_the_system_under_test_only(self):
        scenario = bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0]
        usage = {"team_s": 100.0, "team_u": 40.0, "team_e": 5000.0}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            evaluation = bench.fixture_team_e(
                scenario, [], {"declared_resolutions": [], "declared_features": [],
                               "declared_blockers": [], "readiness_claimed": False},
                "rescamp-current-fixture",
            )
            (root / "evaluation.json").write_text(json.dumps(evaluation), encoding="utf-8")
            bodies = {
                "team_s": (
                    "history = payload['history']\n"
                    "asked = sum(1 for e in history if e.get('action') == 'ask')\n"
                    "body = ({'action': 'ask', 'message': 'One question?',\n"
                    "         'branch': 'decision-purpose', 'question_count': 1}\n"
                    "        if asked == 0 else\n"
                    "        {'action': 'final', 'message': 'done', 'declared_resolutions': [],\n"
                    "         'declared_features': [], 'declared_blockers': [],\n"
                    "         'readiness_claimed': False})\n"
                ),
                "team_u": "body = {'message': 'No stronger private constraint.'}\n",
                "team_e": f"body = json.load(open({str(root / 'evaluation.json')!r}))\n",
            }
            adapters = {}
            for role, body in bodies.items():
                script = root / f"{role}.py"
                script.write_text(
                    "import json, sys\n"
                    "payload = json.loads(sys.stdin.readline())\n"
                    + body
                    + f"body['usage'] = {{'tokens': {usage[role]}, "
                    f"'cost_usd': {usage[role] / 1000.0}}}\n"
                    "print(json.dumps(body))\n",
                    encoding="utf-8",
                )
                adapters[role] = f"{sys.executable} {script}"
            condition = {
                "id": "usage-condition", "adapter": "external-command",
                "command": adapters["team_s"],
                "user_adapter": adapters["team_u"],
                "evaluator_adapter": adapters["team_e"],
                "model_id": "fixture", "host_version": "fixture",
            }

            score = bench.run_one(scenario, condition, 1, root / "runs", 20, 5)
            context = json.loads(
                (root / "runs" / score["run_id"] / "evaluation.json").read_text(encoding="utf-8")
            )["context"]

        by_role = context["usage_by_role"]
        self.assertEqual(by_role["team_u"]["tokens"], usage["team_u"])
        self.assertEqual(by_role["team_e"]["tokens"], usage["team_e"])
        self.assertEqual(by_role["team_s"]["tokens"], usage["team_s"] * by_role["team_s"]["calls"])
        self.assertEqual(context["tokens"], by_role["team_s"]["tokens"])
        self.assertEqual(context["cost_usd"], by_role["team_s"]["cost_usd"])
        self.assertLess(
            context["tokens"],
            sum(item["tokens"] for item in by_role.values()),
            "the evaluator and hidden user must not inflate the system-under-test total",
        )

    def test_operations_rating_separates_the_skilled_and_bare_fixtures(self):
        scenario = bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0]
        conditions = {
            condition["id"]: condition
            for condition in bench.load_config(ROOT / "benchmark/conditions/fixture.json")["conditions"]
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skilled = bench.run_one(scenario, conditions["rescamp-current-fixture"], 1, root, 20, 20)
            bare = bench.run_one(scenario, conditions["no-skill-fixture"], 1, root, 20, 20)

        self.assertGreater(
            skilled["rubric_scores"]["operations"], bare["rubric_scores"]["operations"]
        )

    def test_scoring_failure_removes_the_partial_run_directory(self):
        scenario = bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0]
        condition = bench.load_config(ROOT / "benchmark/conditions/fixture.json")["conditions"][0]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with mock.patch.object(bench, "score_evaluation",
                                   side_effect=RuntimeError("unusable evaluation")):
                with self.assertRaisesRegex(RuntimeError, "unusable evaluation"):
                    bench.run_one(scenario, condition, 1, root, 20, 20)
            self.assertFalse((root / f"{scenario['id']}--{condition['id']}--r1").exists())

            score = bench.run_one(scenario, condition, 1, root, 20, 20)
            self.assertTrue((root / score["run_id"] / "score.json").is_file())

    @unittest.skipUnless(sys.platform.startswith("linux"), "PID identity is read from /proc")
    def test_recycled_descendant_pid_is_not_killed(self):
        survivor = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True,
        )
        self.addCleanup(survivor.wait)
        self.addCleanup(survivor.kill)
        proc = mock.Mock(pid=survivor.pid)

        with mock.patch.object(bench.os, "killpg"):
            bench._terminate_adapter_tree(proc, {survivor.pid: "0"})
        self.assertIsNone(survivor.poll())

        with mock.patch.object(bench.os, "killpg"):
            bench._terminate_adapter_tree(
                proc, {survivor.pid: bench._process_start_token(survivor.pid)}
            )
        self.assertIsNotNone(survivor.wait(timeout=5))

    def test_aggregate_suppresses_pairwise_effect_when_any_sample_failed(self):
        base = {
            "replicate": 1, "score": 50.0,
            "metrics": {"critical_defect_count": 0, "interview_turns": 1,
                        "interaction_burden_score": 80.0},
        }
        scores = [
            dict(base, run_id="s1-a", scenario_id="s1", condition="a"),
            dict(base, run_id="s2-a", scenario_id="s2", condition="a"),
            dict(base, run_id="s1-b", scenario_id="s1", condition="b"),
        ]
        attempts = [
            {"scenario_id": scenario, "condition": condition, "replicate": 1,
             "succeeded": not (scenario == "s2" and condition == "b")}
            for scenario in ("s1", "s2") for condition in ("a", "b")
        ]

        summary = bench.aggregate(scores, attempts)
        pair = summary["pairwise_matched"]["a minus b"]

        self.assertFalse(pair["complete_matched_matrix"])
        self.assertEqual(pair["difference_mean_ci95"], [None, None, None])
        self.assertEqual(summary["conditions"]["b"]["failure_rate"], 0.5)

    def test_compare_run_bundle_preserves_failed_attempts(self):
        score = {
            "run_id": "succeeded--condition-a--r1", "scenario_id": "succeeded",
            "condition": "condition-a", "replicate": 1, "score": 50.0,
            "metrics": {"critical_defect_count": 0, "interview_turns": 1,
                        "interaction_burden_score": 80.0},
        }
        summary = {
            "planned_sample_count": 2, "attempted_sample_count": 2,
            "score_count": 1,
            "job_order": [
                "succeeded--condition-a--r1", "failed--condition-a--r1",
            ],
            "attempts": [
                {"scenario_id": "succeeded", "condition": "condition-a", "replicate": 1,
                 "attempted": True, "succeeded": True},
                {"scenario_id": "failed", "condition": "condition-a", "replicate": 1,
                 "attempted": True, "succeeded": False},
            ],
            "failures": [{
                "scenario": "failed", "condition": "condition-a", "replicate": "1",
                "error": "adapter timed out",
            }],
        }
        with tempfile.TemporaryDirectory() as temp:
            run_output = Path(temp) / "run-output"
            run_output.mkdir()
            (run_output / "scores.json").write_text(json.dumps([score]), encoding="utf-8")
            (run_output / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                bench.cmd_compare(argparse.Namespace(inputs=[str(run_output)], output=None))
        result = json.loads(output.getvalue())
        condition = result["conditions"]["condition-a"]
        self.assertEqual(result["input_contract"], "run-output-bundle")
        self.assertTrue(result["attempts_known"])
        self.assertEqual(condition["n"], 1)
        self.assertEqual(condition["planned_n"], 2)
        self.assertEqual(condition["attempted_n"], 2)
        self.assertEqual(condition["unstarted_n"], 0)
        self.assertEqual(condition["failure_rate"], 0.5)
        self.assertFalse(condition["complete"])

    def test_compare_rejects_scores_json_without_run_summary(self):
        score = {
            "run_id": "ambiguous", "scenario_id": "scenario", "condition": "condition",
            "replicate": 1, "score": 50.0,
            "metrics": {"critical_defect_count": 0, "interview_turns": 1,
                        "interaction_burden_score": 80.0},
        }
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "scores.json"
            path.write_text(json.dumps([score]), encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "requires its sibling summary.json"):
                bench.cmd_compare(argparse.Namespace(inputs=[str(path)], output=None))

    def test_compare_all_failed_run_bundle_reports_failures_without_scores(self):
        summary = {
            "planned_sample_count": 1, "attempted_sample_count": 1, "score_count": 0,
            "job_order": ["failed--condition-a--r1"],
            "attempts": [{
                "scenario_id": "failed", "condition": "condition-a", "replicate": 1,
                "attempted": True, "succeeded": False,
            }],
            "failures": [{
                "scenario": "failed", "condition": "condition-a", "replicate": "1",
                "error": "adapter failed",
            }],
        }
        with tempfile.TemporaryDirectory() as temp:
            run_output = Path(temp) / "run-output"
            run_output.mkdir()
            (run_output / "scores.json").write_text("[]", encoding="utf-8")
            (run_output / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                bench.cmd_compare(argparse.Namespace(inputs=[str(run_output)], output=None))
        result = json.loads(output.getvalue())
        condition = result["conditions"]["condition-a"]
        self.assertEqual(condition["n"], 0)
        self.assertEqual(condition["planned_n"], 1)
        self.assertEqual(condition["attempted_n"], 1)
        self.assertEqual(condition["unstarted_n"], 0)
        self.assertEqual(condition["failure_rate"], 1.0)
        self.assertFalse(condition["complete"])

    def test_compare_run_bundle_preserves_unstarted_conditions(self):
        score = {
            "run_id": "started--condition-a--r1", "scenario_id": "started",
            "condition": "condition-a", "replicate": 1, "score": 50.0,
            "metrics": {"critical_defect_count": 0, "interview_turns": 1,
                        "interaction_burden_score": 80.0},
        }
        summary = {
            "planned_sample_count": 2, "attempted_sample_count": 1,
            "score_count": 1,
            "job_order": [
                "started--condition-a--r1", "queued--condition-b--r1",
            ],
            "attempts": [
                {"scenario_id": "started", "condition": "condition-a", "replicate": 1,
                 "attempted": True, "succeeded": True},
                {"scenario_id": "queued", "condition": "condition-b", "replicate": 1,
                 "attempted": False, "succeeded": False},
            ],
            "failures": [],
        }
        with tempfile.TemporaryDirectory() as temp:
            run_output = Path(temp) / "run-output"
            run_output.mkdir()
            (run_output / "scores.json").write_text(json.dumps([score]), encoding="utf-8")
            (run_output / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                bench.cmd_compare(argparse.Namespace(inputs=[str(run_output)], output=None))
        result = json.loads(output.getvalue())
        queued = result["conditions"]["condition-b"]
        self.assertEqual(queued["planned_n"], 1)
        self.assertEqual(queued["attempted_n"], 0)
        self.assertEqual(queued["unstarted_n"], 1)
        self.assertFalse(queued["complete"])
        self.assertFalse(result["pairwise_matched"]["condition-a minus condition-b"]["complete_matched_matrix"])

    def test_compare_accepts_legacy_summary_without_planned_metadata_conservatively(self):
        score = {
            "run_id": "legacy-run", "scenario_id": "scenario", "condition": "legacy",
            "replicate": 1, "score": 50.0,
            "metrics": {"critical_defect_count": 0, "interview_turns": 1,
                        "interaction_burden_score": 80.0},
        }
        legacy_summary = {
            "run_id": "legacy", "scenario_count": 1, "score_count": 1,
            "conditions": {"legacy": {"n": 1}}, "failures": [],
        }
        with tempfile.TemporaryDirectory() as temp:
            run_output = Path(temp) / "legacy-output"
            run_output.mkdir()
            (run_output / "scores.json").write_text(json.dumps([score]), encoding="utf-8")
            (run_output / "summary.json").write_text(json.dumps(legacy_summary), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                bench.cmd_compare(argparse.Namespace(inputs=[str(run_output)], output=None))
        result = json.loads(output.getvalue())
        condition = result["conditions"]["legacy"]
        self.assertEqual(result["input_contract"], "run-output-bundle")
        self.assertFalse(result["attempts_known"])
        self.assertIsNone(condition["planned_n"])
        self.assertFalse(condition["complete"])
        self.assertIsNone(condition["failure_rate"])

    def test_aggregate_rejects_duplicate_composite_samples(self):
        base = {
            "scenario_id": "s", "condition": "c", "replicate": 1, "score": 50.0,
            "metrics": {"critical_defect_count": 0, "interview_turns": 1,
                        "interaction_burden_score": 80.0},
        }
        with self.assertRaisesRegex(RuntimeError, "duplicate scenario/condition/replicate"):
            bench.aggregate([dict(base, run_id="one"), dict(base, run_id="two")])

    def test_config_rejects_variable_model_sentinel(self):
        config = {"conditions": [{
            "id": "live", "adapter": "external-command", "command": "s",
            "user_adapter": "u", "evaluator_adapter": "e",
            "model_id": "varies-record-per-run",
        }]}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "exact model identifier"):
                bench.load_config(path)

    def test_manual_compare_cannot_promote_score_claim_to_live_evidence(self):
        score = {
            "run_id": "manual-run", "scenario_id": "scenario", "condition": "manual",
            "replicate": 1, "score": 50.0, "evidence_class": bench.LIVE_EVIDENCE_CLASS,
            "metrics": {
                "critical_defect_count": 0, "interview_turns": 1,
                "interaction_burden_score": 100.0,
            },
        }
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "score.json"
            path.write_text(json.dumps(score), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                bench.cmd_compare(argparse.Namespace(inputs=[str(path)], output=None))
        summary = json.loads(output.getvalue())
        self.assertEqual(summary["evidence_class"], bench.UNSPECIFIED_EVIDENCE_CLASS)
        self.assertFalse(summary["attempts_known"])
        self.assertIsNone(summary["conditions"]["manual"]["failure_rate"])
        self.assertEqual(
            summary["conditions"]["manual"]["evidence_class"],
            bench.UNSPECIFIED_EVIDENCE_CLASS,
        )

    def test_manual_compare_rejects_malformed_scores_without_crashing(self):
        malformed = (
            ["not-an-object"],
            {"score": 1.0},
            {
                "run_id": "r", "scenario_id": "s", "condition": "c", "replicate": 1,
                "score": float("nan"),
                "metrics": {"critical_defect_count": 0, "interview_turns": 1,
                            "interaction_burden_score": 100.0},
            },
            {
                "run_id": "r", "scenario_id": "s", "condition": "c", "replicate": 1,
                "score": 1.0,
                "metrics": {"critical_defect_count": -1, "interview_turns": 1,
                            "interaction_burden_score": 100.0},
            },
        )
        with tempfile.TemporaryDirectory() as temp:
            for index, value in enumerate(malformed):
                with self.subTest(index=index):
                    path = Path(temp) / f"bad-{index}.json"
                    path.write_text(json.dumps(value), encoding="utf-8")
                    with self.assertRaisesRegex(SystemExit, "Invalid score input"):
                        bench.cmd_compare(argparse.Namespace(inputs=[str(path)], output=None))

    def test_manual_compare_rejects_unreadable_or_invalid_json(self):
        with tempfile.TemporaryDirectory() as temp:
            invalid = Path(temp) / "invalid.json"
            invalid.write_text("[not json", encoding="utf-8")
            for path in (invalid, Path(temp) / "missing.json"):
                with self.subTest(path=path), self.assertRaisesRegex(
                    SystemExit, "Could not read score input"
                ):
                    bench.cmd_compare(argparse.Namespace(inputs=[str(path)], output=None))

    def test_manual_compare_rejects_duplicate_run_ids_cleanly(self):
        score = {
            "run_id": "duplicate", "scenario_id": "scenario", "condition": "manual",
            "replicate": 1, "score": 50.0,
            "metrics": {"critical_defect_count": 0, "interview_turns": 1,
                        "interaction_burden_score": 100.0},
        }
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "score.json"
            path.write_text(json.dumps(score), encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "duplicate run identity"):
                bench.cmd_compare(argparse.Namespace(inputs=[str(path), str(path)], output=None))


if __name__ == "__main__":
    unittest.main()
