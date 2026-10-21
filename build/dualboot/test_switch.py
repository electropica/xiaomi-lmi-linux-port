"""Controller qualification with mocked transports; no OS/device action."""
import contextlib,hashlib,importlib.util,io,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
s=importlib.util.spec_from_file_location('selector',Path(__file__).with_name('switch-os.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Checks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='selector-test-',dir=Path(__file__).resolve().parent)
        self.base=Path(self.tmp.name)
        def cleanup():
            assert self.base.resolve().parent==Path(__file__).resolve().parent
            self.tmp.cleanup()
        self.addCleanup(cleanup)
        self.image=self.base/'boot-fixture.bin';self.image.write_bytes(b'test image')
        self.config={'fastboot':'fastboot.exe','adb':'adb.exe','wsl_ssh_key':'/private/test-key',
          'dualboot_installation_validated':True,'images':{n:{'path':str(self.image),'sha256':hashlib.sha256(b'test image').hexdigest()} for n in ('android','mobian')}}
        self.path=self.base/'config.json'
    def invoke(self,*args,backend=None):
        self.path.write_text(json.dumps(self.config))
        with patch.object(sys,'argv',['switch-os.py','--config',str(self.path),'--os','android',*args]),patch.object(m,'run',side_effect=backend) as run,contextlib.redirect_stdout(io.StringIO()):
            m.main()
            return run.call_args_list
    def test_plan_never_contacts_device(self):
        self.assertEqual(self.invoke(),[])
    def test_installation_gate(self):
        self.config['dualboot_installation_validated']=False
        with self.assertRaisesRegex(RuntimeError,'controller is locked'):self.invoke('--execute')
    def test_hash_gate(self):
        self.image.write_bytes(b'changed')
        with self.assertRaisesRegex(RuntimeError,'hash mismatch'):self.invoke('--execute')
    def test_wrong_fastboot_product_never_boots(self):
        def backend(args,**kw):
            if args[1:]==['devices']:return subprocess.CompletedProcess(args,0,'one fastboot\n','')
            return subprocess.CompletedProcess(args,0,'','product: other\n')
        with self.assertRaisesRegex(RuntimeError,'not lmi'):self.invoke('--execute',backend=backend)
    def test_multiple_fastboot_devices(self):
        def backend(args,**kw):return subprocess.CompletedProcess(args,0,'one fastboot\ntwo fastboot\n','')
        with self.assertRaisesRegex(RuntimeError,'Exactly one'):self.invoke('--execute',backend=backend)
    def test_unauthorized_adb(self):
        def backend(args,**kw):return subprocess.CompletedProcess(args,0,'one unauthorized\n' if args[0]=='adb.exe' else '','')
        with self.assertRaisesRegex(RuntimeError,'authorization'):self.invoke('--execute',backend=backend)
    def test_success_only_temporary_boot(self):
        def backend(args,**kw):
            if args[1:]==['devices']:out='one fastboot\n'
            elif 'getvar' in args:out='product: lmi\n'
            elif 'boot' in args:out='OKAY\n'
            else:out='1\n'
            return subprocess.CompletedProcess(args,0,out,'')
        calls=self.invoke('--execute',backend=backend)
        commands=[list(c.args[0]) for c in calls]
        self.assertEqual(sum('boot' in c for c in commands),1)
        self.assertFalse(any(x in c for c in commands for x in ('flash','erase','format','set_active')))
if __name__=='__main__':unittest.main()
