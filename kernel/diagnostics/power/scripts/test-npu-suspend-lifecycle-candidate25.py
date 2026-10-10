import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import tempfile,sys,os

spec=importlib.util.spec_from_file_location('triple',Path(__file__).with_name('lmi-npu-suspend-lifecycle-candidate25.py'))
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

class LifecycleTests(unittest.TestCase):
    def setup_patches(self,mode,ns,path):
        for i,io in enumerate(ns.values()):io.path=Path('/sys/devices/fake'+str(i))
        from contextlib import ExitStack
        stack=ExitStack()
        stack.enter_context(patch.object(sys,'argv',['hook',mode,'--state',str(path),'--managed-unit','lmi-npu-bandwidth-trial25.service']))
        stack.enter_context(patch.object(p.os,'geteuid',return_value=0,create=True))
        stack.enter_context(patch.object(p,'state_path',return_value=path))
        stack.enter_context(patch.object(p,'SysfsNode',side_effect=lambda n:ns[n]))
        stack.enter_context(patch.object(p,'verify_managed_unit'))
        return stack
    def test_pre_outside_suspend_refuses_before_write(self):
        ns=nodes()
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            path=Path(tmp)/'state.json'
            with self.setup_patches('pre',ns,path),patch.object(p.subprocess,'check_output',return_value='inactive\n'):
                with self.assertRaises(RuntimeError):p.main()
            self.assertTrue(all(not io.writes for io in ns.values()));self.assertFalse(path.exists())
    def test_pre_busy_npu_refuses_before_write(self):
        ns=nodes()
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            path=Path(tmp)/'state.json'
            with self.setup_patches('pre',ns,path),patch.object(p.subprocess,'check_output',return_value='activating\n'),patch.object(p,'quiet_npu',side_effect=RuntimeError('busy')):
                with self.assertRaises(RuntimeError):p.main()
            self.assertTrue(all(not io.writes for io in ns.values()));self.assertFalse(path.exists())
    def test_post_without_pre_has_no_write(self):
        ns=nodes()
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            path=Path(tmp)/'state.json'
            with self.setup_patches('post',ns,path):p.main()
            self.assertTrue(all(not io.writes for io in ns.values()))
    def test_post_restores_original_policy(self):
        ns=nodes();original=p.apply_all(ns,lambda _:None)
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            path=Path(tmp)/'state.json';path.write_text('{}')
            with self.setup_patches('post',ns,path),patch.object(p,'saved_originals',return_value=original):p.main()
            self.assertTrue(all(io.read('governor')=='performance' for io in ns.values()))
    def test_post_preserves_external_governor_restores_others(self):
        ns=nodes();original=p.apply_all(ns,lambda _:None);list(ns.values())[0].values['governor']='userspace'
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            path=Path(tmp)/'state.json';path.write_text('{}')
            with self.setup_patches('post',ns,path),patch.object(p,'saved_originals',return_value=original):
                with self.assertRaises(RuntimeError):p.main()
            self.assertEqual(list(ns.values())[0].read('governor'),'userspace')
            self.assertTrue(all(io.read('governor')=='performance' for io in list(ns.values())[1:]))

class HookCleanupTests(unittest.TestCase):
    def test_missing_hook_is_noop(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            path=Path(tmp)/'hook'
            with patch.object(p,'HOOK',path):p.disarm_hook()
            self.assertFalse(path.exists())
    def test_only_exact_owned_hook_is_removed(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            path=Path(tmp)/'hook';path.write_bytes(p.HOOK_BYTES)
            real_stat=Path.stat
            def root_owned(q,*a,**k):
                st=real_stat(q,*a,**k);values=list(st);values[4]=0;return os.stat_result(values)
            with patch.object(p,'HOOK',path),patch.object(Path,'stat',root_owned):p.disarm_hook()
            self.assertFalse(path.exists())
    def test_changed_hook_is_preserved(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            path=Path(tmp)/'hook';path.write_bytes(b'external change')
            with patch.object(p,'HOOK',path):
                with self.assertRaises(RuntimeError):p.disarm_hook()
            self.assertEqual(path.read_bytes(),b'external change')

if __name__=='__main__':unittest.main()
