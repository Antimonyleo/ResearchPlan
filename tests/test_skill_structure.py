import importlib.util
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VALIDATE_SPEC = importlib.util.spec_from_file_location(
    "rescamp_validate_release", ROOT / "scripts/validate_release.py",
)
validate_release = importlib.util.module_from_spec(VALIDATE_SPEC)
assert VALIDATE_SPEC.loader
VALIDATE_SPEC.loader.exec_module(validate_release)


class SkillStructureTests(unittest.TestCase):
    def test_release_discovery_ignores_local_and_generated_trees(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            kept = root / "scripts/kept.py"
            kept.parent.mkdir()
            kept.write_text("value = 1\n", encoding="utf-8")
            ignored = (
                root / ".claude/broken.py",
                root / ".agents/skills/rescamp/SKILL.md",
                root / "research-campaigns/draft/broken.py",
                root / "benchmark/runs/run/broken.py",
                root / "docs/examples/sample/working/broken.py",
                root / "node_modules/package/broken.py",
            )
            for path in ignored:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("this is not python", encoding="utf-8")

            discovered = set(validate_release.repository_files(root, "*.py"))

        self.assertEqual(discovered, {kept})

    def test_exactly_one_canonical_skill_md(self):
        files = sorted(validate_release.repository_files(ROOT, "SKILL.md"))
        self.assertEqual(files, [ROOT / "rescamp/SKILL.md"])

    def test_no_host_specific_skill_sources(self):
        paths = [p.as_posix() for p in ROOT.rglob("*")]
        self.assertFalse(any("variants/claude" in p or "variants/codex" in p for p in paths))

    def test_skill_is_concise_and_explicit_only(self):
        text = (ROOT / "rescamp/SKILL.md").read_text(encoding="utf-8")
        self.assertLess(len(text.splitlines()), 500)
        self.assertLess(len(re.findall(r"\S+", text)), 5000)
        self.assertIn("name: rescamp", text)
        self.assertIn("description:", text)
        self.assertIn("disable-model-invocation: true", text)
        self.assertIn("QA orchestration", text)
        self.assertIn("Comparative `benchmark`", text)
        self.assertIn("is always manual", text)
        self.assertIn("Treat unresolved shape as **fog**", text)
        self.assertIn("Never create placeholder campaign objects", text)

    def test_host_policy_is_carried_in_one_bundle(self):
        metadata_path = ROOT / "rescamp/agents/openai.yaml"
        self.assertTrue(metadata_path.exists())
        metadata = metadata_path.read_text(encoding="utf-8")
        self.assertIn("allow_implicit_invocation: false", metadata)
        description = re.search(r'^  short_description: "([^"]+)"$', metadata, re.MULTILINE)
        self.assertIsNotNone(description)
        self.assertGreaterEqual(len(description.group(1)), 25)
        self.assertLessEqual(len(description.group(1)), 64)
        skill = (ROOT / "rescamp/SKILL.md").read_text(encoding="utf-8")
        # Host names and wrapper syntax belong in the focused host reference.
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

    def test_standard_install_command_targets_both_hosts(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("npx skills add Antimonyleo/ResearchPlan --skill rescamp", readme)
        self.assertIn("-a claude-code -a codex", readme)

    def test_committed_examples_pass_strict_audit_in_a_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            results = validate_release.audit_examples(ROOT, Path(temp))
        self.assertTrue(results, "at least one worked example should exercise the release contract")
        self.assertTrue(all(item["returncode"] == 0 for item in results.values()), results)

    def test_every_referenced_file_exists(self):
        """SKILL.md points at references and scripts; a dangling pointer is a silent failure."""
        skill = (ROOT / "rescamp/SKILL.md").read_text(encoding="utf-8")
        for rel in sorted(set(re.findall(r"`((?:references|scripts|assets)/[\w./-]+)`", skill))):
            self.assertTrue((ROOT / "rescamp" / rel).exists(), f"SKILL.md references missing file {rel}")


if __name__ == "__main__":
    unittest.main()
