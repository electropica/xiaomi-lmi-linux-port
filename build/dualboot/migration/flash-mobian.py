"""Operator-run Windows flash to dedicated mobian, then a temporary test boot."""
import argparse,hashlib,json,re,struct,subprocess
from pathlib import Path
def run(args,timeout=15):
    p=subprocess.run([str(x) for x in args],capture_output=True,text=True,timeout=timeout)
    out=p.stdout+'\n'+p.stderr
    if p.returncode:raise RuntimeError(out)
    return out
def value(text,key):
    matches=re.findall(r'^'+re.escape(key)+r':\s*(\S+)\s*$',text,re.M)
    if len(matches)!=1:raise ValueError('Missing or ambiguous Fastboot variable '+key)
    return matches[0]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');a=ap.parse_args()
    downloads=Path.home()/'Downloads';fb=downloads/'platform-tools/fastboot.exe'
    sparse=downloads/'mobian-lmi-dualboot-20261021.img.android-sparse.img'
    boot=downloads/'mobian-lmi-dualboot-boot-20261021.img'
    for p,want in [(sparse,'f803fae6954c4d5e13cfa77815640a895d3d051d8a56db7813c75edce2bd3f8e'),(boot,'75bb65facbd4146d4a1e668039ef52433ef90c2b6bdb07f2c59980caf3191374')]:
        with p.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
        if digest!=want:raise RuntimeError('Image hash mismatch: '+p.name)
    with sparse.open('rb') as f:h=f.read(28)
    magic,major,minor,hs,cs,bs,blocks,chunks,checksum=struct.unpack('<I4H4I',h)
    if magic!=0xed26ff3a or major!=1 or hs!=28 or bs!=4096 or blocks*bs>16*1024**3:raise RuntimeError('Unexpected sparse image')
    rows=[l.split() for l in run([fb,'devices']).splitlines() if l.strip()]
    if len(rows)!=1 or rows[0][1]!='fastboot':raise RuntimeError('Exactly one Fastboot device required')
    serial=rows[0][0];base=[fb,'-s',serial]
    if value(run(base+['getvar','product']),'product')!='lmi':raise RuntimeError('Wrong product')
    size=int(value(run(base+['getvar','partition-size:mobian']),'partition-size:mobian'),16)
    if size!=17179869184:raise RuntimeError('Dedicated mobian size is not 16 GiB')
    print('GUARDS_PASSED: lmi, dedicated mobian 16GiB, pinned sparse and boot hashes',flush=True)
    if not a.execute:print('READ_ONLY: no flash or boot requested');return
    record=Path.home()/'Documents/ChatGPT/Mobian/work/dualboot-flash-result-private.json'
    if record.exists():raise RuntimeError('Prior flash record exists; review it before retry')
    with record.open('x',encoding='utf-8') as f:json.dump({'stage':'flash-starting','partition':'mobian'},f)
    result=run(base+['flash','mobian',sparse],timeout=600)
    outcome={'stage':'flash-completed','partition':'mobian','flash_output':result}
    record.write_text(json.dumps(outcome,indent=2))
    print(result,flush=True)
    result=run(base+['boot',boot],timeout=120)
    outcome.update(stage='temporary-boot-requested',boot_output=result)
    record.write_text(json.dumps(outcome,indent=2))
    print(result,flush=True);print('TEMPORARY_MOBIAN_BOOT_REQUESTED. Target root verification remains required.',flush=True)
if __name__=='__main__':main()
