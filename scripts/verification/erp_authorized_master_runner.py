#!/usr/bin/env python3
"""Run the ERP authorized master-data probe on disposable services."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import time

import erp_authorized_master_probe as probe


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "yuheng_t4_erp_auth_20261122"
MYSQL = "yh-erp-auth-mysql-20261122"
REDIS = "yh-erp-auth-redis-20261122"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13392, 16473, 48237
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/erp-authorized-master-20261122"


def run(*args: str, check: bool = True, input_text: str | None = None,
        env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, input=input_text, text=True,
                          capture_output=True, env=env)


def listening(port: int) -> bool:
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def sql(statement: str) -> str:
    return run("docker", "exec", "-i", MYSQL, "sh", "-c",
               'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
               '--skip-column-names -D "$1"', "probe", SCHEMA,
               input_text=statement).stdout.strip()


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
    probe.validate_target(SCHEMA, APP_PORT)
    assert JAR.is_file(), JAR
    ports = (MYSQL_PORT, REDIS_PORT, APP_PORT)
    assert not any(listening(port) for port in ports)
    existing = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
    assert MYSQL not in existing and REDIS not in existing
    OUT.mkdir(parents=True, exist_ok=True)
    db_password, redis_password = secrets.token_hex(20), secrets.token_hex(20)
    username, password = "erpauth" + secrets.token_hex(4), secrets.token_urlsafe(12)[:16]
    password_hash = run("htpasswd", "-bnBC", "4", username, password).stdout.strip().split(":", 1)[1]
    role_id, user_id = 991101, 991102
    app: subprocess.Popen[str] | None = None
    containers: list[str] = []
    result: dict[str, object] = {
        "result": "FAIL", "schema": SCHEMA,
        "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT, "app": APP_PORT},
        "jar_sha256": hashlib.sha256(JAR.read_bytes()).hexdigest(),
        "credentials_recorded": False,
    }
    try:
        run("docker", "run", "-d", "--name", MYSQL,
            "-e", "MYSQL_ROOT_PASSWORD=" + db_password,
            "-e", "MYSQL_DATABASE=" + SCHEMA,
            "-p", f"127.0.0.1:{MYSQL_PORT}:3306", "mysql:8.0.33")
        containers.append(MYSQL)
        run("docker", "run", "-d", "--name", REDIS,
            "-p", f"127.0.0.1:{REDIS_PORT}:6379", "redis:7.2.17",
            "redis-server", "--requirepass", redis_password)
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
        env = dict(os.environ, YUHENG_DB_HOST="127.0.0.1",
                   YUHENG_DB_PORT=str(MYSQL_PORT), YUHENG_DB_NAME=SCHEMA,
                   YUHENG_DB_USERNAME="root", YUHENG_DB_PASSWORD=db_password,
                   YUHENG_REDIS_PASSWORD=redis_password,
                   YUHENG_PROBE_USERNAME=username, YUHENG_PROBE_PASSWORD=password)
        os.environ.update({"YUHENG_PROBE_USERNAME": username,
                           "YUHENG_PROBE_PASSWORD": password})
        log_path = OUT / "backend.log"
        log = log_path.open("w")
        app = subprocess.Popen(
            ["java", "-jar", str(JAR), f"--server.port={APP_PORT}",
             "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
             f"--spring.data.redis.port={REDIS_PORT}", "--spring.data.redis.database=0",
             "--spring.data.redis.password=" + redis_password,
             "--yudao.security.mock-enable=false", "--spring.quartz.auto-startup=false",
             "--yudao.captcha.enable=false"],
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

        seed_passwords = sql("SELECT id,password FROM system_users WHERE id < 900000 ORDER BY id;")
        permission_rows = sql(
            "SELECT id,permission FROM system_menu WHERE deleted=0 AND permission IN (" +
            ",".join("'" + value + "'" for value in probe.PERMISSIONS) + ");")
        permission_ids = {row.split("\t", 1)[1]: int(row.split("\t", 1)[0])
                          for row in permission_rows.splitlines()}
        assert set(permission_ids) == set(probe.PERMISSIONS), permission_ids
        sql("INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) "
            f"VALUES ({user_id},'{username}','{password_hash}','ERP authorized master',NULL,'[]',0,b'0',1);")
        sql("INSERT INTO system_role (id,name,code,sort,data_scope,data_scope_dept_ids,status,type,remark,creator,updater,deleted,tenant_id) "
            f"VALUES ({role_id},'ERP authorized master','erp_auth_master',1,1,'',0,1,'probe','probe','probe',b'0',1);")
        role_menu_rows = ",".join(
            f"({991110 + index},{role_id},{permission_ids[permission]},'probe','probe',b'0',1)"
            for index, permission in enumerate(probe.PERMISSIONS)
        )
        sql("INSERT INTO system_role_menu (id,role_id,menu_id,creator,updater,deleted,tenant_id) VALUES "
            + role_menu_rows + ";")
        sql("INSERT INTO system_user_role (id,user_id,role_id,creator,updater,deleted,tenant_id) "
            f"VALUES (991103,{user_id},{role_id},'probe','probe',b'0',1);")

        args = type("ProbeArgs", (), {
            "base_url": f"http://127.0.0.1:{APP_PORT}",
            "schema": SCHEMA, "mysql_container": MYSQL,
        })()
        evidence = probe.Probe(args).run()
        assert seed_passwords == sql("SELECT id,password FROM system_users WHERE id < 900000 ORDER BY id;")
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
                    "ports_listening": {str(port): listening(port) for port in ports}}
        cleanup["passed"] = cleanup["containers_absent"] and not any(cleanup["ports_listening"].values())
        result["cleanup"] = cleanup
        OUT.joinpath("runtime.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        assert cleanup["passed"], cleanup
    print(json.dumps({"result": result["result"], "requests": len(result.get("requests", []))}))


if __name__ == "__main__":
    main()
