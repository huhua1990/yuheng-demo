#!/usr/bin/env python3
"""Run current-JAR ERP finance edit and item-ownership probes in isolation."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time

import erp_finance_browser_runner as base

ROOT = base.ROOT
SCHEMAS = ("yuheng_t4_edit_20261123_current", "yuheng_t4_owner_20261123_current")
MYSQL, REDIS = "yh-erp-finance-current-mysql-20261123", "yh-erp-finance-current-redis-20261123"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13439, 16494, 48281
JAR_HASH = "4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1"
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/erp-finance-current-20261123"


def run(*args, check=True, env=None, input_text=None):
    return subprocess.run(args, check=check, env=env, input=input_text, text=True,
                          capture_output=True)


def sql(schema, statement):
    result = run("docker", "exec", "-i", MYSQL, "sh", "-c",
        'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
        '--skip-column-names -D "$1"', "probe", schema, input_text=statement, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "isolated SQL failed")
    return result.stdout.strip()


def stop(process):
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=35)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def wait_for_schema(schema, deadline):
    while True:
        try:
            if int(sql(schema, "SELECT COUNT(*) FROM DATABASECHANGELOG;")) >= 59:
                return
        except RuntimeError:
            pass
        assert time.monotonic() < deadline, "Liquibase readiness timeout"
        time.sleep(1)


def main():
    assert hashlib.sha256(JAR.read_bytes()).hexdigest() == JAR_HASH
    OUT.mkdir(parents=True, exist_ok=True)
    assert not any(base.listening(port) for port in (MYSQL_PORT, REDIS_PORT, APP_PORT))
    existing = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
    assert MYSQL not in existing and REDIS not in existing

    db_password, redis_password = secrets.token_hex(24), secrets.token_hex(24)
    username, password = "erpfinance" + secrets.token_hex(4), secrets.token_urlsafe(12)[:16]
    password_hash = run("htpasswd", "-bnBC", "4", username, password).stdout.strip().split(":", 1)[1]
    containers, app = [], None
    report = {"result": "FAIL", "schemas": list(SCHEMAS), "jar_sha256": JAR_HASH,
        "credentials_recorded": False,
        "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT, "app": APP_PORT}}
    try:
        run("docker", "run", "-d", "--name", MYSQL, "-e", "MYSQL_ROOT_PASSWORD=" + db_password,
            "-e", "MYSQL_DATABASE=" + SCHEMAS[0], "-p", f"127.0.0.1:{MYSQL_PORT}:3306", "mysql:8.0.33")
        containers.append(MYSQL)
        run("docker", "run", "-d", "--name", REDIS, "-p", f"127.0.0.1:{REDIS_PORT}:6379",
            "redis:7.2.17", "redis-server", "--requirepass", redis_password)
        containers.append(REDIS)
        deadline = time.monotonic() + 120
        while True:
            try:
                if sql(SCHEMAS[0], "SELECT DATABASE();") == SCHEMAS[0]:
                    break
            except RuntimeError:
                pass
            assert time.monotonic() < deadline, "isolated MySQL readiness timeout"
            time.sleep(1)
        sql(SCHEMAS[0], f"CREATE DATABASE `{SCHEMAS[1]}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")

        results = {}
        with tempfile.TemporaryDirectory(prefix="yh-erp-finance-current-") as temp_dir:
            for index, (schema, probe_name, evidence_name, user_id) in enumerate((
                (SCHEMAS[0], "erp_finance_edit_probe.py", "finance-edit.json", 993400),
                (SCHEMAS[1], "erp_finance_owner_probe.py", "finance-owner.json", 993401),
            )):
                env = dict(os.environ, YUHENG_DB_HOST="127.0.0.1", YUHENG_DB_PORT=str(MYSQL_PORT),
                    YUHENG_DB_NAME=schema, YUHENG_DB_USERNAME="root", YUHENG_DB_PASSWORD=db_password,
                    YUHENG_REDIS_PASSWORD=redis_password, YUHENG_PROBE_USERNAME=username,
                    YUHENG_PROBE_PASSWORD=password)
                with (Path(temp_dir) / f"backend-{index}.log").open("w") as log:
                    app = subprocess.Popen(["java", "-jar", str(JAR), f"--server.port={APP_PORT}",
                        "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
                        f"--spring.data.redis.port={REDIS_PORT}", "--spring.data.redis.database=0",
                        "--spring.data.redis.password=" + redis_password, "--yudao.security.mock-enable=false",
                        "--spring.quartz.auto-startup=false", "--yudao.captcha.enable=false"],
                        cwd=ROOT, env=env, stdout=log, stderr=log)
                    deadline = time.monotonic() + 180
                    while not base.listening(APP_PORT):
                        assert app.poll() is None and time.monotonic() < deadline, "Demo failed to start"
                        time.sleep(1)
                    wait_for_schema(schema, time.monotonic() + 90)
                    seed_passwords = sql(schema, "SELECT id,password FROM system_users WHERE id<900000 ORDER BY id;")
                    sql(schema, "INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) "
                        f"VALUES ({user_id},'{username}','{password_hash}','ERP finance current',NULL,'[]',0,b'0',1);")
                    sql(schema, "INSERT INTO system_user_role (user_id,role_id,creator,updater,deleted,tenant_id) "
                        f"SELECT {user_id},role_id,creator,updater,b'0',tenant_id FROM system_user_role WHERE user_id=1 AND deleted=0;")
                    probe = run("python3", f"scripts/verification/{probe_name}", "--base-url",
                        f"http://127.0.0.1:{APP_PORT}", "--schema", schema,
                        "--mysql-container", MYSQL, "--output", str(OUT / evidence_name),
                        env=env, check=False)
                    assert probe.returncode == 0, f"{probe_name} failed: {probe.stderr[-2000:]}"
                    results[evidence_name] = json.loads((OUT / evidence_name).read_text())
                    assert seed_passwords == sql(schema,
                        "SELECT id,password FROM system_users WHERE id<900000 ORDER BY id;")
                    results[evidence_name]["seed_passwords_unchanged"] = True
                stop(app)
                app = None

        report["probes"] = results
        report["sql"] = {schema: {"changesets": int(sql(schema, "SELECT COUNT(*) FROM DATABASECHANGELOG;")),
            "seed_passwords_unchanged": True} for schema in SCHEMAS}
        assert all(value["changesets"] == 59 for value in report["sql"].values())
        report["result"] = "PASS"
    except Exception as error:
        report["error"] = str(error)
        raise
    finally:
        stop(app)
        for name in reversed(containers):
            run("docker", "rm", "-fv", name, check=False)
        names = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
        report["cleanup"] = {"containers_absent": all(name not in names for name in (MYSQL, REDIS)),
            "ports_listening": {str(port): base.listening(port) for port in (MYSQL_PORT, REDIS_PORT, APP_PORT)}}
        report["cleanup"]["passed"] = report["cleanup"]["containers_absent"] and not any(
            report["cleanup"]["ports_listening"].values())
        (OUT / "runtime.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        assert report["cleanup"]["passed"], report["cleanup"]
    print(json.dumps({"result": report["result"], "jar_sha256": JAR_HASH,
        "sql": report["sql"], "cleanup": report["cleanup"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
