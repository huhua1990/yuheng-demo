import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "p2_pay_pms_consumer_probe", ROOT / "verification/p2_pay_pms_consumer_probe.py"
)
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


class PayPmsPermissionContractTests(unittest.TestCase):
    def test_limited_role_permissions_cover_only_the_successful_probe_flows(self):
        self.assertEqual(
            set(probe.LIMITED_ROLE_PERMISSIONS),
            {
                "pay:app:create", "pay:app:query", "pay:wallet:query",
                "pay:wallet:update-balance", "pms:pm:project:create",
                "pms:pm:project:update", "pms:pm:project:query",
                "pms:kb:library:create", "pms:kb:library:update",
                "pms:kb:library:query",
            },
        )

    def test_denied_mutations_are_outside_the_limited_role(self):
        self.assertEqual(
            set(probe.DENIED_MUTATIONS),
            {
                ("PUT", "/pay/app/update"),
                ("DELETE", "/pay/app/delete"),
                ("POST", "/pay/channel/create"),
                ("DELETE", "/pms/kb/library/delete"),
                ("POST", "/pms/pm/project/create"),
            },
        )

    def test_probe_uses_business_snapshots_for_rejected_requests(self):
        source = (ROOT / "verification/p2_pay_pms_consumer_probe.py").read_text()
        self.assertIn("before_denied = snapshot_tables(MYSQL)", source)
        self.assertIn("assert before_denied == snapshot_tables(MYSQL)", source)
        self.assertIn("before_spoof = snapshot_tables(MYSQL)", source)
        self.assertIn("assert before_spoof == snapshot_tables(MYSQL)", source)

    def test_cross_tenant_uses_a_separate_authenticated_role(self):
        source = (ROOT / "verification/p2_pay_pms_consumer_probe.py").read_text()
        self.assertIn('headers={"tenant-id": "122"}', source)
        self.assertIn('"cross_tenant_checks": cross_tenant_checks', source)
        self.assertIn('before_cross = snapshot_tables(MYSQL)', source)

    def test_cross_tenant_probe_verifies_sql_ownership_after_each_create(self):
        source = (ROOT / "verification/p2_pay_pms_consumer_probe.py").read_text()
        self.assertIn('"app": "pay_app"', source)
        self.assertIn('"project": "pms_project"', source)
        self.assertIn('"library": "pms_knowledge_library"', source)
        self.assertIn('SELECT tenant_id FROM `{table}` WHERE id=', source)

    def test_optional_browser_probe_uses_desktop_viewport_and_never_records_credentials(self):
        source = (ROOT / "verification/p2_pay_pms_consumer_probe.py").read_text()
        browser = (ROOT / "verification/p2_pay_pms_browser_probe.js").read_text()
        self.assertIn('if os.environ.get("P2_PAY_PMS_BROWSER")', source)
        self.assertIn('"browser": browser_result', source)
        self.assertIn("width: 1440, height: 900", browser)
        self.assertIn(".login-form:visible", browser)
        self.assertNotIn('input[placeholder="请输入用户名"]', browser)
        self.assertIn("pay-app-create", browser)
        self.assertIn("pms-project-create", browser)

    def test_browser_probe_separates_navigation_cancellations_from_failed_requests(self):
        browser = (ROOT / "verification/p2_pay_pms_browser_probe.js").read_text()
        self.assertIn("canceled = []", browser)
        self.assertIn("error === 'net::ERR_ABORTED'", browser)
        self.assertIn("result.canceled = canceled", browser)

    def test_public_share_uses_anonymous_context_without_recording_token(self):
        source = (ROOT / "verification/p2_pay_pms_consumer_probe.py").read_text()
        browser = (ROOT / "verification/p2_pay_pms_browser_probe.js").read_text()
        self.assertIn('P2_SHARE_TOKEN=share["token"]', source)
        self.assertIn("browser.newContext", browser)
        self.assertIn("P2_SHARE_TOKEN", browser)
        self.assertIn("anonymous-share-visible", browser)
        self.assertIn("sanitizeUrl", browser)


if __name__ == "__main__":
    unittest.main()
