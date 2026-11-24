#!/usr/bin/env python3
"""Run ERP finance edit and ownership probes against disposable services."""
import hashlib
import json
import os
import secrets
import socket
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "yuheng_t4_edit_20261121"
OWNER_SCHEMA = "yuheng_t4_owner_20261121"
MYSQL, REDIS = "yh-erp-finance-mysql-20261121", "yh-erp-finance-redis-20261121"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13376, 16457, 48211
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/erp-finance-20261121"


def run(*args, input_text=None):
    result = subprocess.run(args, input=input_text, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def listening(port):
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def sql(statement, schema=SCHEMA):
    return run("docker", "exec", "-i", MYSQL, "sh", "-c",
               'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
               '--skip-column-names -D "$1"', "probe", schema, input_text=statement)


def quote(value):
    return "'" + value.replace("'", "''") + "'"


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
    assert JAR.is_file()
    ports = (MYSQL_PORT, REDIS_PORT, APP_PORT)
    assert not any(listening(port) for port in ports)
    names = run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
    assert MYSQL not in names and REDIS not in names
    db_password, redis_password = secrets.token_hex(20), secrets.token_hex(20)
    username, password = "erpedit" + secrets.token_hex(4), secrets.token_urlsafe(12)[:16]
    password_hash = subprocess.run(["htpasswd", "-bnBC", "4", username, password],
                                   capture_output=True, text=True, check=True).stdout.strip().split(":", 1)[1]
    containers, app = [], None
    OUT.mkdir(parents=True, exist_ok=True)
    result = {"schema": SCHEMA, "jar_sha256": hashlib.sha256(JAR.read_bytes()).hexdigest(),
              "credentials_recorded": False, "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT,
              "app": APP_PORT}}
    try:
        run("docker", "run", "-d", "--name", MYSQL, "-e", "MYSQL_ROOT_PASSWORD=" + db_password,
            "-e", "MYSQL_DATABASE=" + SCHEMA, "-p", f"127.0.0.1:{MYSQL_PORT}:3306", "mysql:8.0.33")
        containers.append(MYSQL)
        run("docker", "run", "-d", "--name", REDIS, "-p", f"127.0.0.1:{REDIS_PORT}:6379",
            "redis:7.2.17", "redis-server", "--requirepass", redis_password)
        containers.append(REDIS)
        deadline = time.monotonic() + 100
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
        log = (OUT / "backend.log").open("w")
        app = subprocess.Popen(["java", "-jar", str(JAR), f"--server.port={APP_PORT}",
            "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
            f"--spring.data.redis.port={REDIS_PORT}", "--spring.data.redis.database=0",
            "--spring.data.redis.password=" + redis_password, "--yudao.security.mock-enable=false",
            "--spring.quartz.auto-startup=false", "--yudao.captcha.enable=false"],
            cwd=ROOT, env=env, stdout=log, stderr=log)
        deadline = time.monotonic() + 180
        while not listening(APP_PORT):
            assert app.poll() is None and time.monotonic() < deadline, "isolated Demo failed to start"
            time.sleep(1)
        deadline = time.monotonic() + 45
        while True:
            try:
                if int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")) >= 54:
                    break
            except RuntimeError:
                pass
            assert time.monotonic() < deadline, "Liquibase readiness timeout"
            time.sleep(1)
        sql("INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) "
            "VALUES (990980," + quote(username) + "," + quote(password_hash)
            + ",'ERP finance probe',NULL,'[]',0,b'0',1);")
        sql("INSERT INTO system_user_role (user_id,role_id,creator,updater,deleted,tenant_id) "
            "SELECT 990980,role_id,creator,updater,b'0',tenant_id FROM system_user_role "
            "WHERE user_id=1 AND deleted=0;")
        env["YUHENG_PROBE_USERNAME"], env["YUHENG_PROBE_PASSWORD"] = username, password
        edit = subprocess.run(["python3", "scripts/verification/erp_finance_edit_probe.py",
            "--base-url", f"http://127.0.0.1:{APP_PORT}", "--schema", SCHEMA,
            "--mysql-container", MYSQL, "--output", str(OUT / "finance-edit.json")],
            cwd=ROOT, env=env, capture_output=True, text=True, timeout=300)
        assert edit.returncode == 0, edit.stderr
        sql(f"CREATE DATABASE `{OWNER_SCHEMA}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        stop(app)
        app = None
        owner_env = dict(env, YUHENG_DB_NAME=OWNER_SCHEMA)
        log = (OUT / "backend-owner.log").open("w")
        app = subprocess.Popen(["java", "-jar", str(JAR), f"--server.port={APP_PORT}",
            "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
            f"--spring.data.redis.port={REDIS_PORT}", "--spring.data.redis.database=0",
            "--spring.data.redis.password=" + redis_password, "--yudao.security.mock-enable=false",
            "--spring.quartz.auto-startup=false", "--yudao.captcha.enable=false"],
            cwd=ROOT, env=owner_env, stdout=log, stderr=log)
        deadline = time.monotonic() + 180
        while not listening(APP_PORT):
            assert app.poll() is None and time.monotonic() < deadline, "isolated Demo failed to restart"
            time.sleep(1)
        deadline = time.monotonic() + 45
        while True:
            try:
                if int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;", OWNER_SCHEMA)) >= 54:
                    break
            except RuntimeError:
                pass
            assert time.monotonic() < deadline, "owner schema Liquibase readiness timeout"
            time.sleep(1)
        sql("INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) "
            "VALUES (990981," + quote(username) + "," + quote(password_hash)
            + ",'ERP owner probe',NULL,'[]',0,b'0',1);", OWNER_SCHEMA)
        sql("INSERT INTO system_user_role (user_id,role_id,creator,updater,deleted,tenant_id) "
            "SELECT 990981,role_id,creator,updater,b'0',tenant_id FROM system_user_role "
            "WHERE user_id=1 AND deleted=0;", OWNER_SCHEMA)
        owner = subprocess.run(["python3", "scripts/verification/erp_finance_owner_probe.py",
            "--base-url", f"http://127.0.0.1:{APP_PORT}", "--schema", OWNER_SCHEMA,
            "--mysql-container", MYSQL, "--output", str(OUT / "finance-owner.json")],
            cwd=ROOT, env=owner_env, capture_output=True, text=True, timeout=300)
        assert owner.returncode == 0, owner.stderr
        result["finance_edit"] = json.loads((OUT / "finance-edit.json").read_text())
        result["finance_owner"] = json.loads((OUT / "finance-owner.json").read_text())
        result["result"] = "PASS"
    finally:
        stop(app)
        for name in reversed(containers):
            subprocess.run(["docker", "rm", "-fv", name], check=True, capture_output=True, text=True)
        names = run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
        result["cleanup"] = {"containers_absent": all(name not in names for name in (MYSQL, REDIS)),
                             "ports_listening": {str(port): listening(port) for port in ports}}
        result["cleanup"]["passed"] = result["cleanup"]["containers_absent"] and not any(result["cleanup"]["ports_listening"].values())
        (OUT / "runtime.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        assert result["cleanup"]["passed"], result["cleanup"]


if __name__ == "__main__":
    main()
