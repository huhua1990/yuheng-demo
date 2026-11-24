import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "verification"))

from member_permission_matrix_probe import (  # noqa: E402
    MEMBER_READ_CASES,
    MEMBER_WRITE_CASES,
    validate_probe_target,
)


class MemberPermissionMatrixProbeTest(unittest.TestCase):
    def test_current_target_is_disposable(self):
        self.assertTrue(validate_probe_target(
            "yuheng_t4_member_acl_20261123", 48260, 13399, 16480
        ))

    def test_inventory_covers_all_member_permission_families(self):
        permissions = {case.permission for case in (*MEMBER_READ_CASES, *MEMBER_WRITE_CASES)}
        self.assertIn("member:user:query", permissions)
        self.assertIn("member:tag:create", permissions)
        self.assertIn("point:sign-in-config:delete", permissions)
        self.assertIn("point:record:query", permissions)

    def test_write_cases_have_nonempty_request_bodies(self):
        self.assertTrue(MEMBER_WRITE_CASES)
        for case in MEMBER_WRITE_CASES:
            with self.subTest(case=case.path):
                self.assertTrue(case.body)


if __name__ == "__main__":
    unittest.main()
