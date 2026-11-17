#!/usr/bin/env python3
"""P1 checks using one disposable schema and one identifiable Demo artifact."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import role_page_browser_runner as runtime

ROOT = runtime.ROOT
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/p1-fixed-package-20261117/platform-runtime.json"
runtime.SCHEMA = "yuheng_p1_platform_20261117"
runtime.MYSQL, runtime.REDIS = "yh-p1-platform-mysql", "yh-p1-platform-redis"
runtime.MYSQL_PORT, runtime.REDIS_PORT, runtime.APP_PORT = 13372, 16452, 48212
sql, literal, run = runtime.sql, runtime.literal, runtime.run
PORTS = (runtime.MYSQL_PORT, runtime.REDIS_PORT, runtime.APP_PORT)


def call(method, path, token=None, body=None, expected=0, tenant=1):
    headers = {"Content-Type": "application/json", "tenant-id": str(tenant)}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(f"http://127.0.0.1:{runtime.APP_PORT}/admin-api{path}", method=method,
                      headers=headers, data=None if body is None else json.dumps(body).encode())
    try:
        response = urlopen(request, timeout=30)
    except HTTPError as error:
        response = error
    with response:
        data = json.load(response)
    assert response.status == 200 and data.get("code") == expected, (path, response.status, data.get("code"), data.get("msg"))
    return data.get("data")


def wait_ready(app, log_path):
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        if app.poll() is not None:
            raise RuntimeError("backend exited; inspect " + str(log_path))
        if runtime.listening(runtime.APP_PORT) and "Started YuhengDemoApplication" in log_path.read_text(errors="replace"):
            return
        time.sleep(1)
    raise RuntimeError("backend readiness timeout; inspect " + str(log_path))


def stop(app):
    app.terminate()
    try:
        app.wait(timeout=35)
    except subprocess.TimeoutExpired:
        app.kill()
        app.wait(timeout=10)
        return False
    return True


def main():
    assert runtime.JAR.is_file() and not any(runtime.listening(port) for port in PORTS)
    names = run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
    assert runtime.MYSQL not in names and runtime.REDIS not in names
    db_password, redis_password = secrets.token_hex(20), secrets.token_hex(20)
    login_password = secrets.token_hex(6)
    suffix = secrets.token_hex(4)
    username = "p1admin" + suffix
    hashed = subprocess.run(["htpasswd", "-bnBC", "4", username, login_password], capture_output=True,
                            text=True, check=True).stdout.strip().split(":", 1)[1]
    result = {"work_id": "YH-20261111-full-source-migration", "schema": runtime.SCHEMA,
              "jar_sha256": hashlib.sha256(runtime.JAR.read_bytes()).hexdigest(), "cases": {}}
    owned, apps = [], []
    with tempfile.TemporaryDirectory(prefix="yuheng-p1-platform-") as temp:
        try:
            run("docker", "run", "-d", "--name", runtime.MYSQL, "-e", "MYSQL_ROOT_PASSWORD=" + db_password,
                "-e", "MYSQL_DATABASE=" + runtime.SCHEMA, "-p", f"127.0.0.1:{runtime.MYSQL_PORT}:3306", "mysql:8.0.33")
            owned.append(runtime.MYSQL)
            run("docker", "run", "-d", "--name", runtime.REDIS, "-p", f"127.0.0.1:{runtime.REDIS_PORT}:6379",
                "redis:7.2.17", "redis-server", "--requirepass", redis_password)
            owned.append(runtime.REDIS)
            deadline = time.monotonic() + 100
            while True:
                try:
                    if sql("SELECT DATABASE();") == runtime.SCHEMA:
                        break
                except RuntimeError:
                    pass
                assert time.monotonic() < deadline
                time.sleep(1)
            env = dict(os.environ, YUHENG_DB_HOST="127.0.0.1", YUHENG_DB_PORT=str(runtime.MYSQL_PORT),
                       YUHENG_DB_NAME=runtime.SCHEMA, YUHENG_DB_USERNAME="root", YUHENG_DB_PASSWORD=db_password,
                       YUHENG_REDIS_PASSWORD=redis_password)

            def start(label):
                log_path = Path(temp) / (label + ".log")
                log = log_path.open("w")
                app = subprocess.Popen(["java", "-jar", str(runtime.JAR), f"--server.port={runtime.APP_PORT}",
                    "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
                    f"--spring.data.redis.port={runtime.REDIS_PORT}", "--spring.data.redis.database=0",
                    "--spring.data.redis.password=" + redis_password, "--yudao.security.mock-enable=false",
                    "--spring.quartz.auto-startup=false", "--yudao.captcha.enable=false"],
                    cwd=ROOT, env=env, stdout=log, stderr=log)
                apps.append(app)
                wait_ready(app, log_path)
                return app, log_path

            first, _ = start("first")
            assert sql("SELECT COUNT(*) FROM DATABASECHANGELOG;") == "56"
            passwords_before = sql("SELECT id,password FROM system_users ORDER BY id;")
            changes_before = sql("SELECT ID,AUTHOR,FILENAME,MD5SUM,EXECTYPE FROM DATABASECHANGELOG ORDER BY ORDEREXECUTED;")
            assert len(passwords_before.splitlines()) > 0
            assert sql("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='system_operate_log' AND COLUMN_NAME='success';") == "0"
            first_stopped = stop(first)
            apps.remove(first)
            second, second_log = start("second")
            passwords_after = sql("SELECT id,password FROM system_users ORDER BY id;")
            changes_after = sql("SELECT ID,AUTHOR,FILENAME,MD5SUM,EXECTYPE FROM DATABASECHANGELOG ORDER BY ORDEREXECUTED;")
            assert passwords_before == passwords_after and changes_before == changes_after
            result["cases"]["restart"] = {"changesets": len(changes_after.splitlines()),
                "seed_user_count": len(passwords_before.splitlines()), "password_rows_equal": True,
                "changeset_rows_equal": True, "success_column_absent": True, "first_stopped": first_stopped,
                "second_log_previously_run": "Previously run:" in second_log.read_text(errors="replace")}

            sql("INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) VALUES "
                "(990901," + literal(username) + "," + literal(hashed) + ",'P1 isolated admin',NULL,'[]',0,b'0',1);")
            sql("INSERT INTO system_user_role (user_id,role_id,creator,updater,deleted,tenant_id) VALUES (990901,1,'probe','probe',b'0',1);")
            admin = call("POST", "/system/auth/login", body={"username": username, "password": login_password})["accessToken"]
            new_user = "p1user" + suffix
            user_password = secrets.token_hex(6)
            uid = call("POST", "/system/user/create", admin, {"username": new_user, "password": user_password,
                       "nickname": "P1 User", "deptId": 100, "postIds": []})
            rid = call("POST", "/system/role/create", admin, {"name": "P1 Role " + suffix,
                       "code": "p1role" + suffix, "sort": 1, "status": 0})
            call("PUT", "/system/user/update", admin, {"id": uid, "username": new_user,
                 "nickname": "P1 Updated", "deptId": 100, "postIds": []})
            assert call("GET", f"/system/user/get?id={uid}", admin)["nickname"] == "P1 Updated"
            call("PUT", "/system/role/update", admin, {"id": rid, "name": "P1 Updated " + suffix,
                 "code": "p1role" + suffix, "sort": 1, "status": 0})
            assert call("GET", f"/system/role/get?id={rid}", admin)["name"] == "P1 Updated " + suffix
            no_role = call("POST", "/system/auth/login", body={"username": new_user, "password": user_password})["accessToken"]
            before = sql(f"SELECT COUNT(*) FROM system_user_role WHERE user_id={int(uid)} AND deleted=0;")
            call("POST", "/system/permission/assign-user-role", no_role, {"userId": uid, "roleIds": [rid]}, expected=403)
            assert before == sql(f"SELECT COUNT(*) FROM system_user_role WHERE user_id={int(uid)} AND deleted=0;") == "0"
            menu_id = int(sql("SELECT id FROM system_menu WHERE permission='system:post:query' AND deleted=0 LIMIT 1;"))
            call("POST", "/system/permission/assign-role-menu", admin, {"roleId": rid, "menuIds": [menu_id]})
            assert menu_id in call("GET", f"/system/permission/list-role-menus?roleId={rid}", admin)
            call("POST", "/system/permission/assign-user-role", admin, {"userId": uid, "roleIds": [rid]})
            assert rid in call("GET", f"/system/permission/list-user-roles?userId={uid}", admin)
            granted = call("POST", "/system/auth/login", body={"username": new_user, "password": user_password})["accessToken"]
            assert call("GET", "/system/post/page?pageNo=1&pageSize=10", granted)["total"] > 0
            call("GET", "/infra/job/page?pageNo=1&pageSize=10", no_role, expected=403)
            call("GET", "/infra/file/page?pageNo=1&pageSize=10", no_role, expected=403)
            jobs = call("GET", "/infra/job/page?pageNo=1&pageSize=10", admin)
            sql("INSERT INTO infra_file (id,config_id,name,path,url,type,size,deleted) VALUES "
                "(990901,4,'p1-file.txt','p1-file.txt','http://127.0.0.1/p1-file.txt','text/plain',15,b'0');")
            sql("INSERT INTO infra_file_content (config_id,path,content,deleted) VALUES "
                "(4,'p1-file.txt',UNHEX('50312066696c652070726f62650a'),b'0');")
            files = call("GET", "/infra/file/page?pageNo=1&pageSize=10", admin)
            assert any(row["id"] == 990901 for row in files["list"])
            with urlopen(f"http://127.0.0.1:{runtime.APP_PORT}/admin-api/infra/file/4/get/p1-file.txt", timeout=20) as response:
                content = response.read()
                assert response.status == 200 and content == b"P1 file probe\n"
            call("DELETE", f"/system/user/delete?id={uid}", admin)
            call("DELETE", f"/system/role/delete?id={rid}", admin)
            assert sql(f"SELECT deleted+0 FROM system_users WHERE id={int(uid)};") == "1"
            assert sql(f"SELECT deleted+0 FROM system_role WHERE id={int(rid)};") == "1"
            result["cases"]["system_and_infra"] = {"user_created": True, "role_created": True,
                "user_role_updated_and_read_back": True, "user_role_deleted": True,
                "unauthorized_assignment_code": 403, "denied_assignment_unchanged": True,
                "role_menu_readback": True, "user_role_readback": True, "granted_query": True,
                "job_denied_code": 403, "file_denied_code": 403,
                "job_total": jobs["total"], "file_total": files["total"],
                "database_file_download_verified": True}
            assert passwords_before == sql("SELECT id,password FROM system_users WHERE id IN (" +
                ",".join(row.split("\t", 1)[0] for row in passwords_before.splitlines()) + ") ORDER BY id;")
            result["cases"]["seed_passwords_after_operations_unchanged"] = True
            result["cases"]["second_stopped"] = stop(second)
            apps.remove(second)
            lifecycle = Path(temp) / "lifecycle"
            (lifecycle / "scripts").mkdir(parents=True)
            target = lifecycle / "yuheng-demo-server/yuheng-demo-server-bootstrap/target"
            target.mkdir(parents=True)
            (target / "yuheng-demo.jar").symlink_to(runtime.JAR)
            (lifecycle / "yuheng-demo-ui").mkdir()
            (lifecycle / "yuheng-demo-ui/dist").symlink_to(ROOT / "yuheng-demo-ui/dist", target_is_directory=True)
            for name in ("start.sh", "stop.sh", "ui_server.py"):
                shutil.copy2(ROOT / "scripts" / name, lifecycle / "scripts" / name)
            bin_dir = lifecycle / "bin"
            bin_dir.mkdir()
            uname = bin_dir / "uname"
            uname.write_text("#!/bin/sh\nif [ \"$1\" = -s ]; then echo Linux; else /usr/bin/uname \"$@\"; fi\n")
            uname.chmod(0o755)
            lifecycle_env = dict(env, PATH=str(bin_dir) + os.pathsep + os.environ["PATH"],
                                 BACKEND_PORT="48213", UI_PORT="5202", YUHENG_REDIS_HOST="127.0.0.1",
                                 YUHENG_REDIS_PORT=str(runtime.REDIS_PORT), YUHENG_REDIS_DATABASE="0")
            assert not any(runtime.listening(p) for p in (48213, 5202))
            try:
                start_result = subprocess.run(["bash", str(lifecycle / "scripts/start.sh")], env=lifecycle_env,
                                              capture_output=True, text=True, timeout=100)
                assert start_result.returncode == 0, start_result.stderr
                with urlopen("http://127.0.0.1:5202/login", timeout=10) as response:
                    assert response.status == 200 and b'<div id="app">' in response.read()
                with urlopen("http://127.0.0.1:48213/admin-api/system/auth/get-permission-info", timeout=10) as response:
                    assert response.status == 200 and json.load(response)["code"] == 401
                result["cases"]["lifecycle"] = {"start_exit": 0, "login_page_http": 200,
                    "backend_anonymous_code": 401, "redis_isolated_port": runtime.REDIS_PORT}
            finally:
                stopped = subprocess.run(["bash", str(lifecycle / "scripts/stop.sh")], env=lifecycle_env,
                                         capture_output=True, text=True, timeout=20)
                result["cases"].setdefault("lifecycle", {})["stop_exit"] = stopped.returncode
                result["cases"]["lifecycle"]["ports_released"] = not any(runtime.listening(p) for p in (48213, 5202))
            assert stopped.returncode == 0 and result["cases"]["lifecycle"]["ports_released"]
            result["completed"] = True
        finally:
            for app in reversed(apps):
                stop(app)
            for container in reversed(owned):
                subprocess.run(["docker", "rm", "-fv", container], check=True, capture_output=True)
            names = run("docker", "ps", "-a", "--format", "{{.Names}}").splitlines()
            result["cleanup"] = {"containers_absent": all(n not in names for n in (runtime.MYSQL, runtime.REDIS)),
                                 "ports_listening": {str(p): runtime.listening(p) for p in PORTS}}
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            assert result["cleanup"]["containers_absent"] and not any(result["cleanup"]["ports_listening"].values())


if __name__ == "__main__":
    main()
