"""Operator-run restoration of the pinned Lineage default boot only."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('flash_helpers',Path(__file__).with_name('flash-mobian.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');ap.add_argument('--temporary',action='store_true');ap.add_argument('--allow-android-default',action='store_true');a=ap.parse_args()
    if a.execute and not a.temporary and not a.allow_android_default:raise RuntimeError('Mobian is now the requested default; Android-default installation is disabled')
    downloads=Path.home()/'Downloads';fb=downloads/'platform-tools/fastboot.exe';boot=downloads/'boot.img'
    with boot.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    if digest!='9d7dd4823860f7ad73c82542669620b2cee1ca466789958175be63bb77e85411':raise RuntimeError('Wrong Lineage boot image')
    rows=[l.split() for l in m.run([fb,'devices']).splitlines() if l.strip()]
    if len(rows)!=1 or rows[0][1]!='fastboot':raise RuntimeError('Exactly one Fastboot device required')
    base=[fb,'-s',rows[0][0]]
    if m.value(m.run(base+['getvar','product']),'product')!='lmi':raise RuntimeError('Wrong product')
    expected={'mobian':17179869184,'userdata':225677672448,'boot':134217728}
    for name,size in expected.items():
        if int(m.value(m.run(base+['getvar','partition-size:'+name]),'partition-size:'+name),16)!=size:raise RuntimeError('Unexpected size: '+name)
    print('ANDROID_BOOT_GUARDS_PASSED: pinned image, lmi, all three partition sizes',flush=True)
    if not a.execute:print('READ_ONLY: no flash or reboot requested');return
    if a.temporary:
        record=Path.home()/'Documents/ChatGPT/Mobian/work/dualboot-android-temporary-result-private.json'
        if record.exists():raise RuntimeError('Prior temporary test exists; review before retry')
        with record.open('x',encoding='utf-8') as f:json.dump({'stage':'temporary-android-boot-starting','sha256':digest},f)
        result=m.run(base+['boot',boot],timeout=180)
        record.write_text(json.dumps({'stage':'temporary-android-boot-requested','sha256':digest,'boot_output':result},indent=2))
        print(result,flush=True);print('TEMPORARY_ANDROID_BOOT_REQUESTED. No partition flashed; default boot unchanged.',flush=True)
        return
    record=Path.home()/'Documents/ChatGPT/Mobian/work/dualboot-android-boot-result-private.json'
    if record.exists():raise RuntimeError('Prior operation record exists; review before retry')
    outcome={'stage':'boot-flash-starting','partition':'boot','sha256':digest}
    with record.open('x',encoding='utf-8') as f:json.dump(outcome,f)
    result=m.run(base+['flash','boot',boot],timeout=180)
    outcome.update(stage='boot-flashed',flash_output=result);record.write_text(json.dumps(outcome,indent=2));print(result,flush=True)
    result=m.run(base+['reboot'],timeout=30)
    outcome.update(stage='android-reboot-requested',reboot_output=result);record.write_text(json.dumps(outcome,indent=2));print(result,flush=True)
    print('ANDROID_FIRST_BOOT_REQUESTED. Mobian partition retained; Android startup remains to verify.',flush=True)
if __name__=='__main__':main()
