#!/usr/bin/env python3
"""Operator-run Windows temporary boot of the pinned compact LineageOS menu. No flash."""
import argparse,hashlib,json,struct,subprocess,time,datetime
from pathlib import Path
SHA='9d7dd4823860f7ad73c82542669620b2cee1ca466789958175be63bb77e85411'

def run(args,timeout=15,check=True):
 p=subprocess.run([str(x) for x in args],capture_output=True,text=True,timeout=timeout)
 if check and p.returncode:raise RuntimeError(p.stdout+'\n'+p.stderr)
 return p

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');a=ap.parse_args()
 downloads=Path.home()/'Downloads';image=downloads/'boot.img'
 fb=downloads/'platform-tools/fastboot.exe'
 raw=image.read_bytes()
 assert len(raw)==134217728 and hashlib.sha256(raw).hexdigest()==SHA,'Probe image mismatch'
 assert raw[:8]==b'ANDROID!' and struct.unpack_from('<I',raw,40)[0]==2
 assert fb.is_file()
 print('PINNED_STOCK_LINEAGE_BOOT_VERIFIED. Direct control; temporary boot only.',flush=True)
 if not a.execute:
  print('PLAN_ONLY: no phone contact, reboot or boot requested.');return
 ssh=['wsl.exe','-d','Ubuntu','-u','linuxagent','--','ssh','-i','/home/linuxagent/.ssh/id_ed25519_codex_lmi','-o','BatchMode=yes','-o','ConnectTimeout=5','root@172.16.42.1']
 # Qualify the installed boot that the smoke menu will cold-reboot into.
 guard=r'''
from pathlib import Path
import subprocess,json,hashlib
assert Path('/etc/lmi/dualboot-installation-validated').read_text().strip()=='lmi-dualboot-v1'
loops=json.loads(subprocess.check_output(['losetup','--list','--json','--output','NAME,BACK-FILE'],text=True))['loopdevices']
assert next(x['back-file'] for x in loops if x['name']=='/dev/loop0')=='/dev/sda35'
with open('/dev/disk/by-partlabel/boot','rb') as f:boot=f.read(54652928)
assert hashlib.sha256(boot).hexdigest()=='a89ae4d9529dcef55d3969eb6b5a75c2617d9ef0e2e1f568c5f619eb1adf5c50'
print('LMI_REBOOT_GUARDS_PASSED',flush=True)
subprocess.run(['systemctl','--reboot-argument=bootloader','reboot'],check=True)
'''
 p=subprocess.run(ssh+['python3','-'],input=guard,text=True,capture_output=True,timeout=25)
 if p.returncode not in (0,255) or 'LMI_REBOOT_GUARDS_PASSED' not in p.stdout:
  raise RuntimeError('Mobian SSH preflight did not complete; reboot not confirmed. Check the USB cable.\n'+p.stdout+p.stderr)
 deadline=time.monotonic()+60
 rows=[]
 while time.monotonic()<deadline:
  rows=[x.split() for x in run([fb,'devices']).stdout.splitlines() if x.strip()]
  if rows:break
  time.sleep(2)
 assert len(rows)==1 and rows[0][1]=='fastboot','Exactly one Fastboot device required'
 base=[fb,'-s',rows[0][0]]
 product=run(base+['getvar','product'])
 assert any(x.strip()=='product: lmi' for x in (product.stdout+product.stderr).splitlines())
 size=run(base+['getvar','partition-size:mobian'])
 assert int((size.stdout+size.stderr).split('partition-size:mobian:')[1].split()[0],16)==17179869184
 userdata=run(base+['getvar','partition-size:userdata'])
 assert int((userdata.stdout+userdata.stderr).split('partition-size:userdata:')[1].split()[0],16)==225677672448
 p=run(base+['boot',image],timeout=180)
 record=Path.home()/'Documents/ChatGPT/Mobian/work/lineage-direct-control-20261021-private.json'
 record.write_text(json.dumps({'host_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':SHA,'phase':'stock_lineage_direct_control_requested','no_flash':True,'stdout':p.stdout,'stderr':p.stderr},indent=2))
 print(p.stdout+p.stderr)
 print('Direct LineageOS control requested. Observe whether Android reaches its lock/home screen or recovery. No flash performed.')
if __name__=='__main__':main()
