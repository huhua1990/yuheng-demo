#!/usr/bin/env python3
"""Inject a delete failure in user-role replacement and assert DB rollback."""
import argparse
import hashlib
import json
import os
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import subprocess


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--mysql-container", default="mysql8")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not args.schema.startswith("yuheng_t4_userrole_"):
        parser.error("refusing to access a schema outside yuheng_t4_userrole_*")
    if not args.base_url.endswith(":48144"):
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

    def snapshot(self):
        rows = self.sql("SELECT id,user_id,role_id,tenant_id,deleted FROM system_user_role ORDER BY id;")
        digest = hashlib.sha256(rows.encode()).hexdigest()
        return {"sha256": digest, "row_count": len(rows.splitlines()) if rows else 0}

    def run(self):
        assert self.sql("SELECT DATABASE();") == self.args.schema
        assert self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;") == "54"
        login = self.call("POST", "/system/auth/login", {
            "username": os.environ["YUHENG_PROBE_USERNAME"],
            "password": os.environ["YUHENG_PROBE_PASSWORD"]})
        self.token = login["accessToken"]
        target_user_id = 2
        old_roles = [int(value) for value in self.sql(
            "SELECT role_id FROM system_user_role WHERE user_id=" + str(target_user_id)
            + " AND tenant_id=1 AND deleted=0 ORDER BY role_id;").splitlines()]
        assert old_roles, "admin seed needs an existing role relation for replacement"
        requested_role = int(self.sql(
            "SELECT COALESCE(MAX(id),0)+100 FROM system_role;"))
        fixture_role = ("INSERT INTO system_role (id,name,code,sort,data_scope,status,type,remark,creator,updater,tenant_id) VALUES ("
                        + str(requested_role)
                        + ",'T4 user-role rollback','t4-user-role-rollback',1,1,0,1,'probe fixture','probe','probe',1);")
        self.sql(fixture_role)
        before = self.snapshot()
        trigger = ("CREATE TRIGGER t4_userrole_delete_failure BEFORE UPDATE ON system_user_role "
                   "FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='T4_USER_ROLE_UPDATE_INJECTED'")
        self.sql(trigger)
        self.call("POST", "/system/permission/assign-user-role",
                  {"userId": target_user_id, "roleIds": [requested_role]}, expected_code=500)
        after = self.snapshot()
        assert before == after, {"before": before, "after": after}
        assert self.sql("SELECT COUNT(*) FROM system_user_role WHERE user_id=" + str(target_user_id) + " AND role_id="
                        + str(requested_role) + " AND deleted=0;") == "0"
        assert self.sql("SELECT COUNT(*) FROM system_user_role WHERE user_id=" + str(target_user_id) + " AND role_id IN ("
                        + ",".join(map(str, old_roles)) + ") AND deleted=0;") == str(len(old_roles))
        result = {"schema": self.args.schema, "user_id": target_user_id, "old_roles": old_roles,
                  "requested_role": requested_role, "failure_point": "delete old user-role relations",
                  "snapshot_before": before, "snapshot_after": after,
                  "transaction_rolled_back": True, "events": self.events}
        with open(self.args.output, "w", encoding="utf-8") as output:
            json.dump(result, output, ensure_ascii=False, indent=2)
            output.write("\n")
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    Probe(parse_args()).run()
