import unittest
from pathlib import Path

from scripts.verification.member_lifecycle_probe import LifecycleProbe


class MemberLifecycleProbeContractTests(unittest.TestCase):
    def test_probe_has_config_and_default_address_lifecycle_contract(self):
        text = Path("scripts/verification/member_lifecycle_probe.py").read_text()
        for marker in (
            "/member/config/save",
            "/member/config/get",
            "/member/address/create",
            "/member/address/update",
            "/member/address/get-default",
            "/member/address/delete?id=%d",
            "deleting_default_leaves_no_default",
            "/member/user/update-level",
            "grant_updates_member_and_records",
            "revoke_clears_member_level_and_experience",
            "def exercise_account_lifecycle(",
            "/member/auth/send-sms-code",
            "/member/user/update-mobile",
            "/member/user/update-password",
            "old_password_login_rejected",
            "/member/user/reset-password",
            "reset_password_sms_code_rejected_without_write",
            "new_password_login_accepted_after_reset",
            "occupied_mobile_rejected_without_sms_or_member_write",
            "invalid_mobile_code_rejected_without_update",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_probe_uses_separate_admin_and_app_api_prefixes(self):
        text = Path("scripts/verification/member_lifecycle_probe.py").read_text()
        self.assertIn("/admin-api", text)
        self.assertIn("/app-api", text)


if __name__ == "__main__":
    unittest.main()
