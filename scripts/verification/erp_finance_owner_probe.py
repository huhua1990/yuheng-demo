#!/usr/bin/env python3
"""Opt-in financial item ownership check against a disposable isolated JAR."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
from urllib.parse import urlparse

from erp_returns_probe import ReturnsProbe


class OwnerProbe(ReturnsProbe):
    def run(self):
        assert self.sql("SELECT DATABASE();") == self.args.schema
        self.installed_changesets(self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;"))
        assert self.sql("SELECT COUNT(*) FROM erp_product;") == "0"
        self.snapshot()
        passwords = self.sql("SELECT id,password FROM system_users ORDER BY id;")
        self.token = self.call("POST", "/system/auth/login", {
            "username": os.environ["YUHENG_PROBE_USERNAME"],
            "password": os.environ["YUHENG_PROBE_PASSWORD"]})["accessToken"]
        category = self.create("product-category", {"parentId": 0, "name": "OWN category", "code": "OWN", "sort": 1, "status": 0})
        unit = self.create("product-unit", {"name": "OWN unit", "status": 0})
        supplier = self.create("supplier", {"name": "OWN supplier", "sort": 1, "status": 0})
        customer = self.create("customer", {"name": "OWN customer", "sort": 1, "status": 0})
        account = self.create("account", {"name": "OWN account", "no": "OWN", "sort": 1, "status": 0})
        warehouse = self.create("warehouse", {"name": "OWN warehouse", "sort": 1, "status": 0})
        product = self.create("product", {"name": "OWN product", "barCode": "OWN", "categoryId": category,
            "unitId": unit, "status": 0, "purchasePrice": 10, "salePrice": 10, "minPrice": 1})
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for kind, party, party_id, move, date, finance, fdate, biz, prior, amount, error in (
            ("purchase", "supplierId", supplier, "in", "inTime", "finance-payment", "paymentTime", 11, "paidPrice", "paymentPrice", 1030601006),
            ("sale", "customerId", customer, "out", "outTime", "finance-receipt", "receiptTime", 21, "receiptedPrice", "receiptPrice", 1030602006),
        ):
            line = {"productId": product, "productUnitId": unit, "productPrice": 10, "count": 10, "taxPercent": 0}
            order = self.create(kind + "-order", {party: party_id, "accountId": account, "orderTime": now,
                "discountPercent": 0, "depositPrice": 0, "items": [line]})
            order_item = self.get(kind + "-order", order)["items"][0]["id"]
            self.status(kind + "-order", order)
            source = self.create(kind + "-" + move, {"accountId": account, date: now, "orderId": order,
                "discountPercent": 0, "otherPrice": 0,
                "items": [dict(line, orderItemId=order_item, warehouseId=warehouse)]})
            self.status(kind + "-" + move, source)
            item = {"bizType": biz, "bizId": source, prior: 0, amount: 10}
            body = {party: party_id, "accountId": account, fdate: now, "discountPrice": 0, "items": [item]}
            first = self.create(finance, body)
            second = self.create(finance, body)
            first_id = self.get(finance, first)["items"][0]["id"]
            second_id = self.get(finance, second)["items"][0]["id"]
            before = self.snapshot()
            for case, method, payload in (
                ("foreign", "PUT", dict(body, id=first, items=[dict(item, id=second_id)])),
                ("missing", "PUT", dict(body, id=first, items=[dict(item, id=999999999)])),
                ("duplicate", "PUT", dict(body, id=first, items=[dict(item, id=first_id), dict(item, id=first_id)])),
                ("create-with-id", "POST", dict(body, items=[dict(item, id=999999998)])),
            ):
                self.case = kind + ":" + case
                self.call(method, "/erp/" + finance + ("/update" if method == "PUT" else "/create"), payload, code=error)
                assert self.snapshot() == before, "invalid item IDs must not change any rows"
            self.call("PUT", "/erp/" + finance + "/update", dict(body, id=first, items=[dict(item, id=first_id, **{amount: 12})]))
            self.equal(self.get(kind + "-" + move, source)[amount], 22)
            # Deliberately create an item owned by a different tenant only in
            # this disposable schema. The victim financial document is absent.
            table = "erp_finance_" + ("payment" if kind == "purchase" else "receipt") + "_item"
            parent = "payment_id" if kind == "purchase" else "receipt_id"
            foreign_id = 899999001 if kind == "purchase" else 899999002
            self.sql(f"INSERT INTO {table} (id,{parent},biz_type,biz_id,biz_no,total_price,"
                     f"{('paid_price,payment_price' if kind == 'purchase' else 'receipted_price,receipt_price')},tenant_id) "
                     f"VALUES ({foreign_id},899999000,{biz},{source},'ISOLATED',100,0,10,999);")
            before = self.snapshot()
            self.case = kind + ":cross-tenant-item"
            self.call("PUT", "/erp/" + finance + "/update",
                      dict(body, id=first, items=[dict(item, id=foreign_id)]), code=error)
            assert self.snapshot() == before, "cross-tenant item IDs must leave all rows unchanged"
        assert self.sql("SELECT id,password FROM system_users ORDER BY id;") == passwords
        return {"result": "PASS", "schema": self.args.schema, "port": urlparse(self.args.base_url).port,
                "requests": self.events, "scope": "payment/receipt foreign, cross-tenant, missing, duplicate and create item IDs; unchanged rows and legitimate update"}


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
    if not re.fullmatch(r"yuheng_t4_owner_[0-9]{8}(?:_[a-z0-9]+)?", args.schema):
        parser.error("only yuheng_t4_owner_YYYYMMDD[_suffix] disposable schemas are allowed")
    probe = OwnerProbe(args)
    probe.case = "setup"
    try:
        result = probe.run()
    except Exception as error:
        args.output.write_text(json.dumps({"result": "FAIL", "case": probe.case, "error": str(error),
                                         "requests": probe.events}, ensure_ascii=False, indent=2) + "\n")
        raise
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"result": result["result"], "requests": len(probe.events)}))


if __name__ == "__main__":
    main()
