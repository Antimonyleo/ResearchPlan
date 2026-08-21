from __future__ import annotations

import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "rescamp_validate_release", ROOT / "scripts/validate_release.py"
)
release = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(release)

BUILD_SPEC = importlib.util.spec_from_file_location(
    "rescamp_build_release", ROOT / "scripts/build_release.py"
)
build = importlib.util.module_from_spec(BUILD_SPEC)
assert BUILD_SPEC.loader
BUILD_SPEC.loader.exec_module(build)


class ReleaseProvenanceTests(unittest.TestCase):
    def test_release_copy_excludes_host_state_caches_and_unknown_roots(self):
        with tempfile.TemporaryDirectory() as temp_str:
            root = Path(temp_str)
            for relative in (
                "README.md",
                "rescamp/SKILL.md",
                "benchmark/scenarios/public/example.json",
                "benchmark/runs/private/session.json",
                ".claude/session-changes.json",
                ".agents/private-state.json",
                ".codex/private-state.json",
                ".pytest_cache/CACHEDIR.TAG",
                "research-campaigns/private/state/campaign.json",
                "unknown-root/private.txt",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(relative, encoding="utf-8")

            destination = root / "release"
            build.copy_source(root, destination)

            self.assertTrue((destination / "README.md").is_file())
            self.assertTrue((destination / "rescamp/SKILL.md").is_file())
            self.assertTrue(
                (destination / "benchmark/scenarios/public/example.json").is_file()
            )
            for private in (
                "benchmark/runs/private/session.json",
                ".claude/session-changes.json",
                ".agents/private-state.json",
                ".codex/private-state.json",
                ".pytest_cache/CACHEDIR.TAG",
                "research-campaigns/private/state/campaign.json",
                "unknown-root/private.txt",
            ):
                with self.subTest(path=private):
                    self.assertFalse((destination / private).exists())

            archive = root / "release.zip"
            build.zip_paths(archive, [(destination, "rescamp-v0.9.0")])
            with zipfile.ZipFile(archive) as packaged:
                members = packaged.namelist()
            self.assertTrue(any(name.endswith("/rescamp/SKILL.md") for name in members))
            self.assertFalse(any("/.claude/" in name or "/.pytest_cache/" in name
                                 for name in members))

    def test_repository_input_digest_covers_tests_but_not_generated_qa(self):
        with tempfile.TemporaryDirectory() as temp_str:
            root = Path(temp_str)
            for relative, content in {
                "rescamp/SKILL.md": "skill\n",
                "tests/test_example.py": "before\n",
                "scripts/validate_release.py": "validator\n",
                "benchmark/scenario.json": "{}\n",
                "benchmark/runs/generated.json": "generated run\n",
                "docs/RELEASE_REPORT.md": "generated report\n",
                "qa/RELEASE_CHECK.json": "generated\n",
            }.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

            original = release.repository_input_digest(root)
            (root / "qa/RELEASE_CHECK.json").write_text("changed output\n", encoding="utf-8")
            self.assertEqual(original, release.repository_input_digest(root))
            (root / "benchmark/runs/generated.json").write_text("changed run\n", encoding="utf-8")
            self.assertEqual(original, release.repository_input_digest(root))
            (root / "docs/RELEASE_REPORT.md").write_text("changed report\n", encoding="utf-8")
            self.assertEqual(original, release.repository_input_digest(root))

            (root / "tests/test_example.py").write_text("after\n", encoding="utf-8")
            self.assertNotEqual(original, release.repository_input_digest(root))

    def test_repository_provenance_reports_commit_and_dirty_state(self):
        provenance = release.repository_provenance(ROOT)
        self.assertEqual(len(provenance["repository_input_sha256"]), 64)
        self.assertTrue(provenance["git_commit"])
        self.assertIsInstance(provenance["git_dirty"], bool)
        self.assertIsInstance(provenance["dirty_paths"], list)

    def test_archive_tree_digest_covers_bytes_and_executable_bits(self):
        with tempfile.TemporaryDirectory() as temp_str:
            root = Path(temp_str)
            skill = root / "skill"
            script = skill / "scripts/run.py"
            script.parent.mkdir(parents=True)
            script.write_text("print('ok')\n", encoding="utf-8")
            script.chmod(0o755)
            archive = root / "skill.zip"
            build.zip_paths(archive, [(skill, "rescamp")])
            self.assertEqual(
                build.tree_digest(skill), build.zip_tree_digest(archive, "rescamp")
            )

            script.chmod(0o644)
            self.assertNotEqual(
                build.tree_digest(skill), build.zip_tree_digest(archive, "rescamp")
            )


if __name__ == "__main__":
    unittest.main()
