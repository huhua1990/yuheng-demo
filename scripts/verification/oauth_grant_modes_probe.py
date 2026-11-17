#!/usr/bin/env python3
"""Verify OAuth2 password and authorization-code grants in isolation."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import socket
import subprocess
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "yuheng_t4_oauthgrants_20261120"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13356, 16436, 48191
MYSQL = "yh-oauthgrants-mysql-20261120"
REDIS = "yh-oauthgrants-redis-20261120"
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/service-write-audit-20261118/oauth-grant-modes-runtime.json"
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


def login(username: str, password: str) -> dict:
    request = Request(
        f"http://127.0.0.1:{APP_PORT}/admin-api/system/auth/login",
        data=json.dumps({"username": username, "password": password}).encode(),
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json", "tenant-id": "1"},
    )
    status, payload = read_json(request)
    assert status == 200 and payload.get("code") == 0, {"http": status, "payload": payload}
    return payload


def token(grant_type: str, client_id: str, client_secret: str,
          params: dict[str, str], expected_code: int | None = 0) -> dict:
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    request = Request(
        f"http://127.0.0.1:{APP_PORT}/admin-api/system/oauth2/token",
        data=urlencode({"grant_type": grant_type, **params}).encode(),
        method="POST",
        headers={
            "Authorization": "Basic " + credentials,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "tenant-id": "1",
        },
    )
    status, payload = read_json(request)
    event = {"http": status, "code": payload.get("code"), "grant_type": grant_type}
    if expected_code is not None:
        assert status == 200 and payload.get("code") == expected_code, event
    return {"payload": payload, "event": event}


def authorize(access_token: str, client_id: str, redirect_uri: str,
              state: str, auto_approve: bool = False) -> dict:
    scope = json.dumps({"user.read": True}, separators=(",", ":"))
    request = Request(
        f"http://127.0.0.1:{APP_PORT}/admin-api/system/oauth2/authorize",
        data=urlencode({
            "response_type": "code",
            "client_id": client_id,
            "scope": scope,
            "redirect_uri": redirect_uri,
            "auto_approve": str(auto_approve).lower(),
            "state": state,
        }).encode(),
        method="POST",
        headers={
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "tenant-id": "1",
        },
    )
    status, payload = read_json(request)
    assert status == 200 and payload.get("code") == 0, {"http": status, "payload": payload}
    redirect = payload["data"]
    parsed = urlparse(redirect)
    query = parse_qs(parsed.query)
    assert query.get("state") == [state], {"redirect": redirect, "state": state}
    assert len(query.get("code", [])) == 1 and query["code"][0]
    return {"payload": payload, "event": {"http": status, "code": 0}, "redirect": redirect,
            "code": query["code"][0]}


def active_counts(client_id: str) -> dict[str, int]:
    return {
        "access": int(sql(
            "SELECT COUNT(*) FROM system_oauth2_access_token "
            "WHERE client_id=" + sql_literal(client_id) + " AND deleted=0;"
        )),
        "refresh": int(sql(
            "SELECT COUNT(*) FROM system_oauth2_refresh_token "
            "WHERE client_id=" + sql_literal(client_id) + " AND deleted=0;"
        )),
        "code": int(sql(
            "SELECT COUNT(*) FROM system_oauth2_code "
            "WHERE client_id=" + sql_literal(client_id) + " AND deleted=0;"
        )),
    }


def token_values(payload: dict) -> tuple[str, str]:
    data = payload["payload"]["data"]
    assert data["token_type"].lower() == "bearer"
    assert data["access_token"] and data["refresh_token"]
    return data["access_token"], data["refresh_token"]


def main() -> None:
    assert JAR.is_file()
    assert not any(listening(port) for port in (MYSQL_PORT, REDIS_PORT, APP_PORT))
    existing = run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
    assert MYSQL not in existing and REDIS not in existing

    db_password = secrets.token_hex(20)
    redis_password = secrets.token_hex(20)
    suffix = secrets.token_hex(6)
    username = "t4oauth" + suffix
    password = secrets.token_urlsafe(12)[:16]
    client_id = "t4-grants-" + suffix
    client_secret = secrets.token_urlsafe(18)
    password_hash = subprocess.run(
        ["htpasswd", "-bnBC", "4", username, password],
        capture_output=True, text=True, check=True,
    ).stdout.strip().split(":", 1)[1]
    redirect_uri = "http://127.0.0.1:48191/oauth/callback"
    app = None
    owned: list[str] = []
    log_path = Path("/tmp/yh-oauthgrants-runtime-20261120.log")
    result = {
        "work_id": "YH-20261111-full-source-migration",
        "schema": SCHEMA,
        "jar_sha256": hashlib.sha256(JAR.read_bytes()).hexdigest(),
        "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT, "app": APP_PORT},
        "cases": {},
    }

    try:
        run("docker", "run", "-d", "--name", MYSQL,
            "-e", "MYSQL_ROOT_PASSWORD=" + db_password,
            "-e", "MYSQL_DATABASE=" + SCHEMA,
            "-p", f"127.0.0.1:{MYSQL_PORT}:3306", "mysql:8.0.33")
        owned.append(MYSQL)
        run("docker", "run", "-d", "--name", REDIS,
            "-p", f"127.0.0.1:{REDIS_PORT}:6379", "redis:7.2.17",
            "redis-server", "--requirepass", redis_password)
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
            ["java", "-jar", str(JAR), f"--server.port={APP_PORT}",
             "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
             f"--spring.data.redis.port={REDIS_PORT}", "--spring.data.redis.database=0",
             "--spring.data.redis.password=" + redis_password,
             "--yudao.security.mock-enable=false", "--spring.quartz.auto-startup=false",
             "--yudao.captcha.enable=false", "--logging.level.com.yuheng=INFO"],
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

        user_values = (
            "(990202," + sql_literal(username) + "," + sql_literal(password_hash)
            + ",'T4 OAuth grant user',NULL,'[]',0,b'0',1)"
        )
        sql(
            "INSERT INTO system_users "
            "(id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) "
            "VALUES " + user_values + ";"
        )
        client_values = (
            "(990203," + sql_literal(client_id) + "," + sql_literal(client_secret)
            + ",'T4 OAuth grant client','',NULL,0,180,600,"
            + sql_literal(json.dumps([redirect_uri], separators=(",", ":"))) + ","
            + sql_literal(json.dumps(["password", "authorization_code", "refresh_token"], separators=(",", ":"))) + ","
            + sql_literal(json.dumps(["user.read"], separators=(",", ":"))) + ","
            + "'[]','[]','[]','{}','probe',CURRENT_TIMESTAMP,'probe',CURRENT_TIMESTAMP,b'0')"
        )
        sql(
            "INSERT INTO system_oauth2_client "
            "(id,client_id,secret,name,logo,description,status,"
            "access_token_validity_seconds,refresh_token_validity_seconds,redirect_uris,"
            "authorized_grant_types,scopes,auto_approve_scopes,authorities,resource_ids,"
            "additional_information,creator,create_time,updater,update_time,deleted) "
            "VALUES " + client_values + ";"
        )
        assert sql("SELECT COUNT(*) FROM system_users WHERE id=990202 AND password<>'';") == "1"
        assert sql("SELECT COUNT(*) FROM system_oauth2_client WHERE client_id="
                   + sql_literal(client_id) + " AND deleted=0;") == "1"

        login_payload = login(username, password)
        user_access = login_payload["data"]["accessToken"]
        password_result = token("password", client_id, client_secret,
                                {"username": username, "password": password, "scope": "user.read"})
        password_access, password_refresh = token_values(password_result)
        assert active_counts(client_id) == {"access": 1, "refresh": 1, "code": 0}
        result["cases"]["password_grant"] = {
            **password_result["event"], "user_id": 990202,
            "token_user_id": int(sql("SELECT user_id FROM system_oauth2_access_token "
                                      "WHERE access_token=" + sql_literal(password_access) + ";")),
            "active_rows": active_counts(client_id),
        }

        state = "state-" + secrets.token_urlsafe(10)
        auth = authorize(user_access, client_id, redirect_uri, state)
        assert active_counts(client_id) == {"access": 1, "refresh": 1, "code": 1}
        result["cases"]["authorization_request"] = {
            **auth["event"], "state_round_trip": True, "code_row_created": True,
        }

        wrong_redirect_result = token(
            "authorization_code", client_id, client_secret,
            {"code": auth["code"], "redirect_uri": redirect_uri + "/wrong", "state": state}, None,
        )
        assert wrong_redirect_result["event"]["code"] != 0
        wrong_redirect_remaining = int(sql("SELECT COUNT(*) FROM system_oauth2_code WHERE code="
                                          + sql_literal(auth["code"]) + " AND deleted=0;"))
        assert wrong_redirect_remaining == 1, wrong_redirect_remaining
        result["cases"]["wrong_redirect_uri"] = {
            **wrong_redirect_result["event"], "code_row_remaining": wrong_redirect_remaining,
            "code_rejected": True,
        }

        state_two = "state-" + secrets.token_urlsafe(10)
        auth_two = authorize(user_access, client_id, redirect_uri, state_two)
        wrong_state_result = token(
            "authorization_code", client_id, client_secret,
            {"code": auth_two["code"], "redirect_uri": redirect_uri, "state": state_two + "-wrong"}, None,
        )
        assert wrong_state_result["event"]["code"] != 0
        wrong_state_remaining = int(sql("SELECT COUNT(*) FROM system_oauth2_code WHERE code="
                                       + sql_literal(auth_two["code"]) + " AND deleted=0;"))
        assert wrong_state_remaining == 1, wrong_state_remaining
        result["cases"]["wrong_state"] = {
            **wrong_state_result["event"], "code_row_remaining": wrong_state_remaining,
            "code_rejected": True,
        }

        state_three = "state-" + secrets.token_urlsafe(10)
        auth_three = authorize(user_access, client_id, redirect_uri, state_three)
        correct = token(
            "authorization_code", client_id, client_secret,
            {"code": auth_three["code"], "redirect_uri": redirect_uri, "state": state_three},
        )
        auth_access, auth_refresh = token_values(correct)
        assert auth_access and auth_refresh
        assert active_counts(client_id) == {"access": 2, "refresh": 2, "code": 2}
        result["cases"]["authorization_code_exchange"] = {
            **correct["event"], "user_id": 990202,
            "token_user_id": int(sql("SELECT user_id FROM system_oauth2_access_token "
                                      "WHERE access_token=" + sql_literal(auth_access) + ";")),
            "active_rows": active_counts(client_id),
        }

        repeated = token(
            "authorization_code", client_id, client_secret,
            {"code": auth_three["code"], "redirect_uri": redirect_uri, "state": state_three}, None,
        )
        assert repeated["event"]["code"] != 0
        result["cases"]["authorization_code_replay"] = {
            **repeated["event"], "rejected": True,
        }

        result["fixture"] = {"user_id": 990202, "client_id": client_id,
                             "password_hash_recorded": False, "secret_recorded": False}
        result["changesets"] = EXPECTED_CHANGESETS
        result["conclusion"] = (
            "Password grant and authorization-code issuance/exchange were exercised with a disposable user. "
            "The authorization code was rejected on replay; redirect/state rejection outcomes and whether the "
            "code remained available after rejection are recorded explicitly."
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
            "ports_listening": {str(port): listening(port) for port in (MYSQL_PORT, REDIS_PORT, APP_PORT)},
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        assert result["cleanup"]["containers_absent"] and not any(result["cleanup"]["ports_listening"].values())


if __name__ == "__main__":
    main()
