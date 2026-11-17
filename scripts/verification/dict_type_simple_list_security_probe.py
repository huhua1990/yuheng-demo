#!/usr/bin/env python3
"""Exercise the shared dictionary-type simple-list contract in isolation."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import socket
import subprocess
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "yuheng_t4_dicttypelist_20261120"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13361, 16441, 48198
MYSQL, REDIS = "yh-dicttypelist-mysql-20261120", "yh-dicttypelist-redis-20261120"
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
OUT = ROOT / (
    "docs/verification/2026-11-11-full-source-migration/"
    "controller-security-inventory-20261119/dict-type-simple-list-runtime.json"
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


def login(username: str, password: str, tenant: int) -> str:
    status, payload = read_json(Request(
        f"http://127.0.0.1:{APP_PORT}/admin-api/system/auth/login",
        data=json.dumps({"username": username, "password": password}).encode(),
        method="POST",
        headers={"tenant-id": str(tenant), "Content-Type": "application/json"},
    ))
    assert status == 200 and payload.get("code") == 0, {"http": status, "payload": payload}
    return payload["data"]["accessToken"]


def fixture_rows(payload: dict) -> list[tuple[int, str, str]]:
    data = payload.get("data")
    assert isinstance(data, list), payload
    rows = []
    for row in data:
        if str(row.get("type", "")).startswith("t4_dict_type_"):
            rows.append((int(row["id"]), str(row["name"]), str(row["type"])))
    return sorted(rows)


def main() -> None:
    assert JAR.is_file()
    ports = (MYSQL_PORT, REDIS_PORT, APP_PORT)
    assert not any(listening(port) for port in ports)
    existing = run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
    assert MYSQL not in existing and REDIS not in existing

    db_password = secrets.token_hex(20)
    redis_password = secrets.token_hex(20)
    suffix = secrets.token_hex(5)
    users = {
        121: ("t4dict121" + suffix, secrets.token_urlsafe(12)[:16]),
        122: ("t4dict122" + suffix, secrets.token_urlsafe(12)[:16]),
    }
    hashes = {
        tenant: subprocess.run(
            ["htpasswd", "-bnBC", "4", username, password],
            capture_output=True, text=True, check=True,
        ).stdout.strip().split(":", 1)[1]
        for tenant, (username, password) in users.items()
    }
    app = None
    log_path = Path("/tmp/yh-dicttypelist-runtime-20261120.log")
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
                "--logging.level.com.yuheng.platform.module.system.dal.mysql=DEBUG",
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
            "INSERT INTO system_dict_type "
            "(id,name,type,status,remark,creator,updater,deleted,deleted_time) VALUES "
            "(990801,'T4 Dict Type Enabled','t4_dict_type_enabled',0,'shared enabled fixture','probe','probe',b'0',NULL),"
            "(990802,'T4 Dict Type Disabled','t4_dict_type_disabled',1,'shared disabled fixture','probe','probe',b'0',NULL);"
        )
        sql(
            "INSERT INTO system_users "
            "(id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) VALUES "
            "(990803," + sql_literal(users[121][0]) + "," + sql_literal(hashes[121]) +
            ",'T4 Dict Tenant 121',NULL,'[]',0,b'0',121),"
            "(990804," + sql_literal(users[122][0]) + "," + sql_literal(hashes[122]) +
            ",'T4 Dict Tenant 122',NULL,'[]',0,b'0',122);"
        )
        assert sql(
            "SELECT COUNT(*) FROM system_dict_type WHERE id IN (990801,990802) "
            "AND deleted=0;"
        ) == "2"

        snapshot_query = (
            "SELECT id,HEX(name),type,status,HEX(COALESCE(remark,'')),deleted+0 "
            "FROM system_dict_type ORDER BY id;"
        )
        before = sql(snapshot_query)
        anon_status, anon = request("/system/dict-type/simple-list", None, None)
        assert anon_status == 200 and anon.get("code") == 401, (anon_status, anon)
        result["cases"]["anonymous"] = {"http": anon_status, "code": anon.get("code")}

        token_121 = login(*users[121], 121)
        status_121, response_121 = request("/system/dict-type/simple-list", token_121, 121)
        assert status_121 == 200 and response_121.get("code") == 0, (status_121, response_121)
        rows_121 = fixture_rows(response_121)
        assert (990801, "T4 Dict Type Enabled", "t4_dict_type_enabled") in rows_121
        assert (990802, "T4 Dict Type Disabled", "t4_dict_type_disabled") in rows_121
        result["cases"]["tenant_121_authenticated_shared_result"] = {
            "http": status_121,
            "code": response_121.get("code"),
            "fixture_rows": rows_121,
            "disabled_fixture_present": (990802, "T4 Dict Type Disabled", "t4_dict_type_disabled") in rows_121,
        }

        token_122 = login(*users[122], 122)
        status_122, response_122 = request("/system/dict-type/simple-list", token_122, 122)
        assert status_122 == 200 and response_122.get("code") == 0, (status_122, response_122)
        rows_122 = fixture_rows(response_122)
        assert rows_122 == rows_121, (rows_121, rows_122)
        result["cases"]["tenant_122_authenticated_same_shared_result"] = {
            "http": status_122,
            "code": response_122.get("code"),
            "fixture_rows": rows_122,
            "matches_tenant_121": rows_122 == rows_121,
        }

        after = sql(snapshot_query)
        assert after == before
        log_text = log_path.read_text(errors="replace")
        dict_sql_lines = [
            line for line in log_text.splitlines()
            if "system_dict_type" in line.lower() and "preparing:" in line.lower()
        ]
        assert dict_sql_lines, "dictionary type query SQL was not logged"
        no_tenant_predicate = all(
            not re.search(r"\btenant_id\b", line, re.IGNORECASE) for line in dict_sql_lines
        )
        assert no_tenant_predicate, dict_sql_lines
        result["sql_snapshot"] = {"before": before, "after": after, "unchanged": True}
        result["sql_log"] = {
            "dictionary_type_query_lines": dict_sql_lines[-8:],
            "tenant_predicate_absent": no_tenant_predicate,
        }
        result["fixture"] = {
            "enabled_dict_type_id": 990801,
            "disabled_dict_type_id": 990802,
            "tenant_121_login_user_id": 990803,
            "tenant_122_login_user_id": 990804,
            "password_hash_recorded": False,
        }
        result["changesets"] = EXPECTED_CHANGESETS
        result["conclusion"] = (
            "Anonymous dictionary-type simple-list access was rejected. Real users from tenants 121 "
            "and 122 received the same shared dictionary-type rows, including the disabled fixture, "
            "the table snapshot was unchanged, and the application SQL log showed no tenant predicate "
            "for the TenantIgnore dictionary table."
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
