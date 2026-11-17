#!/usr/bin/env python3
"""Verify user create rejects a post owned by another tenant in a disposable DB."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--mysql-container", default="mysql8")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not args.schema.startswith(("yuheng_t4_post_", "yuheng_t4_postupdate_")):
        parser.error("refusing to access a schema outside yuheng_t4_post_*")
    if not args.base_url.endswith((":48143", ":48146")):
        parser.error("refusing to access a non-probe port")
    return args


class Probe:
    def __init__(self, args):
        self.args = args
        self.token = None
        self.events = []

    def sql(self, statement):
        command = ["docker", "exec", "-i", self.args.mysql_container, "sh", "-c",
                   'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw --skip-column-names -D "$1"',
                   "probe", self.args.schema]
        import subprocess
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
        self.events.append({"method": method, "path": path, "http": status,
                            "code": payload.get("code")})
        assert status == 200 and payload.get("code") == expected_code, (
            method, path, status, {key: payload.get(key) for key in ("code", "msg")})
        return payload.get("data")

    def table_snapshot(self, table, columns):
        data = self.sql("SELECT " + ",".join("`" + column + "`" for column in columns)
                        + " FROM `" + table + "` ORDER BY "
                        + ",".join("`" + column + "`" for column in columns) + ";")
        return hashlib.sha256(data.encode()).hexdigest(), len(data.splitlines()) if data else 0

    def snapshot(self):
        return {
            "users": self.table_snapshot("system_users", ("id", "username", "dept_id", "tenant_id", "deleted")),
            "user_posts": self.table_snapshot("system_user_post", ("id", "user_id", "post_id", "tenant_id", "deleted")),
        }

    def run(self):
        assert self.sql("SELECT DATABASE();") == self.args.schema
        assert self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;") == "54"
        assert self.sql("SELECT COUNT(*) FROM system_users WHERE id=1 AND password<>'';") == "1"
        assert self.sql("SELECT COUNT(*) FROM system_dept WHERE id=100 AND tenant_id=1 AND status=0 AND deleted=0;") == "1"
        control_post_id = int(self.sql(
            "SELECT id FROM system_post WHERE tenant_id=1 AND status=0 AND deleted=0 ORDER BY id LIMIT 1;"))

        login = self.call("POST", "/system/auth/login", {
            "username": os.environ["YUHENG_PROBE_USERNAME"],
            "password": os.environ["YUHENG_PROBE_PASSWORD"]})
        self.token = login["accessToken"]

        timestamp = datetime.now().strftime("%H%M%S")
        control_username = "ptc" + timestamp
        foreign_username = "ptf" + timestamp
        control_body = {"username": control_username, "password": "Probe1234",
                        "nickname": "Post probe control", "deptId": 100,
                        "postIds": [control_post_id]}
        control_id = self.call("POST", "/system/user/create", control_body)
        assert self.sql("SELECT COUNT(*) FROM system_users WHERE id=" + str(control_id)
                        + " AND tenant_id=1 AND dept_id=100;") == "1"
        assert self.sql("SELECT COUNT(*) FROM system_user_post WHERE user_id=" + str(control_id)
                        + " AND post_id=" + str(control_post_id)
                        + " AND tenant_id=1 AND deleted=0;") == "1"

        foreign_post_id = int(self.sql("SELECT COALESCE(MAX(id),0)+100 FROM system_post;"))
        fixture_sql = ("INSERT INTO system_post (id,code,name,sort,status,remark,creator,updater,tenant_id) VALUES ("
                       + str(foreign_post_id) + ",'T4-POST-X','Foreign tenant post',1,0,'probe fixture',"
                       "'probe','probe',999);")
        self.sql(fixture_sql)
        assert self.sql("SELECT COUNT(*) FROM system_post WHERE id=" + str(foreign_post_id)
                        + " AND tenant_id=999 AND status=0 AND deleted=0;") == "1"

        before = self.snapshot()
        foreign_body = {"username": foreign_username, "password": "Probe1234",
                        "nickname": "Post probe foreign", "deptId": 100,
                        "postIds": [foreign_post_id]}
        self.call("POST", "/system/user/create", foreign_body, expected_code=1002005000)
        after = self.snapshot()
        assert before == after, {"before": before, "after": after}
        assert self.sql("SELECT COUNT(*) FROM system_users WHERE username='" + foreign_username + "';") == "0"
        assert self.sql("SELECT COUNT(*) FROM system_user_post WHERE post_id=" + str(foreign_post_id) + ";") == "0"

        update_before = self.snapshot()
        update_body = {"id": 1, "username": "admin", "nickname": "芋道源码",
                       "deptId": 103, "postIds": [foreign_post_id]}
        self.call("PUT", "/system/user/update", update_body, expected_code=1002005000)
        update_after = self.snapshot()
        assert update_before == update_after, {"before": update_before, "after": update_after}

        result = {
            "schema": self.args.schema,
            "changesets": 54,
            "initial_users": 21,
            "control": {"created_user_id": control_id, "tenant_id": 1,
                        "dept_id": 100, "post_id": control_post_id, "relation_count": 1},
            "foreign_post": {"tenant_id": 999, "id": foreign_post_id,
                             "response_code": self.events[-1]["code"],
                             "user_and_relation_snapshot_unchanged": True,
                             "users_snapshot": before["users"],
                             "user_posts_snapshot": before["user_posts"]},
            "foreign_post_update": {"user_id": 1, "response_code": self.events[-1]["code"],
                                    "user_and_relation_snapshot_unchanged": update_before == update_after,
                                    "users_snapshot": update_before["users"],
                                    "user_posts_snapshot": update_before["user_posts"]},
            "events": self.events,
        }
        with open(self.args.output, "w", encoding="utf-8") as output:
            json.dump(result, output, ensure_ascii=False, indent=2)
            output.write("\n")
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    Probe(parse_args()).run()
