#!/usr/bin/env python3
"""Exercise ERP method-security boundaries with a real no-role account.

The probe assumes a disposable schema containing the normal platform and ERP
Liquibase changesets. It creates ERP rows through an isolated admin fixture,
then checks every ERP controller's representative read/write/status/export
entry point with a real authenticated account that has no role. The response
and a complete ERP table snapshot are recorded without credentials or tokens.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import socket
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from erp_workflow_probe import Probe


RESERVED_PORTS = {3306, 6379, 48080, 48100, 5173}
MIN_CHANGESETS = 59


def validate_probe_target(schema: str, app_port: int, mysql_port: int, redis_port: int) -> bool:
    if not re.fullmatch(r"yuheng_t4_erp_acl_[0-9]{8}(?:_[a-z0-9]+)?", schema):
        raise ValueError("only yuheng_t4_erp_acl_YYYYMMDD[_suffix] schemas are allowed")
    ports = (app_port, mysql_port, redis_port)
    if len(set(ports)) != len(ports) or any(port in RESERVED_PORTS for port in ports):
        raise ValueError("probe ports must be distinct and dedicated")
    if any(port < 1024 or port > 65535 for port in ports):
        raise ValueError("probe ports must be valid unprivileged ports")
    return True


ERP_TABLES = (
    "erp_product_category", "erp_product_unit", "erp_product", "erp_supplier",
    "erp_customer", "erp_account", "erp_warehouse", "erp_stock",
    "erp_stock_record", "erp_purchase_order", "erp_purchase_order_items",
    "erp_purchase_in", "erp_purchase_in_items", "erp_purchase_return",
    "erp_purchase_return_items", "erp_sale_order", "erp_sale_order_items",
    "erp_sale_out", "erp_sale_out_items", "erp_sale_return",
    "erp_sale_return_items", "erp_stock_in", "erp_stock_in_item",
    "erp_stock_out", "erp_stock_out_item", "erp_stock_check",
    "erp_stock_check_item", "erp_stock_move", "erp_stock_move_item",
    "erp_finance_payment", "erp_finance_payment_item", "erp_finance_receipt",
    "erp_finance_receipt_item",
)


READ_CASES = (
    ("product", "/erp/product/get?id=1", "/erp/product/page?pageNo=1&pageSize=10",
     "/erp/product/simple-list", "/erp/product/export-excel"),
    ("product-category", "/erp/product-category/get?id=1", "/erp/product-category/list",
     "/erp/product-category/simple-list", "/erp/product-category/export-excel"),
    ("product-unit", "/erp/product-unit/get?id=1", "/erp/product-unit/page?pageNo=1&pageSize=10",
     "/erp/product-unit/simple-list", "/erp/product-unit/export-excel"),
    ("supplier", "/erp/supplier/get?id=1", "/erp/supplier/page?pageNo=1&pageSize=10",
     "/erp/supplier/simple-list", "/erp/supplier/export-excel"),
    ("customer", "/erp/customer/get?id=1", "/erp/customer/page?pageNo=1&pageSize=10",
     "/erp/customer/simple-list", "/erp/customer/export-excel"),
    ("account", "/erp/account/get?id=1", "/erp/account/page?pageNo=1&pageSize=10",
     "/erp/account/simple-list", "/erp/account/export-excel"),
    ("warehouse", "/erp/warehouse/get?id=1", "/erp/warehouse/page?pageNo=1&pageSize=10",
     "/erp/warehouse/simple-list", "/erp/warehouse/export-excel"),
    ("stock", "/erp/stock/get?id=1", "/erp/stock/page?pageNo=1&pageSize=10",
     "/erp/stock/get-count?productId=1", "/erp/stock/export-excel"),
    ("stock-record", "/erp/stock-record/get?id=1", "/erp/stock-record/page?pageNo=1&pageSize=10",
     None, "/erp/stock-record/export-excel"),
    ("purchase-order", "/erp/purchase-order/get?id=1", "/erp/purchase-order/page?pageNo=1&pageSize=10",
     None, "/erp/purchase-order/export-excel"),
    ("purchase-in", "/erp/purchase-in/get?id=1", "/erp/purchase-in/page?pageNo=1&pageSize=10",
     None, "/erp/purchase-in/export-excel"),
    ("purchase-return", "/erp/purchase-return/get?id=1", "/erp/purchase-return/page?pageNo=1&pageSize=10",
     None, "/erp/purchase-return/export-excel"),
    ("sale-order", "/erp/sale-order/get?id=1", "/erp/sale-order/page?pageNo=1&pageSize=10",
     None, "/erp/sale-order/export-excel"),
    ("sale-out", "/erp/sale-out/get?id=1", "/erp/sale-out/page?pageNo=1&pageSize=10",
     None, "/erp/sale-out/export-excel"),
    ("sale-return", "/erp/sale-return/get?id=1", "/erp/sale-return/page?pageNo=1&pageSize=10",
     None, "/erp/sale-return/export-excel"),
    ("stock-in", "/erp/stock-in/get?id=1", "/erp/stock-in/page?pageNo=1&pageSize=10",
     None, "/erp/stock-in/export-excel"),
    ("stock-out", "/erp/stock-out/get?id=1", "/erp/stock-out/page?pageNo=1&pageSize=10",
     None, "/erp/stock-out/export-excel"),
    ("stock-check", "/erp/stock-check/get?id=1", "/erp/stock-check/page?pageNo=1&pageSize=10",
     None, "/erp/stock-check/export-excel"),
    ("stock-move", "/erp/stock-move/get?id=1", "/erp/stock-move/page?pageNo=1&pageSize=10",
     None, "/erp/stock-move/export-excel"),
    ("finance-payment", "/erp/finance-payment/get?id=1", "/erp/finance-payment/page?pageNo=1&pageSize=10",
     None, "/erp/finance-payment/export-excel"),
    ("finance-receipt", "/erp/finance-receipt/get?id=1", "/erp/finance-receipt/page?pageNo=1&pageSize=10",
     None, "/erp/finance-receipt/export-excel"),
)

DOCUMENTS = (
    "purchase-order", "purchase-in", "purchase-return", "sale-order", "sale-out",
    "sale-return", "stock-in", "stock-out", "stock-check", "stock-move",
    "finance-payment", "finance-receipt",
)

WRITE_BODIES = {
    "purchase-order": {
        "supplierId": 1, "orderTime": "2026-11-22T00:00:00",
        "items": [{"productId": 1, "productUnitId": 1, "count": 1}],
    },
    "purchase-in": {
        "inTime": "2026-11-22T00:00:00", "orderId": 1,
        "items": [{"orderItemId": 1, "warehouseId": 1, "productId": 1,
                   "productUnitId": 1, "count": 1}],
    },
    "purchase-return": {
        "returnTime": "2026-11-22T00:00:00", "orderId": 1,
        "items": [{"orderItemId": 1, "warehouseId": 1, "productId": 1,
                   "productUnitId": 1, "count": 1}],
    },
    "sale-order": {
        "customerId": 1, "orderTime": "2026-11-22T00:00:00",
        "items": [{"productId": 1, "productUnitId": 1, "count": 1}],
    },
    "sale-out": {
        "outTime": "2026-11-22T00:00:00", "orderId": 1,
        "items": [{"orderItemId": 1, "warehouseId": 1, "productId": 1,
                   "productUnitId": 1, "count": 1}],
    },
    "sale-return": {
        "returnTime": "2026-11-22T00:00:00", "orderId": 1,
        "items": [{"orderItemId": 1, "warehouseId": 1, "productId": 1,
                   "productUnitId": 1, "count": 1}],
    },
    "stock-in": {
        "inTime": "2026-11-22T00:00:00",
        "items": [{"warehouseId": 1, "productId": 1, "count": 1}],
    },
    "stock-out": {
        "outTime": "2026-11-22T00:00:00",
        "items": [{"warehouseId": 1, "productId": 1, "count": 1}],
    },
    "stock-check": {
        "checkTime": "2026-11-22T00:00:00",
        "items": [{"warehouseId": 1, "productId": 1, "stockCount": 0,
                   "actualCount": 0, "count": 0}],
    },
    "stock-move": {
        "moveTime": "2026-11-22T00:00:00",
        "items": [{"fromWarehouseId": 1, "toWarehouseId": 2,
                   "productId": 1, "count": 1}],
    },
    "finance-payment": {
        "paymentTime": "2026-11-22T00:00:00", "supplierId": 1,
        "accountId": 1, "discountPrice": 0,
        "items": [{"bizType": 11, "bizId": 1, "paidPrice": 0,
                   "paymentPrice": 1}],
    },
    "finance-receipt": {
        "receiptTime": "2026-11-22T00:00:00", "customerId": 1,
        "accountId": 1, "discountPrice": 0,
        "items": [{"bizType": 21, "bizId": 1, "receiptedPrice": 0,
                   "receiptPrice": 1}],
    },
}


class PermissionProbe(Probe):
    def __init__(self, args: argparse.Namespace):
        super().__init__(args)
        self.events = []
        self.token = ""

    def snapshot(self) -> dict[str, str]:
        return {table: self.sql(f"SELECT * FROM `{table}` ORDER BY id;") for table in ERP_TABLES}

    def call(self, method: str, path: str, body: dict | None = None, expected: int = 0,
             token: str | None = None, record: bool = True) -> object:
        headers = {"Accept": "application/json", "Content-Type": "application/json", "tenant-id": "1"}
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
            content_type = response.headers.get("Content-Type", "")
            if "json" in content_type:
                payload = json.load(response)
            else:
                payload = {"code": 0 if status == 200 else status, "body_sha256": hashlib.sha256(response.read()).hexdigest()}
        if record:
            self.events.append({"method": method, "path": path, "http": status,
                                "code": payload.get("code"), "body_sha256": payload.get("body_sha256")})
        assert status == 200 and payload.get("code") == expected, (
            method, path, status, payload.get("code"), payload.get("msg"))
        return payload.get("data")

    def login(self, username: str, password: str) -> str:
        data = self.call("POST", "/system/auth/login", {"username": username, "password": password})
        return data["accessToken"]  # type: ignore[index]

    def setup_data(self) -> None:
        self.admin_token = self.login(os.environ["YUHENG_PROBE_USERNAME"], os.environ["YUHENG_PROBE_PASSWORD"])
        category = self.call("POST", "/erp/product-category/create", {"parentId": 0, "name": "ACL category", "code": "ACL", "sort": 1, "status": 0}, token=self.admin_token)
        unit = self.call("POST", "/erp/product-unit/create", {"name": "ACL unit", "status": 0}, token=self.admin_token)
        self.call("POST", "/erp/supplier/create", {"name": "ACL supplier", "sort": 1, "status": 0}, token=self.admin_token)
        self.call("POST", "/erp/customer/create", {"name": "ACL customer", "sort": 1, "status": 0}, token=self.admin_token)
        self.call("POST", "/erp/account/create", {"name": "ACL account", "no": "ACL", "sort": 1, "status": 0}, token=self.admin_token)
        self.call("POST", "/erp/warehouse/create", {"name": "ACL warehouse", "sort": 1, "status": 0}, token=self.admin_token)
        self.call("POST", "/erp/product/create", {"name": "ACL product", "barCode": "ACL", "categoryId": category, "unitId": unit, "status": 0, "purchasePrice": 10, "salePrice": 20, "minPrice": 1}, token=self.admin_token)

    def run(self) -> dict[str, object]:
        assert self.sql("SELECT DATABASE();") == self.args.schema
        self.installed_changesets(self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;"))
        self.setup_data()
        self.token = self.login(os.environ["YUHENG_PROBE_NO_ROLE_USERNAME"], os.environ["YUHENG_PROBE_NO_ROLE_PASSWORD"])
        before = self.snapshot()
        protected = []
        unprotected = []
        for name, get_path, page_path, simple_path, export_path in READ_CASES:
            for path in (get_path, page_path, export_path):
                self.call("GET", path, token=self.token, expected=403)
                protected.append(path)
                assert self.snapshot() == before, path
            if simple_path is not None:
                self.call("GET", simple_path, token=self.token, expected=0)
                unprotected.append(simple_path)
        for resource in DOCUMENTS:
            base = "/erp/" + resource
            delete_param = "ids=1" if resource in {
                "purchase-order", "purchase-in", "purchase-return", "sale-order", "sale-out",
                "sale-return", "stock-in", "stock-out", "stock-check", "stock-move",
                "finance-payment", "finance-receipt",
            } else "id=1"
            for path in (base + "/create", base + "/update", base + "/update-status?id=1&status=20", base + "/delete?" + delete_param):
                body = None
                if path.endswith("/create"):
                    body = WRITE_BODIES[resource]
                elif path.endswith("/update"):
                    body = dict(WRITE_BODIES[resource], id=1)
                self.call("POST" if path.endswith("/create") else "PUT" if "/update" in path else "DELETE",
                          path, body=body,
                          token=self.token, expected=403)
                protected.append(path)
                assert self.snapshot() == before, path
        return {
            "result": "PASS",
            "schema": self.args.schema,
            "requests": self.events,
            "protected_denials": len(protected),
            "authenticated_without_erp_permission": unprotected,
            "erp_snapshot_unchanged_after_denials": True,
            "limits": ["Simple-list and stock get-count follow the upstream controller contract and are authenticated but lack method-level ERP permission annotations.", "This probe verifies method-security boundaries; it does not prove every data-scope combination."],
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
        parser.error("use a dedicated loopback HTTP port without path or credentials")
    if not re.fullmatch(r"yuheng_t4_erp_acl_[0-9]{8}(?:_[a-z0-9]+)?", args.schema):
        parser.error("only yuheng_t4_erp_acl_YYYYMMDD[_suffix] disposable schemas are allowed")
    probe = PermissionProbe(args)
    try:
        result = probe.run()
    except Exception as error:
        args.output.write_text(json.dumps({"result": "FAIL", "error": str(error), "requests": probe.events}, ensure_ascii=False, indent=2) + "\n")
        raise
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"result": result["result"], "requests": len(result["requests"]), "protected_denials": result["protected_denials"]}))


if __name__ == "__main__":
    main()
