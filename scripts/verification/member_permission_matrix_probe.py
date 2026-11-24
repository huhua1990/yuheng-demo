#!/usr/bin/env python3
"""Verify the Member admin permission matrix on a disposable runtime."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.error import HTTPError
from urllib.request import Request, urlopen


MEMBER_TABLES = (
    "member_config", "member_level", "member_group", "member_tag", "member_user",
    "member_address", "member_experience_record", "member_level_record",
    "member_point_record", "member_sign_in_config", "member_sign_in_record",
)
RESERVED_PORTS = {3306, 6379, 48080, 48100, 5173}
MIN_CHANGESETS = 59


@dataclass(frozen=True)
class MemberCase:
    name: str
    method: str
    path: str
    permission: str
    body: dict | None = None


MEMBER_READ_CASES = (
    MemberCase("user-get", "GET", "/member/user/get?id=990961", "member:user:query"),
    MemberCase("user-page", "GET", "/member/user/page?pageNo=1&pageSize=10", "member:user:query"),
    MemberCase("tag-get", "GET", "/member/tag/get?id=990962", "member:tag:query"),
    MemberCase("tag-page", "GET", "/member/tag/page?pageNo=1&pageSize=10", "member:tag:query"),
    MemberCase("tag-list", "GET", "/member/tag/list?ids=990962", "member:tag:query"),
    MemberCase("group-get", "GET", "/member/group/get?id=990963", "member:group:query"),
    MemberCase("group-page", "GET", "/member/group/page?pageNo=1&pageSize=10", "member:group:query"),
    MemberCase("level-get", "GET", "/member/level/get?id=990964", "member:level:query"),
    MemberCase("level-list", "GET", "/member/level/list?status=0", "member:level:query"),
    MemberCase("experience-page", "GET", "/member/experience-record/page?pageNo=1&pageSize=10", "member:experience-record:query"),
    MemberCase("level-record-page", "GET", "/member/level-record/page?pageNo=1&pageSize=10", "member:level-record:query"),
    MemberCase("point-record-page", "GET", "/member/point/record/page?pageNo=1&pageSize=10", "point:record:query"),
    MemberCase("sign-in-config-list", "GET", "/member/sign-in/config/list", "point:sign-in-config:query"),
    MemberCase("sign-in-record-page", "GET", "/member/sign-in/record/page?pageNo=1&pageSize=10", "point:sign-in-record:query"),
    MemberCase("config-get", "GET", "/member/config/get", "member:config:query"),
    # These three endpoints intentionally have no method-level permission in the source.
    MemberCase("tag-simple-list", "GET", "/member/tag/list-all-simple", "authenticated-read"),
    MemberCase("group-simple-list", "GET", "/member/group/list-all-simple", "authenticated-read"),
    MemberCase("level-simple-list", "GET", "/member/level/list-all-simple", "authenticated-read"),
)

MEMBER_WRITE_CASES = (
    MemberCase("tag-create", "POST", "/member/tag/create", "member:tag:create", {"name": "ACL tag created"}),
    MemberCase("tag-update", "PUT", "/member/tag/update", "member:tag:update", {"id": 990962, "name": "ACL tag updated"}),
    MemberCase("tag-delete", "DELETE", "/member/tag/delete?id=990962", "member:tag:delete", {"id": 990962}),
    MemberCase("group-create", "POST", "/member/group/create", "member:group:create", {"name": "ACL group created", "status": 0, "remark": "probe"}),
    MemberCase("group-update", "PUT", "/member/group/update", "member:group:update", {"id": 990963, "name": "ACL group updated", "status": 0, "remark": "probe"}),
    MemberCase("group-delete", "DELETE", "/member/group/delete?id=990963", "member:group:delete", {"id": 990963}),
    MemberCase("level-create", "POST", "/member/level/create", "member:level:create", {"name": "ACL level created", "level": 9, "experience": 900, "discountPercent": 90, "icon": "", "backgroundUrl": "", "status": 0}),
    MemberCase("level-update", "PUT", "/member/level/update", "member:level:update", {"id": 990964, "name": "ACL level updated", "level": 8, "experience": 800, "discountPercent": 90, "icon": "", "backgroundUrl": "", "status": 0}),
    MemberCase("level-delete", "DELETE", "/member/level/delete?id=990964", "member:level:delete", {"id": 990964}),
    MemberCase("sign-in-create", "POST", "/member/sign-in/config/create", "point:sign-in-config:create", {"day": 9, "point": 8, "experience": 1, "status": 0}),
    MemberCase("sign-in-update", "PUT", "/member/sign-in/config/update", "point:sign-in-config:update", {"id": 990965, "day": 8, "point": 9, "experience": 1, "status": 0}),
    MemberCase("sign-in-delete", "DELETE", "/member/sign-in/config/delete?id=990965", "point:sign-in-config:delete", {"id": 990965}),
    MemberCase("config-save", "PUT", "/member/config/save", "member:config:save", {"pointTradeDeductEnable": True, "pointTradeDeductUnitPrice": 10, "pointTradeDeductMaxPrice": 100, "pointTradeGivePoint": 1}),
    MemberCase("user-update", "PUT", "/member/user/update", "member:user:update", {"id": 990961, "mobile": "13900009961", "status": 0, "email": "acl@example.com", "nickname": "ACL member updated", "avatar": "", "name": "", "sex": 0, "areaId": None, "mark": "probe", "tagIds": [], "levelId": 990964, "groupId": 990963}),
    MemberCase("user-update-level", "PUT", "/member/user/update-level", "member:user:update-level", {"id": 990961, "levelId": 990964, "reason": "permission probe"}),
    MemberCase("user-update-point", "PUT", "/member/user/update-point", "member:user:update-point", {"id": 990961, "point": 1}),
)


def validate_probe_target(schema: str, app_port: int, mysql_port: int, redis_port: int) -> bool:
    if not re.fullmatch(r"yuheng_t4_member_acl_[0-9]{8}(?:_[a-z0-9]+)?", schema):
        raise ValueError("only yuheng_t4_member_acl_YYYYMMDD[_suffix] schemas are allowed")
    ports = (app_port, mysql_port, redis_port)
    if len(set(ports)) != len(ports) or any(port in RESERVED_PORTS for port in ports):
        raise ValueError("probe ports must be distinct and dedicated")
    if any(port < 1024 or port > 65535 for port in ports):
        raise ValueError("probe ports must be valid unprivileged ports")
    return True


class PermissionProbe:
    def __init__(self, args):
        self.args = args
        self.events: list[dict[str, object]] = []

    def run_cmd(self, *args: str, input_text: str | None = None):
        return subprocess.run(args, input=input_text, text=True, capture_output=True, check=True)

    def sql(self, statement: str) -> str:
        result = self.run_cmd(
            "docker", "exec", "-i", self.args.mysql_container, "sh", "-c",
            'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw --skip-column-names -D "$1"',
            "probe", self.args.schema, input_text=statement)
        return result.stdout.strip()

    def call(self, case: MemberCase, token: str, expected: int = 0):
        headers = {"Accept": "application/json", "Content-Type": "application/json",
                   "Authorization": "Bearer " + token, "tenant-id": "1"}
        request = Request(self.args.base_url + "/admin-api" + case.path,
                          method=case.method, headers=headers,
                          data=None if case.body is None else json.dumps(case.body).encode())
        try:
            response = urlopen(request, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            status = response.status
            content_type = response.headers.get("Content-Type", "")
            if "json" in content_type:
                payload = json.load(response)
            else:
                payload = {"code": status, "body_sha256": hashlib.sha256(response.read()).hexdigest()}
        self.events.append({"name": case.name, "method": case.method, "path": case.path,
                            "permission": case.permission, "http": status, "code": payload.get("code")})
        assert status == 200 and payload.get("code") == expected, (
            case.name, status, payload.get("code"), payload.get("msg"))
        return payload.get("data")

    def login(self, username: str, password: str) -> str:
        case = MemberCase("login", "POST", "/system/auth/login", "", {"username": username, "password": password})
        return self.call(case, "", 0)["accessToken"]

    def snapshot(self) -> dict[str, str]:
        return {table: self.sql(f"SELECT * FROM `{table}` ORDER BY id;") for table in MEMBER_TABLES}

    def run(self) -> dict[str, object]:
        assert self.sql("SELECT DATABASE();") == self.args.schema
        changesets = int(self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;"))
        assert changesets >= MIN_CHANGESETS, changesets
        seed_passwords = self.sql("SELECT id,password FROM system_users WHERE id < 900000 ORDER BY id;")
        no_role_token = self.login(os.environ["YUHENG_PROBE_NO_ROLE_USERNAME"], os.environ["YUHENG_PROBE_NO_ROLE_PASSWORD"])
        allowed_token = self.login(os.environ["YUHENG_PROBE_ALLOWED_USERNAME"], os.environ["YUHENG_PROBE_ALLOWED_PASSWORD"])
        before = self.snapshot()
        denied: list[str] = []
        allowed: list[str] = []
        authenticated_read: list[str] = []
        for case in MEMBER_READ_CASES:
            if case.permission == "authenticated-read":
                self.call(case, no_role_token)
                authenticated_read.append(case.name)
                continue
            self.call(case, no_role_token, expected=403)
            assert self.snapshot() == before, case.name
            denied.append(case.name)
            self.call(case, allowed_token)
            allowed.append(case.name)

        for case in MEMBER_WRITE_CASES:
            case_before = self.snapshot()
            self.call(case, no_role_token, expected=403)
            assert self.snapshot() == case_before, case.name
            self.call(case, allowed_token)
            allowed.append(case.name)

        assert self.sql("SELECT id,password FROM system_users WHERE id < 900000 ORDER BY id;") == seed_passwords
        return {
            "result": "PASS", "schema": self.args.schema, "changesets": changesets,
            "permission_denied_cases": denied, "allowed_cases": allowed,
            "authenticated_read_cases": authenticated_read,
            "requests": self.events, "seed_passwords_unchanged": True,
            "credentials_recorded": False,
            "limits": ["Member admin permission and representative CRUD matrix only; external authentication success and optional Pay/Mall integrations remain outside this probe."],
        }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--mysql-container", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    probe = PermissionProbe(args)
    result = probe.run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": result["result"], "requests": len(probe.events), "changesets": result["changesets"]}))


if __name__ == "__main__":
    main()
