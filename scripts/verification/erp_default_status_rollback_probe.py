#!/usr/bin/env python3
"""Run default-status failure injection in disposable containers only.

Requires Docker, Java, a packaged Demo JAR and YUHENG_PROBE_USERNAME/PASSWORD.
Owns a new container pair and loopback ports 13371, 16471 and 48193. Cleanup
runs in finally; no shared MySQL, Redis, credentials or user rows are changed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import tempfile
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def command(*args, **kwargs):
    return subprocess.run(args, capture_output=True, text=True, check=True, **kwargs).stdout.strip()


def listening(port):
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def run(args):
    root = Path(__file__).resolve().parents[2]
    jar = Path(args.jar).resolve() if args.jar else root / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
    result_dir = Path(args.output_dir).resolve()
    result_dir.mkdir(parents=True, exist_ok=True)
    assert jar.is_file()
    username, password = os.environ["YUHENG_PROBE_USERNAME"], os.environ["YUHENG_PROBE_PASSWORD"]
    for port in (13371, 16471, 48193):
        assert not listening(port), f"Port {port} in use; refusing to replace existing service"
    suffix = secrets.token_hex(4)
    mysql, redis = "yh-defrollback-mysql-" + suffix, "yh-defrollback-redis-" + suffix
    schema = "yuheng_t4_default_rollback"
    db_password, redis_password = secrets.token_hex(16), secrets.token_hex(16)
    owned = []
    process = None
    evidence = {"workId": "YH-20261111-full-source-migration",
                "jar_sha256": hashlib.sha256(jar.read_bytes()).hexdigest(),
                "containers": [mysql, redis], "schema": schema,
                "backend_port": 48193, "mock_authentication": False, "cases": {}}

    def sql(statement):
        return command("docker", "exec", "-i", mysql, "sh", "-c",
                       'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
                       '--skip-column-names -D ' + schema, input=statement)

    def snapshot(table):
        raw = sql(f"SELECT * FROM {table} ORDER BY id;")
        return {"rows": len(raw.splitlines()), "sha256": hashlib.sha256(raw.encode()).hexdigest()}

    def statuses(table):
        return [list(map(int, row.split("\t"))) for row in sql(
            f"SELECT id,default_status+0,tenant_id FROM {table} ORDER BY id;").splitlines()]

    def call(method, path, token=None, body=None):
        headers = {"tenant-id": "1", "Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        request = Request("http://127.0.0.1:48193/admin-api" + path, method=method,
                          headers=headers, data=None if body is None else json.dumps(body).encode())
        try:
            response = urlopen(request, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            assert response.status == 200, response.status
            return json.load(response)

    try:
        command("docker", "run", "-d", "--name", mysql,
                "-e", "MYSQL_ROOT_PASSWORD=" + db_password,
                "-e", "MYSQL_DATABASE=" + schema, "-e", "MYSQL_USER=yhprobe",
                "-e", "MYSQL_PASSWORD=" + db_password, "-p", "127.0.0.1:13371:3306", "mysql:8.0.33")
        owned.append(mysql)
        command("docker", "run", "-d", "--name", redis, "-p", "127.0.0.1:16471:6379",
                "redis:7-alpine", "redis-server", "--requirepass", redis_password)
        owned.append(redis)
        deadline = time.monotonic() + 90
        while True:
            try:
                assert sql("SELECT DATABASE();") == schema
                break
            except (subprocess.CalledProcessError, AssertionError):
                assert time.monotonic() < deadline, "MySQL readiness timeout"
                time.sleep(1)
        with tempfile.TemporaryDirectory(prefix="yh-default-rollback-") as temp:
            logfile = Path(temp) / "backend.log"
            env = dict(os.environ, YUHENG_DB_HOST="127.0.0.1", YUHENG_DB_PORT="13371",
                       YUHENG_DB_NAME=schema, YUHENG_DB_USERNAME="yhprobe",
                       YUHENG_DB_PASSWORD=db_password, YUHENG_REDIS_PASSWORD=redis_password)
            with logfile.open("w") as log:
                process = subprocess.Popen(["java", "-jar", str(jar), "--server.port=48193",
                    "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
                    "--spring.data.redis.port=16471", "--spring.data.redis.database=0",
                    "--spring.data.redis.password=" + redis_password,
                    "--yudao.security.mock-enable=false", "--spring.quartz.auto-startup=false",
                    "--logging.level.com.yuheng=INFO"], cwd=root, env=env, stdout=log, stderr=log)
                try:
                    deadline = time.monotonic() + 120
                    while not listening(48193):
                        assert process.poll() is None, "Backend exited before listening"
                        assert time.monotonic() < deadline, "Backend readiness timeout"
                        time.sleep(1)
                    evidence["changesets"] = int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;"))
                    originals = sql("SELECT id,password FROM system_users ORDER BY id;")
                    token_reply = call("POST", "/system/auth/login",
                                       body={"username": username, "password": password})
                    assert token_reply["code"] == 0, token_reply.get("msg")
                    token = token_reply["data"]["accessToken"]
                    for resource, table in (("warehouse", "erp_warehouse"), ("account", "erp_account")):
                        assert sql(f"SELECT COUNT(*) FROM {table};") == "0"
                        sql(f"INSERT INTO {table} (id,name,sort,status,default_status,tenant_id) VALUES "
                            "(990001,'Rollback old',1,0,b'1',1),(990002,'Rollback new',2,0,b'0',1);")
                        path = f"/erp/{resource}/update-default-status?id=990002&defaultStatus=true"
                        control = call("PUT", path, token)
                        assert control["code"] == 0
                        assert statuses(table) == [[990001, 0, 1], [990002, 1, 1]]
                        sql(f"UPDATE {table} SET default_status=(id=990001);")
                        marker = "T4_DEFAULT_" + resource.upper() + "_INJECTED"
                        trigger = "t4_default_" + resource
                        sql(f"DELIMITER $$\nCREATE TRIGGER {trigger} BEFORE UPDATE ON {table} FOR EACH ROW "
                            f"BEGIN IF NEW.id=990002 AND NEW.default_status=b'1' THEN "
                            f"SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='{marker}'; END IF; END$$\nDELIMITER ;\n")
                        assert sql("SELECT COUNT(*) FROM information_schema.triggers WHERE "
                                   f"trigger_schema=DATABASE() AND trigger_name='{trigger}';") == "1"
                        before, before_rows = snapshot(table), statuses(table)
                        reply = call("PUT", path, token)
                        assert reply["code"] == 500, reply
                        after, after_rows = snapshot(table), statuses(table)
                        for _ in range(20):
                            if marker in logfile.read_text():
                                break
                            time.sleep(.1)
                        assert marker in logfile.read_text(), "Injected SQL failure not confirmed in log"
                        evidence["cases"][resource] = {"path": path, "positive_control_code": 0,
                            "failure_code": reply["code"], "verified_trigger": trigger,
                            "log_marker": marker, "log_marker_observed": True,
                            "before": before, "after": after, "before_rows": before_rows,
                            "after_rows": after_rows, "full_snapshot_unchanged": before == after}
                        assert after_rows == before_rows and before == after, (
                            resource + " default switch must roll back both writes", before_rows, after_rows)
                    evidence["seed_passwords_unchanged"] = originals == sql(
                        "SELECT id,password FROM system_users ORDER BY id;")
                    assert evidence["seed_passwords_unchanged"]
                finally:
                    process.terminate()
                    try:
                        process.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=10)
                    evidence["graceful_shutdown_observed"] = "Graceful shutdown complete" in logfile.read_text()
    finally:
        for container in reversed(owned):
            command("docker", "rm", "-fv", container)
        evidence["cleanup"] = {"ports_listening": {str(p): listening(p) for p in (13371, 16471, 48193)},
            "containers_absent": all(name not in command("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
                                     for name in owned)}
        (result_dir / "runtime.json").write_text(json.dumps(evidence, indent=2) + "\n")
    assert not any(evidence["cleanup"]["ports_listening"].values())
    assert evidence["cleanup"]["containers_absent"]
    print(json.dumps({"probe": "completed", "warehouse_full_rollback": evidence["cases"]["warehouse"]["full_snapshot_unchanged"],
                      "account_full_rollback": evidence["cases"]["account"]["full_snapshot_unchanged"],
                      "cleanup": evidence["cleanup"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--jar", help="Optional isolated packaged JAR; never rebuild a running shared JAR")
    run(parser.parse_args())
