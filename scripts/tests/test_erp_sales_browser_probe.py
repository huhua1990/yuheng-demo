import unittest

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ErpSalesBrowserProbeTest(unittest.TestCase):
    def test_browser_probe_covers_desktop_sales_order_to_stock_out(self):
        source = (ROOT / "scripts/verification/erp_sales_browser_probe.js").read_text()
        for required in (
            "width: 1440, height: 900",
            "/erp/sale/order",
            "/erp/sale/out",
            "/erp/sale/return",
            "/admin-api/erp/sale-order/create",
            "/admin-api/erp/sale-out/create",
            "/admin-api/erp/sale-return/create",
            "sale-order/update-status",
            "sale-out/update-status",
            "sale-return/update-status",
            "YUHENG_PROBE_USERNAME",
            "YUHENG_PROBE_PASSWORD",
            "pageErrors",
            "failedRequests",
        ):
            with self.subTest(required=required):
                self.assertIn(required, source)

    def test_runner_uses_dedicated_resources_and_current_package_hash(self):
        source = (ROOT / "scripts/verification/erp_sales_browser_runner.py").read_text()
        for required in (
            "yuheng_t4_erp_sales_browser_",
            "127.0.0.1:",
            "jar_sha256",
            "cleanup",
            "erp_sales_browser_probe.js",
        ):
            with self.subTest(required=required):
                self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
