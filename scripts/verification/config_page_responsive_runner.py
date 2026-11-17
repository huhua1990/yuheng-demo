#!/usr/bin/env python3
"""Compare the migrated and upstream config page in isolated same-data browser sessions."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import subprocess
import time
from pathlib import Path

import config_value_security_probe as probe

probe.SCHEMA = "yuheng_t3_configresponsive_20261120"
probe.MYSQL_PORT, probe.REDIS_PORT, probe.APP_PORT = 13356, 16436, 48191
probe.MYSQL, probe.REDIS = "yh-configresponsive-mysql-20261120", "yh-configresponsive-redis-20261120"
DEMO_PORT, ORIGINAL_PORT = 5198, 5199
ORIGINAL_ROOT = probe.ROOT.parent / "yudao-ui-admin-vue3"
OUT = probe.ROOT / "docs/verification/2026-11-11-full-source-migration/config-responsive-fixed-20261117"


def main() -> None:
    ports = (probe.MYSQL_PORT, probe.REDIS_PORT, probe.APP_PORT, DEMO_PORT, ORIGINAL_PORT)
    assert probe.JAR.is_file() and (probe.ROOT / "yuheng-demo-ui/dist/index.html").is_file()
    assert (ORIGINAL_ROOT / "node_modules/.bin/vite").is_file()
    assert not any(probe.listening(port) for port in ports)
    names = probe.run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
    assert probe.MYSQL not in names and probe.REDIS not in names

    db_password, redis_password = secrets.token_hex(20), secrets.token_hex(20)
    username, password = "t3responsive" + secrets.token_hex(4), secrets.token_urlsafe(12)[:16]
    password_hash = subprocess.run(["htpasswd", "-bnBC", "4", username, password], capture_output=True,
                                   text=True, check=True).stdout.strip().split(":", 1)[1]
    processes: list[subprocess.Popen] = []
    containers: list[str] = []
    OUT.mkdir(parents=True, exist_ok=True)
    result = {"work_id": "YH-20261111-full-source-migration", "schema": probe.SCHEMA,
              "jar_sha256": hashlib.sha256(probe.JAR.read_bytes()).hexdigest(),
              "original_ui_root": str(ORIGINAL_ROOT), "ports": ports, "browsers": {}}
    logs = []
    try:
        probe.run("docker", "run", "-d", "--name", probe.MYSQL, "-e", "MYSQL_ROOT_PASSWORD=" + db_password,
                  "-e", "MYSQL_DATABASE=" + probe.SCHEMA, "-p", f"127.0.0.1:{probe.MYSQL_PORT}:3306", "mysql:8.0.33")
        containers.append(probe.MYSQL)
        probe.run("docker", "run", "-d", "--name", probe.REDIS, "-p", f"127.0.0.1:{probe.REDIS_PORT}:6379",
                  "redis:7.2.17", "redis-server", "--requirepass", redis_password)
        containers.append(probe.REDIS)
        deadline = time.monotonic() + 100
        while True:
            try:
                assert probe.sql("SELECT DATABASE();") == probe.SCHEMA
                break
            except (RuntimeError, AssertionError):
                assert time.monotonic() < deadline, "isolated MySQL readiness timeout"
                time.sleep(1)

        backend_env = dict(os.environ, YUHENG_DB_HOST="127.0.0.1", YUHENG_DB_PORT=str(probe.MYSQL_PORT),
                           YUHENG_DB_NAME=probe.SCHEMA, YUHENG_DB_USERNAME="root", YUHENG_DB_PASSWORD=db_password,
                           YUHENG_REDIS_PASSWORD=redis_password)
        backend_log = (OUT / "backend.log").open("w")
        logs.append(backend_log)
        backend = subprocess.Popen(["java", "-jar", str(probe.JAR), f"--server.port={probe.APP_PORT}",
            "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
            f"--spring.data.redis.port={probe.REDIS_PORT}", "--spring.data.redis.database=0",
            "--spring.data.redis.password=" + redis_password, "--yudao.security.mock-enable=false",
            "--spring.quartz.auto-startup=false", "--yudao.captcha.enable=false"], cwd=probe.ROOT,
            env=backend_env, stdout=backend_log, stderr=backend_log)
        processes.append(backend)
        deadline = time.monotonic() + 150
        while not probe.listening(probe.APP_PORT):
            assert backend.poll() is None and time.monotonic() < deadline, "isolated backend readiness failed"
            time.sleep(1)
        assert int(probe.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")) == 54
        probe.sql("INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) "
                  "VALUES (990051," + probe.sql_literal(username) + "," + probe.sql_literal(password_hash)
                  + ",'Responsive probe',NULL,'[]',0,b'0',1);")
        probe.sql("INSERT INTO system_user_role (user_id,role_id,creator,updater,deleted,tenant_id) VALUES "
                  "(990051,1,'probe','probe',b'0',1);")
        config_before = probe.sql("SELECT * FROM infra_config ORDER BY id;")
        password_before = probe.sql("SELECT id,password FROM system_users ORDER BY id;")

        demo_log = (OUT / "demo-ui.log").open("w")
        logs.append(demo_log)
        demo = subprocess.Popen(["python3", "scripts/ui_server.py", "--root", "yuheng-demo-ui/dist",
            "--port", str(DEMO_PORT), "--backend", f"http://127.0.0.1:{probe.APP_PORT}"],
            cwd=probe.ROOT, stdout=demo_log, stderr=demo_log)
        processes.append(demo)

        original_log = (OUT / "original-vite.log").open("w")
        logs.append(original_log)
        original_env = dict(os.environ, VITE_BACKEND_ORIGIN=f"http://127.0.0.1:{probe.APP_PORT}",
                            VITE_PORT=str(ORIGINAL_PORT), VITE_OPEN="false")
        original = subprocess.Popen([str(ORIGINAL_ROOT / "node_modules/.bin/vite"), "--host", "127.0.0.1",
            "--port", str(ORIGINAL_PORT), "--strictPort"], cwd=ORIGINAL_ROOT, env=original_env,
            stdout=original_log, stderr=original_log)
        processes.append(original)
        for port, process in ((DEMO_PORT, demo), (ORIGINAL_PORT, original)):
            deadline = time.monotonic() + 45
            while not probe.listening(port):
                assert process.poll() is None and time.monotonic() < deadline, f"UI {port} readiness failed"
                time.sleep(.25)

        snapshot = {"config_sha256": hashlib.sha256(config_before.encode()).hexdigest(),
                    "password_hash_rows": len(password_before.splitlines())}
        browser_failures = []
        for name, port in (("demo", DEMO_PORT), ("original", ORIGINAL_PORT)):
            browser_env = dict(os.environ, YH_BROWSER_USERNAME=username, YH_BROWSER_PASSWORD=password,
                YH_REQUIRE_USABLE_DEFAULT="true" if name == "demo" else "false",
                YH_BROWSER_BASE=f"http://127.0.0.1:{port}", YH_BROWSER_OUTPUT=str(OUT / name),
                NODE_PATH="/Users/huhua/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules")
            completed = subprocess.run(["node", "scripts/verification/config_page_responsive_probe.js"], cwd=probe.ROOT,
                                       env=browser_env, check=False, timeout=180)
            browser_result = json.loads((OUT / f"{name}.json").read_text())
            result["browsers"][name] = browser_result
            if completed.returncode or not browser_result.get("completed"):
                browser_failures.append(name)

        result["snapshots"] = {"config_unchanged": config_before == probe.sql("SELECT * FROM infra_config ORDER BY id;"),
            "config_before_sha256": hashlib.sha256(config_before.encode()).hexdigest(),
            "password_hash_rows_unchanged": password_before == probe.sql("SELECT id,password FROM system_users ORDER BY id;")}
        assert result["snapshots"]["config_unchanged"] and result["snapshots"]["password_hash_rows_unchanged"]
        assert not browser_failures, f"browser probes failed: {browser_failures}"
    finally:
        for process in reversed(processes):
            process.terminate()
            try:
                process.wait(timeout=35)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        for log in logs:
            log.close()
        for container in reversed(containers):
            subprocess.run(["docker", "rm", "-fv", container], check=True, capture_output=True)
        existing = probe.run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
        result["cleanup"] = {"containers_absent": all(name not in existing for name in (probe.MYSQL, probe.REDIS)),
            "ports_listening": {str(port): probe.listening(port) for port in ports}}
        (OUT / "runtime.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        assert result["cleanup"]["containers_absent"] and not any(result["cleanup"]["ports_listening"].values())


if __name__ == "__main__":
    main()
