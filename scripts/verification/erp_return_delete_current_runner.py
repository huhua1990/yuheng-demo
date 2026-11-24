#!/usr/bin/env python3
"""Run current-JAR purchase and sales return delete lifecycle checks in isolation."""
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import time
from zipfile import ZipFile

import erp_finance_edit_runner as base
from erp_return_delete_lifecycle import run_return_delete_lifecycle

ROOT = base.ROOT
SCHEMA = "yuheng_t4_return_delete_20261123_current"
MYSQL, REDIS = "yh-erp-return-delete-mysql-20261123", "yh-erp-return-delete-redis-20261123"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13437, 16492, 48279
JAR_HASH = "4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1"
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
UI_DIST = ROOT / "yuheng-demo-ui/dist"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/erp-return-delete-current-20261123"
PLAYWRIGHT = Path.home() / ".npm/_npx/9833c18b2d85bc59/node_modules"
FLOWS = (
    ("purchase", "erp_purchase_browser_probe.js", 995010, "erppur"),
    ("sale", "erp_sales_browser_probe.js", 995011, "erpsal"),
)


def run(*args, check=True, env=None, input_text=None):
    return subprocess.run(args, check=check, env=env, input=input_text, text=True,
                          capture_output=True)


def sql(statement):
    result = run("docker", "exec", "-i", MYSQL, "sh", "-c",
                 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
                 '--skip-column-names -D "$1"', "probe", SCHEMA, input_text=statement,
                 check=False)
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
    assert packaged == built, "JAR and Demo dist static resources differ"
    return len(packaged)


def fixtures():
    sql("""
INSERT INTO erp_supplier (id,name,status,sort,creator,updater,deleted,tenant_id)
VALUES (995001,'P2 Purchase Supplier',0,1,'1','1',b'0',1);
INSERT INTO erp_account (id,name,no,status,sort,default_status,creator,updater,deleted,tenant_id)
VALUES (995002,'P2 Purchase Account','P2-RET',0,1,b'1','1','1',b'0',1);
INSERT INTO erp_warehouse (id,name,sort,status,default_status,creator,updater,deleted,tenant_id)
VALUES (995003,'P2 Purch Wh',1,0,b'1','1','1',b'0',1);
INSERT INTO erp_product_unit (id,name,status,creator,updater,deleted,tenant_id)
VALUES (995004,'P2 Return Unit',0,'1','1',b'0',1);
INSERT INTO erp_product_category (id,parent_id,name,code,sort,status,creator,updater,deleted,tenant_id)
VALUES (995005,0,'P2 Return Category','P2-RET',1,0,'1','1',b'0',1);
INSERT INTO erp_product (id,name,bar_code,category_id,unit_id,status,purchase_price,sale_price,min_price,creator,updater,deleted,tenant_id)
VALUES (995006,'P2 Purchase Product','P2-RET-P',995005,995004,0,5,12,1,'1','1',b'0',1);
INSERT INTO erp_stock (id,product_id,warehouse_id,`count`,creator,updater,deleted,tenant_id)
VALUES (995007,995006,995003,10,'1','1',b'0',1);
INSERT INTO erp_stock_record (id,product_id,warehouse_id,`count`,total_count,biz_type,biz_id,biz_item_id,biz_no,creator,updater,deleted,tenant_id)
VALUES (995008,995006,995003,10,10,10,995007,995007,'P2-RETURN-OPENING','1','1',b'0',1);
INSERT INTO erp_customer (id,name,status,sort,creator,updater,deleted,tenant_id)
VALUES (995009,'P2 Sales Customer',0,1,'1','1',b'0',1);
INSERT INTO erp_product_unit (id,name,status,creator,updater,deleted,tenant_id)
VALUES (995012,'P2 Sales Unit',0,'1','1',b'0',1);
INSERT INTO erp_product_category (id,parent_id,name,code,sort,status,creator,updater,deleted,tenant_id)
VALUES (995013,0,'P2 Sales Category','P2-SAL',2,0,'1','1',b'0',1);
INSERT INTO erp_product (id,name,bar_code,category_id,unit_id,status,purchase_price,sale_price,min_price,creator,updater,deleted,tenant_id)
VALUES (995014,'P2 Sales Product','P2-RET-S',995013,995012,0,5,12,1,'1','1',b'0',1);
INSERT INTO erp_stock (id,product_id,warehouse_id,`count`,creator,updater,deleted,tenant_id)
VALUES (995015,995014,995003,10,'1','1',b'0',1);
INSERT INTO erp_stock_record (id,product_id,warehouse_id,`count`,total_count,biz_type,biz_id,biz_item_id,biz_no,creator,updater,deleted,tenant_id)
VALUES (995016,995014,995003,10,10,10,995015,995015,'P2-SALE-RETURN-OPENING','1','1',b'0',1);
INSERT INTO erp_warehouse (id,name,sort,status,default_status,creator,updater,deleted,tenant_id)
VALUES (995017,'P2 Sales Warehouse',2,0,b'0','1','1',b'0',1);
INSERT INTO erp_stock (id,product_id,warehouse_id,`count`,creator,updater,deleted,tenant_id)
VALUES (995018,995014,995017,10,'1','1',b'0',1);
INSERT INTO erp_stock_record (id,product_id,warehouse_id,`count`,total_count,biz_type,biz_id,biz_item_id,biz_no,creator,updater,deleted,tenant_id)
VALUES (995019,995014,995017,10,10,10,995018,995018,'P2-SALE-RETURN-OPENING-B','1','1',b'0',1);
""")


def main():
    assert hashlib.sha256(JAR.read_bytes()).hexdigest() == JAR_HASH
    assert (UI_DIST / "index.html").is_file() and (PLAYWRIGHT / "playwright").is_dir()
    static_count = static_match_count()
    ports = (MYSQL_PORT, REDIS_PORT, APP_PORT)
    assert not any(base.listening(port) for port in ports)
    names = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
    assert MYSQL not in names and REDIS not in names
    OUT.mkdir(parents=True, exist_ok=True)
    db_password, redis_password = secrets.token_hex(20), secrets.token_hex(20)
    credentials = {}
    for kind, _, _, prefix in FLOWS:
        username = prefix + secrets.token_hex(4)
        password = secrets.token_urlsafe(12)[:16]
        password_hash = run("htpasswd", "-bnBC", "4", username, password).stdout.strip().split(":", 1)[1]
        credentials[kind] = (username, password, password_hash)
    containers, processes = [], []
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
            except (subprocess.CalledProcessError, RuntimeError):
                pass
            assert time.monotonic() < deadline
            time.sleep(1)
        seed_passwords = None
        env = dict(os.environ, YUHENG_DB_HOST="127.0.0.1", YUHENG_DB_PORT=str(MYSQL_PORT),
                   YUHENG_DB_NAME=SCHEMA, YUHENG_DB_USERNAME="root", YUHENG_DB_PASSWORD=db_password,
                   YUHENG_REDIS_PASSWORD=redis_password,
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
        while not base.listening(APP_PORT):
            assert app.poll() is None and time.monotonic() < deadline
            time.sleep(1)
        deadline = time.monotonic() + 90
        while True:
            try:
                if int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")) >= 59:
                    break
            except (subprocess.CalledProcessError, RuntimeError):
                pass
            assert time.monotonic() < deadline
            time.sleep(1)
        seed_passwords = sql("SELECT id,password FROM system_users WHERE id<900000 ORDER BY id;")
        fixtures()
        flow_results = {}
        for kind, probe, user_id, _ in FLOWS:
            username, password, password_hash = credentials[kind]
            sql("INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) "
                f"VALUES ({user_id},'{username}','{password_hash}','ERP return {kind}',NULL,'[]',0,b'0',1);")
            sql("INSERT INTO system_user_role (user_id,role_id,creator,updater,deleted,tenant_id) "
                f"SELECT {user_id},role_id,creator,updater,b'0',tenant_id FROM system_user_role WHERE user_id=1 AND deleted=0;")
            flow_env = dict(env, YUHENG_PROBE_USERNAME=username, YUHENG_PROBE_PASSWORD=password,
                            YH_ERP_UI_ORIGIN=f"http://127.0.0.1:{APP_PORT}",
                            YH_ERP_BROWSER_OUTPUT=str(OUT / f"{kind}-browser.json"), NODE_PATH=str(PLAYWRIGHT))
            browser = run("node", f"scripts/verification/{probe}", check=False, env=flow_env)
            flow_report = {"stdout": browser.stdout[-3000:], "stderr": browser.stderr[-3000:]}
            assert browser.returncode == 0, f"{kind} desktop flow failed"
            flow_report["browser"] = json.loads((OUT / f"{kind}-browser.json").read_text())
            flow_results[kind] = flow_report
        report["browser_flows"] = flow_results
        p = flow_results["purchase"]["browser"]
        s = flow_results["sale"]["browser"]
        purchase_delete = run_return_delete_lifecycle(
            f"http://127.0.0.1:{APP_PORT}", credentials["purchase"][0], credentials["purchase"][1],
            "erp/purchase-return", p["returnId"], 1030103001, sql, "erp_purchase_return",
            "erp_purchase_return_items", "erp_purchase_order", p["orderId"],
            "SELECT `count` FROM erp_stock WHERE product_id=995006 AND deleted=0;", "20.000000")
        sale_delete = run_return_delete_lifecycle(
            f"http://127.0.0.1:{APP_PORT}", credentials["sale"][0], credentials["sale"][1],
            "erp/sale-return", s["returnId"], 1020203001, sql, "erp_sale_return",
            "erp_sale_return_items", "erp_sale_order", s["orderId"],
            "SELECT `count` FROM erp_stock WHERE product_id=995014 AND warehouse_id=995017 AND deleted=0;", "7.000000")
        report["return_lifecycle"] = {"purchase": purchase_delete, "sale": sale_delete}
        report["sql"] = {
            "purchase_return": sql(f"SELECT status,CASE WHEN deleted=b'1' THEN '1' ELSE '0' END,order_id,total_count FROM erp_purchase_return WHERE id={int(p['returnId'])};"),
            "sale_return": sql(f"SELECT status,CASE WHEN deleted=b'1' THEN '1' ELSE '0' END,order_id,total_count FROM erp_sale_return WHERE id={int(s['returnId'])};"),
            "purchase_order_return_count": sql(f"SELECT return_count FROM erp_purchase_order WHERE id={int(p['orderId'])};"),
            "sale_order_return_count": sql(f"SELECT return_count FROM erp_sale_order WHERE id={int(s['orderId'])};"),
            "purchase_stock": sql("SELECT `count` FROM erp_stock WHERE product_id=995006 AND deleted=0;"),
            "sale_stock": sql("SELECT `count` FROM erp_stock WHERE product_id=995014 AND warehouse_id=995017 AND deleted=0;"),
            "changesets": int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")),
            "seed_passwords_unchanged": seed_passwords == sql("SELECT id,password FROM system_users WHERE id<900000 ORDER BY id;")}
        assert report["sql"]["purchase_order_return_count"] == "0.000000"
        assert report["sql"]["sale_order_return_count"] == "0.000000"
        assert report["sql"]["purchase_stock"] == "20.000000" and report["sql"]["sale_stock"] == "7.000000"
        assert report["sql"]["changesets"] == 59 and report["sql"]["seed_passwords_unchanged"]
        report["result"] = "PASS"
    except Exception as error:
        report["error"] = str(error)
        raise
    finally:
        for process in reversed(processes):
            base.stop(process)
        for name in reversed(containers):
            run("docker", "rm", "-fv", name, check=False)
        if (OUT / "backend.log").exists():
            text = (OUT / "backend.log").read_text(errors="replace")
            for secret in [password, password_hash, db_password, redis_password] + [v for trio in credentials.values() for v in trio]:
                if secret:
                    text = text.replace(secret, "[REDACTED]")
            text = re.sub(r"(?i)(Bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[REDACTED]", text)
            (OUT / "backend.log").write_text(text)
            (OUT / "backend.log").unlink()
        names = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
        report["cleanup"] = {"containers_absent": all(name not in names for name in (MYSQL, REDIS)),
                              "ports_listening": {str(port): base.listening(port) for port in ports}}
        report["cleanup"]["passed"] = report["cleanup"]["containers_absent"] and not any(
            report["cleanup"]["ports_listening"].values())
        (OUT / "runtime.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        assert report["cleanup"]["passed"], report["cleanup"]
    print(json.dumps({"result": report["result"], "jar_sha256": JAR_HASH,
                      "sql": report["sql"], "cleanup": report["cleanup"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
