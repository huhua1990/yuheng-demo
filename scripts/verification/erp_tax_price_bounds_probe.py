#!/usr/bin/env python3
"""Exercise ERP tax and reference-price validation on a disposable Demo schema."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class Probe:
    def __init__(self, args):
        self.args = args
        self.token = None
        self.events = []

    def sql(self, statement):
        command = ["docker", "exec", "-i", self.args.mysql_container, "sh", "-c",
                   'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw --skip-column-names "$1"',
                   "probe", self.args.schema]
        return subprocess.run(command, input=statement, text=True, capture_output=True,
                              check=True).stdout.strip()

    def call(self, method, path, body=None, expected_code=0):
        headers = {"Content-Type": "application/json", "tenant-id": "1"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        request = Request(self.args.base_url + "/admin-api" + path, method=method,
                          headers=headers,
                          data=json.dumps(body).encode() if body is not None else None)
        try:
            response = urlopen(request, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            status = response.status
            data = json.load(response)
        event = {"method": method, "path": path, "http": status, "code": data.get("code")}
        if expected_code != 0:
            event["message"] = data.get("msg")
        self.events.append(event)
        assert status == 200 and data.get("code") == expected_code, event
        return data.get("data")

    def snapshot(self):
        tables = self.sql(
            "SELECT TABLE_NAME FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME LIKE 'erp\\_%' ORDER BY TABLE_NAME;"
        ).splitlines()
        return {table: self.sql(f"SELECT COUNT(*) FROM `{table}`;") for table in tables}

    def reject_without_write(self, method, path, body, message):
        before = self.snapshot()
        self.call(method, path, body, expected_code=400)
        assert message in self.events[-1].get("message", ""), self.events[-1]
        assert self.snapshot() == before, (path, "ERP row counts changed after rejected input")

    def run(self):
        assert self.sql("SELECT DATABASE();") == self.args.schema
        assert self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;") == "54"
        assert self.sql("SELECT COUNT(*) FROM erp_product;") == "0"
        login = self.call("POST", "/system/auth/login", {
            "username": os.environ["YUHENG_PROBE_USERNAME"],
            "password": os.environ["YUHENG_PROBE_PASSWORD"]})
        self.token = login["accessToken"]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for resource, body, label in (
            ("supplier", {"name": "Bounds supplier", "sort": 1, "status": 0,
                           "taxPercent": "-0.01"}, "税率不能小于 0"),
            ("supplier", {"name": "Bounds supplier", "sort": 1, "status": 0,
                           "taxPercent": "100.01"}, "税率不能大于 100"),
            ("customer", {"name": "Bounds customer", "sort": 1, "status": 0,
                           "taxPercent": "-0.01"}, "税率不能小于 0"),
            ("customer", {"name": "Bounds customer", "sort": 1, "status": 0,
                           "taxPercent": "100.01"}, "税率不能大于 100"),
        ):
            self.reject_without_write("POST", f"/erp/{resource}/create", body, label)

        for field, label in (("weight", "基础重量"), ("purchasePrice", "采购价格"),
                             ("salePrice", "销售价格"), ("minPrice", "最低价格")):
            body = {"name": "Bounds product", "barCode": "BOUNDS", "categoryId": 1,
                    "unitId": 1, "status": 0, field: "-0.01"}
            self.reject_without_write("POST", "/erp/product/create", body,
                                      f"{label}不能小于 0")

        tax_cases = (
            ("purchase-order", {"supplierId": 1, "orderTime": now, "discountPercent": 0,
                "items": [{"productId": 1, "productUnitId": 1, "productPrice": 1,
                           "count": 1, "taxPercent": "100.01"}]}),
            ("purchase-in", {"orderId": 1, "inTime": now, "discountPercent": 0,
                "items": [{"orderItemId": 1, "warehouseId": 1, "productId": 1,
                           "productUnitId": 1, "productPrice": 1, "count": 1,
                           "taxPercent": "-0.01"}]}),
            ("purchase-return", {"orderId": 1, "returnTime": now, "discountPercent": 0,
                "items": [{"orderItemId": 1, "warehouseId": 1, "productId": 1,
                           "productUnitId": 1, "productPrice": 1, "count": 1,
                           "taxPercent": "100.01"}]}),
            ("sale-order", {"customerId": 1, "orderTime": now, "discountPercent": 0,
                "items": [{"productId": 1, "productUnitId": 1, "productPrice": 1,
                           "count": 1, "taxPercent": "-0.01"}]}),
            ("sale-out", {"orderId": 1, "outTime": now, "discountPercent": 0,
                "items": [{"orderItemId": 1, "warehouseId": 1, "productId": 1,
                           "productUnitId": 1, "productPrice": 1, "count": 1,
                           "taxPercent": "100.01"}]}),
            ("sale-return", {"orderId": 1, "returnTime": now, "discountPercent": 0,
                "items": [{"orderItemId": 1, "warehouseId": 1, "productId": 1,
                           "productUnitId": 1, "productPrice": 1, "count": 1,
                           "taxPercent": "-0.01"}]}),
        )
        for resource, body in tax_cases:
            self.reject_without_write("POST", f"/erp/{resource}/create", body,
                                      "税率不能" )

        for resource, path, body in (
            ("stock-check", "/erp/stock-check/create", {"checkTime": now,
                "items": [{"warehouseId": 1, "productId": 1, "productPrice": "-0.01",
                           "stockCount": 1, "actualCount": 1, "count": 0}]}),
            ("stock-in", "/erp/stock-in/create", {"inTime": now,
                "items": [{"warehouseId": 1, "productId": 1, "productPrice": "-0.01",
                           "count": 1}]}),
            ("stock-out", "/erp/stock-out/create", {"outTime": now,
                "items": [{"warehouseId": 1, "productId": 1, "productPrice": "-0.01",
                           "count": 1}]}),
            ("stock-move", "/erp/stock-move/create", {"moveTime": now,
                "fromWarehouseId": 1, "toWarehouseId": 2,
                "items": [{"productId": 1, "productPrice": "-0.01", "count": 1}]}),
        ):
            self.reject_without_write("POST", path, body, "产品单价不能小于 0")

        return {"result": "PASS", "schema": self.args.schema,
                "port": urlparse(self.args.base_url).port,
                "time": datetime.now().astimezone().isoformat(), "requests": self.events,
                "assertions": {"rejected_requests_without_erp_writes": len(self.events) - 1,
                    "tax_defaults_and_six_document_line_types": True,
                    "product_and_stock_reference_prices": True}}


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
        parser.error("use a dedicated loopback HTTP port, without a path or credentials")
    if not re.fullmatch(r"yuheng_t4_taxbounds_[0-9]{8}", args.schema):
        parser.error("only yuheng_t4_taxbounds_YYYYMMDD disposable schemas are allowed")
    probe = Probe(args)
    try:
        result = probe.run()
    except Exception as error:
        args.output.write_text(json.dumps({"result": "FAIL", "schema": args.schema,
            "error": str(error), "requests": probe.events}, indent=2, ensure_ascii=False) + "\n")
        raise
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"result": result["result"], "requests": len(result["requests"])},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
