#!/usr/bin/env python3
"""Run the ERP permission matrix in disposable MySQL and Redis services."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import time

import erp_permission_matrix_probe as probe


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "yuheng_t4_erp_acl_20261122"
MYSQL = "yh-erp-acl-mysql-20261122"
REDIS = "yh-erp-acl-redis-20261122"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13391, 16472, 48236
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/erp-permission-matrix-20261122"


def run(*args: str, check: bool = True, input_text: str | None = None,
        env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, input=input_text, text=True,
                          capture_output=True, env=env)


def listening(port: int) -> bool:
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def sql(statement: str) -> str:
    return run("docker", "exec", "-i", MYSQL, "sh", "-c",
               'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw --skip-column-names -D "$1"',
               "probe", SCHEMA, input_text=statement).stdout.strip()


def stop(process: subprocess.Popen[str] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=35)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def main() -> None:
    probe.validate_probe_target(SCHEMA, APP_PORT, MYSQL_PORT, REDIS_PORT)
    assert JAR.is_file(), JAR
    assert not any(listening(port) for port in (MYSQL_PORT, REDIS_PORT, APP_PORT))
    existing = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
    assert MYSQL not in existing and REDIS not in existing
    OUT.mkdir(parents=True, exist_ok=True)
    db_password, redis_password = secrets.token_hex(20), secrets.token_hex(20)
    admin_user, admin_password = "acladmin" + secrets.token_hex(4), secrets.token_urlsafe(12)[:16]
    no_role_user, no_role_password = "aclguest" + secrets.token_hex(4), secrets.token_urlsafe(12)[:16]
    admin_hash = run("htpasswd", "-bnBC", "4", admin_user, admin_password).stdout.strip().split(":", 1)[1]
    no_role_hash = run("htpasswd", "-bnBC", "4", no_role_user, no_role_password).stdout.strip().split(":", 1)[1]
    app: subprocess.Popen[str] | None = None
    containers: list[str] = []
    result: dict[str, object] = {"result": "FAIL", "schema": SCHEMA,
                                  "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT, "app": APP_PORT},
                                  "jar_sha256": hashlib.sha256(JAR.read_bytes()).hexdigest(),
                                  "credentials_recorded": False}
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
                   YUHENG_REDIS_PASSWORD=redis_password, YUHENG_PROBE_USERNAME=admin_user,
                   YUHENG_PROBE_PASSWORD=admin_password, YUHENG_PROBE_NO_ROLE_USERNAME=no_role_user,
                   YUHENG_PROBE_NO_ROLE_PASSWORD=no_role_password)
        os.environ.update({key: env[key] for key in (
            "YUHENG_PROBE_USERNAME", "YUHENG_PROBE_PASSWORD",
            "YUHENG_PROBE_NO_ROLE_USERNAME", "YUHENG_PROBE_NO_ROLE_PASSWORD")})
        log_path = OUT / "backend.log"
        log = log_path.open("w")
        app = subprocess.Popen(["java", "-jar", str(JAR), f"--server.port={APP_PORT}",
            "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
            f"--spring.data.redis.port={REDIS_PORT}", "--spring.data.redis.database=0",
            "--spring.data.redis.password=" + redis_password, "--yudao.security.mock-enable=false",
            "--spring.quartz.auto-startup=false", "--yudao.captcha.enable=false"],
            cwd=ROOT, env=env, stdout=log, stderr=log)
        deadline = time.monotonic() + 180
        while not listening(APP_PORT):
            assert app.poll() is None, f"Demo JAR exited; see {log_path}"
            assert time.monotonic() < deadline, "Demo readiness timeout"
            time.sleep(1)
        deadline = time.monotonic() + 90
        while int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")) < probe.MIN_CHANGESETS:
            assert time.monotonic() < deadline, "Liquibase readiness timeout"
            time.sleep(1)
        sql("INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) VALUES "
            f"(990991,'{admin_user}','{admin_hash}','ACL admin',NULL,'[]',0,b'0',1),"
            f"(990992,'{no_role_user}','{no_role_hash}','ACL guest',NULL,'[]',0,b'0',1);")
        sql("INSERT INTO system_user_role (user_id,role_id,creator,updater,deleted,tenant_id) "
            "VALUES (990991,1,'probe','probe',b'0',1);")
        args = type("ProbeArgs", (), {"base_url": f"http://127.0.0.1:{APP_PORT}",
            "schema": SCHEMA, "mysql_container": MYSQL})()
        evidence = probe.PermissionProbe(args).run()
        result.update(evidence)
        result["result"] = "PASS"
    except Exception as error:
        result["error"] = str(error)
        raise
    finally:
        stop(app)
        for name in reversed(containers):
            run("docker", "rm", "-fv", name, check=False)
        remaining = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
        cleanup = {"containers_absent": all(name not in remaining for name in (MYSQL, REDIS)),
                    "ports_listening": {str(port): listening(port) for port in (MYSQL_PORT, REDIS_PORT, APP_PORT)}}
        cleanup["passed"] = cleanup["containers_absent"] and not any(cleanup["ports_listening"].values())
        result["cleanup"] = cleanup
        OUT.joinpath("runtime.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        assert cleanup["passed"], cleanup
    print(json.dumps({"result": result["result"], "requests": len(result.get("requests", [])),
                      "unprotected_authenticated": len(result.get("authenticated_without_erp_permission", []))}))


if __name__ == "__main__":
    main()
