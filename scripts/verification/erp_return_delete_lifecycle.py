"""Exercise approved-return deletion protection and draft cleanup via real APIs."""
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def run_return_delete_lifecycle(base_url, username, password, resource, identifier,
                                expected_delete_code, sql, table, item_table, order_table,
                                order_id, stock_query, expected_stock):
    events = []
    token = None

    def call(method, path, body=None, expected=0):
        request = Request(base_url + "/admin-api" + path, method=method,
                          headers={"Content-Type": "application/json", "tenant-id": "1",
                                   **({"Authorization": "Bearer " + token} if token else {})},
                          data=None if body is None else json.dumps(body).encode())
        try:
            response = urlopen(request, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            result = json.load(response)
            event = {"method": method, "path": path, "http": response.status,
                     "code": result.get("code")}
        events.append(event)
        assert event["http"] == 200 and event["code"] == expected, event
        return result.get("data")

    token = call("POST", "/system/auth/login", {"username": username, "password": password})["accessToken"]
    before = {
        "header": sql(f"SELECT status,CASE WHEN deleted=b'1' THEN '1' ELSE '0' END,refund_price FROM {table} WHERE id={int(identifier)};"),
        "items": sql(f"SELECT id,CASE WHEN deleted=b'1' THEN '1' ELSE '0' END FROM {item_table} WHERE return_id={int(identifier)} ORDER BY id;"),
        "order": sql(f"SELECT return_count FROM {order_table} WHERE id={int(order_id)};"),
        "stock": sql(stock_query),
        "records": sql("SELECT COUNT(*) FROM erp_stock_record WHERE deleted=0;")}
    call("DELETE", f"/{resource}/delete?ids={int(identifier)}", expected=expected_delete_code)
    after_rejected_delete = {
        "header": sql(f"SELECT status,CASE WHEN deleted=b'1' THEN '1' ELSE '0' END,refund_price FROM {table} WHERE id={int(identifier)};"),
        "items": sql(f"SELECT id,CASE WHEN deleted=b'1' THEN '1' ELSE '0' END FROM {item_table} WHERE return_id={int(identifier)} ORDER BY id;"),
        "order": sql(f"SELECT return_count FROM {order_table} WHERE id={int(order_id)};"),
        "stock": sql(stock_query),
        "records": sql("SELECT COUNT(*) FROM erp_stock_record WHERE deleted=0;")}
    assert after_rejected_delete == before, (before, after_rejected_delete)

    call("PUT", f"/{resource}/update-status?id={int(identifier)}&status=10", {})
    call("DELETE", f"/{resource}/delete?ids={int(identifier)}")
    after_delete = {
        "header": sql(f"SELECT status,CASE WHEN deleted=b'1' THEN '1' ELSE '0' END,refund_price FROM {table} WHERE id={int(identifier)};"),
        "items": sql(f"SELECT id,CASE WHEN deleted=b'1' THEN '1' ELSE '0' END FROM {item_table} WHERE return_id={int(identifier)} ORDER BY id;"),
        "order": sql(f"SELECT return_count FROM {order_table} WHERE id={int(order_id)};"),
        "stock": sql(stock_query),
        "records": sql("SELECT COUNT(*) FROM erp_stock_record WHERE deleted=0;")}
    assert after_delete["header"].split("\t")[:2] == ["10", "1"], after_delete
    assert after_delete["items"] and all(row.endswith("\t1") for row in after_delete["items"].splitlines()), after_delete
    assert after_delete["order"] == "0.000000", after_delete
    assert after_delete["stock"] == expected_stock, after_delete
    assert int(after_delete["records"]) == int(before["records"]) + 1, after_delete
    return {"approved_delete_rejected_without_mutation": True,
            "reverse_approval_and_draft_delete_restored_source_and_stock": True,
            "before": before, "rejected_delete_after": after_rejected_delete,
            "after_delete": after_delete, "api_events": events}
