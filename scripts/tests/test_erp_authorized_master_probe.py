import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "verification"))

from erp_authorized_master_probe import PERMISSIONS, validate_target  # noqa: E402


class ErpAuthorizedMasterProbeTest(unittest.TestCase):
    def test_accepts_disposable_target(self):
        self.assertTrue(validate_target("yuheng_t4_erp_auth_20261122", 48237))

    def test_rejects_shared_or_reserved_target(self):
        with self.assertRaises(ValueError):
            validate_target("yuheng_demo", 48237)
        with self.assertRaises(ValueError):
            validate_target("yuheng_t4_erp_auth_20261122", 48080)

    def test_permission_contract_covers_all_master_crud_operations(self):
        for resource in (
            "product-category", "product-unit", "supplier", "customer",
            "account", "warehouse", "product",
        ):
            with self.subTest(resource=resource):
                self.assertEqual(
                    {item.rsplit(":", 1)[1] for item in PERMISSIONS
                     if item.startswith("erp:" + resource + ":")},
                    {"create", "query", "update", "delete"},
                )


if __name__ == "__main__":
    unittest.main()
