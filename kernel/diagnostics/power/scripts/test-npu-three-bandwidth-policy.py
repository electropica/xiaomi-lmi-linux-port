import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('triple',Path(__file__).with_name('lmi-npu-three-bandwidth-policy.py'))
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class Node:
    def __init__(self,maximum):
        self.expected_max=maximum
        self.values={'governor':'performance','min_freq':'0','max_freq':maximum,'cur_freq':maximum,'available_governors':'powersave performance'}
        self.writes=[];self.fail_apply=False;self.fail_restore=False
    def read(self,n):return self.values[n]
    def write_governor(self,v):
        self.writes.append(v)
        if v=='performance' and self.fail_restore:raise OSError('restore failed')
        self.values['governor']=v;self.values['cur_freq']='0' if v=='powersave' else self.expected_max
        if v=='powersave' and self.fail_apply:raise OSError('partial transition')

def nodes():return {n:Node(m) for n,m in p.BASELINES.items()}

class Tests(unittest.TestCase):
    def test_three_apply_restore(self):
        ns=nodes();saved=[];original=p.apply_all(ns,saved.append)
        self.assertEqual(len(saved),1)
        self.assertTrue(all(x.read('cur_freq')=='0' for x in ns.values()))
        p.restore_all(ns,original)
        self.assertTrue(all(x.read('cur_freq')==x.expected_max for x in ns.values()))
    def test_partial_failure_restores_every_client(self):
        for index in range(3):
            ns=nodes();list(ns.values())[index].fail_apply=True
            with self.assertRaises(OSError):p.apply_all(ns,lambda _:None)
            self.assertTrue(all(x.read('governor')=='performance' for x in ns.values()))
    def test_no_write_if_any_preflight_mismatch(self):
        ns=nodes();list(ns.values())[2].values['min_freq']='1'
        with self.assertRaises(RuntimeError):p.apply_all(ns,lambda _:None)
        self.assertTrue(all(not x.writes for x in ns.values()))
    def test_no_write_if_save_failed(self):
        ns=nodes()
        def fail(_):raise OSError('disk full')
        with self.assertRaises(OSError):p.apply_all(ns,fail)
        self.assertTrue(all(not x.writes for x in ns.values()))
    def test_restore_attempts_remaining_clients_after_failure(self):
        ns=nodes();original=p.apply_all(ns,lambda _:None);list(ns.values())[0].fail_restore=True
        with self.assertRaises(RuntimeError):p.restore_all(ns,original)
        self.assertTrue(all(x.read('governor')=='performance' for x in list(ns.values())[1:]))
    def test_external_governor_preserved_others_restored(self):
        ns=nodes();original=p.apply_all(ns,lambda _:None);first=list(ns.values())[0];first.values['governor']='userspace'
        with self.assertRaises(RuntimeError):p.restore_all(ns,original)
        self.assertEqual(first.read('governor'),'userspace')
        self.assertTrue(all(x.read('governor')=='performance' for x in list(ns.values())[1:]))
    def test_idempotent_restore(self):
        ns=nodes();original=p.apply_all(ns,lambda _:None);p.restore_all(ns,original);p.restore_all(ns,original)
        self.assertTrue(all(x.writes==['powersave','performance'] for x in ns.values()))

if __name__=='__main__':unittest.main()
