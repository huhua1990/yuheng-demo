import unittest


from scripts.verification.p2_member_platform_probe import (
    Probe,
    REQUIRED_CASES,
    ROOT,
    sql_literal,
    validate_probe_target,
)


class MemberPlatformProbeContractTests(unittest.TestCase):
    def test_probe_refuses_shared_schema_and_application_ports(self):
        self.assertTrue(validate_probe_target("yuheng_p2_member_20261117", 48220))
        with self.assertRaises(ValueError):
            validate_probe_target("yuheng_demo", 48220)
        with self.assertRaises(ValueError):
            validate_probe_target("yuheng_p2_member_20261117", 48080)

    def test_probe_contract_covers_member_consumer_acceptance(self):
        self.assertEqual(
            REQUIRED_CASES,
            {
                "member_crud": True,
                "member_user_update": True,
                "unauthorized_write_rejected": True,
                "tenant_header_rejected": True,
                "point_transaction": True,
                "member_app_login": True,
                "address_owner_isolation": True,
                "sign_in_rule_lifecycle": True,
                "sign_in_rewards_lifecycle": True,
                "sign_in_concurrency": True,
                "cleanup": True,
            },
        )

    def test_sql_literal_escapes_probe_values(self):
        self.assertEqual(sql_literal("member 'probe'"), "'member ''probe'''" )

    def test_accepts_expanded_liquibase_baseline_and_rejects_incomplete_install(self):
        self.assertEqual(Probe.installed_changesets("59"), 59)
        with self.assertRaisesRegex(AssertionError, "incomplete Liquibase installation: 53"):
            Probe.installed_changesets("53")

    def test_member_browser_probe_covers_all_top_level_read_pages(self):
        source = (ROOT / "scripts/verification/p2_member_browser_probe.js").read_text()
        for marker in (
            "/admin-api/member/group/page",
            "/admin-api/member/level/list",
            "/admin-api/member/point/record/page",
            "/admin-api/member/sign-in/config/list",
            "/admin-api/member/sign-in/record/page",
            "/admin-api/member/config/get",
        ):
            with self.subTest(api=marker):
                self.assertIn(marker, source)

    def test_member_probe_covers_app_password_login_and_address_ownership(self):
        source = (ROOT / "scripts/verification/p2_member_platform_probe.py").read_text()
        for marker in (
            "'/member/auth/login'",
            "'/member/address/create'",
            "'/member/address/get?id=",
            "address_owner_isolation",
            "expected=400",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, source)

    def test_sign_in_probe_contract_covers_rewards_rollback_and_duplicate(self):
        source = (ROOT / "scripts/verification/p2_member_platform_probe.py").read_text()
        for marker in (
            "def exercise_sign_in_rewards(",
            "expected=1004010000",
            "member_experience_record",
            "member_level_record",
            "member_sign_in_record",
            "sign_in_experience_failure",
            "sign_in_level_failure",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, source)

    def test_sign_in_probe_contract_covers_same_member_concurrent_requests(self):
        source = (ROOT / "scripts/verification/p2_member_platform_probe.py").read_text()
        for marker in (
            "def exercise_concurrent_sign_in(",
            "ThreadPoolExecutor(max_workers=2)",
            "sign_in_concurrency",
            "one_success_one_duplicate",
            "id > 991055",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, source)


if __name__ == "__main__":
    unittest.main()
