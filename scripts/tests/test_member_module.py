import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
JAVA_ROOT = ROOT / "yuheng-demo-server/yuheng-demo-business/src/main/java/com/yuheng/demo/module/member"
RESOURCE_ROOT = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/src/main/resources/db/changelog/business"
UI_ROOT = ROOT / "yuheng-demo-ui/src"


class MemberModuleBoundaryTests(unittest.TestCase):
    def test_member_backend_is_copied_into_demo_package(self):
        java_files = list(JAVA_ROOT.rglob("*.java"))
        self.assertGreaterEqual(len(java_files), 180)
        self.assertTrue(all("com.yuheng.template.member" not in path.read_text() for path in java_files))
        self.assertTrue(any("com.yuheng.demo.module.member.controller.admin.user" in path.read_text()
                            for path in java_files))

    def test_member_business_changelog_owns_member_tables(self):
        changelog = RESOURCE_ROOT / "changelog.yaml"
        self.assertTrue(changelog.is_file())
        self.assertIn("member/changelog.yaml", changelog.read_text(),
                      "verified member schema must run on demo startup")
        member_changelog = RESOURCE_ROOT / "member/changelog.yaml"
        self.assertIn("001-member-schema.sql", member_changelog.read_text())
        content = (RESOURCE_ROOT / "member/001-member-schema.sql").read_text()
        for table in (
            "member_user",
            "member_address",
            "member_tag",
            "member_level",
            "member_level_record",
            "member_experience_record",
            "member_group",
            "member_point_record",
            "member_sign_in_record",
            "member_sign_in_config",
            "member_config",
        ):
            self.assertIn(table, content)

    def test_member_frontend_is_demo_owned_and_route_resolvable(self):
        self.assertTrue((UI_ROOT / "api/member/user/index.ts").is_file())
        self.assertTrue((UI_ROOT / "views/member/user/index.vue").is_file())
        routes = (UI_ROOT / "router/business.ts").read_text()
        self.assertIn("businessViewComponents", routes)
        self.assertIn("../views/member/", routes)


if __name__ == "__main__":
    unittest.main()
