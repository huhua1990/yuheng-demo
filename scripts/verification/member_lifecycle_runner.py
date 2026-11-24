#!/usr/bin/env python3
"""Run the Member lifecycle probe against disposable MySQL/Redis services."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import tempfile
import time

from member_lifecycle_probe import LifecycleProbe


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "yuheng_p2_member_lifecycle_20261123k"
MYSQL = "yh-p2-member-lifecycle-mysql-20261123k"
REDIS = "yh-p2-member-lifecycle-redis-20261123k"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13415, 16496, 48277
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/member-lifecycle-final10-20261123"


def run(*args: str, check: bool = True, input_text: str | None = None, env=None):
    return subprocess.run(args, check=check, input=input_text, text=True,
                          capture_output=True, env=env)


def listening(port: int) -> bool:
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def stop(process):
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=35)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def sql(statement: str) -> str:
    return run(
        "docker", "exec", "-i", MYSQL, "sh", "-c",
        'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
        '--skip-column-names -D "$1"', "probe", SCHEMA, input_text=statement,
    ).stdout.strip()


def literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> None:
    assert JAR.is_file(), JAR
    ports = (MYSQL_PORT, REDIS_PORT, APP_PORT)
    assert not any(listening(port) for port in ports)
    existing = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
    assert MYSQL not in existing and REDIS not in existing
    OUT.mkdir(parents=True, exist_ok=True)
    result: dict[str, object] = {
        "result": "FAIL", "schema": SCHEMA,
        "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT, "app": APP_PORT},
        "jar_sha256": hashlib.sha256(JAR.read_bytes()).hexdigest(),
        "credentials_recorded": False,
    }
    db_password, redis_password = secrets.token_hex(20), secrets.token_hex(20)
    suffix = secrets.token_hex(4)
    admin_name, admin_password = "mLifecycleAdmin" + suffix, secrets.token_urlsafe(12)[:16]
    admin_hash = run("htpasswd", "-bnBC", "4", admin_name, admin_password).stdout.strip().split(":", 1)[1]
    containers: list[str] = []
    app = None
    log = None
    try:
        run("docker", "run", "-d", "--name", MYSQL, "-e", "MYSQL_ROOT_PASSWORD=" + db_password,
            "-e", "MYSQL_DATABASE=" + SCHEMA, "-p", f"127.0.0.1:{MYSQL_PORT}:3306", "mysql:8.0.33")
        containers.append(MYSQL)
        run("docker", "run", "-d", "--name", REDIS, "-p", f"127.0.0.1:{REDIS_PORT}:6379",
            "redis:7.2.17", "redis-server", "--requirepass", redis_password)
        containers.append(REDIS)
        deadline = time.monotonic() + 120
        while True:
            try:
                if sql("SELECT DATABASE();") == SCHEMA:
                    break
            except subprocess.CalledProcessError:
                pass
            assert time.monotonic() < deadline, "isolated MySQL readiness timeout"
            time.sleep(1)

        env = dict(os.environ, YUHENG_DB_HOST="127.0.0.1", YUHENG_DB_PORT=str(MYSQL_PORT),
                   YUHENG_DB_NAME=SCHEMA, YUHENG_DB_USERNAME="root", YUHENG_DB_PASSWORD=db_password,
                   YUHENG_REDIS_PASSWORD=redis_password)
        log_path = Path(tempfile.gettempdir()) / ("yuheng-member-lifecycle-" + SCHEMA + ".log")
        log = log_path.open("w")
        app = subprocess.Popen([
            "java", "-jar", str(JAR), f"--server.port={APP_PORT}",
            "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
            f"--spring.data.redis.port={REDIS_PORT}", "--spring.data.redis.database=0",
            "--spring.data.redis.password=" + redis_password, "--yudao.security.mock-enable=false",
            "--spring.quartz.auto-startup=false", "--yudao.captcha.enable=false",
        ], cwd=ROOT, env=env, stdout=log, stderr=log)
        deadline = time.monotonic() + 180
        while not listening(APP_PORT):
            assert app.poll() is None, f"Demo JAR exited; see {log_path}"
            assert time.monotonic() < deadline, "Demo readiness timeout"
            time.sleep(1)
        deadline = time.monotonic() + 90
        while int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")) < 59:
            assert time.monotonic() < deadline, "Liquibase readiness timeout"
            time.sleep(1)

        password_snapshot = sql(
            "SELECT SHA2(GROUP_CONCAT(CONCAT(id,':',password) ORDER BY id SEPARATOR '|'),256) "
            "FROM system_users;"
        )
        sql("UPDATE system_tenant SET status=0, expire_time=DATE_ADD(NOW(), INTERVAL 1 YEAR) "
            "WHERE id=2 AND deleted=0;")
        sql("INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) "
            "VALUES (991201,%s,%s,'Member lifecycle admin',NULL,'[]',0,b'0',1);" %
            (literal(admin_name), literal(admin_hash)))
        sql("INSERT INTO system_user_role (user_id,role_id,creator,updater,deleted,tenant_id) "
            "SELECT 991201,role_id,creator,updater,b'0',tenant_id FROM system_user_role "
            "WHERE user_id=1 AND deleted=0;")
        member_hash = run("htpasswd", "-bnBC", "4", "19900001202", "fixture").stdout.strip().split(":", 1)[1]
        sql("INSERT INTO member_user (id,mobile,email,password,status,register_ip,nickname,tenant_id) "
            "VALUES (991202,'19900001202','',%s,0,'127.0.0.1','Lifecycle member',1),"
            "(991203,'19900001204','',%s,0,'127.0.0.1','Lifecycle password member',1),"
            "(991204,'19900001205','',%s,0,'127.0.0.1','Lifecycle reset member',1);" %
            (literal(member_hash), literal(member_hash), literal(member_hash)))

        base = f"http://127.0.0.1:{APP_PORT}"
        auth = LifecycleProbe(base, SCHEMA, MYSQL)
        admin = auth.call("POST", "/system/auth/login", "", {
            "username": admin_name, "password": admin_password,
        }, prefix="/admin-api")["accessToken"]
        app_token = auth.call("POST", "/member/auth/login", "", {
            "mobile": "19900001202", "password": "fixture",
        }, prefix="/app-api")["accessToken"]
        result["changesets"] = int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;"))
        result["cases"] = auth.run(admin, app_token)
        assert password_snapshot == sql(
            "SELECT SHA2(GROUP_CONCAT(CONCAT(id,':',password) ORDER BY id SEPARATOR '|'),256) "
            "FROM system_users WHERE id < 991201;"
        )
        result["seed_passwords_unchanged"] = True
        result["result"] = "PASS"
    except Exception as error:
        result["error"] = str(error)
        raise
    finally:
        stop(app)
        if log is not None:
            log.close()
        if "log_path" in locals():
            log_path.unlink(missing_ok=True)
        for name in reversed(containers):
            run("docker", "rm", "-fv", name, check=False)
        remaining = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
        cleanup = {
            "containers_absent": all(name not in remaining for name in (MYSQL, REDIS)),
            "ports_listening": {str(port): listening(port) for port in ports},
        }
        cleanup["passed"] = cleanup["containers_absent"] and not any(cleanup["ports_listening"].values())
        result["cleanup"] = cleanup
        result["completed"] = result.get("result") == "PASS" and cleanup["passed"]
        OUT.joinpath("runtime.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        assert cleanup["passed"], cleanup
    print(json.dumps({"result": result["result"], "changesets": result.get("changesets")}))


if __name__ == "__main__":
    main()
