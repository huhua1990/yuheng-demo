#!/usr/bin/env python3
"""Verify user creation rolls back when its post relation insert fails."""
import argparse
import hashlib
import json
import os
import subprocess
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not args.schema.startswith("yuheng_t4_usercreate_"):
        parser.error("refusing to access a schema outside yuheng_t4_usercreate_*")
    if not args.base_url.endswith(":48145"):
        parser.error("refusing to access a non-probe port")
    return args


class Probe:
    def __init__(self, args):
        self.args = args
        self.token = None
        self.events = []

    def sql(self, statement):
        command = ["docker", "exec", "-i", "mysql8", "sh", "-c",
                   'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw --skip-column-names -D "$1"',
                   "probe", self.args.schema]
        result = subprocess.run(command, input=statement, text=True,
                                capture_output=True, check=True)
        return result.stdout.strip()

    def call(self, method, path, body=None, expected_code=0):
        headers = {"Content-Type": "application/json", "tenant-id": "1"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        request = Request(self.args.base_url + "/admin-api" + path,
                          data=json.dumps(body).encode() if body is not None else None,
                          headers=headers, method=method)
        try:
            response = urlopen(request, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            status = response.status
            payload = json.load(response)
        self.events.append({"method": method, "path": path,
                            "http": status, "code": payload.get("code")})
        assert status == 200 and payload.get("code") == expected_code, (
            method, path, status, {key: payload.get(key) for key in ("code", "msg")})
        return payload.get("data")

    def snapshot(self, table, columns):
        rows = self.sql("SELECT " + ",".join("`" + column + "`" for column in columns)
                        + " FROM `" + table + "` ORDER BY "
                        + ",".join("`" + column + "`" for column in columns) + ";")
        return {"sha256": hashlib.sha256(rows.encode()).hexdigest(),
                "row_count": len(rows.splitlines()) if rows else 0}

    def run(self):
        assert self.sql("SELECT DATABASE();") == self.args.schema
        assert self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;") == "54"
        login = self.call("POST", "/system/auth/login", {
            "username": os.environ["YUHENG_PROBE_USERNAME"],
            "password": os.environ["YUHENG_PROBE_PASSWORD"]})
        self.token = login["accessToken"]
        before = {
            "users": self.snapshot("system_users", ("id", "username", "dept_id", "tenant_id", "deleted")),
            "user_posts": self.snapshot("system_user_post", ("id", "user_id", "post_id", "tenant_id", "deleted")),
        }
        stamp = str(os.getpid())[-5:]
        username = "ucf" + stamp
        trigger = ("CREATE TRIGGER t4_usercreate_post_failure BEFORE INSERT ON system_user_post "
                   "FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='T4_USER_CREATE_POST_INJECTED'")
        self.sql(trigger)
        self.call("POST", "/system/user/create", {
            "username": username, "password": "Probe1234", "nickname": "User rollback probe",
            "deptId": 100, "postIds": [2]}, expected_code=500)
        after = {
            "users": self.snapshot("system_users", ("id", "username", "dept_id", "tenant_id", "deleted")),
            "user_posts": self.snapshot("system_user_post", ("id", "user_id", "post_id", "tenant_id", "deleted")),
        }
        assert before == after, {"before": before, "after": after}
        assert self.sql("SELECT COUNT(*) FROM system_users WHERE username='" + username + "';") == "0"
        result = {"schema": self.args.schema, "changesets": 54, "failure_point": "user post relation insert",
                  "before": before, "after": after, "user_row_rolled_back": True,
                  "events": self.events}
        with open(self.args.output, "w", encoding="utf-8") as output:
            json.dump(result, output, ensure_ascii=False, indent=2)
            output.write("\n")
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    Probe(parse_args()).run()
