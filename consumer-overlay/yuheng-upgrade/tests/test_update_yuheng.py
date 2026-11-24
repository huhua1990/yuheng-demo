import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from update_yuheng import UpgradeError, check_clean_targets, parse_release_manifest, stage_updates


class UpdateYuhengTests(unittest.TestCase):
    def test_reads_core_release_manifest_versions(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = Path(temp) / "release.yaml"
            manifest.write_text(
                "codeVersion: 1.2.3\nartifacts:\n  server: com.yuheng:yuheng-server:1.2.3\n  ui: 'yuheng-ui@1.2.4'\n",
                encoding="utf-8",
            )
            self.assertEqual(
                parse_release_manifest(manifest),
                {"codeVersion": "1.2.3", "server": "1.2.3", "ui": "1.2.4"},
            )

    def test_rejects_missing_or_invalid_artifact_versions(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = Path(temp) / "release.yaml"
            manifest.write_text("codeVersion: 1.2.3\nartifacts:\n  server: bad\n", encoding="utf-8")
            with self.assertRaises(UpgradeError):
                parse_release_manifest(manifest)

    def test_stages_only_dependency_and_release_version_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "yuheng-demo-ui").mkdir()
            (root / "pom.xml").write_text("<yuheng.version>0.1.0-SNAPSHOT</yuheng.version>\n", encoding="utf-8")
            (root / "yuheng-demo-ui/package.json").write_text(
                json.dumps({"dependencies": {"yuheng-ui": "0.1.0-SNAPSHOT", "vue": "3.5.0"}}, indent=2),
                encoding="utf-8",
            )
            consumer_manifest = """codeVersion: 0.1.0-SNAPSHOT
artifacts:
  server: com.yuheng:yuheng-server:0.1.0-SNAPSHOT
  ui: 'yuheng-ui@0.1.0-SNAPSHOT'
governanceVersion: 0.2.0
"""
            (root / "yuheng-manifest.yaml").write_text(consumer_manifest, encoding="utf-8")

            updates = stage_updates(root, {"codeVersion": "1.2.3", "server": "1.2.3", "ui": "1.2.4"})
            self.assertIn("<yuheng.version>1.2.3</yuheng.version>", updates[root / "pom.xml"])
            package = json.loads(updates[root / "yuheng-demo-ui/package.json"])
            self.assertEqual(package["dependencies"]["yuheng-ui"], "1.2.4")
            self.assertEqual(package["dependencies"]["vue"], "3.5.0")
            changed_manifest = updates[root / "yuheng-manifest.yaml"]
            self.assertIn("codeVersion: 1.2.3", changed_manifest)
            self.assertIn("com.yuheng:yuheng-server:1.2.3", changed_manifest)
            self.assertIn("yuheng-ui@1.2.4", changed_manifest)
            self.assertIn("governanceVersion: 0.2.0", changed_manifest)
            self.assertIn("ui: 'yuheng-ui@0.1.0-SNAPSHOT'", consumer_manifest)

    def test_refuses_existing_changes_to_upgrade_targets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            target = root / "pom.xml"
            target.write_text("<project/>\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "pom.xml"], check=True)
            subprocess.run(
                ["git", "-C", str(root), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "baseline"],
                check=True,
            )
            target.write_text("<project>local change</project>\n", encoding="utf-8")
            with self.assertRaises(UpgradeError):
                check_clean_targets(root, [target])


if __name__ == "__main__":
    unittest.main()
