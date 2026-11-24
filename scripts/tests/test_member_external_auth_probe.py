import unittest


from scripts.verification.p2_member_external_auth_probe import (
    AUTH_CASES,
    Probe,
    ROOT,
    sanitized_log_excerpt,
    validate_probe_target,
)


class MemberExternalAuthProbeContractTests(unittest.TestCase):
    def test_probe_refuses_shared_resources(self):
        self.assertTrue(validate_probe_target("yuheng_p2_member_auth_20261122", 48255))
        with self.assertRaises(ValueError):
            validate_probe_target("yuheng_demo", 48255)
        with self.assertRaises(ValueError):
            validate_probe_target("yuheng_p2_member_auth_20261122", 48080)

    def test_probe_covers_external_auth_failure_boundaries(self):
        self.assertEqual(
            AUTH_CASES,
            {
                "sms_validation": True,
                "sms_send_configured_channel": True,
                "sms_invalid_code": True,
                "sms_login_success": True,
                "sms_login_creates_member_and_token": True,
                "social_validation": True,
                "social_invalid_code": True,
                "weixin_validation": True,
                "weixin_invalid_code": True,
                "failed_requests_no_member_or_binding": True,
                "failed_requests_no_oauth_token": True,
                "seed_passwords_unchanged": True,
                "cleanup": True,
            },
        )

    def test_installed_changesets_rejects_incomplete_install(self):
        self.assertEqual(Probe.installed_changesets("59"), 59)
        with self.assertRaisesRegex(AssertionError, "incomplete Liquibase installation: 54"):
            Probe.installed_changesets("54")

    def test_probe_source_declares_all_member_external_auth_routes(self):
        source = (ROOT / "scripts/verification/p2_member_external_auth_probe.py").read_text()
        for marker in (
            "/member/auth/send-sms-code",
            "/member/auth/validate-sms-code",
            "/member/auth/sms-login",
            "/member/auth/social-auth-redirect",
            "/member/auth/social-login",
            "/member/auth/weixin-mini-app-login",
        ):
            with self.subTest(route=marker):
                self.assertIn(marker, source)

    def test_success_result_never_records_access_or_refresh_tokens(self):
        source = (ROOT / "scripts/verification/p2_member_external_auth_probe.py").read_text()
        self.assertIn("access_token_recorded", source)
        self.assertIn("refresh_token_recorded", source)
        self.assertIn("accessToken", source)
        self.assertNotIn('"accessToken": data', source)

    def test_log_excerpt_redacts_provider_credentials(self):
        log_file = ROOT / "docs/verification/2026-11-11-full-source-migration/p2-member-external-auth-20261122/.test-application.log"
        try:
            log_file.write_text(
                "ERROR https://api.example.test/callback?access_token=secret-token\n"
                "java.lang.IllegalStateException: provider failed\n"
                " at example.Provider.call(Provider.java:1)\n"
            )
            excerpt = sanitized_log_excerpt(log_file)
        finally:
            log_file.unlink(missing_ok=True)

        self.assertIn("<redacted-url>", excerpt)
        self.assertNotIn("secret-token", excerpt)

    def test_current_runner_uses_fixed_jar_and_separate_isolated_resources(self):
        source = (ROOT / "scripts/verification/p2_member_external_auth_current_runner.py").read_text()
        for marker in (
            "4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1",
            "yuheng_p2_member_auth_20261123_current",
            "yh-p2-member-auth-current-mysql-20261123",
            "p2-member-external-auth-current-20261123",
            "credentials_recorded",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, source)

    def test_current_runner_rewrites_only_isolated_probe_coordinates(self):
        source = (ROOT / "scripts/verification/p2_member_external_auth_current_runner.py").read_text()
        self.assertIn('"yuheng_p2_member_auth_20261122"', source)
        self.assertIn('"yuheng_p2_member_auth_20261123_current"', source)
        self.assertIn("48255, 13388, 16468", source)
        self.assertIn("48278, 13436, 16491", source)
        self.assertIn("temp_probe.unlink(missing_ok=True)", source)


if __name__ == "__main__":
    unittest.main()
