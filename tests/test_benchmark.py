import importlib.util
import argparse
import contextlib
import copy
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
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
                " print(json.dumps({'action':'ask','message':'Please clarify the next decision.','branch':['decision-purpose','scope-object'][asks],'question_count':1}))\n"
                "else:\n"
                " print(json.dumps({'action':'final','message':'Draft complete.','declared_resolutions':[],'declared_blockers':[],'declared_features':[],'readiness_claimed':False}))\n",
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

    def test_config_validation_rejects_malformed_nested_values(self):
        cases = [
            {"conditions": []},
            {"conditions": ["not-an-object"]},
            {"conditions": [{"id": [], "adapter": "fixture"}]},
            {"conditions": [{"id": "../../../escape", "adapter": "fixture"}]},
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
        self.assertFalse(any(item["_matched_controls"] for item in loaded["conditions"]))

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

    def test_manifest_hashes_every_persisted_run_file(self):
        scenario = bench.load_scenarios(ROOT / "benchmark/scenarios/public")[0]
        condition = bench.load_config(ROOT / "benchmark/conditions/fixture.json")["conditions"][0]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            score = bench.run_one(scenario, condition, 1, root, 20, 20)
            run_dir = root / score["run_id"]
            manifest = json.loads((run_dir / "manifest.json").read_text())
            expected = {
                "public_scenario.json", "transcript.json", "evaluator_transcript.json",
                "evaluation.json", "score.json",
            }
            self.assertEqual(set(manifest["files"]), expected)
            for name in expected:
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


if __name__ == "__main__":
    unittest.main()
