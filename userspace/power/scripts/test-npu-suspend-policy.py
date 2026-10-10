#!/usr/bin/env python3
"""Failure/recovery tests, without sysfs writes or a real suspension."""
import importlib.machinery
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import os
import json
import types

loader = importlib.machinery.SourceFileLoader('policy', str(Path(__file__).with_name('lmi-npu-suspend')))
spec = importlib.util.spec_from_loader(loader.name, loader)
p = importlib.util.module_from_spec(spec)
loader.exec_module(p)


class FakeNode:
    def __init__(self, maximum='10437'):
        self.maximum = maximum
        self.path = Path('/sys/devices/fake')
        self.values = dict(governor='performance', min_freq='0', max_freq=maximum,
                           cur_freq=maximum, available_governors='performance powersave')
        self.fail = None
        self.writes = []

    def read(self, name):
        return self.values[name]

    def write(self, governor):
        self.writes.append(governor)
        if governor == self.fail:
            raise OSError('injected write failure')
        self.values.update(governor=governor, cur_freq='0' if governor == 'powersave' else self.maximum)


class PolicyTest(unittest.TestCase):
    def setUp(self):
        self.nodes = {n: FakeNode(v) for n, v in p.BASELINES.items()}
        self.originals = {n: p.inspect(io) for n, io in self.nodes.items()}

    def test_save_precedes_writes(self):
        def save(values):
            self.assertTrue(all(not n.writes for n in self.nodes.values()))
            self.assertEqual(values, self.originals)
        p.apply_all(self.nodes, save)
        self.assertTrue(all(n.read('cur_freq') == '0' for n in self.nodes.values()))

    def test_save_failure_no_write(self):
        with self.assertRaises(OSError):
            p.apply_all(self.nodes, lambda _: (_ for _ in ()).throw(OSError()))
        self.assertTrue(all(not n.writes for n in self.nodes.values()))

    def test_preflight_all_before_save(self):
        list(self.nodes.values())[-1].values['max_freq'] = '9'
        with self.assertRaises(RuntimeError):
            p.apply_all(self.nodes, lambda _: self.fail('saved invalid baseline'))
        self.assertTrue(all(not n.writes for n in self.nodes.values()))

    def test_partial_write_restores_all(self):
        list(self.nodes.values())[1].fail = 'powersave'
        with self.assertRaises(OSError):
            p.apply_all(self.nodes, lambda _: None)
        self.assertTrue(all(n.read('governor') == 'performance' for n in self.nodes.values()))

    def test_restore_failure_attempts_remaining(self):
        p.apply_all(self.nodes, lambda _: None)
        list(self.nodes.values())[0].fail = 'performance'
        with self.assertRaises(RuntimeError):
            p.restore_all(self.nodes, self.originals)
        self.assertTrue(all(n.read('governor') == 'performance' for n in list(self.nodes.values())[1:]))

    def test_external_governor_preserved(self):
        p.apply_all(self.nodes, lambda _: None)
        first = list(self.nodes.values())[0]
        first.values['governor'] = 'userspace'
        with self.assertRaises(RuntimeError):
            p.restore_all(self.nodes, self.originals)
        self.assertEqual(first.read('governor'), 'userspace')

    def test_external_limits_preserved(self):
        p.apply_all(self.nodes, lambda _: None)
        first = list(self.nodes.values())[0]
        first.values['min_freq'] = '1'
        with self.assertRaises(RuntimeError):
            p.restore_all(self.nodes, self.originals)
        self.assertEqual(first.read('min_freq'), '1')

    def test_repeated_cycles(self):
        for _ in range(3):
            p.apply_all(self.nodes, lambda _: None)
            p.restore_all(self.nodes, self.originals)
        self.assertTrue(all(n.read('cur_freq') == n.maximum for n in self.nodes.values()))

    def test_symlink_state_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'real'
            target.write_text('{}')
            link = Path(directory) / 'state'
            link.symlink_to(target)
            with self.assertRaises(RuntimeError):
                p.load_state(link, self.nodes)

    def test_state_identity_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state'
            path.write_text(json.dumps({'version': 100}))
            with patch.object(p, 'private_regular'):
                with self.assertRaises(RuntimeError):
                    p.load_state(path, self.nodes)

    def test_failed_recovery_retains_record(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state'
            path.write_text('{}')
            p.apply_all(self.nodes, lambda _: None)
            list(self.nodes.values())[0].fail = 'performance'
            with patch.object(p, 'load_state', return_value=self.originals):
                with self.assertRaises(RuntimeError):
                    p.recover(path, self.nodes)
            self.assertTrue(path.exists())

    def test_successful_recovery_removes_record(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state'
            path.write_text('{}')
            p.apply_all(self.nodes, lambda _: None)
            with patch.object(p, 'load_state', return_value=self.originals):
                p.recover(path, self.nodes)
            self.assertFalse(path.exists())

    def test_unknown_kernel_skipped(self):
        with patch.object(p.OPT_IN.__class__, 'exists', return_value=True), patch.object(p, 'private_regular'), \
             patch.object(p.os, 'uname', return_value=types.SimpleNamespace(release='other', version=p.VERSION)), \
             patch.object(p.subprocess, 'check_output', side_effect=AssertionError('must not contact systemd')):
            self.assertFalse(p.pre_allowed())

    def test_busy_npu_skipped(self):
        with patch.object(p.OPT_IN.__class__, 'exists', return_value=True), patch.object(p, 'private_regular'), \
             patch.object(p.os, 'uname', return_value=types.SimpleNamespace(release=p.RELEASE, version=p.VERSION)), \
             patch.object(p.subprocess, 'check_output', return_value='activating\n'), \
             patch.object(p.subprocess, 'run', return_value=types.SimpleNamespace(returncode=0)):
            self.assertFalse(p.pre_allowed())

    def test_manual_apply_rejected(self):
        with patch.object(p.OPT_IN.__class__, 'exists', return_value=True), patch.object(p, 'private_regular'), \
             patch.object(p.os, 'uname', return_value=types.SimpleNamespace(release=p.RELEASE, version=p.VERSION)), \
             patch.object(p.subprocess, 'check_output', return_value='inactive\n'):
            with self.assertRaises(RuntimeError):
                p.pre_allowed()


if __name__ == '__main__':
    unittest.main()
