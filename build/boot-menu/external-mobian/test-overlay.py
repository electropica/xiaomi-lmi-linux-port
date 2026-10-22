#!/usr/bin/env python3
"""Apply/restore only a small fixture; verify tamper refusal before restoration."""
from pathlib import Path
import importlib.util,json,shutil,subprocess,tempfile
here=Path(__file__).resolve().parent;recipe=here.parent
s=importlib.util.spec_from_file_location('outer',here/'apply-outer.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
root=Path('/home/linuxagent/lmi-boot-menu-build');real=root/'source/edk2-msm'
edits=m.patchset(real,recipe,root/'output')
with tempfile.TemporaryDirectory(prefix='lmi-outer-overlay-') as tmp:
    p=Path(tmp);src=p/'source';out=p/'output';out.mkdir()
    shutil.copyfile(root/'output/outer-lock.h',out/'outer-lock.h')
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
