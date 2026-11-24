#!/usr/bin/env python3
"""Verify ERP master-data operations for a real limited-permission role."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


MIN_CHANGESETS = 59
PERMISSIONS = (
    "erp:product-category:create", "erp:product-category:query",
    "erp:product-category:update", "erp:product-category:delete",
    "erp:product-unit:create", "erp:product-unit:query",
    "erp:product-unit:update", "erp:product-unit:delete",
    "erp:supplier:create", "erp:supplier:query", "erp:supplier:update",
    "erp:supplier:delete", "erp:customer:create", "erp:customer:query",
    "erp:customer:update", "erp:customer:delete", "erp:account:create",
    "erp:account:query", "erp:account:update", "erp:account:delete",
    "erp:warehouse:create", "erp:warehouse:query", "erp:warehouse:update",
    "erp:warehouse:delete", "erp:product:create", "erp:product:query",
    "erp:product:update", "erp:product:delete",
)


def validate_target(schema: str, port: int) -> bool:
    if not re.fullmatch(r"yuheng_t4_erp_auth_[0-9]{8}(?:_[a-z0-9]+)?", schema):
        raise ValueError("only yuheng_t4_erp_auth_YYYYMMDD[_suffix] schemas are allowed")
    if port in {48080, 48100, 5173} or port < 1024 or port > 65535:
        raise ValueError("probe app port must be a dedicated unprivileged port")
    return True


class Probe:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.events: list[dict[str, object]] = []

    def sql(self, statement: str) -> str:
        import subprocess

        return subprocess.run(
            ["docker", "exec", "-i", self.args.mysql_container, "sh", "-c",
             'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
             '--skip-column-names -D "$1"', "probe", self.args.schema],
            input=statement, text=True, capture_output=True, check=True,
        ).stdout.strip()

    def call(self, method: str, path: str, body: dict | None = None,
             token: str | None = None) -> object:
        headers = {"Accept": "application/json", "Content-Type": "application/json",
                   "tenant-id": "1"}
        if token:
            headers["Authorization"] = "Bearer " + token
        request = Request(self.args.base_url + "/admin-api" + path, method=method,
                          headers=headers,
                          data=None if body is None else json.dumps(body).encode())
        try:
            response = urlopen(request, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            status = response.status
            payload = json.load(response)
        self.events.append({"method": method, "path": path, "http": status,
                            "code": payload.get("code")})
        assert status == 200 and payload.get("code") == 0, (
            method, path, status, payload.get("code"), payload.get("msg"))
        return payload.get("data")

    def login(self) -> str:
        data = self.call("POST", "/system/auth/login", {
            "username": os.environ["YUHENG_PROBE_USERNAME"],
            "password": os.environ["YUHENG_PROBE_PASSWORD"],
        })
        return data["accessToken"]  # type: ignore[index]

    def run(self) -> dict[str, object]:
        assert self.sql("SELECT DATABASE();") == self.args.schema
        changesets = int(self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;"))
        assert changesets >= MIN_CHANGESETS, changesets
        token = self.login()
        suffix = datetime.now().strftime("%H%M%S")

        category = self.call("POST", "/erp/product-category/create", {
            "parentId": 0, "name": "AC" + suffix,
            "code": "AUTH-" + suffix, "sort": 1, "status": 0,
        }, token)
        unit = self.call("POST", "/erp/product-unit/create", {
            "name": "AU" + suffix, "status": 0,
        }, token)
        supplier = self.call("POST", "/erp/supplier/create", {
            "name": "AS" + suffix, "sort": 1, "status": 0,
        }, token)
        customer = self.call("POST", "/erp/customer/create", {
            "name": "ACU" + suffix, "sort": 1, "status": 0,
        }, token)
        account = self.call("POST", "/erp/account/create", {
            "name": "AA" + suffix, "no": "A" + suffix,
            "sort": 1, "status": 0,
        }, token)
        warehouse = self.call("POST", "/erp/warehouse/create", {
            "name": "AW" + suffix, "sort": 1, "status": 0,
        }, token)
        product_body = {
            "name": "AP" + suffix, "barCode": "AUTH" + suffix,
            "categoryId": category, "unitId": unit, "status": 0,
            "purchasePrice": 10, "salePrice": 20, "minPrice": 1,
        }
        product = self.call("POST", "/erp/product/create", product_body, token)

        for resource, identifier in (
            ("product-category", category), ("product-unit", unit),
            ("supplier", supplier), ("customer", customer),
            ("account", account), ("warehouse", warehouse),
            ("product", product),
        ):
            self.call("GET", f"/erp/{resource}/get?id={identifier}", token=token)
            self.call("GET", f"/erp/{resource}/simple-list", token=token)

        self.call("GET", "/erp/product-category/list?status=0", token=token)
        self.call("GET", "/erp/product-unit/page?pageNo=1&pageSize=20", token=token)
        self.call("GET", "/erp/supplier/page?pageNo=1&pageSize=20", token=token)
        self.call("GET", "/erp/customer/page?pageNo=1&pageSize=20", token=token)
        self.call("GET", "/erp/account/page?pageNo=1&pageSize=20", token=token)
        self.call("GET", "/erp/warehouse/page?pageNo=1&pageSize=20", token=token)
        self.call("GET", "/erp/product/page?pageNo=1&pageSize=20", token=token)

        self.call("PUT", "/erp/product-category/update", {
            "id": category, "parentId": 0, "name": "ACU" + suffix,
            "code": "AUTH-" + suffix, "sort": 2, "status": 0,
        }, token)
        self.call("PUT", "/erp/product-unit/update", {
            "id": unit, "name": "AUU" + suffix, "status": 0,
        }, token)
        self.call("PUT", "/erp/supplier/update", {
            "id": supplier, "name": "ASU" + suffix,
            "sort": 2, "status": 0,
        }, token)
        self.call("PUT", "/erp/customer/update", {
            "id": customer, "name": "ACUU" + suffix,
            "sort": 2, "status": 0,
        }, token)
        self.call("PUT", "/erp/account/update", {
            "id": account, "name": "AAU" + suffix,
            "no": "B" + suffix, "sort": 2, "status": 0,
        }, token)
        self.call("PUT", "/erp/warehouse/update", {
            "id": warehouse, "name": "AWU" + suffix,
            "sort": 2, "status": 0,
        }, token)
        self.call("PUT", "/erp/warehouse/update-default-status?" + urlencode({
            "id": warehouse, "defaultStatus": "true",
        }), token=token)
        self.call("PUT", "/erp/product/update", {
            **product_body, "id": product, "name": "APU" + suffix,
        }, token)

        for resource, identifier in (
            ("product", product), ("warehouse", warehouse),
            ("account", account), ("customer", customer),
            ("supplier", supplier), ("product-unit", unit),
            ("product-category", category),
        ):
            self.call("DELETE", f"/erp/{resource}/delete?id={identifier}", token=token)

        deleted = {}
        for table, identifier in (
            ("erp_product", product), ("erp_warehouse", warehouse),
            ("erp_account", account), ("erp_customer", customer),
            ("erp_supplier", supplier), ("erp_product_unit", unit),
            ("erp_product_category", category),
        ):
            deleted[table] = self.sql(
                f"SELECT deleted+0 FROM `{table}` WHERE id={int(identifier)};") == "1"
        assert all(deleted.values()), deleted
        return {
            "result": "PASS", "schema": self.args.schema,
            "changesets": changesets, "requests": self.events,
            "limited_role_permissions": list(PERMISSIONS),
            "all_created_master_rows_soft_deleted": True,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--mysql-container", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    url = urlparse(args.base_url)
    if url.scheme != "http" or url.hostname != "127.0.0.1" or not url.port or url.path or url.query or url.fragment:
        parser.error("use a dedicated loopback HTTP base URL without a path")
    validate_target(args.schema, url.port)
    probe = Probe(args)
    try:
        result = probe.run()
    except Exception as error:
        result = {"result": "FAIL", "schema": args.schema,
                  "error": str(error), "requests": probe.events}
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        raise
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"result": result["result"], "requests": len(result["requests"])}))


if __name__ == "__main__":
    main()
