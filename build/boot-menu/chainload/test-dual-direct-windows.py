#!/usr/bin/env python3
"""User-run qualified dual-menu RAM launch. Never flash; never interrupt trace."""
from pathlib import Path
import argparse,datetime,hashlib,json,struct,subprocess,time
SHA='35a8bf8d508d1b7b98f435d871ee50665a6321eaef496feea132bf0815f129c8'
def run(args,timeout=15):
 p=subprocess.run([str(a) for a in args],capture_output=True,text=True,timeout=timeout)
 if p.returncode:raise RuntimeError(p.stdout+'\n'+p.stderr)
 return p.stdout+p.stderr
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');a=ap.parse_args()
 downloads=Path.home()/'Downloads';image=downloads/'lmi-menu-dual-direct-20261022.img'
 raw=image.read_bytes();assert len(raw)==47237120 and hashlib.sha256(raw).hexdigest()==SHA
 assert raw[:8]==b'ANDROID!' and struct.unpack_from('<II',raw,40)==(1,536871337)
 adb=downloads/'platform-tools/adb.exe';fb=downloads/'platform-tools/fastboot.exe'
 assert adb.is_file() and fb.is_file()
 print('DUAL_DIRECT_IMAGE_VERIFIED. Temporary RAM boot only.',flush=True)
 if not a.execute:print('PLAN_ONLY: no phone contact.');return
 rows=[s.split() for s in run([adb,'devices']).splitlines() if s.strip() and not s.startswith('List of devices')]
 assert len(rows)==1 and rows[0][1]=='device'
 ad=[adb,'-s',rows[0][0]]
 assert run(ad+['shell','getprop','sys.boot_completed']).strip()=='1'
 assert run(ad+['shell','getprop','ro.product.device']).strip() in ('lmi','lmipro')
 assert 'uid=0(' in run(ad+['shell','id'])
 # Refuse to destroy the trace or invalidate the ongoing battery interval.
 run(ad+['shell','test','!','-e','/sys/kernel/tracing/instances/lmi_power_compare'])
 digest=run(ad+['shell','dd if=/dev/block/bootdevice/by-name/boot bs=4096 count=13343 2>/dev/null | sha256sum'])
 assert digest.split()[0]=='a89ae4d9529dcef55d3969eb6b5a75c2617d9ef0e2e1f568c5f619eb1adf5c50'
 print('ANDROID_TRACE_AND_INSTALLED_MOBIAN_GUARDS_PASSED',flush=True)
 run(ad+['reboot','bootloader'])
 deadline=time.monotonic()+60;rows=[]
 while time.monotonic()<deadline:
  rows=[s.split() for s in run([fb,'devices']).splitlines() if s.strip()]
  if rows:break
  time.sleep(2)
 assert len(rows)==1 and rows[0][1]=='fastboot'
 base=[fb,'-s',rows[0][0]]
 assert any(s.strip()=='product: lmi' for s in run(base+['getvar','product']).splitlines())
 size=run(base+['getvar','partition-size:mobian'])
 assert int(size.split('partition-size:mobian:')[1].split()[0],16)==17179869184
 output=run(base+['boot',image],timeout=90)
 p=Path.home()/'Documents/ChatGPT/Mobian/work/menu-dual-direct-20261022-launch-private.json'
 p.write_text(json.dumps({'host_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':SHA,'no_flash':True,'output':output},indent=2))
 print(output);print('First test: let the 15-second default attempt direct Mobian. Do not flash.')
if __name__=='__main__':main()
