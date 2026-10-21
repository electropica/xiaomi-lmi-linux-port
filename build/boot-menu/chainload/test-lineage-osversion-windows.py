#!/usr/bin/env python3
"""Operator-run RAM test from the successfully booted stock Android. No flash."""
from pathlib import Path
import argparse,hashlib,struct,subprocess,time,json,datetime
SHA='71e226f1a8adaf5d0574d1311d686143694404f49ab62df5d343c8a36c3c5196'
def run(args,timeout=15):
    p=subprocess.run([str(x) for x in args],capture_output=True,text=True,timeout=timeout)
    if p.returncode:raise RuntimeError(p.stdout+'\n'+p.stderr)
    return p.stdout+p.stderr
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');a=ap.parse_args()
    downloads=Path.home()/'Downloads';image=downloads/'lmi-menu-lineage-osversion-20261021.img'
    adb=downloads/'platform-tools/adb.exe';fb=downloads/'platform-tools/fastboot.exe'
    raw=image.read_bytes();assert len(raw)==25993216 and hashlib.sha256(raw).hexdigest()==SHA
    assert raw[:8]==b'ANDROID!' and struct.unpack_from('<II',raw,40)==(1,536871337)
    assert adb.is_file() and fb.is_file()
    print('OS_VERSION_CONTROL_IMAGE_VERIFIED. Temporary RAM boot only.',flush=True)
    if not a.execute:print('PLAN_ONLY: no phone contact or reboot.');return
    rows=[x.split() for x in run([adb,'devices']).splitlines() if x.strip() and not x.startswith('List of devices')]
    assert len(rows)==1 and rows[0][1]=='device','Exactly one authorized Android device required'
    ad=[adb,'-s',rows[0][0]]
    assert run(ad+['shell','getprop','sys.boot_completed']).strip()=='1','Start from the successful Android boot'
    assert run(ad+['shell','getprop','ro.product.device']).strip()=='lmi'
    assert 'uid=0(' in run(ad+['shell','id']),'Root ADB must still be enabled for the read-only boot guard'
    digest=run(ad+['shell','dd if=/dev/block/bootdevice/by-name/boot bs=4096 count=13343 2>/dev/null | sha256sum'])
    assert digest.split()[0]=='a89ae4d9529dcef55d3969eb6b5a75c2617d9ef0e2e1f568c5f619eb1adf5c50','Persistent Mobian boot mismatch'
    print('ANDROID_AND_INSTALLED_MOBIAN_BOOT_GUARDS_PASSED',flush=True)
    run(ad+['reboot','bootloader'])
    deadline=time.monotonic()+60;rows=[]
    while time.monotonic()<deadline:
        rows=[x.split() for x in run([fb,'devices']).splitlines() if x.strip()]
        if rows:break
        time.sleep(2)
    assert len(rows)==1 and rows[0][1]=='fastboot'
    base=[fb,'-s',rows[0][0]]
    assert any(x.strip()=='product: lmi' for x in run(base+['getvar','product']).splitlines())
    size=run(base+['getvar','partition-size:mobian']);assert int(size.split('partition-size:mobian:')[1].split()[0],16)==17179869184
    result=run(base+['boot',image],timeout=60)
    record=Path.home()/'Documents/ChatGPT/Mobian/work/menu-lineage-osversion-boot-20261021-private.json'
    record.write_text(json.dumps({'host_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':SHA,'phase':'os_version_control_requested','no_flash':True,'output':result},indent=2))
    print(result);print('Select LineageOS then Boot using Volume/Power. No flash performed.')
if __name__=='__main__':main()
