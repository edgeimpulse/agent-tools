import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "bump_skill_versions.py"
SPEC = importlib.util.spec_from_file_location("bump_skill_versions", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BumpSkillVersionsTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary_directory.name)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def write_skill(self, relative: str, frontmatter: str) -> Path:
        skill_dir = self.repo / relative
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\n{frontmatter}---\n\nInstructions.\n",
            encoding="utf-8",
        )
        return skill_dir

    def test_bumps_existing_patch_version(self):
        skill_dir = self.write_skill(
            "skills/example",
            'name: example\ndescription: Example skill.\nmetadata:\n  version: "1.2.3"\n',
        )

        previous, current = MODULE.bump_skill_version(skill_dir)

        self.assertEqual((previous, current), ("1.2.3", "1.2.4"))
        self.assertIn(
            '  version: "1.2.4"',
            (skill_dir / "SKILL.md").read_text(encoding="utf-8"),
        )

    def test_initializes_stable_and_experimental_versions(self):
        stable = self.write_skill(
            "skills/stable",
            "name: stable\ndescription: Stable skill.\n",
        )
        experimental = self.write_skill(
            "skills/.experimental/preview",
            "name: preview\ndescription: Preview skill.\n",
        )

        self.assertEqual(MODULE.bump_skill_version(stable), (None, "1.0.0"))
        self.assertEqual(MODULE.bump_skill_version(experimental), (None, "0.1.0"))

    def test_maps_nested_changed_file_to_nearest_skill(self):
        first = self.write_skill(
            "skills/first",
            "name: first\ndescription: First skill.\n",
        )
        self.write_skill(
            "skills/second",
            "name: second\ndescription: Second skill.\n",
        )
        reference = first / "references" / "REFERENCE.md"
        reference.parent.mkdir()
        reference.write_text("Reference", encoding="utf-8")

        result = MODULE.changed_skill_directories(
            self.repo,
            ["skills/first/references/REFERENCE.md", "README.md"],
        )

        self.assertEqual(result, [first])

    def test_rejects_non_semver_version(self):
        skill_dir = self.write_skill(
            "skills/example",
            'name: example\ndescription: Example skill.\nmetadata:\n  version: "latest"\n',
        )

        with self.assertRaisesRegex(ValueError, "MAJOR.MINOR.PATCH"):
            MODULE.bump_skill_version(skill_dir)


if __name__ == "__main__":
    unittest.main()
