#!/usr/bin/env python3
"""Run ERP probes on new, explicitly isolated containers and schemas."""
import hashlib
import json
import os
import re
import secrets
import subprocess
import time
import traceback
from pathlib import Path

import erp_finance_edit_runner as base

ROOT = base.ROOT
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/erp-p2-sidecar-20261122"
MYSQL = "yh-erp-p2-sidecar-mysql-20261122"
REDIS = "yh-erp-p2-sidecar-redis-20261122"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13386, 16467, 48231
JAR_HASH = "fb66307402876756a689c7a9e4a079ceb351d16619d05404d2f67138fdc81302"
CASES = (
    ("create", "yuheng_t4_item_owner_20261122", "erp_item_owner_http_probe.py"),
    ("update", "yuheng_t4_item_update_20261122", "erp_item_owner_update_http_probe.py"),
    ("workflow", "yuheng_t4_flows_20261122", "erp_workflow_probe.py"),
    ("stock-lifecycle", "yuheng_t4_stock_lifecycle_20261122", "erp_stock_lifecycle_probe.py"),
    ("audit-status", "yuheng_t4_status_20261122", "erp_audit_status_probe.py"),
)


def redact_backend_log(text):
    text = re.sub(r'("password"\s*:\s*")[^"]*(")', r'\1[REDACTED]\2', text)
    text = re.sub(r'(password=)[^&\s,}]*', r'\1[REDACTED]', text)
    return re.sub(r'(Bearer\s+)[A-Za-z0-9._~-]+', r'\1[REDACTED]', text)


def run(*args, input_text=None, check=True, env=None):
    return subprocess.run(args, input=input_text, text=True, capture_output=True,
                          check=check, env=env)


def sql(statement, schema):
    result = run("docker", "exec", "-i", MYSQL, "sh", "-c",
                 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
                 '--skip-column-names -D "$1"', "probe", schema, input_text=statement)
    return result.stdout.strip()


def readiness(schema):
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        try:
            if sql("SELECT DATABASE();", schema) == schema:
                return
        except subprocess.CalledProcessError:
            pass
        time.sleep(1)
    raise RuntimeError(f"MySQL readiness timeout for {schema}")


def start_app(schema, password, redis_password, username, probe_password, log_path):
    env = dict(os.environ, YUHENG_DB_HOST="127.0.0.1", YUHENG_DB_PORT=str(MYSQL_PORT),
               YUHENG_DB_NAME=schema, YUHENG_DB_USERNAME="root", YUHENG_DB_PASSWORD=password,
               YUHENG_REDIS_PASSWORD=redis_password, YUHENG_PROBE_USERNAME=username,
               YUHENG_PROBE_PASSWORD=probe_password)
    log = log_path.open("w")
    process = subprocess.Popen(
        ["java", "-jar", str(base.JAR), f"--server.port={APP_PORT}",
         "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
         f"--spring.data.redis.port={REDIS_PORT}", "--spring.data.redis.database=0",
         "--spring.data.redis.password=" + redis_password, "--yudao.security.mock-enable=false",
         "--spring.quartz.auto-startup=false", "--yudao.captcha.enable=false"],
        cwd=ROOT, env=env, stdout=log, stderr=log)
    deadline = time.monotonic() + 180
    while not base.listening(APP_PORT):
        if process.poll() is not None:
            raise RuntimeError(f"JAR exited with {process.returncode}; see {log_path}")
        if time.monotonic() >= deadline:
            raise RuntimeError(f"JAR readiness timeout; see {log_path}")
        time.sleep(1)
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            if int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;", schema)) >= 54:
                return process, env
        except subprocess.CalledProcessError:
            pass
        time.sleep(1)
    raise RuntimeError(f"Liquibase readiness timeout for {schema}; see {log_path}")


def seed_user(schema, username, password_hash, user_id):
    sql("INSERT INTO system_users "
        "(id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) VALUES "
        f"({user_id},'{username}','{password_hash}','ERP P2 sidecar',NULL,'[]',0,b'0',1);", schema)
    sql("INSERT INTO system_user_role (user_id,role_id,creator,updater,deleted,tenant_id) "
        f"SELECT {user_id},role_id,creator,updater,b'0',tenant_id FROM system_user_role "
        "WHERE user_id=1 AND deleted=0;", schema)


def run_probe(name, schema, script, env):
    output = OUT / f"{name}.json"
    return run("python3", f"scripts/verification/{script}", "--base-url", f"http://127.0.0.1:{APP_PORT}",
               "--schema", schema, "--mysql-container", MYSQL, "--output", str(output),
               check=False, env=env)


def main():
    assert base.JAR.is_file()
    actual_hash = hashlib.sha256(base.JAR.read_bytes()).hexdigest()
    assert actual_hash == JAR_HASH, actual_hash
    ports = (MYSQL_PORT, REDIS_PORT, APP_PORT)
    assert not any(base.listening(port) for port in ports)
    existing = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
    assert MYSQL not in existing and REDIS not in existing
    OUT.mkdir(parents=True, exist_ok=True)
    db_password = secrets.token_hex(20)
    redis_password = secrets.token_hex(20)
    username = "erpp2" + secrets.token_hex(4)
    password = secrets.token_urlsafe(12)[:16]
    password_hash = run("htpasswd", "-bnBC", "4", username, password).stdout.strip().split(":", 1)[1]
    containers, processes = [], []
    report = {"result": "FAIL", "jar_sha256": actual_hash,
              "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT, "app": APP_PORT},
              "schemas": {name: schema for name, schema, _ in CASES}, "probes": {}}
    try:
        run("docker", "run", "-d", "--name", MYSQL, "-e", "MYSQL_ROOT_PASSWORD=" + db_password,
            "-e", "MYSQL_DATABASE=" + CASES[0][1], "-p", f"127.0.0.1:{MYSQL_PORT}:3306", "mysql:8.0.33")
        containers.append(MYSQL)
        run("docker", "run", "-d", "--name", REDIS, "-p", f"127.0.0.1:{REDIS_PORT}:6379",
            "redis:7.2.17", "redis-server", "--requirepass", redis_password)
        containers.append(REDIS)
        for index, (name, schema, script) in enumerate(CASES):
            if index:
                sql(f"CREATE DATABASE `{schema}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;", CASES[0][1])
            readiness(schema)
            process, env = start_app(schema, db_password, redis_password, username, password,
                                     OUT / f"backend-{name}.log")
            processes.append(process)
            seed_user(schema, username, password_hash, 990990 + index)
            result = run_probe(name, schema, script, env)
            report["probes"][name] = {"returncode": result.returncode,
                                      "stdout": result.stdout[-4000:], "stderr": result.stderr[-4000:]}
            base.stop(process)
            processes.pop()
            if result.returncode:
                raise RuntimeError(f"{name} probe failed with {result.returncode}")
        report["result"] = "PASS"
    except Exception as error:
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        raise
    finally:
        for process in reversed(processes):
            base.stop(process)
        for log_path in OUT.glob("backend-*.log"):
            log_path.write_text(redact_backend_log(log_path.read_text(errors="replace")))
        for name in reversed(containers):
            run("docker", "rm", "-fv", name, check=False)
        names = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
        report["cleanup"] = {"containers_absent": all(name not in names for name in (MYSQL, REDIS)),
                              "ports_listening": {str(port): base.listening(port) for port in ports}}
        report["cleanup"]["passed"] = (report["cleanup"]["containers_absent"] and
                                        not any(report["cleanup"]["ports_listening"].values()))
        (OUT / "runtime.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        assert report["cleanup"]["passed"], report["cleanup"]


if __name__ == "__main__":
    main()
