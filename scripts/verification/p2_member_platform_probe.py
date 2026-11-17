#!/usr/bin/env python3
"""Real member API/SQL checks using disposable Docker services only."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import tempfile
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = 'yuheng_p2_member_20261117'
APP_PORT, MYSQL_PORT, REDIS_PORT = 48220, 13373, 16453
UI_PORT = 5203
MYSQL, REDIS = 'yh-p2-member-mysql-20261117', 'yh-p2-member-redis-20261117'
JAR = ROOT / 'yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar'
OUT = ROOT / 'docs/verification/2026-11-11-full-source-migration/p2-member-platform-20261117'
REQUIRED_CASES = dict.fromkeys(('member_crud', 'member_user_update', 'unauthorized_write_rejected',
                              'tenant_header_rejected', 'point_transaction', 'cleanup'), True)


def validate_probe_target(schema, app_port):
    if not re.fullmatch(r'yuheng_p2_member_[a-zA-Z0-9_]+', schema) or app_port != APP_PORT:
        raise ValueError('refusing shared schema or non-probe port')
    return True


def sql_literal(value):
    return "'" + value.replace("'", "''") + "'"


def run(*args, input_text=None):
    p = subprocess.run(args, input=input_text, text=True, capture_output=True)
    if p.returncode:
        raise RuntimeError(p.stderr.strip())
    return p.stdout.strip()


def listening(port):
    with socket.socket() as sock:
        return sock.connect_ex(('127.0.0.1', port)) == 0


def sql(statement):
    return run('docker', 'exec', '-i', MYSQL, 'sh', '-c',
               'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw '
               '--skip-column-names -D "$1"', 'probe', SCHEMA, input_text=statement)


class Probe:
    def __init__(self):
        self.events = []

    def call(self, method, path, token=None, body=None, tenant=1, expected=0):
        headers = {'Content-Type': 'application/json', 'tenant-id': str(tenant)}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        request = Request('http://127.0.0.1:%d/admin-api%s' % (APP_PORT, path), method=method,
                          headers=headers, data=None if body is None else json.dumps(body).encode())
        try:
            response = urlopen(request, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            data = json.load(response)
            status = response.status
        self.events.append({'method': method, 'path': path, 'http': status, 'code': data.get('code')})
        assert status == 200 and data.get('code') == expected, (method, path, status, data.get('code'), data.get('msg'))
        return data.get('data')

    def exercise(self, admin, guest, reader, cases):
        call = self.call
        assert sql('SELECT COUNT(*) FROM member_tag;') == '0'
        call('POST', '/member/tag/create', body={'name': 'P2 denied'}, expected=401)
        call('POST', '/member/tag/create', guest, {'name': 'P2 denied'}, expected=403)
        assert sql('SELECT COUNT(*) FROM member_tag;') == '0'
        cases['unauthorized_write_rejected'] = True
        resources = {
            'tag': {'name': 'P2 tag'},
            'group': {'name': 'P2 group', 'status': 0, 'remark': 'isolated probe'},
            'level': {'name': 'P2 level', 'level': 1, 'experience': 100,
                      'discountPercent': 90, 'status': 0, 'icon': '', 'backgroundUrl': ''},
        }
        ids = {}
        for resource, body in resources.items():
            identifier = call('POST', f'/member/{resource}/create', admin, body)
            ids[resource] = identifier
            body.update(id=identifier, name=body['name'] + ' updated')
            call('PUT', f'/member/{resource}/update', admin, body)
            assert call('GET', f'/member/{resource}/get?id={identifier}', admin)['name'] == body['name']
            assert sql(f'SELECT name FROM member_{resource} WHERE id={int(identifier)};') == body['name']

        # Member users are tenant-owned; create only isolated test fixtures in SQL.
        sql("INSERT INTO member_user (id,mobile,status,register_ip,nickname,tenant_id) VALUES "
            "(990951,'19900000951',0,'127.0.0.1','P2 member 1',1),"
            "(990952,'19900000952',0,'127.0.0.1','P2 member 2',2);")
        before = sql('SELECT id,nickname,point,tenant_id FROM member_user WHERE id IN (990951,990952) ORDER BY id;')
        assert call('GET', '/member/user/get?id=990952', admin, tenant=1) is None
        call('GET', '/member/user/get?id=990951', admin, tenant=2, expected=403)
        assert sql('SELECT id,nickname,point,tenant_id FROM member_user WHERE id IN (990951,990952) ORDER BY id;') == before
        cases['tenant_header_rejected'] = True
        update = {'id': 990951, 'mobile': '19900000951', 'status': 0, 'nickname': 'P2 member updated',
                  'email': '', 'avatar': '', 'name': '', 'sex': 0, 'mark': 'P2 verified',
                  'tagIds': [], 'levelId': ids['level'], 'groupId': ids['group']}
        call('PUT', '/member/user/update', admin, update)
        user = call('GET', '/member/user/get?id=990951', admin)
        assert user['nickname'] == update['nickname'] and user['levelId'] == ids['level']
        row = sql('SELECT nickname,level_id,group_id,tenant_id FROM member_user WHERE id=990951;').split('\t')
        assert row == [update['nickname'], str(ids['level']), str(ids['group']), '1']
        cases['member_user_update'] = True

        sql("UPDATE member_user SET point=10 WHERE id=990951;")
        before_points = sql('SELECT point FROM member_user WHERE id=990951;')
        trigger = ("CREATE TRIGGER p2_member_point_failure BEFORE INSERT ON member_point_record "
                   "FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='P2_MEMBER_POINT_INJECTED'")
        sql(trigger)
        before_records = sql('SELECT id,point,total_point FROM member_point_record WHERE user_id=990951 ORDER BY id;')
        call('PUT', '/member/user/update-point', admin, {'id': 990951, 'point': 5}, expected=500)
        after_points = sql('SELECT point FROM member_user WHERE id=990951;')
        after_records = sql('SELECT id,point,total_point FROM member_point_record WHERE user_id=990951 ORDER BY id;')
        sql('DROP TRIGGER p2_member_point_failure;')
        assert before_points == after_points == '10'
        assert before_records == after_records == ''
        assert sql('SELECT COUNT(*) FROM member_point_record WHERE user_id=990951;') == '0'
        call('PUT', '/member/user/update-point', admin, {'id': 990951, 'point': 5})
        assert sql('SELECT point FROM member_user WHERE id=990951;') == '15'
        assert sql('SELECT CONCAT(point,":",total_point) FROM member_point_record WHERE user_id=990951;') == '5:15'
        cases['point_transaction'] = True

        call('DELETE', f"/member/group/delete?id={ids['group']}", admin, expected=1004012001)
        call('DELETE', f"/member/level/delete?id={ids['level']}", admin, expected=1004011005)
        sql('UPDATE member_user SET level_id=NULL,group_id=NULL WHERE id=990951;')
        call('DELETE', f"/member/tag/delete?id={ids['tag']}", admin)
        call('DELETE', f"/member/group/delete?id={ids['group']}", admin)
        call('DELETE', f"/member/level/delete?id={ids['level']}", admin)
        for table, identifier in (('member_tag', ids['tag']), ('member_group', ids['group']),
                                  ('member_level', ids['level'])):
            assert sql(f'SELECT deleted+0 FROM {table} WHERE id={int(identifier)};') == '1'
        cases['member_crud'] = True
        return {'fixture_user_count': 2, 'member_data_tenant_scoped': True,
                'lookup_foreign_tenant_hidden': True, 'spoofed_tenant_rejected': True,
                'points_after_injected_failure': 10, 'points_after_credit': 15,
                'referenced_group_and_level_delete_rejected': True,
                'dimension_records_soft_deleted': True, 'events': self.events}


def stop(app):
    if app is None or app.poll() is not None:
        return True
    app.terminate()
    try:
        app.wait(timeout=35)
        return True
    except subprocess.TimeoutExpired:
        app.kill()
        app.wait(timeout=10)
        return False


def main():
    validate_probe_target(SCHEMA, APP_PORT)
    assert JAR.is_file()
    ports = (MYSQL_PORT, REDIS_PORT, APP_PORT, UI_PORT)
    assert not any(listening(port) for port in ports)
    existing = run('docker', 'ps', '-a', '--format', '{{.Names}}').splitlines()
    assert MYSQL not in existing and REDIS not in existing
    db_password, redis_password = secrets.token_hex(20), secrets.token_hex(20)
    suffix = secrets.token_hex(4)
    admin_name, admin_password = 'p2memberadmin' + suffix, secrets.token_urlsafe(12)[:16]
    guest_name, guest_password = 'p2memberguest' + suffix, secrets.token_urlsafe(12)[:16]
    admin_hash = subprocess.run(['htpasswd', '-bnBC', '4', admin_name, admin_password],
                                capture_output=True, text=True, check=True).stdout.strip().split(':', 1)[1]
    guest_hash = subprocess.run(['htpasswd', '-bnBC', '4', guest_name, guest_password],
                                capture_output=True, text=True, check=True).stdout.strip().split(':', 1)[1]
    result = {'work_id': 'YH-20261111-full-source-migration', 'schema': SCHEMA,
              'jar_sha256': hashlib.sha256(JAR.read_bytes()).hexdigest(),
              'credentials_recorded': False, 'cases': {}}
    containers, app, ui = [], None, None
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        run('docker', 'run', '-d', '--name', MYSQL, '-e', 'MYSQL_ROOT_PASSWORD=' + db_password,
            '-e', 'MYSQL_DATABASE=' + SCHEMA, '-p', f'127.0.0.1:{MYSQL_PORT}:3306', 'mysql:8.0.33')
        containers.append(MYSQL)
        run('docker', 'run', '-d', '--name', REDIS, '-p', f'127.0.0.1:{REDIS_PORT}:6379',
            'redis:7.2.17', 'redis-server', '--requirepass', redis_password)
        containers.append(REDIS)
        deadline = time.monotonic() + 100
        while True:
            try:
                if sql('SELECT DATABASE();') == SCHEMA:
                    break
            except RuntimeError:
                pass
            assert time.monotonic() < deadline, 'isolated MySQL readiness timeout'
            time.sleep(1)
        with tempfile.TemporaryDirectory(prefix='yuheng-p2-member-') as temp:
            log_path = Path(temp) / 'demo.log'
            env = dict(os.environ, YUHENG_DB_HOST='127.0.0.1', YUHENG_DB_PORT=str(MYSQL_PORT),
                       YUHENG_DB_NAME=SCHEMA, YUHENG_DB_USERNAME='root', YUHENG_DB_PASSWORD=db_password,
                       YUHENG_REDIS_PASSWORD=redis_password)
            log = log_path.open('w')
            app = subprocess.Popen(['java', '-jar', str(JAR), f'--server.port={APP_PORT}',
                '--spring.profiles.active=local', '--spring.data.redis.host=127.0.0.1',
                f'--spring.data.redis.port={REDIS_PORT}', '--spring.data.redis.database=0',
                '--spring.data.redis.password=' + redis_password, '--yudao.security.mock-enable=false',
                '--spring.quartz.auto-startup=false', '--yudao.captcha.enable=false'],
                cwd=ROOT, env=env, stdout=log, stderr=log)
            deadline = time.monotonic() + 180
            while not listening(APP_PORT):
                assert app.poll() is None and time.monotonic() < deadline, 'isolated Demo failed to start'
                time.sleep(1)
            deadline = time.monotonic() + 30
            while sql('SELECT COUNT(*) FROM DATABASECHANGELOG;') != '56':
                assert time.monotonic() < deadline, 'Liquibase changeset count mismatch'
                time.sleep(1)
            sql("UPDATE system_tenant SET status=0, expire_time=DATE_ADD(NOW(), INTERVAL 1 YEAR) WHERE id=2 AND deleted=0;")
            sql('INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) '
                'VALUES (990954,' + sql_literal(admin_name) + ',' + sql_literal(admin_hash) +
                ",'P2 admin',NULL,'[]',0,b'0',1);")
            sql('INSERT INTO system_user_role (user_id,role_id,creator,updater,deleted,tenant_id) '
                'SELECT 990954,role_id,creator,updater,b\'0\',tenant_id FROM system_user_role '
                'WHERE user_id=1 AND deleted=0;')
            assert sql('SELECT COUNT(*) FROM system_user_role WHERE user_id=990954 AND deleted=0;') != '0'
            sql('INSERT INTO system_users (id,username,password,nickname,dept_id,post_ids,status,deleted,tenant_id) '
                'VALUES (990953,' + sql_literal(guest_name) + ',' + sql_literal(guest_hash) +
                ",'P2 no-role',NULL,'[]',0,b'0',1);")
            probe = Probe()
            admin = probe.call('POST', '/system/auth/login', body={'username': admin_name, 'password': admin_password})['accessToken']
            guest = probe.call('POST', '/system/auth/login', body={'username': guest_name, 'password': guest_password})['accessToken']
            result['cases']['member_runtime'] = probe.exercise(admin, guest, None, result['cases'])
            result['changesets'] = 56
            result['completed'] = all(result['cases'].get(key) for key in REQUIRED_CASES if key != 'cleanup')
            ui_log = (Path(temp) / 'ui.log').open('w')
            ui = subprocess.Popen(['python3', '-c',
                'import http.server,runpy; http.server.ThreadingHTTPServer.request_queue_size=128; '
                'runpy.run_path("scripts/ui_server.py",run_name="__main__")',
                '--root', 'yuheng-demo-ui/dist', '--host', '127.0.0.1', '--port', str(UI_PORT),
                '--backend', f'http://127.0.0.1:{APP_PORT}'],
                cwd=ROOT, env=env, stdout=ui_log, stderr=ui_log)
            deadline = time.monotonic() + 30
            while not listening(UI_PORT):
                assert ui.poll() is None and time.monotonic() < deadline, 'isolated UI failed to start'
                time.sleep(.25)
            browser_output = OUT / 'member-browser.json'
            browser_env = dict(os.environ, YH_MEMBER_BROWSER_OUTPUT=str(browser_output),
                               YH_MEMBER_USERNAME=admin_name, YH_MEMBER_PASSWORD=admin_password,
                               NODE_PATH='/Users/huhua/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules')
            browser = subprocess.run(['node', 'scripts/verification/p2_member_browser_probe.js'],
                                     cwd=ROOT, env=browser_env, timeout=180, check=False)
            browser_data = json.loads(browser_output.read_text())
            result['cases']['member_browser'] = browser_data
            result['completed'] = result['completed'] and browser.returncode == 0 and browser_data.get('completed')
            if result['completed']:
                user_point = sql('SELECT point FROM member_user WHERE id=990951;')
                point_record = sql('SELECT CONCAT(point,":",total_point,":",biz_type) '
                                   'FROM member_point_record WHERE user_id=990951 '
                                   'ORDER BY id DESC LIMIT 1;')
                assert user_point == '13' and point_record == '-2:13:2', (user_point, point_record)
                result['cases']['member_browser_sql'] = {
                    'member_user_point': int(user_point),
                    'latest_point_record': point_record,
                    'verified': True,
                }
    finally:
        result['cleanup'] = {'app_stopped': stop(app), 'ui_stopped': stop(ui), 'containers_absent': False,
                             'ports_listening': {str(port): listening(port) for port in ports}}
        for name in reversed(containers):
            subprocess.run(['docker', 'rm', '-fv', name], check=True, capture_output=True, text=True)
        names = run('docker', 'ps', '-a', '--format', '{{.Names}}').splitlines()
        result['cleanup']['containers_absent'] = all(name not in names for name in (MYSQL, REDIS))
        time.sleep(1)
        result['cleanup']['ports_listening'] = {str(port): listening(port) for port in ports}
        result['cases']['cleanup'] = (result['cleanup']['containers_absent'] and
                                      not any(result['cleanup']['ports_listening'].values()))
        result['completed'] = result.get('completed', False) and result['cases']['cleanup']
        (OUT / 'member-runtime.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        assert result['cases']['cleanup'], result['cleanup']


if __name__ == '__main__':
    main()
