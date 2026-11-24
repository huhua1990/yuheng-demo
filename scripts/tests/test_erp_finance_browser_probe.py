import unittest

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ErpFinanceBrowserProbeTest(unittest.TestCase):
    def test_browser_probe_covers_desktop_receipt_to_source_amount(self):
        source = (ROOT / "scripts/verification/erp_finance_browser_probe.js").read_text()
        for required in (
            "width: 1440, height: 900",
            "/erp/finance/receipt",
            "P2 Sales Customer",
            "/admin-api/erp/finance-receipt/create",
            "/admin-api/erp/finance-receipt/update-status",
            "/erp/finance/payment",
            "P2 Purchase Supplier",
            "/admin-api/erp/finance-payment/create",
            "/admin-api/erp/finance-payment/update-status",
            "pageErrors",
            "failedRequests",
        ):
            with self.subTest(required=required):
                self.assertIn(required, source)

    def test_runner_uses_disposable_resources_and_reconciles_finance_sql(self):
        source = (ROOT / "scripts/verification/erp_finance_browser_runner.py").read_text()
        for required in (
            "yuheng_t4_finance_browser_",
            "127.0.0.1:",
            "jar_sha256",
            "jar_dist_byte_match",
            "DATABASECHANGELOG",
            "erp_finance_receipt_item",
            "erp_sale_out",
            "erp_finance_payment_item",
            "erp_purchase_in",
            "seed_passwords_unchanged",
            "cleanup",
        ):
            with self.subTest(required=required):
                self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
