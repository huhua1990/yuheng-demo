#!/usr/bin/env python3
"""Run a real Demo role page probe against disposable MySQL/Redis resources."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import socket
import subprocess
import time
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "yuheng_t3_role_page_20261120"
MYSQL_PORT, REDIS_PORT, APP_PORT, UI_PORT = 13364, 16445, 48201, 5201
MYSQL, REDIS = "yh-rolepage-mysql-20261120", "yh-rolepage-redis-20261120"
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/role-page-collapse-desktop-20261117"


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
        '--skip-column-names -D "$1"', "probe", SCHEMA, input_text=statement,
    )


def literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def assert_static_matches_jar() -> int:
    dist = ROOT / "yuheng-demo-ui/dist"
    with ZipFile(JAR) as archive:
        packaged = {
            name.removeprefix("BOOT-INF/classes/static/"): hashlib.sha256(archive.read(name)).digest()
            for name in archive.namelist()
            if name.startswith("BOOT-INF/classes/static/") and not name.endswith("/")
        }
    built = {
        path.relative_to(dist).as_posix(): hashlib.sha256(path.read_bytes()).digest()
        for path in dist.rglob("*") if path.is_file()
    }
    if packaged != built:
        missing = sorted(packaged.keys() - built.keys())
        extra = sorted(built.keys() - packaged.keys())
        changed = sorted(key for key in packaged.keys() & built.keys() if packaged[key] != built[key])
        raise RuntimeError(f"dist does not match tested JAR static resources: missing={missing[:5]}, extra={extra[:5]}, changed={changed[:5]}")
    return len(packaged)


def main() -> None:
    assert JAR.is_file()
    static_resource_count = assert_static_matches_jar()
    ports = (MYSQL_PORT, REDIS_PORT, APP_PORT, UI_PORT)
    assert not any(listening(port) for port in ports)
    existing = run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
    assert MYSQL not in existing and REDIS not in existing
    OUT.mkdir(parents=True, exist_ok=True)
    db_password, redis_password = secrets.token_hex(20), secrets.token_hex(20)
    username, password = "t3rolepage" + secrets.token_hex(4), secrets.token_urlsafe(12)[:16]
    password_hash = subprocess.run(
        ["htpasswd", "-bnBC", "4", username, password], capture_output=True, text=True, check=True
    ).stdout.strip().split(":", 1)[1]
    processes: list[subprocess.Popen] = []
    containers: list[str] = []
    result = {
        "work_id": "YH-20261111-full-source-migration",
        "schema": SCHEMA,
        "jar_sha256": hashlib.sha256(JAR.read_bytes()).hexdigest(),
        "ui_source": "yuheng-demo-ui/dist; SHA-256 verified byte-for-byte against the tested JAR before startup",
        "jar_static_resource_count": static_resource_count,
        "jar_dist_byte_match": True,
        "test_server_request_queue_size": 128,
        "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT, "app": APP_PORT, "ui": UI_PORT},
        "credentials_recorded": False,
    }
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
                assert sql("SELECT DATABASE();") == SCHEMA
                break
            except (RuntimeError, AssertionError):
                assert time.monotonic() < deadline
                time.sleep(1)
        env = dict(os.environ, YUHENG_DB_HOST="127.0.0.1", YUHENG_DB_PORT=str(MYSQL_PORT),
                   YUHENG_DB_NAME=SCHEMA, YUHENG_DB_USERNAME="root", YUHENG_DB_PASSWORD=db_password,
                   YUHENG_REDIS_PASSWORD=redis_password)
        backend_log = (OUT / "backend.log").open("w")
        backend = subprocess.Popen(
            ["java", "-jar", str(JAR), f"--server.port={APP_PORT}", "--spring.profiles.active=local",
             "--spring.data.redis.host=127.0.0.1", f"--spring.data.redis.port={REDIS_PORT}",
             "--spring.data.redis.database=0", "--spring.data.redis.password=" + redis_password,
             "--yudao.security.mock-enable=false", "--spring.quartz.auto-startup=false",
             "--yudao.captcha.enable=false"], cwd=ROOT, env=env, stdout=backend_log, stderr=backend_log)
        processes.append(backend)
        deadline = time.monotonic() + 150
        while not listening(APP_PORT):
            assert backend.poll() is None and time.monotonic() < deadline
            time.sleep(1)
        deadline = time.monotonic() + 45
        while True:
            try:
                if int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")) >= 56:
                    break
            except RuntimeError:
                pass
            assert time.monotonic() < deadline
            time.sleep(1)
        sql(
            "INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) VALUES "
            "(990801," + literal(username) + "," + literal(password_hash) + ",'T3 Role Page Probe',NULL,'[]',0,b'0',1);"
        )
        sql("INSERT INTO system_user_role (user_id,role_id,creator,updater,deleted,tenant_id) VALUES "
            "(990801,1,'probe','probe',b'0',1);")
        ui_log = (OUT / "ui.log").open("w")
        ui = subprocess.Popen(
            ["python3", "-c", "import http.server, runpy; http.server.ThreadingHTTPServer.request_queue_size = 128; runpy.run_path('scripts/ui_server.py', run_name='__main__')", "--root", "yuheng-demo-ui/dist", "--host", "127.0.0.1",
             "--port", str(UI_PORT), "--backend", f"http://127.0.0.1:{APP_PORT}"],
            cwd=ROOT, stdout=ui_log, stderr=ui_log)
        processes.append(ui)
        deadline = time.monotonic() + 30
        while not listening(UI_PORT):
            assert ui.poll() is None and time.monotonic() < deadline
            time.sleep(.25)
        probe_env = dict(os.environ, YH_BROWSER_BASE=f"http://127.0.0.1:{UI_PORT}",
                         YH_BROWSER_USERNAME=username, YH_BROWSER_PASSWORD=password,
                         YH_BROWSER_OUTPUT=str(OUT / "browser"),
                         NODE_PATH="/Users/huhua/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules")
        probe = subprocess.run(["node", "scripts/verification/role_page_browser_probe.js"],
                               cwd=ROOT, env=probe_env, timeout=240, check=False)
        browser_result = json.loads((OUT / "browser.json").read_text())
        result["browser"] = browser_result
        assert probe.returncode == 0 and browser_result.get("completed")
    finally:
        for process in reversed(processes):
            process.terminate()
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        for container in reversed(containers):
            subprocess.run(["docker", "rm", "-fv", container], check=True, capture_output=True, text=True)
        result["cleanup"] = {
            "containers_absent": all(name not in run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
                                      for name in (MYSQL, REDIS)),
            "ports_listening": {str(port): listening(port) for port in ports},
        }
        (OUT / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        assert result["cleanup"]["containers_absent"] and not any(result["cleanup"]["ports_listening"].values())


if __name__ == "__main__":
    main()
