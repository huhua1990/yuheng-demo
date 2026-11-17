#!/usr/bin/env python3
"""Verify role-menu set replacement rolls back after delete failure."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--mysql-container", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.base_url != "http://127.0.0.1:48172":
        parser.error("only the dedicated role-menu probe port is allowed")
    if args.schema != "yuheng_t4_role_menu_20261115":
        parser.error("refusing to access a schema outside the dedicated role-menu probe")
    if args.mysql_container != "yh-t4-rolemenu-mysql-final":
        parser.error("only the dedicated disposable MySQL container is allowed")
    return args


class Probe:
    def __init__(self, args):
        self.args = args
        self.events = []

    def sql(self, statement):
        command = [
            "docker", "exec", "-i", self.args.mysql_container, "sh", "-c",
            'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw --skip-column-names -D "$1"',
            "probe", self.args.schema,
        ]
        result = subprocess.run(command, input=statement, text=True,
                                capture_output=True, check=True)
        return result.stdout.strip()

    def call(self, method, path, body=None, expected_code=0):
        headers = {
            "Content-Type": "application/json",
            "tenant-id": "1",
            "Authorization": "Bearer test1",
        }
        request = Request(
            self.args.base_url + "/admin-api" + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers=headers,
            method=method,
        )
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
            method, path, status, {key: payload.get(key) for key in ("code", "msg")}
        )
        return payload.get("data")

    def snapshot(self):
        rows = self.sql(
            "SELECT id,role_id,menu_id,tenant_id,deleted FROM system_role_menu ORDER BY id;"
        )
        return {
            "sha256": hashlib.sha256(rows.encode()).hexdigest(),
            "row_count": len(rows.splitlines()) if rows else 0,
        }

    def run(self):
        assert self.sql("SELECT DATABASE();") == self.args.schema
        assert self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;") == "56"
        assert self.sql(
            "SELECT COUNT(*) FROM system_users WHERE id=1 AND password IS NOT NULL AND password<>'';"
        ) == "1"
        role_id, insert_menu_id = 2, 566
        assert self.sql(
            f"SELECT COUNT(*) FROM system_menu WHERE id={insert_menu_id} AND deleted=0 AND status=0;"
        ) == "1"
        assert self.sql(
            f"SELECT COUNT(*) FROM system_role_menu WHERE role_id={role_id} "
            f"AND menu_id={insert_menu_id} AND tenant_id=1 AND deleted=0;"
        ) == "0"
        before = self.snapshot()
        assert before["row_count"] > 0
        self.sql(
            "CREATE TRIGGER t4_role_menu_delete_failure BEFORE UPDATE ON system_role_menu "
            "FOR EACH ROW SIGNAL SQLSTATE '45000' "
            "SET MESSAGE_TEXT='T4_ROLE_MENU_DELETE_INJECTED';"
        )
        trigger_count = self.sql(
            "SELECT COUNT(*) FROM information_schema.triggers "
            "WHERE trigger_schema=DATABASE() AND trigger_name='t4_role_menu_delete_failure';"
        )
        assert trigger_count == "1"
        self.call(
            "POST", "/system/permission/assign-role-menu",
            {"roleId": role_id, "menuIds": [insert_menu_id]}, expected_code=500,
        )
        after = self.snapshot()
        assert before == after, {"before": before, "after": after}
        assert self.sql(
            f"SELECT COUNT(*) FROM system_role_menu WHERE role_id={role_id} "
            f"AND menu_id={insert_menu_id} AND tenant_id=1 AND deleted=0;"
        ) == "0"
        result = {
            "result": "PASS",
            "schema": self.args.schema,
            "liquibase_changesets": 56,
            "role_id": role_id,
            "attempted_new_menu_id": insert_menu_id,
            "failure_point": "logical deletion of old role-menu relations",
            "trigger_verified_before_request": True,
            "snapshot_before": before,
            "snapshot_after": after,
            "new_relation_absent_after_rollback": True,
            "transaction_rolled_back": True,
            "events": self.events,
        }
        self.args.output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps({key: result[key] for key in (
            "result", "role_id", "attempted_new_menu_id", "snapshot_before",
            "snapshot_after", "events",
        )}, ensure_ascii=False))


if __name__ == "__main__":
    Probe(parse_args()).run()
