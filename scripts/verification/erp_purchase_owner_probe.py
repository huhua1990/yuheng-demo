#!/usr/bin/env python3
"""Opt-in purchase order item ownership checks on a disposable isolated JAR."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
from urllib.parse import urlparse

from erp_returns_probe import ReturnsProbe


class PurchaseOwnerProbe(ReturnsProbe):
    def run(self):
        assert self.sql("SELECT DATABASE();") == self.args.schema
        assert self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;") == "54"
        assert self.sql("SELECT COUNT(*) FROM erp_product;") == "0"
        self.snapshot()
        passwords = self.sql("SELECT id,password FROM system_users ORDER BY id;")
        self.token = self.call("POST", "/system/auth/login", {"username": os.environ["YUHENG_PROBE_USERNAME"],
                           "password": os.environ["YUHENG_PROBE_PASSWORD"]})["accessToken"]
        category = self.create("product-category", {"parentId": 0, "name": "PO category", "code": "PO-OWN", "sort": 1, "status": 0})
        unit = self.create("product-unit", {"name": "PO unit", "status": 0})
        supplier = self.create("supplier", {"name": "PO supplier", "sort": 1, "status": 0})
        product = self.create("product", {"name": "PO product", "barCode": "PO-OWN", "categoryId": category,
                                          "unitId": unit, "status": 0, "purchasePrice": 10, "salePrice": 10, "minPrice": 1})
        item = {"productId": product, "productUnitId": unit, "productPrice": 10, "count": 1, "taxPercent": 0}
        body = {"supplierId": supplier, "orderTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "discountPercent": 0, "depositPrice": 0, "items": [item]}
        first = self.create("purchase-order", body)
        second = self.create("purchase-order", body)
        first_item = self.get("purchase-order", first)["items"][0]["id"]
        second_item = self.get("purchase-order", second)["items"][0]["id"]
        self.sql(f"INSERT INTO erp_purchase_order_items (id,order_id,product_id,product_unit_id,product_price,`count`,total_price,tenant_id) "
                 f"VALUES (899999101,899999100,{product},{unit},10,1,10,999);")
        before = self.snapshot()
        for case, method, payload in (
            ("foreign", "PUT", dict(body, id=first, items=[dict(item, id=second_item)])),
            ("missing", "PUT", dict(body, id=first, items=[dict(item, id=999999999)])),
            ("duplicate", "PUT", dict(body, id=first, items=[dict(item, id=first_item), dict(item, id=first_item)])),
            ("other-tenant", "PUT", dict(body, id=first, items=[dict(item, id=899999101)])),
            ("create-with-id", "POST", dict(body, items=[dict(item, id=999999998)])),
        ):
            self.case = case
            self.call(method, "/erp/purchase-order/" + ("update" if method == "PUT" else "create"),
                      payload, code=1030101011)
            assert self.snapshot() == before, "invalid item ID must leave all rows unchanged"
        self.call("PUT", "/erp/purchase-order/update", dict(body, id=first, items=[dict(item, id=first_item, count=2)]))
        self.equal(self.get("purchase-order", first)["totalCount"], 2)
        assert self.sql("SELECT id,password FROM system_users ORDER BY id;") == passwords
        return {"result": "PASS", "schema": self.args.schema, "port": urlparse(self.args.base_url).port,
                "requests": self.events, "scope": "purchase order foreign, missing, duplicate, SQL other-tenant and create-time IDs; valid update"}


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
    if not re.fullmatch(r"yuheng_t4_po_[0-9]{8}(?:_[a-z0-9]+)?", args.schema):
        parser.error("only yuheng_t4_po_YYYYMMDD[_suffix] disposable schemas are allowed")
    probe = PurchaseOwnerProbe(args)
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
