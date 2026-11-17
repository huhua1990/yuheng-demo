#!/usr/bin/env python3
"""Opt-in large-amount finance verification; operator isolates datasource and Redis."""
import argparse
from datetime import datetime
from decimal import Decimal
import json
import os
from pathlib import Path
import re
from urllib.parse import urlparse

from erp_returns_probe import ReturnsProbe


class PrecisionProbe(ReturnsProbe):
    def run(self):
        assert self.sql("SELECT DATABASE();") == self.args.schema
        assert self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;") == "54"
        assert self.sql("SELECT COUNT(*) FROM erp_product;") == "0"
        self.snapshot()
        passwords = self.sql("SELECT id,password FROM system_users ORDER BY id;")
        self.token = self.call("POST", "/system/auth/login", {
            "username": os.environ["YUHENG_PROBE_USERNAME"],
            "password": os.environ["YUHENG_PROBE_PASSWORD"]})["accessToken"]
        category = self.create("product-category", {"parentId": 0, "name": "MONEY category", "code": "MONEY", "sort": 1, "status": 0})
        unit = self.create("product-unit", {"name": "MONEY unit", "status": 0})
        supplier = self.create("supplier", {"name": "MONEY supplier", "sort": 1, "status": 0})
        customer = self.create("customer", {"name": "MONEY customer", "sort": 1, "status": 0})
        account = self.create("account", {"name": "MONEY account", "no": "MONEY", "sort": 1, "status": 0})
        warehouse = self.create("warehouse", {"name": "MONEY warehouse", "sort": 1, "status": 0})
        price = "9007199254740991.12"
        product = self.create("product", {"name": "MONEY product", "barCode": "MONEY",
            "categoryId": category, "unitId": unit, "status": 0, "purchasePrice": price,
            "salePrice": price, "minPrice": "0.01"})
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for kind, party, party_id, movement, date, finance, finance_date, biz_type, prior, value, excess_code in (
            ("purchase", "supplierId", supplier, "in", "inTime", "finance-payment", "paymentTime", 11, "paidPrice", "paymentPrice", 1030102007),
            ("sale", "customerId", customer, "out", "outTime", "finance-receipt", "receiptTime", 21, "receiptedPrice", "receiptPrice", 1020202007),
        ):
            line = {"productId": product, "productUnitId": unit, "productPrice": price, "count": 1, "taxPercent": 0}
            order = self.create(kind + "-order", {party: party_id, "accountId": account, "orderTime": now,
                "discountPercent": 0, "depositPrice": 0, "items": [line]})
            source_item = self.get(kind + "-order", order)["items"][0]["id"]
            self.status(kind + "-order", order)
            resource = kind + "-" + movement
            source = self.create(resource, {"accountId": account, date: now, "orderId": order,
                "discountPercent": 0, "otherPrice": 0,
                "items": [dict(line, orderItemId=source_item, warehouseId=warehouse)]})
            self.status(resource, source)
            self.equal(self.get(resource, source)["totalPrice"], price)
            body = {party: party_id, "accountId": account, finance_date: now, "discountPrice": 0,
                    "items": [{"bizType": biz_type, "bizId": source, prior: 0, value: price}]}
            self.create(finance, body)
            actual = self.get(resource, source)[value]
            self.equal(actual, price)
            table = "erp_" + resource.replace("-", "_")
            self.equal(self.sql(f"SELECT {('payment_price' if kind == 'purchase' else 'receipt_price')} "
                                f"FROM {table} WHERE id={int(source)};"), price)
            before = self.snapshot()
            self.create(finance, dict(body, items=[{"bizType": biz_type, "bizId": source,
                                                    prior: price, value: "0.01"}]), code=excess_code)
            assert self.snapshot() == before, "excess finance write must roll back"
        assert self.sql("SELECT id,password FROM system_users ORDER BY id;") == passwords
        return {"result": "PASS", "schema": self.args.schema, "port": urlparse(self.args.base_url).port,
                "time": datetime.now().astimezone().isoformat(), "requests": self.events,
                "assertions": {"payment_and_receipt_sum": price, "extra_cent_rejected_and_rolled_back": True,
                               "seed_passwords_unchanged": True}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--mysql-container", default="mysql8")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    url = urlparse(args.base_url)
    if (url.scheme != "http" or url.hostname != "127.0.0.1" or not url.port or url.port in (48080, 5173)
            or url.path or url.query or url.fragment or url.username):
        parser.error("use a dedicated loopback port without path or credentials")
    if not re.fullmatch(r"yuheng_t4_money_[0-9]{8}(?:_[a-z0-9]+)?", args.schema):
        parser.error("only yuheng_t4_money_YYYYMMDD[_suffix] disposable schemas are allowed")
    probe = PrecisionProbe(args)
    try:
        result = probe.run()
    except Exception as error:
        args.output.write_text(json.dumps({"result": "FAIL", "error": str(error), "requests": probe.events},
                                         ensure_ascii=False, indent=2) + "\n")
        raise
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"result": result["result"], "requests": len(probe.events),
                      "assertions": result["assertions"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
