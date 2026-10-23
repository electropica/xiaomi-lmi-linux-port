#!/usr/bin/env python3
"""Apply/restore only a small fixture; verify tamper refusal before restoration."""
from pathlib import Path
import hashlib,importlib.util,json,shutil,subprocess,tempfile
here=Path(__file__).resolve().parent;recipe=here.parent
s=importlib.util.spec_from_file_location('outer',here/'apply-outer.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
root=Path('/home/linuxagent/lmi-boot-menu-build');real=root/'source/edk2-msm'
with tempfile.TemporaryDirectory(prefix='lmi-outer-overlay-') as tmp:
    p=Path(tmp);src=p/'source';out=p/'output';out.mkdir()
    shutil.copyfile(root/'output/outer-lock.h',out/'outer-lock.h')
    manifest=root/'output/outer-source-manifest.json'
    if manifest.exists():
        previous=json.loads(manifest.read_text())
        for name,info in previous.items():
            assert hashlib.sha256((real/name).read_bytes()).hexdigest()==info['after'],name
            if info['before'] is not None:
                data=(root/'output/outer-source-before'/name).read_bytes()
                assert hashlib.sha256(data).hexdigest()==info['before'],name
                dest=src/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        edits=m.patchset(src,recipe,root/'output')
    else:
        edits=m.patchset(real,recipe,root/'output')
    originals={}
    for name,(old,_) in edits.items():
        if old is not None:
            dest=src/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(old);originals[name]=old
    cmd=['python3','-B',str(here/'apply-outer.py'),str(src),str(recipe),str(out)]
    subprocess.run(cmd,check=True)
    record=json.loads((out/'outer-source-manifest.json').read_text());assert len(record)==12
    subprocess.run(cmd+['--restore'],check=True)
    assert not (out/'outer-source-manifest.json').exists()
    assert {str(f.relative_to(src)):f.read_bytes() for f in src.rglob('*') if f.is_file()}==originals
    subprocess.run(cmd,check=True)
    victim=src/'GPLDrivers/Library/SimpleInit/src/main/uefimain.c'
    victim.write_bytes(victim.read_bytes()+b'\n/* unreviewed */\n')
    before={str(f.relative_to(src)):f.read_bytes() for f in src.rglob('*') if f.is_file()}
    result=subprocess.run(cmd+['--restore'],capture_output=True,text=True)
    assert result.returncode!=0
    assert {str(f.relative_to(src)):f.read_bytes() for f in src.rglob('*') if f.is_file()}==before
print('OUTER_12_SOURCE_APPLY_EXACT_RESTORE_AND_ATOMIC_TAMPER_REFUSAL_PASS')
