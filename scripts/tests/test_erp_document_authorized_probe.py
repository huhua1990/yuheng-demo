import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "verification"))

from erp_document_authorized_probe import PERMISSIONS, validate_target  # noqa: E402


class ErpDocumentAuthorizedProbeTest(unittest.TestCase):
    def test_accepts_disposable_target(self):
        self.assertTrue(validate_target(
            "yuheng_t4_erp_document_auth_20261122", 48239, 13394, 16475
        ))

    def test_rejects_shared_or_reserved_target(self):
        with self.assertRaises(ValueError):
            validate_target("yuheng_demo", 48239, 13394, 16475)
        with self.assertRaises(ValueError):
            validate_target("yuheng_t4_erp_document_auth_20261122", 48080, 13394, 16475)

    def test_covers_each_document_write_and_query_boundary(self):
        documents = (
            "purchase-order", "purchase-in", "sale-order", "sale-out",
            "finance-payment", "finance-receipt",
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
