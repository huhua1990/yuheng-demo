#!/usr/bin/env python3
"""Run the Member admin permission matrix with disposable services."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import time

import member_permission_matrix_probe as probe


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "yuheng_t4_member_acl_20261123"
MYSQL = "yh-member-acl-mysql-20261123"
REDIS = "yh-member-acl-redis-20261123"
MYSQL_PORT, REDIS_PORT, APP_PORT = 13399, 16480, 48260
JAR = ROOT / "yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar"
OUT = ROOT / "docs/verification/2026-11-11-full-source-migration/member-permission-matrix-20261123"


def run(*args: str, check: bool = True, input_text: str | None = None, env=None):
    return subprocess.run(args, check=check, input=input_text, text=True, capture_output=True, env=env)


def listening(port: int) -> bool:
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def sql(statement: str) -> str:
    return run("docker", "exec", "-i", MYSQL, "sh", "-c",
               'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw --skip-column-names -D "$1"',
               "probe", SCHEMA, input_text=statement).stdout.strip()


def literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def stop(process):
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=35)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def main() -> None:
    probe.validate_probe_target(SCHEMA, APP_PORT, MYSQL_PORT, REDIS_PORT)
    assert JAR.is_file(), JAR
    assert not any(listening(port) for port in (MYSQL_PORT, REDIS_PORT, APP_PORT))
    existing = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
    assert MYSQL not in existing and REDIS not in existing
    OUT.mkdir(parents=True, exist_ok=True)
    db_password, redis_password = secrets.token_hex(20), secrets.token_hex(20)
    suffix = secrets.token_hex(4)
    allowed_user, allowed_password = "mAclAllowed" + suffix, secrets.token_urlsafe(12)[:16]
    denied_user, denied_password = "mAclDenied" + suffix, secrets.token_urlsafe(12)[:16]
    allowed_hash = run("htpasswd", "-bnBC", "4", allowed_user, allowed_password).stdout.strip().split(":", 1)[1]
    denied_hash = run("htpasswd", "-bnBC", "4", denied_user, denied_password).stdout.strip().split(":", 1)[1]
    app = None
    containers: list[str] = []
    result: dict[str, object] = {"result": "FAIL", "schema": SCHEMA,
                                  "ports": {"mysql": MYSQL_PORT, "redis": REDIS_PORT, "app": APP_PORT},
                                  "jar_sha256": hashlib.sha256(JAR.read_bytes()).hexdigest(),
                                  "credentials_recorded": False}
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
                   YUHENG_REDIS_PASSWORD=redis_password,
                   YUHENG_PROBE_ALLOWED_USERNAME=allowed_user, YUHENG_PROBE_ALLOWED_PASSWORD=allowed_password,
                   YUHENG_PROBE_NO_ROLE_USERNAME=denied_user, YUHENG_PROBE_NO_ROLE_PASSWORD=denied_password)
        os.environ.update({key: env[key] for key in (
            "YUHENG_PROBE_ALLOWED_USERNAME", "YUHENG_PROBE_ALLOWED_PASSWORD",
            "YUHENG_PROBE_NO_ROLE_USERNAME", "YUHENG_PROBE_NO_ROLE_PASSWORD")})
        log_path = OUT / "backend.log"
        log = log_path.open("w")
        app = subprocess.Popen(["java", "-jar", str(JAR), f"--server.port={APP_PORT}",
            "--spring.profiles.active=local", "--spring.data.redis.host=127.0.0.1",
            f"--spring.data.redis.port={REDIS_PORT}", "--spring.data.redis.database=0",
            "--spring.data.redis.password=" + redis_password, "--yudao.security.mock-enable=false",
            "--spring.quartz.auto-startup=false", "--yudao.captcha.enable=false"],
            cwd=ROOT, env=env, stdout=log, stderr=log)
        deadline = time.monotonic() + 180
        while not listening(APP_PORT):
            assert app.poll() is None, f"Demo JAR exited; see {log_path}"
            assert time.monotonic() < deadline, "Demo readiness timeout"
            time.sleep(1)
        deadline = time.monotonic() + 90
        while int(sql("SELECT COUNT(*) FROM DATABASECHANGELOG;")) < probe.MIN_CHANGESETS:
            assert time.monotonic() < deadline, "Liquibase readiness timeout"
            time.sleep(1)

        permissions = [row.split("\t", 1) for row in sql(
            "SELECT id,permission FROM system_menu WHERE deleted=0 AND permission<>'';").splitlines()]
        permission_ids = {permission: int(menu_id) for menu_id, permission in permissions}
        required = {case.permission for case in (*probe.MEMBER_READ_CASES, *probe.MEMBER_WRITE_CASES)
                    if case.permission != "authenticated-read"}
        assert required <= permission_ids.keys(), sorted(required - permission_ids.keys())
        role_id = 990967
        role_menu_start = 990968
        sql("INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) VALUES "
            f"(990959,{literal(allowed_user)},{literal(allowed_hash)},'ACL allowed',NULL,'[]',0,b'0',1),"
            f"(990960,{literal(denied_user)},{literal(denied_hash)},'ACL denied',NULL,'[]',0,b'0',1);")
        sql("INSERT INTO system_role (id,name,code,sort,data_scope,data_scope_dept_ids,status,type,remark,creator,updater,deleted,tenant_id) VALUES "
            f"({role_id},'Member ACL probe','member_acl_{suffix}',1,1,'',0,1,'isolated permission fixture','probe','probe',b'0',1);")
        role_menu_rows = ",".join(
            f"({role_menu_start + index},{role_id},{permission_ids[permission]},'probe','probe',b'0',1)"
            for index, permission in enumerate(sorted(required)))
        sql("INSERT INTO system_role_menu (id,role_id,menu_id,creator,updater,deleted,tenant_id) VALUES "
            + role_menu_rows + ";")
        sql(f"INSERT INTO system_user_role (id,user_id,role_id,creator,updater,deleted,tenant_id) VALUES (990969,990959,{role_id},'probe','probe',b'0',1);")
        sql("INSERT INTO member_user (id,mobile,email,password,status,register_ip,nickname,avatar,point,tag_ids,level_id,experience,group_id,deleted,tenant_id) "
            "VALUES (990961,'13900009961','acl@example.com','fixture',0,'127.0.0.1','ACL member','',10,NULL,NULL,100,NULL,b'0',1);")
        sql("INSERT INTO member_tag (id,name,deleted,tenant_id) VALUES (990962,'ACL tag',b'0',1);")
        sql("INSERT INTO member_group (id,name,status,remark,deleted,tenant_id) VALUES (990963,'ACL group',0,'probe',b'0',1);")
        sql("INSERT INTO member_level (id,name,level,experience,discount_percent,icon,background_url,status,deleted,tenant_id) VALUES (990964,'ACL level',8,800,90,'','',0,b'0',1);")
        sql("INSERT INTO member_sign_in_config (id,day,point,experience,status,deleted,tenant_id) VALUES (990965,7,7,1,0,b'0',1);")
        sql("INSERT INTO member_config (id,point_trade_deduct_enable,point_trade_deduct_unit_price,point_trade_deduct_max_price,point_trade_give_point,deleted,tenant_id) VALUES (990966,b'1',10,100,1,b'0',1);")
        sql("INSERT INTO member_experience_record (id,user_id,biz_id,biz_type,title,description,experience,total_experience,deleted,tenant_id) VALUES (990970,990961,'probe',1,'probe','probe',1,101,b'0',1);")
        sql("INSERT INTO member_level_record (id,user_id,level_id,level,discount_percent,experience,user_experience,remark,description,deleted,tenant_id) VALUES (990971,990961,990964,8,90,800,100,'probe','probe',b'0',1);")
        sql("INSERT INTO member_point_record (id,user_id,biz_id,biz_type,title,description,point,total_point,deleted,tenant_id) VALUES (990972,990961,'probe',2,'probe','probe',1,10,b'0',1);")
        sql("INSERT INTO member_sign_in_record (id,user_id,day,point,experience,deleted,tenant_id) VALUES (990973,990961,7,7,1,b'0',1);")
        args = type("ProbeArgs", (), {"base_url": f"http://127.0.0.1:{APP_PORT}", "schema": SCHEMA,
                                      "mysql_container": MYSQL})()
        evidence = probe.PermissionProbe(args).run()
        result.update(evidence)
        result["result"] = "PASS"
    except Exception as error:
        result["error"] = str(error)
        raise
    finally:
        stop(app)
        for name in reversed(containers):
            run("docker", "rm", "-fv", name, check=False)
        remaining = run("docker", "ps", "-a", "--format", "{{.Names}}").stdout.splitlines()
        cleanup = {"containers_absent": all(name not in remaining for name in (MYSQL, REDIS)),
                    "ports_listening": {str(port): listening(port) for port in (MYSQL_PORT, REDIS_PORT, APP_PORT)}}
        cleanup["passed"] = cleanup["containers_absent"] and not any(cleanup["ports_listening"].values())
        result["cleanup"] = cleanup
        OUT.joinpath("runtime.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        assert cleanup["passed"], cleanup
    print(json.dumps({"result": result["result"], "requests": len(result.get("requests", [])),
                      "changesets": result.get("changesets")}))


if __name__ == "__main__":
    main()
