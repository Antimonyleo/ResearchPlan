import builtins
import importlib.util
import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
VALIDATE_PATH = ROOT / "scripts/validate_release.py"
SKILL_VALIDATE_PATH = ROOT / "rescamp/scripts/validate_skill.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("rescamp_validate_release_test", VALIDATE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class ReleaseValidationTests(unittest.TestCase):
    def test_missing_jsonschema_is_a_release_blocking_error(self):
        def import_without_jsonschema(name, *args, **kwargs):
            if name == "jsonschema":
                raise ImportError("jsonschema unavailable for test")
            return original_import(name, *args, **kwargs)

        original_import = builtins.__import__
        with mock.patch("builtins.__import__", side_effect=import_without_jsonschema):
            validator = load_validator()
            with tempfile.TemporaryDirectory() as temp:
                errors, warnings = validator.validate_json(Path(temp))

        self.assertTrue(any("jsonschema is not installed" in error for error in errors))
        self.assertEqual(warnings, [])

    def test_review_schema_requires_execution_evidence_for_independence_claims(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema is not installed")

        schema = json.loads(
            (ROOT / "rescamp/assets/review.schema.json").read_text(encoding="utf-8")
        )
        validator = jsonschema.Draft202012Validator(schema)
        digest = "sha256:" + "a" * 64
        base = {
            "role": "methods-evidence",
            "reviewer_id": "reviewer-1",
            "verdict": "pass",
            "content_digest": digest,
            "rubric_digest": digest,
            "packet_digest": digest,
            "summary": "reviewed",
            "findings": [],
        }
        for mode in ("independent-subagent", "separate-session", "external-human"):
            with self.subTest(mode=mode):
                errors = list(validator.iter_errors({**base, "mode": mode}))
                self.assertTrue(
                    any("execution_evidence" in error.message for error in errors),
                    errors,
                )

        sequential_errors = list(
            validator.iter_errors({**base, "mode": "sequential-pass"})
        )
        self.assertEqual(sequential_errors, [])

        valid_independent = {
            **base,
            "mode": "independent-subagent",
            "execution_evidence": {
                "executor_id": "session-1",
                "started_at": "2026-08-26T00:00:00Z",
                "completed_at": "2026-08-26T00:01:00Z",
            },
        }
        self.assertEqual(list(validator.iter_errors(valid_independent)), [])

    def test_subprocess_timeout_is_reported_as_structured_failure(self):
        validator = load_validator()

        with tempfile.TemporaryDirectory() as temp:
            result = validator.run(
                [sys.executable, "-c", "import time; time.sleep(0.25)"],
                Path(temp), timeout=0.01,
            )

        self.assertNotEqual(result["returncode"], 0)
        self.assertTrue(result["timed_out"])
        self.assertIn("timed out", result["stderr"])
        self.assertNotIn("Traceback", result["stderr"])

    def test_invalid_utf8_subprocess_output_is_a_structured_result(self):
        validator = load_validator()

        with tempfile.TemporaryDirectory() as temp:
            result = validator.run(
                [
                    sys.executable,
                    "-c",
                    "import sys; sys.stdout.buffer.write(b'out\\xff'); "
                    "sys.stderr.buffer.write(b'err\\xfe')",
                ],
                Path(temp),
            )

        self.assertEqual(result["returncode"], 0)
        self.assertIn("\ufffd", result["stdout"])
        self.assertIn("\ufffd", result["stderr"])
        self.assertNotIn("Traceback", result["stderr"])

    @unittest.skipUnless(hasattr(os, "killpg"), "process-group termination requires POSIX")
    def test_subprocess_timeout_kills_descendants_and_returns_promptly(self):
        validator = load_validator()

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            late = root / "late-write.txt"
            child = (
                "import time; from pathlib import Path; "
                f"time.sleep(2); Path({str(late)!r}).write_text('late', encoding='utf-8')"
            )
            command = [
                sys.executable,
                "-c",
                "import subprocess, sys, time; "
                f"subprocess.Popen([sys.executable, '-c', {child!r}], start_new_session=True); "
                "time.sleep(10)",
            ]
            started = time.monotonic()
            result = validator.run(command, root, timeout=0.2)
            elapsed = time.monotonic() - started
            time.sleep(0.1)
            self.assertFalse(late.exists())

        self.assertTrue(result["timed_out"])
        self.assertLess(elapsed, 1.5)

    @unittest.skipUnless(hasattr(os, "killpg"), "process-group termination requires POSIX")
    def test_subprocess_timeout_tolerates_process_exit_race(self):
        validator = load_validator()
        process = mock.Mock(pid=123, returncode=-9)
        process.communicate.side_effect = [
            subprocess.TimeoutExpired(["fake"], 0.01),
            ("", ""),
        ]

        with mock.patch.object(validator.subprocess, "Popen", return_value=process):
            with mock.patch.object(
                validator.os, "killpg", side_effect=ProcessLookupError,
            ):
                result = validator.run(["fake"], Path.cwd(), timeout=0.01)

        self.assertTrue(result["timed_out"])
        self.assertEqual(result["returncode"], 124)
        process.communicate.assert_called()

    def test_post_kill_drain_is_bounded_when_an_escaped_child_keeps_pipes_open(self):
        validator = load_validator()
        process = mock.Mock(pid=123, returncode=-9)
        process.communicate.side_effect = [
            subprocess.TimeoutExpired(["fake"], 0.01),
            subprocess.TimeoutExpired(["fake"], 1.0, output=b"partial"),
        ]
        process.wait.return_value = -9

        with mock.patch.object(validator.subprocess, "Popen", return_value=process), \
                mock.patch.object(validator, "_terminate_process_group"):
            result = validator.run(["fake"], Path.cwd(), timeout=0.01)

        self.assertTrue(result["timed_out"])
        self.assertEqual(result["stdout"], "partial")
        process.stdout.close.assert_called_once()
        process.stderr.close.assert_called_once()

    def test_windows_taskkill_is_bounded_and_falls_back_to_process_kill(self):
        validator = load_validator()
        process = mock.Mock(pid=321)
        with mock.patch.object(validator.os, "name", "nt"), \
                mock.patch.object(
                    validator.subprocess, "run",
                    side_effect=subprocess.TimeoutExpired(["taskkill"], 5),
                ) as taskkill:
            validator._terminate_process_group(process)

        self.assertEqual(taskkill.call_args.kwargs["timeout"], 5)
        process.kill.assert_called_once_with()

    def test_skill_validation_requires_the_complete_canonical_tree(self):
        with tempfile.TemporaryDirectory() as temp:
            skill_root = Path(temp) / "rescamp"
            shutil.copytree(ROOT / "rescamp", skill_root)
            (skill_root / "assets/review.schema.json").unlink()
            result = subprocess.run(
                [sys.executable, str(SKILL_VALIDATE_PATH), str(skill_root)],
                capture_output=True, text=True, check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing required file: assets/review.schema.json", result.stdout)

    def test_skill_validation_rejects_unexpected_files(self):
        with tempfile.TemporaryDirectory() as temp:
            skill_root = Path(temp) / "rescamp"
            shutil.copytree(ROOT / "rescamp", skill_root)
            (skill_root / "stale.txt").write_text("stale\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SKILL_VALIDATE_PATH), str(skill_root)],
                capture_output=True, text=True, check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexpected skill file: stale.txt", result.stdout)

    def test_rendered_campaign_json_is_checked_against_the_structural_schema(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            assets = root / "rescamp/assets"
            assets.mkdir(parents=True)
            for name in ("campaign.schema.json", "review.schema.json", "scenario.schema.json"):
                shutil.copy2(ROOT / "rescamp/assets" / name, assets / name)
            output = root / "docs/examples/example/outputs/campaign.json"
            output.parent.mkdir(parents=True)
            output.write_text("{}\n", encoding="utf-8")

            errors, _ = validator.validate_json(root)

        self.assertTrue(any(
            "docs/examples/example/outputs/campaign.json schema" in error
            for error in errors
        ), errors)

    def test_example_audit_copy_excludes_transient_private_trees(self):
        validator = load_validator()

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            source = root / "docs/examples/example"
            (source / "state").mkdir(parents=True)
            (source / "outputs").mkdir()
            (source / "state/campaign.json").write_text("{}\n", encoding="utf-8")
            (source / "outputs/published.md").write_text("published\n", encoding="utf-8")
            for directory in ("working", "artifacts", "private", "transient"):
                path = source / directory
                path.mkdir()
                (path / "should-not-be-copied.txt").write_text("private\n", encoding="utf-8")

            calls = []

            def fake_run(command, cwd, timeout=180, env=None):
                calls.append((command, cwd))
                return {"returncode": 0}

            with mock.patch.object(validator, "run", side_effect=fake_run):
                results = validator.audit_examples(root, Path(temp) / "audit")

            self.assertEqual(set(results), {"example"})
            target = Path(calls[0][0][3])
            self.assertTrue((target / "state/campaign.json").is_file())
            self.assertTrue((target / "outputs/published.md").is_file())
            for directory in ("working", "artifacts", "private", "transient"):
                self.assertFalse((target / directory).exists())

    def test_benchmark_smoke_preserves_failure_and_cleans_temp_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            observed = temp_root / "output-path.txt"
            shim = temp_root / "fake_python.py"
            shim.write_text(
                "import sys\n"
                "from pathlib import Path\n"
                f"observed = Path({str(observed)!r})\n"
                "args = sys.argv[1:]\n"
                "if 'run' not in args:\n"
                "    raise SystemExit(0)\n"
                "output = Path(args[args.index('--output') + 1])\n"
                "output.mkdir(parents=True)\n"
                "(output / 'sentinel').write_text('created', encoding='utf-8')\n"
                "observed.write_text(str(output), encoding='utf-8')\n"
                "raise SystemExit(23)\n",
                encoding="utf-8",
            )
            launcher = temp_root / "fake-python"
            launcher.write_text(
                "#!/bin/sh\n"
                f"exec {shlex.quote(sys.executable)} {shlex.quote(str(shim))} \"$@\"\n",
                encoding="utf-8",
            )
            launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR)

            result = subprocess.run(
                ["make", "benchmark-smoke", f"PYTHON={launcher}"],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )

            # GNU make returns its standard recipe-error status, while retaining
            # the recipe's status in the diagnostic. The important contract is
            # that a failing benchmark is non-zero and is not masked by cleanup.
            self.assertNotEqual(result.returncode, 0, result.stderr)
            self.assertIn("Error 23", result.stderr)
            output_path = Path(observed.read_text(encoding="utf-8"))
            self.assertFalse(output_path.exists())

    def test_make_clean_removes_coverage_files_and_gitignore_excludes_them(self):
        self.assertIn("*.cover", (ROOT / ".gitignore").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp:
            cover = Path(temp) / "generated.cover"
            cover.write_text("coverage", encoding="utf-8")
            result = subprocess.run(
                ["make", "-f", str(ROOT / "Makefile"), "clean"],
                cwd=temp, capture_output=True, text=True, check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(cover.exists())


if __name__ == "__main__":
    unittest.main()
