import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "verification"))

from erp_tenant_permission_probe import (  # noqa: E402
    REQUIRED_PERMISSIONS,
    Probe,
    validate_probe_target,
)


class ErpTenantPermissionProbeTest(unittest.TestCase):
    def test_accepts_disposable_target_and_current_permission_contract(self):
        self.assertTrue(validate_probe_target(
            "yuheng_t4_erp_tenant_20261122", 48235, 13390, 16471
        ))
        self.assertEqual(len(REQUIRED_PERMISSIONS), 8)
        self.assertIn("erp:product:create", REQUIRED_PERMISSIONS)
        self.assertIn("erp:warehouse:update", REQUIRED_PERMISSIONS)

    def test_rejects_shared_or_reserved_targets(self):
        for schema, app_port, mysql_port, redis_port in (
            ("yuheng_demo", 48235, 13390, 16471),
            ("yuheng_t4_erp_tenant_20261122", 48080, 13390, 16471),
            ("yuheng_t4_erp_tenant_20261122", 48235, 3306, 16471),
            ("yuheng_t4_erp_tenant_20261122", 48235, 13390, 6379),
        ):
            with self.subTest(schema=schema, app_port=app_port,
                              mysql_port=mysql_port, redis_port=redis_port):
                with self.assertRaises(ValueError):
                    validate_probe_target(schema, app_port, mysql_port, redis_port)

    def test_permission_contract_has_distinct_create_query_update_delete_actions(self):
        grouped = {}
        for permission in REQUIRED_PERMISSIONS:
            resource, action = permission.removeprefix("erp:").split(":")
            grouped.setdefault(resource, set()).add(action)
        self.assertEqual(grouped["product"], {"create", "query", "update", "delete"})
        self.assertEqual(grouped["warehouse"], {"create", "query", "update", "delete"})

    def test_probe_has_separate_tokens_for_allowed_and_denied_users(self):
        source = (ROOT / "scripts" / "verification" / "erp_tenant_permission_probe.py").read_text()
        self.assertIn('self.tokens[label + "_denied"]', source)
        self.assertIn('self.users[label + "_denied"]', source)
        self.assertTrue(hasattr(Probe, "setup_fixtures"))


if __name__ == "__main__":
    unittest.main()
