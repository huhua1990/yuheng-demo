import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "verification"))
from erp_item_owner_http_probe import OwnerProbe
from erp_item_owner_update_http_probe import UpdateOwnerProbe


class BaselineTest(unittest.TestCase):
    def test_both_probes_accept_expanded_baseline_before_snapshot(self):
        for probe_class in (OwnerProbe, UpdateOwnerProbe):
            with self.subTest(probe=probe_class.__name__):
                probe = probe_class(SimpleNamespace(schema="disposable"))
                probe.sql = Mock(side_effect=["disposable", "59", "0"])
                probe.snapshot = Mock(side_effect=RuntimeError("snapshot reached"))
                with self.assertRaisesRegex(RuntimeError, "snapshot reached"):
                    probe.run()

    def test_both_probes_reject_incomplete_baseline(self):
        for probe_class in (OwnerProbe, UpdateOwnerProbe):
            with self.subTest(probe=probe_class.__name__):
                probe = probe_class(SimpleNamespace(schema="disposable"))
                probe.sql = Mock(side_effect=["disposable", "53", "0"])
                with self.assertRaises(AssertionError):
                    probe.run()


if __name__ == "__main__":
    unittest.main()
