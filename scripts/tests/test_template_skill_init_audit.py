import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "template_skill_init_audit", ROOT / "scripts/verification/template_skill_init_audit.py"
)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class TemplateSkillInitAuditTest(unittest.TestCase):
    def test_real_skill_initialization_matches_independent_file_manifest(self):
        report = AUDIT.run()
        self.assertEqual("PASS", report["result"])
        self.assertTrue(report["consumer_is_disposable_git_project"])
        self.assertTrue(report["consumer_removed_after_audit"])
        self.assertEqual({"erp", "member"}, set(report["modules"]))
        for module, result in report["modules"].items():
            with self.subTest(module=module):
                self.assertEqual(result["expected_file_count"], result["created_file_count"])
                self.assertEqual([], result["missing"])
                self.assertEqual([], result["extra"])
                self.assertEqual([], result["byte_different"])


if __name__ == "__main__":
    unittest.main()
