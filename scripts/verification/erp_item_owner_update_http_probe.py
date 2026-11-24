#!/usr/bin/env python3
"""Verify update-time ERP child-ID ownership with real rows in a disposable schema."""
from datetime import datetime
import argparse
import json
import os
from pathlib import Path
import re
from urllib.parse import urlencode, urlparse

from erp_item_owner_http_probe import OwnerProbe


CASES = {
    "purchase-order": 1030101011,
    "purchase-in": 1030102009,
    "purchase-return": 1030103009,
    "sale-order": 1020201011,
    "sale-out": 1020202009,
    "sale-return": 1020203009,
    "stock-in": 1030401099,
    "stock-out": 1030402099,
    "stock-check": 1030410000,
    "stock-move": 1030410001,
}
ITEM_TABLES = {
    "purchase-order": ("erp_purchase_order_items", "order_id"),
    "purchase-in": ("erp_purchase_in_items", "in_id"),
    "purchase-return": ("erp_purchase_return_items", "return_id"),
    "sale-order": ("erp_sale_order_items", "order_id"),
    "sale-out": ("erp_sale_out_items", "out_id"),
    "sale-return": ("erp_sale_return_items", "return_id"),
    "stock-in": ("erp_stock_in_item", "in_id"),
    "stock-out": ("erp_stock_out_item", "out_id"),
    "stock-check": ("erp_stock_check_item", "check_id"),
    "stock-move": ("erp_stock_move_item", "move_id"),
}


class UpdateOwnerProbe(OwnerProbe):
    def make_order(self, kind, party_id, unit, product, now, account=None):
        party_field = "supplierId" if kind == "purchase" else "customerId"
        body = {party_field: party_id, "orderTime": now, "discountPercent": 0,
                "items": [{"productId": product, "productUnitId": unit,
                           "productPrice": 10, "count": 10, "taxPercent": 0}]}
        if account is not None:
            body["accountId"] = account
            body["depositPrice"] = 0
        identifier = self.create(kind + "-order", body)
        item = self.get(kind + "-order", identifier)["items"][0]
        return identifier, item["id"], body

    def pair(self, resource, header, item, time_field=None):
        def body_with(item_id):
            line = dict(item, id=item_id)
            body = dict(header, items=[line])
            return body
        first = self.create(resource, body_with(None))
        second = self.create(resource, body_with(None))
        first_data = self.get(resource, first)
        second_data = self.get(resource, second)
        first_item = first_data["items"][0]["id"]
        foreign_item = second_data["items"][0]["id"]
        update = body_with(foreign_item)
        update["id"] = first
        before = self.snapshot()
        self.call("PUT", f"/erp/{resource}/update", update, code=CASES[resource])
        assert self.snapshot() == before, f"{resource} foreign item update changed persisted rows"
        missing = body_with(987654321)
        missing["id"] = first
        self.call("PUT", f"/erp/{resource}/update", missing, code=CASES[resource])
        assert self.snapshot() == before, f"{resource} missing item update changed persisted rows"
        duplicate = body_with(first_item)
        duplicate["items"].append(dict(duplicate["items"][0]))
        duplicate["id"] = first
        self.call("PUT", f"/erp/{resource}/update", duplicate, code=CASES[resource])
        assert self.snapshot() == before, f"{resource} duplicate item update changed persisted rows"
        table, parent_column = ITEM_TABLES[resource]
        tenant_item_id = 987654000 + len(self.events)
        columns = self.sql(f"SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='{self.args.schema}' AND TABLE_NAME='{table}' ORDER BY ORDINAL_POSITION;").splitlines()
        assert "id" in columns and "tenant_id" in columns and parent_column in columns, (table, columns)
        select_values = []
        for column in columns:
            if column == "id":
                select_values.append(str(tenant_item_id))
            elif column == "tenant_id":
                select_values.append("999")
            else:
                select_values.append(f"`{column}`")
        sql = (f"INSERT INTO `{table}` ({','.join('`'+column+'`' for column in columns)}) "
               f"SELECT {','.join(select_values)} FROM `{table}` WHERE id={first_item} LIMIT 1;")
        self.sql(sql)
        assert self.sql(f"SELECT tenant_id FROM `{table}` WHERE id={tenant_item_id};") == "999"
        tenant_case = body_with(tenant_item_id)
        tenant_case["id"] = first
        before = self.snapshot()
        self.call("PUT", f"/erp/{resource}/update", tenant_case, code=CASES[resource])
        assert self.snapshot() == before, f"{resource} cross-tenant child update changed persisted rows"
        return {"resource": resource, "firstId": first, "firstItemId": first_item,
                "foreignItemId": foreign_item, "missingItemId": 987654321,
                "duplicateItemId": first_item, "crossTenantItemId": tenant_item_id,
                "errorCode": CASES[resource]}

    def run(self):
        assert self.sql("SELECT DATABASE();") == self.args.schema
        self.installed_changesets(self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;"))
        assert self.sql("SELECT COUNT(*) FROM erp_product;") == "0"
        self.snapshot()
        seed_passwords = self.sql("SELECT id,password FROM system_users ORDER BY id;")
        login = self.call("POST", "/system/auth/login", {
            "username": os.environ["YUHENG_PROBE_USERNAME"],
            "password": os.environ["YUHENG_PROBE_PASSWORD"]})
        self.token = login["accessToken"]
        category = self.create("product-category", {"parentId": 0, "name": "OWNER category",
            "code": "OWNER-UPD", "sort": 1, "status": 0})
        unit = self.create("product-unit", {"name": "OWNER unit", "status": 0})
        supplier = self.create("supplier", {"name": "OWNER supplier", "sort": 1, "status": 0})
        customer = self.create("customer", {"name": "OWNER customer", "sort": 1, "status": 0})
        account = self.create("account", {"name": "OWNER account", "no": "OWNER-UPD", "sort": 1, "status": 0})
        warehouse1 = self.create("warehouse", {"name": "OWNER warehouse 1", "sort": 1, "status": 0})
        warehouse2 = self.create("warehouse", {"name": "OWNER warehouse 2", "sort": 2, "status": 0})
        product = self.create("product", {"name": "OWNER product", "barCode": "OWNER-UPD",
            "categoryId": category, "unitId": unit, "status": 0,
            "purchasePrice": 10, "salePrice": 10, "minPrice": 1})
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        results = []

        # Order documents are created pending so their own update remains legal.
        for kind, party in (("purchase", supplier), ("sale", customer)):
            identifier, item_id, body = self.make_order(kind, party, unit, product, now, account)
            second, foreign_id, _ = self.make_order(kind, party, unit, product, now, account)
            body["id"] = identifier
            body["items"][0]["id"] = foreign_id
            before = self.snapshot()
            resource = kind + "-order"
            self.call("PUT", f"/erp/{resource}/update", body, code=CASES[resource])
            assert self.snapshot() == before, f"{resource} update was not rolled back"
            results.append({"resource": resource, "id": identifier, "ownItemId": item_id,
                            "foreignItemId": foreign_id, "errorCode": CASES[resource]})

        purchase_approved = []
        for _ in range(2):
            order, order_item, _ = self.make_order("purchase", supplier, unit, product, now, account)
            self.status("purchase-order", order)
            purchase_approved.append((order, order_item))
        sale_approved = []
        for _ in range(2):
            order, order_item, _ = self.make_order("sale", customer, unit, product, now, account)
            self.status("sale-order", order)
            sale_approved.append((order, order_item))

        inbound = self.create("purchase-in", {"orderId": purchase_approved[0][0],
            "accountId": account, "inTime": now, "discountPercent": 0, "otherPrice": 0,
            "items": [{"orderItemId": purchase_approved[0][1], "warehouseId": warehouse1,
                "productId": product, "productUnitId": unit, "productPrice": 10, "count": 2,
                "taxPercent": 0}]})
        self.status("purchase-in", inbound)
        outbound = self.create("sale-out", {"orderId": sale_approved[0][0],
            "accountId": account, "outTime": now, "discountPercent": 0, "otherPrice": 0,
            "items": [{"orderItemId": sale_approved[0][1], "warehouseId": warehouse1,
                "productId": product, "productUnitId": unit, "productPrice": 10, "count": 1,
                "taxPercent": 0}]})
        self.status("sale-out", outbound)

        purchase_in_header = {"orderId": purchase_approved[0][0], "accountId": account,
            "inTime": now, "discountPercent": 0, "otherPrice": 0}
        purchase_in_item = {"orderItemId": purchase_approved[0][1], "warehouseId": warehouse1,
            "productId": product, "productUnitId": unit, "productPrice": 10, "count": 1,
            "taxPercent": 0}
        results.append(self.pair("purchase-in", purchase_in_header, purchase_in_item))

        purchase_return_header = {"orderId": purchase_approved[0][0], "accountId": account,
            "returnTime": now, "discountPercent": 0, "otherPrice": 0}
        purchase_return_item = {"orderItemId": purchase_approved[0][1], "warehouseId": warehouse1,
            "productId": product, "productUnitId": unit, "productPrice": 10, "count": 1,
            "taxPercent": 0}
        results.append(self.pair("purchase-return", purchase_return_header, purchase_return_item))

        sale_out_header = {"orderId": sale_approved[0][0], "accountId": account,
            "outTime": now, "discountPercent": 0, "otherPrice": 0}
        sale_out_item = {"orderItemId": sale_approved[0][1], "warehouseId": warehouse1,
            "productId": product, "productUnitId": unit, "productPrice": 10, "count": 1,
            "taxPercent": 0}
        results.append(self.pair("sale-out", sale_out_header, sale_out_item))

        sale_return_header = {"orderId": sale_approved[0][0], "accountId": account,
            "returnTime": now, "discountPercent": 0, "otherPrice": 0}
        sale_return_item = {"orderItemId": sale_approved[0][1], "warehouseId": warehouse1,
            "productId": product, "productUnitId": unit, "productPrice": 10, "count": 1,
            "taxPercent": 0}
        results.append(self.pair("sale-return", sale_return_header, sale_return_item))

        for resource, header, extra in (
            ("stock-in", {"supplierId": supplier, "inTime": now}, {"warehouseId": warehouse1, "productId": product,
                "productPrice": 10, "count": 1}),
            ("stock-out", {"customerId": customer, "outTime": now}, {"warehouseId": warehouse1, "productId": product,
                "productPrice": 10, "count": 1}),
            ("stock-check", {"checkTime": now}, {"warehouseId": warehouse1, "productId": product,
                "productPrice": 10, "stockCount": 0, "actualCount": 0, "count": 0}),
        ):
            results.append(self.pair(resource, header, extra))
        results.append(self.pair("stock-move", {"moveTime": now}, {
            "fromWarehouseId": warehouse1, "toWarehouseId": warehouse2,
            "productId": product, "productPrice": 10, "count": 1}))

        assert self.sql("SELECT id,password FROM system_users ORDER BY id;") == seed_passwords
        return {"result": "PASS", "schema": self.args.schema, "requests": self.events,
                "cases": results, "scope": "real HTTP foreign, missing, duplicate and SQL-created tenant-999 item ID updates for ten document endpoints; full row snapshots unchanged"}


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
    if not re.fullmatch(r"yuheng_t4_item_update_[0-9]{8}(?:_[a-z0-9]+)?", args.schema):
        parser.error("only yuheng_t4_item_update_YYYYMMDD[_suffix] disposable schemas are allowed")
    probe = UpdateOwnerProbe(args)
    try:
        result = probe.run()
    except Exception as error:
        args.output.write_text(json.dumps({"result": "FAIL", "error": str(error),
            "requests": probe.events}, ensure_ascii=False, indent=2) + "\n")
        raise
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"result": result["result"], "requests": len(result["requests"]),
                      "cases": len(result["cases"])}))


if __name__ == "__main__":
    main()
