import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class InstallerTests(unittest.TestCase):
    def test_both_hosts_receive_identical_skill(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            home.mkdir()
            env = dict(os.environ)
            env["HOME"] = str(home)
            proc = subprocess.run(["python3", str(ROOT / "scripts/install.py"), "--host", "both", "--scope", "user", "--force"], cwd=ROOT, env=env, text=True, capture_output=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            claude = home / ".claude/skills/rescamp/SKILL.md"
            codex = home / ".agents/skills/rescamp/SKILL.md"
            source = ROOT / "rescamp/SKILL.md"
            self.assertEqual(claude.read_bytes(), codex.read_bytes())
            self.assertEqual(source.read_bytes(), claude.read_bytes())
            settings = json.loads((home / ".claude/settings.json").read_text())
            self.assertEqual(settings["skillOverrides"]["rescamp"], "user-invocable-only")

    def test_install_preserves_existing_claude_settings(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            settings = home / ".claude/settings.json"
            settings.parent.mkdir(parents=True)
            original = {"permissions": {"deny": ["Read(./secrets/**)"]}}
            settings.write_text(json.dumps(original) + "\n", encoding="utf-8")
            env = dict(os.environ)
            env["HOME"] = str(home)
            proc = subprocess.run(
                ["python3", str(ROOT / "scripts/install.py"), "--host", "claude-code",
                 "--scope", "user", "--force"],
                cwd=ROOT, env=env, text=True, capture_output=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            installed = json.loads(settings.read_text(encoding="utf-8"))
            self.assertEqual(installed["permissions"], original["permissions"])
            self.assertEqual(installed["skillOverrides"]["rescamp"], "user-invocable-only")

    def test_invalid_claude_settings_fail_before_skill_installation(self):
        for payload in ([], {"skillOverrides": []}):
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as temp:
                home = Path(temp) / "home"
                settings = home / ".claude/settings.json"
                settings.parent.mkdir(parents=True)
                settings.write_text(json.dumps(payload) + "\n", encoding="utf-8")
                env = dict(os.environ)
                env["HOME"] = str(home)
                proc = subprocess.run(
                    ["python3", str(ROOT / "scripts/install.py"), "--host", "claude-code",
                     "--scope", "user"],
                    cwd=ROOT, env=env, text=True, capture_output=True,
                )
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn("must be a JSON object", proc.stderr)
                self.assertFalse((home / ".claude/skills/rescamp").exists())


if __name__ == "__main__":
    unittest.main()
