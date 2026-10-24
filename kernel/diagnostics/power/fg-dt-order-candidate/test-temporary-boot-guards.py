from pathlib import Path
import importlib.util
s=importlib.util.spec_from_file_location('t',Path(__file__).resolve().parent/'temporary-boot-windows.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def check(case):
 calls=[]
 def fake(args,timeout=20):
  a=[str(x) for x in args];calls.append(a)
  if a[-1]=='devices':return {'none':'','multiple':'ONE fastboot\nTWO fastboot\n'}.get(case,'ONE fastboot\n')
  if a[-2:]==['getvar','product']:return 'product: '+('other' if case=='product' else 'lmi')+'\n'
  if a[-1]=='partition-size:boot':return 'partition-size:boot: '+('0x10' if case=='boot-size' else '0x8000000')+'\n'
  if a[-1]=='partition-size:mobian':return 'partition-size:mobian: '+('0x10' if case=='root-size' else '0x400000000')+'\n'
  if 'boot' in a:return 'Booting OKAY\n'
  raise AssertionError(a)
 try:m.launch(Path('image.img'),Path('fastboot.exe'),fake)
 except RuntimeError:assert case!='valid'
 else:assert case=='valid'
 boots=[x for x in calls if 'boot' in x]
 assert len(boots)==(1 if case=='valid' else 0)
 assert not any('flash' in x or 'reboot' in x for x in calls)
for c in ['none','multiple','product','boot-size','root-size','valid']:check(c)
print('PASS: five bad-device/product/size cases reject before boot; valid case requests exactly one RAM boot; no flash/reboot command')
