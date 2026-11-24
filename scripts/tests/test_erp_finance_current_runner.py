import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class ErpFinanceCurrentRunnerTest(unittest.TestCase):
    def test_runner_pins_current_jar_and_separates_edit_and_owner_schemas(self):
        source = (ROOT / "scripts/verification/erp_finance_current_runner.py").read_text()
        for required in (
            "4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1",
            "yuheng_t4_edit_20261123_current",
            "yuheng_t4_owner_20261123_current",
            "erp_finance_edit_probe.py",
            "erp_finance_owner_probe.py",
            "seed_passwords_unchanged",
            "cleanup",
        ):
            with self.subTest(required=required):
                self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
