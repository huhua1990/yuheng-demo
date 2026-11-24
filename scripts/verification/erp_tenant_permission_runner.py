#!/usr/bin/env python3
"""Run the ERP tenant and permission probe on disposable Docker services."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import time

import erp_tenant_permission_probe as probe


ROOT = probe.ROOT
SCHEMA = "yuheng_t4_erp_tenant_20261122"
MYSQL = "yh-erp-tenant-mysql-20261122"
REDIS = "yh-erp-tenant-redis-20261122"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13390, 16471, 48235
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/erp-tenant-permission-20261122"


def command(*args: str, check: bool = True, input_text: str | None = None,
            env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, input=input_text, text=True,
                          capture_output=True, env=env)


def stop(process: subprocess.Popen[str] | None) -> bool:
    if process is None or process.poll() is not None:
        return True
    process.terminate()
    try:
        process.wait(timeout=35)
        return True
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)
        return False


def main() -> None:
    probe.validate_probe_target(SCHEMA, APP_PORT, MYSQL_PORT, REDIS_PORT)
    assert JAR.is_file(), JAR
    actual_hash = hashlib.sha256(JAR.read_bytes()).hexdigest()
    assert not any(probe.listening(port) for port in (MYSQL_PORT, REDIS_PORT, APP_PORT))
    existing = command("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
    assert MYSQL not in existing and REDIS not in existing

    db_password = secrets.token_hex(20)
    redis_password = secrets.token_hex(20)
    containers: list[str] = []
    application: subprocess.Popen[str] | None = None
    OUT.mkdir(parents=True, exist_ok=True)
    result: dict[str, object] = {
        "result": "FAIL",
        "schema": SCHEMA,
        "jar_sha256": actual_hash,
        "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT, "app": APP_PORT},
        "credentials_recorded": False,
    }
    try:
        command("docker", "run", "-d", "--name", MYSQL,
                "-e", "MYSQL_ROOT_PASSWORD=" + db_password,
                "-e", "MYSQL_DATABASE=" + SCHEMA,
                "-p", f"127.0.0.1:{MYSQL_PORT}:3306", "mysql:8.0.33")
        containers.append(MYSQL)
        command("docker", "run", "-d", "--name", REDIS,
                "-p", f"127.0.0.1:{REDIS_PORT}:6379", "redis:7.2.17",
                "redis-server", "--requirepass", redis_password)
        containers.append(REDIS)

        deadline = time.monotonic() + 120
        while True:
            try:
                check = command("docker", "exec", "-i", MYSQL, "sh", "-c",
                                'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot --batch --skip-column-names -D "$1"',
                                "probe", SCHEMA, input_text="SELECT DATABASE();")
                if check.stdout.strip() == SCHEMA:
                    break
            except subprocess.CalledProcessError:
                pass
            assert time.monotonic() < deadline, "isolated MySQL readiness timeout"
            time.sleep(1)

        env = dict(os.environ, YUHENG_DB_HOST="127.0.0.1", YUHENG_DB_PORT=str(MYSQL_PORT),
                   YUHENG_DB_NAME=SCHEMA, YUHENG_DB_USERNAME="root",
                   YUHENG_DB_PASSWORD=db_password, YUHENG_REDIS_PASSWORD=redis_password)
        log_path = OUT / "backend.log"
        log = log_path.open("w")
        application = subprocess.Popen(
            ["java", "-jar", str(JAR), f"--server.port={APP_PORT}",
             "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
             f"--spring.data.redis.port={REDIS_PORT}", "--spring.data.redis.database=0",
             "--spring.data.redis.password=" + redis_password,
             "--yudao.security.mock-enable=false", "--spring.quartz.auto-startup=false",
             "--yudao.captcha.enable=false"],
            cwd=ROOT, env=env, stdout=log, stderr=log)
        deadline = time.monotonic() + 180
        while not probe.listening(APP_PORT):
            assert application.poll() is None, f"Demo JAR exited; see {log_path}"
            assert time.monotonic() < deadline, "isolated Demo readiness timeout"
            time.sleep(1)
        deadline = time.monotonic() + 90
        while True:
            try:
                check = command("docker", "exec", "-i", MYSQL, "sh", "-c",
                                'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot --batch --skip-column-names -D "$1"',
                                "probe", SCHEMA, input_text="SELECT COUNT(*) FROM DATABASECHANGELOG;")
                if int(check.stdout.strip()) >= probe.MIN_CHANGESETS:
                    break
            except (subprocess.CalledProcessError, ValueError):
                pass
            assert time.monotonic() < deadline, "Liquibase readiness timeout"
            time.sleep(1)

        args = type("ProbeArgs", (), {
            "base_url": f"http://127.0.0.1:{APP_PORT}",
            "schema": SCHEMA,
            "mysql_container": MYSQL,
        })()
        runner_probe = probe.Probe(args)
        runner_probe.load_permission_ids()
        runner_probe.setup_fixtures()
        evidence = runner_probe.run()
        result.update(evidence)
        result["result"] = "PASS"
    except Exception as error:
        result["error"] = str(error)
        raise
    finally:
        stop(application)
        for name in reversed(containers):
            command("docker", "rm", "-fv", name, check=False)
        remaining = command("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
        cleanup = {
            "containers_absent": all(name not in remaining for name in (MYSQL, REDIS)),
            "ports_listening": {str(port): probe.listening(port)
                                for port in (MYSQL_PORT, REDIS_PORT, APP_PORT)},
        }
        cleanup["passed"] = cleanup["containers_absent"] and not any(cleanup["ports_listening"].values())
        result["cleanup"] = cleanup
        OUT.joinpath("runtime.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        assert cleanup["passed"], cleanup
    print(json.dumps({"result": result["result"], "requests": len(result.get("requests", [])),
                      "jar_sha256": actual_hash}, ensure_ascii=False))


if __name__ == "__main__":
    main()
