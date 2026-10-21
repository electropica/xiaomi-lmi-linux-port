#!/usr/bin/env python3
"""Windows PC selector. Default is a plan; --execute boots, never flashes."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path

def run(args,timeout=15,check=True):
    p=subprocess.run([str(x) for x in args],capture_output=True,text=True,timeout=timeout)
    if check and p.returncode:raise RuntimeError(p.stdout+'\n'+p.stderr)
    return p
def devices(tool,fastboot=False):
    p=run([tool,'devices'],check=False)
    rows=[]
    for line in p.stdout.splitlines():
        cells=line.split()
        if len(cells)>=2 and cells[1] in ('device','fastboot','unauthorized','offline'):rows.append(cells[:2])
    if any(state in ('unauthorized','offline') for _,state in rows):raise RuntimeError('ADB unavailable: authorization/offline state; no reboot attempted')
    return rows
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,required=True);ap.add_argument('--os',choices=('android','mobian'),required=True);ap.add_argument('--execute',action='store_true');a=ap.parse_args()
    c=json.loads(a.config.read_text());image=Path(c['images'][a.os]['path'])
    if hashlib.sha256(image.read_bytes()).hexdigest()!=c['images'][a.os]['sha256']:raise RuntimeError('Image hash mismatch')
    if not c.get('dualboot_installation_validated'):raise RuntimeError('Migration and both OS boots must first be validated; controller is locked')
    if not a.execute:
        print(json.dumps({'mode':'PLAN_ONLY','target':a.os,'image':str(image),'writes_boot_partition':False}));return
    fb=c['fastboot'];adb=c['adb'];rows=devices(fb,True)
    if not rows:
        android=devices(adb)
        if len(android)>1:raise RuntimeError('Multiple ADB devices')
        if android:
            if run([adb,'-s',android[0][0],'shell','getprop','ro.product.device']).stdout.strip()!='lmi':raise RuntimeError('Wrong Android device')
            run([adb,'-s',android[0][0],'reboot','bootloader'])
        else:
            ssh=['wsl.exe','-d','Ubuntu','-u','linuxagent','--','ssh','-i',c['wsl_ssh_key'],'-o','BatchMode=yes','-o','ConnectTimeout=5','root@172.16.42.1']
            # Root must be on the dedicated partition before autonomous switching.
            probe=run(ssh+['cat /etc/lmi/dualboot-installation-validated'],check=False)
            if probe.returncode or probe.stdout.strip()!='lmi-dualboot-v1':raise RuntimeError('No validated Mobian endpoint; no reboot attempted')
            p=run(ssh+['systemctl reboot bootloader'],check=False)
            if p.returncode not in (0,255):raise RuntimeError('Reboot request failed')
        deadline=time.monotonic()+90
        while time.monotonic()<deadline:
            rows=devices(fb,True)
            if rows:break
            time.sleep(2)
    if len(rows)!=1:raise RuntimeError('Exactly one Fastboot device required')
    serial=rows[0][0]
    product=run([fb,'-s',serial,'getvar','product'])
    if not any(l.strip()=='product: lmi' for l in (product.stdout+'\n'+product.stderr).splitlines()):raise RuntimeError('Fastboot product is not lmi')
    run([fb,'-s',serial,'boot',image],timeout=120)
    deadline=time.monotonic()+180
    while time.monotonic()<deadline:
        if a.os=='android':
            p=run([adb,'-s',serial,'shell','getprop','sys.boot_completed'],timeout=8,check=False)
            if p.returncode==0 and p.stdout.strip()=='1':print('ANDROID_BOOT_CONFIRMED');return
        else:
            p=run(['wsl.exe','-d','Ubuntu','-u','linuxagent','--','ssh','-i',c['wsl_ssh_key'],'-o','BatchMode=yes','-o','ConnectTimeout=3','root@172.16.42.1','cat /etc/lmi/dualboot-installation-validated'],timeout=8,check=False)
            if p.returncode==0 and p.stdout.strip()=='lmi-dualboot-v1':print('MOBIAN_BOOT_CONFIRMED');return
        time.sleep(3)
    raise RuntimeError('Boot not confirmed. No flash/retry loop performed.')
if __name__=='__main__':main()
