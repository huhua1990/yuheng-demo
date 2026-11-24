#!/usr/bin/env python3
"""Verify ERP update/delete permissions on real draft documents."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

MIN_CHANGESETS = 59
DOCUMENTS = (
    "purchase-order", "purchase-in", "purchase-return", "sale-order", "sale-out",
    "sale-return", "stock-in", "stock-out", "stock-check", "stock-move",
    "finance-payment", "finance-receipt",
)
PERMISSIONS = tuple(
    f"erp:{document}:{action}"
    for document in DOCUMENTS
    for action in ("create", "query", "export", "update", "update-status", "delete")
)


def validate_target(schema: str, app_port: int, mysql_port: int, redis_port: int) -> bool:
    if not re.fullmatch(r"yuheng_t4_erp_mutation_auth_[0-9]{8}(?:_[a-z0-9]+)?", schema):
        raise ValueError("only yuheng_t4_erp_mutation_auth_YYYYMMDD[_suffix] schemas are allowed")
    ports = (app_port, mysql_port, redis_port)
    if len(set(ports)) != 3 or any(port < 1024 or port > 65535 for port in ports):
        raise ValueError("probe ports must be distinct dedicated unprivileged ports")
    if app_port in {48080, 48100, 5173} or mysql_port == 3306 or redis_port == 6379:
        raise ValueError("probe must not use shared ports")
    return True


class Probe:
    def __init__(self, args):
        self.args = args
        self.events = []

    def sql(self, statement):
        import subprocess
        result = subprocess.run(
            ["docker", "exec", "-i", self.args.mysql_container, "sh", "-c",
             'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw --skip-column-names -D "$1"',
             "probe", self.args.schema], input=statement, text=True,
            capture_output=True, check=False)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "isolated MySQL statement failed")
        return result.stdout.strip()

    def call(self, method, path, token, body=None):
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
        assert status == 200 and payload.get("code") == 0, (method, path, status, payload)
        return payload.get("data")

    def login(self):
        return self.call("POST", "/system/auth/login", None, {
            "username": os.environ["YUHENG_PROBE_USERNAME"],
            "password": os.environ["YUHENG_PROBE_PASSWORD"],
        })["accessToken"]

    def create(self, token, document, body):
        return self.call("POST", f"/erp/{document}/create", token, body)

    def update_delete(self, token, document, identifier, body, table):
        self.call("PUT", f"/erp/{document}/update", token, dict(body, id=identifier))
        self.call("DELETE", f"/erp/{document}/delete?ids={identifier}", token)
        assert self.sql(f"SELECT deleted+0 FROM {table} WHERE id={int(identifier)};") == "1", document

    def status(self, token, document, identifier, status=20):
        self.call("PUT", f"/erp/{document}/update-status?id={identifier}&status={status}", token, {})

    def run(self):
        assert self.sql("SELECT DATABASE();") == self.args.schema
        changesets = int(self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;"))
        assert changesets >= MIN_CHANGESETS, changesets
        token = self.login()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        supplier, customer, account = 992501, 992506, 992503
        warehouse, warehouse2, unit, product = 992502, 992507, 992504, 992505

        po_body = {"supplierId": supplier, "accountId": account, "orderTime": now,
                   "discountPercent": 0, "depositPrice": 0,
                   "items": [{"productId": product, "productUnitId": unit,
                              "productPrice": 10, "count": 10, "taxPercent": 0}]}
        po = self.create(token, "purchase-order", po_body)
        po_data = self.call("GET", f"/erp/purchase-order/get?id={po}", token)
        self.update_delete(token, "purchase-order", po, dict(po_body, discountPercent=1), "erp_purchase_order")
        # Recreate a valid source chain after testing deletion.
        po = self.create(token, "purchase-order", po_body)
        po_data = self.call("GET", f"/erp/purchase-order/get?id={po}", token)
        self.status(token, "purchase-order", po)
        po_item = po_data["items"][0]["id"]
        in_body = {"accountId": account, "inTime": now, "orderId": po,
                   "discountPercent": 0, "otherPrice": 0,
                   "items": [{"orderItemId": po_item, "warehouseId": warehouse,
                              "productId": product, "productUnitId": unit,
                              "productPrice": 10, "count": 10, "taxPercent": 0}]}
        pin = self.create(token, "purchase-in", in_body)
        self.update_delete(token, "purchase-in", pin, in_body, "erp_purchase_in")
        pin = self.create(token, "purchase-in", in_body)
        self.status(token, "purchase-in", pin)

        so_body = {"customerId": customer, "accountId": account, "orderTime": now,
                   "discountPercent": 0, "depositPrice": 0,
                   "items": [{"productId": product, "productUnitId": unit,
                              "productPrice": 20, "count": 4, "taxPercent": 0}]}
        so = self.create(token, "sale-order", so_body)
        so_data = self.call("GET", f"/erp/sale-order/get?id={so}", token)
        self.update_delete(token, "sale-order", so, dict(so_body, discountPercent=1), "erp_sale_order")
        so = self.create(token, "sale-order", so_body)
        so_data = self.call("GET", f"/erp/sale-order/get?id={so}", token)
        self.status(token, "sale-order", so)
        so_item = so_data["items"][0]["id"]
        out_body = {"accountId": account, "outTime": now, "orderId": so,
                    "discountPercent": 0, "otherPrice": 0,
                    "items": [{"orderItemId": so_item, "warehouseId": warehouse,
                               "productId": product, "productUnitId": unit,
                               "productPrice": 20, "count": 4, "taxPercent": 0}]}
        pout = self.create(token, "sale-out", out_body)
        self.update_delete(token, "sale-out", pout, out_body, "erp_sale_out")
        pout = self.create(token, "sale-out", out_body)
        self.status(token, "sale-out", pout)

        pr_body = {"supplierId": supplier, "accountId": account, "returnTime": now,
                   "orderId": po, "discountPercent": 0, "otherPrice": 0,
                   "items": [{"orderItemId": po_item, "warehouseId": warehouse,
                              "productId": product, "productUnitId": unit,
                              "productPrice": 10, "count": 1, "taxPercent": 0}]}
        pr = self.create(token, "purchase-return", pr_body)
        self.update_delete(token, "purchase-return", pr, pr_body, "erp_purchase_return")
        sr_body = {"customerId": customer, "accountId": account, "returnTime": now,
                   "orderId": so, "discountPercent": 0, "otherPrice": 0,
                   "items": [{"orderItemId": so_item, "warehouseId": warehouse,
                              "productId": product, "productUnitId": unit,
                              "productPrice": 20, "count": 1, "taxPercent": 0}]}
        sr = self.create(token, "sale-return", sr_body)
        self.update_delete(token, "sale-return", sr, sr_body, "erp_sale_return")

        stock_bodies = {
            "stock-in": ({"supplierId": supplier, "inTime": now,
                          "items": [{"warehouseId": warehouse, "productId": product, "productPrice": 10, "count": 1}]}, "erp_stock_in"),
            "stock-out": ({"customerId": customer, "outTime": now,
                           "items": [{"warehouseId": warehouse, "productId": product, "productPrice": 10, "count": 1}]}, "erp_stock_out"),
            "stock-check": ({"checkTime": now,
                             "items": [{"warehouseId": warehouse2, "productId": product, "productUnitId": unit, "productPrice": 10, "stockCount": 0, "actualCount": 0, "count": 0}]}, "erp_stock_check"),
            "stock-move": ({"moveTime": now,
                            "items": [{"fromWarehouseId": warehouse, "toWarehouseId": warehouse2, "productId": product, "productUnitId": unit, "productPrice": 10, "count": 1}]}, "erp_stock_move"),
        }
        for document, (body, table) in stock_bodies.items():
            identifier = self.create(token, document, body)
            self.update_delete(token, document, identifier, body, table)

        payment_body = {"supplierId": supplier, "accountId": account, "paymentTime": now,
                        "discountPrice": 0, "items": [{"bizType": 11, "bizId": pin, "paidPrice": 0, "paymentPrice": 1}]}
        payment = self.create(token, "finance-payment", payment_body)
        self.update_delete(token, "finance-payment", payment, payment_body, "erp_finance_payment")
        receipt_body = {"customerId": customer, "accountId": account, "receiptTime": now,
                        "discountPrice": 0, "items": [{"bizType": 21, "bizId": pout, "receiptedPrice": 0, "receiptPrice": 1}]}
        receipt = self.create(token, "finance-receipt", receipt_body)
        self.update_delete(token, "finance-receipt", receipt, receipt_body, "erp_finance_receipt")
        return {"result": "PASS", "schema": self.args.schema, "changesets": changesets,
                "requests": self.events, "limited_role_permissions": list(PERMISSIONS),
                "assertions": {"all_document_update_delete": True,
                                "draft_rows_soft_deleted": True,
                                "source_chains_remained_valid": True}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--mysql-container", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    url = urlparse(args.base_url)
    if url.scheme != "http" or url.hostname != "127.0.0.1" or not url.port or url.path or url.query or url.fragment:
        parser.error("use a dedicated loopback HTTP base URL")
    validate_target(args.schema, url.port, 13396, 16477)
    probe = Probe(args)
    try:
        result = probe.run()
    except Exception as error:
        result = {"result": "FAIL", "schema": args.schema, "error": str(error), "requests": probe.events}
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        raise
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"result": result["result"], "requests": len(result["requests"])}))


if __name__ == "__main__":
    main()
