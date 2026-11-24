import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "verification"))

from erp_auxiliary_authorized_probe import PERMISSIONS, validate_target  # noqa: E402


class ErpAuxiliaryAuthorizedProbeTest(unittest.TestCase):
    def test_accepts_disposable_target(self):
        self.assertTrue(validate_target(
            "yuheng_t4_erp_aux_auth_20261122", 48240, 13395, 16476
        ))

    def test_rejects_shared_or_reserved_target(self):
        with self.assertRaises(ValueError):
            validate_target("yuheng_demo", 48240, 13395, 16476)
        with self.assertRaises(ValueError):
            validate_target("yuheng_t4_erp_aux_auth_20261122", 48080, 13395, 16476)

    def test_covers_source_return_and_stock_auxiliary_documents(self):
        documents = (
            "purchase-order", "purchase-in", "purchase-return",
            "sale-order", "sale-out", "sale-return",
            "stock-in", "stock-out", "stock-check", "stock-move",
        )
        for document in documents:
            with self.subTest(document=document):
                self.assertEqual(
                    {permission.rsplit(":", 1)[1] for permission in PERMISSIONS
                     if permission.startswith("erp:" + document + ":")},
                    {"create", "query", "export", "update-status"},
                )


if __name__ == "__main__":
    unittest.main()
