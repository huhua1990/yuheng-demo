import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ErpStockBrowserProbeTest(unittest.TestCase):
    def test_probe_covers_desktop_stock_check_and_two_warehouse_move(self):
        source = (ROOT / "scripts/verification/erp_stock_browser_probe.js").read_text()
        for required in (
            "width: 1440, height: 900",
            "/erp/stock/check",
            "/erp/stock/move",
            "/admin-api/erp/stock-check/create",
            "/admin-api/erp/stock-check/update-status",
            "/admin-api/erp/stock-move/create",
            "/admin-api/erp/stock-move/update-status",
            "let row = dialog.locator('.el-table__body-wrapper tbody tr').first()",
            "stockRead",
            "const moveQuantity = row.locator('.el-input-number input').nth(0)",
            "stock-check-create-with-positive-adjustment",
            "stock-move-create-two-warehouses",
            "pageErrors",
            "failedRequests",
        ):
            with self.subTest(required=required):
                self.assertIn(required, source)

    def test_stock_lifecycle_probe_checks_multi_line_rollback_and_competition(self):
        source = (ROOT / "scripts/verification/erp_stock_lifecycle_probe.py").read_text()
        for required in (
            "insufficient_out",
            "before_stock = self.stock()",
            "before_records = self.sql(\"SELECT COUNT(*) FROM erp_stock_record;\")",
            "self.get(\"stock-out\", insufficient_out)[\"status\"]",
            "insufficient_stock_rolls_back_prior_line_status_and_records",
            "concurrent_stock_out_one_approved_one_rejected",
        ):
            with self.subTest(required=required):
                self.assertIn(required, source)

    def test_current_stock_lifecycle_runner_is_pinned_and_isolated(self):
        source = (ROOT / "scripts/verification/erp_stock_lifecycle_current_runner.py").read_text()
        for required in (
            "4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1",
            "yuheng_t4_stock_lifecycle_20261123_current",
            "yh-erp-stock-lifecycle-current-mysql-20261123",
            "--mysql-container",
            "cleanup",
        ):
            with self.subTest(required=required):
                self.assertIn(required, source)

    def test_runner_uses_isolated_package_and_checks_stock_rows_and_records(self):
        source = (ROOT / "scripts/verification/erp_stock_browser_runner.py").read_text()
        for required in (
            "yuheng_t4_erp_stock_browser_",
            "jar_sha256",
            "jar_dist_byte_match",
            "erp_stock_check_item",
            "erp_stock_move_item",
            "erp_stock_record",
            "seed_passwords_unchanged",
            "cleanup",
        ):
            with self.subTest(required=required):
                self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
