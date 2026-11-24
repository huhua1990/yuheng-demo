import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/verification"))
from erp_workflow_probe import Probe
from erp_p2_sidecar_runner import redact_backend_log


class ErpProbeChangelogTest(unittest.TestCase):
    def test_accepts_current_expanded_liquibase_baseline(self):
        self.assertEqual(Probe.installed_changesets("105"), 105)

    def test_rejects_incomplete_liquibase_baseline(self):
        with self.assertRaisesRegex(AssertionError, "incomplete Liquibase installation: 53"):
            Probe.installed_changesets("53")

    def test_erp_acceptance_probes_share_expanded_baseline_guard(self):
        probe_dir = ROOT / "scripts/verification"
        probes = (
            "erp_finance_edit_probe.py",
            "erp_finance_owner_probe.py",
        )
        for name in probes:
            with self.subTest(probe=name):
                source = (probe_dir / name).read_text()
                self.assertIn('self.installed_changesets(self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;"))', source)

    def test_audit_status_probe_rejects_incomplete_current_baseline(self):
        source = (ROOT / "scripts/verification/erp_audit_status_probe.py").read_text()
        self.assertIn("MIN_CHANGESETS = 59", source)
        self.assertIn("incomplete Liquibase installation", source)

    def test_disposable_probe_schemas_allow_isolated_suffixes(self):
        for name, prefix in (
            ("erp_stock_lifecycle_probe.py", "yuheng_t4_stock_lifecycle"),
            ("erp_audit_status_probe.py", "yuheng_t4_status"),
        ):
            with self.subTest(probe=name):
                source = (ROOT / "scripts/verification" / name).read_text()
                self.assertIn(prefix + r"_[0-9]{8}(?:_[a-z0-9]+)?", source)

    def test_sidecar_backend_logs_redact_credentials_and_tokens(self):
        line = ('{"username":"probe","password":"plain-secret"} '
                'password=property-secret Authorization: Bearer abc.def-token')
        redacted = redact_backend_log(line)
        self.assertNotIn("plain-secret", redacted)
        self.assertNotIn("property-secret", redacted)
        self.assertNotIn("abc.def-token", redacted)
        self.assertEqual(redacted.count("[REDACTED]"), 3)


if __name__ == "__main__":
    unittest.main()
