#!/usr/bin/env python3
"""Verify ERP document workflows with a limited real role."""

from __future__ import annotations

import argparse
from datetime import datetime
from decimal import Decimal
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


MIN_CHANGESETS = 59
PERMISSIONS = tuple(
    permission
    for document in (
        "purchase-order", "purchase-in", "sale-order", "sale-out",
        "finance-payment", "finance-receipt",
    )
    for permission in (
        f"erp:{document}:create", f"erp:{document}:query",
        f"erp:{document}:export", f"erp:{document}:update-status",
    )
)


def validate_target(schema: str, app_port: int, mysql_port: int, redis_port: int) -> bool:
    if not re.fullmatch(r"yuheng_t4_erp_document_auth_[0-9]{8}(?:_[a-z0-9]+)?", schema):
        raise ValueError("only yuheng_t4_erp_document_auth_YYYYMMDD[_suffix] schemas are allowed")
    ports = (app_port, mysql_port, redis_port)
    if len(set(ports)) != 3 or any(port < 1024 or port > 65535 for port in ports):
        raise ValueError("probe ports must be distinct dedicated unprivileged ports")
    if app_port in {48080, 48100, 5173} or mysql_port == 3306 or redis_port == 6379:
        raise ValueError("probe must not use shared ports")
    return True


class Probe:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.events: list[dict[str, object]] = []

    def sql(self, statement: str) -> str:
        import subprocess

        result = subprocess.run(
            ["docker", "exec", "-i", self.args.mysql_container, "sh", "-c",
             'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
             '--skip-column-names -D "$1"', "probe", self.args.schema],
            input=statement, text=True, capture_output=True, check=False,
        )
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "isolated MySQL statement failed")
        return result.stdout.strip()

    def call(self, method: str, path: str, token: str, body: dict | None = None,
             *, binary: bool = False) -> object:
        headers = {"Accept": "application/json", "Content-Type": "application/json",
                   "tenant-id": "1", "Authorization": "Bearer " + token}
        request = Request(self.args.base_url + "/admin-api" + path, method=method,
                          headers=headers,
                          data=None if body is None else json.dumps(body).encode())
        try:
            response = urlopen(request, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            status = response.status
            content_type = response.headers.get("Content-Type", "")
            raw = response.read()
        event: dict[str, object] = {"method": method, "path": path, "http": status,
                                    "content_type": content_type, "bytes": len(raw)}
        self.events.append(event)
        assert status == 200 and raw, (method, path, status, raw[:200])
        if binary:
            assert len(raw) > 100, (method, path, len(raw))
            return raw
        payload = json.loads(raw)
        event["code"] = payload.get("code")
        assert payload.get("code") == 0, (method, path, payload)
        return payload.get("data")

    def login(self) -> str:
        headers = {"Accept": "application/json", "Content-Type": "application/json",
                   "tenant-id": "1"}
        request = Request(self.args.base_url + "/admin-api/system/auth/login",
                          method="POST", headers=headers,
                          data=json.dumps({
                              "username": os.environ["YUHENG_PROBE_USERNAME"],
                              "password": os.environ["YUHENG_PROBE_PASSWORD"],
                          }).encode())
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
        assert payload.get("code") == 0, payload
        return payload["data"]["accessToken"]

    def document_reads(self, token: str, document: str, identifier: int) -> dict:
        detail = self.call("GET", f"/erp/{document}/get?id={identifier}", token)
        page = self.call("GET", f"/erp/{document}/page?pageNo=1&pageSize=20", token)
        assert page["total"] >= 1, (document, page)
        self.call("GET", f"/erp/{document}/export-excel?pageNo=1&pageSize=20",
                  token, binary=True)
        return {"detail": detail, "page_total": page["total"]}

    def status(self, token: str, document: str, identifier: int) -> None:
        self.call("PUT", f"/erp/{document}/update-status?id={identifier}&status=20", token,
                  {})

    def run(self) -> dict[str, object]:
        assert self.sql("SELECT DATABASE();") == self.args.schema
        changesets = int(self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;"))
        assert changesets >= MIN_CHANGESETS, changesets
        token = self.login()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        purchase_order = self.call("POST", "/erp/purchase-order/create", token, {
            "supplierId": 992301, "accountId": 992303, "orderTime": now,
            "discountPercent": 0, "depositPrice": 0,
            "items": [{"productId": 992305, "productUnitId": 992304,
                        "productPrice": 10, "count": 10, "taxPercent": 0}],
        })
        po = self.document_reads(token, "purchase-order", purchase_order)
        self.status(token, "purchase-order", purchase_order)
        order_item = po["detail"]["items"][0]["id"]
        purchase_in = self.call("POST", "/erp/purchase-in/create", token, {
            "accountId": 992303, "inTime": now, "orderId": purchase_order,
            "discountPercent": 0, "otherPrice": 0,
            "items": [{"orderItemId": order_item, "warehouseId": 992302,
                        "productId": 992305, "productUnitId": 992304,
                        "productPrice": 10, "count": 10, "taxPercent": 0}],
        })
        self.document_reads(token, "purchase-in", purchase_in)
        self.status(token, "purchase-in", purchase_in)

        payment = self.call("POST", "/erp/finance-payment/create", token, {
            "supplierId": 992301, "accountId": 992303, "paymentTime": now,
            "discountPrice": 0,
            "items": [{"bizType": 11, "bizId": purchase_in,
                        "paidPrice": 0, "paymentPrice": 100}],
        })
        self.document_reads(token, "finance-payment", payment)
        self.status(token, "finance-payment", payment)

        sale_order = self.call("POST", "/erp/sale-order/create", token, {
            "customerId": 992306, "accountId": 992303, "orderTime": now,
            "discountPercent": 0, "depositPrice": 0,
            "items": [{"productId": 992305, "productUnitId": 992304,
                        "productPrice": 20, "count": 4, "taxPercent": 0}],
        })
        so = self.document_reads(token, "sale-order", sale_order)
        self.status(token, "sale-order", sale_order)
        sale_item = so["detail"]["items"][0]["id"]
        sale_out = self.call("POST", "/erp/sale-out/create", token, {
            "accountId": 992303, "outTime": now, "orderId": sale_order,
            "discountPercent": 0, "otherPrice": 0,
            "items": [{"orderItemId": sale_item, "warehouseId": 992302,
                        "productId": 992305, "productUnitId": 992304,
                        "productPrice": 20, "count": 4, "taxPercent": 0}],
        })
        self.document_reads(token, "sale-out", sale_out)
        self.status(token, "sale-out", sale_out)

        receipt = self.call("POST", "/erp/finance-receipt/create", token, {
            "customerId": 992306, "accountId": 992303, "receiptTime": now,
            "discountPrice": 0,
            "items": [{"bizType": 21, "bizId": sale_out,
                        "receiptedPrice": 0, "receiptPrice": 80}],
        })
        self.document_reads(token, "finance-receipt", receipt)
        self.status(token, "finance-receipt", receipt)

        assert self.sql("SELECT `count` FROM erp_stock WHERE product_id=992305 AND warehouse_id=992302 AND deleted=0;") == "6.000000"
        assert self.sql("SELECT status FROM erp_purchase_order WHERE id=" + str(purchase_order) + ";") == "20"
        assert self.sql("SELECT status FROM erp_purchase_in WHERE id=" + str(purchase_in) + ";") == "20"
        assert self.sql("SELECT status FROM erp_sale_order WHERE id=" + str(sale_order) + ";") == "20"
        assert self.sql("SELECT status FROM erp_sale_out WHERE id=" + str(sale_out) + ";") == "20"
        assert self.sql("SELECT payment_price FROM erp_finance_payment WHERE id=" + str(payment) + ";") == "100.000000"
        assert self.sql("SELECT receipt_price FROM erp_finance_receipt WHERE id=" + str(receipt) + ";") == "80.000000"
        return {"result": "PASS", "schema": self.args.schema,
                "changesets": changesets, "requests": self.events,
                "limited_role_permissions": list(PERMISSIONS),
                "assertions": {"six_document_create_query_export_status": True,
                                "stock_after_purchase_and_sale": "6.000000",
                                "payment_price": "100.000000", "receipt_price": "80.000000"}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--mysql-container", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    url = urlparse(args.base_url)
    if url.scheme != "http" or url.hostname != "127.0.0.1" or not url.port or url.path or url.query or url.fragment:
        parser.error("use a dedicated loopback HTTP base URL")
    validate_target(args.schema, url.port, 13394, 16475)
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
