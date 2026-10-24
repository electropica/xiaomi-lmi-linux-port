#!/usr/bin/env python3
"""Operator-run pinned temporary RAM boot. Default plan has no phone contact."""
from pathlib import Path
import argparse,datetime,hashlib,json,re,struct,subprocess
SHA='7425c00bffefb677f52d76fa360c024a0c4b5d6e58312f33350b4eb8928cb9ff'
REFERENCE='be9841c76cbe34d0c72606c47877f99582aee224144744349a9e78d15cfd0a94'
SIZE=81051648

def pinned(path,digest):
 raw=path.read_bytes()
 if len(raw)!=SIZE or hashlib.sha256(raw).hexdigest()!=digest:raise RuntimeError('Image identity mismatch: '+path.name)
 if raw[:8]!=b'ANDROID!' or struct.unpack_from('<II',raw,40)!=(1,536871337) or struct.unpack_from('<I',raw,16)[0]!=55054349:raise RuntimeError('Unexpected boot header')
 return raw

def command(args,timeout=20):
 p=subprocess.run([str(x) for x in args],capture_output=True,text=True,timeout=timeout)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout+p.stderr

def fastboot_guard(fb,run=command):
 rows=[line.split() for line in run([fb,'devices']).splitlines() if line.strip()]
 if len(rows)!=1 or len(rows[0])!=2 or rows[0][1]!='fastboot':raise RuntimeError('Exactly one Fastboot device required; no boot requested')
 base=[fb,'-s',rows[0][0]]
 text=run(base+['getvar','product'])
 if not any(re.fullmatch(r'(?:\(bootloader\)\s*)?product:\s*lmi',line.strip()) for line in text.splitlines()):raise RuntimeError('Product lmi not confirmed')
 for name,expected in [('boot',134217728),('mobian',17179869184)]:
  text=run(base+['getvar','partition-size:'+name]);values=[]
  for line in text.splitlines():
   match=re.fullmatch(r'(?:\(bootloader\)\s*)?partition-size:'+name+r':\s*(0x[0-9a-fA-F]+|[0-9a-fA-F]+)',line.strip())
   if match:values.append(int(match.group(1),16))
  if values!=[expected]:raise RuntimeError('Unexpected '+name+' partition size')
 return base

def launch(image,fb,run=command):
 base=fastboot_guard(fb,run)
 return run(base+['boot',image],timeout=120)

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');ap.add_argument('--downloads',type=Path,default=Path.home()/'Downloads');ap.add_argument('--records',type=Path,default=Path(__file__).resolve().parent/'private-state/fg-dt-order');a=ap.parse_args()
 image=a.downloads/'lmi-fg-dt-order-test-20261024.img';fb=a.downloads/'platform-tools/fastboot.exe'
 pinned(image,SHA);pinned(a.downloads/'lmi-menu-outer-dual-extent-20261023.img',REFERENCE)
 if not fb.is_file():raise RuntimeError('Native Windows fastboot.exe missing')
 print('FG_DT_ORDER_IMAGE_AND_REFERENCE_VERIFIED. Temporary RAM boot only.',flush=True)
 if not a.execute:print('PLAN_ONLY: no phone contact, reboot or boot requested.');return
 output=launch(image,fb);a.records.mkdir(parents=True,exist_ok=True)
 stamp=datetime.datetime.now(datetime.timezone.utc)
 receipt={'utc':stamp.isoformat(),'sha256':SHA,'reference_sha256':REFERENCE,'phase':'temporary_boot_requested_not_validated','no_flash':True,'output':output}
 p=a.records/('launch-'+stamp.strftime('%Y%m%dT%H%M%S%fZ')+'-private.json')
 with p.open('x',encoding='utf-8') as f:f.write(json.dumps(receipt,indent=2)+'\n')
 print(output);print('Laisse le compte a rebours choisir Mobian. Garde le cable branche. Aucun test de decharge ne demarre automatiquement.')
 print('Receipt: '+str(p))
if __name__=='__main__':main()
