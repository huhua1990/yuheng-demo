#!/usr/bin/env python3
"""Verify stock-in/out, move and check approval/reversal stock lifecycles."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import os
from pathlib import Path
import re
import threading
from urllib.parse import urlencode, urlparse

from erp_workflow_probe import Probe


class StockLifecycleProbe(Probe):
    def stock(self):
        rows = self.sql("SELECT warehouse_id,`count` FROM erp_stock "
                        "WHERE deleted=0 ORDER BY warehouse_id;").splitlines()
        return [tuple(row.split("\t")) for row in rows]

    def expect_stock(self, expected):
        actual = self.stock()
        assert actual == expected, (actual, expected)

    def run(self):
        assert self.sql("SELECT DATABASE();") == self.args.schema
        changesets = self.installed_changesets(self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;"))
        assert self.sql("SELECT COUNT(*) FROM erp_product;") == "0", "fresh schema required"
        self.token = self.call("POST", "/system/auth/login", {
            "username": os.environ["YUHENG_PROBE_USERNAME"],
            "password": os.environ["YUHENG_PROBE_PASSWORD"]})["accessToken"]
        category = self.create("product-category", {"parentId": 0, "name": "LIFE category",
            "code": "LIFE", "sort": 1, "status": 0})
        unit = self.create("product-unit", {"name": "LIFE unit", "status": 0})
        supplier = self.create("supplier", {"name": "LIFE supplier", "sort": 1, "status": 0})
        customer = self.create("customer", {"name": "LIFE customer", "sort": 1, "status": 0})
        warehouse1 = self.create("warehouse", {"name": "LIFE warehouse 1", "sort": 1, "status": 0})
        warehouse2 = self.create("warehouse", {"name": "LIFE warehouse 2", "sort": 2, "status": 0})
        product = self.create("product", {"name": "LIFE product", "barCode": "LIFE",
            "categoryId": category, "unitId": unit, "status": 0,
            "purchasePrice": 1, "salePrice": 1, "minPrice": 1})
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stock_in = self.create("stock-in", {"supplierId": supplier, "inTime": now,
            "items": [{"warehouseId": warehouse1, "productId": product,
                       "productPrice": 1, "count": 10}]})
        self.status("stock-in", stock_in)
        self.expect_stock([(str(warehouse1), "10.000000")])
        self.status("stock-in", stock_in, status=10)
        self.expect_stock([(str(warehouse1), "0.000000")])
        self.status("stock-in", stock_in)
        self.expect_stock([(str(warehouse1), "10.000000")])

        stock_out = self.create("stock-out", {"customerId": customer, "outTime": now,
            "items": [{"warehouseId": warehouse1, "productId": product,
                       "productPrice": 1, "count": 2}]})
        self.status("stock-out", stock_out)
        self.expect_stock([(str(warehouse1), "8.000000")])
        self.status("stock-out", stock_out, status=10)
        self.expect_stock([(str(warehouse1), "10.000000")])
        self.status("stock-out", stock_out)
        self.expect_stock([(str(warehouse1), "8.000000")])

        stock_move = self.create("stock-move", {"moveTime": now,
            "items": [{"fromWarehouseId": warehouse1, "toWarehouseId": warehouse2,
                       "productId": product, "productPrice": 1, "count": 3}]})
        self.status("stock-move", stock_move)
        self.expect_stock([(str(warehouse1), "5.000000"), (str(warehouse2), "3.000000")])
        self.status("stock-move", stock_move, status=10)
        self.expect_stock([(str(warehouse1), "8.000000"), (str(warehouse2), "0.000000")])
        self.status("stock-move", stock_move)
        self.expect_stock([(str(warehouse1), "5.000000"), (str(warehouse2), "3.000000")])

        stock_check = self.create("stock-check", {"checkTime": now,
            "items": [{"warehouseId": warehouse2, "productId": product,
                       "productPrice": 1, "stockCount": 3, "actualCount": 5, "count": 2}]})
        self.status("stock-check", stock_check)
        self.expect_stock([(str(warehouse1), "5.000000"), (str(warehouse2), "5.000000")])
        self.status("stock-check", stock_check, status=10)
        self.expect_stock([(str(warehouse1), "5.000000"), (str(warehouse2), "3.000000")])
        self.status("stock-check", stock_check)
        self.expect_stock([(str(warehouse1), "5.000000"), (str(warehouse2), "5.000000")])

        negative_check = self.create("stock-check", {"checkTime": now,
            "items": [{"warehouseId": warehouse2, "productId": product,
                       "productPrice": 1, "stockCount": 5, "actualCount": 2, "count": -3}]})
        self.status("stock-check", negative_check)
        self.expect_stock([(str(warehouse1), "5.000000"), (str(warehouse2), "2.000000")])
        self.status("stock-check", negative_check, status=10)
        self.expect_stock([(str(warehouse1), "5.000000"), (str(warehouse2), "5.000000")])
        self.status("stock-check", negative_check)
        self.expect_stock([(str(warehouse1), "5.000000"), (str(warehouse2), "2.000000")])

        insufficient_out = self.create("stock-out", {"customerId": customer, "outTime": now,
            "items": [{"warehouseId": warehouse1, "productId": product,
                       "productPrice": 1, "count": 1},
                      {"warehouseId": warehouse2, "productId": product,
                       "productPrice": 1, "count": 3}]})
        before_stock = self.stock()
        before_records = self.sql("SELECT COUNT(*) FROM erp_stock_record;")
        self.status("stock-out", insufficient_out, code=1030404000)
        self.equal(self.get("stock-out", insufficient_out)["status"], 10)
        self.expect_stock(before_stock)
        assert self.sql("SELECT COUNT(*) FROM erp_stock_record;") == before_records

        competitors = [self.create("stock-out", {"customerId": customer, "outTime": now,
            "items": [{"warehouseId": warehouse1, "productId": product,
                       "productPrice": 1, "count": 4}]}) for _ in range(2)]
        barrier = threading.Barrier(2)

        def approve_competitor(identifier):
            probe = Probe(self.args)
            probe.token = self.token
            barrier.wait(timeout=10)
            try:
                probe.status("stock-out", identifier)
                outcome = "approved"
            except AssertionError:
                event = probe.events[-1]
                assert event["http"] == 200 and event["code"] == 1030404000, event
                outcome = "insufficient"
            return outcome, probe.events

        before_records = int(self.sql("SELECT COUNT(*) FROM erp_stock_record;"))
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(approve_competitor, competitors))
        for _, events in outcomes:
            self.events.extend(events)
        assert sorted(outcome for outcome, _ in outcomes) == ["approved", "insufficient"], outcomes
        assert sorted(self.get("stock-out", identifier)["status"] for identifier in competitors) == [10, 20]
        self.expect_stock([(str(warehouse1), "1.000000"), (str(warehouse2), "2.000000")])
        assert int(self.sql("SELECT COUNT(*) FROM erp_stock_record;")) == before_records + 1
        return {"result": "PASS", "schema": self.args.schema, "changesets": changesets,
                "port": urlparse(self.args.base_url).port, "requests": self.events,
                "assertions": {"stock_in_approve_reverse_reapprove": True,
                    "stock_out_approve_reverse_reapprove": True,
                    "stock_move_two_warehouse_approve_reverse_reapprove": True,
                    "stock_check_positive_adjustment_approve_reverse_reapprove": True,
                    "stock_check_negative_adjustment_approve_reverse_reapprove": True,
                    "insufficient_stock_rolls_back_prior_line_status_and_records": True,
                    "concurrent_stock_out_one_approved_one_rejected": True,
                    "final_stock": self.stock()}}


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
    if not re.fullmatch(r"yuheng_t4_stock_lifecycle_[0-9]{8}(?:_[a-z0-9]+)?", args.schema):
        parser.error("only yuheng_t4_stock_lifecycle_YYYYMMDD[_suffix] disposable schemas are allowed")
    probe = StockLifecycleProbe(args)
    try:
        result = probe.run()
    except Exception as error:
        args.output.write_text(json.dumps({"result": "FAIL", "schema": args.schema,
            "error": str(error), "requests": probe.events}, ensure_ascii=False, indent=2) + "\n")
        raise
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"result": result["result"], "requests": len(result["requests"]),
                      "assertions": result["assertions"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
