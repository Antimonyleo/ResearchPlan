import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class SkillStructureTests(unittest.TestCase):
    def test_exactly_one_canonical_skill_md(self):
        files = [p for p in ROOT.rglob("SKILL.md") if ".dist" not in p.parts and "dist" not in p.parts]
        self.assertEqual(files, [ROOT / "rescamp/SKILL.md"])

    def test_no_host_specific_skill_sources(self):
        paths = [p.as_posix() for p in ROOT.rglob("*")]
        self.assertFalse(any("variants/claude" in p or "variants/codex" in p for p in paths))
        self.assertFalse((ROOT / ".claude/skills").exists())
        self.assertFalse((ROOT / ".agents/skills").exists())

    def test_skill_is_concise_and_standard(self):
        text = (ROOT / "rescamp/SKILL.md").read_text(encoding="utf-8")
        self.assertLess(len(text.splitlines()), 500)
        self.assertLess(len(re.findall(r"\S+", text)), 5000)
        self.assertIn("name: rescamp", text)
        self.assertIn("description:", text)
        self.assertNotIn("disable-model-invocation", text)
        self.assertIn("Automatic quality loop", text)
        self.assertIn("manual `benchmark`", text)

    def test_codex_metadata_does_not_change_skill(self):
        """Host policy lives outside SKILL.md, so both hosts read identical bytes."""
        self.assertTrue((ROOT / "rescamp/agents/openai.yaml").exists())
        self.assertIn("allow_implicit_invocation: false", (ROOT / "rescamp/agents/openai.yaml").read_text())
        skill = (ROOT / "rescamp/SKILL.md").read_text(encoding="utf-8")
        # Assert on the names a host is actually referred to by. The previous token
        # list was chosen so that it passed over the real violation it claimed to
        # catch ("Claude Code invokes /rescamp; Codex invokes $rescamp").
        for host_token in ("Claude Code", "Codex", "$rescamp", ".claude/", ".agents/",
                           "openai", "allow_implicit_invocation", "skillOverrides", "AskUserQuestion"):
            self.assertNotIn(
                host_token, skill,
                f"host-specific token {host_token!r} leaked into the canonical skill; "
                "per-host detail belongs in references/hosts.md",
            )
        # `/rescamp` as an invocation, not as part of the `scripts/rescamp.py` path.
        self.assertIsNone(
            re.search(r"(?<![\w.])/rescamp\b", skill),
            "host invocation syntax leaked into the canonical skill",
        )

    def test_host_registry_covers_every_installable_host(self):
        """Adding a host must mean editing hosts.md and install.py, never SKILL.md."""
        import importlib.util

        spec = importlib.util.spec_from_file_location("installer", ROOT / "scripts/install.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        registry = (ROOT / "rescamp/references/hosts.md").read_text(encoding="utf-8")
        for host_id in installer.HOSTS:
            self.assertIn(f"`{host_id}`", registry, f"host {host_id!r} is installable but undocumented in hosts.md")

    def test_every_referenced_file_exists(self):
        """SKILL.md points at references and scripts; a dangling pointer is a silent failure."""
        skill = (ROOT / "rescamp/SKILL.md").read_text(encoding="utf-8")
        for rel in sorted(set(re.findall(r"`((?:references|scripts|assets)/[\w./-]+)`", skill))):
            self.assertTrue((ROOT / "rescamp" / rel).exists(), f"SKILL.md references missing file {rel}")


if __name__ == "__main__":
    unittest.main()
