"""Host-only failure-injection tests; no sysfs, unit or handset operations."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
import json

spec = importlib.util.spec_from_file_location('policy', Path(__file__).with_name('lmi-npu-bandwidth-policy.py'))
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


class FakeNode:
    def __init__(self):
        self.values = {'governor': 'performance', 'min_freq': '0', 'max_freq': '10437', 'cur_freq': '10437', 'available_governors': 'powersave performance'}
        self.writes = []
        self.failure = None

    def read(self, name):
        return self.values[name]

    def write_governor(self, value):
        self.writes.append(value)
        self.values['governor'] = value
        self.values['cur_freq'] = '0' if value == 'powersave' else '10437'
        if self.failure and value == 'powersave':
            kind = self.failure
            self.failure = None
            if kind == 'partial_write':
                raise OSError('Simulated write failure after partial transition')
            if kind == 'target':
                self.values['cur_freq'] = '762'


class PolicyTests(unittest.TestCase):
    def test_apply_restore_one_client(self):
        io = FakeNode(); saved = []
        original = policy.apply(io, saved.append)
        self.assertEqual(saved, [original])
        self.assertEqual(io.read('cur_freq'), '0')
        policy.restore(io, saved[0])
        self.assertEqual(io.writes, ['powersave', 'performance'])
        self.assertEqual(io.read('cur_freq'), '10437')

    def test_original_mismatch_means_no_write(self):
        for key, value in [('governor', 'userspace'), ('min_freq', '762'), ('max_freq', '6881'), ('cur_freq', '762'), ('available_governors', 'performance')]:
            with self.subTest(key=key):
                io = FakeNode();io.values[key] = value;saved = []
                with self.assertRaises(RuntimeError):policy.apply(io, saved.append)
                self.assertEqual(io.writes, []);self.assertEqual(saved, [])

    def test_save_failure_means_no_write(self):
        io = FakeNode()
        def fail(_):raise OSError('Disk unavailable')
        with self.assertRaises(OSError):policy.apply(io, fail)
        self.assertEqual(io.writes, [])

    def test_partial_write_failure_restores_original(self):
        io = FakeNode();io.failure = 'partial_write';saved = []
        with self.assertRaises(OSError):policy.apply(io, saved.append)
        self.assertEqual(io.writes, ['powersave', 'performance'])
        self.assertEqual(io.read('cur_freq'), '10437')

    def test_nonzero_target_restores_and_rejects_trial(self):
        io = FakeNode();io.failure = 'target'
        with self.assertRaises(RuntimeError):policy.apply(io, lambda _:None)
        self.assertEqual(io.writes, ['powersave', 'performance'])

    def test_external_governor_is_preserved(self):
        io = FakeNode();original = policy.apply(io, lambda _:None)
        io.values['governor'] = 'userspace'
        with self.assertRaises(RuntimeError):policy.restore(io, original)
        self.assertEqual(io.writes, ['powersave'])

    def test_external_limits_are_preserved(self):
        io = FakeNode();original = policy.apply(io, lambda _:None)
        io.values['min_freq'] = '762'
        with self.assertRaises(RuntimeError):policy.restore(io, original)
        self.assertEqual(io.read('min_freq'), '762')
        self.assertEqual(io.writes, ['powersave'])

    def test_restore_is_idempotent(self):
        io = FakeNode();original = policy.apply(io, lambda _:None)
        policy.restore(io, original);policy.restore(io, original)
        self.assertEqual(io.writes, ['powersave', 'performance'])

    def test_unreviewed_saved_state_means_no_write(self):
        io = FakeNode();original = policy.inspect(io);original['governor'] = 'userspace'
        with self.assertRaises(RuntimeError):policy.restore(io, original)
        self.assertEqual(io.writes, [])

    def test_typed_hook_and_runtime_guard(self):
        expected = ['/usr/bin/python3', '/var/tmp/helper.py', 'restore', '--state', '/var/tmp/lmi-npu-bandwidth-trial21.json']
        hook = ['/usr/bin/python3', expected, False, 0, 0, 0, 0, 0, 0, 0]
        policy.verify_managed_settings('active', 900000000, [hook], expected)
        invalid = []
        invalid.append(('inactive', 900000000, [hook]))
        invalid.append(('active', 18446744073709551615, [hook]))
        invalid.append(('active', 0, [hook]))
        invalid.append(('active', True, [hook]))
        invalid.append(('active', 900000000, []))
        invalid.append(('active', 900000000, [hook, hook]))
        invalid.append(('active', 900000000, [['/bin/echo', expected, False, 0, 0, 0, 0, 0, 0, 0]]))
        invalid.append(('active', 900000000, [['/usr/bin/python3', [' '.join(expected)], False, 0, 0, 0, 0, 0, 0, 0]]))
        invalid.append(('active', 900000000, [['/usr/bin/python3', expected, True, 0, 0, 0, 0, 0, 0, 0]]))
        for active, runtime, hooks in invalid:
            with self.subTest(active=active, runtime=runtime, hooks=hooks):
                with self.assertRaises(RuntimeError):policy.verify_managed_settings(active, runtime, hooks, expected)

    def test_missing_state_never_reports_success(self):
        p = Mock();p.exists.return_value = False
        with self.assertRaises(RuntimeError):policy.load_original(p, '/sys/devices/test')

    def test_corrupt_foreign_or_symlink_state_is_rejected(self):
        p = Mock();p.exists.return_value = True;p.is_file.return_value = True;p.is_symlink.return_value = False;p.stat.return_value.st_uid = 0
        p.read_text.return_value = '{broken'
        with self.assertRaises(json.JSONDecodeError):policy.load_original(p, '/sys/devices/test')
        p.read_text.return_value = json.dumps({'version':1,'device':'/sys/devices/foreign','original':{}})
        with self.assertRaises(RuntimeError):policy.load_original(p, '/sys/devices/test')
        p.is_symlink.return_value = True
        with self.assertRaises(RuntimeError):policy.load_original(p, '/sys/devices/test')
        p.is_symlink.return_value = False;p.stat.return_value.st_uid = 1000
        with self.assertRaises(RuntimeError):policy.load_original(p, '/sys/devices/test')

    def test_failed_restoration_is_not_success(self):
        io = FakeNode();original = policy.apply(io, lambda _:None)
        io.write_governor = Mock(side_effect=OSError('Restore rejected'))
        with self.assertRaises(OSError):policy.restore(io, original)
        self.assertEqual(io.read('governor'), 'powersave')

    def test_busctl_json_preserves_scalar_property_types(self):
        with patch.object(policy.subprocess, 'check_output', return_value='{"type":"s","data":"active"}'):
            self.assertEqual(policy.dbus_value([], 's'), 'active')
        with patch.object(policy.subprocess, 'check_output', return_value='{"type":"t","data":900000000}'):
            self.assertEqual(policy.dbus_value([], 't'), 900000000)
        with patch.object(policy.subprocess, 'check_output', return_value='{"type":"s","data":"wrong"}'):
            with self.assertRaises(RuntimeError):policy.dbus_value([], 't')


if __name__ == '__main__':
    unittest.main()
