#!/usr/bin/env python3
"""Verify Member external-auth failure boundaries in an isolated Demo runtime."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import tempfile
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "yuheng_p2_member_auth_20261122"
APP_PORT, MYSQL_PORT, REDIS_PORT = 48255, 13388, 16468
MYSQL, REDIS = "yh-p2-member-auth-mysql-20261122", "yh-p2-member-auth-redis-20261122"
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
OUT = Path(os.environ.get(
    "YH_MEMBER_EXTERNAL_AUTH_OUTPUT_DIR",
    ROOT / "docs/verification/2026-11-11-full-source-migration/p2-member-external-auth-20261122",
))
AUTH_CASES = {
    "sms_validation": True,
    "sms_send_configured_channel": True,
    "sms_invalid_code": True,
    "sms_login_success": True,
    "sms_login_creates_member_and_token": True,
    "social_validation": True,
    "social_invalid_code": True,
    "weixin_validation": True,
    "weixin_invalid_code": True,
    "failed_requests_no_member_or_binding": True,
    "failed_requests_no_oauth_token": True,
    "seed_passwords_unchanged": True,
    "cleanup": True,
}


def validate_probe_target(schema: str, app_port: int) -> bool:
    if not re.fullmatch(r"yuheng_p2_member_auth_[a-zA-Z0-9_]+", schema) or app_port != APP_PORT:
        raise ValueError("refusing shared schema or non-probe port")
    return True


def run(*args, input_text=None) -> str:
    result = subprocess.run(args, input=input_text, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def listening(port: int) -> bool:
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def sanitized_log_excerpt(log_file: Path) -> str:
    """Keep only stack frames and error labels, never provider payloads."""
    lines = []
    for line in log_file.read_text(errors="replace").splitlines():
        if any(marker in line for marker in ("defaultExceptionHandler", "ERROR", "Exception:", " at ")):
            line = re.sub(r"https?://\S+", "<redacted-url>", line)
            line = re.sub(r"(?i)(access[_-]?token|refresh[_-]?token|client[-_]?secret|apiSecret)=?[^ ,)]+", r"\1=<redacted>", line)
            lines.append(line)
    return "\n".join(lines[-80:])


class Probe:
    @staticmethod
    def installed_changesets(count: str) -> int:
        count = int(count)
        assert count >= 59, f"incomplete Liquibase installation: {count}"
        return count

    def __init__(self):
        self.events = []

    def call(self, method, path, body=None, expected=None, prefix="/app-api"):
        request = Request(
            f"http://127.0.0.1:{APP_PORT}{prefix}{path}",
            method=method,
            headers={"Content-Type": "application/json", "tenant-id": "1"},
            data=None if body is None else json.dumps(body).encode(),
        )
        try:
            response = urlopen(request, timeout=45)
        except HTTPError as error:
            response = error
        with response:
            payload = json.load(response)
            status = response.status
        event = {"method": method, "path": path, "http": status, "code": payload.get("code")}
        self.events.append(event)
        if expected is not None:
            assert status == 200 and payload.get("code") == expected, (event, payload.get("msg"))
        return payload


def mysql_exec(statement: str) -> str:
    return run(
        "docker", "exec", "-i", MYSQL, "sh", "-c",
        'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
        '--skip-column-names -D "$1"',
        "probe", SCHEMA, input_text=statement,
    )


def snapshot() -> dict[str, str]:
    return {
        "member_users": mysql_exec("SELECT COUNT(*) FROM member_user;"),
        "social_users": mysql_exec("SELECT COUNT(*) FROM system_social_user;"),
        "social_binds": mysql_exec("SELECT COUNT(*) FROM system_social_user_bind;"),
        "access_tokens": mysql_exec("SELECT COUNT(*) FROM system_oauth2_access_token;"),
        "refresh_tokens": mysql_exec("SELECT COUNT(*) FROM system_oauth2_refresh_token;"),
        "login_logs": mysql_exec("SELECT COUNT(*) FROM system_login_log;"),
        "sms_codes": mysql_exec("SELECT COUNT(*) FROM system_sms_code WHERE mobile='19900001100';"),
        "seed_password_digest": mysql_exec(
            "SELECT SHA2(GROUP_CONCAT(CONCAT(id, ':', password) ORDER BY id SEPARATOR '|'), 256) "
            "FROM system_users;"
        ),
    }


def assert_code(probe: Probe, method: str, path: str, body: dict, code: int) -> None:
    probe.call(method, path, body=body, expected=code)


def exercise(probe: Probe, result: dict, before: dict[str, str]) -> None:
    # Validation must run before any Core service or external provider call.
    assert_code(probe, "POST", "/member/auth/send-sms-code", {"mobile": "bad", "scene": 1}, 400)
    assert_code(probe, "POST", "/member/auth/validate-sms-code", {"mobile": "bad", "scene": 1, "code": "x"}, 400)
    assert_code(probe, "POST", "/member/auth/sms-login", {"mobile": "bad", "code": "x"}, 400)
    result["sms_validation"] = True

    assert_code(probe, "POST", "/member/auth/send-sms-code", {"mobile": "19900001100", "scene": 1}, 0)
    assert mysql_exec("SELECT COUNT(*) FROM system_sms_code WHERE mobile='19900001100' AND scene=1;") == "1"
    result["sms_send_configured_channel"] = True
    assert_code(probe, "POST", "/member/auth/validate-sms-code", {"mobile": "19900001100", "scene": 1, "code": "0000"}, 1002014000)
    assert_code(probe, "POST", "/member/auth/sms-login", {"mobile": "19900001100", "code": "0000"}, 1002014000)
    result["sms_invalid_code"] = True
    after_sms_failure = snapshot()
    for key in ("member_users", "social_users", "social_binds", "access_tokens", "refresh_tokens", "login_logs", "seed_password_digest"):
        assert after_sms_failure[key] == before[key], (key, before, after_sms_failure)
    assert int(after_sms_failure["sms_codes"]) == int(before["sms_codes"]) + 1, (before, after_sms_failure)

    # Use the value generated by the configured debug channel. Keep the token
    # response in memory only: the evidence must prove issuance without
    # persisting credentials.
    sms_code = mysql_exec(
        "SELECT code FROM system_sms_code "
        "WHERE mobile='19900001100' AND scene=1 AND used=0 "
        "ORDER BY id DESC LIMIT 1;"
    )
    assert sms_code, "configured SMS channel did not persist a usable code"
    success = probe.call(
        "POST", "/member/auth/sms-login",
        {"mobile": "19900001100", "code": sms_code}, expected=0,
    )
    data = success.get("data") or {}
    user_id = data.get("userId")
    access_token = data.get("accessToken")
    refresh_token = data.get("refreshToken")
    assert user_id and access_token and refresh_token, "SMS login response is incomplete"

    member = mysql_exec(
        "SELECT id,tenant_id FROM member_user "
        "WHERE mobile='19900001100' AND deleted=b'0' ORDER BY id DESC LIMIT 1;"
    ).split()
    assert len(member) == 2 and str(user_id) == member[0] and member[1] == "1", member
    after_success = snapshot()
    assert int(after_success["member_users"]) == int(before["member_users"]) + 1
    assert int(after_success["access_tokens"]) == int(before["access_tokens"]) + 1
    assert int(after_success["refresh_tokens"]) == int(before["refresh_tokens"]) + 1
    assert int(after_success["login_logs"]) == int(before["login_logs"]) + 1
    assert mysql_exec(
        "SELECT used FROM system_sms_code "
        "WHERE mobile='19900001100' AND scene=1 ORDER BY id DESC LIMIT 1;"
    ) == "1"
    result["sms_login_success"] = True
    result["sms_login_creates_member_and_token"] = True
    result["access_token_recorded"] = False
    result["refresh_token_recorded"] = False

    assert_code(probe, "POST", "/member/auth/social-login", {"type": None, "code": "", "state": ""}, 400)
    assert_code(probe, "GET", "/member/auth/social-auth-redirect?type=999&redirectUri=http%3A%2F%2F127.0.0.1%2Fcallback", None, 400)
    assert_code(probe, "GET", "/member/auth/social-auth-redirect?type=10&redirectUri=http%3A%2F%2F127.0.0.1%2Fcallback", None, 1002018000)
    result["social_validation"] = True
    assert_code(probe, "POST", "/member/auth/social-login", {"type": 10, "code": "invalid-p2-code", "state": "invalid-p2-state"}, 1002018000)
    result["social_invalid_code"] = True

    assert_code(probe, "POST", "/member/auth/weixin-mini-app-login", {"phoneCode": "", "loginCode": "", "state": ""}, 400)
    result["weixin_validation"] = True
    assert_code(probe, "POST", "/member/auth/weixin-mini-app-login", {"phoneCode": "invalid-p2-phone-code", "loginCode": "invalid-p2-login-code", "state": "invalid-p2-state"}, 1002018200)
    result["weixin_invalid_code"] = True

    after_failures = snapshot()
    for key in ("member_users", "social_users", "social_binds", "access_tokens", "refresh_tokens", "login_logs", "seed_password_digest"):
        assert after_failures[key] == after_success[key], (key, after_success, after_failures)
    assert int(after_failures["sms_codes"]) == int(after_success["sms_codes"]), (after_success, after_failures)
    result["failed_requests_no_member_or_binding"] = True
    result["failed_requests_no_oauth_token"] = True
    result["seed_passwords_unchanged"] = True


def stop(process):
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=35)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def main() -> None:
    validate_probe_target(SCHEMA, APP_PORT)
    assert JAR.is_file()
    assert not any(listening(port) for port in (MYSQL_PORT, REDIS_PORT, APP_PORT))
    names = run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
    assert MYSQL not in names and REDIS not in names
    db_password, redis_password = secrets.token_hex(20), secrets.token_hex(20)
    result = {
        "work_id": "YH-20261111-full-source-migration",
        "schema": SCHEMA,
        "jar_sha256": hashlib.sha256(JAR.read_bytes()).hexdigest(),
        "credentials_recorded": False,
        "cases": {},
    }
    app = None
    containers = []
    OUT.mkdir(parents=True, exist_ok=True)
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
                if mysql_exec("SELECT DATABASE();") == SCHEMA:
                    break
            except RuntimeError:
                pass
            assert time.monotonic() < deadline, "isolated MySQL readiness timeout"
            time.sleep(1)
        with tempfile.TemporaryDirectory(prefix="yuheng-p2-member-auth-") as temp:
            log_file = Path(temp) / "application.log"
            env = dict(os.environ, YUHENG_DB_HOST="127.0.0.1", YUHENG_DB_PORT=str(MYSQL_PORT),
                       YUHENG_DB_NAME=SCHEMA, YUHENG_DB_USERNAME="root", YUHENG_DB_PASSWORD=db_password,
                       YUHENG_REDIS_PASSWORD=redis_password)
            try:
                with log_file.open("w") as log:
                    app = subprocess.Popen(
                        ["java", "-jar", str(JAR), f"--server.port={APP_PORT}",
                         "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
                         f"--spring.data.redis.port={REDIS_PORT}", "--spring.data.redis.database=0",
                         "--spring.data.redis.password=" + redis_password, "--yudao.security.mock-enable=false",
                         "--spring.quartz.auto-startup=false", "--yudao.captcha.enable=false"],
                        cwd=ROOT, env=env, stdout=log, stderr=log)
                    deadline = time.monotonic() + 180
                    while not listening(APP_PORT):
                        assert app.poll() is None and time.monotonic() < deadline, "isolated Demo failed to start"
                        time.sleep(1)
                    deadline = time.monotonic() + 90
                    changesets = None
                    while changesets is None:
                        try:
                            changesets = Probe.installed_changesets(mysql_exec("SELECT COUNT(*) FROM DATABASECHANGELOG;"))
                        except AssertionError:
                            assert time.monotonic() < deadline, "Liquibase changeset count mismatch"
                            time.sleep(1)
                    result["changesets"] = changesets
                    probe = Probe()
                    before = snapshot()
                    exercise(probe, result["cases"], before)
                    result["cases"]["events"] = probe.events
            finally:
                # Keep only a redacted failure excerpt; provider logs can contain
                # access tokens even when the probe input contains no secrets.
                if log_file.exists():
                    excerpt = sanitized_log_excerpt(log_file)
                    if excerpt:
                        (OUT / "application-error-excerpt.txt").write_text(excerpt + "\n")
    finally:
        stop(app)
        for container in reversed(containers):
            run("docker", "rm", "-f", container)
        result["cases"]["cleanup"] = not any(listening(port) for port in (MYSQL_PORT, REDIS_PORT, APP_PORT))
        (OUT / "member-external-auth-runtime.json").write_text(json.dumps(result, indent=2) + "\n")
        if not result["cases"]["cleanup"]:
            raise RuntimeError("probe cleanup failed")


if __name__ == "__main__":
    main()
