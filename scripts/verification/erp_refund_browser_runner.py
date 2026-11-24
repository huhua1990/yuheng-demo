#!/usr/bin/env python3
"""Run purchase and sales return-refund desktop flows in an isolated runtime."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
from zipfile import ZipFile

import erp_finance_browser_runner as base

ROOT = base.ROOT
SCHEMA = "yuheng_t4_refund_browser_20261123"
MYSQL, REDIS = "yh-erp-refund-browser-mysql-20261123", "yh-erp-refund-browser-redis-20261123"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13448, 16528, 48328
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
UI_DIST = ROOT / "yuheng-demo-ui/dist"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/erp-refund-browser-20261123"
PLAYWRIGHT = Path.home() / ".npm/_npx/9833c18b2d85bc59/node_modules"
JAR_HASH = "4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1"
FLOWS = (("purchase", "erp_purchase_browser_probe.js", 996120),
         ("sale", "erp_sales_browser_probe.js", 996121))


def run(*args, check=True, env=None, input_text=None):
    return subprocess.run(args, check=check, env=env, input=input_text, text=True,
                          capture_output=True)


def sql(statement):
    result = run("docker", "exec", "-i", MYSQL, "sh", "-c",
                 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
                 '--skip-column-names -D "$1"', "probe", SCHEMA,
                 input_text=statement, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "isolated SQL failed")
    return result.stdout.strip()


def static_match_count():
    with ZipFile(JAR) as archive:
        packaged = {name.removeprefix("BOOT-INF/classes/static/"): hashlib.sha256(archive.read(name)).digest()
                    for name in archive.namelist()
                    if name.startswith("BOOT-INF/classes/static/") and not name.endswith("/")}
    built = {path.relative_to(UI_DIST).as_posix(): hashlib.sha256(path.read_bytes()).digest()
             for path in UI_DIST.rglob("*") if path.is_file()}
    assert packaged == built, "JAR and Demo UI dist assets differ"
    return len(packaged)


def stop(process):
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=35)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def seed_fixtures():
    sql("""
INSERT INTO erp_supplier (id,name,status,sort,creator,updater,deleted,tenant_id)
VALUES (996001,'P2 Purchase Supplier',0,1,'1','1',b'0',1);
INSERT INTO erp_customer (id,name,status,sort,creator,updater,deleted,tenant_id)
VALUES (996002,'P2 Sales Customer',0,1,'1','1',b'0',1);
INSERT INTO erp_account (id,name,no,status,sort,default_status,creator,updater,deleted,tenant_id)
VALUES (996003,'P2 Refund Account','P2-REFUND',0,1,b'1','1','1',b'0',1);
INSERT INTO erp_warehouse (id,name,sort,status,default_status,creator,updater,deleted,tenant_id)
VALUES (996004,'P2 Purch Wh',1,0,b'1','1','1',b'0',1);
INSERT INTO erp_warehouse (id,name,sort,status,default_status,creator,updater,deleted,tenant_id)
VALUES (996005,'P2 Sales Warehouse',2,0,b'0','1','1',b'0',1);
INSERT INTO erp_product_unit (id,name,status,creator,updater,deleted,tenant_id)
VALUES (996006,'P2 Purchase Unit',0,'1','1',b'0',1),(996007,'P2 Sales Unit',0,'1','1',b'0',1);
INSERT INTO erp_product_category (id,parent_id,name,code,sort,status,creator,updater,deleted,tenant_id)
VALUES (996008,0,'P2 Purchase Category','P2-PUR',1,0,'1','1',b'0',1),
       (996009,0,'P2 Sales Category','P2-SAL',2,0,'1','1',b'0',1);
INSERT INTO erp_product (id,name,bar_code,category_id,unit_id,status,purchase_price,sale_price,min_price,creator,updater,deleted,tenant_id)
VALUES (996010,'P2 Purchase Product','P2-PUR',996008,996006,0,10,20,1,'1','1',b'0',1),
       (996011,'P2 Sales Product','P2-SAL',996009,996007,0,5,12,1,'1','1',b'0',1);
INSERT INTO erp_stock (id,product_id,warehouse_id,`count`,creator,updater,deleted,tenant_id)
VALUES (996012,996010,996004,0,'1','1',b'0',1),(996013,996011,996005,8,'1','1',b'0',1);
INSERT INTO erp_stock_record (id,product_id,warehouse_id,`count`,total_count,biz_type,biz_id,biz_item_id,biz_no,creator,updater,deleted,tenant_id)
VALUES (996014,996010,996004,0,0,10,996012,996012,'P2-PURCHASE-OPENING','1','1',b'0',1),
       (996015,996011,996005,8,8,10,996013,996013,'P2-SALE-OPENING','1','1',b'0',1);
""")


def main():
    assert hashlib.sha256(JAR.read_bytes()).hexdigest() == JAR_HASH
    assert (UI_DIST / "index.html").is_file() and (PLAYWRIGHT / "playwright").is_dir()
    static_count = static_match_count()
    ports = (MYSQL_PORT, REDIS_PORT, APP_PORT)
    assert not any(base.listening(port) for port in ports), "dedicated port occupied"
    names = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
    assert MYSQL not in names and REDIS not in names, "dedicated container name exists"
    OUT.mkdir(parents=True, exist_ok=True)
    db_password, redis_password = secrets.token_hex(20), secrets.token_hex(20)
    credentials = {}
    for kind, _, _ in FLOWS:
        username = "rfd" + secrets.token_hex(5)
        password = secrets.token_urlsafe(12)[:16]
        password_hash = run("htpasswd", "-bnBC", "4", username, password).stdout.strip().split(":", 1)[1]
        credentials[kind] = (username, password, password_hash)
    app = ui = None
    containers = []
    report = {"result": "FAIL", "schema": SCHEMA, "jar_sha256": JAR_HASH,
              "jar_static_resource_count": static_count, "jar_dist_byte_match": True,
              "viewport": "desktop-1440x900", "credentials_recorded": False,
              "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT, "app": APP_PORT}}
    try:
        run("docker", "run", "-d", "--name", MYSQL, "-e", "MYSQL_ROOT_PASSWORD=" + db_password,
            "-e", "MYSQL_DATABASE=" + SCHEMA, "-p", f"127.0.0.1:{MYSQL_PORT}:3306", "mysql:8.0.33")
        containers.append(MYSQL)
        run("docker", "run", "-d", "--name", REDIS, "-p", f"127.0.0.1:{REDIS_PORT}:6379",
            "redis:7.2.17", "redis-server", "--requirepass", redis_password)
        containers.append(REDIS)
        deadline = time.monotonic() + 120
        while True:
            try:
                if sql("SELECT DATABASE();") == SCHEMA:
                    break
            except RuntimeError:
                pass
            assert time.monotonic() < deadline, "isolated MySQL readiness timeout"
            time.sleep(1)

        env = dict(os.environ, YUHENG_DB_HOST="127.0.0.1", YUHENG_DB_PORT=str(MYSQL_PORT),
                   YUHENG_DB_NAME=SCHEMA, YUHENG_DB_USERNAME="root", YUHENG_DB_PASSWORD=db_password,
                   YUHENG_REDIS_PASSWORD=redis_password,
                   YUHENG_CHROME_EXECUTABLE="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        with (OUT / "backend.log").open("w") as backend_log:
            app = subprocess.Popen(["java", "-jar", str(JAR), f"--server.port={APP_PORT}",
                "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
                f"--spring.data.redis.port={REDIS_PORT}", "--spring.data.redis.database=0",
                "--spring.data.redis.password=" + redis_password, "--yudao.security.mock-enable=false",
                "--spring.quartz.auto-startup=false", "--yudao.captcha.enable=false"],
                cwd=ROOT, env=env, stdout=backend_log, stderr=backend_log)
            deadline = time.monotonic() + 180
            while not base.listening(APP_PORT):
                assert app.poll() is None and time.monotonic() < deadline, "Demo JAR failed to start"
                time.sleep(1)
            deadline = time.monotonic() + 90
            while True:
                try:
                    changesets = int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;"))
                    if changesets >= 59:
                        break
                except RuntimeError:
                    pass
                assert time.monotonic() < deadline, "Liquibase readiness timeout"
                time.sleep(1)

            seed_passwords = sql("SELECT id,password FROM system_users WHERE id<900000 ORDER BY id;")
            seed_fixtures()
            flow_results = {}
            for kind, probe_name, user_id in FLOWS:
                username, password, password_hash = credentials[kind]
                sql("INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) "
                    f"VALUES ({user_id},'{username}','{password_hash}','ERP refund {kind}',NULL,'[]',0,b'0',1);")
                sql("INSERT INTO system_user_role (user_id,role_id,creator,updater,deleted,tenant_id) "
                    f"SELECT {user_id},role_id,creator,updater,b'0',tenant_id FROM system_user_role "
                    "WHERE user_id=1 AND deleted=0;")
                flow_env = dict(env, YUHENG_PROBE_USERNAME=username, YUHENG_PROBE_PASSWORD=password,
                    YH_ERP_UI_ORIGIN=f"http://127.0.0.1:{APP_PORT}",
                    YH_ERP_BROWSER_OUTPUT=str(OUT / f"{kind}-browser.json"), NODE_PATH=str(PLAYWRIGHT))
                browser = run("node", f"scripts/verification/{probe_name}", check=False, env=flow_env)
                assert browser.returncode == 0, f"{kind} return browser flow failed: {browser.stderr[-2000:]}"
                flow_results[kind] = json.loads((OUT / f"{kind}-browser.json").read_text())
            report["return_flows"] = flow_results

            for kind, table, identifier in (("sale", "erp_sale_return", flow_results["sale"]["returnId"]),
                                            ("purchase", "erp_purchase_return", flow_results["purchase"]["returnId"])):
                row = sql(f"SELECT status,total_price,refund_price,tenant_id FROM {table} WHERE id={int(identifier)};")
                assert row.startswith("20\t"), (kind, row)
                flow_results[kind]["returnBeforeRefund"] = row.split("\t")
                flow_results[kind]["returnTotal"] = row.split("\t")[1]

            ui_env = dict(env, NODE_PATH=str(PLAYWRIGHT))
            with (OUT / "ui.log").open("w") as ui_log:
                ui = subprocess.Popen(["python3", "-c",
                    "import http.server,runpy; http.server.ThreadingHTTPServer.request_queue_size=128; "
                    "runpy.run_path('scripts/ui_server.py',run_name='__main__')", "--root", str(UI_DIST),
                    "--port", "5234", "--backend", f"http://127.0.0.1:{APP_PORT}"],
                    cwd=ROOT, env=ui_env, stdout=ui_log, stderr=ui_log)
                deadline = time.monotonic() + 20
                while not base.listening(5234):
                    assert ui.poll() is None and time.monotonic() < deadline, "isolated UI failed to start"
                    time.sleep(.25)
                browser_env = dict(ui_env, YH_ERP_UI_ORIGIN="http://127.0.0.1:5234",
                    YH_ERP_BROWSER_OUTPUT=str(OUT / "refund-browser.json"),
                    YUHENG_PROBE_USERNAME=credentials["sale"][0], YUHENG_PROBE_PASSWORD=credentials["sale"][1])
                browser = run("node", "scripts/verification/erp_refund_browser_probe.js", check=False, env=browser_env)
                assert browser.returncode == 0, f"refund desktop browser probe failed: {browser.stderr[-2500:]}"
            report["browser"] = json.loads((OUT / "refund-browser.json").read_text())
            receipt_id, payment_id = int(report["browser"]["receiptId"]), int(report["browser"]["paymentId"])
            sale_return_id = int(flow_results["sale"]["returnId"])
            purchase_return_id = int(flow_results["purchase"]["returnId"])
            report["sql"] = {
                "changesets": int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")),
                "sale_return": sql(f"SELECT CONCAT(status,':',total_price,':',refund_price,':',tenant_id) FROM erp_sale_return WHERE id={sale_return_id} AND deleted=0;"),
                "sale_refund": sql(f"SELECT CONCAT(status,':',total_price,':',receipt_price,':',tenant_id) FROM erp_finance_receipt WHERE id={receipt_id} AND deleted=0;"),
                "sale_refund_item": sql(f"SELECT CONCAT(biz_type,':',biz_id,':',total_price,':',receipt_price,':',tenant_id) FROM erp_finance_receipt_item WHERE receipt_id={receipt_id} AND deleted=0;"),
                "purchase_return": sql(f"SELECT CONCAT(status,':',total_price,':',refund_price,':',tenant_id) FROM erp_purchase_return WHERE id={purchase_return_id} AND deleted=0;"),
                "purchase_refund": sql(f"SELECT CONCAT(status,':',total_price,':',payment_price,':',tenant_id) FROM erp_finance_payment WHERE id={payment_id} AND deleted=0;"),
                "purchase_refund_item": sql(f"SELECT CONCAT(biz_type,':',biz_id,':',total_price,':',payment_price,':',tenant_id) FROM erp_finance_payment_item WHERE payment_id={payment_id} AND deleted=0;"),
                "seed_passwords_unchanged": seed_passwords == sql("SELECT id,password FROM system_users WHERE id<900000 ORDER BY id;")}
            assert report["sql"]["changesets"] == 59
            sale_price = float(flow_results["sale"]["returnTotal"])
            sale_refund = abs(float(report["browser"]["saleRefundInput"]))
            purchase_price = float(flow_results["purchase"]["returnTotal"])
            purchase_refund = abs(float(report["browser"]["purchaseRefundInput"]))
            assert report["sql"]["sale_return"].startswith(
                f"20:{sale_price:.6f}:{sale_refund:.6f}:1"), report["sql"]
            assert report["sql"]["sale_refund"].startswith(
                f"20:{-sale_refund:.6f}:{-sale_refund:.6f}:1"), report["sql"]
            assert report["sql"]["sale_refund_item"].startswith(
                f"22:{sale_return_id}:{-sale_price:.6f}:{-sale_refund:.6f}:1"), report["sql"]
            assert report["sql"]["purchase_return"].startswith(
                f"20:{purchase_price:.6f}:{purchase_refund:.6f}:1"), report["sql"]
            assert report["sql"]["purchase_refund"].startswith(
                f"20:{-purchase_refund:.6f}:{-purchase_refund:.6f}:1"), report["sql"]
            assert report["sql"]["purchase_refund_item"].startswith(
                f"12:{purchase_return_id}:{-purchase_price:.6f}:{-purchase_refund:.6f}:1"), report["sql"]
            assert report["sql"]["seed_passwords_unchanged"]
            report["result"] = "PASS"
    except Exception as error:
        report["error"] = str(error)
        raise
    finally:
        stop(ui)
        stop(app)
        for name in reversed(containers):
            run("docker", "rm", "-fv", name, check=False)
        names = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
        report["cleanup"] = {"containers_absent": all(name not in names for name in (MYSQL, REDIS)),
            "ports_listening": {str(port): base.listening(port) for port in (*ports, 5234)}}
        report["cleanup"]["passed"] = report["cleanup"]["containers_absent"] and not any(
            report["cleanup"]["ports_listening"].values())
        for log_name in ("backend.log", "ui.log"):
            log_path = OUT / log_name
            if log_path.exists():
                log_path.unlink()
        report["sensitive_logs_removed"] = not any((OUT / name).exists()
                                                   for name in ("backend.log", "ui.log"))
        report["cleanup"]["passed"] = report["cleanup"]["passed"] and report["sensitive_logs_removed"]
        (OUT / "runtime.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        assert report["cleanup"]["passed"], report["cleanup"]
    print(json.dumps({"result": report["result"], "jar_sha256": JAR_HASH,
        "sql": report["sql"], "cleanup": report["cleanup"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
