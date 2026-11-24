import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "verification"))

from erp_full_tenant_permission_probe import (  # noqa: E402
    BUSINESS_TABLES,
    FIXTURE_KEYS,
    RESOURCE_MATRIX,
    TENANTS,
    make_probe_password,
    validate_probe_target,
)
from erp_full_tenant_permission_runner import redact_backend_log  # noqa: E402


class ErpFullTenantPermissionProbeTest(unittest.TestCase):
    def test_target_is_disposable_and_never_shared(self):
        self.assertTrue(validate_probe_target(
            "yuheng_t4_erp_full_tenant_20261122", 48242, 13397, 16478
        ))
        for values in (
            ("yuheng_demo", 48242, 13397, 16478),
            ("yuheng_t4_erp_full_tenant_20261122", 48080, 13397, 16478),
            ("yuheng_t4_erp_full_tenant_20261122", 48242, 3306, 16478),
            ("yuheng_t4_erp_full_tenant_20261122", 48242, 13397, 6379),
        ):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    validate_probe_target(*values)

    def test_matrix_covers_every_erp_controller_family_and_business_table(self):
        self.assertEqual(len(RESOURCE_MATRIX), 23)
        self.assertEqual(len(BUSINESS_TABLES), 33)
        self.assertEqual(TENANTS, (121, 122))
        self.assertIn("purchase-order", RESOURCE_MATRIX)
        self.assertIn("finance-payment", RESOURCE_MATRIX)
        self.assertIn("statistics-purchase", RESOURCE_MATRIX)
        self.assertIn("erp_finance_payment_item", BUSINESS_TABLES)

    def test_matrix_requires_cross_tenant_read_and_write_assertions(self):
        for name, spec in RESOURCE_MATRIX.items():
            with self.subTest(resource=name):
                self.assertIn("detail", spec)
                self.assertIn("page", spec)
                self.assertIn("foreign_write", spec)
                self.assertIn("permission", spec)
        self.assertEqual(FIXTURE_KEYS["product-category"], "category")
        self.assertEqual(FIXTURE_KEYS["product-unit"], "unit")

    def test_category_list_declares_list_response_shape(self):
        self.assertEqual(RESOURCE_MATRIX["product-category"]["page_shape"], "list")

    def test_foreign_delete_allows_upstream_success_noop_contract(self):
        source = (ROOT / "scripts" / "verification" /
                  "erp_full_tenant_permission_probe.py").read_text()
        self.assertIn("foreign_delete_success_noop", source)

    def test_probe_records_sql_unchanged_for_foreign_writes(self):
        source = (ROOT / "scripts" / "verification" /
                  "erp_full_tenant_permission_probe.py").read_text()
        self.assertIn("foreign_write_sql_unchanged", source)
        self.assertIn("TENANTS", source)

    def test_fixture_password_matches_core_login_length_contract(self):
        password = make_probe_password()
        self.assertGreaterEqual(len(password), 4)
        self.assertLessEqual(len(password), 16)

    def test_full_tenant_runner_redacts_passwords_and_bearer_tokens(self):
        line = '{"password":"secret"} password=property-secret Bearer abc.def-token'
        redacted = redact_backend_log(line)
        for secret in ("secret", "property-secret", "abc.def-token"):
            self.assertNotIn(secret, redacted)
        self.assertEqual(redacted.count("[REDACTED]"), 3)


if __name__ == "__main__":
    unittest.main()
