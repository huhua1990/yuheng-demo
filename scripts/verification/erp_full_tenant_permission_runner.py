"""Run the full ERP tenant probe on disposable Docker services."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import time

import erp_full_tenant_permission_probe as probe

ROOT = probe.ROOT if hasattr(probe, "ROOT") else Path(__file__).resolve().parents[2]
SCHEMA = "yuheng_t4_erp_full_tenant_20261122"
MYSQL = "yh-erp-full-tenant-mysql-20261122"
REDIS = "yh-erp-full-tenant-redis-20261122"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13397, 16478, 48242
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/erp-full-tenant-20261122"


def redact_backend_log(text: str) -> str:
    text = re.sub(r'(\"password\"\s*:\s*\")[^\"]*(\")', r'\1[REDACTED]\2', text)
    text = re.sub(r'(password=)[^&\s,}]*', r'\1[REDACTED]', text)
    return re.sub(r'(Bearer\s+)[A-Za-z0-9._~-]+', r'\1[REDACTED]', text)


def run(*args: str, check: bool = True, input_text: str | None = None,
        env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, input=input_text, text=True,
                          capture_output=True, env=env)


def listening(port: int) -> bool:
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


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
    ports = (MYSQL_PORT, REDIS_PORT, APP_PORT)
    assert not any(listening(port) for port in ports)
    existing = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
    assert MYSQL not in existing and REDIS not in existing
    OUT.mkdir(parents=True, exist_ok=True)
    db_password, redis_password = secrets.token_hex(20), secrets.token_hex(20)
    containers: list[str] = []
    app: subprocess.Popen[str] | None = None
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

        def sql(statement: str) -> str:
            completed = run("docker", "exec", "-i", MYSQL, "sh", "-c",
                            'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
                            '--skip-column-names -D "$1"', "probe", SCHEMA,
                            input_text=statement, check=False)
            if completed.returncode:
                raise RuntimeError(completed.stderr.strip() or "isolated MySQL statement failed")
            return completed.stdout.strip()

        deadline = time.monotonic() + 120
        while True:
            try:
                if sql("SELECT DATABASE();") == SCHEMA:
                    break
            except RuntimeError:
                pass
            assert time.monotonic() < deadline, "isolated MySQL readiness timeout"
            time.sleep(1)

        env = dict(os.environ, YUHENG_DB_HOST="127.0.0.1",
                   YUHENG_DB_PORT=str(MYSQL_PORT), YUHENG_DB_NAME=SCHEMA,
                   YUHENG_DB_USERNAME="root", YUHENG_DB_PASSWORD=db_password,
                   YUHENG_REDIS_PASSWORD=redis_password)
        log_path = OUT / "backend.log"
        log = log_path.open("w")
        app = subprocess.Popen(
            ["java", "-jar", str(JAR), f"--server.port={APP_PORT}",
             "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
             f"--spring.data.redis.port={REDIS_PORT}", "--spring.data.redis.database=0",
             "--spring.data.redis.password=" + redis_password,
             "--yudao.security.mock-enable=false", "--spring.quartz.auto-startup=false",
             "--yudao.captcha.enable=false"], cwd=ROOT, env=env,
            stdout=log, stderr=log)
        deadline = time.monotonic() + 180
        while not listening(APP_PORT):
            assert app.poll() is None, f"Demo JAR exited; see {log_path}"
            assert time.monotonic() < deadline, "isolated Demo readiness timeout"
            time.sleep(1)
        deadline = time.monotonic() + 90
        while int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")) < probe.MIN_CHANGESETS:
            assert time.monotonic() < deadline, "Liquibase readiness timeout"
            time.sleep(1)
        args = type("ProbeArgs", (), {"base_url": f"http://127.0.0.1:{APP_PORT}",
                                      "schema": SCHEMA, "mysql_container": MYSQL})()
        evidence = probe.Probe(args).run()
        result.update(evidence)
        result["result"] = "PASS"
    except Exception as error:
        result["error"] = str(error)
        raise
    finally:
        stop(app)
        for log_path in OUT.glob("backend*.log"):
            log_path.write_text(redact_backend_log(log_path.read_text(errors="replace")))
        for name in reversed(containers):
            run("docker", "rm", "-fv", name, check=False)
        remaining = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
        cleanup = {"containers_absent": all(name not in remaining for name in (MYSQL, REDIS)),
                    "ports_listening": {str(port): listening(port) for port in ports}}
        cleanup["passed"] = cleanup["containers_absent"] and not any(cleanup["ports_listening"].values())
        result["cleanup"] = cleanup
        OUT.joinpath("runtime.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        assert cleanup["passed"], cleanup
    print(json.dumps({"result": result["result"], "requests": len(result.get("requests", [])),
                      "jar_sha256": result["jar_sha256"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
