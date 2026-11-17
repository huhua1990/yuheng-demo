#!/usr/bin/env python3
"""Opt-in ERP write verification against a disposable, empty local instance.

The operator must start the JAR against the named schema on the supplied port.
This script neither creates nor drops schemas. It deliberately refuses normal
application ports and any schema outside the dedicated probe namespace.
Credentials are read from environment variables and never included in evidence.
"""
import argparse
from datetime import datetime
from decimal import Decimal
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


class Probe:
    def __init__(self, args):
        self.args = args
        self.token = None
        self.events = []

    def sql(self, statement):
        command = ["docker", "exec", "-i", self.args.mysql_container, "sh", "-c",
                   'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot '
                   '--batch --raw --skip-column-names "$1"', "probe", self.args.schema]
        result = subprocess.run(command, input=statement, text=True,
                                capture_output=True, check=True)
        return result.stdout.strip()

    def call(self, method, path, body=None, code=0):
        headers = {"Content-Type": "application/json", "tenant-id": "1"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        request = Request(self.args.base_url + "/admin-api" + path,
                          data=json.dumps(body).encode() if body is not None else None,
                          headers=headers, method=method)
        try:
            response = urlopen(request, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            status = response.status
            data = json.load(response)
        self.events.append({"method": method, "path": path, "http": status,
                            "code": data.get("code")})
        assert status == 200 and data.get("code") == code, (method, path, status,
                {key: data.get(key) for key in ("code", "msg")})
        return data.get("data")

    def create(self, resource, body, code=0):
        return self.call("POST", f"/erp/{resource}/create", body, code)

    def get(self, resource, identifier):
        return self.call("GET", f"/erp/{resource}/get?id={identifier}")

    def status(self, resource, identifier, status=20, code=0):
        self.call("PUT", f"/erp/{resource}/update-status?" +
                  urlencode({"id": identifier, "status": status}), code=code)

    @staticmethod
    def equal(actual, expected):
        assert Decimal(str(actual)) == Decimal(str(expected)), (actual, expected)

    def run(self):
        assert self.sql("SELECT DATABASE();") == self.args.schema
        assert self.sql("SELECT COUNT(*) FROM erp_product;") == "0", "fresh schema required"
        assert self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;") == "54"
        assert self.sql("SELECT COUNT(*) FROM system_users WHERE password IS NULL OR password='';") == "0"
        login = self.call("POST", "/system/auth/login", {
            "username": os.environ["YUHENG_PROBE_USERNAME"],
            "password": os.environ["YUHENG_PROBE_PASSWORD"]})
        self.token = login["accessToken"]
        category = self.create("product-category", {"parentId": 0, "name": "T4 flow category",
            "code": "T4-FLOWS", "sort": 1, "status": 0})
        unit = self.create("product-unit", {"name": "T4 piece", "status": 0})
        supplier = self.create("supplier", {"name": "T4 supplier", "sort": 1, "status": 0})
        customer = self.create("customer", {"name": "T4 customer", "sort": 1, "status": 0})
        account = self.create("account", {"name": "T4 account", "no": "T4-FLOWS", "sort": 1, "status": 0})
        warehouse = self.create("warehouse", {"name": "T4 warehouse", "sort": 1, "status": 0})
        product = self.create("product", {"name": "T4 product", "barCode": "T4-FLOWS",
            "categoryId": category, "unitId": unit, "status": 0,
            "purchasePrice": 10, "salePrice": 20, "minPrice": 1})
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Purchase: unapproved source rejected; approved receipt raises stock.
        po = self.create("purchase-order", {"supplierId": supplier, "accountId": account,
            "orderTime": now, "discountPercent": 0, "depositPrice": 0,
            "items": [{"productId": product, "productUnitId": unit,
                       "productPrice": 10, "count": 10, "taxPercent": 0}]})
        po_data = self.get("purchase-order", po)
        self.equal(po_data["status"], 10)
        inbound_body = {"accountId": account, "inTime": now, "orderId": po,
            "discountPercent": 0, "otherPrice": 0,
            "items": [{"orderItemId": po_data["items"][0]["id"], "warehouseId": warehouse,
                       "productId": product, "productUnitId": unit,
                       "productPrice": 10, "count": 10, "taxPercent": 0}]}
        self.create("purchase-in", inbound_body, code=1030101006)
        self.status("purchase-order", po)
        inbound = self.create("purchase-in", inbound_body)
        self.equal(self.get("purchase-order", po)["inCount"], 0)
        self.status("purchase-in", inbound)
        self.status("purchase-in", inbound, code=1030102003)
        self.equal(self.get("purchase-order", po)["inCount"], 10)
        assert self.sql("SELECT `count` FROM erp_stock WHERE deleted=0;") == "10.000000"

        payment_body = {"supplierId": supplier, "accountId": account,
            "paymentTime": now, "discountPrice": 0,
            "items": [{"bizType": 11, "bizId": inbound, "paidPrice": 0, "paymentPrice": 100}]}
        payment = self.create("finance-payment", payment_body)
        self.equal(self.get("finance-payment", payment)["status"], 10)
        self.equal(self.get("purchase-in", inbound)["paymentPrice"], 100)
        self.status("finance-payment", payment)
        self.status("finance-payment", payment, code=1030601003)
        self.status("purchase-in", inbound, status=10, code=1030102008)
        payment_body["items"][0].update({"paidPrice": 100, "paymentPrice": 1})
        self.create("finance-payment", payment_body, code=1030102007)
        assert self.sql("SELECT COUNT(*) FROM erp_finance_payment WHERE deleted=0;") == "1"
        assert self.sql("SELECT COUNT(*) FROM erp_finance_payment_item WHERE deleted=0;") == "1"
        self.equal(self.get("purchase-in", inbound)["paymentPrice"], 100)

        # Sale: stock moves only at approval; receipts reserve source amounts on creation.
        so = self.create("sale-order", {"customerId": customer, "accountId": account,
            "orderTime": now, "discountPercent": 0, "depositPrice": 0,
            "items": [{"productId": product, "productUnitId": unit,
                       "productPrice": 20, "count": 4, "taxPercent": 0}]})
        so_data = self.get("sale-order", so)
        outbound_body = {"accountId": account, "outTime": now, "orderId": so,
            "discountPercent": 0, "otherPrice": 0,
            "items": [{"orderItemId": so_data["items"][0]["id"], "warehouseId": warehouse,
                       "productId": product, "productUnitId": unit,
                       "productPrice": 20, "count": 4, "taxPercent": 0}]}
        self.create("sale-out", outbound_body, code=1020201006)
        self.status("sale-order", so)
        outbound = self.create("sale-out", outbound_body)
        # Upstream sales count includes pending outbound documents (unlike
        # purchase inCount). Preserve that contract and check stock separately.
        self.equal(self.get("sale-order", so)["outCount"], 4)
        assert self.sql("SELECT `count` FROM erp_stock WHERE deleted=0;") == "10.000000"
        self.status("sale-out", outbound)
        self.status("sale-out", outbound, code=1020202003)
        self.equal(self.get("sale-order", so)["outCount"], 4)

        receipt_body = {"customerId": customer, "accountId": account,
            "receiptTime": now, "discountPrice": 0,
            "items": [{"bizType": 21, "bizId": outbound, "receiptedPrice": 0, "receiptPrice": 80}]}
        receipt = self.create("finance-receipt", receipt_body)
        self.equal(self.get("finance-receipt", receipt)["status"], 10)
        self.equal(self.get("sale-out", outbound)["receiptPrice"], 80)
        self.status("finance-receipt", receipt)
        self.status("finance-receipt", receipt, code=1030602003)
        self.status("sale-out", outbound, status=10, code=1020202008)
        receipt_body["items"][0].update({"receiptedPrice": 80, "receiptPrice": 1})
        self.create("finance-receipt", receipt_body, code=1020202007)
        assert self.sql("SELECT COUNT(*) FROM erp_finance_receipt WHERE deleted=0;") == "1"
        assert self.sql("SELECT COUNT(*) FROM erp_finance_receipt_item WHERE deleted=0;") == "1"
        self.equal(self.get("sale-out", outbound)["receiptPrice"], 80)

        # Finance reverse-approval/re-approval has no effect on reserved source amounts.
        for resource, identifier in (("finance-payment", payment), ("finance-receipt", receipt)):
            self.status(resource, identifier, status=10)
            self.equal(self.get(resource, identifier)["status"], 10)
            self.status(resource, identifier)
            self.equal(self.get(resource, identifier)["status"], 20)
        self.equal(self.get("purchase-in", inbound)["paymentPrice"], 100)
        self.equal(self.get("sale-out", outbound)["receiptPrice"], 80)

        stock = self.call("GET", "/erp/stock/page?pageNo=1&pageSize=10")
        self.equal(stock["total"], 1)
        self.equal(stock["list"][0]["count"], 6)
        assert self.sql("SELECT CONCAT(tenant_id, ':', `count`) FROM erp_stock WHERE deleted=0;") == "1:6.000000"
        assert self.sql("SELECT CONCAT(biz_type, ':', `count`) FROM erp_stock_record WHERE deleted=0 ORDER BY id;") == "70:10.000000\n50:-4.000000"
        for table in ("erp_purchase_order", "erp_purchase_in", "erp_sale_order", "erp_sale_out",
                      "erp_finance_payment", "erp_finance_receipt"):
            assert self.sql(f"SELECT CONCAT(status, ':', tenant_id) FROM {table} WHERE deleted=0;") == "20:1", table
        return {"result": "PASS", "schema": self.args.schema, "port": urlparse(self.args.base_url).port,
                "time": datetime.now().astimezone().isoformat(), "requests": self.events,
                "assertions": {"purchase_count": 10, "sale_count": 4, "stock_count": 6,
                    "payment_price": 100, "receipt_price": 80, "stock_records": 2,
                    "final_document_status": 20, "tenant_id": 1,
                    "overpayment_and_overreceipt_rolled_back": True}}


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
    if not re.fullmatch(r"yuheng_t4_flows_[0-9]{8}(?:_[a-z0-9]+)?", args.schema):
        parser.error("only yuheng_t4_flows_YYYYMMDD[_suffix] disposable schemas are allowed")
    probe = Probe(args)
    try:
        result = probe.run()
    except Exception as error:
        result = {"result": "FAIL", "schema": args.schema, "error": str(error), "requests": probe.events}
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        raise
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"result": result["result"], "requests": len(probe.events),
                      "assertions": result["assertions"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
