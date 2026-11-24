#!/usr/bin/env python3
"""Run the ERP stock lifecycle probe on the current fixed Demo package."""
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import time

import erp_finance_edit_runner as base

ROOT = base.ROOT
SCHEMA = "yuheng_t4_stock_lifecycle_20261123_current"
MYSQL = "yh-erp-stock-lifecycle-current-mysql-20261123"
REDIS = "yh-erp-stock-lifecycle-current-redis-20261123"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13435, 16490, 48277
JAR_HASH = "4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/erp-stock-lifecycle-current-20261123"


def run(*args, input_text=None, check=True, env=None):
    return subprocess.run(args, input=input_text, text=True, capture_output=True,
                          check=check, env=env)


def sql(statement):
    result = run("docker", "exec", "-i", MYSQL, "sh", "-c",
                 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
                 '--skip-column-names -D "$1"', "probe", SCHEMA, input_text=statement)
    return result.stdout.strip()


def main():
    assert base.JAR.is_file()
    jar_hash = hashlib.sha256(base.JAR.read_bytes()).hexdigest()
    assert jar_hash == JAR_HASH, jar_hash
    ports = (MYSQL_PORT, REDIS_PORT, APP_PORT)
    assert not any(base.listening(port) for port in ports), "dedicated verification port is occupied"
    names = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
    assert MYSQL not in names and REDIS not in names, "dedicated container name already exists"
    OUT.mkdir(parents=True, exist_ok=True)
    db_password, redis_password = secrets.token_hex(20), secrets.token_hex(20)
    username, password = "erplc" + secrets.token_hex(4), secrets.token_urlsafe(12)[:16]
    password_hash = run("htpasswd", "-bnBC", "4", username, password).stdout.strip().split(":", 1)[1]
    containers, app = [], None
    report = {"result": "FAIL", "schema": SCHEMA, "jar_sha256": jar_hash,
              "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT, "app": APP_PORT},
              "credentials_recorded": False}
    try:
        run("docker", "run", "-d", "--name", MYSQL, "-e", "MYSQL_ROOT_PASSWORD=" + db_password,
            "-e", "MYSQL_DATABASE=" + SCHEMA, "-p", f"127.0.0.1:{MYSQL_PORT}:3306", "mysql:8.0.33")
        containers.append(MYSQL)
        run("docker", "run", "-d", "--name", REDIS, "-p", f"127.0.0.1:{REDIS_PORT}:6379",
            "redis:7.2.17", "redis-server", "--requirepass", redis_password)
        containers.append(REDIS)
        deadline = time.monotonic() + 120
        while True:
            try:
                if sql("SELECT DATABASE();") == SCHEMA:
                    break
            except subprocess.CalledProcessError:
                pass
            assert time.monotonic() < deadline, "isolated MySQL readiness timeout"
            time.sleep(1)

        env = dict(os.environ, YUHENG_DB_HOST="127.0.0.1", YUHENG_DB_PORT=str(MYSQL_PORT),
                   YUHENG_DB_NAME=SCHEMA, YUHENG_DB_USERNAME="root", YUHENG_DB_PASSWORD=db_password,
                   YUHENG_REDIS_PASSWORD=redis_password, YUHENG_PROBE_USERNAME=username,
                   YUHENG_PROBE_PASSWORD=password)
        log_path = OUT / "backend.log"
        log = log_path.open("w")
        app = subprocess.Popen(["java", "-jar", str(base.JAR), f"--server.port={APP_PORT}",
            "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
            f"--spring.data.redis.port={REDIS_PORT}", "--spring.data.redis.database=0",
            "--spring.data.redis.password=" + redis_password, "--yudao.security.mock-enable=false",
            "--spring.quartz.auto-startup=false", "--yudao.captcha.enable=false"],
            cwd=ROOT, env=env, stdout=log, stderr=log)
        deadline = time.monotonic() + 180
        while not base.listening(APP_PORT):
            assert app.poll() is None and time.monotonic() < deadline, "isolated Demo failed to start"
            time.sleep(1)
        deadline = time.monotonic() + 90
        while True:
            try:
                if int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")) >= 59:
                    break
            except subprocess.CalledProcessError:
                pass
            assert time.monotonic() < deadline, "Liquibase readiness timeout"
            time.sleep(1)
        seed_passwords = sql("SELECT id,password FROM system_users WHERE id < 900000 ORDER BY id;")
        sql("INSERT INTO system_users "
            "(id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) "
            f"VALUES (990990,'{username}','{password_hash}','ERP stock lifecycle',NULL,'[]',0,b'0',1);")
        sql("INSERT INTO system_user_role (user_id,role_id,creator,updater,deleted,tenant_id) "
            "SELECT 990990,role_id,creator,updater,b'0',tenant_id FROM system_user_role "
            "WHERE user_id=1 AND deleted=0;")
        env["YUHENG_PROBE_USERNAME"], env["YUHENG_PROBE_PASSWORD"] = username, password
        probe = run("python3", "scripts/verification/erp_stock_lifecycle_probe.py",
                    "--base-url", f"http://127.0.0.1:{APP_PORT}", "--schema", SCHEMA,
                    "--mysql-container", MYSQL, "--output", str(OUT / "stock-lifecycle.json"),
                    check=False, env=env)
        report["probe_stdout"], report["probe_stderr"] = probe.stdout[-5000:], probe.stderr[-5000:]
        assert probe.returncode == 0, "current-JAR ERP stock lifecycle probe failed"
        report["probe"] = json.loads((OUT / "stock-lifecycle.json").read_text())
        report["seed_passwords_unchanged"] = seed_passwords == sql(
            "SELECT id,password FROM system_users WHERE id < 900000 ORDER BY id;")
        assert report["seed_passwords_unchanged"]
        report["changesets"] = int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;"))
        assert report["changesets"] == 59
        report["result"] = "PASS"
    except Exception as error:
        report["error"] = str(error)
        raise
    finally:
        if app is not None:
            base.stop(app)
        for name in reversed(containers):
            run("docker", "rm", "-fv", name, check=False)
        if (OUT / "backend.log").exists():
            text = (OUT / "backend.log").read_text(errors="replace")
            for secret in (password, password_hash, db_password, redis_password):
                if secret:
                    text = text.replace(secret, "[REDACTED]")
            text = re.sub(r"(?i)(Bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[REDACTED]", text)
            (OUT / "backend.log").write_text(text)
            (OUT / "backend.log").unlink()
        names = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
        report["cleanup"] = {"containers_absent": all(name not in names for name in (MYSQL, REDIS)),
                              "ports_listening": {str(port): base.listening(port) for port in ports}}
        report["cleanup"]["passed"] = report["cleanup"]["containers_absent"] and not any(
            report["cleanup"]["ports_listening"].values())
        (OUT / "runtime.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        assert report["cleanup"]["passed"], report["cleanup"]
    print(json.dumps({"result": report["result"], "jar_sha256": jar_hash,
                      "changesets": report["changesets"],
                      "assertions": report["probe"]["assertions"],
                      "cleanup": report["cleanup"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
