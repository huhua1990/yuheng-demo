#!/usr/bin/env python3
"""Verify Pay/PMS after explicit template initialization in a disposable consumer."""

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
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "yuheng_p2_pay_pms_consumer_20261122"
MYSQL = "yh-p2-pay-pms-mysql-20261122"
REDIS = "yh-p2-pay-pms-redis-20261122"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13401, 16481, 48261
OUT = Path(os.environ.get("P2_PAY_PMS_OUT", ROOT / "docs/verification/2026-11-11-full-source-migration/p2-pay-pms-consumer-20261122"))
JAR = Path(os.environ.get("P2_PAY_PMS_JAR", ""))
LIMITED_ROLE_PERMISSIONS = (
    "pay:app:create", "pay:app:query", "pay:wallet:query", "pay:wallet:update-balance",
    "pms:pm:project:create", "pms:pm:project:update", "pms:pm:project:query",
    "pms:kb:library:create", "pms:kb:library:update", "pms:kb:library:query",
)
DENIED_MUTATIONS = (
    ("PUT", "/pay/app/update"), ("DELETE", "/pay/app/delete"),
    ("POST", "/pay/channel/create"), ("DELETE", "/pms/kb/library/delete"),
    ("POST", "/pms/pm/project/create"),
)


def run(*args: str, check: bool = True, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, input=input_text, text=True, capture_output=True)


def sql(container: str, statement: str) -> str:
    result = run("docker", "exec", "-i", container, "sh", "-c",
                 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
                 '--skip-column-names -D "$1"', "probe", SCHEMA, input_text=statement)
    return result.stdout.strip()


def snapshot_tables(mysql: str) -> dict[str, str]:
    tables = sql(mysql, "SELECT table_name FROM information_schema.tables WHERE table_schema=DATABASE() "
                 "AND (table_name LIKE 'pay_%' OR table_name LIKE 'pms_%') ORDER BY table_name;")
    return {table: hashlib.sha256(sql(mysql, f"SELECT * FROM `{table}` ORDER BY id;").encode()).hexdigest()
            for table in tables.splitlines()}


def call(base: str, method: str, path: str, token: str = "", body: object | None = None,
         headers: dict[str, str] | None = None) -> tuple[int, dict]:
    request_headers = {"Accept": "application/json", "Content-Type": "application/json",
                       "tenant-id": "1", "Authorization": "Bearer " + token}
    request_headers.update(headers or {})
    request = Request(base + "/admin-api" + path, method=method,
                      headers=request_headers,
                      data=None if body is None else json.dumps(body).encode())
    try:
        response = urlopen(request, timeout=30)
    except HTTPError as error:
        response = error
    with response:
        return response.status, json.loads(response.read())


def expect(base: str, method: str, path: str, token: str = "", body: object | None = None,
           code: int = 0) -> dict:
    status, payload = call(base, method, path, token, body)
    assert status == 200 and payload.get("code") == code, (method, path, status, payload)
    return payload.get("data")


def login(base: str, username: str, password: str) -> str:
    return expect(base, "POST", "/system/auth/login", body={"username": username, "password": password})["accessToken"]


def port_ready(port: int) -> bool:
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def cross_tenant_probe(base: str, first_token: str, first_ids: dict[str, int]) -> list[dict]:
    """Compare real tenant sessions; method permission succeeds before testing row isolation."""
    username, password = "p2tenant" + secrets.token_hex(3), secrets.token_urlsafe(12)[:16]
    hashed = run("htpasswd", "-bnBC", "4", username, password).stdout.strip().split(":", 1)[1]
    assert sql(MYSQL, "SELECT COUNT(*) FROM system_tenant WHERE id=122 AND deleted=0;") == "1"
    sql(MYSQL, "UPDATE system_tenant SET status=0,expire_time='2099-12-31 00:00:00' WHERE id=122;"
        "INSERT INTO system_users (id,username,password,nickname,post_ids,status,deleted,tenant_id) "
        f"VALUES (998300,'{username}','{hashed}','P2 Tenant Two','[]',0,b'0',122);"
        "INSERT INTO system_role (id,name,code,sort,data_scope,data_scope_dept_ids,status,type,creator,updater,deleted,tenant_id) "
        "VALUES (998301,'P2 Tenant Two','p2_tenant_two',1,1,'',0,1,'probe','probe',b'0',122);"
        "INSERT INTO system_role_menu (role_id,menu_id,creator,updater,deleted,tenant_id) "
        "SELECT 998301,menu_id,'probe','probe',b'0',122 FROM system_role_menu WHERE role_id=998264;"
        "INSERT INTO system_user_role (user_id,role_id,creator,updater,deleted,tenant_id) "
        "VALUES (998300,998301,'probe','probe',b'0',122);")
    status, payload = call(base, "POST", "/system/auth/login", body={"username": username, "password": password},
                           headers={"tenant-id": "122"})
    assert status == 200 and payload.get("code") == 0, (status, payload.get("code"), payload.get("msg"))
    second_token = payload["data"]["accessToken"]
    events = []

    def request(method, path, token, tenant, body=None):
        status, payload = call(base, method, path, token, body, headers={"tenant-id": str(tenant)})
        events.append({"method": method, "path": path, "tenant": tenant, "http": status, "code": payload.get("code")})
        assert status == 200 and payload.get("code") != 500, events[-1]
        return payload

    bodies = {
        "app": {"appKey": "p2-tenant-two", "name": "P2 Tenant Two App", "status": 0,
                "orderNotifyUrl": "https://example.invalid/pay", "refundNotifyUrl": "https://example.invalid/refund"},
        "project": {"name": "P2 Tenant Two Project", "type": 1, "level": 3, "openStatus": True, "icon": "ep:folder"},
        "library": {"name": "P2 Tenant Two Library", "openStatus": True},
    }
    roots = {"app": "/pay/app", "project": "/pms/pm/project", "library": "/pms/kb/library"}
    second_ids = {}
    for resource, root in roots.items():
        created = request("POST", root + "/create", second_token, 122, bodies[resource])
        assert created.get("code") == 0, (resource, created)
        second_ids[resource] = created["data"]
    tables = {"app": "pay_app", "project": "pms_project", "library": "pms_knowledge_library"}
    for resource, table in tables.items():
        for ids, tenant in ((first_ids, 1), (second_ids, 122)):
            actual = sql(MYSQL, f"SELECT tenant_id FROM `{table}` WHERE id={int(ids[resource])};")
            assert actual == str(tenant), (resource, ids[resource], actual, tenant)
    for token, tenant, own, other in ((first_token, 1, first_ids, second_ids),
                                     (second_token, 122, second_ids, first_ids)):
        for resource, root in roots.items():
            own_payload = request("GET", f"{root}/get?id={own[resource]}", token, tenant)
            assert own_payload.get("code") == 0 and own_payload["data"]["id"] == own[resource], own_payload
            before_cross = snapshot_tables(MYSQL)
            foreign = request("GET", f"{root}/get?id={other[resource]}", token, tenant)
            assert foreign.get("code") not in (401, 403), ("permission check masked tenant filtering", foreign)
            assert foreign.get("code") != 0 or foreign.get("data") is None, ("cross-tenant detail visible", resource)
            assert before_cross == snapshot_tables(MYSQL), ("foreign detail mutated data", resource)
            if resource != "app":
                updated = request("PUT", root + "/update", token, tenant,
                                  {**bodies[resource], "id": other[resource], "name": "Forbidden cross-tenant update"})
                assert updated.get("code") not in (0, 401, 403), (resource, updated)
                assert before_cross == snapshot_tables(MYSQL), ("cross-tenant update changed data", resource)
    return events


def main() -> None:
    if not JAR.is_file():
        raise SystemExit("P2_PAY_PMS_JAR must point to a mapped consumer jar")
    db_password, redis_password = secrets.token_hex(20), secrets.token_hex(20)
    containers: list[str] = []
    app = None
    result: dict[str, object] = {
        "result": "FAIL", "schema": SCHEMA,
        "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT, "app": APP_PORT},
        "jar_sha256": hashlib.sha256(JAR.read_bytes()).hexdigest(),
        "credentials_recorded": False,
    }
    OUT.mkdir(parents=True, exist_ok=True)
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
                if sql(MYSQL, "SELECT DATABASE();") == SCHEMA:
                    break
            except subprocess.CalledProcessError:
                pass
            assert time.monotonic() < deadline
            time.sleep(1)
        env = dict(os.environ, YUHENG_DB_HOST="127.0.0.1", YUHENG_DB_PORT=str(MYSQL_PORT),
                   YUHENG_DB_NAME=SCHEMA, YUHENG_DB_USERNAME="root", YUHENG_DB_PASSWORD=db_password,
                   YUHENG_REDIS_PASSWORD=redis_password)
        log_path = OUT / "backend.log"
        log = log_path.open("w")
        app = subprocess.Popen(["java", "-jar", str(JAR), f"--server.port={APP_PORT}",
                                "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
                                f"--spring.data.redis.port={REDIS_PORT}", "--spring.data.redis.database=0",
                                "--spring.data.redis.password=" + redis_password,
                                "--yuheng.security.mock-enable=false", "--spring.quartz.auto-startup=false",
                                "--yuheng.captcha.enable=false",
                                "--logging.level.com.yuheng.platform=warn"], cwd=JAR.parents[3], env=env,
                               stdout=log, stderr=log)
        deadline = time.monotonic() + 180
        while True:
            try:
                changesets = int(sql(MYSQL, "SELECT COUNT(*) FROM DATABASECHANGELOG;") or "0")
            except subprocess.CalledProcessError:
                changesets = 0
            if changesets >= 106:
                break
            assert app.poll() is None, f"application exited; see {log_path}"
            assert time.monotonic() < deadline
            time.sleep(1)
        changesets_first = int(sql(MYSQL, "SELECT COUNT(*) FROM DATABASECHANGELOG;"))
        deadline = time.monotonic() + 120
        while not port_ready(APP_PORT):
            assert app.poll() is None, f"application exited before HTTP readiness; see {log_path}"
            assert time.monotonic() < deadline
            time.sleep(1)
        base = f"http://127.0.0.1:{APP_PORT}"

        username, password = "p2paypms" + secrets.token_hex(4), secrets.token_urlsafe(12)[:16]
        denied_username, denied_password = "p2noperm" + secrets.token_hex(3), secrets.token_urlsafe(12)[:16]
        hashed = run("htpasswd", "-bnBC", "4", username, password).stdout.strip().split(":", 1)[1]
        denied_hashed = run("htpasswd", "-bnBC", "4", denied_username, denied_password).stdout.strip().split(":", 1)[1]
        permission_rows = sql(MYSQL, "SELECT id,permission FROM system_menu WHERE deleted=0 AND permission IN (" +
                             ",".join("'" + value + "'" for value in LIMITED_ROLE_PERMISSIONS) + ");")
        permission_ids = {row.split("\t", 1)[1]: int(row.split("\t", 1)[0])
                          for row in permission_rows.splitlines()}
        assert set(permission_ids) == set(LIMITED_ROLE_PERMISSIONS), permission_ids
        sql(MYSQL, f"INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) "
                   f"VALUES (998261,'{username}','{hashed}','P2 Limited Role',NULL,'[]',0,b'0',1),"
                   f"(998262,'{denied_username}','{denied_hashed}','P2 No Role',NULL,'[]',0,b'0',1);"
                   "INSERT INTO system_role (id,name,code,sort,data_scope,data_scope_dept_ids,status,type,remark,creator,updater,deleted,tenant_id) "
                   "VALUES (998264,'P2 Pay PMS Limited','p2_pay_pms_limited',1,1,'',0,1,'probe','probe','probe',b'0',1);"
                   "INSERT INTO system_role_menu (id,role_id,menu_id,creator,updater,deleted,tenant_id) VALUES " +
                   ",".join(f"({998270 + index},998264,{permission_ids[value]},'probe','probe',b'0',1)"
                            for index, value in enumerate(LIMITED_ROLE_PERMISSIONS)) + ";"
                   "INSERT INTO system_user_role (id,user_id,role_id,creator,updater,deleted,tenant_id) "
                   "VALUES (998263,998261,998264,'probe','probe',b'0',1);")
        allowed = login(base, username, password)
        denied = login(base, denied_username, denied_password)
        before = snapshot_tables(MYSQL)
        anonymous = call(base, "GET", "/pay/app/page?pageNo=1&pageSize=10")
        denied_response = call(base, "GET", "/pms/pm/project/page?pageNo=1&pageSize=10", denied)
        assert anonymous[1].get("code") == 401, anonymous
        assert denied_response[1].get("code") == 403, denied_response
        assert before == snapshot_tables(MYSQL)
        app_id = expect(base, "POST", "/pay/app/create", allowed, {
            "appKey": "p2-consumer", "name": "P2 Consumer", "status": 0,
            "orderNotifyUrl": "https://example.invalid/pay/order", "refundNotifyUrl": "https://example.invalid/pay/refund"})
        expect(base, "GET", f"/pay/app/get?id={app_id}", allowed)
        wallet = expect(base, "GET", "/pay/wallet/get?userId=998261", allowed)
        expect(base, "PUT", "/pay/wallet/update-balance", allowed, {"userId": 998261, "balance": 125})
        wallet_after = expect(base, "GET", "/pay/wallet/get?userId=998261", allowed)
        assert wallet_after["balance"] == wallet["balance"] + 125, (wallet, wallet_after)
        expect(base, "GET", "/pay/wallet-transaction/page?pageNo=1&pageSize=10&userId=998261", allowed)

        project_id = expect(base, "POST", "/pms/pm/project/create", allowed, {
            "name": "P2 Consumer Project", "type": 1, "level": 3, "openStatus": False, "icon": "ep:folder"})
        expect(base, "PUT", "/pms/pm/project/update", allowed,
               {"id": project_id, "name": "P2 Consumer Project Updated", "type": 1, "level": 2,
                "openStatus": False, "icon": "ep:folder"})
        expect(base, "GET", f"/pms/pm/project/get?id={project_id}", allowed)
        library_id = expect(base, "POST", "/pms/kb/library/create", allowed,
                            {"name": "P2 Consumer Library", "openStatus": False})
        folder_id = expect(base, "POST", "/pms/kb/document/create", allowed,
                           {"libraryId": library_id, "folderId": 0, "parentId": 0, "title": "P2 document",
                            "type": 3, "content": "P2 content"})
        document_id = folder_id
        share = expect(base, "POST", "/pms/kb/document-share/open", allowed,
                       {"documentId": document_id, "shareUserIds": []})
        public = expect(base, "GET", "/pms/kb/document-share/get-by-token?token=" + share["token"])
        assert public["id"] == document_id, public

        denied_mutations = []
        for method, path in DENIED_MUTATIONS:
            path = path + (f"?id={app_id}" if path in ("/pay/app/delete", "/pay/app/update")
                           else f"?id={library_id}" if path == "/pms/kb/library/delete" else "")
            if path.startswith("/pay/app/update"):
                body = {"id": app_id, "appKey": "denied", "name": "denied", "status": 0,
                        "orderNotifyUrl": "https://example.invalid/pay", "refundNotifyUrl": "https://example.invalid/refund"}
            elif path.startswith("/pay/channel/create"):
                body = {"appId": app_id, "code": "mock", "status": 0, "feeRate": 0, "config": "{}"}
            elif path.startswith("/pms/pm/project/create"):
                body = {"name": "Denied project", "type": 1, "level": 3,
                        "openStatus": False, "icon": "ep:folder"}
            else:
                body = None
            before_denied = snapshot_tables(MYSQL)
            actor = denied if path == "/pms/pm/project/create" else allowed
            status, payload = call(base, method, path, actor, body)
            assert status == 200 and payload.get("code") == 403, (method, path, status, payload)
            assert before_denied == snapshot_tables(MYSQL), (method, path)
            denied_mutations.append({"method": method, "path": path.split("?", 1)[0], "code": payload["code"]})
        before_spoof = snapshot_tables(MYSQL)
        spoof_status, spoof_payload = call(base, "GET", "/pms/pm/project/page?pageNo=1&pageSize=10",
                                           allowed, headers={"tenant-id": "2"})
        assert spoof_payload.get("code") == 403, (spoof_status, spoof_payload)
        assert before_spoof == snapshot_tables(MYSQL), "spoofed tenant header changed Pay/PMS data"
        cross_tenant_checks = cross_tenant_probe(base, allowed, {"app": app_id, "project": project_id, "library": library_id})

        browser_result = None
        if os.environ.get("P2_PAY_PMS_BROWSER"):
            browser_user = "p2browser" + secrets.token_hex(3)
            browser_password = secrets.token_urlsafe(12)[:16]
            browser_hash = run("htpasswd", "-bnBC", "4", browser_user, browser_password).stdout.strip().split(":", 1)[1]
            sql(MYSQL, "INSERT INTO system_users (id,username,password,nickname,post_ids,status,deleted,tenant_id) "
                f"VALUES (998400,'{browser_user}','{browser_hash}','P2 Browser','[]',0,b'0',1);"
                "INSERT INTO system_user_role (user_id,role_id,creator,updater,deleted,tenant_id) "
                "VALUES (998400,1,'probe','probe',b'0',1);")
            browser_env = dict(os.environ, P2_BROWSER_USER=browser_user, P2_BROWSER_PASSWORD=browser_password,
                               P2_SHARE_TOKEN=share["token"],
                               P2_BROWSER_OUTPUT=str(OUT / "browser.json"))
            subprocess.run(["node", str(ROOT / "scripts/verification/p2_pay_pms_browser_probe.js")],
                           check=True, env=browser_env)
            browser_result = json.loads((OUT / "browser.json").read_text())

        app.terminate()
        app.wait(timeout=35)
        app = subprocess.Popen(["java", "-jar", str(JAR), f"--server.port={APP_PORT}",
                                "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
                                f"--spring.data.redis.port={REDIS_PORT}", "--spring.data.redis.database=0",
                                "--spring.data.redis.password=" + redis_password,
                                "--yuheng.security.mock-enable=false", "--spring.quartz.auto-startup=false",
                                "--yuheng.captcha.enable=false",
                                "--logging.level.com.yuheng.platform=warn"], cwd=JAR.parents[3], env=env,
                               stdout=log, stderr=log)
        deadline = time.monotonic() + 120
        while not port_ready(APP_PORT):
            assert app.poll() is None, f"application restart exited; see {log_path}"
            assert time.monotonic() < deadline
            time.sleep(1)
        changesets_second = int(sql(MYSQL, "SELECT COUNT(*) FROM DATABASECHANGELOG;"))
        assert changesets_second == changesets_first == 107

        result.update({"result": "PASS", "changesets_first": changesets_first,
                       "changesets_second": changesets_second,
                       "flows": {"pay_app": True, "wallet_balance": wallet_after["balance"],
                                 "pms_project": True, "pms_library_document_share": True},
                       "anonymous_code": anonymous[1].get("code"), "invalid_token_code": None,
                       "limited_role_permissions": list(LIMITED_ROLE_PERMISSIONS),
                       "cross_tenant_checks": cross_tenant_checks,
                       "browser": browser_result,
                       "denied_mutations": denied_mutations,
                       "denied_user_project_query_code": denied_response[1].get("code"),
                       "spoofed_tenant_project_query_code": spoof_payload.get("code")})
    except Exception as error:
        result["error"] = str(error)
        raise
    finally:
        if app is not None and app.poll() is None:
            app.terminate()
            try:
                app.wait(timeout=35)
            except subprocess.TimeoutExpired:
                app.kill()
                app.wait(timeout=10)
        for container in reversed(containers):
            run("docker", "rm", "-fv", container, check=False)
        result["cleanup"] = {"containers_absent": all(name not in run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
                                                       for name in (MYSQL, REDIS))}
        OUT.joinpath("runtime.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"result": result["result"], "jar_sha256": result["jar_sha256"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
