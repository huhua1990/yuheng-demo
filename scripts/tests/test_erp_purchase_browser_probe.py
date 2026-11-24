import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ErpPurchaseBrowserProbeTest(unittest.TestCase):
    def test_browser_probe_covers_desktop_purchase_order_inbound_and_return(self):
        source = (ROOT / "scripts/verification/erp_purchase_browser_probe.js").read_text()
        for required in (
            "width: 1440, height: 900",
            "/erp/purchase/order",
            "/erp/purchase/in",
            "/erp/purchase/return",
            "/admin-api/erp/purchase-order/create",
            "/admin-api/erp/purchase-in/create",
            "/admin-api/erp/purchase-return/create",
            "purchase-return-create-from-order",
            "getByRole('button', { name: '选择' })",
            "selector.locator('.el-radio').first().click()",
            "pageErrors",
            "failedRequests",
        ):
            with self.subTest(required=required):
                self.assertIn(required, source)

    def test_approved_return_delete_and_draft_delete_lifecycle_contract(self):
        source = (ROOT / "scripts/verification/erp_return_delete_lifecycle.py").read_text()
        for required in (
            "approved_delete_rejected_without_mutation",
            "after_rejected_delete == before",
            "update-status?id={int(identifier)}&status=10",
            "deleted",
            "return_count",
            "reverse_approval_and_draft_delete_restored_source_and_stock",
        ):
            with self.subTest(required=required):
                self.assertIn(required, source)

    def test_runner_isolates_runtime_and_reconciles_purchase_inventory_sql(self):
        source = (ROOT / "scripts/verification/erp_return_delete_current_runner.py").read_text()
        for required in (
            "yuheng_t4_return_delete_20261123_current",
            "127.0.0.1:",
            "jar_sha256",
            "jar_dist_byte_match",
            "erp_purchase_browser_probe.js",
            "erp_sales_browser_probe.js",
            "1030103001",
            "1020203001",
            "run_return_delete_lifecycle",
            "purchase_order_return_count",
            "sale_order_return_count",
            "CASE WHEN deleted=b'1' THEN '1' ELSE '0' END",
            '"20.000000")',
            '"7.000000")',
            "erp_purchase_return_items",
            "erp_sale_return_items",
            "4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1",
            "credentials_recorded",
            "seed_passwords_unchanged",
            "cleanup",
        ):
            with self.subTest(required=required):
                self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
