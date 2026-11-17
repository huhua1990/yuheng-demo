#!/usr/bin/env python3
"""Verify that one authorization code can be consumed only once under concurrency."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import secrets
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
probe = importlib.import_module("oauth_grant_modes_probe")

# Keep this run independent from the single-request grant evidence.
probe.SCHEMA = "yuheng_t4_oauthconcurrency_20261120"
probe.MYSQL_PORT = 13357
probe.REDIS_PORT = 16437
probe.APP_PORT = 48194
probe.MYSQL = "yh-oauthconcurrency-mysql-20261120"
probe.REDIS = "yh-oauthconcurrency-redis-20261120"
probe.EXPECTED_CHANGESETS = 56

JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
OUT = ROOT / (
    "docs/verification/2026-11-11-full-source-migration/"
    "service-write-audit-20261118/oauth-grant-concurrency-runtime.json"
)


def listening(port: int) -> bool:
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def main() -> None:
    assert JAR.is_file()
    ports = (probe.MYSQL_PORT, probe.REDIS_PORT, probe.APP_PORT)
    assert not any(listening(port) for port in ports)
    existing = probe.run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
    assert probe.MYSQL not in existing and probe.REDIS not in existing

    db_password = secrets.token_hex(20)
    redis_password = secrets.token_hex(20)
    suffix = secrets.token_hex(6)
    username = "t4oauthc" + suffix
    password = secrets.token_urlsafe(12)[:16]
    client_id = "t4-grant-concurrency-" + suffix
    client_secret = secrets.token_urlsafe(18)
    redirect_uri = f"http://127.0.0.1:{probe.APP_PORT}/oauth/callback"
    password_hash = subprocess.run(
        ["htpasswd", "-bnBC", "4", username, password],
        capture_output=True, text=True, check=True,
    ).stdout.strip().split(":", 1)[1]
    app = None
    log_path = Path("/tmp/yh-oauthconcurrency-runtime-20261120.log")
    owned: list[str] = []
    result = {
        "work_id": "YH-20261111-full-source-migration",
        "schema": probe.SCHEMA,
        "jar_sha256": hashlib.sha256(JAR.read_bytes()).hexdigest(),
        "ports": {"mysql": probe.MYSQL_PORT, "redis": probe.REDIS_PORT, "app": probe.APP_PORT},
        "concurrency": {"requests": 8},
    }

    try:
        probe.run(
            "docker", "run", "-d", "--name", probe.MYSQL,
            "-e", "MYSQL_ROOT_PASSWORD=" + db_password,
            "-e", "MYSQL_DATABASE=" + probe.SCHEMA,
            "-p", f"127.0.0.1:{probe.MYSQL_PORT}:3306", "mysql:8.0.33",
        )
        owned.append(probe.MYSQL)
        probe.run(
            "docker", "run", "-d", "--name", probe.REDIS,
            "-p", f"127.0.0.1:{probe.REDIS_PORT}:6379", "redis:7.2.17",
            "redis-server", "--requirepass", redis_password,
        )
        owned.append(probe.REDIS)

        deadline = time.monotonic() + 100
        while True:
            try:
                assert probe.sql("SELECT DATABASE();") == probe.SCHEMA
                break
            except (RuntimeError, AssertionError):
                assert time.monotonic() < deadline, "isolated MySQL readiness timeout"
                time.sleep(1)

        env = dict(
            os.environ,
            YUHENG_DB_HOST="127.0.0.1",
            YUHENG_DB_PORT=str(probe.MYSQL_PORT),
            YUHENG_DB_NAME=probe.SCHEMA,
            YUHENG_DB_USERNAME="root",
            YUHENG_DB_PASSWORD=db_password,
            YUHENG_REDIS_PASSWORD=redis_password,
        )
        log = log_path.open("w")
        app = subprocess.Popen(
            [
                "java", "-jar", str(JAR), f"--server.port={probe.APP_PORT}",
                "--spring.profiles.active=local",
                "--spring.data.redis.host=127.0.0.1",
                f"--spring.data.redis.port={probe.REDIS_PORT}",
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
        while not listening(probe.APP_PORT):
            assert app.poll() is None, "isolated backend exited before listening"
            assert time.monotonic() < deadline, "isolated backend readiness timeout"
            time.sleep(1)
        deadline = time.monotonic() + 30
        while True:
            try:
                if int(probe.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")) == probe.EXPECTED_CHANGESETS:
                    break
            except RuntimeError:
                pass
            assert time.monotonic() < deadline, "Liquibase readiness timeout"
            time.sleep(1)

        probe.sql(
            "INSERT INTO system_users "
            "(id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) VALUES "
            "(990302," + probe.sql_literal(username) + "," + probe.sql_literal(password_hash) +
            ",'T4 OAuth concurrency user',NULL,'[]',0,b'0',1);"
        )
        client_values = (
            "(990303," + probe.sql_literal(client_id) + "," + probe.sql_literal(client_secret) +
            ",'T4 OAuth concurrency client','',NULL,0,180,600," +
            probe.sql_literal(json.dumps([redirect_uri], separators=(",", ":"))) + "," +
            probe.sql_literal(json.dumps(["authorization_code"], separators=(",", ":"))) + "," +
            probe.sql_literal(json.dumps(["user.read"], separators=(",", ":"))) +
            ",'[]','[]','[]','{}','probe',CURRENT_TIMESTAMP,'probe',CURRENT_TIMESTAMP,b'0')"
        )
        probe.sql(
            "INSERT INTO system_oauth2_client "
            "(id,client_id,secret,name,logo,description,status,"
            "access_token_validity_seconds,refresh_token_validity_seconds,redirect_uris,"
            "authorized_grant_types,scopes,auto_approve_scopes,authorities,resource_ids,"
            "additional_information,creator,create_time,updater,update_time,deleted) VALUES "
            + client_values + ";"
        )

        login_payload = probe.login(username, password)
        user_access = login_payload["data"]["accessToken"]
        state = "state-" + secrets.token_urlsafe(10)
        auth = probe.authorize(user_access, client_id, redirect_uri, state)
        assert probe.active_counts(client_id) == {"access": 0, "refresh": 0, "code": 1}

        def exchange() -> dict:
            return probe.token(
                "authorization_code", client_id, client_secret,
                {"code": auth["code"], "redirect_uri": redirect_uri, "state": state}, None,
            )["event"]

        events: list[dict] = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(exchange) for _ in range(8)]
            for future in as_completed(futures):
                events.append(future.result())
        events.sort(key=lambda event: (event.get("code") != 0, event.get("code", -1)))
        success_count = sum(event.get("code") == 0 for event in events)
        failure_count = len(events) - success_count
        counts_after = probe.active_counts(client_id)
        code_remaining = int(probe.sql(
            "SELECT COUNT(*) FROM system_oauth2_code WHERE code=" +
            probe.sql_literal(auth["code"]) + " AND deleted=0;"
        ))
        assert success_count == 1, events
        assert failure_count == 7, events
        assert counts_after == {"access": 1, "refresh": 1, "code": 0}, counts_after
        assert code_remaining == 0, code_remaining
        result["concurrency"].update({
            "events": events,
            "success_count": success_count,
            "failure_count": failure_count,
            "active_rows_after": counts_after,
            "code_row_remaining": code_remaining,
            "single_consumer_assertion": True,
        })

        # A rejected binding must leave a newly issued code available and create no token.
        second_state = "state-" + secrets.token_urlsafe(10)
        second = probe.authorize(user_access, client_id, redirect_uri, second_state)
        before = probe.active_counts(client_id)
        rejected = probe.token(
            "authorization_code", client_id, client_secret,
            {"code": second["code"], "redirect_uri": redirect_uri + "/wrong", "state": second_state}, None,
        )["event"]
        after = probe.active_counts(client_id)
        second_remaining = int(probe.sql(
            "SELECT COUNT(*) FROM system_oauth2_code WHERE code=" +
            probe.sql_literal(second["code"]) + " AND deleted=0;"
        ))
        assert rejected["code"] != 0
        assert before == after == {"access": 1, "refresh": 1, "code": 1}
        assert second_remaining == 1
        result["rejected_binding"] = {
            "event": rejected,
            "active_rows_before": before,
            "active_rows_after": after,
            "code_row_remaining": second_remaining,
            "token_creation_blocked": True,
        }
        result["changesets"] = probe.EXPECTED_CHANGESETS
        result["fixture"] = {"user_id": 990302, "client_id": client_id,
                             "password_hash_recorded": False, "secret_recorded": False}
        result["conclusion"] = (
            "Eight concurrent exchanges of one authorization code produced exactly one token pair; "
            "the other seven requests were rejected and no duplicate active token rows were created. "
            "A wrong redirect binding rejected a second code without consuming it or creating tokens."
        )
        print(json.dumps(result["concurrency"], ensure_ascii=False, indent=2))
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
                name not in probe.run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
                for name in (probe.MYSQL, probe.REDIS)
            ),
            "ports_listening": {str(port): listening(port) for port in ports},
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        assert result["cleanup"]["containers_absent"] and not any(result["cleanup"]["ports_listening"].values())


if __name__ == "__main__":
    main()
