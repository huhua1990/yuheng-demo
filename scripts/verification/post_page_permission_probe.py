#!/usr/bin/env python3
"""Verify the post page permission with real logins on disposable services."""

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
SCHEMA = "yuheng_t4_postpage_20261120"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13350, 16430, 48185
MYSQL, REDIS = "yh-postpage-mysql-20261120", "yh-postpage-redis-20261120"
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/controller-security-inventory-20261119/post-page-permission-runtime.json"


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


def call(path: str, token: str | None = None, tenant: int | None = 1) -> tuple[int, dict]:
    headers = {"Accept": "application/json"}
    if tenant is not None:
        headers["tenant-id"] = str(tenant)
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(f"http://127.0.0.1:{APP_PORT}/admin-api{path}", headers=headers)
    try:
        response = urlopen(request, timeout=25)
    except HTTPError as error:
        response = error
    with response:
        return response.status, json.load(response)


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
    users = {"denied": (990041, "t4pdenied" + suffix),
             "allowed": (990043, "t4pallowed" + suffix)}
    passwords = {name: secrets.token_urlsafe(12)[:16] for name in users}
    hashes = {name: subprocess.run(["htpasswd", "-bnBC", "4", users[name][1], passwords[name]],
                                   capture_output=True, text=True, check=True).stdout.strip().split(":", 1)[1]
              for name in users}
    app = None
    log_path = Path("/tmp/yh-postpage-runtime-20261120.log")
    owned: list[str] = []
    result = {"work_id": "YH-20261111-full-source-migration", "schema": SCHEMA,
              "permission": "system:post:query", "permission_menu_id": 43,
              "jar_sha256": hashlib.sha256(JAR.read_bytes()).hexdigest(),
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

        assert int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")) == 54
        assert sql("SELECT permission FROM system_menu WHERE id=43 AND deleted=0;") == "system:post:query"
        for name, (user_id, username) in users.items():
            assert sql("SELECT COUNT(*) FROM system_users WHERE id=" + str(user_id)
                       + " OR username=" + sql_literal(username) + ";") == "0"
        assert sql("SELECT COUNT(*) FROM system_role WHERE id=990042;") == "0"
        sql("INSERT INTO system_role (id,name,code,sort,data_scope,data_scope_dept_ids,status,type,remark,creator,updater,deleted,tenant_id) "
            "VALUES (990042,'T4 post page probe','t4_postpage_" + suffix
            + "',1,1,'',0,1,'isolated permission fixture','probe','probe',b'0',1);")
        sql("INSERT INTO system_role_menu (id,role_id,menu_id,creator,updater,deleted,tenant_id) "
            "VALUES (990044,990042,43,'probe','probe',b'0',1);")
        for name, (user_id, username) in users.items():
            sql("INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) VALUES ("
                + str(user_id) + "," + sql_literal(username) + "," + sql_literal(hashes[name])
                + "," + sql_literal("T4 post page " + name) + ",NULL,'[]',0,b'0',1);")
        sql("INSERT INTO system_user_role (id,user_id,role_id,creator,updater,deleted,tenant_id) "
            "VALUES (990045,990043,990042,'probe','probe',b'0',1);")
        assert sql("SELECT COUNT(*) FROM system_user_role WHERE user_id=990041 AND deleted=0;") == "0"
        assert sql("SELECT COUNT(*) FROM system_user_role ur JOIN system_role_menu rm ON rm.role_id=ur.role_id "
                   "WHERE ur.user_id=990043 AND ur.deleted=0 AND rm.menu_id=43 AND rm.deleted=0;") == "1"

        post_snapshot_query = ("SELECT id,HEX(code),HEX(name),sort,status+0,deleted+0,tenant_id FROM system_post "
                               "ORDER BY id;")
        before = sql(post_snapshot_query)
        anon_status, anon = call("/system/post/page?pageNo=1&pageSize=10", tenant=None)
        assert anon_status == 200 and anon.get("code") == 401, (anon_status, anon)
        result["cases"]["anonymous"] = {"http": anon_status, "code": anon.get("code")}

        denied_token = login(users["denied"][1], passwords["denied"])
        denied_status, denied = call("/system/post/page?pageNo=1&pageSize=10", denied_token)
        assert denied_status == 200 and denied.get("code") == 403, (denied_status, denied)
        after_denied = sql(post_snapshot_query)
        assert after_denied == before
        result["cases"]["real_login_without_permission"] = {
            "http": denied_status, "code": denied.get("code"), "post_snapshot_unchanged": True}

        allowed_token = login(users["allowed"][1], passwords["allowed"])
        allowed_status, allowed = call("/system/post/page?pageNo=1&pageSize=10", allowed_token)
        assert allowed_status == 200 and allowed.get("code") == 0, (allowed_status, allowed)
        assert isinstance(allowed.get("data", {}).get("list"), list), allowed
        result["cases"]["real_login_with_query_permission"] = {
            "http": allowed_status, "code": allowed.get("code"),
            "returned_rows": len(allowed["data"]["list"]),
            "total": allowed["data"].get("total")}
        result["post_snapshot"] = {"before": before, "after_denied": after_denied,
                                   "unchanged_after_denied_request": True}
        result["users"] = {name: {"id": value[0], "tenant_id": 1,
                                  "password_hash_recorded": False} for name, value in users.items()}
        result["conclusion"] = "Anonymous requests are rejected, an ordinary real-login user without system:post:query is forbidden, and a user granted only that query permission can read the post page. The denied request does not mutate post rows."
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
