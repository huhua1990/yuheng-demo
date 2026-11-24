import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'verification'))
SPEC = importlib.util.spec_from_file_location(
    'p2_member_pay_runner', ROOT / 'verification/p2_member_pay_runner.py')
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class MemberPayRunnerTests(unittest.TestCase):
    def test_shared_database_or_container_is_rejected_before_any_docker_call(self):
        with patch.object(runner, 'SCHEMA', 'yuheng_demo'), \
                patch.object(runner.support, 'run') as run:
            with self.assertRaises(ValueError):
                runner.validate_isolation()
            run.assert_not_called()
        with patch.object(runner, 'MYSQL', 'mysql8'), \
                patch.object(runner.support, 'run') as run:
            with self.assertRaises(ValueError):
                runner.validate_isolation()
            run.assert_not_called()

    def test_reader_permissions_allow_list_and_wallet_read_but_no_balance_write(self):
        self.assertEqual(set(runner.READER_PERMISSIONS),
                         {'member:user:query', 'pay:wallet:query'})

    def test_wallet_snapshot_uses_each_tables_actual_columns(self):
        statements = []
        def sql(statement):
            statements.append(statement)
            return 'snapshot'
        self.assertEqual(runner.wallet_snapshot(sql), ('snapshot', 'snapshot'))
        self.assertIn('user_id,user_type,balance,total_expense,total_recharge', statements[0])
        self.assertNotIn('wallet_id', statements[0])
        self.assertIn('wallet_id,biz_type,biz_id,price,balance', statements[1])


if __name__ == '__main__':
    unittest.main()
