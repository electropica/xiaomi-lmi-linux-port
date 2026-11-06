#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('guard', Path(__file__).with_name('lmi-usb-pc-guard.py'))
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class FakeChild:
    def __init__(self):
        self.running = True
        self.terminated = False

    def poll(self):
        return None if self.running else 0

    def terminate(self):
        self.terminated = True
        self.running = False

    def wait(self, timeout=None):
        return 0


class GuardTest(unittest.TestCase):
    def setUp(self):
        self.valid = {'online': '1', 'vbus': '4760000', 'udc': 'configured',
                      'carrier': '1', 'partner': True}

    def test_requires_all_independent_signals(self):
        self.assertTrue(guard.qualifies(self.valid))
        for key, bad in [('online', '0'), ('vbus', '0'), ('vbus', None),
                         ('vbus', 'invalid'), ('udc', 'not attached'),
                         ('carrier', '0'), ('partner', False)]:
            sample = dict(self.valid)
            sample[key] = bad
            with self.subTest(key=key, bad=bad):
                self.assertFalse(guard.qualifies(sample))

    def test_two_positives_then_immediate_release_on_any_negative(self):
        child = FakeChild()
        with mock.patch.object(guard.subprocess, 'Popen', return_value=child) as popen:
            g = guard.Guard()
            g.update(True)
            popen.assert_not_called()
            g.update(True)
            popen.assert_called_once()
            self.assertIs(g.child, child)
            g.update(False)
            self.assertTrue(child.terminated)
            self.assertIsNone(g.child)
            self.assertEqual(g.positives, 0)

    def test_inhibitor_exit_is_retried_and_shutdown_cleans_up(self):
        first, second = FakeChild(), FakeChild()
        with mock.patch.object(guard.subprocess, 'Popen', side_effect=[first, second]):
            g = guard.Guard()
            g.update(True)
            g.update(True)
            first.running = False
            g.update(True)
            self.assertIs(g.child, second)
            g.release()
            self.assertTrue(second.terminated)


if __name__ == '__main__':
    unittest.main()
