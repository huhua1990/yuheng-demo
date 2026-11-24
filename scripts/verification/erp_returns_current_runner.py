#!/usr/bin/env python3
"""Run current-JAR ERP return/refund transaction probes in isolation."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import tempfile
import time

import erp_finance_browser_runner as base

ROOT = base.ROOT
SCHEMA = "yuheng_t4_returns_20261123_current"
MYSQL, REDIS = "yh-erp-returns-current-mysql-20261123", "yh-erp-returns-current-redis-20261123"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13438, 16493, 48280
JAR_HASH = "4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1"
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/erp-returns-current-20261123"


def run(*args, check=True, env=None, input_text=None):
    return subprocess.run(args, check=check, env=env, input=input_text, text=True,
                          capture_output=True)


def listening(port):
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def sql(statement):
    result = run("docker", "exec", "-i", MYSQL, "sh", "-c",
                 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
                 '--skip-column-names -D "$1"', "probe", SCHEMA, input_text=statement,
                 check=False)
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


def main():
    assert hashlib.sha256(JAR.read_bytes()).hexdigest() == JAR_HASH
    OUT.mkdir(parents=True, exist_ok=True)
    ports = (MYSQL_PORT, REDIS_PORT, APP_PORT)
    assert not any(listening(port) for port in ports)
    names = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
    assert MYSQL not in names and REDIS not in names

    db_password, redis_password = secrets.token_hex(24), secrets.token_hex(24)
    username = "erpreturn" + secrets.token_hex(4)
    password = secrets.token_urlsafe(12)[:16]
    password_hash = run("htpasswd", "-bnBC", "4", username, password).stdout.strip().split(":", 1)[1]
    containers, app = [], None
    report = {"result": "FAIL", "schema": SCHEMA, "jar_sha256": JAR_HASH,
              "viewport": "api-sql-only", "credentials_recorded": False,
              "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT, "app": APP_PORT}}
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
            except RuntimeError:
                pass
            assert time.monotonic() < deadline, "isolated MySQL readiness timeout"
            time.sleep(1)

        env = dict(os.environ, YUHENG_DB_HOST="127.0.0.1", YUHENG_DB_PORT=str(MYSQL_PORT),
                   YUHENG_DB_NAME=SCHEMA, YUHENG_DB_USERNAME="root", YUHENG_DB_PASSWORD=db_password,
                   YUHENG_REDIS_PASSWORD=redis_password, YUHENG_PROBE_USERNAME=username,
                   YUHENG_PROBE_PASSWORD=password)
        with tempfile.TemporaryDirectory(prefix="yh-erp-returns-current-") as temp_dir:
            log_path = Path(temp_dir) / "backend.log"
            with log_path.open("w") as log:
                app = subprocess.Popen(["java", "-jar", str(JAR), f"--server.port={APP_PORT}",
                    "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
                    f"--spring.data.redis.port={REDIS_PORT}", "--spring.data.redis.database=0",
                    "--spring.data.redis.password=" + redis_password, "--yudao.security.mock-enable=false",
                    "--spring.quartz.auto-startup=false", "--yudao.captcha.enable=false"],
                    cwd=ROOT, env=env, stdout=log, stderr=log)
                deadline = time.monotonic() + 180
                while not listening(APP_PORT):
                    assert app.poll() is None and time.monotonic() < deadline, "Demo failed to start"
                    time.sleep(1)
                deadline = time.monotonic() + 90
                while True:
                    try:
                        if int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")) >= 59:
                            break
                    except RuntimeError:
                        pass
                    assert time.monotonic() < deadline, "Liquibase readiness timeout"
                    time.sleep(1)

                seed_passwords = sql("SELECT id,password FROM system_users WHERE id<900000 ORDER BY id;")
                sql("INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) "
                    f"VALUES (993300,'{username}','{password_hash}','ERP returns current',NULL,'[]',0,b'0',1);")
                sql("INSERT INTO system_user_role (user_id,role_id,creator,updater,deleted,tenant_id) "
                    "SELECT 993300,role_id,creator,updater,b'0',tenant_id FROM system_user_role "
                    "WHERE user_id=1 AND deleted=0;")
                probe = run("python3", "scripts/verification/erp_returns_probe.py",
                    "--base-url", f"http://127.0.0.1:{APP_PORT}", "--schema", SCHEMA,
                    "--mysql-container", MYSQL, "--output", str(OUT / "returns.json"),
                    env=env, check=False)
                report["probe_stdout"], report["probe_stderr"] = probe.stdout[-3000:], probe.stderr[-3000:]
                assert probe.returncode == 0, "ERP returns/refund transaction probe failed"
                report["probe"] = json.loads((OUT / "returns.json").read_text())
                report["sql"] = {"changesets": int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")),
                    "active_return_headers": int(sql("SELECT COUNT(*) FROM erp_purchase_return WHERE deleted=0;") or "0")
                        + int(sql("SELECT COUNT(*) FROM erp_sale_return WHERE deleted=0;") or "0"),
                    "active_refund_headers": int(sql("SELECT COUNT(*) FROM erp_finance_payment WHERE deleted=0;") or "0")
                        + int(sql("SELECT COUNT(*) FROM erp_finance_receipt WHERE deleted=0;") or "0"),
                    "seed_passwords_unchanged": seed_passwords == sql("SELECT id,password FROM system_users WHERE id<900000 ORDER BY id;")}
                assert report["sql"]["changesets"] == 59
                assert report["sql"]["active_return_headers"] == 0
                assert report["sql"]["active_refund_headers"] == 0
                assert report["sql"]["seed_passwords_unchanged"]
                report["result"] = "PASS"
    except Exception as error:
        report["error"] = str(error)
        raise
    finally:
        stop(app)
        for name in reversed(containers):
            run("docker", "rm", "-fv", name, check=False)
        remaining = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
        report["cleanup"] = {"containers_absent": all(name not in remaining for name in (MYSQL, REDIS)),
            "ports_listening": {str(port): listening(port) for port in ports}}
        report["cleanup"]["passed"] = report["cleanup"]["containers_absent"] and not any(
            report["cleanup"]["ports_listening"].values())
        (OUT / "runtime.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        assert report["cleanup"]["passed"], report["cleanup"]
    print(json.dumps({"result": report["result"], "jar_sha256": JAR_HASH,
        "sql": report["sql"], "assertions": report["probe"]["assertions"],
        "cleanup": report["cleanup"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
