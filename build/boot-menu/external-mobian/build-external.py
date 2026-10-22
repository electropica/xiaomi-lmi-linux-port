#!/usr/bin/env python3
"""Prepare an isolated 32-MiB menu recipe; firmware build requires --build."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,subprocess

REPO=Path('/home/linuxagent/xiaomi-lmi-linux-port')
DEST_ROOT=Path('/home/linuxagent/lmi-outer-mobian-recipes')
BASELINE='78e8328dfb09bbbce109bd0a4accf8561d44af94'

def files():
    here=Path(__file__).resolve().parent;parent=here.parent
    spec=importlib.util.spec_from_file_location('baseline',parent/'reset-guard/build-baseline.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    result=m.recipe_files()
    inner=result['build-inside.sh'].decode()
    needle='cd /source\n';assert inner.count(needle)==1
    inner=inner.replace(needle,needle+'python3 -B /recipe/external-mobian/apply-outer.py /source/edk2-msm /recipe /output --restore\n',1)
    needle='cd /source/edk2-msm\n';assert inner.count(needle)==1
    inner=inner.replace(needle,'python3 -B /recipe/external-mobian/make-outer.py /recipe /inputs /output\npython3 -B /recipe/external-mobian/apply-outer.py /source/edk2-msm /recipe /output\n'+needle)
    result['build-inside.sh']=inner.encode()
    for name in ['outer-range.h','outer-pei.h','outer-loader.h','lmi-kernel-extent.h',
                 'make-outer.py','apply-outer.py','pack-outer.py']:
        result['external-mobian/'+name]=(here/name).read_bytes()
    return result

def prepare():
    contents=files()
    fingerprint=hashlib.sha256(b''.join(name.encode()+b'\0'+hashlib.sha256(raw).digest() for name,raw in sorted(contents.items()))).hexdigest()[:16]
    DEST=DEST_ROOT/fingerprint
    if DEST_ROOT.is_symlink() or DEST.is_symlink():raise RuntimeError('Refusing a symlink recipe')
    for name,raw in contents.items():
        path=DEST/name
        if path.exists():
            if path.is_symlink() or path.read_bytes()!=raw:raise RuntimeError('Existing snapshot differs: '+name)
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as stream:stream.write(raw)
    actual={str(p.relative_to(DEST)) for p in DEST.rglob('*') if p.is_file()}
    assert not actual-(set(contents)|{'external-recipe-manifest.json'}),'Unexpected snapshot files'
    manifest={'baseline':BASELINE,'files':{name:hashlib.sha256(raw).hexdigest() for name,raw in sorted(contents.items())},'firmware_built':False}
    (DEST/'external-recipe-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    for name in ['build.sh','build-inside.sh']:subprocess.run(['bash','-n',str(DEST/name)],check=True)
    print('ISOLATED_OUTER_MOBIAN_RECIPE_PREPARED_NO_FIRMWARE_BUILD',flush=True)
    return DEST

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--build',action='store_true');a=ap.parse_args()
    destination=prepare()
    if a.build:
        subprocess.run(['bash',str(destination/'build.sh'),'--build','--with-lineage'],check=True)
        subprocess.run(['python3','-B',str(destination/'external-mobian/pack-outer.py'),
                        '/home/linuxagent/lmi-boot-menu-build/output'],check=True)
