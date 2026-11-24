#!/usr/bin/env python3
"""Member Pay adapter acceptance against a disposable Pay/Member consumer."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
import secrets
import subprocess
import time

import p2_pay_pms_consumer_probe as support

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = 'yuheng_p2_member_pay_20261122'
MYSQL, REDIS = 'yh-p2-member-pay-mysql-20261122', 'yh-p2-member-pay-redis-20261122'
MYSQL_PORT, REDIS_PORT, APP_PORT, UI_PORT = 13402, 16482, 48262, 5220
MEMBER_ID = 998501
READER_PERMISSIONS = ('member:user:query', 'pay:wallet:query')


def validate_isolation():
    if not re.fullmatch(r'yuheng_p2_member_pay_\d{8}(?:_[a-z0-9]+)?', SCHEMA):
        raise ValueError('expected dedicated Member/Pay schema')
    suffix = SCHEMA.removeprefix('yuheng_p2_member_pay_')
    if MYSQL != 'yh-p2-member-pay-mysql-' + suffix or REDIS != 'yh-p2-member-pay-redis-' + suffix:
        raise ValueError('expected dedicated Member/Pay containers')
    ports = (MYSQL_PORT, REDIS_PORT, APP_PORT, UI_PORT)
    if len(set(ports)) != 4 or any(port in (3306, 6379, 5173, 48080) for port in ports):
        raise ValueError('expected distinct dedicated ports')


def wallet_snapshot(sql):
    return (
        sql('SELECT id,user_id,user_type,balance,total_expense,total_recharge,tenant_id,deleted+0 '
            'FROM pay_wallet ORDER BY id;'),
        sql('SELECT id,wallet_id,biz_type,biz_id,price,balance,tenant_id,deleted+0 '
            'FROM pay_wallet_transaction ORDER BY id;'),
    )


def sql_literal(value):
    return "'" + value.replace('\\', '\\\\').replace("'", "''") + "'"


def stop(process):
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=35)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)


def main():
    validate_isolation()
    os.umask(0o077)
    jar = Path(os.environ['P2_MEMBER_PAY_JAR']).resolve()
    dist = Path(os.environ['P2_MEMBER_PAY_DIST']).resolve()
    out = Path(os.environ['P2_MEMBER_PAY_OUT']).resolve()
    assert jar.is_file() and (dist / 'index.html').is_file()
    out.mkdir(parents=True, exist_ok=True)
    ports = (MYSQL_PORT, REDIS_PORT, APP_PORT, UI_PORT)
    assert not any(support.port_ready(port) for port in ports), 'probe port occupied'
    names = support.run('docker', 'ps', '-a', '--format', '{{.Names}}').stdout.splitlines()
    assert MYSQL not in names and REDIS not in names
    support.SCHEMA = SCHEMA
    sql = lambda statement: support.sql(MYSQL, statement)
    db_password, redis_password = secrets.token_hex(20), secrets.token_hex(20)
    users = [(998504, 'p2payadmin' + secrets.token_hex(3), secrets.token_urlsafe(12)[:16]),
             (998505, 'p2payreader' + secrets.token_hex(3), secrets.token_urlsafe(12)[:16])]
    containers, app, ui = [], None, None
    result = {'result': 'FAIL', 'work_id': 'YH-20261111-full-source-migration', 'schema': SCHEMA,
              'jar_sha256': hashlib.sha256(jar.read_bytes()).hexdigest(),
              'ports': list(ports), 'credentials_recorded': False, 'events': []}
    base = f'http://127.0.0.1:{APP_PORT}'

    def expect(method, path, token='', body=None, code=0, headers=None):
        status, payload = support.call(base, method, path, token, body, headers)
        result['events'].append({'method': method, 'path': path.split('?')[0], 'http': status,
                                 'code': payload.get('code')})
        assert status == 200 and payload.get('code') == code, (
            method, path, status, payload.get('code'), payload.get('msg'))
        return payload.get('data')

    def snapshot():
        return wallet_snapshot(sql)

    try:
        support.run('docker', 'run', '-d', '--name', MYSQL, '-e', 'MYSQL_ROOT_PASSWORD=' + db_password,
                    '-e', 'MYSQL_DATABASE=' + SCHEMA, '-p', f'127.0.0.1:{MYSQL_PORT}:3306', 'mysql:8.0.33')
        containers.append(MYSQL)
        support.run('docker', 'run', '-d', '--name', REDIS, '-p', f'127.0.0.1:{REDIS_PORT}:6379',
                    'redis:7.2.17', 'redis-server', '--requirepass', redis_password)
        containers.append(REDIS)
        deadline = time.monotonic() + 120
        while True:
            try:
                if sql('SELECT DATABASE();') == SCHEMA:
                    break
            except subprocess.CalledProcessError:
                pass
            assert time.monotonic() < deadline, 'isolated MySQL readiness timeout'
            time.sleep(1)
        env = dict(os.environ, YUHENG_DB_HOST='127.0.0.1', YUHENG_DB_PORT=str(MYSQL_PORT),
                   YUHENG_DB_NAME=SCHEMA, YUHENG_DB_USERNAME='root', YUHENG_DB_PASSWORD=db_password,
                   YUHENG_REDIS_PASSWORD=redis_password)
        log = (out / 'backend.log').open('w')
        command = ['java', '-jar', str(jar), f'--server.port={APP_PORT}', '--spring.profiles.active=local',
                   '--spring.data.redis.host=127.0.0.1', f'--spring.data.redis.port={REDIS_PORT}',
                   '--spring.data.redis.database=2', '--spring.data.redis.password=' + redis_password,
                   '--yuheng.security.mock-enable=false', '--spring.quartz.auto-startup=false',
                   '--yuheng.captcha.enable=false', '--logging.level.com.yuheng.platform=warn']
        app = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=log)
        deadline = time.monotonic() + 180
        while not support.port_ready(APP_PORT):
            assert app.poll() is None and time.monotonic() < deadline, 'isolated Demo failed to start'
            time.sleep(1)
        deadline = time.monotonic() + 120
        while True:
            try:
                changesets = int(sql('SELECT COUNT(*) FROM DATABASECHANGELOG;'))
                if changesets >= 107:
                    break
            except (subprocess.CalledProcessError, ValueError):
                pass
            assert app.poll() is None and time.monotonic() < deadline, 'Liquibase cold install timed out'
            time.sleep(1)
        result['changesets_first'] = changesets
        seed_passwords_before = sql('SELECT id,password FROM system_users ORDER BY id;')

        user_values = []
        for identifier, username, password in users:
            hashed = subprocess.run(['htpasswd', '-bnBC', '4', username, password],
                                    capture_output=True, text=True, check=True).stdout.strip().split(':', 1)[1]
            user_values.append((identifier, username, password, hashed))
        reader_menu_rows = sql('SELECT id,permission,parent_id FROM system_menu WHERE deleted=0 AND permission IN ('
                               + ','.join(sql_literal(p) for p in READER_PERMISSIONS) + ');')
        reader_menus, reader_parent_ids = {}, set()
        for row in reader_menu_rows.splitlines():
            menu_id, permission, parent_id = row.split('\t')
            reader_menus[permission] = int(menu_id)
            reader_parent_ids.add(int(parent_id))
        assert set(reader_menus) == set(READER_PERMISSIONS)
        member_parent_rows = sql('SELECT id,parent_id FROM system_menu WHERE id IN ('
                                 + ','.join(str(value) for value in reader_parent_ids) + ');')
        member_menu_ids = set(reader_parent_ids)
        member_menu_ids.update(int(row.split('\t')[1]) for row in member_parent_rows.splitlines())
        sql("INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) "
            + 'VALUES ' + ','.join(f"({i},'{u}','{h}','P2 Pay User',NULL,'[]',0,b'0',1)"
                       for i, u, _, h in user_values) + ";"
            "INSERT INTO system_role (id,name,code,sort,data_scope,data_scope_dept_ids,status,type,creator,updater,deleted,tenant_id) "
            "VALUES (998506,'P2 Pay Limited','p2_pay_limited',1,1,'',0,1,'probe','probe',b'0',1);"
            "INSERT INTO system_role_menu (role_id,menu_id,creator,updater,deleted,tenant_id) VALUES "
            + ','.join(f"(998506,{menu},'probe','probe',b'0',1)" for menu in member_menu_ids | set(reader_menus.values())) + ';'
            "INSERT INTO system_user_role (user_id,role_id,creator,updater,deleted,tenant_id) VALUES "
            "(998504,1,'probe','probe',b'0',1),(998505,998506,'probe','probe',b'0',1);")
        admin = support.login(base, user_values[0][1], user_values[0][2])
        reader = support.login(base, user_values[1][1], user_values[1][2])
        member_hash = subprocess.run(['htpasswd', '-bnBC', '4', '19900009851', 'P2Member851'],
                                     capture_output=True, text=True, check=True).stdout.strip().split(':', 1)[1]
        sql(f"INSERT INTO member_user (id,mobile,email,password,status,register_ip,nickname,tenant_id) "
            f"VALUES ({MEMBER_ID},'19900009851','',{sql_literal(member_hash)},0,'127.0.0.1','P2 Pay Member',1);")
        member_user_before = sql('SELECT password,tenant_id FROM member_user WHERE id=998501;')
        assert sql('SELECT COUNT(*) FROM pay_wallet WHERE user_id=998501 AND user_type=1;') == '0'
        wallet = expect('GET', f'/pay/wallet/get?userId={MEMBER_ID}', admin)
        assert wallet['userId'] == MEMBER_ID and wallet['balance'] == 0
        wallet_id = int(wallet['id'])
        wallet_sql_before = sql(f'SELECT balance,total_expense,total_recharge,tenant_id FROM pay_wallet WHERE id={wallet_id};')
        before = snapshot()
        expect('PUT', '/pay/wallet/update-balance', reader, {'userId': MEMBER_ID, 'balance': 777}, 403)
        assert before == snapshot(), 'read-only role changed wallet state'
        expect('PUT', '/pay/wallet/update-balance', admin, {'userId': MEMBER_ID, 'balance': 100},
               403, {'tenant-id': '2'})
        expect('PUT', '/pay/wallet/update-balance', '', {'userId': MEMBER_ID, 'balance': 50}, 401)
        assert before == snapshot(), 'rejected wallet update changed database state'
        sql("CREATE TRIGGER p2_member_pay_fail BEFORE INSERT ON pay_wallet_transaction FOR EACH ROW "
            "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='P2_MEMBER_PAY_INJECTED';")
        expect('PUT', '/pay/wallet/update-balance', admin, {'userId': MEMBER_ID, 'balance': 100}, 500)
        sql('DROP TRIGGER p2_member_pay_fail;')
        assert wallet_sql_before == sql(f'SELECT balance,total_expense,total_recharge,tenant_id FROM pay_wallet WHERE id={wallet_id};')
        assert before == snapshot(), 'failed ledger insert left partial wallet update'
        expect('PUT', '/pay/wallet/update-balance', admin, {'userId': MEMBER_ID, 'balance': 125})
        assert sql(f'SELECT price,balance,biz_type,tenant_id FROM pay_wallet_transaction WHERE wallet_id={wallet_id};') == '125\t125\t5\t1'

        ui_log = (out / 'ui.log').open('w')
        ui = subprocess.Popen(['python3', '-c',
            'import http.server,runpy; http.server.ThreadingHTTPServer.request_queue_size=128; '
            'runpy.run_path("scripts/ui_server.py",run_name="__main__")', '--root', str(dist),
            '--host', '127.0.0.1', '--port', str(UI_PORT), '--backend', base],
            cwd=ROOT, env=env, stdout=ui_log, stderr=ui_log)
        deadline = time.monotonic() + 30
        while not support.port_ready(UI_PORT):
            assert ui.poll() is None and time.monotonic() < deadline, 'isolated UI failed to start'
            time.sleep(.25)
        output = out / 'member-pay-browser.json'
        browser_env = dict(os.environ, P2_MEMBER_PAY_ORIGIN=f'http://127.0.0.1:{UI_PORT}',
                           P2_MEMBER_PAY_ID=str(MEMBER_ID), P2_MEMBER_PAY_USER=user_values[0][1],
                           P2_MEMBER_PAY_PASSWORD=user_values[0][2], P2_MEMBER_PAY_READER=user_values[1][1],
                           P2_MEMBER_PAY_READER_PASSWORD=user_values[1][2],
                           P2_MEMBER_PAY_BROWSER_OUTPUT=str(output),
                           NODE_PATH='/Users/huhua/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules')
        browser = subprocess.run(['node', str(ROOT / 'scripts/verification/p2_member_pay_browser_probe.js')],
                                 cwd=ROOT, env=browser_env, timeout=240, check=False)
        browser_result = json.loads(output.read_text())
        assert browser.returncode == 0 and browser_result.get('result') == 'PASS', browser_result
        wallet_final = sql(f'SELECT balance,total_expense,total_recharge,tenant_id FROM pay_wallet WHERE id={wallet_id};')
        ledger_final = sql(f'SELECT price,balance,biz_type,tenant_id FROM pay_wallet_transaction WHERE wallet_id={wallet_id} ORDER BY id;')
        assert wallet_final == '300\t0\t0\t1', wallet_final
        assert ledger_final == '125\t125\t5\t1\n250\t375\t5\t1\n-75\t300\t5\t1', ledger_final
        assert sql('SELECT password,tenant_id FROM member_user WHERE id=998501;') == member_user_before
        assert sql('SELECT id,password FROM system_users WHERE id NOT IN (998504,998505) ORDER BY id;') == seed_passwords_before
        stop(app)
        app = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=log)
        deadline = time.monotonic() + 180
        while not support.port_ready(APP_PORT):
            assert app.poll() is None and time.monotonic() < deadline, 'isolated Demo restart failed'
            time.sleep(1)
        support.login(base, user_values[0][1], user_values[0][2])
        assert wallet_final == sql(f'SELECT balance,total_expense,total_recharge,tenant_id FROM pay_wallet WHERE id={wallet_id};')
        assert sql('SELECT id,password FROM system_users WHERE id NOT IN (998504,998505) ORDER BY id;') == seed_passwords_before
        result.update({'result': 'PASS', 'changesets_second': int(sql('SELECT COUNT(*) FROM DATABASECHANGELOG;')),
                       'wallet_id': wallet_id, 'wallet_before_rejected_writes': wallet_sql_before,
                       'wallet_final': wallet_final, 'ledger_final': ledger_final,
                       'rollback_on_ledger_failure': True, 'member_password_unchanged': True,
                       'seed_passwords_unchanged': True, 'restarted': True,
                       'browser': browser_result})
        assert result['changesets_first'] == result['changesets_second'] == 107
    except Exception as error:
        result['error'] = str(error)
        raise
    finally:
        stop(ui)
        stop(app)
        for container in reversed(containers):
            support.run('docker', 'rm', '-fv', container, check=False)
        names = support.run('docker', 'ps', '-a', '--format', '{{.Names}}').stdout.splitlines()
        result['cleanup'] = {'containers_absent': MYSQL not in names and REDIS not in names,
                             'ports_listening': {str(port): support.port_ready(port) for port in ports}}
        result['cleanup']['complete'] = result['cleanup']['containers_absent'] and not any(
            result['cleanup']['ports_listening'].values())
        result['result'] = 'PASS' if result.get('result') == 'PASS' and result['cleanup']['complete'] else 'FAIL'
        (out / 'member-pay-runtime.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'result': result['result'], 'jar_sha256': result['jar_sha256'],
                      'cleanup': result['cleanup']}, ensure_ascii=False))
    if result['result'] != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
