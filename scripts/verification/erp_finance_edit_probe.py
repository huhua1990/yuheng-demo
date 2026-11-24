#!/usr/bin/env python3
"""Opt-in finance editing checks against an operator-verified disposable local JAR."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
from urllib.parse import urlparse

from erp_returns_probe import ReturnsProbe


class EditProbe(ReturnsProbe):
    def run(self):
        assert self.sql("SELECT DATABASE();") == self.args.schema
        self.installed_changesets(self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;"))
        assert self.sql("SELECT COUNT(*) FROM erp_product;") == "0"
        self.snapshot()
        passwords = self.sql("SELECT id,password FROM system_users ORDER BY id;")
        self.token = self.call("POST", "/system/auth/login", {
            "username": os.environ["YUHENG_PROBE_USERNAME"],
            "password": os.environ["YUHENG_PROBE_PASSWORD"]})["accessToken"]
        category = self.create("product-category", {"parentId": 0, "name": "EDIT category", "code": "EDIT", "sort": 1, "status": 0})
        unit = self.create("product-unit", {"name": "EDIT unit", "status": 0})
        supplier = self.create("supplier", {"name": "EDIT supplier", "sort": 1, "status": 0})
        customer = self.create("customer", {"name": "EDIT customer", "sort": 1, "status": 0})
        account = self.create("account", {"name": "EDIT account", "no": "EDIT", "sort": 1, "status": 0})
        warehouse = self.create("warehouse", {"name": "EDIT warehouse", "sort": 1, "status": 0})
        product = self.create("product", {"name": "EDIT product", "barCode": "EDIT", "categoryId": category,
            "unitId": unit, "status": 0, "purchasePrice": 10, "salePrice": 10, "minPrice": 1})
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for kind, party, party_id, move, date, finance, fdate, biz, prior, amount, excess in (
            ("purchase", "supplierId", supplier, "in", "inTime", "finance-payment", "paymentTime", 11, "paidPrice", "paymentPrice", 1030102007),
            ("sale", "customerId", customer, "out", "outTime", "finance-receipt", "receiptTime", 21, "receiptedPrice", "receiptPrice", 1020202007),
        ):
            line = {"productId": product, "productUnitId": unit, "productPrice": 10, "count": 10, "taxPercent": 0}
            order = self.create(kind + "-order", {party: party_id, "accountId": account, "orderTime": now,
                "discountPercent": 0, "depositPrice": 0, "items": [line]})
            source_item = self.get(kind + "-order", order)["items"][0]["id"]
            self.status(kind + "-order", order)
            resource = kind + "-" + move
            sources = []
            for i in (1, 2):
                source = self.create(resource, {"accountId": account, date: now, "orderId": order,
                    "discountPercent": 0, "otherPrice": 0,
                    "items": [dict(line, count=5, orderItemId=source_item, warehouseId=warehouse)]})
                self.status(resource, source)
                sources.append(source)
            def item(source, price, identifier=None):
                result = {"bizType": biz, "bizId": source, prior: 0, amount: price}
                if identifier is not None:
                    result["id"] = identifier
                return result
            def check_source(source, expected):
                actual = self.get(resource, source)[amount]
                self.checks.append({"kind": kind, "source": source, "expected": str(expected), "actual": str(actual)})
                self.equal(actual, expected)
            def update(items, code=0):
                return self.call("PUT", f"/erp/{finance}/update", dict(body, id=finance_id, items=items), code=code)
            body = {party: party_id, "accountId": account, fdate: now, "discountPrice": 0,
                    "items": [item(sources[0], 10)]}
            finance_id = self.create(finance, body)
            line_id = self.get(finance, finance_id)["items"][0]["id"]
            check_source(sources[0], 10)
            update([item(sources[0], 20, line_id)])
            check_source(sources[0], 20)
            before = self.snapshot()
            update([item(sources[0], 51, line_id)], code=excess)
            assert self.snapshot() == before, "excess edit must roll back all affected rows"
            update([item(sources[1], 15, line_id)])
            check_source(sources[0], 0)
            check_source(sources[1], 15)
            update([item(sources[0], 7)])
            check_source(sources[1], 0)
            check_source(sources[0], 7)
            return_resource = kind + "-return"
            return_id = self.create(return_resource, {"orderId": order, "accountId": account, "returnTime": now,
                "discountPercent": 0, "otherPrice": 0, "items": [dict(line, count=1,
                    orderItemId=source_item, warehouseId=warehouse)]})
            self.status(return_resource, return_id)
            replacement_id = self.get(finance, finance_id)["items"][0]["id"]
            return_line = {"id": replacement_id, "bizType": 12 if kind == "purchase" else 22,
                           "bizId": return_id, prior: 0, amount: -3}
            update([return_line])
            check_source(sources[0], 0)
            self.equal(self.get(return_resource, return_id)["refundPrice"], 3)
            update([item(sources[1], 4, replacement_id)])
            self.equal(self.get(return_resource, return_id)["refundPrice"], 0)
            check_source(sources[1], 4)
            self.status(return_resource, return_id, status=10)
        assert self.sql("SELECT id,password FROM system_users ORDER BY id;") == passwords
        return {"result": "PASS", "schema": self.args.schema, "port": urlparse(self.args.base_url).port,
                "requests": self.events, "checks": self.checks,
                "scope": "purchase/sale same-line amount, source and type changes, replacement, excess rollback"}


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
    if not re.fullmatch(r"yuheng_t4_edit_[0-9]{8}(?:_[a-z0-9]+)?", args.schema):
        parser.error("only yuheng_t4_edit_YYYYMMDD[_suffix] disposable schemas are allowed")
    probe = EditProbe(args)
    probe.checks = []
    try:
        result = probe.run()
    except Exception as error:
        args.output.write_text(json.dumps({"result": "FAIL", "error": str(error), "requests": probe.events,
                                         "checks": probe.checks}, ensure_ascii=False, indent=2) + "\n")
        raise
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"result": result["result"], "requests": len(probe.events), "checks": len(probe.checks)}))


if __name__ == "__main__":
    main()
