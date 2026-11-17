"""Opt-in warehouse boundary checks against an empty, disposable local JAR.

Requires YUHENG_TEST_URL, YUHENG_WAREHOUSE_PROBE_SCHEMA,
YUHENG_PROBE_USERNAME and YUHENG_PROBE_PASSWORD. The operator must verify the
JAR's actual datasource first. This test creates rows only in that instance;
schema lifecycle and dedicated Redis cleanup belong to the operator.
"""
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import unittest
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


SCHEMA = os.environ.get("YUHENG_WAREHOUSE_PROBE_SCHEMA")
BASE = os.environ.get("YUHENG_TEST_URL")


@unittest.skipUnless(SCHEMA and BASE, "requires explicitly configured disposable warehouse instance")
class ErpWarehouseHttpTest(unittest.TestCase):
    def test_name_boundaries_preserve_database_on_rejected_writes(self):
        url = urlparse(BASE)
        self.assertEqual(url.scheme, "http")
        self.assertEqual(url.hostname, "127.0.0.1")
        self.assertTrue(url.port and url.port not in (48080, 5173))
        self.assertFalse(url.path or url.username or url.query or url.fragment)
        self.assertRegex(SCHEMA, r"^yuheng_t4_wh_[0-9]{8}(?:_[a-z0-9]+)?$")
        self.events = []
        self.token = None
        outcome = "FAIL"
        try:
            self.assertEqual(self.sql("SELECT DATABASE();"), SCHEMA)
            self.assertEqual(self.sql("SELECT COUNT(*) FROM erp_warehouse;"), "0")
            self.assertEqual(self.sql("SELECT CHARACTER_MAXIMUM_LENGTH FROM information_schema.columns "
                                      "WHERE table_schema=DATABASE() AND table_name='erp_warehouse' AND column_name='name';"), "20")
            login = self.call("POST", "/system/auth/login", {
                "username": os.environ["YUHENG_PROBE_USERNAME"],
                "password": os.environ["YUHENG_PROBE_PASSWORD"]})
            self.token = login["accessToken"]
            for character in ("a", "仓"):
                warehouse_id = self.call("POST", "/erp/warehouse/create", {
                    "name": character * 20, "sort": 1, "status": 0})
                for method, path, extra in (
                    ("POST", "/erp/warehouse/create", {}),
                    ("PUT", "/erp/warehouse/update", {"id": warehouse_id}),
                ):
                    for kind, name in (("over-limit", character * 21), ("empty", ""),
                                       ("null", None), ("omitted", None)):
                        before = self.sql("SELECT id,name FROM erp_warehouse ORDER BY id;")
                        body = {"sort": 1, "status": 0, **extra}
                        if kind != "omitted":
                            body["name"] = name
                        expected_message = ("仓库名称长度不能超过 20 个字符"
                                            if kind == "over-limit" else "仓库名称不能为空")
                        self.call(method, path, body, code=400, message="请求参数不正确:" + expected_message)
                        self.assertEqual(self.sql("SELECT id,name FROM erp_warehouse ORDER BY id;"), before)
                self.call("PUT", "/erp/warehouse/update", {
                    "id": warehouse_id, "name": character * 19 + "X", "sort": 1, "status": 0})
                saved = self.call("GET", f"/erp/warehouse/get?id={warehouse_id}")
                self.assertEqual(saved["name"], character * 19 + "X")
            self.assertEqual(self.sql("SELECT COUNT(*) FROM erp_warehouse WHERE deleted=0;"), "2")
            self.assertEqual(self.sql("SELECT COUNT(*) FROM erp_warehouse WHERE tenant_id<>1;"), "0")
            outcome = "PASS"
        finally:
            if os.environ.get("YUHENG_WAREHOUSE_PROBE_EVIDENCE"):
                Path(os.environ["YUHENG_WAREHOUSE_PROBE_EVIDENCE"]).write_text(json.dumps({
                    "result": outcome, "schema": SCHEMA, "port": url.port,
                    "time": datetime.now().astimezone().isoformat(), "requests": self.events,
                    "scope": "ASCII/BMP 20 accepted; 21/empty/null/omitted rejected on create/update; rejected writes preserve rows",
                }, ensure_ascii=False, indent=2) + "\n")

    def sql(self, statement):
        result = subprocess.run([
            "docker", "exec", "-i", "mysql8", "sh", "-c",
            'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw --skip-column-names "$1"',
            "warehouse-probe", SCHEMA,
        ], input=statement, text=True, capture_output=True, check=True)
        return result.stdout.strip()

    def call(self, method, path, body=None, code=0, message=None):
        headers = {"tenant-id": "1", "Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        request = Request(BASE + "/admin-api" + path, method=method, headers=headers,
                          data=json.dumps(body).encode() if body is not None else None)
        try:
            response = urlopen(request, timeout=15)
        except HTTPError as error:
            response = error
        with response:
            status = response.status
            data = json.load(response)
        self.events.append({"method": method, "path": path, "http": status,
                            "code": data.get("code"), "msg": data.get("msg"),
                            "name_length": len(body["name"]) if body and isinstance(body.get("name"), str) else None})
        self.assertEqual(status, 200)
        self.assertEqual(data.get("code"), code, data.get("msg"))
        if message:
            self.assertEqual(data.get("msg"), message)
        return data.get("data")


if __name__ == "__main__":
    unittest.main()
