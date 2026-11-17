#!/usr/bin/env python3
"""Exercise the user simple-list auth, tenant filter, and department filter in isolation."""

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
SCHEMA = "yuheng_t4_userlist_20261120"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13359, 16439, 48196
MYSQL, REDIS = "yh-userlist-mysql-20261120", "yh-userlist-redis-20261120"
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
OUT = ROOT / (
    "docs/verification/2026-11-11-full-source-migration/"
    "controller-security-inventory-20261119/user-simple-list-runtime.json"
)
EXPECTED_CHANGESETS = 56


def run(*args: str, input_text: str | None = None) -> str:
    completed = subprocess.run(args, input=input_text, text=True, capture_output=True)
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip())
    return completed.stdout.strip()


def listening(port: int) -> bool:
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def sql(statement: str) -> str:
    return run(
        "docker", "exec", "-i", MYSQL, "sh", "-c",
        'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
        '--skip-column-names -D "$1"',
        "probe", SCHEMA, input_text=statement,
    )


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def read_json(request: Request) -> tuple[int, dict]:
    try:
        response = urlopen(request, timeout=25)
    except HTTPError as error:
        response = error
    with response:
        return response.status, json.load(response)


def request(path: str, token: str | None, tenant: int | None) -> tuple[int, dict]:
    headers = {"Accept": "application/json"}
    if tenant is not None:
        headers["tenant-id"] = str(tenant)
    if token:
        headers["Authorization"] = "Bearer " + token
    return read_json(Request(f"http://127.0.0.1:{APP_PORT}/admin-api{path}", headers=headers))


def login(username: str, password: str) -> str:
    status, payload = read_json(Request(
        f"http://127.0.0.1:{APP_PORT}/admin-api/system/auth/login",
        data=json.dumps({"username": username, "password": password}).encode(),
        method="POST",
        headers={"tenant-id": "121", "Content-Type": "application/json"},
    ))
    assert status == 200 and payload.get("code") == 0, {"http": status, "payload": payload}
    return payload["data"]["accessToken"]


def names(payload: dict) -> list[str]:
    data = payload.get("data")
    assert isinstance(data, list), payload
    return [str(row.get("nickname")) for row in data]


def main() -> None:
    assert JAR.is_file()
    ports = (MYSQL_PORT, REDIS_PORT, APP_PORT)
    assert not any(listening(port) for port in ports)
    existing = run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
    assert MYSQL not in existing and REDIS not in existing

    db_password = secrets.token_hex(20)
    redis_password = secrets.token_hex(20)
    suffix = secrets.token_hex(5)
    login_username = "t4userlist" + suffix
    login_password = secrets.token_urlsafe(12)[:16]
    password_hash = subprocess.run(
        ["htpasswd", "-bnBC", "4", login_username, login_password],
        capture_output=True, text=True, check=True,
    ).stdout.strip().split(":", 1)[1]
    app = None
    log_path = Path("/tmp/yh-userlist-runtime-20261120.log")
    owned: list[str] = []
    result = {
        "work_id": "YH-20261111-full-source-migration",
        "schema": SCHEMA,
        "jar_sha256": hashlib.sha256(JAR.read_bytes()).hexdigest(),
        "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT, "app": APP_PORT},
        "cases": {},
    }

    try:
        run(
            "docker", "run", "-d", "--name", MYSQL,
            "-e", "MYSQL_ROOT_PASSWORD=" + db_password,
            "-e", "MYSQL_DATABASE=" + SCHEMA,
            "-p", f"127.0.0.1:{MYSQL_PORT}:3306", "mysql:8.0.33",
        )
        owned.append(MYSQL)
        run(
            "docker", "run", "-d", "--name", REDIS,
            "-p", f"127.0.0.1:{REDIS_PORT}:6379", "redis:7.2.17",
            "redis-server", "--requirepass", redis_password,
        )
        owned.append(REDIS)

        deadline = time.monotonic() + 100
        while True:
            try:
                assert sql("SELECT DATABASE();") == SCHEMA
                break
            except (RuntimeError, AssertionError):
                assert time.monotonic() < deadline, "isolated MySQL readiness timeout"
                time.sleep(1)

        env = dict(
            os.environ,
            YUHENG_DB_HOST="127.0.0.1",
            YUHENG_DB_PORT=str(MYSQL_PORT),
            YUHENG_DB_NAME=SCHEMA,
            YUHENG_DB_USERNAME="root",
            YUHENG_DB_PASSWORD=db_password,
            YUHENG_REDIS_PASSWORD=redis_password,
        )
        log = log_path.open("w")
        app = subprocess.Popen(
            [
                "java", "-jar", str(JAR), f"--server.port={APP_PORT}",
                "--spring.profiles.active=local",
                "--spring.data.redis.host=127.0.0.1",
                f"--spring.data.redis.port={REDIS_PORT}",
                "--spring.data.redis.database=0",
                "--spring.data.redis.password=" + redis_password,
                "--yudao.security.mock-enable=false",
                "--spring.quartz.auto-startup=false",
                "--yudao.captcha.enable=false",
                "--logging.level.com.yuheng=INFO",
            ],
            cwd=ROOT, env=env, stdout=log, stderr=log,
        )
        owned.append("process")
        deadline = time.monotonic() + 150
        while not listening(APP_PORT):
            assert app.poll() is None, "isolated backend exited before listening"
            assert time.monotonic() < deadline, "isolated backend readiness timeout"
            time.sleep(1)
        deadline = time.monotonic() + 30
        while True:
            try:
                if int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")) == EXPECTED_CHANGESETS:
                    break
            except RuntimeError:
                pass
            assert time.monotonic() < deadline, "Liquibase readiness timeout"
            time.sleep(1)

        sql(
            "UPDATE system_tenant SET status=0, expire_time=DATE_ADD(NOW(), INTERVAL 1 YEAR) "
            "WHERE id IN (121,122) AND deleted=0;"
        )
        assert sql(
            "SELECT COUNT(*) FROM system_tenant WHERE id IN (121,122) "
            "AND status=0 AND expire_time>NOW() AND deleted=0;"
        ) == "2"
        sql(
            "INSERT INTO system_dept "
            "(id,name,parent_id,sort,leader_user_id,phone,email,status,creator,updater,deleted,tenant_id) VALUES "
            "(990601,'T4 User List Dept 121',0,1,NULL,NULL,NULL,0,'probe','probe',b'0',121),"
            "(990602,'T4 User List Dept 122',0,1,NULL,NULL,NULL,0,'probe','probe',b'0',122);"
        )
        sql(
            "INSERT INTO system_role "
            "(id,name,code,sort,data_scope,data_scope_dept_ids,status,type,remark,creator,updater,deleted,tenant_id) VALUES "
            "(990604,'T4 user list data scope','t4_userlist_" + suffix +
            "',1,1,'',0,1,'isolated data-scope fixture','probe','probe',b'0',121);"
        )
        sql(
            "INSERT INTO system_users "
            "(id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) VALUES "
            "(990601,'t4-list-121',''," + sql_literal("T4 User List 121") +
            ",990601,'[]',0,b'0',121),"
            "(990602,'t4-list-122',''," + sql_literal("T4 User List 122") +
            ",990602,'[]',0,b'0',122),"
            "(990603," + sql_literal(login_username) + "," + sql_literal(password_hash) +
            "," + sql_literal("T4 User List Login") + ",990601,'[]',0,b'0',121);"
        )
        sql(
            "INSERT INTO system_user_role "
            "(id,user_id,role_id,creator,updater,deleted,tenant_id) VALUES "
            "(990605,990603,990604,'probe','probe',b'0',121);"
        )
        assert sql(
            "SELECT COUNT(*) FROM system_users WHERE id IN (990601,990602,990603) "
            "AND status=0 AND deleted=0;"
        ) == "3"

        snapshot_query = (
            "SELECT id,username,HEX(nickname),dept_id,status+0,deleted+0,tenant_id "
            "FROM system_users ORDER BY id;"
        )
        before = sql(snapshot_query)
        anon_status, anon = request("/system/user/simple-list", None, None)
        assert anon_status == 200 and anon.get("code") == 401, (anon_status, anon)
        result["cases"]["anonymous"] = {"http": anon_status, "code": anon.get("code")}

        access_token = login(login_username, login_password)
        all_status, all_users = request("/system/user/simple-list", access_token, 121)
        assert all_status == 200 and all_users.get("code") == 0, (all_status, all_users)
        all_names = names(all_users)
        assert "T4 User List 121" in all_names
        assert "T4 User List Login" in all_names
        assert "T4 User List 122" not in all_names
        result["cases"]["real_token_tenant_filtered"] = {
            "login_code": 0,
            "http": all_status,
            "code": all_users.get("code"),
            "returned_fixture_names": [name for name in all_names if name.startswith("T4 User List")],
            "foreign_tenant_row_absent": "T4 User List 122" not in all_names,
        }

        filtered_status, filtered = request(
            "/system/user/simple-list?deptId=990601", access_token, 121,
        )
        assert filtered_status == 200 and filtered.get("code") == 0, (filtered_status, filtered)
        filtered_names = names(filtered)
        assert "T4 User List 121" in filtered_names
        assert "T4 User List Login" in filtered_names
        assert "T4 User List 122" not in filtered_names
        result["cases"]["real_token_department_filter"] = {
            "http": filtered_status,
            "code": filtered.get("code"),
            "dept_id": 990601,
            "returned_fixture_names": [name for name in filtered_names if name.startswith("T4 User List")],
            "foreign_dept_row_absent": "T4 User List 122" not in filtered_names,
        }

        forged_status, forged = request("/system/user/simple-list", access_token, 122)
        assert forged_status == 200 and forged.get("code") == 403, (forged_status, forged)
        result["cases"]["real_token_forged_tenant_header"] = {
            "token_tenant_id": 121,
            "request_tenant_id": 122,
            "http": forged_status,
            "code": forged.get("code"),
            "denied": True,
        }
        after = sql(snapshot_query)
        assert after == before
        result["sql_snapshot"] = {"before": before, "after": after, "unchanged": True}
        result["fixture"] = {
            "tenant_121_user_id": 990601,
            "tenant_122_user_id": 990602,
            "login_user_id": 990603,
            "password_hash_recorded": False,
        }
        result["changesets"] = EXPECTED_CHANGESETS
        result["conclusion"] = (
            "Anonymous user simple-list access was rejected. A tenant-121 real token returned only "
            "enabled tenant-121 users, the deptId filter retained only the requested department, and "
            "changing the tenant header to 122 was rejected; the user table snapshot remained unchanged."
        )
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
            "containers_absent": all(
                name not in run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
                for name in (MYSQL, REDIS)
            ),
            "ports_listening": {str(port): listening(port) for port in ports},
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        assert result["cleanup"]["containers_absent"] and not any(result["cleanup"]["ports_listening"].values())


if __name__ == "__main__":
    main()
