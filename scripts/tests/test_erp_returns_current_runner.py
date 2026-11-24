import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class ErpReturnsCurrentRunnerTest(unittest.TestCase):
    def test_runner_pins_current_jar_and_isolates_all_runtime_resources(self):
        source = (ROOT / "scripts/verification/erp_returns_current_runner.py").read_text()
        for required in (
            "4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1",
            "yuheng_t4_returns_20261123_current",
            "erp_returns_probe.py",
            "--mysql-container",
            "DATABASECHANGELOG",
            "seed_passwords_unchanged",
            "id<900000",
            "cleanup",
            "tempfile.TemporaryDirectory",
        ):
            with self.subTest(required=required):
                self.assertIn(required, source)

    def test_probe_accepts_only_the_dedicated_returns_schema_family(self):
        source = (ROOT / "scripts/verification/erp_returns_probe.py").read_text()
        self.assertIn(r"yuheng_t4_returns_[0-9]{8}(?:_[a-z0-9]+)?", source)


if __name__ == "__main__":
    unittest.main()
