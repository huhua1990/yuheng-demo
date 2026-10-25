import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("sync-specs-api.py")


def load_module():
    spec = importlib.util.spec_from_file_location("yuheng_sync_specs", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SyncSpecsApiTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def build_source(self, root):
        (root / "governance/rules").mkdir(parents=True)
        (root / "governance/skills/yuheng-full-workflow").mkdir(parents=True)
        (root / "ai-knowledge-core/server").mkdir(parents=True)
        (root / "ai-knowledge-core/ui").mkdir(parents=True)
        (root / "ai-knowledge-core/data").mkdir(parents=True)
        (root / "release").mkdir(parents=True)
        (root / "governance/rules/entry.md").write_text("rule", encoding="utf-8")
        (root / "governance/skills/yuheng-full-workflow/SKILL.md").write_text(
            "skill", encoding="utf-8"
        )
        for track in ("server", "ui", "data"):
            (root / "ai-knowledge-core" / track / "overview.md").write_text(
                track, encoding="utf-8"
            )
        (root / "release/yuheng-manifest.yaml").write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "project": {"id": "yuheng-core", "kind": "framework"},
                    "codeVersion": "0.1.0",
                    "artifacts": {
                        "server": "com.yuheng:yuheng-server:0.1.0",
                        "ui": "yuheng-ui@0.1.0",
                    },
                    "governanceVersion": "0.1.0",
                    "knowledgeVersion": "0.1.0",
                    "overlayVersion": "core-2026.10.25",
                    "compatibility": {
                        "code": ">=0.1.0 <1.0.0",
                        "governance": ">=0.1.0 <1.0.0",
                        "knowledge": ">=0.1.0 <1.0.0",
                    },
                    "knowledgeTracks": ["server", "ui", "data"],
                    "sourceCommit": "54600e6",
                    "generatedAt": "2026-10-25T12:00:00+08:00",
                    "overlays": [],
                }
            ),
            encoding="utf-8",
        )

    def test_check_is_read_only_and_protects_consumer_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            source = workspace / "core"
            target = workspace / "consumer"
            self.build_source(source)
            (target / "docs/specs").mkdir(parents=True)
            (target / "business").mkdir()
            (target / "consumer-overlay").mkdir()
            (target / "docs/specs/keep.md").write_text("keep", encoding="utf-8")
            report = self.module.sync_bundle(source, target, mode="check")
            self.assertEqual(report["status"], "PASS", report)
            self.assertFalse((target / "yuheng-rules").exists())
            self.assertEqual(
                (target / "docs/specs/keep.md").read_text(encoding="utf-8"),
                "keep",
            )

    def test_apply_updates_managed_snapshot_without_touching_business_files(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            source = workspace / "core"
            target = workspace / "consumer"
            self.build_source(source)
            (target / "business").mkdir(parents=True)
            (target / "business/domain.txt").write_text("business", encoding="utf-8")
            (target / "yuheng-rules").mkdir()
            (target / "yuheng-rules/old.md").write_text("old", encoding="utf-8")
            report = self.module.sync_bundle(source, target, mode="apply")
            self.assertEqual(report["status"], "PASS", report)
            self.assertEqual(
                (target / "yuheng-rules/entry.md").read_text(encoding="utf-8"),
                "rule",
            )
            self.assertFalse((target / "yuheng-rules/old.md").exists())
            self.assertEqual(
                (target / "business/domain.txt").read_text(encoding="utf-8"),
                "business",
            )
            verify_report = self.module.sync_bundle(source, target, mode="verify")
            self.assertEqual(verify_report["status"], "PASS", verify_report)

    def test_apply_rejects_symlinked_managed_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            source = workspace / "core"
            target = workspace / "consumer"
            self.build_source(source)
            target.mkdir()
            outside = workspace / "outside"
            outside.mkdir()
            (target / "yuheng-rules").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(self.module.SyncError):
                self.module.sync_bundle(source, target, mode="apply")


if __name__ == "__main__":
    unittest.main()
