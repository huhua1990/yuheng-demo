import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class ErpRefundBrowserProbeTest(unittest.TestCase):
    def test_probe_covers_purchase_and_sale_return_refunds(self):
        source = (ROOT / "scripts/verification/erp_refund_browser_probe.js").read_text()
        for required in (
            "width: 1440, height: 900",
            "/erp/finance/receipt",
            "添加销售退货单",
            "/admin-api/erp/sale-return/page",
            "/admin-api/erp/finance-receipt/create",
            "/erp/finance/payment",
            "添加采购退货单",
            "/admin-api/erp/purchase-return/page",
            "/admin-api/erp/finance-payment/create",
            "saleRefundInput",
            "purchaseRefundInput",
            "amount.fill('-2')",
            "amount.fill('-3')",
            "strictEqual(await amount.inputValue(), '-2.00')",
            "strictEqual(await amount.inputValue(), '-3.00')",
            "failedRequests",
        ):
            with self.subTest(required=required):
                self.assertIn(required, source)

    def test_runner_isolates_refund_sql_and_records_cleanup(self):
        source = (ROOT / "scripts/verification/erp_refund_browser_runner.py").read_text()
        for required in (
            "yuheng_t4_refund_browser_",
            "erp_sale_return",
            "erp_purchase_return",
            "erp_finance_receipt_item",
            "erp_finance_payment_item",
            "refund_price",
            "-sale_refund:.6f",
            "-purchase_refund:.6f",
            "jar_sha256",
            "seed_passwords_unchanged",
            "cleanup",
        ):
            with self.subTest(required=required):
                self.assertIn(required, source)

    def test_refund_selectors_match_seeded_customer_and_supplier(self):
        runner = (ROOT / "scripts/verification/erp_refund_browser_runner.py").read_text()
        probe = (ROOT / "scripts/verification/erp_refund_browser_probe.js").read_text()
        self.assertIn("'P2 Sales Customer'", runner)
        self.assertIn("'P2 Purchase Supplier'", runner)
        self.assertIn("name: 'P2 Sales Customer'", probe)
        self.assertIn("name: 'P2 Purchase Supplier'", probe)
        self.assertIn("'P2 Sales Customer'", runner)
        self.assertIn("'P2 Purchase Supplier'", runner)
        self.assertIn('("backend.log", "ui.log")', runner)
        self.assertIn("log_path.unlink()", runner)
        self.assertIn("request_queue_size=128", runner)


if __name__ == "__main__":
    unittest.main()
