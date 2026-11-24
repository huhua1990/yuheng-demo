#!/usr/bin/env python3
"""Verify ERP returns and stock auxiliary documents with a limited role."""

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
    "purchase-order", "purchase-in", "purchase-return",
    "sale-order", "sale-out", "sale-return",
    "stock-in", "stock-out", "stock-check", "stock-move",
)
PERMISSIONS = tuple(
    permission
    for document in DOCUMENTS
    for permission in (
        f"erp:{document}:create", f"erp:{document}:query",
        f"erp:{document}:export", f"erp:{document}:update-status",
    )
)


def validate_target(schema: str, app_port: int, mysql_port: int, redis_port: int) -> bool:
    if not re.fullmatch(r"yuheng_t4_erp_aux_auth_[0-9]{8}(?:_[a-z0-9]+)?", schema):
        raise ValueError("only yuheng_t4_erp_aux_auth_YYYYMMDD[_suffix] schemas are allowed")
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

    def reads(self, token: str, document: str, identifier: int) -> dict:
        detail = self.call("GET", f"/erp/{document}/get?id={identifier}", token)
        page = self.call("GET", f"/erp/{document}/page?pageNo=1&pageSize=20", token)
        assert page["total"] >= 1, (document, page)
        self.call("GET", f"/erp/{document}/export-excel?pageNo=1&pageSize=20",
                  token, binary=True)
        return {"detail": detail, "page_total": page["total"]}

    def approve(self, token: str, document: str, identifier: int) -> None:
        self.call("PUT", f"/erp/{document}/update-status?id={identifier}&status=20", token, {})

    def stock(self) -> str:
        return self.sql("SELECT warehouse_id,`count` FROM erp_stock "
                        "WHERE deleted=0 ORDER BY warehouse_id;")

    def run(self) -> dict[str, object]:
        assert self.sql("SELECT DATABASE();") == self.args.schema
        changesets = int(self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;"))
        assert changesets >= MIN_CHANGESETS, changesets
        token = self.login()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # The fixture IDs are inserted by the isolated runner. This role has no
        # master-data permissions, so creating those rows through HTTP would test
        # the wrong contract.
        supplier, customer, account, warehouse1, warehouse2, unit, product = (
            992401, 992406, 992403, 992402, 992407, 992404, 992405)

        purchase_order = self.call("POST", "/erp/purchase-order/create", token, {
            "supplierId": supplier, "accountId": account, "orderTime": now,
            "discountPercent": 0, "depositPrice": 0,
            "items": [{"productId": product, "productUnitId": unit,
                        "productPrice": 10, "count": 10, "taxPercent": 0}],
        })
        po = self.reads(token, "purchase-order", purchase_order)
        self.approve(token, "purchase-order", purchase_order)
        po_item = po["detail"]["items"][0]["id"]
        purchase_in = self.call("POST", "/erp/purchase-in/create", token, {
            "accountId": account, "inTime": now, "orderId": purchase_order,
            "discountPercent": 0, "otherPrice": 0,
            "items": [{"orderItemId": po_item, "warehouseId": warehouse1,
                        "productId": product, "productUnitId": unit,
                        "productPrice": 10, "count": 10, "taxPercent": 0}],
        })
        self.reads(token, "purchase-in", purchase_in)
        self.approve(token, "purchase-in", purchase_in)

        sale_order = self.call("POST", "/erp/sale-order/create", token, {
            "customerId": customer, "accountId": account, "orderTime": now,
            "discountPercent": 0, "depositPrice": 0,
            "items": [{"productId": product, "productUnitId": unit,
                        "productPrice": 20, "count": 4, "taxPercent": 0}],
        })
        so = self.reads(token, "sale-order", sale_order)
        self.approve(token, "sale-order", sale_order)
        so_item = so["detail"]["items"][0]["id"]
        sale_out = self.call("POST", "/erp/sale-out/create", token, {
            "accountId": account, "outTime": now, "orderId": sale_order,
            "discountPercent": 0, "otherPrice": 0,
            "items": [{"orderItemId": so_item, "warehouseId": warehouse1,
                        "productId": product, "productUnitId": unit,
                        "productPrice": 20, "count": 4, "taxPercent": 0}],
        })
        self.reads(token, "sale-out", sale_out)
        self.approve(token, "sale-out", sale_out)
        assert self.stock() == f"{warehouse1}\t6.000000"

        purchase_return = self.call("POST", "/erp/purchase-return/create", token, {
            "supplierId": supplier, "accountId": account, "returnTime": now,
            "orderId": purchase_order, "discountPercent": 0, "otherPrice": 0,
            "items": [{"orderItemId": po_item, "warehouseId": warehouse1,
                        "productId": product, "productUnitId": unit,
                        "productPrice": 10, "count": 2, "taxPercent": 0}],
        })
        self.reads(token, "purchase-return", purchase_return)
        self.approve(token, "purchase-return", purchase_return)
        assert self.stock() == f"{warehouse1}\t4.000000"

        sale_return = self.call("POST", "/erp/sale-return/create", token, {
            "customerId": customer, "accountId": account, "returnTime": now,
            "orderId": sale_order, "discountPercent": 0, "otherPrice": 0,
            "items": [{"orderItemId": so_item, "warehouseId": warehouse1,
                        "productId": product, "productUnitId": unit,
                        "productPrice": 20, "count": 1, "taxPercent": 0}],
        })
        self.reads(token, "sale-return", sale_return)
        self.approve(token, "sale-return", sale_return)
        assert self.stock() == f"{warehouse1}\t5.000000"

        stock_in = self.call("POST", "/erp/stock-in/create", token, {
            "supplierId": supplier, "inTime": now,
            "items": [{"warehouseId": warehouse1, "productId": product,
                        "productPrice": 10, "count": 3}],
        })
        self.reads(token, "stock-in", stock_in)
        self.approve(token, "stock-in", stock_in)
        assert self.stock() == f"{warehouse1}\t8.000000"

        stock_out = self.call("POST", "/erp/stock-out/create", token, {
            "customerId": customer, "outTime": now,
            "items": [{"warehouseId": warehouse1, "productId": product,
                        "productPrice": 10, "count": 2}],
        })
        self.reads(token, "stock-out", stock_out)
        self.approve(token, "stock-out", stock_out)
        assert self.stock() == f"{warehouse1}\t6.000000"

        stock_move = self.call("POST", "/erp/stock-move/create", token, {
            "moveTime": now,
            "items": [{"fromWarehouseId": warehouse1, "toWarehouseId": warehouse2,
                        "productId": product, "productUnitId": unit,
                        "productPrice": 10, "count": 2}],
        })
        self.reads(token, "stock-move", stock_move)
        self.approve(token, "stock-move", stock_move)
        assert self.stock() == f"{warehouse1}\t4.000000\n{warehouse2}\t2.000000"

        stock_check = self.call("POST", "/erp/stock-check/create", token, {
            "checkTime": now,
            "items": [{"warehouseId": warehouse2, "productId": product,
                        "productUnitId": unit, "productPrice": 10,
                        "stockCount": 2, "actualCount": 3, "count": 1}],
        })
        self.reads(token, "stock-check", stock_check)
        self.approve(token, "stock-check", stock_check)
        assert self.stock() == f"{warehouse1}\t4.000000\n{warehouse2}\t3.000000"

        for document, identifier in (
            ("purchase-order", purchase_order), ("purchase-in", purchase_in),
            ("purchase-return", purchase_return), ("sale-order", sale_order),
            ("sale-out", sale_out), ("sale-return", sale_return),
            ("stock-in", stock_in), ("stock-out", stock_out),
            ("stock-move", stock_move), ("stock-check", stock_check),
        ):
            status = self.sql(f"SELECT status FROM erp_{document.replace('-', '_')} "
                              f"WHERE id={int(identifier)};")
            assert status == "20", (document, status)
        return {"result": "PASS", "schema": self.args.schema,
                "changesets": changesets, "requests": self.events,
                "limited_role_permissions": list(PERMISSIONS),
                "assertions": {
                    "purchase_and_sale_returns": True,
                    "stock_in_out_move_check": True,
                    "final_stock": self.stock(),
                    "all_auxiliary_documents_approved": True,
                }}


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
    validate_target(args.schema, url.port, 13395, 16476)
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
