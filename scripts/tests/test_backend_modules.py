import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
NS = {"m": "http://maven.apache.org/POM/4.0.0"}


class BackendModulesTest(unittest.TestCase):
    def run_build_script(self, jar_in_use):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "yuheng-demo-server/yuheng-demo-server-bootstrap/target").mkdir(parents=True)
            (root / "yuheng-demo-ui").mkdir()
            (root / "yuheng-demo-ui/package.json").write_text(
                '{"dependencies":{"yuheng-ui":"0.1.0-SNAPSHOT"}}\n'
            )
            build_script = root / "scripts/build.sh"
            build_script.write_text((ROOT / "scripts/build.sh").read_text())
            jar = root / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
            jar.touch()

            bin_dir = root / "bin"
            bin_dir.mkdir()
            lsof = bin_dir / "lsof"
            lsof.write_text("#!/bin/sh\nif [ \"$JAR_IN_USE\" = 1 ]; then echo 4242; exit 0; fi\nexit 1\n")
            lsof.chmod(0o755)
            mvn_marker = root / "mvn-ran"
            mvn = bin_dir / "mvn"
            mvn.write_text(f"#!/bin/sh\ntouch '{mvn_marker}'\n")
            mvn.chmod(0o755)
            env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ["PATH"],
                       JAR_IN_USE="1" if jar_in_use else "0")
            result = subprocess.run(["bash", str(build_script)], env=env, capture_output=True, text=True)
            return result, mvn_marker.exists()

    def test_build_refuses_to_repackage_jar_open_by_running_process(self):
        result, mvn_ran = self.run_build_script(jar_in_use=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("后端 JAR 正被运行进程使用", result.stderr)
        self.assertFalse(mvn_ran)

    def test_build_runs_when_target_jar_is_not_open(self):
        result, mvn_ran = self.run_build_script(jar_in_use=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(mvn_ran)

    def test_maven_frontend_build_is_bound_before_resources(self):
        bootstrap = ET.parse(ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/pom.xml").getroot()
        plugins = bootstrap.findall("m:build/m:plugins/m:plugin", NS)
        plugin = next((p for p in plugins if p.findtext("m:artifactId", namespaces=NS) == "exec-maven-plugin"), None)
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.findtext("m:executions/m:execution/m:phase", namespaces=NS), "generate-resources")
        self.assertIn("build-ui.sh", ET.tostring(plugin, encoding="unicode"))

    def test_frontend_build_fails_before_packaging_when_pnpm_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "yuheng-demo-ui").mkdir()
            script = root / "scripts/build-ui.sh"
            script.write_text((ROOT / "scripts/build-ui.sh").read_text())
            (root / "yuheng-demo-ui/package.json").write_text(
                '{"dependencies":{"yuheng-ui":"0.1.0-SNAPSHOT"}}\n'
            )
            pnpm = root / "pnpm"
            pnpm.write_text('#!/bin/sh\nexit 37\n')
            pnpm.chmod(0o755)
            env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ["PATH"])
            result = subprocess.run(["bash", str(script)], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 37, result.stderr)

    def test_frontend_override_rejects_package_with_wrong_version(self):
        import json
        import tarfile
        import io

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "demo"
            (root / "scripts").mkdir(parents=True)
            (root / "yuheng-demo-ui").mkdir()
            module_dir = root / "yuheng-demo-server/yuheng-demo-server-bootstrap"
            module_dir.mkdir(parents=True)
            script = root / "scripts/build-ui.sh"
            script.write_text((ROOT / "scripts/build-ui.sh").read_text())
            (root / "yuheng-demo-ui/package.json").write_text(json.dumps({
                "dependencies": {"yuheng-ui": "0.1.0-SNAPSHOT"}
            }))
            archive = Path(tmp) / "wrong.tgz"
            data = json.dumps({"name": "yuheng-ui", "version": "0.0.0"}).encode()
            with tarfile.open(archive, "w:gz") as package:
                info = tarfile.TarInfo("package/package.json")
                info.size = len(data)
                package.addfile(info, io.BytesIO(data))
            env = dict(os.environ, YUHENG_UI_PACKAGE=str(archive))
            result = subprocess.run(["bash", str(script)], env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("版本不匹配", result.stderr)

    def test_frontend_override_resolves_relative_package_from_demo_root(self):
        import json
        import tarfile
        import io

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "demo"
            (root / "scripts").mkdir(parents=True)
            (root / "yuheng-demo-ui").mkdir()
            module_dir = root / "yuheng-demo-server/yuheng-demo-server-bootstrap"
            module_dir.mkdir(parents=True)
            script = root / "scripts/build-ui.sh"
            script.write_text((ROOT / "scripts/build-ui.sh").read_text())
            (root / "yuheng-demo-ui/package.json").write_text(json.dumps({
                "dependencies": {"yuheng-ui": "0.1.0-SNAPSHOT"}
            }))
            archive = root / "vendor/yuheng-ui.tgz"
            archive.parent.mkdir()
            data = json.dumps({"name": "yuheng-ui", "version": "0.1.0-SNAPSHOT"}).encode()
            with tarfile.open(archive, "w:gz") as package:
                info = tarfile.TarInfo("package/package.json")
                info.size = len(data)
                package.addfile(info, io.BytesIO(data))
            pnpm = Path(tmp) / "pnpm"
            pnpm.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\nwhile [ "$#" -gt 0 ]; do\n'
                            '  if [ "$1" = "--dir" ]; then shift; dir="$1"; fi\n'
                            '  shift\ndone\ncat "$dir/package.json"\nmkdir -p "$dir/dist"\n'
                            'printf "<html/>\\n" > "$dir/dist/index.html"\n')
            pnpm.chmod(0o755)
            env = dict(os.environ, PATH=str(tmp) + os.pathsep + os.environ["PATH"],
                       YUHENG_UI_PACKAGE="vendor/yuheng-ui.tgz")
            result = subprocess.run(["bash", str(script)], cwd=module_dir, env=env,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(archive), result.stdout)

    def test_role_browser_runner_rejects_ui_assets_that_do_not_match_jar(self):
        import importlib.util
        import zipfile

        runner_path = ROOT / "scripts/verification/role_page_browser_runner.py"
        spec = importlib.util.spec_from_file_location("role_page_browser_runner_test", runner_path)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dist = root / "yuheng-demo-ui/dist"
            dist.mkdir(parents=True)
            (dist / "index.html").write_text("<html>different</html>")
            archive_path = root / "demo.jar"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("BOOT-INF/classes/static/index.html", "<html>packaged</html>")
            runner.ROOT = root
            runner.JAR = archive_path
            with self.assertRaisesRegex(RuntimeError, "does not match tested JAR"):
                runner.assert_static_matches_jar()

    def test_role_browser_runner_accepts_matching_ui_assets(self):
        import importlib.util
        import zipfile

        runner_path = ROOT / "scripts/verification/role_page_browser_runner.py"
        spec = importlib.util.spec_from_file_location("role_page_browser_runner_test", runner_path)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dist = root / "yuheng-demo-ui/dist"
            dist.mkdir(parents=True)
            (dist / "index.html").write_text("<html>same</html>")
            archive_path = root / "demo.jar"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("BOOT-INF/classes/static/index.html", "<html>same</html>")
            runner.ROOT = root
            runner.JAR = archive_path
            self.assertEqual(runner.assert_static_matches_jar(), 1)

    def test_config_crud_runner_checks_static_assets_against_tested_jar(self):
        runner_path = ROOT / "scripts/verification/config_page_crud_runner.py"
        source = runner_path.read_text()
        self.assertIn("import role_page_browser_runner as package_evidence", source)
        self.assertIn("package_evidence.assert_static_matches_jar()", source)
        self.assertIn('"jar_dist_byte_match": True', source)

    def test_reactor_and_bootstrap_dependency(self):
        root = ET.parse(ROOT / "pom.xml").getroot()
        self.assertEqual(root.findtext("m:packaging", namespaces=NS), "pom")
        self.assertIn("yuheng-demo-server", [m.text for m in root.findall("m:modules/m:module", NS)])
        backend = ET.parse(ROOT / "yuheng-demo-server/pom.xml").getroot()
        self.assertEqual([m.text for m in backend.findall("m:modules/m:module", NS)],
                         ["yuheng-demo-business", "yuheng-demo-server-bootstrap"])
        bootstrap = ET.parse(ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/pom.xml").getroot()
        dependencies = [d.findtext("m:artifactId", namespaces=NS) for d in bootstrap.findall("m:dependencies/m:dependency", NS)]
        self.assertIn("yuheng-demo-business", dependencies)
        self.assertTrue((ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/src/main/resources/db/changelog/db.changelog-master.yaml").is_file())

    def test_demo_compiler_keeps_lombok_and_mapstruct_processing(self):
        root = ET.parse(ROOT / "pom.xml").getroot()
        processors = root.findall(
            "m:build/m:pluginManagement/m:plugins/m:plugin/m:configuration/m:annotationProcessorPaths/m:path",
            NS,
        )
        artifacts = {path.findtext("m:artifactId", namespaces=NS) for path in processors}
        self.assertIn("lombok", artifacts)
        self.assertIn("lombok-mapstruct-binding", artifacts)
        self.assertIn("mapstruct-processor", artifacts)

    def test_demo_uses_core_lombok_chain_convention(self):
        config = (ROOT / "lombok.config").read_text()
        self.assertIn("config.stopBubbling = true", config)
        self.assertIn("lombok.accessors.chain=true", config)

    def test_erp_audit_status_validator_is_present_in_demo_business_module(self):
        validator = ROOT / "yuheng-demo-server/yuheng-demo-business/src/main/java/com/yuheng/demo/module/erp/enums/ErpAuditStatusValidation.java"
        self.assertTrue(validator.is_file())
        source = validator.read_text()
        self.assertIn("ValidationUtils.validate(new StatusRequest(status));", source)
        self.assertIn("@InEnum(value = ErpAuditStatus.class", source)

    def test_local_logging_uses_migrated_java_packages(self):
        local_config = (ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/src/main/resources/application-local.yaml").read_text()
        self.assertNotIn("cn.iocoder.yudao", local_config)
        self.assertIn("com.yuheng.platform.module.system.dal.mysql", local_config)
        self.assertIn("com.yuheng.platform.module.infra.dal.mysql", local_config)

    def test_dev_datasources_require_explicit_database_credentials(self):
        dev = (ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/src/main/resources/application-dev.yaml").read_text()
        datasource = dev.split("      datasource:\n", 1)[1].split("#        tdengine:", 1)[0]
        self.assertEqual(datasource.count("${YUHENG_DB_NAME}"), 2)
        self.assertEqual(datasource.count("${YUHENG_DB_USERNAME}"), 2)
        self.assertEqual(datasource.count("${YUHENG_DB_PASSWORD}"), 2)
        self.assertNotIn("ruoyi-vue-pro", datasource)

if __name__ == "__main__":
    unittest.main()
