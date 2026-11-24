import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "verification"))

from erp_permission_matrix_probe import (  # noqa: E402
    DOCUMENTS,
    READ_CASES,
    WRITE_BODIES,
    validate_probe_target,
)


class ErpPermissionMatrixProbeTest(unittest.TestCase):
    def test_current_target_is_disposable(self):
        self.assertTrue(validate_probe_target(
            "yuheng_t4_erp_acl_20261122", 48236, 13391, 16472
        ))

    def test_each_document_has_a_validation_complete_write_body(self):
        self.assertEqual(set(DOCUMENTS), set(WRITE_BODIES))
        for resource, body in WRITE_BODIES.items():
            with self.subTest(resource=resource):
                self.assertTrue(body.get("items"))

    def test_only_real_simple_reads_are_marked_unprotected(self):
        simple_paths = {case[3] for case in READ_CASES if case[3] is not None}
        self.assertEqual(simple_paths, {
            "/erp/product/simple-list",
            "/erp/product-category/simple-list",
            "/erp/product-unit/simple-list",
            "/erp/supplier/simple-list",
            "/erp/customer/simple-list",
            "/erp/account/simple-list",
            "/erp/warehouse/simple-list",
            "/erp/stock/get-count?productId=1",
        })


if __name__ == "__main__":
    unittest.main()
