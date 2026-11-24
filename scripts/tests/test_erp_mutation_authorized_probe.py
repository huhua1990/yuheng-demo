import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "verification"))

from erp_mutation_authorized_probe import PERMISSIONS, validate_target  # noqa: E402


class ErpMutationAuthorizedProbeTest(unittest.TestCase):
    def test_accepts_disposable_target(self):
        self.assertTrue(validate_target(
            "yuheng_t4_erp_mutation_auth_20261122", 48241, 13396, 16477
        ))

    def test_rejects_shared_or_reserved_target(self):
        with self.assertRaises(ValueError):
            validate_target("yuheng_demo", 48241, 13396, 16477)
        with self.assertRaises(ValueError):
            validate_target("yuheng_t4_erp_mutation_auth_20261122", 48080, 13396, 16477)

    def test_includes_full_document_write_permission_set(self):
        self.assertEqual({item.rsplit(":", 1)[1] for item in PERMISSIONS},
                         {"create", "query", "export", "update", "update-status", "delete"})


if __name__ == "__main__":
    unittest.main()
