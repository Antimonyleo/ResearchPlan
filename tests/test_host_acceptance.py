from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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

    def test_dry_run_uses_each_hosts_explicit_skill_syntax(self):
        with tempfile.TemporaryDirectory() as temp_str:
            project = Path(temp_str)
            cases = (("codex", "$rescamp review /tmp/campaign"),
                     ("claude-code", "/rescamp review /tmp/campaign"))
            for host, expected in cases:
                with self.subTest(host=host):
                    result = self.run_acceptance(
                        "--host", host, "--project", str(project), "--mode", "review",
                        "--campaign", "/tmp/campaign", "--dry-run",
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    receipt = json.loads(result.stdout)
                    self.assertEqual(receipt["prompt"], expected)
                    self.assertTrue(receipt["dry_run"])
                    self.assertNotIn(expected, receipt["command"],
                                     "receipts retain a prompt digest, not research text in argv logs")
                    if host == "codex":
                        self.assertNotIn("--sandbox", receipt["command"])
                        self.assertIn("--approve-for-me", receipt["command"])
                    else:
                        self.assertNotIn("--settings", receipt["command"])

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
            installed = project / ".agents/skills/rescamp/SKILL.md"
            installed.parent.mkdir(parents=True)
            installed.write_text("---\nname: rescamp\n---\n", encoding="utf-8")
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
            installed = project / ".agents/skills/rescamp/SKILL.md"
            installed.parent.mkdir(parents=True)
            installed.write_text("---\nname: rescamp\n---\n", encoding="utf-8")
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
            installed = project / ".agents/skills/rescamp/SKILL.md"
            installed.parent.mkdir(parents=True)
            installed.write_text("---\nname: rescamp\n---\n", encoding="utf-8")
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

    def test_non_help_modes_require_an_expected_artifact(self):
        with tempfile.TemporaryDirectory() as temp_str:
            result = self.run_acceptance(
                "--host", "codex", "--project", temp_str, "--mode", "test",
                "--campaign", "research-campaigns/example",
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--expect is required", result.stderr)

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
                "    print('{\"result\":\"ok\"}')\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            for host, skill_path in (("codex", ".agents/skills/rescamp/SKILL.md"),
                                     ("claude-code", ".claude/skills/rescamp/SKILL.md")):
                with self.subTest(host=host):
                    project = root / host
                    installed = project / skill_path
                    installed.parent.mkdir(parents=True)
                    installed.write_text("---\nname: rescamp\n---\n", encoding="utf-8")
                    evidence = root / f"evidence-{host}"
                    result = self.run_acceptance(
                        "--host", host, "--project", str(project), "--mode", "help",
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
                    self.assertEqual(receipt["expected_artifacts"], {"acceptance.done": True})
                    self.assertTrue((evidence / "request.txt").is_file())
                    self.assertTrue((evidence / "response.txt").is_file())
                    self.assertTrue((evidence / "receipt.json").is_file())

    def test_preexisting_artifact_cannot_satisfy_acceptance(self):
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
            installed = project / ".agents/skills/rescamp/SKILL.md"
            installed.parent.mkdir(parents=True)
            installed.write_text("---\nname: rescamp\n---\n", encoding="utf-8")
            artifact = project / "already-there.txt"
            artifact.write_text("old output", encoding="utf-8")

            result = self.run_acceptance(
                "--host", "codex", "--project", str(project), "--mode", "test",
                "--campaign", "campaign", "--executable", str(fake),
                "--expect", "already-there.txt",
            )

        self.assertEqual(result.returncode, 2, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertFalse(receipt["passed"])
        self.assertEqual(receipt["expected_artifacts"], {"already-there.txt": False})


if __name__ == "__main__":
    unittest.main()
