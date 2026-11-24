#!/usr/bin/env python3
"""Verify ERP permission and tenant boundaries on one disposable runtime.

The runner creates only disposable tenant users, roles and ERP rows in a
dedicated schema. It never connects to the shared Demo database.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import time
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
REQUIRED_PERMISSIONS = (
    "erp:product:create",
    "erp:product:query",
    "erp:product:update",
    "erp:product:delete",
    "erp:warehouse:create",
    "erp:warehouse:query",
    "erp:warehouse:update",
    "erp:warehouse:delete",
)
FIXTURE_PERMISSIONS = REQUIRED_PERMISSIONS + (
    "erp:product-category:create",
    "erp:product-unit:create",
)
MIN_CHANGESETS = 59
RESERVED_PORTS = {3306, 6379, 48080, 48100, 5173}


def validate_probe_target(schema: str, app_port: int, mysql_port: int, redis_port: int) -> bool:
    if not re.fullmatch(r"yuheng_t4_erp_tenant_[0-9]{8}(?:_[a-z0-9]+)?", schema):
        raise ValueError("only yuheng_t4_erp_tenant_YYYYMMDD[_suffix] schemas are allowed")
    ports = (app_port, mysql_port, redis_port)
    if len(set(ports)) != len(ports) or any(port in RESERVED_PORTS for port in ports):
        raise ValueError("probe ports must be distinct and dedicated")
    if any(port < 1024 or port > 65535 for port in ports):
        raise ValueError("probe ports must be valid unprivileged ports")
    return True


def run(*args: str, input_text: str | None = None, env: dict[str, str] | None = None,
        check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, input=input_text, text=True, capture_output=True,
                          check=check, env=env)


def listening(port: int) -> bool:
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


class Probe:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.events: list[dict[str, object]] = []
        self.tokens: dict[str, str] = {}
        self.permission_ids: list[int] = []

    def sql(self, statement: str) -> str:
        result = run(
            "docker", "exec", "-i", self.args.mysql_container, "sh", "-c",
            'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
            '--skip-column-names -D "$1"', "probe", self.args.schema,
            input_text=statement,
        )
        return result.stdout.strip()

    def call(self, method: str, path: str, token: str | None = None,
             body: dict | None = None, tenant: int | None = None,
             expected: int = 0) -> object:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if tenant is not None:
            headers["tenant-id"] = str(tenant)
        if token:
            headers["Authorization"] = "Bearer " + token
        request = Request(self.args.base_url + "/admin-api" + path, method=method,
                          headers=headers, data=None if body is None else json.dumps(body).encode())
        try:
            response = urlopen(request, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            status = response.status
            payload = json.load(response)
        self.events.append({"method": method, "path": path, "tenant": tenant,
                            "http": status, "code": payload.get("code")})
        assert status == 200 and payload.get("code") == expected, (
            method, path, tenant, status, payload.get("code"), payload.get("msg"))
        return payload.get("data")

    def login(self, username: str, password: str, tenant: int) -> str:
        data = self.call("POST", "/system/auth/login", body={
            "username": username, "password": password}, tenant=tenant)
        return data["accessToken"]  # type: ignore[index]

    def snapshot(self) -> dict[str, str]:
        return {
            table: self.sql(f"SELECT * FROM `{table}` ORDER BY id;")
            for table in ("erp_product", "erp_warehouse")
        }

    def run(self) -> dict[str, object]:
        assert self.sql("SELECT DATABASE();") == self.args.schema
        changesets = int(self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;"))
        assert changesets >= MIN_CHANGESETS, changesets
        assert self.sql("SELECT COUNT(*) FROM system_users WHERE password IS NULL OR password='';") == "0"
        assert self.sql("SELECT id,password FROM system_users WHERE id < 900000 ORDER BY id;") == self.seed_passwords

        for label, tenant in (("one", 121), ("two", 122)):
            self.tokens[label] = self.login(self.users[label][0], self.users[label][1], tenant)
            self.tokens[label + "_denied"] = self.login(
                self.users[label + "_denied"][0], self.users[label + "_denied"][1], tenant
            )

        permission_ids = {
            row.split("\t", 1)[1]: int(row.split("\t", 1)[0])
            for row in self.sql(
                "SELECT id,permission FROM system_menu WHERE deleted=0 "
                "AND permission IN (" + ",".join("'" + permission + "'" for permission in FIXTURE_PERMISSIONS)
                + ");"
            ).splitlines()
        }
        assert set(REQUIRED_PERMISSIONS) <= set(permission_ids), permission_ids

        # The two tenant fixtures are disposable rows in this schema only.
        for label, tenant in (("one", 121), ("two", 122)):
            token = self.tokens[label]
            denied = self.tokens[label + "_denied"]
            prefix = label.upper()
            category = self.call("POST", "/erp/product-category/create", token=token,
                                 tenant=tenant, body={"parentId": 0, "name": prefix + " category",
                                                     "code": prefix + "-CATEGORY", "sort": 1, "status": 0})
            unit = self.call("POST", "/erp/product-unit/create", token=token,
                             tenant=tenant, body={"name": prefix + " unit", "status": 0})
            product_body = {"name": prefix + " product", "barCode": prefix + "-PRODUCT",
                            "categoryId": category, "unitId": unit, "status": 0,
                            "purchasePrice": 10, "salePrice": 20, "minPrice": 1}
            before_denied = self.snapshot()
            self.call("GET", "/erp/product/page?pageNo=1&pageSize=100", token=denied,
                      tenant=tenant, expected=403)
            self.call("GET", "/erp/warehouse/page?pageNo=1&pageSize=100", token=denied,
                      tenant=tenant, expected=403)
            self.call("POST", "/erp/product/create", token=denied, tenant=tenant,
                      body=product_body, expected=403)
            assert self.snapshot() == before_denied
            product = self.call("POST", "/erp/product/create", token=token,
                                tenant=tenant, body=product_body)
            warehouse_body = {"name": prefix + " warehouse", "sort": 1, "status": 0}
            self.call("POST", "/erp/warehouse/create", token=denied, tenant=tenant,
                      body=warehouse_body, expected=403)
            warehouse = self.call("POST", "/erp/warehouse/create", token=token,
                                  tenant=tenant, body=warehouse_body)
            self.call("GET", "/erp/product/get?id=" + str(product), token=token, tenant=tenant)
            self.call("GET", "/erp/warehouse/get?id=" + str(warehouse), token=token, tenant=tenant)
            self.call("GET", "/erp/product/page?pageNo=1&pageSize=100", token=token, tenant=tenant)
            self.call("GET", "/erp/warehouse/page?pageNo=1&pageSize=100", token=token, tenant=tenant)
            before_denied_update = self.snapshot()
            self.call("PUT", "/erp/product/update", token=denied, tenant=tenant,
                      body=dict(product_body, id=product, name=prefix + " denied update"), expected=403)
            self.call("PUT", "/erp/warehouse/update", token=denied, tenant=tenant,
                      body=dict(warehouse_body, id=warehouse, name=prefix + " denied wh"), expected=403)
            self.call("PUT", "/erp/warehouse/update-default-status?" + urlencode(
                {"id": warehouse, "defaultStatus": "true"}), token=denied, tenant=tenant, expected=403)
            assert self.snapshot() == before_denied_update
            self.call("PUT", "/erp/product/update", token=token, tenant=tenant,
                      body=dict(product_body, id=product, name=prefix + " product updated"))
            self.call("PUT", "/erp/warehouse/update", token=token, tenant=tenant,
                      body=dict(warehouse_body, id=warehouse, name=prefix + " wh updated"))
            self.call("PUT", "/erp/warehouse/update-default-status?" + urlencode(
                {"id": warehouse, "defaultStatus": "true"}), token=token, tenant=tenant)
            before_denied_delete = self.snapshot()
            self.call("DELETE", "/erp/product/delete?id=" + str(product), token=denied,
                      tenant=tenant, expected=403)
            self.call("DELETE", "/erp/warehouse/delete?id=" + str(warehouse), token=denied,
                      tenant=tenant, expected=403)
            assert self.snapshot() == before_denied_delete
            self.fixtures[label] = {"tenant": tenant, "product": product, "warehouse": warehouse}

        # Tenant filtering must prevent a valid user from seeing the other tenant's rows.
        for label, foreign_label, tenant in (("one", "two", 121), ("two", "one", 122)):
            token = self.tokens[label]
            foreign = self.fixtures[foreign_label]
            product = self.call("GET", "/erp/product/get?id=" + str(foreign["product"]),
                                token=token, tenant=tenant)
            warehouse = self.call("GET", "/erp/warehouse/get?id=" + str(foreign["warehouse"]),
                                  token=token, tenant=tenant)
            assert product is None and warehouse is None
            pages = self.call("GET", "/erp/product/page?pageNo=1&pageSize=100",
                              token=token, tenant=tenant)
            names = [row["name"] for row in pages["list"]]
            assert all(foreign_label.upper() not in name for name in names)

        before_forged = self.snapshot()
        self.call("GET", "/erp/product/page?pageNo=1&pageSize=100",
                  token=self.tokens["one"], tenant=122, expected=403)
        self.call("PUT", "/erp/warehouse/update-default-status?" + urlencode(
            {"id": self.fixtures["one"]["warehouse"], "defaultStatus": "false"}),
            token=self.tokens["one"], tenant=122, expected=403)
        assert self.snapshot() == before_forged

        for label in ("one", "two"):
            tenant = self.fixtures[label]["tenant"]
            token = self.tokens[label]
            self.call("DELETE", "/erp/product/delete?id=" + str(self.fixtures[label]["product"]),
                      token=token, tenant=tenant)
            self.call("DELETE", "/erp/warehouse/delete?id=" + str(self.fixtures[label]["warehouse"]),
                      token=token, tenant=tenant)
        assert self.sql("SELECT id,password FROM system_users WHERE id < 900000 ORDER BY id;") == self.seed_passwords

        return {
            "result": "PASS",
            "schema": self.args.schema,
            "changesets": changesets,
            "tenants": {"one": 121, "two": 122},
            "fixtures": self.fixtures,
            "permission_contract": list(REQUIRED_PERMISSIONS),
            "seed_passwords_unchanged": True,
            "requests": self.events,
            "limits": ["ERP product and warehouse permissions and tenant boundary only; other ERP controllers remain open.",
                        "ERP template tables expose tenant_id and audit creator fields, but no dept_id/user_id data-scope columns are registered; department and self scopes are outside this ERP probe and remain an explicit template capability boundary.",
                        "External authentication and optional Member integrations are outside this probe."],
        }

    def setup_fixtures(self) -> None:
        self.seed_passwords = self.sql(
            "SELECT id,password FROM system_users WHERE id < 900000 ORDER BY id;")
        suffix = secrets.token_hex(4)
        self.users = {}
        self.fixtures: dict[str, dict[str, object]] = {}
        user_rows = []
        role_rows = []
        role_menu_rows = []
        user_role_rows = []
        for index, (label, tenant) in enumerate((("one", 121), ("two", 122))):
            allowed_id, denied_id = 990820 + index * 10, 990821 + index * 10
            role_id = 990822 + index * 10
            self.users[label] = ("erp" + label + suffix, secrets.token_urlsafe(12)[:16])
            self.users[label + "_denied"] = ("erp" + label + "denied" + suffix, secrets.token_urlsafe(12)[:16])
            allowed_hash = run("htpasswd", "-bnBC", "4", self.users[label][0], self.users[label][1]).stdout.strip().split(":", 1)[1]
            denied_hash = run("htpasswd", "-bnBC", "4", self.users[label + "_denied"][0], self.users[label + "_denied"][1]).stdout.strip().split(":", 1)[1]
            user_rows.extend([
                f"({allowed_id},'{self.users[label][0]}','{allowed_hash}','ERP allowed {label}',NULL,'[]',0,b'0',{tenant})",
                f"({denied_id},'{self.users[label + '_denied'][0]}','{denied_hash}','ERP denied {label}',NULL,'[]',0,b'0',{tenant})",
            ])
            role_rows.append(f"({role_id},'ERP tenant probe {label}','erp_tenant_{label}_{suffix}',1,1,'',0,1,'probe','probe','probe',b'0',{tenant})")
            role_menu_rows.extend(
                f"({990830 + index * 10 + menu_index},{role_id},{permission_id},'probe','probe',b'0',{tenant})"
                for menu_index, permission_id in enumerate(self.permission_ids)
            )
            user_role_rows.append(f"({990840 + index * 10},{allowed_id},{role_id},'probe','probe',b'0',{tenant})")
        self.sql("UPDATE system_tenant SET status=0, expire_time='2099-12-31 00:00:00' WHERE id IN (121,122);")
        self.sql("INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) VALUES "
                 + ",".join(user_rows) + ";")
        self.sql("INSERT INTO system_role (id,name,code,sort,data_scope,data_scope_dept_ids,status,type,remark,creator,updater,deleted,tenant_id) VALUES "
                 + ",".join(role_rows) + ";")
        self.sql("INSERT INTO system_role_menu (id,role_id,menu_id,creator,updater,deleted,tenant_id) VALUES "
                 + ",".join(role_menu_rows) + ";")
        self.sql("INSERT INTO system_user_role (id,user_id,role_id,creator,updater,deleted,tenant_id) VALUES "
                 + ",".join(user_role_rows) + ";")

    def load_permission_ids(self) -> None:
        self.permission_ids = [int(row.split("\t", 1)[0]) for row in self.sql(
            "SELECT id,permission FROM system_menu WHERE deleted=0 AND permission IN (" +
            ",".join("'" + permission + "'" for permission in FIXTURE_PERMISSIONS) +
            ") ORDER BY FIELD(permission," + ",".join("'" + permission + "'" for permission in FIXTURE_PERMISSIONS) + ");"
        ).splitlines()]
        assert len(self.permission_ids) == len(FIXTURE_PERMISSIONS), self.permission_ids


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--mysql-container", required=True)
    parser.add_argument("--app-port", type=int, required=True)
    parser.add_argument("--mysql-port", type=int, required=True)
    parser.add_argument("--redis-port", type=int, required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    url = urlparse(args.base_url)
    if url.scheme != "http" or url.hostname != "127.0.0.1" or url.path or url.query or url.fragment:
        parser.error("use a dedicated loopback HTTP base URL without a path")
    if url.port != args.app_port:
        parser.error("base URL port must match --app-port")
    validate_probe_target(args.schema, args.app_port, args.mysql_port, args.redis_port)
    return args


def main() -> None:
    args = parse_args()
    probe = Probe(args)
    try:
        probe.load_permission_ids()
        probe.setup_fixtures()
        result = probe.run()
    except Exception as error:
        result = {"result": "FAIL", "schema": args.schema, "error": str(error),
                  "requests": probe.events}
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        raise
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"result": result["result"], "requests": len(probe.events),
                      "changesets": result["changesets"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
