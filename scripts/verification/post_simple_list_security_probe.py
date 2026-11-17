#!/usr/bin/env python3
"""Exercise the post simple-list auth and tenant filters on disposable services."""

from __future__ import annotations

import hashlib
import json
import secrets
import socket
import subprocess
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "yuheng_t4_postlist_20261119"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13348, 16428, 48183
MYSQL, REDIS = "yh-postlist-mysql-20261119", "yh-postlist-redis-20261119"
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/controller-security-inventory-20261119/post-simple-list-runtime.json"


def run(*args: str, input_text: str | None = None) -> str:
    return subprocess.run(args, input=input_text, text=True, capture_output=True, check=True).stdout.strip()


def listening(port: int) -> bool:
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def request(path: str, tenant: int, token: str | None) -> tuple[int, dict]:
    headers = {"tenant-id": str(tenant)}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = Request(f"http://127.0.0.1:{APP_PORT}/admin-api{path}", headers=headers)
    try:
        response = urlopen(req, timeout=25)
    except HTTPError as error:
        response = error
    with response:
        return response.status, json.load(response)


def post_json(path: str, body: dict, tenant: int) -> tuple[int, dict]:
    req = Request(f"http://127.0.0.1:{APP_PORT}/admin-api{path}",
                  data=json.dumps(body).encode(), method="POST",
                  headers={"tenant-id": str(tenant), "Content-Type": "application/json"})
    try:
        response = urlopen(req, timeout=25)
    except HTTPError as error:
        response = error
    with response:
        return response.status, json.load(response)


def sql(statement: str) -> str:
    command = ["docker", "exec", "-i", MYSQL, "sh", "-c",
               'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw --skip-column-names -D "$1"',
               "probe", SCHEMA]
    completed = subprocess.run(command, input=statement, text=True, capture_output=True)
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip())
    return completed.stdout.strip()


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> None:
    assert JAR.is_file()
    assert not any(listening(port) for port in (MYSQL_PORT, REDIS_PORT, APP_PORT))
    existing = run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
    assert MYSQL not in existing and REDIS not in existing
    db_password, redis_password, mock_secret = (secrets.token_hex(20) for _ in range(3))
    real_username = "t4tenant121"
    real_password = secrets.token_urlsafe(12)[:16]
    password_hash = subprocess.run(["htpasswd", "-bnBC", "4", real_username, real_password],
                                   capture_output=True, text=True, check=True).stdout.strip().split(":", 1)[1]
    app = None
    log_path = Path("/tmp/yh-postlist-runtime-20261119.log")
    result = {"work_id": "YH-20261111-full-source-migration", "schema": SCHEMA,
              "jar_sha256": hashlib.sha256(JAR.read_bytes()).hexdigest(),
              "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT, "app": APP_PORT},
              "mock_auth": "isolated process only; random secret", "cases": {}}
    owned: list[str] = []
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

        import os
        env = dict(os.environ, YUHENG_DB_HOST="127.0.0.1", YUHENG_DB_PORT=str(MYSQL_PORT),
                   YUHENG_DB_NAME=SCHEMA, YUHENG_DB_USERNAME="root", YUHENG_DB_PASSWORD=db_password,
                   YUHENG_REDIS_PASSWORD=redis_password)
        log = log_path.open("w")
        app = subprocess.Popen(["java", "-jar", str(JAR), f"--server.port={APP_PORT}",
            "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
            f"--spring.data.redis.port={REDIS_PORT}", "--spring.data.redis.database=0",
            "--spring.data.redis.password=" + redis_password, "--yudao.security.mock-enable=true",
            "--yudao.security.mock-secret=" + mock_secret, "--spring.quartz.auto-startup=false",
            "--yudao.captcha.enable=false",
            "--logging.level.com.yuheng=INFO"], cwd=ROOT, env=env, stdout=log, stderr=log)
        owned.append("process")
        deadline = time.monotonic() + 150
        while not listening(APP_PORT):
            assert app.poll() is None, "isolated backend exited before listening"
            assert time.monotonic() < deadline, "isolated backend readiness timeout"
            time.sleep(1)
        changesets = int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;"))
        assert changesets == 54, changesets
        assert sql("SELECT COUNT(*) FROM system_post WHERE id IN (990001,990002);") == "0"
        sql("UPDATE system_tenant SET status=0, expire_time=DATE_ADD(NOW(), INTERVAL 1 YEAR) "
            "WHERE id IN (121,122) AND deleted=0;")
        assert sql("SELECT COUNT(*) FROM system_tenant WHERE id IN (121,122) AND status=0 "
                   "AND expire_time>NOW() AND deleted=0;") == "2"
        seed_counts = {"tenant_121": int(sql("SELECT COUNT(*) FROM system_post WHERE tenant_id=121 AND deleted=0;")),
                       "tenant_122": int(sql("SELECT COUNT(*) FROM system_post WHERE tenant_id=122 AND deleted=0;"))}
        fixture = ("INSERT INTO system_post (id,code,name,sort,status,remark,creator,updater,tenant_id) VALUES "
                   "(990001,'T4-PST-121','Tenant 121 Post',1,0,'fixture','probe','probe',121),"
                   "(990002,'T4-PST-122','Tenant 122 Post',1,0,'fixture','probe','probe',122);")
        sql(fixture)
        sql("INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) "
            "VALUES (990011," + sql_literal(real_username) + "," + sql_literal(password_hash)
            + ",'Tenant 121 auth probe',NULL,'[]',0,b'0',121);")
        assert sql("SELECT COUNT(*) FROM system_users WHERE id=990011 AND tenant_id=121 AND password<>'';") == "1"
        result["changesets"] = changesets
        result["seed_active_post_counts"] = seed_counts
        result["fixtures"] = {"tenant_121_post_id": 990001, "tenant_122_post_id": 990002}

        anon_status, anon = request("/system/post/simple-list", 121, None)
        assert anon_status == 200 and anon.get("code") == 401, (anon_status, anon)
        result["cases"]["anonymous_tenant_121"] = {"http": anon_status, "code": anon.get("code")}

        no_permission_status, no_permission = request("/system/post/simple-list", 121, mock_secret + "900099")
        assert no_permission_status == 200 and no_permission.get("code") == 0, (no_permission_status, no_permission)
        names1 = [row["name"] for row in no_permission["data"]]
        assert "Tenant 121 Post" in names1 and "Tenant 122 Post" not in names1, names1
        result["cases"]["authenticated_without_role_or_permission_tenant_121"] = {
            "http": no_permission_status, "code": no_permission.get("code"),
            "returned_fixture_names": [name for name in names1 if name.startswith("Tenant 12")],
            "foreign_tenant_row_absent": "Tenant 122 Post" not in names1}

        tenant122_status, tenant122 = request("/system/post/simple-list", 122, mock_secret + "900099")
        assert tenant122_status == 200 and tenant122.get("code") == 0, (tenant122_status, tenant122)
        names122 = [row["name"] for row in tenant122["data"]]
        assert "Tenant 122 Post" in names122 and "Tenant 121 Post" not in names122, names122
        result["cases"]["authenticated_without_role_or_permission_tenant_122"] = {
            "http": tenant122_status, "code": tenant122.get("code"),
            "returned_fixture_names": [name for name in names122 if name.startswith("Tenant 12")],
            "foreign_tenant_row_absent": "Tenant 121 Post" not in names122}

        login_status, login = post_json("/system/auth/login",
                                        {"username": real_username, "password": real_password}, 121)
        assert login_status == 200 and login.get("code") == 0, (login_status, login)
        real_token = login["data"]["accessToken"]
        real_same_status, real_same = request("/system/post/simple-list", 121, real_token)
        assert real_same_status == 200 and real_same.get("code") == 0, (real_same_status, real_same)
        real_names = [row["name"] for row in real_same["data"]]
        assert "Tenant 121 Post" in real_names and "Tenant 122 Post" not in real_names
        result["cases"]["real_token_matching_tenant_header"] = {
            "login_http": login_status, "login_code": login.get("code"),
            "request_http": real_same_status, "request_code": real_same.get("code"),
            "returned_fixture_names": [name for name in real_names if name.startswith("Tenant 12")],
            "foreign_tenant_row_absent": "Tenant 122 Post" not in real_names}

        forged_status, forged = request("/system/post/simple-list", 122, real_token)
        assert forged_status == 200 and forged.get("code") == 403, (forged_status, forged)
        result["cases"]["real_token_forged_tenant_header"] = {
            "token_tenant_id": 121, "request_tenant_id": 122,
            "http": forged_status, "code": forged.get("code"), "denied": forged.get("code") == 403}

        result["sql_fixture_rows"] = sql("SELECT id,tenant_id,name,status,deleted FROM system_post "
                                         "WHERE id IN (990001,990002) ORDER BY id;")
        result["tenant_fixture_adjustment"] = "Only disposable tenants 121 and 122 had status reset to enabled and expire_time extended one year; the schema and container are destroyed after the probe."
        result["real_login_user"] = {"id": 990011, "tenant_id": 121, "password_hash_recorded": False}
        result["conclusion"] = "Anonymous access is rejected; an authenticated mock principal with no role can read the upstream-defined simple list; SQL results follow the active tenant context in both directions. A real token issued to a disposable tenant-121 user reads tenant-121 rows and is denied with code 403 when the request tenant header is changed to 122."
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"changesets": changesets, "cases": result["cases"], "sql_fixture_rows": result["sql_fixture_rows"]}, ensure_ascii=False, indent=2))
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
        result["cleanup"] = {"containers_absent": all(
            name not in run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
            for name in (MYSQL, REDIS)),
            "ports_listening": {str(port): listening(port) for port in (MYSQL_PORT, REDIS_PORT, APP_PORT)}}
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        assert result["cleanup"]["containers_absent"] and not any(result["cleanup"]["ports_listening"].values())


if __name__ == "__main__":
    main()
