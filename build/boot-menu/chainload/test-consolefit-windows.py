#!/usr/bin/env python3
"""User-run console-fit/provenance RAM test from Mobian. Never flash."""
from pathlib import Path
import argparse,datetime,hashlib,json,struct,subprocess,time
SHA='548b06b3aabc4948dfafb1e9fefb7e9bef5e6e7b8a621d61b3aeb8fa69e6cdaa'
def run(args,timeout=15):
 p=subprocess.run([str(x) for x in args],capture_output=True,text=True,timeout=timeout)
 if p.returncode:raise RuntimeError(p.stdout+'\n'+p.stderr)
 return p.stdout+p.stderr
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');a=ap.parse_args()
 d=Path.home()/'Downloads';image=d/'lmi-menu-dual-consolefit-20261022.img';fb=d/'platform-tools/fastboot.exe'
 raw=image.read_bytes()
 assert len(raw)==47237120 and hashlib.sha256(raw).hexdigest()==SHA
 assert raw[:8]==b'ANDROID!' and struct.unpack_from('<II',raw,40)==(1,536871337)
 assert fb.is_file()
 print('CONSOLEFIT_MARKER2_IMAGE_VERIFIED. Temporary RAM boot only.',flush=True)
 if not a.execute:print('PLAN_ONLY: no phone contact.');return
 ssh=['wsl.exe','-d','Ubuntu','-u','linuxagent','--','ssh','-i','/home/linuxagent/.ssh/id_ed25519_codex_lmi','-o','BatchMode=yes','-o','ConnectTimeout=5','root@172.16.42.1']
 guard=r'''
from pathlib import Path
import subprocess,json,hashlib
assert Path('/etc/lmi/dualboot-installation-validated').read_text().strip()=='lmi-dualboot-v1'
assert Path('/sys/block/loop0/loop/backing_file').read_text().strip()=='/dev/sda35'
assert subprocess.check_output(['findmnt','-n','-o','SOURCE','/'],text=True).strip()=='/dev/loop0p2'
for root in ['/sys/kernel/tracing','/sys/kernel/debug/tracing']:
 assert not (Path(root)/'instances/lmi_power_compare').exists(),'Power trace remains active'
with open('/dev/disk/by-partlabel/boot','rb') as f:raw=f.read(54652928)
assert hashlib.sha256(raw).hexdigest()=='a89ae4d9529dcef55d3969eb6b5a75c2617d9ef0e2e1f568c5f619eb1adf5c50'
print('LMI_REBOOT_GUARDS_PASSED',flush=True)
subprocess.run(['systemctl','--reboot-argument=bootloader','reboot'],check=True)
'''
 p=subprocess.run(ssh+['python3','-'],input=guard,text=True,capture_output=True,timeout=25)
 if p.returncode not in (0,255) or 'LMI_REBOOT_GUARDS_PASSED' not in p.stdout:
  raise RuntimeError('Mobian SSH checks did not complete. No reboot confirmed.\n'+p.stdout+p.stderr)
 deadline=time.monotonic()+60;rows=[]
 while time.monotonic()<deadline:
  rows=[x.split() for x in run([fb,'devices']).splitlines() if x.strip()]
  if rows:break
  time.sleep(2)
 assert len(rows)==1 and rows[0][1]=='fastboot'
 base=[fb,'-s',rows[0][0]]
 assert any(s.strip()=='product: lmi' for s in run(base+['getvar','product']).splitlines())
 size=run(base+['getvar','partition-size:mobian'])
 assert int(size.split('partition-size:mobian:')[1].split()[0],16)==17179869184
 output=run(base+['boot',image],timeout=90)
 p=Path.home()/'Documents/ChatGPT/Mobian/work/menu-consolefit-20261022-launch-private.json'
 p.write_text(json.dumps({'host_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':SHA,'no_flash':True,'output':output},indent=2))
 print(output);print('First trial: let Mobian start after 15 seconds; check loading text and report startup.')
if __name__=='__main__':main()
