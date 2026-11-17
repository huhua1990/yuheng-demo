#!/usr/bin/env python3
"""Verify config value visibility, authentication, and tenant-header boundaries."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import socket
import subprocess
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "yuheng_t4_configvalue_20261119"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13349, 16429, 48184
MYSQL, REDIS = "yh-configvalue-mysql-20261119", "yh-configvalue-redis-20261119"
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/controller-security-inventory-20261119/config-value-runtime.json"


def run(*args: str, input_text: str | None = None) -> str:
    completed = subprocess.run(args, input=input_text, text=True, capture_output=True)
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip())
    return completed.stdout.strip()


def listening(port: int) -> bool:
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def sql(statement: str) -> str:
    return run("docker", "exec", "-i", MYSQL, "sh", "-c",
               'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw --skip-column-names -D "$1"',
               "probe", SCHEMA, input_text=statement)


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def call(method: str, path: str, tenant: int | None, token: str | None = None,
         body: dict | None = None) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    if tenant is not None:
        headers["tenant-id"] = str(tenant)
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(f"http://127.0.0.1:{APP_PORT}/admin-api{path}", method=method,
                      headers=headers, data=None if body is None else json.dumps(body).encode())
    try:
        response = urlopen(request, timeout=25)
    except HTTPError as error:
        response = error
    with response:
        return response.status, json.load(response)


def main() -> None:
    assert JAR.is_file()
    assert not any(listening(port) for port in (MYSQL_PORT, REDIS_PORT, APP_PORT))
    existing = run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
    assert MYSQL not in existing and REDIS not in existing

    db_password, redis_password = secrets.token_hex(20), secrets.token_hex(20)
    username = "t4config121"
    password = secrets.token_urlsafe(12)[:16]
    password_hash = subprocess.run(["htpasswd", "-bnBC", "4", username, password],
                                   capture_output=True, text=True, check=True).stdout.strip().split(":", 1)[1]
    app = None
    log_path = Path("/tmp/yh-configvalue-runtime-20261119.log")
    owned: list[str] = []
    result = {
        "work_id": "YH-20261111-full-source-migration",
        "schema": SCHEMA,
        "jar_sha256": hashlib.sha256(JAR.read_bytes()).hexdigest(),
        "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT, "app": APP_PORT},
        "cases": {},
    }
    try:
        run("docker", "run", "-d", "--name", MYSQL,
            "-e", "MYSQL_ROOT_PASSWORD=" + db_password, "-e", "MYSQL_DATABASE=" + SCHEMA,
            "-p", f"127.0.0.1:{MYSQL_PORT}:3306", "mysql:8.0.33")
        owned.append(MYSQL)
        run("docker", "run", "-d", "--name", REDIS,
            "-p", f"127.0.0.1:{REDIS_PORT}:6379", "redis:7.2.17", "redis-server",
            "--requirepass", redis_password)
        owned.append(REDIS)
        deadline = time.monotonic() + 100
        while True:
            try:
                assert sql("SELECT DATABASE();") == SCHEMA
                break
            except (RuntimeError, AssertionError):
                assert time.monotonic() < deadline, "isolated MySQL readiness timeout"
                time.sleep(1)

        env = dict(os.environ, YUHENG_DB_HOST="127.0.0.1", YUHENG_DB_PORT=str(MYSQL_PORT),
                   YUHENG_DB_NAME=SCHEMA, YUHENG_DB_USERNAME="root", YUHENG_DB_PASSWORD=db_password,
                   YUHENG_REDIS_PASSWORD=redis_password)
        log = log_path.open("w")
        app = subprocess.Popen(["java", "-jar", str(JAR), f"--server.port={APP_PORT}",
            "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
            f"--spring.data.redis.port={REDIS_PORT}", "--spring.data.redis.database=0",
            "--spring.data.redis.password=" + redis_password, "--yudao.security.mock-enable=false",
            "--spring.quartz.auto-startup=false", "--yudao.captcha.enable=false",
            "--logging.level.com.yuheng=INFO"], cwd=ROOT, env=env, stdout=log, stderr=log)
        owned.append("process")
        deadline = time.monotonic() + 150
        while not listening(APP_PORT):
            assert app.poll() is None, "isolated backend exited before listening"
            assert time.monotonic() < deadline, "isolated backend readiness timeout"
            time.sleep(1)

        assert int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")) == 54
        sql("UPDATE system_tenant SET status=0, expire_time=DATE_ADD(NOW(), INTERVAL 1 YEAR) "
            "WHERE id IN (121,122) AND deleted=0;")
        assert sql("SELECT COUNT(*) FROM system_tenant WHERE id IN (121,122) AND status=0 "
                   "AND expire_time>NOW() AND deleted=0;") == "2"
        tenant_snapshot_query = ("SELECT id,name,status+0,deleted+0,expire_time FROM system_tenant "
                                 "WHERE deleted=0 AND status=0 ORDER BY id;")
        active_tenants_before = sql(tenant_snapshot_query)
        assert sql("SELECT COUNT(*) FROM infra_config WHERE id IN (990021,990022) "
                   "OR config_key IN ('t4.config.visible','t4.config.hidden');") == "0"
        assert sql("SELECT COUNT(*) FROM system_users WHERE id=990031 OR username='t4config121';") == "0"
        sql("INSERT INTO infra_config (id,category,type,name,config_key,value,visible,remark,creator,updater,deleted) "
            "VALUES (990021,'probe',2,'Visible probe','t4.config.visible','visible-value',b'1','probe','probe','probe',b'0'),"
            "(990022,'probe',2,'Hidden probe','t4.config.hidden','secret-value',b'0','probe','probe','probe',b'0');")
        sql("INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) "
            "VALUES (990031," + sql_literal(username) + "," + sql_literal(password_hash)
            + ",'Tenant 121 config probe',NULL,'[]',0,b'0',121);")
        assert sql("SELECT COUNT(*) FROM system_users WHERE id=990031 AND tenant_id=121 AND password<>'';") == "1"
        assert sql("SELECT COUNT(*) FROM system_user_role WHERE user_id=990031 AND deleted=0;") == "0"
        snapshot_query = ("SELECT id,config_key,SHA2(value,256),visible+0,deleted+0 FROM infra_config "
                          "WHERE id IN (990021,990022) ORDER BY id;")
        before = sql(snapshot_query)
        assert len(before.splitlines()) == 2

        status, tenant_list = call("GET", "/system/tenant/simple-list", None)
        assert status == 200 and tenant_list.get("code") == 0, (status, tenant_list)
        tenant_items = tenant_list.get("data")
        assert isinstance(tenant_items, list)
        expected_tenant_ids = [int(row.split("\t", 1)[0]) for row in active_tenants_before.splitlines()]
        assert sorted(item["id"] for item in tenant_items) == expected_tenant_ids, tenant_items
        assert all({key for key, value in item.items() if value is not None} == {"id", "name"}
                   for item in tenant_items), tenant_items
        result["cases"]["anonymous_tenant_simple_list_no_tenant_header"] = {
            "http": status, "code": tenant_list.get("code"),
            "tenant_ids": sorted(item["id"] for item in tenant_items),
            "non_null_fields": sorted({key for item in tenant_items for key, value in item.items()
                                        if value is not None}),
            "nullable_vo_fields_also_serialized": True}

        status, payload = call("GET", "/infra/config/get-value-by-key?key=t4.config.visible", 121)
        assert status == 200 and payload.get("code") == 401, (status, payload)
        result["cases"]["anonymous_visible"] = {"http": status, "code": payload.get("code")}

        status, login = call("POST", "/system/auth/login", 121,
                             body={"username": username, "password": password})
        assert status == 200 and login.get("code") == 0, (status, login)
        token = login["data"]["accessToken"]

        status, visible = call("GET", "/infra/config/get-value-by-key?key=t4.config.visible", 121, token)
        assert status == 200 and visible.get("code") == 0 and visible.get("data") == "visible-value", visible
        result["cases"]["real_token_visible_matching_tenant"] = {
            "http": status, "code": visible.get("code"), "value_returned": visible.get("data")}

        status, hidden = call("GET", "/infra/config/get-value-by-key?key=t4.config.hidden", 121, token)
        assert status == 200 and hidden.get("code") == 1001000004 and hidden.get("data") is None, hidden
        result["cases"]["real_token_hidden_value"] = {
            "http": status, "code": hidden.get("code"), "value_suppressed": hidden.get("data") is None}

        status, forged = call("GET", "/infra/config/get-value-by-key?key=t4.config.visible", 122, token)
        assert status == 200 and forged.get("code") == 403, forged
        result["cases"]["real_token_forged_tenant_header"] = {
            "token_tenant_id": 121, "request_tenant_id": 122,
            "http": status, "code": forged.get("code"), "denied": True}

        after = sql(snapshot_query)
        assert after == before, (before, after)
        result["config_snapshot"] = {"before": before, "after": after, "unchanged": True}
        active_tenants_after = sql(tenant_snapshot_query)
        assert active_tenants_after == active_tenants_before
        result["active_tenant_snapshot"] = {"before": active_tenants_before,
                                             "after": active_tenants_after,
                                             "unchanged": True}
        result["user"] = {"id": 990031, "tenant_id": 121, "password_hash_recorded": False}
        result["conclusion"] = "Anonymous access is rejected; a real tenant-121 token can read a visible platform config value, cannot read a hidden value, and is rejected with code 403 when the request tenant header is changed to 122."
        print(json.dumps(result["cases"], ensure_ascii=False, indent=2))
    finally:
        if app is not None:
            app.terminate()
            try:
                app.wait(timeout=35)
            except subprocess.TimeoutExpired:
                app.kill()
                app.wait(timeout=10)
            result["graceful_shutdown"] = "Graceful shutdown complete" in log_path.read_text(errors="replace")
        for container in reversed([name for name in owned if name != "process"]):
            subprocess.run(["docker", "rm", "-fv", container], check=True, capture_output=True, text=True)
        result["cleanup"] = {
            "containers_absent": all(name not in run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
                                      for name in (MYSQL, REDIS)),
            "ports_listening": {str(port): listening(port) for port in (MYSQL_PORT, REDIS_PORT, APP_PORT)},
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        assert result["cleanup"]["containers_absent"] and not any(result["cleanup"]["ports_listening"].values())


if __name__ == "__main__":
    main()
