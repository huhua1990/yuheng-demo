#!/usr/bin/env python3
"""Member address-default and config lifecycle checks for a disposable runtime."""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError
from urllib.request import Request, urlopen


@dataclass
class LifecycleProbe:
    base_url: str
    schema: str
    mysql_container: str

    def __post_init__(self):
        self.events: list[dict[str, object]] = []

    def sql(self, statement: str) -> str:
        import subprocess

        result = subprocess.run(
            "docker exec -i %s sh -c 'MYSQL_PWD=\"$MYSQL_ROOT_PASSWORD\" exec mysql -uroot "
            "--batch --raw --skip-column-names -D \"$1\"' probe %s"
            % (self.mysql_container, self.schema),
            shell=True,
            input=statement,
            text=True,
            capture_output=True,
            check=True,
        )
        return result.stdout.strip()

    def call(self, method: str, path: str, token: str, body=None, prefix: str = "/app-api",
             expected: int = 0):
        headers = {"Accept": "application/json", "Content-Type": "application/json",
                   "Authorization": "Bearer " + token, "tenant-id": "1"}
        request = Request(self.base_url + prefix + path, method=method, headers=headers,
                          data=None if body is None else json.dumps(body).encode())
        try:
            response = urlopen(request, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            payload = json.load(response)
            status = response.status
        self.events.append({"method": method, "path": path, "status": status,
                            "code": payload.get("code")})
        assert status == 200 and payload.get("code") == expected, (
            method, path, status, payload.get("code"), payload.get("msg"))
        return payload.get("data")

    def call_raw(self, method: str, path: str, body=None, prefix: str = "/app-api"):
        request = Request(self.base_url + prefix + path, method=method,
                          headers={"Accept": "application/json", "Content-Type": "application/json",
                                   "tenant-id": "1"},
                          data=None if body is None else json.dumps(body).encode())
        try:
            response = urlopen(request, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            payload = json.load(response)
            status = response.status
        self.events.append({"method": method, "path": path, "status": status,
                            "code": payload.get("code")})
        return status, payload

    def send_code(self, token: str, mobile: str, scene: int) -> str:
        self.call("POST", "/member/auth/send-sms-code", token,
                  {"mobile": mobile, "scene": scene})
        code = self.sql(
            "SELECT code FROM system_sms_code WHERE mobile='%s' AND scene=%d AND used=0 "
            "ORDER BY id DESC LIMIT 1;" % (mobile, scene)
        )
        assert code and code.isdigit() and 4 <= len(code) <= 6
        return code

    def exercise_account_lifecycle(self, app_token: str) -> dict[str, object]:
        user_id = 991202
        self.call("PUT", "/member/user/update", app_token,
                  {"nickname": "Updated member", "avatar": "", "email": "lifecycle@example.com", "sex": 1})
        profile = self.call("GET", "/member/user/get", app_token)
        assert profile["nickname"] == "Updated member" and profile["email"] == "lifecycle@example.com"
        assert self.sql("SELECT nickname,email,sex FROM member_user WHERE id=%d;" % user_id) == \
            "Updated member\tlifecycle@example.com\t1"

        mobile_sms_before = self.sql("SELECT COUNT(*) FROM system_sms_code;")
        occupied_status, occupied_response = self.call_raw("POST", "/member/auth/send-sms-code", {
            "mobile": "19900001204", "scene": 2,
        }, prefix="/app-api")
        assert occupied_status == 200 and occupied_response.get("code") == 1004003007
        assert self.sql("SELECT COUNT(*) FROM system_sms_code;") == mobile_sms_before
        new_mobile = "19900001203"
        mobile_code = self.send_code(app_token, new_mobile, 2)
        before_mobile = self.sql("SELECT id,mobile FROM member_user WHERE id=%d;" % user_id)
        sms_used_before = self.sql("SELECT used FROM system_sms_code WHERE mobile='%s' AND scene=2 "
                                   "ORDER BY id DESC LIMIT 1;" % new_mobile)
        self.call("PUT", "/member/user/update-mobile", app_token,
                  {"mobile": new_mobile, "code": "000000"}, expected=1002014000)
        assert self.sql("SELECT id,mobile FROM member_user WHERE id=%d;" % user_id) == before_mobile
        assert self.sql("SELECT used FROM system_sms_code WHERE mobile='%s' AND scene=2 "
                        "ORDER BY id DESC LIMIT 1;" % new_mobile) == sms_used_before == "0"
        self.call("PUT", "/member/user/update-mobile", app_token,
                  {"mobile": new_mobile, "code": mobile_code})
        assert self.sql("SELECT mobile FROM member_user WHERE id=%d;" % user_id) == new_mobile
        status, old_mobile_login = self.call_raw("POST", "/member/auth/login",
                                                  {"mobile": "19900001202", "password": "fixture"})
        assert status == 200 and old_mobile_login.get("code") != 0, old_mobile_login.get("code")
        new_mobile_login = self.call("POST", "/member/auth/login", "", {
            "mobile": new_mobile, "password": "fixture",
        })
        assert new_mobile_login["userId"] == user_id

        password_user_id = 991203
        password_user_mobile = "19900001204"
        password_login = self.call("POST", "/member/auth/login", "", {
            "mobile": password_user_mobile, "password": "fixture",
        })
        password_token = password_login["accessToken"]
        password_code = self.send_code(password_token, password_user_mobile, 3)
        self.call("PUT", "/member/user/update-password", password_token,
                  {"password": "changed-secret", "code": password_code})
        old_password_status, old_password_login = self.call_raw(
            "POST", "/member/auth/login", {"mobile": password_user_mobile, "password": "fixture"})
        assert old_password_status == 200 and old_password_login.get("code") != 0
        changed_login = self.call("POST", "/member/auth/login", "", {
            "mobile": password_user_mobile, "password": "changed-secret",
        })
        assert changed_login["userId"] == password_user_id
        assert self.sql("SELECT COUNT(*) FROM member_user WHERE id=%d AND mobile='%s';" %
                        (user_id, new_mobile)) == "1"
        assert self.sql("SELECT COUNT(*) FROM member_user WHERE id=%d AND password LIKE '$2%%';" %
                        password_user_id) == "1"
        reset_user_id = 991204
        reset_mobile = "19900001205"
        before_reset_hash = self.sql("SELECT password FROM member_user WHERE id=%d;" % reset_user_id)
        reset_sms_before = self.sql("SELECT COUNT(*) FROM system_sms_code;")
        missing_status, missing_send = self.call_raw("POST", "/member/auth/send-sms-code", {
            "mobile": "19900001299", "scene": 4,
        })
        assert missing_status == 200 and missing_send.get("code") == 1004001001
        assert self.sql("SELECT COUNT(*) FROM system_sms_code;") == reset_sms_before
        reset_code = self.send_code("", reset_mobile, 4)
        self.call("PUT", "/member/user/reset-password", "", {
            "mobile": reset_mobile, "password": "reset-secret", "code": "000000",
        }, expected=1002014000)
        assert self.sql("SELECT password FROM member_user WHERE id=%d;" % reset_user_id) == before_reset_hash
        self.call("PUT", "/member/user/reset-password", "", {
            "mobile": reset_mobile, "password": "reset-secret", "code": reset_code,
        })
        reset_login = self.call("POST", "/member/auth/login", "", {
            "mobile": reset_mobile, "password": "reset-secret",
        })
        assert reset_login["userId"] == reset_user_id
        assert self.sql("SELECT COUNT(*) FROM system_sms_code WHERE mobile='%s' AND scene=4 AND used=1;"
                        % reset_mobile) == "1"
        return {"profile_update_api_and_sql": True, "phone_update_uses_sms_code": True,
                "old_mobile_login_rejected": True, "new_mobile_login_accepted": True,
                "occupied_mobile_rejected_without_sms_or_member_write": True,
                "invalid_mobile_code_rejected_without_update": True,
                "password_update_uses_sms_code": True, "old_password_login_rejected": True,
                "new_password_login_accepted": True,
                "reset_password_sms_code_rejected_without_write": True,
                "missing_mobile_reset_request_rejected_without_code": True,
                "reset_password_code_consumed": True,
                "new_password_login_accepted_after_reset": True,
                "original_mobile_snapshot": before_mobile}

    def run(self, admin_token: str, app_token: str) -> dict[str, object]:
        config_before = self.sql("SELECT COUNT(*) FROM member_config WHERE deleted=0 AND tenant_id=1;")
        assert config_before == "0", config_before
        config = {
            "pointTradeDeductEnable": True,
            "pointTradeDeductUnitPrice": 12,
            "pointTradeDeductMaxPrice": 240,
            "pointTradeGivePoint": 3,
        }
        self.call("PUT", "/member/config/save", admin_token, config, prefix="/admin-api")
        saved = self.call("GET", "/member/config/get", admin_token, prefix="/admin-api")
        assert saved["pointTradeDeductUnitPrice"] == 12
        assert self.sql("SELECT COUNT(*) FROM member_config WHERE deleted=0 AND tenant_id=1;") == "1"
        updated = dict(config, pointTradeDeductEnable=False, pointTradeGivePoint=5)
        self.call("PUT", "/member/config/save", admin_token, updated, prefix="/admin-api")
        reread = self.call("GET", "/member/config/get", admin_token, prefix="/admin-api")
        assert reread["pointTradeDeductEnable"] is False
        assert reread["pointTradeGivePoint"] == 5
        assert self.sql(
            "SELECT point_trade_deduct_enable+0,point_trade_deduct_unit_price,"
            "point_trade_deduct_max_price,point_trade_give_point "
            "FROM member_config WHERE deleted=0 AND tenant_id=1;"
        ) == "0\t12\t240\t5"

        first = self.call("POST", "/member/address/create", app_token, {
            "name": "P2 first", "mobile": "19900000951", "areaId": 110000,
            "detailAddress": "first address", "defaultStatus": True,
        })
        second = self.call("POST", "/member/address/create", app_token, {
            "name": "P2 second", "mobile": "19900000951", "areaId": 110000,
            "detailAddress": "second address", "defaultStatus": False,
        })
        assert self.sql(
            "SELECT id,default_status+0 FROM member_address WHERE id IN (%d,%d) ORDER BY id;"
            % (first, second)
        ) == "%d\t1\n%d\t0" % (first, second)
        assert self.call("GET", "/member/address/get-default", app_token)["id"] == first

        self.call("PUT", "/member/address/update", app_token, {
            "id": second, "name": "P2 second", "mobile": "19900000951",
            "areaId": 110000, "detailAddress": "second address", "defaultStatus": True,
        })
        assert self.sql(
            "SELECT id,default_status+0 FROM member_address WHERE id IN (%d,%d) ORDER BY id;"
            % (first, second)
        ) == "%d\t0\n%d\t1" % (first, second)
        assert self.call("GET", "/member/address/get-default", app_token)["id"] == second

        self.call("DELETE", "/member/address/delete?id=%d" % second, app_token)
        assert self.call("GET", "/member/address/get-default", app_token) is None
        assert self.sql(
            "SELECT id,default_status+0,deleted+0 FROM member_address WHERE id=%d;" % first
        ) == "%d\t0\t0" % first
        assert self.sql(
            "SELECT deleted+0 FROM member_address WHERE id=%d;" % second
        ) == "1"

        level_id = self.call("POST", "/member/level/create", admin_token, {
            "name": "P2 level", "level": 6, "experience": 60,
            "discountPercent": 90, "icon": "", "backgroundUrl": "", "status": 0,
        }, prefix="/admin-api")
        self.call("PUT", "/member/user/update-level", admin_token, {
            "id": 991202, "levelId": level_id, "reason": "P2 lifecycle grant",
        }, prefix="/admin-api")
        assert self.sql(
            "SELECT level_id,experience FROM member_user WHERE id=991202;"
        ) == "%d\t60" % level_id
        assert self.sql(
            "SELECT level_id,experience,user_experience FROM member_level_record "
            "WHERE user_id=991202 ORDER BY id DESC LIMIT 1;"
        ) == "%d\t60\t60" % level_id
        assert self.sql(
            "SELECT experience,total_experience,biz_type FROM member_experience_record "
            "WHERE user_id=991202 ORDER BY id DESC LIMIT 1;"
        ) == "60\t60\t0"
        self.call("PUT", "/member/user/update-level", admin_token, {
            "id": 991202, "levelId": None, "reason": "P2 lifecycle revoke",
        }, prefix="/admin-api")
        assert self.sql(
            "SELECT level_id,experience FROM member_user WHERE id=991202;"
        ) == "0\t0"
        revoked_level_record = self.sql(
            "SELECT experience,user_experience FROM member_level_record "
            "WHERE user_id=991202 ORDER BY id DESC LIMIT 1;"
        )
        assert revoked_level_record == "-60\t0", revoked_level_record
        assert self.sql(
            "SELECT experience,total_experience,biz_type FROM member_experience_record "
            "WHERE user_id=991202 ORDER BY id DESC LIMIT 1;"
        ) == "-60\t0\t0"
        self.call("DELETE", "/member/level/delete?id=%d" % level_id, admin_token,
                  prefix="/admin-api")
        assert self.sql("SELECT deleted+0 FROM member_level WHERE id=%d;" % level_id) == "1"

        return {
            "config": {"initial_save": True, "update_in_place": True,
                        "single_active_row": True, "sql_consistent": True},
            "addresses": {
                "new_default_clears_previous": True,
                "update_default_clears_previous": True,
                "get_default_follows_active_row": True,
                "deleting_default_leaves_no_default": True,
                "remaining_address_preserved": True,
                "deleted_address_soft_deleted": True,
            },
            "level": {
                "grant_updates_member_and_records": True,
                "revoke_clears_member_level_and_experience": True,
                "level_soft_deleted_after_revoke": True,
            },
            "account": self.exercise_account_lifecycle(app_token),
            "events": self.events,
        }
