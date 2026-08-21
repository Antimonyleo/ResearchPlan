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


if __name__ == "__main__":
    unittest.main()
