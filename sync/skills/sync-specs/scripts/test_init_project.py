import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("init-project.py")


def load_module():
    spec = importlib.util.spec_from_file_location("yuheng_init_project", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class InitProjectTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_init_creates_consumer_layout_and_preserves_existing_docs(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            source = workspace / "core"
            target = workspace / "consumer"
            (source / "governance/rules").mkdir(parents=True)
            (source / "governance/skills/workflow").mkdir(parents=True)
            (source / "ai-knowledge-core/server").mkdir(parents=True)
            (source / "ai-knowledge-core/ui").mkdir(parents=True)
            (source / "ai-knowledge-core/data").mkdir(parents=True)
            (source / "release").mkdir()
            (source / "governance/rules/entry.md").write_text("rule", encoding="utf-8")
            (source / "governance/skills/workflow/SKILL.md").write_text(
                "skill", encoding="utf-8"
            )
            for track in ("server", "ui", "data"):
                (source / "ai-knowledge-core" / track / "overview.md").write_text(
                    track, encoding="utf-8"
                )
            (source / "release/yuheng-manifest.yaml").write_text(
                "schemaVersion: 1\nproject:\n  id: yuheng-core\n  kind: framework\n"
                "codeVersion: 0.1.0\ngovernanceVersion: 0.1.0\nknowledgeVersion: 0.1.0\n"
                "overlayVersion: core-2026.10.25\nsourceCommit: 54600e6\n"
                "generatedAt: 2026-10-25T12:00:00+08:00\n",
                encoding="utf-8",
            )
            (target / "docs/specs").mkdir(parents=True)
            (target / "docs/specs/keep.md").write_text("keep", encoding="utf-8")

            result = self.module.init_project(source, target, "yuheng-demo")

            self.assertEqual(result["status"], "PASS", result)
            self.assertTrue((target / ".yuheng/project.yaml").exists())
            self.assertTrue((target / "docs/plans").is_dir())
            self.assertTrue((target / "docs/verification").is_dir())
            self.assertTrue((target / "consumer-overlay").is_dir())
            self.assertTrue((target / "yuheng-rules/entry.md").exists())
            self.assertEqual(
                (target / "docs/specs/keep.md").read_text(encoding="utf-8"),
                "keep",
            )


if __name__ == "__main__":
    unittest.main()
