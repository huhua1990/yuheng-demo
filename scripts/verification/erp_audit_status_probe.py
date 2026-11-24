#!/usr/bin/env python3
"""Verify unsupported ERP audit statuses are rejected before service writes."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


RESOURCES = (
    "purchase-order", "purchase-in", "purchase-return",
    "sale-order", "sale-out", "sale-return",
    "stock-in", "stock-out", "stock-check", "stock-move",
    "finance-payment", "finance-receipt",
)
MIN_CHANGESETS = 59


class Probe:
    def __init__(self, args):
        self.args = args
        self.token = None
        self.events = []

    def sql(self, statement):
        command = ["docker", "exec", "-i", self.args.mysql_container, "sh", "-c",
                   'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot -D "$1" '
                   '--batch --raw --skip-column-names -e "$2"', "probe", self.args.schema, statement]
        return subprocess.run(command, text=True, capture_output=True, check=True).stdout

    def snapshot(self):
        tables = self.sql("SELECT TABLE_NAME FROM information_schema.TABLES "
                          "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME LIKE 'erp\\_%' "
                          "ORDER BY TABLE_NAME;").splitlines()
        result = {}
        for table in tables:
            result[table] = self.sql(f"SELECT * FROM `{table}` ORDER BY id;")
        return result

    def call(self, method, path, body=None, expected_code=0):
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
            status, data = response.status, json.load(response)
        event = {"method": method, "path": path, "http": status, "code": data.get("code")}
        self.events.append(event)
        assert status == 200 and data.get("code") == expected_code, event
        return data

    def run(self):
        assert self.sql("SELECT DATABASE();").strip() == self.args.schema
        changesets = int(self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;").strip())
        assert changesets >= MIN_CHANGESETS, f"incomplete Liquibase installation: {changesets}"
        login = self.call("POST", "/system/auth/login", {
            "username": os.environ["YUHENG_PROBE_USERNAME"],
            "password": os.environ["YUHENG_PROBE_PASSWORD"]})
        self.token = login["data"]["accessToken"]

        self.baseline = self.snapshot()
        for resource in RESOURCES:
            path = "/erp/" + resource + "/update-status?" + urlencode({"id": 1, "status": 99})
            self.call("PUT", path, expected_code=400)
            assert self.snapshot() == self.baseline, f"{resource}: ERP rows changed for unsupported status"

        return {"result": "PASS", "schema": self.args.schema,
                "changesets": changesets,
                "port": urlparse(self.args.base_url).port,
                "time": datetime.now().astimezone().isoformat(), "requests": self.events,
                "assertions": {"unsupported_status_rejected_for_all_resources": len(RESOURCES),
                               "erp_full_row_snapshot_unchanged_after_each_request": True}}


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
    if not re.fullmatch(r"yuheng_t4_status_[0-9]{8}(?:_[a-z0-9]+)?", args.schema):
        parser.error("only yuheng_t4_status_YYYYMMDD[_suffix] disposable schemas are allowed")
    probe = Probe(args)
    try:
        result = probe.run()
    except Exception as error:
        args.output.write_text(json.dumps({"result": "FAIL", "schema": args.schema,
            "error": str(error), "requests": probe.events}, indent=2, ensure_ascii=False) + "\n")
        raise
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"result": result["result"], "requests": len(result["requests"]),
                      "assertions": result["assertions"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
