import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class CrmCustomerProbeContractTest(unittest.TestCase):
    def test_browser_role_receives_crm_root_and_customer_page_menus(self):
        source = (ROOT / "scripts/verification/p2_crm_customer_runner.py").read_text(encoding="utf-8")

        self.assertIn("component='crm/customer/index'", source)
        self.assertIn("path='/crm'", source)
        self.assertIn("CRM_MENU_IDS", source)
        self.assertIn("menu_ids = CRM_MENU_IDS | set(permission_ids.values())", source)

    def test_browser_uses_unique_customer_table_header_locator(self):
        source = (ROOT / "scripts/verification/p2_crm_customer_browser_probe.js").read_text(encoding="utf-8")

        self.assertIn("getByRole('columnheader', { name: '客户名称', exact: true })", source)

    def test_customer_is_created_before_browser_page_reads_it(self):
        source = (ROOT / "scripts/verification/p2_crm_customer_runner.py").read_text(encoding="utf-8")

        self.assertLess(source.index('call(base, "POST", "/crm/customer/create"'),
                        source.index('subprocess.run(["node", str(ROOT / "scripts/verification/p2_crm_customer_browser_probe.js")]'))


if __name__ == "__main__":
    unittest.main()
