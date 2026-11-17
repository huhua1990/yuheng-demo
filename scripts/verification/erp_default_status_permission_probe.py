#!/usr/bin/env python3
"""Real-login permission checks against the dedicated default-status test runtime.

The runner must first verify the JVM uses yh_default_probe in the dedicated
container and Redis on 16470. This script only accepts that disposable runtime.
Credentials and tokens are never included in the evidence.
"""
import argparse
import hashlib
import json
import os
import secrets
import subprocess
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def sql(statement):
    command = ["docker", "exec", "-i", "yh-t4-default-mysql-1116", "sh", "-c",
               'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
               '--skip-column-names -D yh_default_probe']
    return subprocess.run(command, input=statement, text=True, capture_output=True,
                          check=True).stdout.strip()


def snapshot(table):
    raw = sql(f"SELECT * FROM `{table}` ORDER BY id;")
    return {"rows": len(raw.splitlines()) if raw else 0,
            "sha256": hashlib.sha256(raw.encode()).hexdigest()}


def status_rows(table):
    return [list(map(int, row.split("\t"))) for row in sql(
        f"SELECT id,default_status+0,tenant_id,deleted+0 FROM `{table}` ORDER BY id;"
    ).splitlines()]


def run(args):
    base = "http://127.0.0.1:48192/admin-api"
    events = []

    def call(method, path, body=None, token=None, code=0, record=True):
        headers = {"Content-Type": "application/json", "tenant-id": "1"}
        if token:
            headers["Authorization"] = "Bearer " + token
        req = Request(base + path, headers=headers, method=method,
                      data=json.dumps(body).encode() if body is not None else None)
        try:
            response = urlopen(req, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            http = response.status
            data = json.load(response)
        if record:
            events.append({"method": method, "path": path, "http": http,
                           "code": data.get("code")})
        assert http == 200 and data.get("code") == code, (path, http, data.get("code"), data.get("msg"))
        return data.get("data")

    def login(username, password):
        return call("POST", "/system/auth/login", {"username": username,
                    "password": password}, record=False)["accessToken"]

    assert sql("SELECT DATABASE();") == "yh_default_probe"
    seed_passwords = sql("SELECT id,password FROM system_users WHERE id<900000 ORDER BY id;")
    admin = login(os.environ["YUHENG_PROBE_USERNAME"], os.environ["YUHENG_PROBE_PASSWORD"])
    suffix = secrets.token_hex(4)
    password = secrets.token_hex(6)
    tokens = {}
    users = {}
    for label in ("denied", "allowed"):
        username = "ds" + label + suffix
        uid = call("POST", "/system/user/create", {"username": username,
                   "password": password, "nickname": "Default status " + label,
                   "deptId": 100, "postIds": []}, admin)
        users[label] = uid
        if label == "allowed":
            rid = call("POST", "/system/role/create", {"name": "Default status probe",
                       "code": "ds" + suffix, "sort": 1, "status": 0}, admin)
            call("POST", "/system/permission/assign-role-menu",
                 {"roleId": rid, "menuIds": [621, 683]}, admin)
            call("POST", "/system/permission/assign-user-role",
                 {"userId": uid, "roleIds": [rid]}, admin)
        tokens[label] = login(username, password)
    # SQL checks complement method security and rule out super-admin controls.
    assert sql(f"SELECT r.code FROM system_role r JOIN system_user_role ur ON r.id=ur.role_id "
               f"WHERE ur.user_id={users['allowed']} AND ur.deleted=0;") == "ds" + suffix
    assert sql(f"SELECT COUNT(*) FROM system_user_role WHERE user_id={users['denied']} AND deleted=0;") == "0"
    sql("UPDATE erp_warehouse SET default_status=(id=990001) WHERE id IN (990001,990002);"
        "UPDATE erp_account SET default_status=(id=990011) WHERE id IN (990011,990012);")
    results = {}
    for resource, table, target in (("warehouse", "erp_warehouse", 990002),
                                     ("account", "erp_account", 990012)):
        assert sql(f"SELECT COUNT(*) FROM {table};") == "2"
        path = f"/erp/{resource}/update-default-status?id={target}&defaultStatus=true"
        before = snapshot(table)
        call("PUT", path, token=tokens["denied"], code=403)
        after = snapshot(table)
        assert before == after, resource
        call("PUT", path, token=tokens["allowed"])
        rows = status_rows(table)
        assert sum(row[1] for row in rows) == 1
        assert next(row[1] for row in rows if row[0] == target) == 1
        call("PUT", path.replace("true", "false"), token=tokens["allowed"])
        cleared = status_rows(table)
        assert sum(row[1] for row in cleared) == 0
        results[resource] = {"denied_before": before, "denied_after": after,
                             "allowed_true_rows": rows, "allowed_false_rows": cleared}
    preserved = seed_passwords == sql("SELECT id,password FROM system_users WHERE id<900000 ORDER BY id;")
    # New API-created users have IDs above the manually inserted test fixture only
    # if AUTO_INCREMENT was advanced; compare each original ID explicitly instead.
    if not preserved:
        original_ids = [row.split("\t")[0] for row in seed_passwords.splitlines()]
        preserved = seed_passwords == sql("SELECT id,password FROM system_users WHERE id IN ("
                                         + ",".join(original_ids) + ") ORDER BY id;")
    assert preserved
    evidence = {"workId": "YH-20261111-full-source-migration", "schema": "yh_default_probe",
                "backend_port": 48192, "mysql_container": "yh-t4-default-mysql-1116",
                "redis_container": "yh-t4-default-redis-1116", "authentication": "real password login",
                "allowed_role_permissions": ["erp:warehouse:update", "erp:account:update"],
                "seed_passwords_unchanged": preserved, "results": results, "events": events,
                "limits": ["One tenant and two ordinary users; no cross-tenant or concurrency proof.",
                           "Permission and successful true/false writes only; no failure injection.",
                           "Packaged JAR provenance recorded in result.md; not full source-build equivalence."]}
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(evidence, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"result": "PASS", "requests": len(events),
                      "seed_passwords_unchanged": preserved}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    run(parser.parse_args())
