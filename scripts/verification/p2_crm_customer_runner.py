#!/usr/bin/env python3
"""Verify the CRM customer API and SQL lifecycle in an isolated consumer JAR."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import time
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
JAR = Path(os.environ.get("P2_CRM_JAR", "/tmp/yuheng-p2-crm-bpm-clean-d5jtBb/consumer/yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"))
SCHEMA = "yuheng_p2_crm_customer_20261123"
REDIS = "yh-p2-crm-customer-redis-20261123"
REDIS_PORT = 16501
APP_PORT = 48301
UI_PORT = 48302
MYSQL_CONTAINER = "codex-qc-schema-mysql"
MYSQL_PORT = 51045
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/p2-crm-customer-current-20261123"
UI_DIST = Path("/tmp/yuheng-p2-crm-bpm-clean-d5jtBb/consumer/yuheng-demo-ui/dist")
PLAYWRIGHT = Path.home() / ".npm/_npx/9833c18b2d85bc59/node_modules"
USER_ID = 992610
ROLE_ID = 992611

PERMISSIONS = ("crm:customer:create", "crm:customer:query", "crm:customer:update", "crm:customer:delete")
CRM_MENU_IDS: set[int] = set()


def run(*args: str, check: bool = True, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, input=input_text, text=True, capture_output=True, check=check)


def listening(port: int) -> bool:
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def mysql_password() -> str:
    env = run("docker", "inspect", "-f", "{{range .Config.Env}}{{println .}}{{end}}", MYSQL_CONTAINER).stdout
    for line in env.splitlines():
        if line.startswith("MYSQL_ROOT_PASSWORD="):
            return line.split("=", 1)[1]
    raise RuntimeError("MySQL root password is unavailable")


MYSQL_PASSWORD = mysql_password()


def sql(statement: str, schema: str | None = SCHEMA) -> str:
    database_args = ("-D", schema) if schema else ()
    result = run(
        "docker", "exec", "-i", MYSQL_CONTAINER, "sh", "-c",
        'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
        '--skip-column-names "$@"', "probe", *database_args, input_text=statement,
    )
    return result.stdout.strip()


def call(base: str, method: str, path: str, token: str = "", body: object | None = None) -> tuple[int, dict]:
    headers = {"Accept": "application/json", "Content-Type": "application/json", "tenant-id": "1"}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(base + "/admin-api" + path, method=method, headers=headers,
                      data=None if body is None else json.dumps(body).encode())
    try:
        response = urlopen(request, timeout=30)
    except HTTPError as error:
        response = error
    with response:
        return response.status, json.loads(response.read())


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
    assert JAR.is_file(), JAR
    assert not listening(REDIS_PORT) and not listening(APP_PORT) and not listening(UI_PORT)
    names = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
    assert REDIS not in names
    OUT.mkdir(parents=True, exist_ok=True)
    redis_password = secrets.token_hex(20)
    username = "crmprobe" + secrets.token_hex(4)
    password = secrets.token_urlsafe(12)[:16]
    password_hash = run("htpasswd", "-bnBC", "4", username, password).stdout.strip().split(":", 1)[1]
    app: subprocess.Popen[str] | None = None
    ui: subprocess.Popen[str] | None = None
    result: dict[str, object] = {
        "result": "FAIL", "schema": SCHEMA, "mysql_container": MYSQL_CONTAINER,
        "jar_sha256": hashlib.sha256(JAR.read_bytes()).hexdigest(),
        "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT, "app": APP_PORT, "ui": UI_PORT},
        "credentials_recorded": False,
    }
    try:
        sql(f"CREATE DATABASE `{SCHEMA}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;", schema=None)
        run("docker", "run", "-d", "--name", REDIS,
            "-p", f"127.0.0.1:{REDIS_PORT}:6379", "redis:7.2.17",
            "redis-server", "--requirepass", redis_password)
        deadline = time.monotonic() + 30
        while not listening(REDIS_PORT):
            assert time.monotonic() < deadline, "Redis readiness timeout"
            time.sleep(1)

        env = dict(os.environ, YUHENG_DB_HOST="127.0.0.1", YUHENG_DB_PORT=str(MYSQL_PORT),
                   YUHENG_DB_NAME=SCHEMA, YUHENG_DB_USERNAME="root", YUHENG_DB_PASSWORD=MYSQL_PASSWORD,
                   YUHENG_REDIS_PASSWORD=redis_password)
        log_path = OUT / "backend.log"
        log = log_path.open("w")
        app = subprocess.Popen(
            ["java", "-jar", str(JAR), f"--server.port={APP_PORT}", "--spring.profiles.active=local",
             "--spring.data.redis.host=127.0.0.1", f"--spring.data.redis.port={REDIS_PORT}",
             "--spring.data.redis.database=0", "--spring.data.redis.password=" + redis_password,
             "--yudao.security.mock-enable=false", "--spring.quartz.auto-startup=false",
             "--yudao.captcha.enable=false"],
            cwd=ROOT, env=env, stdout=log, stderr=log,
        )
        deadline = time.monotonic() + 180
        while not listening(APP_PORT):
            assert app.poll() is None, f"JAR exited; see {log_path}"
            assert time.monotonic() < deadline, "Demo readiness timeout"
            time.sleep(1)
        deadline = time.monotonic() + 120
        while True:
            try:
                changesets = int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;"))
                if changesets >= 59:
                    break
            except subprocess.CalledProcessError:
                pass
            assert time.monotonic() < deadline, "Liquibase readiness timeout"
            time.sleep(1)

        seed_passwords = sql("SELECT id,password FROM system_users WHERE id < 900000 ORDER BY id;")
        permission_rows = sql("SELECT id,permission FROM system_menu WHERE deleted=0 AND permission IN ("
                              + ",".join("'" + permission + "'" for permission in PERMISSIONS) + ");")
        permission_ids = {row.split("\t", 1)[1]: int(row.split("\t", 1)[0])
                          for row in permission_rows.splitlines() if "\t" in row}
        missing = [permission for permission in PERMISSIONS if permission not in permission_ids]
        assert not missing, f"CRM template permission seed is incomplete: {missing}"
        crm_menu_rows = sql("SELECT id,CONCAT(COALESCE(path,''),'|',COALESCE(component,'')) FROM system_menu WHERE deleted=0 AND "
                            "((path='/crm' AND type=1) OR component='crm/customer/index');")
        CRM_MENU_IDS = {int(row.split("\t", 1)[0]) for row in crm_menu_rows.splitlines() if "\t" in row}
        menu_components = {row.split("\t", 1)[1].split("|", 1)[1]
                           for row in crm_menu_rows.splitlines() if "\t" in row}
        assert "crm/customer/index" in menu_components, "CRM customer page menu seed is missing"
        assert CRM_MENU_IDS, "CRM root and customer page menu seeds are missing"
        sql("INSERT INTO system_users (id,username,password,nickname,post_ids,status,deleted,tenant_id) "
            f"VALUES ({USER_ID},'{username}','{password_hash}','CRM API probe','[]',0,b'0',1);")
        sql("INSERT INTO system_role (id,name,code,sort,data_scope,data_scope_dept_ids,status,type,creator,updater,deleted,tenant_id) "
            f"VALUES ({ROLE_ID},'CRM API probe','crm_api_probe',1,1,'',0,1,'probe','probe',b'0',1);")
        menu_ids = CRM_MENU_IDS | set(permission_ids.values())
        sql("INSERT INTO system_role_menu (id,role_id,menu_id,creator,updater,deleted,tenant_id) VALUES "
            + ",".join(f"({ROLE_ID * 100 + i},{ROLE_ID},{menu_id},'probe','probe',b'0',1)"
                        for i, menu_id in enumerate(sorted(menu_ids))) + ";")
        sql("INSERT INTO system_user_role (id,user_id,role_id,creator,updater,deleted,tenant_id) "
            f"VALUES ({ROLE_ID * 100 + 50},{USER_ID},{ROLE_ID},'probe','probe',b'0',1);")

        base = f"http://127.0.0.1:{APP_PORT}"
        status, anonymous = call(base, "GET", "/crm/customer/page?pageNo=1&pageSize=20")
        assert status == 200 and anonymous.get("code") == 401, anonymous
        status, login = call(base, "POST", "/system/auth/login", body={"username": username, "password": password})
        assert status == 200 and login.get("code") == 0, login
        token = login["data"]["accessToken"]
        marker = "P2 CRM customer " + secrets.token_hex(4)
        body = {"name": marker, "ownerUserId": USER_ID, "mobile": "13800138000", "remark": "isolated P2"}
        status, created = call(base, "POST", "/crm/customer/create", token, body)
        assert status == 200 and created.get("code") == 0, created
        customer_id = int(created["data"])
        row = sql(f"SELECT id,name,owner_user_id,CAST(deleted AS UNSIGNED),tenant_id FROM crm_customer WHERE id={customer_id};")
        assert row.split("\t")[:5] == [str(customer_id), marker, str(USER_ID), "0", "1"], row
        permission = sql(f"SELECT biz_type,biz_id,user_id,level,deleted,tenant_id FROM crm_permission WHERE biz_id={customer_id};")
        assert permission and str(customer_id) in permission and str(USER_ID) in permission, permission
        status, page = call(base, "GET", "/crm/customer/page?pageNo=1&pageSize=20&name=" + quote(marker), token)
        assert status == 200 and page.get("code") == 0 and page["data"]["total"] == 1, page

        assert (UI_DIST / "index.html").is_file() and (PLAYWRIGHT / "playwright").is_dir()
        ui_log_path = OUT / "ui.log"
        ui_log = ui_log_path.open("w")
        ui = subprocess.Popen(["python3", str(ROOT / "scripts/ui_server.py"), "--root", str(UI_DIST),
                               "--port", str(UI_PORT), "--backend", f"http://127.0.0.1:{APP_PORT}"],
                              cwd=ROOT, env=dict(os.environ, NODE_PATH=str(PLAYWRIGHT)),
                              stdout=ui_log, stderr=ui_log)
        deadline = time.monotonic() + 20
        while not listening(UI_PORT):
            assert ui.poll() is None and time.monotonic() < deadline, "isolated CRM UI failed to start"
            time.sleep(.25)
        browser_env = dict(os.environ, NODE_PATH=str(PLAYWRIGHT),
                           P2_CRM_UI_ORIGIN=f"http://127.0.0.1:{UI_PORT}",
                           P2_CRM_USERNAME=username, P2_CRM_PASSWORD=password,
                           P2_CRM_CUSTOMER_MARKER=marker,
                           P2_CRM_BROWSER_OUTPUT=str(OUT / "browser.json"))
        browser = subprocess.run(["node", str(ROOT / "scripts/verification/p2_crm_customer_browser_probe.js")],
                                 cwd=ROOT, env=browser_env, text=True, capture_output=True)
        assert browser.returncode == 0, f"desktop CRM browser probe failed: {browser.stderr[-2500:]}"
        result["browser"] = json.loads((OUT / "browser.json").read_text())
        status, updated = call(base, "PUT", "/crm/customer/update", token,
                               {**body, "id": customer_id, "name": marker + " updated"})
        assert status == 200 and updated.get("code") == 0, updated
        assert sql(f"SELECT name FROM crm_customer WHERE id={customer_id} AND deleted=0;") == marker + " updated"
        status, deleted = call(base, "DELETE", f"/crm/customer/delete?id={customer_id}", token)
        assert status == 200 and deleted.get("code") == 0, deleted
        assert sql(f"SELECT CAST(deleted AS UNSIGNED) FROM crm_customer WHERE id={customer_id};") == "1"
        assert sql(f"SELECT COUNT(*) FROM crm_permission WHERE biz_id={customer_id} AND deleted=0;") == "0"
        assert seed_passwords == sql("SELECT id,password FROM system_users WHERE id < 900000 ORDER BY id;")
        result.update({"result": "PASS", "changesets": changesets,
                       "assertions": ["anonymous_requires_auth", "login", "create", "sql_owner_and_tenant",
                                       "permission_row", "page_query", "update", "soft_delete", "permission_cleanup",
                                       "seed_passwords_unchanged"]})
    except Exception as error:
        result["error"] = str(error)
        raise
    finally:
        stop(app)
        stop(ui)
        run("docker", "rm", "-fv", REDIS, check=False)
        run("docker", "exec", "-e", "MYSQL_PWD=" + MYSQL_PASSWORD,
            MYSQL_CONTAINER, "mysql", "-uroot", "-e", f"DROP DATABASE IF EXISTS `{SCHEMA}`", check=False)
        log_path = OUT / "backend.log"
        if log_path.exists():
            text = log_path.read_text(errors="replace")
            for secret in (password, password_hash, redis_password, MYSQL_PASSWORD):
                text = text.replace(secret, "[REDACTED]")
            log_path.write_text(text)
            log_path.unlink()
        ui_log_path = OUT / "ui.log"
        if ui_log_path.exists():
            ui_log_path.unlink()
        result["cleanup"] = {"redis_absent": REDIS not in run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines(),
                              "schema_absent": SCHEMA not in sql("SHOW DATABASES;", schema=None),
                              "ports_listening": {str(p): listening(p) for p in (REDIS_PORT, APP_PORT, UI_PORT)}}
        result["cleanup"]["passed"] = result["cleanup"]["redis_absent"] and result["cleanup"]["schema_absent"] and not any(result["cleanup"]["ports_listening"].values())
        (OUT / "runtime.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        assert result["cleanup"]["passed"], result["cleanup"]
    print(json.dumps({"result": result["result"], "changesets": result.get("changesets"),
                      "jar_sha256": result["jar_sha256"], "cleanup": result["cleanup"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
