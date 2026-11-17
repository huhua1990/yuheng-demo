#!/usr/bin/env python3
"""Verify infra config endpoint permissions with real logins on disposable services."""

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
SCHEMA = "yuheng_t4_configperm_20261120"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13355, 16435, 48190
MYSQL, REDIS = "yh-configperm-mysql-20261120", "yh-configperm-redis-20261120"
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/controller-security-inventory-20261119/config-permission-runtime.json"


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


def call(method: str, path: str, token: str | None = None, body: dict | None = None,
         tenant: int | None = 1) -> tuple[int, dict]:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if tenant is not None:
        headers["tenant-id"] = str(tenant)
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(f"http://127.0.0.1:{APP_PORT}/admin-api{path}", method=method, headers=headers,
                      data=None if body is None else json.dumps(body).encode())
    try:
        response = urlopen(request, timeout=25)
    except HTTPError as error:
        response = error
    with response:
        content = response.read()
        if "json" in response.headers.get("Content-Type", ""):
            return response.status, json.loads(content)
        return response.status, {"binary_size": len(content), "content_type": response.headers.get("Content-Type", "")}


def login(username: str, password: str) -> str:
    request = Request(f"http://127.0.0.1:{APP_PORT}/admin-api/system/auth/login",
                      data=json.dumps({"username": username, "password": password}).encode(),
                      method="POST", headers={"tenant-id": "1", "Content-Type": "application/json"})
    try:
        response = urlopen(request, timeout=25)
    except HTTPError as error:
        response = error
    with response:
        payload = json.load(response)
    assert response.status == 200 and payload.get("code") == 0, payload
    return payload["data"]["accessToken"]


def main() -> None:
    assert JAR.is_file()
    assert not any(listening(port) for port in (MYSQL_PORT, REDIS_PORT, APP_PORT))
    existing = run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
    assert MYSQL not in existing and REDIS not in existing

    db_password, redis_password = secrets.token_hex(20), secrets.token_hex(20)
    suffix = secrets.token_hex(5)
    users = {"denied": (990041, "t4cdenied" + suffix),
             "allowed": (990043, "t4callowed" + suffix)}
    passwords = {name: secrets.token_urlsafe(12)[:16] for name in users}
    hashes = {name: subprocess.run(["htpasswd", "-bnBC", "4", users[name][1], passwords[name]],
                                   capture_output=True, text=True, check=True).stdout.strip().split(":", 1)[1]
              for name in users}
    app = None
    log_path = Path("/tmp/yh-postpage-runtime-20261120.log")
    owned: list[str] = []
    result = {"work_id": "YH-20261111-full-source-migration", "schema": SCHEMA,
              "permission": "infra:config", "jar_sha256": hashlib.sha256(JAR.read_bytes()).hexdigest(),
              "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT, "app": APP_PORT}, "cases": {}}
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

        assert int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")) == 56
        menus = sql("SELECT id,permission FROM system_menu WHERE deleted=0 AND permission IN "
                    "('infra:config:create','infra:config:update','infra:config:delete','infra:config:query','infra:config:export') ORDER BY id;")
        menu_ids = {row.split("\t", 1)[1]: int(row.split("\t", 1)[0]) for row in menus.splitlines()}
        expected_permissions = {"infra:config:create", "infra:config:update", "infra:config:delete",
                                "infra:config:query", "infra:config:export"}
        assert expected_permissions <= menu_ids.keys(), menu_ids
        assert sql("SELECT COUNT(*) FROM infra_config WHERE config_key LIKE 't4.configperm.%';") == "0"
        for name, (user_id, username) in users.items():
            assert sql("SELECT COUNT(*) FROM system_users WHERE id=" + str(user_id)
                       + " OR username=" + sql_literal(username) + ";") == "0"
        assert sql("SELECT COUNT(*) FROM system_role WHERE id=990042;") == "0"
        sql("INSERT INTO system_role (id,name,code,sort,data_scope,data_scope_dept_ids,status,type,remark,creator,updater,deleted,tenant_id) "
            "VALUES (990042,'T4 config permission probe','t4_configperm_" + suffix
            + "',1,1,'',0,1,'isolated permission fixture','probe','probe',b'0',1);")
        role_menu_rows = ",".join("(9900" + str(44 + index) + ",990042," + str(menu_id)
                                   + ",'probe','probe',b'0',1)" for index, menu_id in enumerate(menu_ids.values()))
        sql("INSERT INTO system_role_menu (id,role_id,menu_id,creator,updater,deleted,tenant_id) VALUES "
            + role_menu_rows + ";")
        for name, (user_id, username) in users.items():
            sql("INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) VALUES ("
                + str(user_id) + "," + sql_literal(username) + "," + sql_literal(hashes[name])
                + "," + sql_literal("T4 config permission " + name) + ",NULL,'[]',0,b'0',1);")
        sql("INSERT INTO system_user_role (id,user_id,role_id,creator,updater,deleted,tenant_id) "
            "VALUES (990060,990043,990042,'probe','probe',b'0',1);")
        assert sql("SELECT COUNT(*) FROM system_user_role WHERE user_id=990041 AND deleted=0;") == "0"
        assert sql("SELECT COUNT(DISTINCT m.permission) FROM system_user_role ur JOIN system_role_menu rm "
                   "ON rm.role_id=ur.role_id AND rm.deleted=0 JOIN system_menu m ON m.id=rm.menu_id "
                   "WHERE ur.user_id=990043 AND ur.deleted=0 AND m.permission LIKE 'infra:config:%';") == "5"

        config_snapshot_query = "SELECT * FROM infra_config ORDER BY id;"
        before = sql(config_snapshot_query)
        denied_token = login(users["denied"][1], passwords["denied"])
        after_denied = before
        cases = [
            ("create", "POST", "/infra/config/create", {"category":"probe","name":"Denied","key":"t4.configperm.denied","value":"x","visible":True}, "infra:config:create"),
            ("update", "PUT", "/infra/config/update", {"id":1,"category":"probe","name":"Denied","key":"t4.configperm.update","value":"x","visible":True}, "infra:config:update"),
            ("delete", "DELETE", "/infra/config/delete?id=1", None, "infra:config:delete"),
            ("batch_delete", "DELETE", "/infra/config/delete-list?ids=1,2", None, "infra:config:delete"),
            ("export", "GET", "/infra/config/export-excel?pageNo=1&pageSize=10", None, "infra:config:export"),
        ]
        for name, method, path, body, permission in cases:
            status, payload = call(method, path, denied_token, body)
            assert status == 200 and payload.get("code") == 403, (name, status, payload)
            after_denied = sql(config_snapshot_query)
            assert after_denied == before, name
            result["cases"]["denied_" + name] = {"http": status, "code": payload.get("code"),
                                                   "snapshot_unchanged": True, "required_permission": permission}

        allowed_token = login(users["allowed"][1], passwords["allowed"])
        status, payload = call("GET", "/infra/config/page?pageNo=1&pageSize=10", allowed_token)
        assert status == 200 and payload.get("code") == 0 and payload["data"]["total"] > 0, payload
        result["cases"]["allowed_query"] = {"http": status, "code": 0, "total": payload["data"]["total"]}
        created = []
        for index in (1, 2, 3):
            body = {"category": "probe", "name": f"Allowed {index}", "key": f"t4.configperm.allowed.{index}",
                    "value": "ok", "visible": True}
            status, payload = call("POST", "/infra/config/create", allowed_token, body)
            assert status == 200 and payload.get("code") == 0 and isinstance(payload.get("data"), int), payload
            created.append(payload["data"])
        result["cases"]["allowed_create"] = {"http": 200, "code": 0, "ids": created}
        updated_body = {"id": created[0], "category": "probe", "name": "Allowed updated",
                        "key": "t4.configperm.allowed.1", "value": "updated", "visible": True}
        status, payload = call("PUT", "/infra/config/update", allowed_token, updated_body)
        assert status == 200 and payload.get("code") == 0, payload
        assert sql("SELECT value FROM infra_config WHERE id=" + str(created[0]) + ";") == "updated"
        result["cases"]["allowed_update"] = {"http": status, "code": 0, "value_persisted": True}
        status, payload = call("GET", "/infra/config/export-excel?pageNo=1&pageSize=10", allowed_token)
        assert status == 200 and payload.get("binary_size", 0) > 100, payload
        result["cases"]["allowed_export"] = {"http": status, **payload}
        for name, path in (("delete", f"/infra/config/delete?id={created[0]}"),
                           ("batch_delete", f"/infra/config/delete-list?ids={created[1]},{created[2]}")):
            status, payload = call("DELETE", path, allowed_token)
            assert status == 200 and payload.get("code") == 0, payload
            result["cases"]["allowed_" + name] = {"http": status, "code": 0}
        assert sql("SELECT COUNT(*) FROM infra_config WHERE config_key LIKE 't4.configperm.allowed.%' AND deleted=1;") == "3"
        result["config_snapshot"] = {"before_sha256": hashlib.sha256(before.encode()).hexdigest(),
                                      "after_denied_sha256": hashlib.sha256(after_denied.encode()).hexdigest(),
                                      "denied_requests_unchanged": True}
        result["users"] = {name: {"id": value[0], "tenant_id": 1,
                                  "password_hash_recorded": False} for name, value in users.items()}
        result["conclusion"] = "A real authenticated user with no role is forbidden from infra config create, update, single delete, batch delete and export, with the entire config snapshot unchanged after every denied request. A user granted the five config permissions can query, create, update, delete and export."
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
            "ports_listening": {str(port): listening(port) for port in (MYSQL_PORT, REDIS_PORT, APP_PORT)}}
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        assert result["cleanup"]["containers_absent"] and not any(result["cleanup"]["ports_listening"].values())


if __name__ == "__main__":
    main()
