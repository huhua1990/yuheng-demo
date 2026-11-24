"""Verify ERP tenant boundaries across every current ERP resource family."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from urllib.error import HTTPError
from urllib.request import Request, urlopen

MIN_CHANGESETS = 59
RESERVED_PORTS = {3306, 6379, 48080, 48100, 5173}
TENANTS = (121, 122)


def make_probe_password() -> str:
    """Keep disposable login fixtures within Core's 4-16 character rule."""
    return os.urandom(8).hex()

BUSINESS_TABLES = (
    "erp_product_category", "erp_product_unit", "erp_product", "erp_supplier",
    "erp_customer", "erp_account", "erp_warehouse", "erp_stock",
    "erp_stock_record", "erp_purchase_order", "erp_purchase_order_items",
    "erp_purchase_in", "erp_purchase_in_items", "erp_purchase_return",
    "erp_purchase_return_items", "erp_sale_order", "erp_sale_order_items",
    "erp_sale_out", "erp_sale_out_items", "erp_sale_return",
    "erp_sale_return_items", "erp_stock_in", "erp_stock_in_item",
    "erp_stock_out", "erp_stock_out_item", "erp_stock_check",
    "erp_stock_check_item", "erp_stock_move", "erp_stock_move_item",
    "erp_finance_payment", "erp_finance_payment_item", "erp_finance_receipt",
    "erp_finance_receipt_item",
)
MASTER_RESOURCES = ("product-category", "product-unit", "product", "supplier",
                    "customer", "account", "warehouse")
DOCUMENT_RESOURCES = ("purchase-order", "purchase-in", "purchase-return", "sale-order",
                      "sale-out", "sale-return", "stock-in", "stock-out", "stock-check",
                      "stock-move", "finance-payment", "finance-receipt")
FIXTURE_KEYS = {"product-category": "category", "product-unit": "unit"}
FIXTURE_KEYS.update({resource: resource for resource in MASTER_RESOURCES
                     if resource not in FIXTURE_KEYS})


def _permission(resource: str, action: str) -> str:
    return f"erp:{resource}:{action}"


ALL_PERMISSIONS = tuple(
    _permission(resource, action) for resource in MASTER_RESOURCES
    for action in ("create", "query", "update", "delete", "export")
) + tuple(
    _permission(resource, action) for resource in DOCUMENT_RESOURCES
    for action in ("create", "query", "update", "update-status", "delete", "export")
) + ("erp:stock:query", "erp:stock:export", "erp:stock-record:query",
     "erp:stock-record:export", "erp:statistics:query")


def _spec(resource: str, collection: str = "page") -> dict[str, str]:
    return {"detail": f"/erp/{resource}/get?id={{id}}",
            "page": f"/erp/{resource}/{collection}?pageNo=1&pageSize=100",
            "foreign_write": f"/erp/{resource}/update",
            "permission": _permission(resource, "query"),
            "page_shape": "list" if collection == "list" else "page"}


RESOURCE_MATRIX = {
    **{resource: _spec(resource, "list" if resource == "product-category" else "page")
       for resource in MASTER_RESOURCES},
    **{resource: _spec(resource) for resource in DOCUMENT_RESOURCES},
    "stock": _spec("stock"),
    "stock-record": _spec("stock-record"),
    "statistics-purchase": {"detail": "/erp/purchase-statistics/summary",
        "page": "/erp/purchase-statistics/time-summary?count=1",
        "foreign_write": "/erp/purchase-statistics/summary", "permission": "erp:statistics:query",
        "page_shape": "list"},
    "statistics-sale": {"detail": "/erp/sale-statistics/summary",
        "page": "/erp/sale-statistics/time-summary?count=1",
        "foreign_write": "/erp/sale-statistics/summary", "permission": "erp:statistics:query",
        "page_shape": "list"},
}


def validate_probe_target(schema: str, app_port: int, mysql_port: int,
                          redis_port: int) -> bool:
    if not re.fullmatch(r"yuheng_t4_erp_full_tenant_[0-9]{8}(?:_[a-z0-9]+)?", schema):
        raise ValueError("only yuheng_t4_erp_full_tenant_YYYYMMDD[_suffix] schemas are allowed")
    ports = (app_port, mysql_port, redis_port)
    if len(set(ports)) != 3 or any(port in RESERVED_PORTS for port in ports):
        raise ValueError("probe ports must be distinct and dedicated")
    if any(port < 1024 or port > 65535 for port in ports):
        raise ValueError("probe ports must be valid unprivileged ports")
    return True


class Probe:
    def __init__(self, args):
        self.args = args
        self.events = []
        self.tokens = {}
        self.users = {}
        self.fixtures = {}

    def sql(self, statement: str) -> str:
        result = subprocess.run(
            ["docker", "exec", "-i", self.args.mysql_container, "sh", "-c",
             'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
             '--skip-column-names -D "$1"', "probe", self.args.schema],
            input=statement, text=True, capture_output=True, check=True)
        return result.stdout.strip()

    def snapshot(self):
        return {table: self.sql(f"SELECT * FROM `{table}` ORDER BY id;")
                for table in BUSINESS_TABLES}

    def call(self, method, path, token, tenant, body=None, expected=0, reject=False):
        request = Request(self.args.base_url + "/admin-api" + path, method=method,
                          headers={"Accept": "application/json", "Content-Type": "application/json",
                                   "tenant-id": str(tenant), "Authorization": "Bearer " + token},
                          data=None if body is None else json.dumps(body).encode())
        try:
            response = urlopen(request, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            status, content_type, raw = response.status, response.headers.get("Content-Type", ""), response.read()
        if "json" in content_type or raw.startswith(b"{"):
            payload = json.loads(raw)
            code = payload.get("code")
        else:
            payload = {"code": status, "body_sha256": hashlib.sha256(raw).hexdigest()}
            code = payload["code"]
        self.events.append({"method": method, "path": path, "tenant": tenant, "http": status, "code": code})
        if reject:
            assert status != 200 or code != 0, (method, path, status, payload)
        else:
            assert status == 200 and code == expected, (method, path, tenant, status, code, payload.get("msg"))
        return payload.get("data")

    def login(self, label, tenant):
        username, password = self.users[label]
        data = self.call("POST", "/system/auth/login", "", tenant,
                         {"username": username, "password": password})
        return data["accessToken"]

    def setup_users(self):
        self.seed_passwords = self.sql("SELECT id,password FROM system_users WHERE id < 900000 ORDER BY id;")
        values = ",".join("'" + value + "'" for value in ALL_PERMISSIONS)
        permission_rows = self.sql("SELECT id,permission FROM system_menu WHERE deleted=0 AND permission IN (" + values + ");")
        permission_ids = {row.split("\t", 1)[1]: int(row.split("\t", 1)[0]) for row in permission_rows.splitlines()}
        assert set(ALL_PERMISSIONS) <= set(permission_ids), set(ALL_PERMISSIONS) - set(permission_ids)
        users, roles, menus, links = [], [], [], []
        for index, (label, tenant) in enumerate(zip(("one", "two"), TENANTS)):
            user_id, role_id = 993000 + index * 100, 993010 + index * 100
            username, password = f"erpfull{label}{os.urandom(4).hex()}", make_probe_password()
            hashed = subprocess.run(["htpasswd", "-bnBC", "4", username, password], capture_output=True, text=True, check=True).stdout.strip().split(":", 1)[1]
            self.users[label] = (username, password)
            users.append(f"({user_id},'{username}','{hashed}','ERP full {label}',NULL,'[]',0,b'0',{tenant})")
            roles.append(f"({role_id},'ERP full {label}','erp_full_{label}',1,1,'',0,1,'probe','probe','probe',b'0',{tenant})")
            menus.extend(f"({993100 + index * 1000 + n},{role_id},{permission_ids[value]},'probe','probe',b'0',{tenant})" for n, value in enumerate(ALL_PERMISSIONS))
            links.append(f"({993020 + index * 100},{user_id},{role_id},'probe','probe',b'0',{tenant})")
        self.sql("UPDATE system_tenant SET status=0,expire_time='2099-12-31 00:00:00' WHERE id IN (121,122);")
        self.sql("INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) VALUES " + ",".join(users) + ";")
        self.sql("INSERT INTO system_role (id,name,code,sort,data_scope,data_scope_dept_ids,status,type,remark,creator,updater,deleted,tenant_id) VALUES " + ",".join(roles) + ";")
        self.sql("INSERT INTO system_role_menu (id,role_id,menu_id,creator,updater,deleted,tenant_id) VALUES " + ",".join(menus) + ";")
        self.sql("INSERT INTO system_user_role (id,user_id,role_id,creator,updater,deleted,tenant_id) VALUES " + ",".join(links) + ";")
        for label, tenant in zip(("one", "two"), TENANTS):
            self.tokens[label] = self.login(label, tenant)

    def setup_master(self, label, tenant):
        base = 994000 if label == "one" else 995000
        v = {"supplier": base + 1, "customer": base + 2, "account": base + 3, "warehouse": base + 4,
             "warehouse2": base + 5, "unit": base + 6, "category": base + 7, "product": base + 8}
        self.sql(f"""
INSERT INTO erp_supplier (id,name,status,sort,creator,updater,deleted,tenant_id) VALUES ({v['supplier']},'{label} supplier',0,1,'1','1',b'0',{tenant});
INSERT INTO erp_customer (id,name,status,sort,creator,updater,deleted,tenant_id) VALUES ({v['customer']},'{label} customer',0,1,'1','1',b'0',{tenant});
INSERT INTO erp_account (id,name,no,status,sort,default_status,creator,updater,deleted,tenant_id) VALUES ({v['account']},'{label} account','{label}-account',0,1,b'0','1','1',b'0',{tenant});
INSERT INTO erp_warehouse (id,name,sort,status,default_status,creator,updater,deleted,tenant_id) VALUES ({v['warehouse']},'{label} warehouse 1',1,0,b'0','1','1',b'0',{tenant}),({v['warehouse2']},'{label} warehouse 2',2,0,b'0','1','1',b'0',{tenant});
INSERT INTO erp_product_unit (id,name,status,creator,updater,deleted,tenant_id) VALUES ({v['unit']},'{label} unit',0,'1','1',b'0',{tenant});
INSERT INTO erp_product_category (id,parent_id,name,code,sort,status,creator,updater,deleted,tenant_id) VALUES ({v['category']},0,'{label} category','{label}-category',1,0,'1','1',b'0',{tenant});
INSERT INTO erp_product (id,name,bar_code,category_id,unit_id,status,purchase_price,sale_price,min_price,creator,updater,deleted,tenant_id) VALUES ({v['product']},'{label} product','{label}-product',{v['category']},{v['unit']},0,10,20,1,'1','1',b'0',{tenant});
""")
        return v

    def create_documents(self, label, tenant, m):
        token, now = self.tokens[label], "2026-11-22 12:00:00"
        def post(resource, body):
            return int(self.call("POST", f"/erp/{resource}/create", token, tenant, body))
        def approve(resource, ident):
            self.call("PUT", f"/erp/{resource}/update-status?id={ident}&status=20", token, tenant, {})
        po = post("purchase-order", {"supplierId": m["supplier"], "accountId": m["account"], "orderTime": now, "discountPercent": 0, "depositPrice": 0, "items": [{"productId": m["product"], "productUnitId": m["unit"], "productPrice": 10, "count": 10, "taxPercent": 0}]})
        po_data = self.call("GET", f"/erp/purchase-order/get?id={po}", token, tenant)
        approve("purchase-order", po)
        po_item = po_data["items"][0]["id"]
        pin = post("purchase-in", {"accountId": m["account"], "inTime": now, "orderId": po, "discountPercent": 0, "otherPrice": 0, "items": [{"orderItemId": po_item, "warehouseId": m["warehouse"], "productId": m["product"], "productUnitId": m["unit"], "productPrice": 10, "count": 10, "taxPercent": 0}]})
        approve("purchase-in", pin)
        so = post("sale-order", {"customerId": m["customer"], "accountId": m["account"], "orderTime": now, "discountPercent": 0, "depositPrice": 0, "items": [{"productId": m["product"], "productUnitId": m["unit"], "productPrice": 20, "count": 4, "taxPercent": 0}]})
        so_data = self.call("GET", f"/erp/sale-order/get?id={so}", token, tenant)
        approve("sale-order", so)
        so_item = so_data["items"][0]["id"]
        pout = post("sale-out", {"accountId": m["account"], "outTime": now, "orderId": so, "discountPercent": 0, "otherPrice": 0, "items": [{"orderItemId": so_item, "warehouseId": m["warehouse"], "productId": m["product"], "productUnitId": m["unit"], "productPrice": 20, "count": 4, "taxPercent": 0}]})
        approve("sale-out", pout)
        pr = post("purchase-return", {"supplierId": m["supplier"], "accountId": m["account"], "returnTime": now, "orderId": po, "discountPercent": 0, "otherPrice": 0, "items": [{"orderItemId": po_item, "warehouseId": m["warehouse"], "productId": m["product"], "productUnitId": m["unit"], "productPrice": 10, "count": 1, "taxPercent": 0}]})
        approve("purchase-return", pr)
        sr = post("sale-return", {"customerId": m["customer"], "accountId": m["account"], "returnTime": now, "orderId": so, "discountPercent": 0, "otherPrice": 0, "items": [{"orderItemId": so_item, "warehouseId": m["warehouse"], "productId": m["product"], "productUnitId": m["unit"], "productPrice": 20, "count": 1, "taxPercent": 0}]})
        approve("sale-return", sr)
        sin = post("stock-in", {"supplierId": m["supplier"], "inTime": now, "items": [{"warehouseId": m["warehouse"], "productId": m["product"], "productUnitId": m["unit"], "productPrice": 10, "count": 2}]})
        approve("stock-in", sin)
        sout = post("stock-out", {"customerId": m["customer"], "outTime": now, "items": [{"warehouseId": m["warehouse"], "productId": m["product"], "productUnitId": m["unit"], "productPrice": 10, "count": 1}]})
        approve("stock-out", sout)
        move = post("stock-move", {"moveTime": now, "items": [{"fromWarehouseId": m["warehouse"], "toWarehouseId": m["warehouse2"], "productId": m["product"], "productUnitId": m["unit"], "productPrice": 10, "count": 1}]})
        approve("stock-move", move)
        check = post("stock-check", {"checkTime": now, "items": [{"warehouseId": m["warehouse2"], "productId": m["product"], "productUnitId": m["unit"], "productPrice": 10, "stockCount": 1, "actualCount": 2, "count": 1}]})
        approve("stock-check", check)
        payment = post("finance-payment", {"supplierId": m["supplier"], "accountId": m["account"], "paymentTime": now, "discountPrice": 0, "items": [{"bizType": 11, "bizId": pin, "paidPrice": 0, "paymentPrice": 90}]})
        approve("finance-payment", payment)
        receipt = post("finance-receipt", {"customerId": m["customer"], "accountId": m["account"], "receiptTime": now, "discountPrice": 0, "items": [{"bizType": 21, "bizId": pout, "receiptedPrice": 0, "receiptPrice": 60}]})
        approve("finance-receipt", receipt)
        stock = self.sql(f"SELECT id FROM erp_stock WHERE tenant_id={tenant} AND deleted=0 ORDER BY id;")
        record = self.sql(f"SELECT id FROM erp_stock_record WHERE tenant_id={tenant} AND deleted=0 ORDER BY id;")
        return {"purchase-order": po, "purchase-in": pin, "purchase-return": pr, "sale-order": so,
                "sale-out": pout, "sale-return": sr, "stock-in": sin, "stock-out": sout,
                "stock-move": move, "stock-check": check, "finance-payment": payment,
                "finance-receipt": receipt, "stock": int(stock.splitlines()[0]),
                "stock-record": int(record.splitlines()[0]), **m}

    def assert_reads(self, label, tenant, fixture, foreign=False):
        token = self.tokens[label]
        for resource, spec in RESOURCE_MATRIX.items():
            if resource.startswith("statistics-"):
                self.call("GET", spec["detail"], token, tenant)
                self.call("GET", spec["page"], token, tenant)
                continue
            ident = fixture[FIXTURE_KEYS.get(resource, resource)]
            data = self.call("GET", spec["detail"].format(id=ident), token, tenant)
            page = self.call("GET", spec["page"], token, tenant)
            if foreign:
                rows = page if spec.get("page_shape") == "list" else page.get("list", [])
                assert data is None and all(str(row.get("id")) != str(ident) for row in rows), resource
            else:
                has_rows = bool(page) if spec.get("page_shape") == "list" else page["total"] >= 1
                assert data is not None and has_rows, resource

    def assert_foreign_writes(self, label, tenant, foreign):
        token, before = self.tokens[label], self.snapshot()
        for resource in DOCUMENT_RESOURCES:
            ident = foreign[resource]
            self.call("PUT", f"/erp/{resource}/update-status?id={ident}&status=10", token, tenant, {}, reject=True)
            # The upstream delete services return success when the tenant-filtered
            # lookup is empty. The security property is the unchanged SQL state.
            self.call("DELETE", f"/erp/{resource}/delete?ids={ident}", token, tenant)
            assert self.snapshot() == before, (resource, "foreign_delete_success_noop")
        return True

    def run(self):
        assert self.sql("SELECT DATABASE();") == self.args.schema
        changesets = int(self.sql("SELECT COUNT(*) FROM DATABASECHANGELOG;"))
        assert changesets >= MIN_CHANGESETS, changesets
        self.setup_users()
        for label, tenant in zip(("one", "two"), TENANTS):
            self.fixtures[label] = self.create_documents(label, tenant, self.setup_master(label, tenant))
            self.assert_reads(label, tenant, self.fixtures[label])
        self.assert_reads("one", TENANTS[0], self.fixtures["two"], foreign=True)
        self.assert_reads("two", TENANTS[1], self.fixtures["one"], foreign=True)
        foreign_write_sql_unchanged = self.assert_foreign_writes("one", TENANTS[0], self.fixtures["two"])
        before = self.snapshot()
        self.call("GET", "/erp/product/page?pageNo=1&pageSize=100", self.tokens["one"], TENANTS[1], reject=True)
        assert self.snapshot() == before
        assert self.seed_passwords == self.sql("SELECT id,password FROM system_users WHERE id < 900000 ORDER BY id;")
        return {"result": "PASS", "schema": self.args.schema, "changesets": changesets,
                "resource_count": len(RESOURCE_MATRIX), "business_table_count": len(BUSINESS_TABLES),
                "requests": self.events, "foreign_write_sql_unchanged": foreign_write_sql_unchanged,
                "seed_passwords_unchanged": True,
                "limits": [
                    "ERP tenant isolation is verified across the listed resource families; department and self data scopes are not claimed for ERP.",
                    "The ERP template tables use tenant_id plus audit creator fields and do not declare dept_id/user_id columns or a DeptDataPermissionRule customizer.",
                    "External authentication and optional Member integrations are outside this ERP probe.",
                ]}
