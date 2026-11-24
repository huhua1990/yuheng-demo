#!/usr/bin/env python3
"""Run the ERP desktop receipt workflow against disposable MySQL and Redis."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import time
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "yuheng_t4_finance_browser_20261123"
MYSQL = "yh-erp-finance-browser-mysql-20261123"
REDIS = "yh-erp-finance-browser-redis-20261123"
MYSQL_PORT, REDIS_PORT, APP_PORT, UI_PORT = 13432, 16487, 48274, 5233
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
UI_DIST = ROOT / "yuheng-demo-ui/dist"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/erp-finance-browser-20261123"
PLAYWRIGHT = Path.home() / ".npm/_npx/9833c18b2d85bc59/node_modules"


def run(*args, check=True, env=None, input_text=None):
    return subprocess.run(args, check=check, env=env, input=input_text, text=True,
                          capture_output=True)


def listening(port):
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def sql(statement):
    result = run("docker", "exec", "-i", MYSQL, "sh", "-c",
                 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
                 '--skip-column-names -D "$1"', "probe", SCHEMA, input_text=statement, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "isolated SQL command failed")
    return result.stdout.strip()


def stop(process):
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=35)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def assert_static_matches_jar():
    dist = ROOT / "yuheng-demo-ui/dist"
    with ZipFile(JAR) as archive:
        packaged = {
            name.removeprefix("BOOT-INF/classes/static/"): hashlib.sha256(archive.read(name)).digest()
            for name in archive.namelist()
            if name.startswith("BOOT-INF/classes/static/") and not name.endswith("/")
        }
    built = {
        path.relative_to(dist).as_posix(): hashlib.sha256(path.read_bytes()).digest()
        for path in dist.rglob("*") if path.is_file()
    }
    if packaged != built:
        missing = sorted(packaged.keys() - built.keys())
        extra = sorted(built.keys() - packaged.keys())
        changed = sorted(key for key in packaged.keys() & built.keys() if packaged[key] != built[key])
        raise RuntimeError(f"dist does not match tested JAR static resources: missing={missing[:5]}, extra={extra[:5]}, changed={changed[:5]}")
    return len(packaged)


def seed_fixtures():
    sql("""
INSERT INTO erp_customer (id,name,status,sort,creator,updater,deleted,tenant_id)
VALUES (993101,'P2 Sales Customer',0,1,'1','1',b'0',1);
INSERT INTO erp_account (id,name,no,status,sort,default_status,creator,updater,deleted,tenant_id)
VALUES (993102,'P2 Sales Account','P2-SALES',0,1,b'1','1','1',b'0',1);
INSERT INTO erp_warehouse (id,name,sort,status,default_status,creator,updater,deleted,tenant_id)
VALUES (993103,'P2 Sales Warehouse',1,0,b'1','1','1',b'0',1);
INSERT INTO erp_product_unit (id,name,status,creator,updater,deleted,tenant_id)
VALUES (993104,'P2 Sales Unit',0,'1','1',b'0',1);
INSERT INTO erp_product_category (id,parent_id,name,code,sort,status,creator,updater,deleted,tenant_id)
VALUES (993105,0,'P2 Sales Category','P2-SALES',1,0,'1','1',b'0',1);
INSERT INTO erp_product (id,name,bar_code,category_id,unit_id,status,purchase_price,sale_price,min_price,creator,updater,deleted,tenant_id)
VALUES (993106,'P2 Sales Product','P2-SALES',993105,993104,0,5,12,1,'1','1',b'0',1);
INSERT INTO erp_stock (id,product_id,warehouse_id,`count`,creator,updater,deleted,tenant_id)
VALUES (993107,993106,993103,8,'1','1',b'0',1);
INSERT INTO erp_stock_record (id,product_id,warehouse_id,`count`,total_count,biz_type,biz_id,biz_item_id,biz_no,creator,updater,deleted,tenant_id)
VALUES (993108,993106,993103,8,8,10,993107,993107,'P2-FINANCE-OPENING','1','1',b'0',1);
INSERT INTO erp_supplier (id,name,status,sort,creator,updater,deleted,tenant_id)
VALUES (993201,'P2 Purchase Supplier',0,1,'1','1',b'0',1);
INSERT INTO erp_purchase_order (id,no,status,supplier_id,account_id,order_time,total_count,total_price,total_product_price,total_tax_price,discount_percent,discount_price,deposit_price,remark,in_count,return_count,creator,updater,deleted,tenant_id)
VALUES (993202,'P2-FINANCE-PURCHASE-ORDER',20,993201,993102,NOW(),2,20,20,0,0,0,0,'',2,0,'1','1',b'0',1);
INSERT INTO erp_purchase_order_items (id,order_id,product_id,product_unit_id,product_price,`count`,total_price,tax_percent,tax_price,in_count,return_count,creator,updater,deleted,tenant_id)
VALUES (993203,993202,993106,993104,10,2,20,0,0,2,0,'1','1',b'0',1);
INSERT INTO erp_purchase_in (id,no,status,supplier_id,account_id,in_time,order_id,order_no,total_count,total_price,payment_price,total_product_price,total_tax_price,discount_percent,discount_price,other_price,creator,updater,deleted,tenant_id)
VALUES (993204,'P2-FINANCE-PURCHASE-IN',20,993201,993102,NOW(),993202,'P2-FINANCE-PURCHASE-ORDER',2,20,0,20,0,0,0,0,'1','1',b'0',1);
INSERT INTO erp_purchase_in_items (id,in_id,order_item_id,warehouse_id,product_id,product_unit_id,product_price,`count`,total_price,tax_percent,tax_price,creator,updater,deleted,tenant_id)
VALUES (993205,993204,993203,993103,993106,993104,10,2,20,0,0,'1','1',b'0',1);
INSERT INTO erp_sale_out (id,no,status,out_time,customer_id,account_id,sale_user_id,order_id,order_no,total_count,total_price,receipt_price,total_product_price,total_tax_price,discount_percent,discount_price,other_price,creator,updater,deleted,tenant_id)
VALUES (993109,'P2-FINANCE-SALE-OUT',20,NOW(),993101,993102,NULL,993111,'P2-FINANCE-ORDER',3,36,0,36,0,0,0,0,'1','1',b'0',1);
INSERT INTO erp_sale_out_items (id,out_id,order_item_id,product_id,warehouse_id,product_unit_id,product_price,count,total_price,tax_percent,tax_price,creator,updater,deleted,tenant_id)
VALUES (993110,993109,993111,993106,993103,993104,12,3,36,0,0,'1','1',b'0',1);
""")


def redact_logs(passwords):
    for name in ("backend.log", "ui.log"):
        path = OUT / name
        if not path.exists():
            continue
        text = path.read_text(errors="replace")
        for secret in passwords:
            if secret:
                text = text.replace(secret, "[REDACTED]")
        import re
        text = re.sub(r"(?i)(Bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[REDACTED]", text)
        path.write_text(text)


def main():
    assert JAR.is_file(), JAR
    assert (UI_DIST / "index.html").is_file(), UI_DIST
    assert (PLAYWRIGHT / "playwright").is_dir(), PLAYWRIGHT
    static_resource_count = assert_static_matches_jar()
    ports = (MYSQL_PORT, REDIS_PORT, APP_PORT, UI_PORT)
    assert not any(listening(port) for port in ports), "a dedicated verification port is occupied"
    names = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
    assert MYSQL not in names and REDIS not in names, "dedicated container name already exists"
    OUT.mkdir(parents=True, exist_ok=True)
    db_password, redis_password = secrets.token_hex(20), secrets.token_hex(20)
    username, password = "erpfin" + secrets.token_hex(4), secrets.token_urlsafe(12)[:16]
    password_hash = run("htpasswd", "-bnBC", "4", username, password).stdout.strip().split(":", 1)[1]
    containers, processes = [], []
    report = {"result": "FAIL", "schema": SCHEMA,
              "jar_sha256": hashlib.sha256(JAR.read_bytes()).hexdigest(),
              "jar_static_resource_count": static_resource_count,
              "jar_dist_byte_match": True,
              "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT,
                        "backend": APP_PORT, "ui": UI_PORT},
              "credentials_recorded": False, "viewport": "desktop-1440x900"}
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
            except (subprocess.CalledProcessError, RuntimeError):
                pass
            assert time.monotonic() < deadline, "isolated MySQL readiness timeout"
            time.sleep(1)
        env = dict(os.environ, YUHENG_DB_HOST="127.0.0.1", YUHENG_DB_PORT=str(MYSQL_PORT),
                   YUHENG_DB_NAME=SCHEMA, YUHENG_DB_USERNAME="root", YUHENG_DB_PASSWORD=db_password,
                   YUHENG_REDIS_PASSWORD=redis_password, YUHENG_PROBE_USERNAME=username,
                   YUHENG_PROBE_PASSWORD=password,
                   YUHENG_CHROME_EXECUTABLE="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        log = (OUT / "backend.log").open("w")
        app = subprocess.Popen(["java", "-jar", str(JAR), f"--server.port={APP_PORT}",
            "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
            f"--spring.data.redis.port={REDIS_PORT}", "--spring.data.redis.database=0",
            "--spring.data.redis.password=" + redis_password, "--yudao.security.mock-enable=false",
            "--spring.quartz.auto-startup=false", "--yudao.captcha.enable=false"],
            cwd=ROOT, env=env, stdout=log, stderr=log)
        processes.append(app)
        deadline = time.monotonic() + 180
        while not listening(APP_PORT):
            assert app.poll() is None and time.monotonic() < deadline, "isolated Demo failed to start"
            time.sleep(1)
        deadline = time.monotonic() + 90
        while True:
            try:
                if int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")) >= 59:
                    break
            except (subprocess.CalledProcessError, RuntimeError):
                pass
            assert time.monotonic() < deadline, "Liquibase readiness timeout"
            time.sleep(1)
        seed_passwords = sql("SELECT id,password FROM system_users WHERE id < 900000 ORDER BY id;")
        sql("INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) "
            f"VALUES (993120,'{username}','{password_hash}','ERP finance browser',NULL,'[]',0,b'0',1);")
        sql("INSERT INTO system_user_role (user_id,role_id,creator,updater,deleted,tenant_id) "
            "SELECT 993120,role_id,creator,updater,b'0',tenant_id FROM system_user_role "
            "WHERE user_id=1 AND deleted=0;")
        seed_fixtures()
        ui_env = dict(env, NODE_PATH=str(PLAYWRIGHT))
        ui_log = (OUT / "ui.log").open("w")
        ui = subprocess.Popen(["python3", "scripts/ui_server.py", "--root", str(UI_DIST),
            "--port", str(UI_PORT), "--backend", f"http://127.0.0.1:{APP_PORT}"],
            cwd=ROOT, env=ui_env, stdout=ui_log, stderr=ui_log)
        processes.append(ui)
        deadline = time.monotonic() + 20
        while not listening(UI_PORT):
            assert ui.poll() is None and time.monotonic() < deadline, "isolated UI failed to start"
            time.sleep(.25)
        browser_env = dict(ui_env, YH_ERP_UI_ORIGIN=f"http://127.0.0.1:{UI_PORT}",
                           YH_ERP_BROWSER_OUTPUT=str(OUT / "browser.json"))
        browser = run("node", "scripts/verification/erp_finance_browser_probe.js", check=False, env=browser_env)
        report["browser_stdout"] = browser.stdout[-3000:]
        report["browser_stderr"] = browser.stderr[-3000:]
        assert browser.returncode == 0, "desktop ERP finance browser probe failed"
        report["browser"] = json.loads((OUT / "browser.json").read_text())
        receipt_id = report["browser"]["receiptId"]
        payment_id = report["browser"]["paymentId"]
        report["sql"] = {
            "receipt": sql(f"SELECT CONCAT(status,':',total_price,':',discount_price,':',receipt_price,':',customer_id,':',tenant_id) FROM erp_finance_receipt WHERE id={int(receipt_id)} AND deleted=0;"),
            "receipt_item": sql(f"SELECT CONCAT(biz_type,':',biz_id,':',total_price,':',receipted_price,':',receipt_price,':',tenant_id) FROM erp_finance_receipt_item WHERE receipt_id={int(receipt_id)} AND deleted=0;"),
            "sale_out": sql("SELECT CONCAT(status,':',receipt_price,':',total_price,':',tenant_id) FROM erp_sale_out WHERE id=993109 AND deleted=0;"),
            "payment": sql(f"SELECT CONCAT(status,':',total_price,':',discount_price,':',payment_price,':',supplier_id,':',tenant_id) FROM erp_finance_payment WHERE id={int(payment_id)} AND deleted=0;"),
            "payment_item": sql(f"SELECT CONCAT(biz_type,':',biz_id,':',total_price,':',paid_price,':',payment_price,':',tenant_id) FROM erp_finance_payment_item WHERE payment_id={int(payment_id)} AND deleted=0;"),
            "purchase_in": sql("SELECT CONCAT(status,':',payment_price,':',total_price,':',tenant_id) FROM erp_purchase_in WHERE id=993204 AND deleted=0;"),
            "changesets": int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")),
            "seed_passwords_unchanged": seed_passwords == sql("SELECT id,password FROM system_users WHERE id < 900000 ORDER BY id;")}
        assert report["sql"]["receipt"].startswith("20:3.000000:0.000000:3.000000:993101:1"), report["sql"]
        assert report["sql"]["receipt_item"].startswith("21:993109:36.000000:0.000000:3.000000:1"), report["sql"]
        assert report["sql"]["sale_out"].startswith("20:3.000000:36.000000:1"), report["sql"]
        assert report["sql"]["payment"].startswith("20:4.000000:0.000000:4.000000:993201:1"), report["sql"]
        assert report["sql"]["payment_item"].startswith("11:993204:20.000000:0.000000:4.000000:1"), report["sql"]
        assert report["sql"]["purchase_in"].startswith("20:4.000000:20.000000:1"), report["sql"]
        assert report["sql"]["changesets"] == 59 and report["sql"]["seed_passwords_unchanged"], report["sql"]
        report["result"] = "PASS"
    except Exception as error:
        report["error"] = str(error)
        raise
    finally:
        for process in reversed(processes):
            stop(process)
        for name in reversed(containers):
            run("docker", "rm", "-fv", name, check=False)
        redact_logs((password, password_hash, db_password, redis_password))
        remaining = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
        report["cleanup"] = {"containers_absent": all(name not in remaining for name in (MYSQL, REDIS)),
                              "ports_listening": {str(port): listening(port) for port in ports}}
        report["cleanup"]["passed"] = report["cleanup"]["containers_absent"] and not any(report["cleanup"]["ports_listening"].values())
        (OUT / "runtime.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        assert report["cleanup"]["passed"], report["cleanup"]
    print(json.dumps({"result": report["result"], "jar_sha256": report["jar_sha256"],
                      "actions": report["browser"]["actions"], "sql": report["sql"],
                      "cleanup": report["cleanup"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
