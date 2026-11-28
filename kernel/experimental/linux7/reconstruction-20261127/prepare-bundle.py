#!/usr/bin/env python3
"""Replace only the kernel in the retained working bundle; no device access."""
import hashlib, importlib.util, json, sys, zlib
from pathlib import Path

if len(sys.argv)!=4:
    raise SystemExit('Usage: prepare-bundle.py WORKING_BUNDLE NEW_IMAGE NEW_OUTPUT_DIRECTORY')
base,image,out=map(Path,sys.argv[1:])
tool=Path(__file__).resolve().parent.parent/'tools/build-linux7-bundle.py'
sha=lambda data: hashlib.sha256(data).hexdigest()
if out.exists(): raise SystemExit('Output exists; refusing overwrite')
raw=base.read_bytes()
if sha(raw)!='1092a81cef951676f6e01bf8f2d17e32d0881bfebc763df51738c0f9145d1f0e':
    raise SystemExit('Working bundle hash mismatch')
spec=importlib.util.spec_from_file_location('bundle',tool)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
_,_,entries=mod.parse(raw)
old={e['name']:mod.decode(e['name'],raw[e['offset']:e['offset']+e['length']]) for e in entries}
if sha(old['linux7/dtb'])!='1fc0316ac94754dac33c34cb8ab57b76ba4dc10b074f64c93d03f99beeec310b':
    raise SystemExit('Working DTB mismatch')
new=dict(old); new['linux7/kernel']=image.read_bytes()
changed=sorted(k for k in new if old[k]!=new[k])
if changed!=['linux7/kernel']: raise SystemExit('Expected exactly one changed component')
data=mod.build(entries,new)
if len(data)>=64*1024*1024: raise SystemExit('Bundle too large')
_,_,rows=mod.parse(data)
for row in rows:
    part=data[row['offset']:row['offset']+row['length']]
    if zlib.crc32(part)&0xffffffff!=row['crc32'] or mod.decode(row['name'],part)!=new[row['name']]:
        raise SystemExit('Bundle component verification failed: '+row['name'])
out.mkdir()
(out/'lmi-outer-linux7.bin').write_bytes(data)
(out/'BUNDLE_RESULT.json').write_text(json.dumps(mod.manifest(data,entries,new,changed,hardware_tested=False),indent=2)+'\n')
print('KERNEL_ONLY_BUNDLE_READY_NOT_FLASHABLE',sha(data))
