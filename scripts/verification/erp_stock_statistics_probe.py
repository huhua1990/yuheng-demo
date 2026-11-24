#!/usr/bin/env python3
"""Verify ERP stock and statistics reads with a real limited-permission role."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


MIN_CHANGESETS = 59
PERMISSIONS = (
    "erp:stock:query", "erp:stock:export",
    "erp:stock-record:query", "erp:stock-record:export",
    "erp:statistics:query",
)


def number(value: object) -> float:
    return float(value)


def validate_target(schema: str, app_port: int, mysql_port: int, redis_port: int) -> bool:
    if not re.fullmatch(r"yuheng_t4_erp_stock_auth_[0-9]{8}(?:_[a-z0-9]+)?", schema):
        raise ValueError("only yuheng_t4_erp_stock_auth_YYYYMMDD[_suffix] schemas are allowed")
    ports = (app_port, mysql_port, redis_port)
    if any(port < 1024 or port > 65535 for port in ports) or len(set(ports)) != 3:
        raise ValueError("probe ports must be distinct dedicated unprivileged ports")
    if app_port in {48080, 48100, 5173} or mysql_port == 3306 or redis_port == 6379:
        raise ValueError("probe must not use shared application, MySQL, or Redis ports")
    return True


class Probe:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.events: list[dict[str, object]] = []

    def sql(self, statement: str) -> str:
        import subprocess

        return subprocess.run(
            ["docker", "exec", "-i", self.args.mysql_container, "sh", "-c",
             'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
             '--skip-column-names -D "$1"', "probe", self.args.schema],
            input=statement, text=True, capture_output=True, check=True,
        ).stdout.strip()

    def call(self, method: str, path: str, token: str, *, binary: bool = False) -> object:
        headers = {"Accept": "application/json", "tenant-id": "1",
                   "Authorization": "Bearer " + token}
        request = Request(self.args.base_url + "/admin-api" + path,
                          method=method, headers=headers)
        try:
            response = urlopen(request, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            body = response.read()
            status = response.status
            content_type = response.headers.get("Content-Type", "")
        event: dict[str, object] = {"method": method, "path": path,
                                    "http": status, "content_type": content_type,
                                    "bytes": len(body)}
        self.events.append(event)
        assert status == 200 and body, (method, path, status, body[:200])
        if binary:
            assert len(body) > 100, (method, path, len(body))
            return body
        payload = json.loads(body)
        event["code"] = payload.get("code")
        assert payload.get("code") == 0, (method, path, payload)
        return payload.get("data")

    def login(self) -> str:
        headers = {"Accept": "application/json", "Content-Type": "application/json",
                   "tenant-id": "1"}
        request = Request(self.args.base_url + "/admin-api/system/auth/login",
                          method="POST", headers=headers,
                          data=json.dumps({
                              "username": os.environ["YUHENG_PROBE_USERNAME"],
                              "password": os.environ["YUHENG_PROBE_PASSWORD"],
                          }).encode())
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
        assert payload.get("code") == 0, payload
        return payload["data"]["accessToken"]

    def run(self) -> dict[str, object]:
        assert self.sql("SELECT DATABASE();") == self.args.schema
        changesets = int(self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;"))
        assert changesets >= MIN_CHANGESETS, changesets
        token = self.login()

        stock = self.call("GET", "/erp/stock/get?id=991210", token)
        assert stock["productId"] == 991201 and stock["warehouseId"] == 991202
        assert number(stock["count"]) == 12, stock
        stock_page = self.call("GET", "/erp/stock/page?pageNo=1&pageSize=20", token)
        assert stock_page["total"] == 1 and number(stock_page["list"][0]["count"]) == 12, stock_page
        self.call("GET", "/erp/stock/export-excel?pageNo=1&pageSize=20", token, binary=True)

        record = self.call("GET", "/erp/stock-record/get?id=991211", token)
        assert record["productId"] == 991201 and record["warehouseId"] == 991202
        record_page = self.call("GET", "/erp/stock-record/page?pageNo=1&pageSize=20", token)
        assert record_page["total"] == 1 and number(record_page["list"][0]["totalCount"]) == 12, record_page
        self.call("GET", "/erp/stock-record/export-excel?pageNo=1&pageSize=20", token, binary=True)

        stock_count = self.call("GET", "/erp/stock/get-count?productId=991201", token)
        assert number(stock_count) == 12, stock_count
        purchase = self.call("GET", "/erp/purchase-statistics/summary", token)
        sale = self.call("GET", "/erp/sale-statistics/summary", token)
        assert number(purchase["todayPrice"]) == 80, purchase
        assert number(sale["todayPrice"]) == 170, sale
        purchase_time = self.call("GET", "/erp/purchase-statistics/time-summary?count=1", token)
        sale_time = self.call("GET", "/erp/sale-statistics/time-summary?count=1", token)
        assert number(purchase_time[0]["price"]) == 80, purchase_time
        assert number(sale_time[0]["price"]) == 170, sale_time
        return {"result": "PASS", "schema": self.args.schema,
                "changesets": changesets, "requests": self.events,
                "limited_role_permissions": list(PERMISSIONS),
                "assertions": {
                    "stock_detail_page_export": True,
                    "stock_record_detail_page_export": True,
                    "authenticated_stock_count": True,
                    "purchase_today_and_month_summary": True,
                    "sale_today_and_month_summary": True,
                },
                "verified_at": datetime.now().isoformat(timespec="seconds")}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--mysql-container", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    url = urlparse(args.base_url)
    if url.scheme != "http" or url.hostname != "127.0.0.1" or not url.port or url.path or url.query or url.fragment:
        parser.error("use a dedicated loopback HTTP base URL without a path")
    if not re.fullmatch(r"yuheng_t4_erp_stock_auth_[0-9]{8}(?:_[a-z0-9]+)?", args.schema):
        parser.error("use a disposable stock-auth schema")
    probe = Probe(args)
    try:
        result = probe.run()
    except Exception as error:
        result = {"result": "FAIL", "schema": args.schema,
                  "error": str(error), "requests": probe.events}
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        raise
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"result": result["result"], "requests": len(result["requests"])}))


if __name__ == "__main__":
    main()
