#!/usr/bin/env python3
"""Run the config-page browser probe against disposable MySQL and Redis."""
import hashlib
import json
import os
import secrets
import subprocess
import time
from pathlib import Path

import config_value_security_probe as probe

probe.SCHEMA = "yuheng_t3_configbrowser_20261117"
probe.MYSQL_PORT, probe.REDIS_PORT, probe.APP_PORT = 13352, 16432, 48187
probe.MYSQL, probe.REDIS = "yh-configbrowser-mysql-20261117", "yh-configbrowser-redis-20261117"
UI_PORT = 5299
OUT = probe.ROOT / "docs/verification/2026-11-11-full-source-migration/config-browser-20261117"


def main():
    ports = (probe.MYSQL_PORT, probe.REDIS_PORT, probe.APP_PORT, UI_PORT)
    assert probe.JAR.is_file() and (probe.ROOT / "yuheng-demo-ui/dist/index.html").is_file()
    assert not any(probe.listening(port) for port in ports)
    existing = probe.run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
    assert probe.MYSQL not in existing and probe.REDIS not in existing
    db_password, redis_password = secrets.token_hex(20), secrets.token_hex(20)
    username, password = "t3browser" + secrets.token_hex(4), secrets.token_urlsafe(12)[:16]
    hashed = subprocess.run(["htpasswd", "-bnBC", "4", username, password], capture_output=True,
                            text=True, check=True).stdout.strip().split(":", 1)[1]
    processes, containers = [], []
    OUT.mkdir(parents=True, exist_ok=True)
    result = {"work_id": "YH-20261111-full-source-migration", "schema": probe.SCHEMA,
              "jar_sha256": hashlib.sha256(probe.JAR.read_bytes()).hexdigest(), "ports": ports}
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
                assert time.monotonic() < deadline
                time.sleep(1)
        env = dict(os.environ, YUHENG_DB_HOST="127.0.0.1", YUHENG_DB_PORT=str(probe.MYSQL_PORT),
                   YUHENG_DB_NAME=probe.SCHEMA, YUHENG_DB_USERNAME="root", YUHENG_DB_PASSWORD=db_password,
                   YUHENG_REDIS_PASSWORD=redis_password)
        backend_log = open(OUT / "backend.log", "w")
        backend = subprocess.Popen(["java", "-jar", str(probe.JAR), f"--server.port={probe.APP_PORT}",
            "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
            f"--spring.data.redis.port={probe.REDIS_PORT}", "--spring.data.redis.database=0",
            "--spring.data.redis.password=" + redis_password, "--yudao.security.mock-enable=false",
            "--spring.quartz.auto-startup=false", "--yudao.captcha.enable=false"], cwd=probe.ROOT,
            env=env, stdout=backend_log, stderr=backend_log)
        processes.append(backend)
        deadline = time.monotonic() + 150
        while not probe.listening(probe.APP_PORT):
            assert backend.poll() is None and time.monotonic() < deadline
            time.sleep(1)
        assert int(probe.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")) == 56
        assert probe.sql("SELECT COUNT(*) FROM system_users WHERE id=990051 OR username=" + probe.sql_literal(username) + ";") == "0"
        probe.sql("INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) "
                  "VALUES (990051," + probe.sql_literal(username) + "," + probe.sql_literal(hashed)
                  + ",'Browser probe',NULL,'[]',0,b'0',1);")
        probe.sql("INSERT INTO system_user_role (user_id,role_id,creator,updater,deleted,tenant_id) "
                  "VALUES (990051,1,'probe','probe',b'0',1);")
        snapshot_sql = "SELECT * FROM infra_config ORDER BY id;"
        before = probe.sql(snapshot_sql)
        result["config_snapshot_before_sha256"] = hashlib.sha256(before.encode()).hexdigest()
        ui_log = open(OUT / "ui.log", "w")
        ui = subprocess.Popen(["python3", "scripts/ui_server.py", "--root", "yuheng-demo-ui/dist", "--port", str(UI_PORT),
                               "--backend", f"http://127.0.0.1:{probe.APP_PORT}"], cwd=probe.ROOT,
                              stdout=ui_log, stderr=ui_log)
        processes.append(ui)
        deadline = time.monotonic() + 20
        while not probe.listening(UI_PORT):
            assert ui.poll() is None and time.monotonic() < deadline
            time.sleep(.2)
        browser_env = dict(os.environ, YH_BROWSER_USERNAME=username, YH_BROWSER_PASSWORD=password,
                           YH_BROWSER_OUTPUT=str(OUT / "browser"),
                           NODE_PATH="/Users/huhua/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules")
        subprocess.run(["node", "scripts/verification/config_page_browser_probe.js"], cwd=probe.ROOT,
                       env=browser_env, check=True, timeout=160)
        after = probe.sql(snapshot_sql)
        result["config_snapshot_after_sha256"] = hashlib.sha256(after.encode()).hexdigest()
        result["config_snapshot_unchanged"] = before == after
        assert before == after, "infra_config changed during cancel-only probe"
        result["browser_completed"] = True
    finally:
        for process in reversed(processes):
            process.terminate()
            try:
                process.wait(timeout=35)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        for container in reversed(containers):
            subprocess.run(["docker", "rm", "-fv", container], check=True, capture_output=True)
        names = probe.run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
        result["cleanup"] = {"containers_absent": all(name not in names for name in (probe.MYSQL, probe.REDIS)),
                             "ports_listening": {str(port): probe.listening(port) for port in ports}}
        (OUT / "runtime.json").write_text(json.dumps(result, indent=2) + "\n")
        assert result["cleanup"]["containers_absent"] and not any(result["cleanup"]["ports_listening"].values())


if __name__ == "__main__":
    main()
