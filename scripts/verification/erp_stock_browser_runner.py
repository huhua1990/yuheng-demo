#!/usr/bin/env python3
"""Run desktop stock-check and stock-move flows against disposable services."""
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import time
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "yuheng_t4_erp_stock_browser_20261123"
MYSQL = "yh-erp-stock-browser-mysql-20261123"
REDIS = "yh-erp-stock-browser-redis-20261123"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13434, 16489, 48276
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
UI_DIST = ROOT / "yuheng-demo-ui/dist"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/erp-stock-browser-20261123"
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
                 '--skip-column-names -D "$1"', "probe", SCHEMA,
                 input_text=statement, check=False)
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
    with ZipFile(JAR) as archive:
        packaged = {name.removeprefix("BOOT-INF/classes/static/"): hashlib.sha256(archive.read(name)).digest()
                    for name in archive.namelist()
                    if name.startswith("BOOT-INF/classes/static/") and not name.endswith("/")}
    built = {path.relative_to(UI_DIST).as_posix(): hashlib.sha256(path.read_bytes()).digest()
             for path in UI_DIST.rglob("*") if path.is_file()}
    if packaged != built:
        missing, extra = sorted(packaged.keys() - built.keys()), sorted(built.keys() - packaged.keys())
        changed = sorted(key for key in packaged.keys() & built.keys() if packaged[key] != built[key])
        raise RuntimeError(f"dist/JAR static resources differ: missing={missing[:5]}, extra={extra[:5]}, changed={changed[:5]}")
    return len(packaged)


def seed_fixtures():
    sql("""
INSERT INTO erp_account (id,name,no,status,sort,default_status,creator,updater,deleted,tenant_id)
VALUES (994001,'P2 Stock Account','P2-STOCK',0,1,b'1','1','1',b'0',1);
INSERT INTO erp_warehouse (id,name,sort,status,default_status,creator,updater,deleted,tenant_id)
VALUES (994002,'P2 Stock Warehouse A',1,0,b'1','1','1',b'0',1),
       (994003,'P2 Stock Warehouse B',2,0,b'0','1','1',b'0',1);
INSERT INTO erp_product_unit (id,name,status,creator,updater,deleted,tenant_id)
VALUES (994004,'P2 Stock Unit',0,'1','1',b'0',1);
INSERT INTO erp_product_category (id,parent_id,name,code,sort,status,creator,updater,deleted,tenant_id)
VALUES (994005,0,'P2 Stock Category','P2-STOCK',1,0,'1','1',b'0',1);
INSERT INTO erp_product (id,name,bar_code,category_id,unit_id,status,purchase_price,sale_price,min_price,creator,updater,deleted,tenant_id)
VALUES (994006,'P2 Stock Product','P2-STOCK',994005,994004,0,10,20,1,'1','1',b'0',1);
INSERT INTO erp_stock (id,product_id,warehouse_id,`count`,creator,updater,deleted,tenant_id)
VALUES (994007,994006,994002,5,'1','1',b'0',1),
       (994008,994006,994003,0,'1','1',b'0',1);
INSERT INTO erp_stock_record (id,product_id,warehouse_id,`count`,total_count,biz_type,biz_id,biz_item_id,biz_no,creator,updater,deleted,tenant_id)
VALUES (994009,994006,994002,5,5,10,994007,994007,'P2-STOCK-OPENING-A','1','1',b'0',1),
       (994010,994006,994003,0,0,10,994008,994008,'P2-STOCK-OPENING-B','1','1',b'0',1);
""")


def redact_logs(secrets_to_redact):
    for name in ("backend.log",):
        path = OUT / name
        if path.exists():
            text = path.read_text(errors="replace")
            for secret in secrets_to_redact:
                if secret:
                    text = text.replace(secret, "[REDACTED]")
            text = re.sub(r"(?i)(Bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[REDACTED]", text)
            path.write_text(text)


def main():
    assert JAR.is_file(), JAR
    assert (UI_DIST / "index.html").is_file(), UI_DIST
    assert (PLAYWRIGHT / "playwright").is_dir(), PLAYWRIGHT
    static_count = assert_static_matches_jar()
    ports = (MYSQL_PORT, REDIS_PORT, APP_PORT)
    assert not any(listening(port) for port in ports), "a dedicated verification port is occupied"
    names = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
    assert MYSQL not in names and REDIS not in names, "dedicated container name already exists"
    OUT.mkdir(parents=True, exist_ok=True)
    db_password, redis_password = secrets.token_hex(20), secrets.token_hex(20)
    username, password = "erpstk" + secrets.token_hex(4), secrets.token_urlsafe(12)[:16]
    password_hash = run("htpasswd", "-bnBC", "4", username, password).stdout.strip().split(":", 1)[1]
    containers, processes = [], []
    report = {"result": "FAIL", "schema": SCHEMA,
              "jar_sha256": hashlib.sha256(JAR.read_bytes()).hexdigest(),
              "jar_static_resource_count": static_count, "jar_dist_byte_match": True,
              "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT, "app": APP_PORT},
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
            f"VALUES (994011,'{username}','{password_hash}','ERP stock browser',NULL,'[]',0,b'0',1);")
        sql("INSERT INTO system_user_role (user_id,role_id,creator,updater,deleted,tenant_id) "
            "SELECT 994011,role_id,creator,updater,b'0',tenant_id FROM system_user_role "
            "WHERE user_id=1 AND deleted=0;")
        seed_fixtures()
        browser_env = dict(env, NODE_PATH=str(PLAYWRIGHT),
                           YH_ERP_UI_ORIGIN=f"http://127.0.0.1:{APP_PORT}",
                           YH_ERP_BROWSER_OUTPUT=str(OUT / "browser.json"))
        browser = run("node", "scripts/verification/erp_stock_browser_probe.js", check=False, env=browser_env)
        report["browser_stdout"], report["browser_stderr"] = browser.stdout[-3000:], browser.stderr[-3000:]
        assert browser.returncode == 0, "desktop ERP stock browser probe failed"
        report["browser"] = json.loads((OUT / "browser.json").read_text())
        check_id, move_id = report["browser"]["checkId"], report["browser"]["moveId"]
        report["sql"] = {
            "check": sql(f"SELECT CONCAT(status,':',total_count,':',tenant_id) FROM erp_stock_check WHERE id={int(check_id)} AND deleted=0;"),
            "check_item": sql(f"SELECT CONCAT(warehouse_id,':',product_id,':',stock_count,':',actual_count,':',`count`) FROM erp_stock_check_item WHERE check_id={int(check_id)} AND deleted=0;"),
            "move": sql(f"SELECT CONCAT(status,':',total_count,':',tenant_id) FROM erp_stock_move WHERE id={int(move_id)} AND deleted=0;"),
            "move_item": sql(f"SELECT CONCAT(from_warehouse_id,':',to_warehouse_id,':',product_id,':',`count`) FROM erp_stock_move_item WHERE move_id={int(move_id)} AND deleted=0;"),
            "stock": sql("SELECT CONCAT(warehouse_id,':',`count`) FROM erp_stock WHERE product_id=994006 AND deleted=0 ORDER BY warehouse_id;"),
            "stock_records": sql("SELECT CONCAT(biz_type,':',warehouse_id,':',`count`) FROM erp_stock_record WHERE product_id=994006 AND deleted=0 ORDER BY id;"),
            "changesets": int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")),
            "seed_passwords_unchanged": seed_passwords == sql("SELECT id,password FROM system_users WHERE id < 900000 ORDER BY id;")}
        assert report["sql"]["check"].startswith("20:2.000000:1"), report["sql"]
        assert report["sql"]["check_item"] == "994002:994006:5.000000:7.000000:2.000000", report["sql"]
        assert report["sql"]["move"].startswith("20:3.000000:1"), report["sql"]
        assert report["sql"]["move_item"] == "994002:994003:994006:3.000000", report["sql"]
        assert report["sql"]["stock"] == "994002:4.000000\n994003:3.000000", report["sql"]
        assert report["sql"]["stock_records"].endswith("40:994002:2.000000\n32:994002:-3.000000\n30:994003:3.000000"), report["sql"]
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
