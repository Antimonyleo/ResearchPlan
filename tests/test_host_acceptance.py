from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts/host_acceptance.py"
SPEC = importlib.util.spec_from_file_location("rescamp_host_acceptance", SCRIPT)
host_acceptance = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(host_acceptance)


class HostAcceptanceTests(unittest.TestCase):
    def run_acceptance(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=False
        )

    def install_skill(self, project: Path, host: str = "codex") -> Path:
        relative = host_acceptance.HOST_ADAPTERS[host].skill_path
        destination = project / relative
        shutil.copytree(ROOT / "rescamp", destination.parent)
        return destination

    def test_dry_run_uses_canonical_modes_and_each_hosts_explicit_skill_syntax(self):
        self.assertEqual(
            host_acceptance.CANONICAL_MODES,
            ("Camp-auto", "Camp-brief", "Camp-full"),
        )
        with tempfile.TemporaryDirectory() as temp_str:
            project = Path(temp_str)
            for host, prefix in (("codex", "/rescamp"), ("claude-code", "/rescamp")):
                for mode in host_acceptance.CANONICAL_MODES:
                    with self.subTest(host=host, mode=mode):
                        result = self.run_acceptance(
                            "--host", host, "--project", str(project), "--mode", mode,
                            "--goal", "bounded goal", "--dry-run",
                        )
                        self.assertEqual(result.returncode, 0, result.stderr)
                        receipt = json.loads(result.stdout)
                        expected = f"{prefix} {mode} bounded goal"
                        self.assertEqual(receipt["prompt"], expected)
                        self.assertTrue(receipt["dry_run"])
                        self.assertNotIn(expected, receipt["command"],
                                         "receipts retain a prompt digest, not research text in argv logs")
                        if host == "codex":
                            self.assertNotIn("--sandbox", receipt["command"])
                            self.assertIn("--approve-for-me", receipt["command"])
                            self.assertIn("--skip-git-repo-check", receipt["command"])
                        else:
                            self.assertNotIn("--settings", receipt["command"])

    def test_camp_full_can_address_an_existing_brief(self):
        with tempfile.TemporaryDirectory() as temp_str:
            result = self.run_acceptance(
                "--host", "codex", "--project", temp_str, "--mode", "Camp-full",
                "--campaign", "research-campaigns/brief", "--dry-run",
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout)["prompt"],
            "/rescamp Camp-full research-campaigns/brief",
        )

    def test_canonical_modes_require_a_goal_or_existing_brief(self):
        with tempfile.TemporaryDirectory() as temp_str:
            for mode in host_acceptance.CANONICAL_MODES:
                with self.subTest(mode=mode):
                    result = self.run_acceptance(
                        "--host", "codex", "--project", temp_str,
                        "--mode", mode, "--dry-run",
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("--goal is required", result.stderr)

    def test_modes_reject_arguments_they_do_not_use(self):
        with tempfile.TemporaryDirectory() as temp_str:
            cases = (
                ("Camp-auto", ("--campaign", "campaign"), "only for Camp-full"),
                ("Camp-brief", ("--campaign", "campaign"), "only for Camp-full"),
                ("Camp-full", ("--goal", "goal", "--campaign", "campaign"), "either"),
                ("help", ("--goal", "ignored"), "does not accept"),
            )
            for mode, extra, message in cases:
                with self.subTest(mode=mode):
                    result = self.run_acceptance(
                        "--host", "codex", "--project", temp_str, "--mode", mode,
                        *extra, "--dry-run",
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(message, result.stderr)

    def test_mode_tokens_are_case_sensitive(self):
        with tempfile.TemporaryDirectory() as temp_str:
            result = self.run_acceptance(
                "--host", "codex", "--project", temp_str, "--mode", "camp-auto",
                "--dry-run",
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)

    def test_claude_error_envelope_is_not_a_passing_response(self):
        self.assertFalse(host_acceptance.response_ok(
            "claude-code", '{"is_error":true,"result":"permission denied"}'
        ))
        self.assertFalse(host_acceptance.response_ok("claude-code", "not json"))
        self.assertTrue(host_acceptance.response_ok(
            "claude-code", '{"is_error":false,"result":"ok"}'
        ))
        self.assertFalse(host_acceptance.response_ok(
            "claude-code",
            '{"is_error":false,"result":"The rescamp skill is disabled; I cannot invoke it."}',
        ))
        self.assertFalse(host_acceptance.response_ok(
            "codex", "The rescamp skill is disabled; I cannot invoke it."
        ))
        self.assertFalse(host_acceptance.response_ok("codex", "Error: skill not found"))
        self.assertFalse(host_acceptance.response_ok("codex", "Unknown skill: rescamp"))
        for malformed in ("[]", "null", "true", '{"result":"ok"}',
                          '{"is_error":false,"result":null}'):
            with self.subTest(malformed=malformed):
                self.assertFalse(host_acceptance.response_ok("claude-code", malformed))

    def test_timeout_must_be_positive(self):
        with tempfile.TemporaryDirectory() as temp_str:
            result = self.run_acceptance(
                "--host", "codex", "--project", temp_str, "--mode", "help",
                "--timeout", "0", "--dry-run",
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("positive integer", result.stderr)

    def test_host_timeout_returns_a_failed_receipt_without_traceback(self):
        with tempfile.TemporaryDirectory() as temp_str:
            root = Path(temp_str)
            fake = root / "slow-host.py"
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "import sys, time\n"
                "if '--version' in sys.argv:\n"
                "    print('slow-host 1.0')\n"
                "else:\n"
                "    time.sleep(5)\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            project = root / "project"
            self.install_skill(project)
            evidence = root / "evidence"
            result = self.run_acceptance(
                "--host", "codex", "--project", str(project), "--mode", "help",
                "--executable", str(fake), "--timeout", "1",
                "--evidence-dir", str(evidence),
            )
            receipt_file_exists = (evidence / "receipt.json").is_file()

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        receipt = json.loads(result.stdout)
        self.assertTrue(receipt["timed_out"])
        self.assertEqual(receipt["timeout_stage"], "host")
        self.assertEqual(receipt["returncode"], 124)
        self.assertFalse(receipt["passed"])
        self.assertTrue(receipt_file_exists)

    def test_version_timeout_returns_a_failed_receipt_without_traceback(self):
        with tempfile.TemporaryDirectory() as temp_str:
            root = Path(temp_str)
            fake = root / "slow-version.py"
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "import time\n"
                "time.sleep(5)\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            project = root / "project"
            self.install_skill(project)
            result = self.run_acceptance(
                "--host", "codex", "--project", str(project), "--mode", "help",
                "--executable", str(fake), "--timeout", "1",
            )

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        receipt = json.loads(result.stdout)
        self.assertTrue(receipt["timed_out"])
        self.assertEqual(receipt["timeout_stage"], "version")
        self.assertEqual(receipt["host_version_returncode"], 124)
        self.assertEqual(receipt["returncode"], 124)
        self.assertFalse(receipt["passed"])

    def test_missing_executable_returns_a_failed_receipt_without_traceback(self):
        with tempfile.TemporaryDirectory() as temp_str:
            root = Path(temp_str)
            project = root / "project"
            self.install_skill(project)
            result = self.run_acceptance(
                "--host", "codex", "--project", str(project), "--mode", "help",
                "--executable", str(root / "does-not-exist"),
            )

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["failure_stage"], "version")
        self.assertEqual(receipt["host_version_returncode"], 127)
        self.assertFalse(receipt["passed"])

    def test_every_non_help_live_mode_requires_an_expected_artifact(self):
        cases = (
            ("Camp-auto", ("--goal", "bounded goal")),
            ("Camp-brief", ("--goal", "bounded goal")),
            ("Camp-full", ("--goal", "bounded goal")),
        )
        with tempfile.TemporaryDirectory() as temp_str:
            for mode, extra in cases:
                with self.subTest(mode=mode):
                    result = self.run_acceptance(
                        "--host", "codex", "--project", temp_str, "--mode", mode,
                        *extra,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("--expect or --expect-glob is required", result.stderr)

    def test_run_records_evidence_and_verifies_expected_artifacts(self):
        with tempfile.TemporaryDirectory() as temp_str:
            root = Path(temp_str)
            fake = root / "fake-host.py"
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "import pathlib, sys\n"
                "prompt = sys.stdin.read()\n"
                "pathlib.Path('acceptance.done').write_text(prompt, encoding='utf-8')\n"
                "if '-o' in sys.argv:\n"
                "    pathlib.Path(sys.argv[sys.argv.index('-o') + 1]).write_text('ok', encoding='utf-8')\n"
                "else:\n"
                "    print('{\"is_error\":false,\"result\":\"ok\"}')\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            for host, skill_path in (("codex", ".agents/skills/rescamp/SKILL.md"),
                                     ("claude-code", ".claude/skills/rescamp/SKILL.md")):
                with self.subTest(host=host):
                    project = root / host
                    installed = self.install_skill(project, host)
                    self.assertEqual(installed, project / skill_path)
                    evidence = root / f"evidence-{host}"
                    result = self.run_acceptance(
                        "--host", host, "--project", str(project), "--mode", "Camp-auto",
                        "--goal", "bounded goal",
                        "--executable", str(fake), "--expect", "acceptance.done",
                        "--evidence-dir", str(evidence),
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    receipt = json.loads(result.stdout)
                    self.assertTrue(receipt["passed"])
                    self.assertEqual(
                        receipt["acceptance_scope"],
                        "transport-response-and-artifact-change",
                    )
                    self.assertTrue(receipt["host_version"])
                    self.assertEqual(len(receipt["skill_tree_sha256"]), 64)
                    self.assertEqual(
                        receipt["skill_tree_sha256"],
                        host_acceptance.digest_tree(installed.parent),
                    )
                    self.assertEqual(receipt["expected_artifacts"], {"acceptance.done": True})
                    self.assertEqual(
                        (project / "acceptance.done").read_text(encoding="utf-8"),
                        f"{host_acceptance.HOST_ADAPTERS[host].prompt_prefix} Camp-auto bounded goal",
                    )
                    self.assertTrue((evidence / "request.txt").is_file())
                    self.assertTrue((evidence / "response.txt").is_file())
                    self.assertTrue((evidence / "receipt.json").is_file())

    def test_incomplete_skill_installation_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_str:
            project = Path(temp_str)
            skill = project / ".agents/skills/rescamp/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: rescamp\n---\n", encoding="utf-8")
            result = self.run_acceptance(
                "--host", "codex", "--project", str(project), "--mode", "help",
                "--executable", sys.executable,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("installation is incomplete", result.stderr)

    def test_complete_canonical_tree_is_required_for_both_hosts(self):
        for host in host_acceptance.HOST_ADAPTERS:
            with self.subTest(host=host), tempfile.TemporaryDirectory() as temp_str:
                project = Path(temp_str)
                self.install_skill(project, host)
                (project / host_acceptance.HOST_ADAPTERS[host].skill_path).parent.joinpath(
                    "assets/review.schema.json"
                ).unlink()
                result = self.run_acceptance(
                    "--host", host, "--project", str(project), "--mode", "help",
                    "--executable", sys.executable,
                )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("assets/review.schema.json", result.stderr)

    @unittest.skipUnless(hasattr(os, "killpg"), "process-group termination requires POSIX")
    def test_timeout_cleanup_tolerates_process_exit_race(self):
        process = mock.Mock(pid=123, returncode=-9)
        process.communicate.side_effect = [
            subprocess.TimeoutExpired(["fake"], 0.01),
            ("", ""),
        ]
        with mock.patch.object(host_acceptance.subprocess, "Popen", return_value=process):
            with mock.patch.object(
                host_acceptance.os, "killpg", side_effect=ProcessLookupError,
            ):
                result, timed_out = host_acceptance.run_process(
                    ["fake"], Path.cwd(), timeout=0.01,
                )

        self.assertTrue(timed_out)
        self.assertEqual(result.returncode, 124)
        process.communicate.assert_called()

    def test_preexisting_artifact_cannot_satisfy_any_non_help_mode(self):
        cases = (
            ("Camp-auto", ("--goal", "bounded goal")),
            ("Camp-brief", ("--goal", "bounded goal")),
            ("Camp-full", ("--goal", "bounded goal")),
        )
        with tempfile.TemporaryDirectory() as temp_str:
            root = Path(temp_str)
            fake = root / "no-op-host.py"
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "import sys\n"
                "print('no-op-host 1.0' if '--version' in sys.argv else 'ok')\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            project = root / "project"
            self.install_skill(project)
            artifact = project / "already-there.txt"
            artifact.write_text("old output", encoding="utf-8")

            for mode, extra in cases:
                with self.subTest(mode=mode):
                    result = self.run_acceptance(
                        "--host", "codex", "--project", str(project), "--mode", mode,
                        *extra, "--executable", str(fake), "--expect", "already-there.txt",
                    )
                    self.assertEqual(result.returncode, 2, result.stderr)
                    receipt = json.loads(result.stdout)
                    self.assertFalse(receipt["passed"])
                    self.assertEqual(
                        receipt["expected_artifacts"], {"already-there.txt": False}
                    )

    def test_touching_identical_content_does_not_satisfy_acceptance(self):
        with tempfile.TemporaryDirectory() as temp_str:
            root = Path(temp_str)
            fake = root / "touch-host.py"
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "import pathlib, sys\n"
                "if '--version' in sys.argv: print('touch-host 1.0')\n"
                "else: pathlib.Path('artifact.txt').touch(); print('ok')\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            project = root / "project"
            self.install_skill(project)
            (project / "artifact.txt").write_text("unchanged", encoding="utf-8")

            result = self.run_acceptance(
                "--host", "codex", "--project", str(project), "--mode", "Camp-brief",
                "--goal", "goal", "--executable", str(fake), "--expect", "artifact.txt",
            )

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertFalse(json.loads(result.stdout)["expected_artifacts"]["artifact.txt"])

    @unittest.skipUnless(hasattr(os, "killpg"), "process-group termination requires POSIX")
    def test_timeout_terminates_descendant_processes(self):
        with tempfile.TemporaryDirectory() as temp_str:
            root = Path(temp_str)
            late = root / "late-write.txt"
            fake = root / "descendant-host.py"
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "import subprocess, sys, time\n"
                "if '--version' in sys.argv:\n"
                "    print('descendant-host 1.0')\n"
                "else:\n"
                f"    subprocess.Popen([sys.executable, '-c', \"import time; from pathlib import Path; time.sleep(2); Path({str(late)!r}).write_text('late')\"])\n"
                "    time.sleep(10)\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            project = root / "project"
            self.install_skill(project)

            result = self.run_acceptance(
                "--host", "codex", "--project", str(project), "--mode", "help",
                "--executable", str(fake), "--timeout", "1",
            )
            time.sleep(2.5)
            self.assertFalse(late.exists())

        self.assertEqual(result.returncode, 2, result.stderr)

    def test_expected_path_cannot_be_replaced_by_an_external_symlink(self):
        with tempfile.TemporaryDirectory() as temp_str:
            root = Path(temp_str)
            outside = root / "outside.txt"
            outside.write_text("outside", encoding="utf-8")
            fake = root / "symlink-host.py"
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "import os, pathlib, sys\n"
                "if '--version' in sys.argv: print('symlink-host 1.0')\n"
                f"else: os.symlink({str(outside)!r}, 'artifact.txt'); print('ok')\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            project = root / "project"
            self.install_skill(project)

            result = self.run_acceptance(
                "--host", "codex", "--project", str(project), "--mode", "Camp-brief",
                "--goal", "goal", "--executable", str(fake), "--expect", "artifact.txt",
            )

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        receipt = json.loads(result.stdout)
        self.assertFalse(receipt["passed"])
        self.assertIn("artifact.txt", receipt["artifact_errors"])

    def test_glob_expectation_accepts_a_host_chosen_campaign_id(self):
        with tempfile.TemporaryDirectory() as temp_str:
            root = Path(temp_str)
            fake = root / "fake-host.py"
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "import pathlib, sys\n"
                "if '--version' in sys.argv:\n"
                "    print('fake-host 1.0')\n"
                "else:\n"
                "    target = pathlib.Path('research-campaigns/host-chosen/state/campaign.json')\n"
                "    target.parent.mkdir(parents=True, exist_ok=True)\n"
                "    target.write_text('new state', encoding='utf-8')\n"
                "    if '-o' in sys.argv:\n"
                "        pathlib.Path(sys.argv[sys.argv.index('-o') + 1]).write_text('ok', encoding='utf-8')\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            project = root / "project"
            self.install_skill(project)
            result = self.run_acceptance(
                "--host", "codex", "--project", str(project), "--mode", "Camp-brief",
                "--goal", "bounded goal", "--executable", str(fake),
                "--expect-glob", "research-campaigns/*/state/campaign.json",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertTrue(receipt["passed"])
        self.assertEqual(
            receipt["expected_artifact_globs"],
            {"research-campaigns/*/state/campaign.json": True},
        )


if __name__ == "__main__":
    unittest.main()
