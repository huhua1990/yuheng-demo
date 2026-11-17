#!/usr/bin/env python3
"""Verify ERP two-line returns on an explicitly isolated, empty local JAR.

The operator must verify the JAR datasource before running this script. Schema,
service and Redis lifecycle are intentionally managed outside the probe.
"""
import argparse
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from erp_workflow_probe import Probe


def money(value):
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class ReturnsProbe(Probe):
    def call(self, method, path, body=None, code=0):
        headers = {"Content-Type": "application/json", "tenant-id": "1"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        request = Request(self.args.base_url + "/admin-api" + path, method=method,
                          headers=headers, data=json.dumps(body).encode() if body is not None else None)
        try:
            response = urlopen(request, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            status, data = response.status, json.load(response, parse_float=Decimal)
        self.events.append({"method": method, "path": path, "http": status,
                            "code": data.get("code"), "msg": data.get("msg")})
        assert status == 200 and data.get("code") == code, (method, path, status, data.get("code"), data.get("msg"))
        return data.get("data")

    def snapshot(self):
        tables = ["erp_stock", "erp_stock_record", "erp_finance_payment", "erp_finance_payment_item",
                  "erp_finance_receipt", "erp_finance_receipt_item"]
        tables += ["erp_" + kind + suffix for kind in ("purchase", "sale")
                   for suffix in ("_order", "_order_items", "_return", "_return_items")]
        return {table: self.sql(f"SELECT * FROM {table} ORDER BY id;") for table in tables}

    def stock(self, counts):
        actual = self.sql("SELECT product_id,`count` FROM erp_stock WHERE deleted=0 ORDER BY product_id;")
        expected = "\n".join(f"{product}\t{count:.6f}" for product, count in zip(self.products, counts))
        assert actual == expected, (actual, expected)

    def amounts(self, resource, identifier, lines, discount="7.5", other="0.03"):
        data = self.get(resource, identifier)
        expected_lines = []
        for line in lines:
            total = money(Decimal(line["productPrice"]) * Decimal(line["count"]))
            tax = money(total * Decimal(line["taxPercent"]) / 100)
            expected_lines.append((total, tax))
        items = sorted(data["items"], key=lambda item: item["productId"])
        for item, line, (total, tax) in zip(items, lines, expected_lines):
            # The upstream response Item exposes taxPrice, but not totalPrice;
            # verify persisted line totals below instead of inventing an API field.
            for field, expected in (("productPrice", line["productPrice"]), ("count", line["count"]),
                                    ("taxPrice", tax)):
                self.equal(item[field], expected)
        assert len(items) == len(lines) == 2
        subtotal = sum((row[0] for row in expected_lines), Decimal(0))
        tax = sum((row[1] for row in expected_lines), Decimal(0))
        reduction = money((subtotal + tax) * Decimal(discount) / 100)
        totals = {"totalProductPrice": subtotal, "totalTaxPrice": tax,
                  "discountPrice": reduction,
                  "totalPrice": subtotal + tax - reduction + Decimal(other),
                  "totalCount": sum((Decimal(line["count"]) for line in lines), Decimal(0))}
        for field, expected in totals.items():
            self.equal(data[field], expected)
        table = "erp_" + resource.replace("-", "_")
        db = self.sql(f"SELECT total_product_price,total_tax_price,discount_price,total_price,total_count "
                      f"FROM {table} WHERE id={int(identifier)};").split("\t")
        for actual, expected in zip(db, totals.values()):
            self.equal(actual, expected)
        item_parent = "return_id" if resource.endswith("return") else "order_id"
        db_items = self.sql(f"SELECT product_price,`count`,total_price,tax_price FROM {table}_items "
                            f"WHERE {item_parent}={int(identifier)} AND deleted=0 ORDER BY product_id;")
        assert len(db_items.splitlines()) == 2
        for row, line, (total, tax) in zip(db_items.splitlines(), lines, expected_lines):
            for actual, expected in zip(row.split("\t"), (line["productPrice"], line["count"], total, tax)):
                self.equal(actual, expected)
        self.checks.append({"resource": resource, "id": identifier,
                            "totals": {key: str(value) for key, value in totals.items()}})
        return data

    def run(self):
        self.checks = []
        assert self.sql("SELECT DATABASE();") == self.args.schema
        assert self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;") == "54"
        assert self.sql("SELECT COUNT(*) FROM erp_product;") == "0", "fresh schema required"
        self.snapshot()  # Fail before API writes if current table names do not match.
        # Keep the complete comparison only in memory; GROUP_CONCAT can truncate.
        seed_passwords = self.sql("SELECT id,password FROM system_users ORDER BY id;")
        self.token = self.call("POST", "/system/auth/login", {
            "username": os.environ["YUHENG_PROBE_USERNAME"],
            "password": os.environ["YUHENG_PROBE_PASSWORD"]})["accessToken"]
        category = self.create("product-category", {"parentId": 0, "name": "RET category", "code": "RET", "sort": 1, "status": 0})
        unit = self.create("product-unit", {"name": "RET unit", "status": 0})
        supplier = self.create("supplier", {"name": "RET supplier", "sort": 1, "status": 0})
        customer = self.create("customer", {"name": "RET customer", "sort": 1, "status": 0})
        account = self.create("account", {"name": "RET account", "no": "RET", "sort": 1, "status": 0})
        warehouse = self.create("warehouse", {"name": "RET warehouse", "sort": 1, "status": 0})
        self.products = [self.create("product", {"name": f"RET product {index}", "barCode": f"RET-{index}",
                         "categoryId": category, "unitId": unit, "status": 0,
                         "purchasePrice": "1.234567", "salePrice": "3.456789", "minPrice": "0.01"}) for index in (1, 2)]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        baseline = [Decimal("7.000000"), Decimal("6.000000")]
        documents = {}
        for kind, party, party_id, prices, counts, move, date_field in (
            ("purchase", "supplierId", supplier, ("1.234567", "2.345678"), ("10.125", "8.375"), "in", "inTime"),
            ("sale", "customerId", customer, ("3.456789", "4.567891"), ("3.125", "2.375"), "out", "outTime"),
        ):
            lines = [{"productId": product, "productUnitId": unit, "productPrice": price,
                      "count": count, "taxPercent": tax} for product, price, count, tax in
                     zip(self.products, prices, counts, ("13", "6"))]
            order = self.create(kind + "-order", {party: party_id, "accountId": account,
                "orderTime": now, "discountPercent": "7.5", "depositPrice": 0, "items": lines})
            # Orders have no other-price field; use the same line-level rounding oracle.
            order_data = self.amounts(kind + "-order", order, lines, other="0")
            self.status(kind + "-order", order)
            order_lines = sorted(order_data["items"], key=lambda item: item["productId"])
            move_lines = [dict(line, orderItemId=item["id"], warehouseId=warehouse)
                          for line, item in zip(lines, order_lines)]
            movement = self.create(kind + "-" + move, {"orderId": order, "accountId": account,
                date_field: now, "discountPercent": "7.5", "otherPrice": "0.03", "items": move_lines})
            self.status(kind + "-" + move, movement)
            documents[kind] = (order, order_lines, prices)
        self.stock(baseline)

        for kind, return_counts, sign, exceed_code, approved_code, finance, party, party_id, biz_type, value_field, prior_field in (
            ("purchase", ("0.125", "0.375"), -1, 1030101009, 1030103, "finance-payment", "supplierId", supplier, 12, "paymentPrice", "paidPrice"),
            ("sale", ("0.025", "0.075"), 1, 1020201009, 1020203, "finance-receipt", "customerId", customer, 22, "receiptPrice", "receiptedPrice"),
        ):
            order, order_lines, prices = documents[kind]
            resource = kind + "-return"
            lines = [{"productId": product, "productUnitId": unit, "orderItemId": source["id"],
                      "warehouseId": warehouse, "productPrice": price, "count": count, "taxPercent": tax}
                     for product, source, price, count, tax in
                     zip(self.products, order_lines, prices, return_counts, ("13", "6"))]
            body = {"orderId": order, "accountId": account, "returnTime": now,
                    "discountPercent": "7.5", "otherPrice": "0.03", "items": lines}
            before = self.snapshot()
            invalid = dict(body, items=[dict(lines[0]), dict(lines[1], count="99")])
            self.create(resource, invalid, code=exceed_code)
            assert self.snapshot() == before, "second-line overflow must roll back header, lines and first-line order progress"
            identifier = self.create(resource, body)
            self.amounts(resource, identifier, lines)
            expected_return = sum(map(Decimal, return_counts))
            self.equal(self.get(kind + "-order", order)["returnCount"], expected_return)
            self.stock(baseline)
            adjusted = [value + sign * Decimal(count) for value, count in zip(baseline, return_counts)]
            for status, expected in ((20, adjusted), (10, baseline), (20, adjusted)):
                self.status(resource, identifier, status=status)
                self.stock(expected)
                self.equal(self.get(kind + "-order", order)["returnCount"], expected_return)
            before = self.snapshot()
            self.status(resource, identifier, code=approved_code * 1000 + 3)
            self.call("PUT", f"/erp/{resource}/update", dict(body, id=identifier), code=approved_code * 1000 + 5)
            self.call("DELETE", f"/erp/{resource}/delete?ids={identifier}", code=approved_code * 1000 + 1)
            assert self.snapshot() == before, "approved edit/delete/reapproval must preserve data"

            # Negative finance items represent refunds. They reserve the source
            # return amount at creation, independently of finance audit status.
            total = Decimal(str(self.get(resource, identifier)["totalPrice"]))
            finance_prefix = 1030601 if kind == "purchase" else 1030602
            refund_body = {party: party_id, "accountId": account, "discountPrice": 0,
                ("paymentTime" if kind == "purchase" else "receiptTime"): now,
                "items": [{"bizType": biz_type, "bizId": identifier, prior_field: "0",
                           value_field: str(-total)}]}
            finance_id = self.create(finance, refund_body)
            self.equal(self.get(resource, identifier)["refundPrice"], total)
            finance_data = self.get(finance, finance_id)
            self.equal(finance_data["totalPrice"], -total)
            self.equal(finance_data[value_field], -total)
            self.equal(finance_data["items"][0]["totalPrice"], -total)
            self.equal(finance_data["items"][0][value_field], -total)
            before = self.snapshot()
            self.status(resource, identifier, status=10, code=approved_code * 1000 + 8)
            extra = dict(refund_body, items=[{"bizType": biz_type, "bizId": identifier,
                          prior_field: str(-total), value_field: "-0.01"}])
            self.create(finance, extra, code=approved_code * 1000 + 7)
            assert self.snapshot() == before, "refund excess and return reversal must roll back all rows"
            self.status(finance, finance_id)
            self.call("DELETE", f"/erp/{finance}/delete?ids={finance_id}", code=finance_prefix * 1000 + 1)
            self.equal(self.get(resource, identifier)["refundPrice"], total)
            self.status(finance, finance_id, status=10)
            self.equal(self.get(resource, identifier)["refundPrice"], total)
            self.call("DELETE", f"/erp/{finance}/delete?ids={finance_id}")
            self.equal(self.get(resource, identifier)["refundPrice"], 0)
            self.status(resource, identifier, status=10)
            self.stock(baseline)
            self.call("DELETE", f"/erp/{resource}/delete?ids={identifier}")
            self.equal(self.get(kind + "-order", order)["returnCount"], 0)
            assert self.sql(f"SELECT COUNT(*) FROM erp_{kind}_return WHERE deleted=0;") == "0"
            assert self.sql(f"SELECT COUNT(*) FROM erp_{kind}_return_items WHERE deleted=0;") == "0"
            self.stock(baseline)
        assert self.sql("SELECT COUNT(*) FROM erp_stock_record WHERE deleted=0;") == "20"
        movements = self.sql("SELECT biz_type,COUNT(*) FROM erp_stock_record WHERE deleted=0 GROUP BY biz_type ORDER BY biz_type;")
        assert movements == "50\t2\n60\t4\n61\t4\n70\t2\n80\t4\n81\t4", movements
        assert self.sql("SELECT COUNT(*) FROM erp_stock WHERE deleted=0 AND tenant_id<>1;") == "0"
        assert self.sql("SELECT id,password FROM system_users ORDER BY id;") == seed_passwords, "seed passwords changed"
        return {"result": "PASS", "schema": self.args.schema, "port": urlparse(self.args.base_url).port,
                "time": datetime.now().astimezone().isoformat(), "requests": self.events, "amount_checks": self.checks,
                "assertions": {"two_line_purchase_and_sale_returns": True, "line_half_up_scale": 2,
                    "second_line_overflow_full_rollback": True, "approval_reverse_delete_stock_consistency": True,
                    "refund_finance_reservation_excess_rollback_and_release": True,
                    "final_stock": [str(value) for value in baseline], "stock_record_count": 20,
                    "seed_passwords_unchanged": True, "supplementary_workflows_not_covered": "finance update; negative/illegal status inputs; UI acceptance"}}


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
        parser.error("use a dedicated loopback HTTP port without path or credentials")
    if not re.fullmatch(r"yuheng_t4_returns_[0-9]{8}(?:_[a-z0-9]+)?", args.schema):
        parser.error("only yuheng_t4_returns_YYYYMMDD[_suffix] disposable schemas are allowed")
    probe = ReturnsProbe(args)
    try:
        result = probe.run()
    except Exception as error:
        args.output.write_text(json.dumps({"result": "FAIL", "error": str(error),
            "requests": probe.events}, ensure_ascii=False, indent=2) + "\n")
        raise
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"result": result["result"], "requests": len(probe.events),
                      "assertions": result["assertions"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
