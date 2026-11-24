#!/usr/bin/env python3
"""Verify create-time child-ID rejection for all ERP documents on an isolated JAR."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from erp_workflow_probe import Probe


CASES = [
    ("purchase-order", 1030101011, {"supplierId": 1, "orderTime": "time"},
     {"productId": 1, "productUnitId": 1, "productPrice": 1, "count": 1}),
    ("purchase-in", 1030102009, {"orderId": 1, "accountId": 1, "inTime": "time"},
     {"orderItemId": 1, "warehouseId": 1, "productId": 1, "productUnitId": 1,
      "productPrice": 1, "count": 1}),
    ("purchase-return", 1030103009, {"orderId": 1, "accountId": 1, "returnTime": "time"},
     {"orderItemId": 1, "warehouseId": 1, "productId": 1, "productUnitId": 1,
      "productPrice": 1, "count": 1}),
    ("sale-order", 1020201011, {"customerId": 1, "orderTime": "time"},
     {"productId": 1, "productUnitId": 1, "productPrice": 1, "count": 1}),
    ("sale-out", 1020202009, {"orderId": 1, "accountId": 1, "outTime": "time"},
     {"orderItemId": 1, "warehouseId": 1, "productId": 1, "productUnitId": 1,
      "productPrice": 1, "count": 1}),
    ("sale-return", 1020203009, {"orderId": 1, "accountId": 1, "returnTime": "time"},
     {"orderItemId": 1, "warehouseId": 1, "productId": 1, "productUnitId": 1,
      "productPrice": 1, "count": 1}),
    ("stock-in", 1030401099, {"inTime": "time"},
     {"warehouseId": 1, "productId": 1, "productPrice": 1, "count": 1}),
    ("stock-out", 1030402099, {"outTime": "time"},
     {"warehouseId": 1, "productId": 1, "productPrice": 1, "count": 1}),
    ("stock-check", 1030410000, {"checkTime": "time"},
     {"warehouseId": 1, "productId": 1, "productPrice": 1,
      "stockCount": 0, "actualCount": 0, "count": 0}),
    ("stock-move", 1030410001, {"moveTime": "time"},
     {"fromWarehouseId": 1, "toWarehouseId": 2, "productId": 1,
      "productPrice": 1, "count": 1}),
]


class OwnerProbe(Probe):
    def __init__(self, args):
        super().__init__(args)
        self.events = []

    def call(self, method, path, body=None, code=0):
        from urllib.request import Request, urlopen
        from urllib.error import HTTPError
        headers = {"Content-Type": "application/json", "tenant-id": "1"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        req = Request(self.args.base_url + "/admin-api" + path, method=method,
                      headers=headers, data=json.dumps(body).encode() if body is not None else None)
        try:
            response = urlopen(req, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            status, data = response.status, json.load(response)
        self.events.append({"method": method, "path": path, "http": status, "code": data.get("code")})
        assert status == 200 and data.get("code") == code, (method, path, status, data.get("code"), data.get("msg"))
        return data.get("data")

    def snapshot(self):
        tables = ["erp_stock", "erp_stock_record", "erp_finance_payment", "erp_finance_payment_item",
                  "erp_finance_receipt", "erp_finance_receipt_item"]
        tables.extend((
            "erp_purchase_order", "erp_purchase_order_items",
            "erp_purchase_in", "erp_purchase_in_items",
            "erp_purchase_return", "erp_purchase_return_items",
            "erp_sale_order", "erp_sale_order_items",
            "erp_sale_out", "erp_sale_out_items",
            "erp_sale_return", "erp_sale_return_items",
            "erp_stock_in", "erp_stock_in_item",
            "erp_stock_out", "erp_stock_out_item",
            "erp_stock_check", "erp_stock_check_item",
            "erp_stock_move", "erp_stock_move_item",
        ))
        return {table: self.sql(f"SELECT * FROM {table} ORDER BY id;") for table in tables}

    def run(self):
        assert self.sql("SELECT DATABASE();") == self.args.schema
        self.installed_changesets(self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;"))
        assert self.sql("SELECT COUNT(*) FROM erp_product;") == "0"
        before = self.snapshot()
        login = self.call("POST", "/system/auth/login", {
            "username": os.environ["YUHENG_PROBE_USERNAME"],
            "password": os.environ["YUHENG_PROBE_PASSWORD"]})
        self.token = login["accessToken"]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for resource, expected, header, item in CASES:
            header = {key: now if value == "time" else value for key, value in header.items()}
            body = dict(header, items=[dict(item, id=987654321)])
            self.call("POST", f"/erp/{resource}/create", body, code=expected)
            assert self.snapshot() == before, f"{resource} invalid ID changed database rows"
        return {"result": "PASS", "schema": self.args.schema, "requests": self.events,
                "scope": "create-time client item IDs rejected for ten ERP document endpoints; full business row snapshots unchanged"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--mysql-container", default="mysql8")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    url = urlparse(args.base_url)
    if (url.scheme != "http" or url.hostname != "127.0.0.1" or not url.port
            or url.port in (48080, 5173) or url.path or url.query or url.fragment or url.username):
        parser.error("use a dedicated loopback HTTP port without path or credentials")
    if not re.fullmatch(r"yuheng_t4_item_owner_[0-9]{8}(?:_[a-z0-9]+)?", args.schema):
        parser.error("only yuheng_t4_item_owner_YYYYMMDD[_suffix] disposable schemas are allowed")
    probe = OwnerProbe(args)
    try:
        result = probe.run()
    except Exception as error:
        args.output.write_text(json.dumps({"result": "FAIL", "error": str(error),
            "requests": probe.events}, ensure_ascii=False, indent=2) + "\n")
        raise
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"result": result["result"], "requests": len(result["requests"])}))


if __name__ == "__main__":
    main()
