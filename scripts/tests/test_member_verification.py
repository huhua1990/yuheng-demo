import unittest


from scripts.verification.p2_member_platform_probe import (
    REQUIRED_CASES,
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
                "cleanup": True,
            },
        )

    def test_sql_literal_escapes_probe_values(self):
        self.assertEqual(sql_literal("member 'probe'"), "'member ''probe'''" )


if __name__ == "__main__":
    unittest.main()
