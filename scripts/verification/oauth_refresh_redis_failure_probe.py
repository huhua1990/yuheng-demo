#!/usr/bin/env python3
"""Verify refresh-token behavior when one Redis access-token DEL fails.

The probe uses a disposable MySQL/Redis pair and a small RESP proxy. The proxy
passes Redis traffic through unchanged until armed, then returns one error for
the next access-token DEL without forwarding it. This avoids changing ACLs on
an already pooled Redis connection.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import select
import socket
import subprocess
import threading
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "yuheng_t4_oauthrefreshredisfail_20261120"
MYSQL_PORT, REDIS_PORT, PROXY_PORT, APP_PORT = 13363, 16443, 16444, 48200
MYSQL = "yh-oauthrefreshfail-mysql-20261120"
REDIS = "yh-oauthrefreshfail-redis-20261120"
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/service-write-audit-20261118/oauth-refresh-redis-failure.json"


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
    return run(
        "docker", "exec", REDIS, "redis-cli", "-a", password,
        "--no-auth-warning", "EXISTS", key,
    ) == "1"


def parse_resp_command(buffer: bytearray) -> tuple[int, list[bytes]] | None:
    """Parse one RESP array of bulk strings, returning end offset and args."""
    if not buffer.startswith(b"*"):
        return None
    line_end = buffer.find(b"\r\n")
    if line_end < 0:
        return None
    try:
        count = int(buffer[1:line_end])
    except ValueError:
        return None
    pos = line_end + 2
    args: list[bytes] = []
    for _ in range(count):
        if pos >= len(buffer) or buffer[pos:pos + 1] != b"$":
            return None
        length_end = buffer.find(b"\r\n", pos)
        if length_end < 0:
            return None
        try:
            length = int(buffer[pos + 1:length_end])
        except ValueError:
            return None
        value_start = length_end + 2
        value_end = value_start + length
        if len(buffer) < value_end + 2:
            return None
        if buffer[value_end:value_end + 2] != b"\r\n":
            return None
        args.append(bytes(buffer[value_start:value_end]))
        pos = value_end + 2
    return pos, args


class RedisFailureProxy:
    def __init__(self, listen_port: int, target_port: int) -> None:
        self.listen_port = listen_port
        self.target_port = target_port
        self.server: socket.socket | None = None
        self.thread: threading.Thread | None = None
        self.armed = False
        self.injected = False
        self.injected_command: list[str] | None = None
        self.stop_event = threading.Event()

    def start(self) -> None:
        self.server = socket.socket()
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(("127.0.0.1", self.listen_port))
        self.server.listen(16)
        self.server.settimeout(0.25)
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def arm(self) -> None:
        self.armed = True

    def close(self) -> None:
        self.stop_event.set()
        if self.server is not None:
            self.server.close()
        if self.thread is not None:
            self.thread.join(timeout=3)

    def _serve(self) -> None:
        assert self.server is not None
        while not self.stop_event.is_set():
            try:
                client, _ = self.server.accept()
            except (socket.timeout, OSError):
                continue
            threading.Thread(target=self._connection, args=(client,), daemon=True).start()

    def _connection(self, client: socket.socket) -> None:
        upstream: socket.socket | None = None
        try:
            upstream = socket.create_connection(("127.0.0.1", self.target_port), timeout=10)
            client.setblocking(False)
            upstream.setblocking(False)
            client_buffer = bytearray()
            sockets = [client, upstream]
            while not self.stop_event.is_set():
                readable, _, exceptional = select.select(sockets, [], sockets, 0.25)
                if exceptional:
                    break
                for source in readable:
                    data = source.recv(65536)
                    if not data:
                        return
                    if source is upstream:
                        client.sendall(data)
                        continue
                    client_buffer.extend(data)
                    while True:
                        parsed = parse_resp_command(client_buffer)
                        if parsed is None:
                            break
                        end, args = parsed
                        command = bytes(args[0]).upper() if args else b""
                        is_access_delete = command == b"DEL" and any(
                            key.startswith(b"oauth2_access_token:") for key in args[1:]
                        )
                        if self.armed and not self.injected and is_access_delete:
                            self.injected = True
                            self.injected_command = [arg.decode("utf-8", "replace") for arg in args]
                            client.sendall(b"-ERR T4_REFRESH_REDIS_DELETE_INJECTED\r\n")
                        else:
                            upstream.sendall(client_buffer[:end])
                        del client_buffer[:end]
        except (ConnectionError, OSError):
            return
        finally:
            client.close()
            if upstream is not None:
                upstream.close()


def read_json(request: Request) -> tuple[int, dict]:
    try:
        response = urlopen(request, timeout=30)
    except HTTPError as error:
        response = error
    with response:
        return response.status, json.load(response)


def call_token(grant_type: str, client_id: str, secret: str,
               params: dict[str, str], expected_code: int | None = 0) -> dict:
    credentials = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
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


def check_token(token: str, client_id: str, secret: str) -> dict:
    credentials = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
    request = Request(
        f"http://127.0.0.1:{APP_PORT}/admin-api/system/oauth2/check-token?"
        + urlencode({"token": token}),
        data=b"",
        method="POST",
        headers={
            "Authorization": "Basic " + credentials,
            "Accept": "application/json",
            "tenant-id": "1",
        },
    )
    status, payload = read_json(request)
    assert status == 200 and payload.get("code") == 0, {"status": status, "payload": payload}
    return payload


def token_values(payload: dict) -> tuple[str, str]:
    data = payload["payload"]["data"]
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
    all_ports = (MYSQL_PORT, REDIS_PORT, PROXY_PORT, APP_PORT)
    assert not any(listening(port) for port in all_ports)
    existing = run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
    assert MYSQL not in existing and REDIS not in existing

    db_password = secrets.token_hex(20)
    redis_password = secrets.token_hex(20)
    suffix = secrets.token_hex(6)
    client_id = "t4-refresh-fail-" + suffix
    client_secret = secrets.token_urlsafe(18)
    app = None
    proxy = RedisFailureProxy(PROXY_PORT, REDIS_PORT)
    owned: list[str] = []
    log_path = Path("/tmp/yh-oauthrefreshfail-runtime-20261120.log")
    result = {
        "work_id": "YH-20261111-full-source-migration",
        "schema": SCHEMA,
        "jar_sha256": hashlib.sha256(JAR.read_bytes()).hexdigest(),
        "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT, "proxy": PROXY_PORT, "app": APP_PORT},
        "client_id_recorded": True,
        "secret_recorded": False,
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
        proxy.start()

        deadline = time.monotonic() + 100
        while True:
            try:
                assert sql("SELECT DATABASE();") == SCHEMA
                break
            except (RuntimeError, AssertionError):
                assert time.monotonic() < deadline, "isolated MySQL readiness timeout"
                time.sleep(1)

        env = dict(os.environ,
                   YUHENG_DB_HOST="127.0.0.1", YUHENG_DB_PORT=str(MYSQL_PORT),
                   YUHENG_DB_NAME=SCHEMA, YUHENG_DB_USERNAME="root",
                   YUHENG_DB_PASSWORD=db_password, YUHENG_REDIS_PASSWORD=redis_password)
        log = log_path.open("w")
        app = subprocess.Popen(
            ["java", "-jar", str(JAR), f"--server.port={APP_PORT}",
             "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
             f"--spring.data.redis.port={PROXY_PORT}", "--spring.data.redis.database=0",
             "--spring.data.redis.password=" + redis_password,
             "--yudao.security.mock-enable=false", "--spring.quartz.auto-startup=false",
             "--yudao.captcha.enable=false", "--logging.level.com.yuheng=INFO"],
            cwd=ROOT, env=env, stdout=log, stderr=log)
        owned.append("process")
        deadline = time.monotonic() + 150
        while not listening(APP_PORT):
            assert app.poll() is None, "isolated backend exited before listening"
            assert time.monotonic() < deadline, "isolated backend readiness timeout"
            time.sleep(1)
        deadline = time.monotonic() + 45
        while True:
            try:
                if int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")) >= 56:
                    break
            except RuntimeError:
                pass
            assert time.monotonic() < deadline, "Liquibase readiness timeout"
            time.sleep(1)

        client_values = (
            "(990401," + sql_literal(client_id) + "," + sql_literal(client_secret)
            + ",'T4 refresh Redis failure','',NULL,0,180,600,'[]',"
            + "'[\"client_credentials\",\"refresh_token\"]','[\"user.read\"]','[]','[]','[]','{}','probe',CURRENT_TIMESTAMP,"
            + "'probe',CURRENT_TIMESTAMP,b'0')"
        )
        sql(
            "INSERT INTO system_oauth2_client "
            "(id,client_id,secret,name,logo,description,status,access_token_validity_seconds,"
            "refresh_token_validity_seconds,redirect_uris,authorized_grant_types,scopes,"
            "auto_approve_scopes,authorities,resource_ids,additional_information,creator,"
            "create_time,updater,update_time,deleted) VALUES " + client_values + ";")

        issued = call_token("client_credentials", client_id, client_secret, {"scope": "user.read"})
        access_token, refresh_token = token_values(issued)
        assert active_counts(client_id) == {"access": 1, "refresh": 1}
        check_token(access_token, client_id, client_secret)
        check_token(refresh_token, client_id, client_secret)
        access_key = "oauth2_access_token:" + access_token
        refresh_key = "oauth2_access_token:" + refresh_token
        before = {
            "active_rows": active_counts(client_id),
            "access_key": redis_exists(redis_password, access_key),
            "refresh_key": redis_exists(redis_password, refresh_key),
        }
        assert before == {"active_rows": {"access": 1, "refresh": 1},
                          "access_key": True, "refresh_key": True}

        proxy.arm()
        failed = call_token("refresh_token", client_id, client_secret,
                            {"refresh_token": refresh_token}, expected_code=None)
        after = {
            "active_rows": active_counts(client_id),
            "access_key": redis_exists(redis_password, access_key),
            "refresh_key": redis_exists(redis_password, refresh_key),
        }
        assert failed["event"]["code"] != 0, failed["event"]
        assert proxy.injected and before == after, {"before": before, "after": after}
        result["cases"]["refresh_redis_delete_failure"] = {
            "request": failed["event"],
            "before": before,
            "after": after,
            "proxy": {"injected": proxy.injected, "command": proxy.injected_command},
        }
        result["conclusion"] = (
            "A one-shot Redis DEL failure during refresh returned an application error; "
            "the MySQL token rows remained active after transaction rollback and both "
            "pre-existing Redis keys remained present."
        )
    finally:
        if app is not None:
            app.terminate()
            try:
                app.wait(timeout=35)
            except subprocess.TimeoutExpired:
                app.kill()
                app.wait(timeout=10)
            result["graceful_shutdown"] = "Graceful shutdown complete" in log_path.read_text(errors="replace")
        proxy.close()
        for container in reversed([name for name in owned if name != "process"]):
            subprocess.run(["docker", "rm", "-fv", container], check=True, capture_output=True, text=True)
        result["cleanup"] = {
            "containers_absent": all(
                name not in run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
                for name in (MYSQL, REDIS)
            ),
            "ports_listening": {str(port): listening(port) for port in all_ports},
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        assert result["cleanup"]["containers_absent"] and not any(result["cleanup"]["ports_listening"].values())


if __name__ == "__main__":
    main()
