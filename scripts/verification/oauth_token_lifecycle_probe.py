#!/usr/bin/env python3
"""Verify the isolated OAuth2 client-credentials token lifecycle."""

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
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "yuheng_t4_oauthtoken_20261120"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13349, 16429, 48184
MYSQL = "yh-oauthtoken-mysql-20261120"
REDIS = "yh-oauthtoken-redis-20261120"
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/service-write-audit-20261118/oauth-token-lifecycle-runtime.json"


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


def redis_exists(password: str, key: str) -> bool:
    output = run(
        "docker", "exec", REDIS, "redis-cli", "-a", password,
        "--no-auth-warning", "EXISTS", key,
    )
    return output.strip() == "1"


def call_token(grant_type: str, client_id: str, secret: str,
               params: dict[str, str], expected_code: int | None = 0) -> dict:
    credentials = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
    form = {"grant_type": grant_type, **params}
    request = Request(
        f"http://127.0.0.1:{APP_PORT}/admin-api/system/oauth2/token",
        data=urlencode(form).encode(),
        method="POST",
        headers={
            "Authorization": "Basic " + credentials,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "tenant-id": "1",
        },
    )
    try:
        response = urlopen(request, timeout=25)
    except HTTPError as error:
        response = error
    with response:
        payload = json.load(response)
    event = {"http": response.status, "code": payload.get("code"), "grant_type": grant_type}
    if expected_code is not None:
        assert response.status == 200 and payload.get("code") == expected_code, event
    return {"payload": payload, "event": event}


def check_token(access_token: str, client_id: str, secret: str) -> dict:
    credentials = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
    request = Request(
        f"http://127.0.0.1:{APP_PORT}/admin-api/system/oauth2/check-token?"
        + urlencode({"token": access_token}),
        data=b"",
        method="POST",
        headers={
            "Authorization": "Basic " + credentials,
            "Accept": "application/json",
            "tenant-id": "1",
        },
    )
    try:
        response = urlopen(request, timeout=25)
    except HTTPError as error:
        response = error
    with response:
        payload = json.load(response)
    return {"payload": payload, "event": {"http": response.status, "code": payload.get("code")}}


def revoke_token(access_token: str, client_id: str, secret: str) -> dict:
    credentials = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
    request = Request(
        f"http://127.0.0.1:{APP_PORT}/admin-api/system/oauth2/token?"
        + urlencode({"token": access_token}),
        method="DELETE",
        headers={
            "Authorization": "Basic " + credentials,
            "Accept": "application/json",
            "tenant-id": "1",
        },
    )
    try:
        response = urlopen(request, timeout=25)
    except HTTPError as error:
        response = error
    with response:
        payload = json.load(response)
    assert response.status == 200 and payload.get("code") == 0, payload
    return {"payload": payload, "event": {"http": response.status, "code": payload.get("code")}}


def token_values(payload: dict) -> tuple[str, str]:
    data = payload["payload"]["data"]
    assert data["token_type"].lower() == "bearer"
    assert isinstance(data["access_token"], str) and data["access_token"]
    assert isinstance(data["refresh_token"], str) and data["refresh_token"]
    return data["access_token"], data["refresh_token"]


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
    }


def main() -> None:
    assert JAR.is_file()
    assert not any(listening(port) for port in (MYSQL_PORT, REDIS_PORT, APP_PORT))
    existing = run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
    assert MYSQL not in existing and REDIS not in existing

    db_password = secrets.token_hex(20)
    redis_password = secrets.token_hex(20)
    suffix = secrets.token_hex(6)
    client_id = "t4-lifecycle-" + suffix
    client_secret = secrets.token_urlsafe(18)
    app = None
    owned: list[str] = []
    log_path = Path("/tmp/yh-oauthtoken-runtime-20261120.log")
    result = {
        "work_id": "YH-20261111-full-source-migration",
        "schema": SCHEMA,
        "jar_sha256": hashlib.sha256(JAR.read_bytes()).hexdigest(),
        "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT, "app": APP_PORT},
        "client_id_recorded": True,
        "secret_recorded": False,
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
                if int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")) == 54:
                    break
            except RuntimeError:
                pass
            assert time.monotonic() < deadline, "Liquibase readiness timeout"
            time.sleep(1)

        client_values = (
            "(990201," + sql_literal(client_id) + "," + sql_literal(client_secret)
            + ",'T4 OAuth lifecycle probe','',NULL,0,180,600,'[]',"
            + "'[\"client_credentials\",\"refresh_token\"]',"
            + "'[\"user.read\"]','[]','[]','[]','{}','probe',CURRENT_TIMESTAMP,"
            + "'probe',CURRENT_TIMESTAMP,b'0')"
        )
        sql(
            "INSERT INTO system_oauth2_client "
            "(id,client_id,secret,name,logo,description,status,"
            "access_token_validity_seconds,refresh_token_validity_seconds,redirect_uris,"
            "authorized_grant_types,scopes,auto_approve_scopes,authorities,resource_ids,"
            "additional_information,creator,create_time,updater,update_time,deleted) "
            "VALUES " + client_values + ";"
        )
        assert sql(
            "SELECT COUNT(*) FROM system_oauth2_client WHERE client_id="
            + sql_literal(client_id) + " AND deleted=0;"
        ) == "1"

        wrong = call_token(
            "client_credentials", client_id, "wrong-secret", {"scope": "user.read"}, None
        )
        assert wrong["event"]["http"] == 200 and wrong["event"]["code"] != 0, wrong["event"]
        result["cases"]["wrong_client_secret"] = wrong["event"]

        first = call_token(
            "client_credentials", client_id, client_secret, {"scope": "user.read"}
        )
        access_one, refresh_token = token_values(first)
        assert active_counts(client_id) == {"access": 1, "refresh": 1}
        assert redis_exists(redis_password, "oauth2_access_token:" + access_one)
        checked_one = check_token(access_one, client_id, client_secret)
        assert checked_one["event"]["http"] == 200 and checked_one["event"]["code"] == 0
        assert checked_one["payload"]["data"]["client_id"] == client_id
        result["cases"]["client_credentials"] = {
            **first["event"], "active_rows": active_counts(client_id),
            "redis_access_key": True, "check_token": checked_one["event"],
        }

        refreshed = call_token(
            "refresh_token", client_id, client_secret, {"refresh_token": refresh_token}
        )
        access_two, refresh_token_two = token_values(refreshed)
        assert refresh_token_two == refresh_token
        assert access_two != access_one
        assert active_counts(client_id) == {"access": 1, "refresh": 1}
        assert not redis_exists(redis_password, "oauth2_access_token:" + access_one)
        assert redis_exists(redis_password, "oauth2_access_token:" + access_two)
        old_check = check_token(access_one, client_id, client_secret)
        new_check = check_token(access_two, client_id, client_secret)
        assert old_check["event"]["code"] != 0
        assert new_check["event"]["code"] == 0
        result["cases"]["refresh_token"] = {
            **refreshed["event"], "same_refresh_token": True,
            "old_access_rejected": old_check["event"],
            "new_access_accepted": new_check["event"],
            "active_rows": active_counts(client_id),
            "old_redis_access_key": False, "new_redis_access_key": True,
        }

        revoked = revoke_token(access_two, client_id, client_secret)
        assert active_counts(client_id) == {"access": 0, "refresh": 0}
        assert not redis_exists(redis_password, "oauth2_access_token:" + access_two)
        revoked_check = check_token(access_two, client_id, client_secret)
        assert revoked_check["event"]["code"] != 0
        result["cases"]["revoke"] = {
            **revoked["event"], "active_rows": active_counts(client_id),
            "redis_access_key": False, "post_revoke_check": revoked_check["event"],
        }
        result["conclusion"] = (
            "An isolated client-credentials token was issued and checked, refreshed with "
            "the same refresh token, then revoked; old and revoked access tokens were "
            "rejected and MySQL/Redis active state matched each lifecycle transition."
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
            "ports_listening": {
                str(port): listening(port) for port in (MYSQL_PORT, REDIS_PORT, APP_PORT)
            },
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        assert result["cleanup"]["containers_absent"] and not any(result["cleanup"]["ports_listening"].values())


if __name__ == "__main__":
    main()
