"""Mocked Windows transport checks. No device commands or real boot files."""
import contextlib,importlib.util,io,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
s=importlib.util.spec_from_file_location('android_boot',Path(__file__).with_name('flash-android-boot.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Checks(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='android-boot-test-',dir=Path(__file__).resolve().parent)
  self.root=Path(self.tmp.name);(self.root/'Downloads').mkdir();(self.root/'Downloads/boot.img').write_bytes(b'fixture')
  (self.root/'Documents/ChatGPT/Mobian/work').mkdir(parents=True)
  def cleanup():
   assert self.root.resolve().parent==Path(__file__).resolve().parent
   self.tmp.cleanup()
  self.addCleanup(cleanup);self.calls=[];self.sizes={'mobian':17179869184,'userdata':225677672448,'boot':134217728}
 def backend(self,args,**kw):
  args=[str(x) for x in args]
  self.calls.append([str(x) for x in args])
  if args[1:]==['devices']:return 'fixture fastboot\n'
  if args[-2:]==['getvar','product']:return 'product: lmi\n'
  if args[-1].startswith('partition-size:'):
   key=args[-1];return key+': '+hex(self.sizes[key.split(':')[1]])+'\n'
  return 'OKAY\n'
 def invoke(self,*flags):
  digest=SimpleNamespace(hexdigest=lambda:'9d7dd4823860f7ad73c82542669620b2cee1ca466789958175be63bb77e85411')
  with patch.object(sys,'argv',['test',*flags]),patch.object(Path,'home',return_value=self.root),patch.object(m.hashlib,'file_digest',return_value=digest),patch.object(m.m,'run',side_effect=self.backend),contextlib.redirect_stdout(io.StringIO()):m.main()
 def test_android_default_is_locked(self):
  with self.assertRaisesRegex(RuntimeError,'requested default'):self.invoke('--execute')
  self.assertEqual(self.calls,[])
 def test_temporary_mode_never_flashes(self):
  self.invoke('--execute','--temporary')
  self.assertEqual(sum('boot' in c and 'getvar' not in c for c in self.calls),1)
  self.assertFalse(any(x in c for c in self.calls for x in ('flash','erase','format','reboot')))
  record=self.root/'Documents/ChatGPT/Mobian/work/dualboot-android-temporary-result-private.json'
  self.assertEqual(json.loads(record.read_text())['stage'],'temporary-android-boot-requested')
 def test_preflight_never_boots(self):
  self.invoke('--temporary')
  self.assertFalse(any('boot' in c and 'getvar' not in c for c in self.calls))
 def test_wrong_size_stops_before_boot(self):
  self.sizes['mobian']=1024
  with self.assertRaisesRegex(RuntimeError,'Unexpected size'):self.invoke('--execute','--temporary')
  self.assertFalse(any('boot' in c and 'getvar' not in c for c in self.calls))
 def test_prior_record_stops_retry(self):
  (self.root/'Documents/ChatGPT/Mobian/work/dualboot-android-temporary-result-private.json').write_text('{}')
  with self.assertRaisesRegex(RuntimeError,'Prior temporary test'):self.invoke('--execute','--temporary')
  self.assertFalse(any('boot' in c and 'getvar' not in c for c in self.calls))
if __name__=='__main__':unittest.main()
