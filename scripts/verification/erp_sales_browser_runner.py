#!/usr/bin/env python3
"""Run a desktop ERP sales workflow against disposable MySQL and Redis."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "yuheng_t4_erp_sales_browser_20261123"
MYSQL = "yh-erp-sales-browser-mysql-20261123"
REDIS = "yh-erp-sales-browser-redis-20261123"
MYSQL_PORT, REDIS_PORT, APP_PORT, UI_PORT = 13404, 16485, 48272, 5231
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
UI_DIST = ROOT / "yuheng-demo-ui/dist"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/erp-sales-browser-20261123"
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
                 '--skip-column-names -D "$1"', "probe", SCHEMA, input_text=statement)
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


def seed_fixtures():
    sql("""
INSERT INTO erp_customer (id,name,status,sort,creator,updater,deleted,tenant_id)
VALUES (993001,'P2 Sales Customer',0,1,'1','1',b'0',1);
INSERT INTO erp_account (id,name,no,status,sort,default_status,creator,updater,deleted,tenant_id)
VALUES (993002,'P2 Sales Account','P2-SALES',0,1,b'1','1','1',b'0',1);
INSERT INTO erp_warehouse (id,name,sort,status,default_status,creator,updater,deleted,tenant_id)
VALUES (993003,'P2 Sales Warehouse',1,0,b'1','1','1',b'0',1);
INSERT INTO erp_product_unit (id,name,status,creator,updater,deleted,tenant_id)
VALUES (993004,'P2 Sales Unit',0,'1','1',b'0',1);
INSERT INTO erp_product_category (id,parent_id,name,code,sort,status,creator,updater,deleted,tenant_id)
VALUES (993005,0,'P2 Sales Category','P2-SALES',1,0,'1','1',b'0',1);
INSERT INTO erp_product (id,name,bar_code,category_id,unit_id,status,purchase_price,sale_price,min_price,creator,updater,deleted,tenant_id)
VALUES (993006,'P2 Sales Product','P2-SALES',993005,993004,0,5,12,1,'1','1',b'0',1);
INSERT INTO erp_stock (id,product_id,warehouse_id,`count`,creator,updater,deleted,tenant_id)
VALUES (993007,993006,993003,8,'1','1',b'0',1);
INSERT INTO erp_stock_record (id,product_id,warehouse_id,`count`,total_count,biz_type,biz_id,biz_item_id,biz_no,creator,updater,deleted,tenant_id)
VALUES (993008,993006,993003,8,8,10,993007,993007,'P2-SALES-OPENING','1','1',b'0',1);
""")


def main():
    assert JAR.is_file(), JAR
    assert (UI_DIST / "index.html").is_file(), UI_DIST
    assert (PLAYWRIGHT / "playwright").is_dir(), PLAYWRIGHT
    jar_hash = hashlib.sha256(JAR.read_bytes()).hexdigest()
    ports = (MYSQL_PORT, REDIS_PORT, APP_PORT, UI_PORT)
    assert not any(listening(port) for port in ports), "a dedicated verification port is occupied"
    names = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
    assert MYSQL not in names and REDIS not in names, "dedicated container name already exists"
    OUT.mkdir(parents=True, exist_ok=True)
    db_password, redis_password = secrets.token_hex(20), secrets.token_hex(20)
    username, password = "erpsales" + secrets.token_hex(4), secrets.token_urlsafe(12)[:16]
    password_hash = run("htpasswd", "-bnBC", "4", username, password).stdout.strip().split(":", 1)[1]
    containers, processes = [], []
    report = {"result": "FAIL", "schema": SCHEMA, "jar_sha256": jar_hash,
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
            except subprocess.CalledProcessError:
                pass
            assert time.monotonic() < deadline, "isolated MySQL readiness timeout"
            time.sleep(1)
        env = dict(os.environ, YUHENG_DB_HOST="127.0.0.1", YUHENG_DB_PORT=str(MYSQL_PORT),
                   YUHENG_DB_NAME=SCHEMA, YUHENG_DB_USERNAME="root", YUHENG_DB_PASSWORD=db_password,
                   YUHENG_REDIS_PASSWORD=redis_password, YUHENG_PROBE_USERNAME=username,
                   YUHENG_PROBE_PASSWORD=password, YUHENG_CHROME_EXECUTABLE="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
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
            except subprocess.CalledProcessError:
                pass
            assert time.monotonic() < deadline, "Liquibase readiness timeout"
            time.sleep(1)
        seed_passwords = sql("SELECT id,password FROM system_users WHERE id < 900000 ORDER BY id;")
        sql("INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) "
            f"VALUES (993010,'{username}','{password_hash}','ERP sales browser',NULL,'[]',0,b'0',1);")
        sql("INSERT INTO system_user_role (user_id,role_id,creator,updater,deleted,tenant_id) "
            "SELECT 993010,role_id,creator,updater,b'0',tenant_id FROM system_user_role "
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
        browser = run("node", "scripts/verification/erp_sales_browser_probe.js", check=False, env=browser_env)
        report["browser_stdout"] = browser.stdout[-3000:]
        report["browser_stderr"] = browser.stderr[-3000:]
        assert browser.returncode == 0, "desktop ERP sales browser probe failed"
        report["browser"] = json.loads((OUT / "browser.json").read_text())
        order_id, out_id, return_id = (report["browser"]["orderId"],
                                       report["browser"]["outId"],
                                       report["browser"]["returnId"])
        report["sql"] = {
            "order": sql(f"SELECT CONCAT(status,':',total_count,':',customer_id,':',tenant_id) FROM erp_sale_order WHERE id={int(order_id)} AND deleted=0;"),
            "order_item": sql(f"SELECT CONCAT(count,':',product_id) FROM erp_sale_order_items WHERE order_id={int(order_id)} AND deleted=0;"),
            "outbound": sql(f"SELECT CONCAT(status,':',total_count,':',order_id,':',customer_id,':',tenant_id) FROM erp_sale_out WHERE id={int(out_id)} AND deleted=0;"),
            "return": sql(f"SELECT CONCAT(status,':',total_count,':',order_id,':',customer_id,':',tenant_id) FROM erp_sale_return WHERE id={int(return_id)} AND deleted=0;"),
            "stock": sql("SELECT `count` FROM erp_stock WHERE id=993007 AND deleted=0;"),
            "stock_records": sql("SELECT CONCAT(biz_type,':',`count`) FROM erp_stock_record WHERE product_id=993006 AND deleted=0 ORDER BY id;"),
            "changesets": int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")),
            "seed_passwords_unchanged": seed_passwords == sql("SELECT id,password FROM system_users WHERE id < 900000 ORDER BY id;"),
        }
        assert report["sql"]["order"].startswith("20:3.000000:993001:1"), report["sql"]
        assert report["sql"]["order_item"].startswith("3.000000:993006"), report["sql"]
        assert report["sql"]["outbound"].startswith(f"20:3.000000:{order_id}:993001:1"), report["sql"]
        assert report["sql"]["return"].startswith(f"20:3.000000:{order_id}:993001:1"), report["sql"]
        assert report["sql"]["stock"] == "8.000000", report["sql"]
        assert report["sql"]["stock_records"].endswith("60:3.000000"), report["sql"]
        assert report["sql"]["seed_passwords_unchanged"]
        report["result"] = "PASS"
    except Exception as error:
        report["error"] = str(error)
        raise
    finally:
        for process in reversed(processes):
            stop(process)
        for name in reversed(containers):
            run("docker", "rm", "-fv", name, check=False)
        remaining = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
        report["cleanup"] = {"containers_absent": all(name not in remaining for name in (MYSQL, REDIS)),
                              "ports_listening": {str(port): listening(port) for port in ports}}
        report["cleanup"]["passed"] = report["cleanup"]["containers_absent"] and not any(report["cleanup"]["ports_listening"].values())
        (OUT / "runtime.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        assert report["cleanup"]["passed"], report["cleanup"]
    print(json.dumps({"result": report["result"], "jar_sha256": jar_hash,
                      "actions": report["browser"]["actions"], "sql": report["sql"],
                      "cleanup": report["cleanup"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
