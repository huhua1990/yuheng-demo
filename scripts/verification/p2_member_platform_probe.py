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
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = 'yuheng_p2_member_20261117'
APP_PORT, MYSQL_PORT, REDIS_PORT = 48220, 13373, 16453
UI_PORT = 5203
MYSQL, REDIS = 'yh-p2-member-mysql-20261117', 'yh-p2-member-redis-20261117'
JAR = ROOT / 'yuheng-demo-server/yuheng-demo-server-bootstrap/target/yuheng-demo.jar'
UI_DIST = Path(os.environ.get('YH_MEMBER_UI_DIST', ROOT / 'yuheng-demo-ui/dist')).resolve()
OUT = Path(os.environ.get('YH_MEMBER_PROBE_OUTPUT_DIR',
                          ROOT / 'docs/verification/2026-11-11-full-source-migration/p2-member-platform-20261117'))
REQUIRED_CASES = dict.fromkeys(('member_crud', 'member_user_update', 'unauthorized_write_rejected',
                              'tenant_header_rejected', 'point_transaction', 'member_app_login',
                              'address_owner_isolation', 'sign_in_rule_lifecycle',
                              'sign_in_rewards_lifecycle', 'sign_in_concurrency', 'cleanup'), True)


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

    def call(self, method, path, token=None, body=None, tenant=1, expected=0, prefix='/admin-api'):
        headers = {'Content-Type': 'application/json', 'tenant-id': str(tenant)}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        request = Request('http://127.0.0.1:%d%s%s' % (APP_PORT, prefix, path), method=method,
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
        assert sql('SELECT COUNT(*) FROM member_user WHERE id IN (990951,990952,990955);') == '3'
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

    @staticmethod
    def installed_changesets(count):
        count = int(count)
        assert count >= 56, f'incomplete Liquibase installation: {count}'
        return count

    def exercise_app(self, first_token, second_token, cases):
        call = self.call
        invalid_address = call('POST', '/member/address/create', first_token,
                          {'name': 'P2 recipient too long', 'mobile': '19900000951', 'areaId': 110000,
                           'detailAddress': 'isolated address', 'defaultStatus': True}, expected=400, prefix='/app-api')
        assert sql('SELECT COUNT(*) FROM member_address;') == '0'
        address_id = call('POST', '/member/address/create', first_token,
                          {'name': 'P2 member', 'mobile': '19900000951', 'areaId': 110000,
                           'detailAddress': 'isolated address', 'defaultStatus': True}, prefix='/app-api')
        first_list = call('GET', '/member/address/list', first_token, prefix='/app-api')
        second_list = call('GET', '/member/address/list', second_token, prefix='/app-api')
        assert [item['id'] for item in first_list] == [address_id]
        assert all(item['id'] != address_id for item in second_list)
        assert call('GET', f'/member/address/get?id={address_id}', second_token,
                    prefix='/app-api') is None
        assert call('GET', f'/member/address/get?id={address_id}', first_token,
                    prefix='/app-api')['id'] == address_id
        assert sql('SELECT user_id,default_status+0 FROM member_address WHERE id=%d;' % int(address_id)) == '990951\t1'
        call('PUT', '/member/address/update', first_token,
             {'id': address_id, 'name': 'P2 updated', 'mobile': '19900000951', 'areaId': 110000,
              'detailAddress': 'updated isolated address', 'defaultStatus': True}, prefix='/app-api')
        assert call('GET', f'/member/address/get?id={address_id}', first_token,
                    prefix='/app-api')['name'] == 'P2 updated'
        assert sql('SELECT name,default_status+0 FROM member_address WHERE id=%d;' % int(address_id)) == 'P2 updated\t1'
        call('DELETE', f'/member/address/delete?id={address_id}', first_token, prefix='/app-api')
        assert sql('SELECT deleted+0 FROM member_address WHERE id=%d;' % int(address_id)) == '1'
        cases['address_owner_isolation'] = True
        cases['address_validation'] = {'overlong_name_rejected_before_write': invalid_address is None,
                                       'valid_name_persisted': True}
        return {'created_address_owned_by': 990951, 'foreign_user_hidden': True,
                'cross_user_get_rejected': True, 'soft_delete_verified': True,
                'events': [event for event in self.events if event['path'].startswith('/member/address/')]}

    def exercise_sign_in_rules(self, admin, cases):
        call = self.call
        rule = {'day': 27, 'point': 8, 'experience': 3, 'status': 0}
        identifier = call('POST', '/member/sign-in/config/create', admin, rule)
        assert sql(f'SELECT day,point,experience,status FROM member_sign_in_config WHERE id={int(identifier)};') == '27\t8\t3\t0'
        duplicate = dict(rule, day=27, point=9)
        call('POST', '/member/sign-in/config/create', admin, duplicate, expected=1004009001)
        assert sql('SELECT COUNT(*) FROM member_sign_in_config WHERE day=27 AND deleted=b\'0\';') == '1'
        updated = dict(rule, id=identifier, day=28, point=9)
        call('PUT', '/member/sign-in/config/update', admin, updated)
        assert sql(f'SELECT day,point,experience FROM member_sign_in_config WHERE id={int(identifier)};') == '28\t9\t3'
        call('DELETE', f'/member/sign-in/config/delete?id={identifier}', admin)
        assert sql(f'SELECT deleted+0 FROM member_sign_in_config WHERE id={int(identifier)};') == '1'
        cases['sign_in_rule_lifecycle'] = True
        return {'created_updated_deleted': True, 'duplicate_day_rejected': True}

    def exercise_sign_in_rewards(self, first_token, second_token, cases):
        call = self.call
        user_id = 990951
        sql('UPDATE member_user SET experience=0,level_id=NULL WHERE id=990951;')
        sql('INSERT INTO member_level (id,name,level,experience,discount_percent,status,tenant_id) '
            "VALUES (991001,'P2 sign-in level',1,3,90,0,1);")
        sql("INSERT INTO member_sign_in_config (id,day,point,experience,status,tenant_id) "
            'VALUES (991001,1,4,3,0,1);')
        call('GET', '/member/sign-in/record/get-summary', first_token, prefix='/app-api')

        def snapshot():
            return {
                'sign_in': sql(f'SELECT id,user_id,day,point,experience FROM member_sign_in_record WHERE user_id={user_id} ORDER BY id;'),
                'point': sql(f'SELECT id,biz_type,biz_id,point,total_point FROM member_point_record WHERE user_id={user_id} ORDER BY id;'),
                'experience': sql(f'SELECT id,biz_type,biz_id,experience,total_experience FROM member_experience_record WHERE user_id={user_id} ORDER BY id;'),
                'level': sql(f'SELECT id,level_id,experience,user_experience FROM member_level_record WHERE user_id={user_id} ORDER BY id;'),
                'member': sql(f'SELECT point,experience,level_id FROM member_user WHERE id={user_id};'),
            }

        injected = []
        for trigger_name, table, case_name in (
            ('sign_in_experience_failure', 'member_experience_record', 'sign_in_experience_rollback'),
            ('sign_in_level_failure', 'member_level_record', 'sign_in_level_rollback'),
        ):
            before = snapshot()
            sql(f"CREATE TRIGGER {trigger_name} BEFORE INSERT ON {table} FOR EACH ROW "
                "SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='P2_SIGN_IN_INJECTED';")
            try:
                call('POST', '/member/sign-in/record/create', first_token, prefix='/app-api', expected=500)
            finally:
                sql(f'DROP TRIGGER {trigger_name};')
            after = snapshot()
            assert after == before, (case_name, before, after)
            injected.append(case_name)

        signed = call('POST', '/member/sign-in/record/create', first_token, prefix='/app-api')
        assert signed['day'] == 1 and signed['point'] == 4 and signed['experience'] == 3, signed
        after_success = snapshot()
        assert after_success['member'] == '19\t3\t991001', after_success
        assert sql('SELECT COUNT(*) FROM member_sign_in_record WHERE user_id=990951;') == '1'
        assert sql("SELECT COUNT(*) FROM member_point_record WHERE user_id=990951 AND biz_type=1 AND point=4;") == '1'
        assert sql("SELECT COUNT(*) FROM member_experience_record WHERE user_id=990951 AND biz_type=4 AND experience=3;") == '1'
        assert sql('SELECT COUNT(*) FROM member_level_record WHERE user_id=990951 AND level_id=991001;') == '1'
        cases['sign_in_rewards_lifecycle'] = True

        before_repeat = snapshot()
        call('POST', '/member/sign-in/record/create', first_token, prefix='/app-api', expected=1004010000)
        assert snapshot() == before_repeat
        foreign_page = call('GET', '/member/sign-in/record/page?pageNo=1&pageSize=10',
                            second_token, prefix='/app-api')
        assert foreign_page['total'] == 0 and foreign_page['list'] == [], foreign_page
        assert call('GET', '/member/sign-in/record/get-summary', second_token,
                    prefix='/app-api')['totalDay'] == 0
        cases['sign_in_rewards_lifecycle'] = True
        return {'automatic_level_up': True, 'repeat_sign_in_rejected_without_writes': True,
                'other_member_sign_in_not_visible': True, 'injected_rollbacks': injected,
                'member_state_after_sign_in': after_success['member']}

    def exercise_concurrent_sign_in(self, token, cases):
        user_id = 990955
        sql('INSERT INTO member_sign_in_record (id,user_id,day,point,experience,create_time,tenant_id) '
            'VALUES (991055,990955,1,0,0,DATE_SUB(NOW(), INTERVAL 2 DAY),1);')
        barrier = Barrier(2)

        def request_sign_in():
            barrier.wait(timeout=10)
            try:
                data = self.call('POST', '/member/sign-in/record/create', token, prefix='/app-api')
                return {'outcome': 'success', 'data': data}
            except AssertionError as error:
                if '1004010000' in str(error):
                    return {'outcome': 'duplicate'}
                raise

        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda _: request_sign_in(), range(2)))
        outcomes = sorted(response['outcome'] for response in responses)
        diagnostics = {
            'responses': responses,
            'sign_in_rows': sql('SELECT id,day,point,experience FROM member_sign_in_record WHERE user_id=990955 ORDER BY id;'),
            'point_rows': sql('SELECT id,biz_id,biz_type,point,total_point FROM member_point_record WHERE user_id=990955 ORDER BY id;'),
            'experience_rows': sql('SELECT id,biz_id,biz_type,experience,total_experience FROM member_experience_record WHERE user_id=990955 ORDER BY id;'),
            'member_state': sql('SELECT point,experience,level_id FROM member_user WHERE id=990955;'),
        }
        assert outcomes == ['duplicate', 'success'], diagnostics
        assert sql('SELECT COUNT(*) FROM member_sign_in_record WHERE user_id=990955 AND id > 991055;') == '1', diagnostics
        assert sql("SELECT COUNT(*) FROM member_point_record WHERE user_id=990955 AND biz_type=1 AND point=4;") == '1', diagnostics
        assert sql("SELECT COUNT(*) FROM member_experience_record WHERE user_id=990955 AND biz_type=4 AND experience=3;") == '1', diagnostics
        assert sql('SELECT point,experience FROM member_user WHERE id=990955;') == '4\t3', diagnostics
        cases['sign_in_concurrency'] = True
        return {'concurrent_requests': 2, 'outcomes': outcomes,
                'same_day_sign_in_records': 1, 'single_reward_set': True,
                'one_success_one_duplicate': True,
                'success_response': next(response['data'] for response in responses
                                         if response['outcome'] == 'success')}


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
    if any((OUT / name).exists() for name in ('member-runtime.json', 'member-browser.json')):
        raise FileExistsError(f'refusing to overwrite prior evidence in {OUT}; set YH_MEMBER_PROBE_OUTPUT_DIR')
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
            log_path = Path(temp) / 'application-diagnostic.log'
            log_path.touch(mode=0o600, exist_ok=True)
            log_path.write_text('')
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
            deadline = time.monotonic() + 60
            changesets = None
            while changesets is None:
                try:
                    changesets = Probe.installed_changesets(sql('SELECT COUNT(*) FROM DATABASECHANGELOG;'))
                except AssertionError:
                    assert time.monotonic() < deadline, 'Liquibase changeset count mismatch'
                    changesets = None
                    time.sleep(1)
            password_snapshot = sql("SELECT SHA2(GROUP_CONCAT(CONCAT(id,':',password) ORDER BY id SEPARATOR '|'),256) "
                                    'FROM system_users;')
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
            member_one = {'mobile': '19900000951', 'email': '', 'password': 'P2Member51',
                          'point': 10, 'status': 0, 'register_ip': '127.0.0.1',
                          'nickname': 'P2 app member 1', 'tenant_id': 1}
            member_two = {'mobile': '19900000955', 'email': '', 'password': 'P2Member55',
                          'status': 0, 'register_ip': '127.0.0.1', 'nickname': 'P2 app member 2', 'tenant_id': 1}
            admin_member = {'mobile': '19900000952', 'email': '', 'password': secrets.token_urlsafe(16),
                            'status': 0, 'register_ip': '127.0.0.1', 'nickname': 'P2 admin tenant member', 'tenant_id': 2}
            for identifier, member in ((990951, member_one), (990955, member_two), (990952, admin_member)):
                member['password'] = subprocess.run(
                    ['htpasswd', '-bnBC', '4', member['mobile'], member['password']],
                    capture_output=True, text=True, check=True).stdout.strip().split(':', 1)[1]
                sql('INSERT INTO member_user (id,mobile,email,password,status,register_ip,nickname,tenant_id) VALUES '
                    f"({identifier},{sql_literal(member['mobile'])},'',{sql_literal(member['password'])},0,'127.0.0.1',"
                    f"{sql_literal(member['nickname'])},{member['tenant_id']});")
            probe = Probe()
            admin = probe.call('POST', '/system/auth/login', body={'username': admin_name, 'password': admin_password})['accessToken']
            guest = probe.call('POST', '/system/auth/login', body={'username': guest_name, 'password': guest_password})['accessToken']
            first_app = probe.call('POST', '/member/auth/login', body={'mobile': member_one['mobile'],
                                       'password': 'P2Member51'}, prefix='/app-api')['accessToken']
            second_app = probe.call('POST', '/member/auth/login', body={'mobile': member_two['mobile'],
                                        'password': 'P2Member55'}, prefix='/app-api')['accessToken']
            result['cases']['member_app_login'] = True
            result['cases']['member_app_address'] = probe.exercise_app(first_app, second_app, result['cases'])
            result['cases']['member_runtime'] = probe.exercise(admin, guest, None, result['cases'])
            result['cases']['sign_in_rule_lifecycle'] = probe.exercise_sign_in_rules(admin, result['cases'])
            result['cases']['sign_in_rewards_lifecycle'] = probe.exercise_sign_in_rewards(
                first_app, second_app, result['cases'])
            result['cases']['sign_in_concurrency'] = probe.exercise_concurrent_sign_in(
                second_app, result['cases'])
            assert password_snapshot == sql("SELECT SHA2(GROUP_CONCAT(CONCAT(id,':',password) ORDER BY id SEPARATOR '|'),256) "
                                            'FROM system_users WHERE id < 990953;')
            result['cases']['seed_passwords_unchanged'] = True
            result['changesets'] = changesets
            result['completed'] = all(result['cases'].get(key) for key in REQUIRED_CASES if key != 'cleanup')
            ui_log = (Path(temp) / 'ui.log').open('w')
            ui = subprocess.Popen(['python3', '-c',
                'import http.server,runpy; http.server.ThreadingHTTPServer.request_queue_size=128; '
                'runpy.run_path("scripts/ui_server.py",run_name="__main__")',
                '--root', str(UI_DIST), '--host', '127.0.0.1', '--port', str(UI_PORT),
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
                assert user_point == '17' and point_record == '-2:17:2', (user_point, point_record)
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
    if not result.get('completed'):
        raise SystemExit('member verification did not complete; see runtime evidence')


if __name__ == '__main__':
    main()
