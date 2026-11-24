import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "verification"))

from erp_stock_statistics_probe import (  # noqa: E402
    PERMISSIONS,
    validate_target,
)


class ErpStockStatisticsProbeTest(unittest.TestCase):
    def test_accepts_disposable_target(self):
        self.assertTrue(validate_target(
            "yuheng_t4_erp_stock_auth_20261122", 48238, 13393, 16474
        ))

    def test_rejects_shared_or_reserved_target(self):
        with self.assertRaises(ValueError):
            validate_target("yuheng_demo", 48238, 13393, 16474)
        with self.assertRaises(ValueError):
            validate_target("yuheng_t4_erp_stock_auth_20261122", 48080, 13393, 16474)

    def test_permission_contract_covers_stock_record_and_statistics(self):
        self.assertEqual(set(PERMISSIONS), {
            "erp:stock:query",
            "erp:stock:export",
            "erp:stock-record:query",
            "erp:stock-record:export",
            "erp:statistics:query",
        })


if __name__ == "__main__":
    unittest.main()
