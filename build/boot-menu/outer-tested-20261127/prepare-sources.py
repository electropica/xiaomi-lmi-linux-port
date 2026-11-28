#!/usr/bin/env python3
"""Clone only pinned tracked sources locally; borrow object stores read-only."""
from pathlib import Path
import json,os,subprocess,sys

BASE=Path(os.environ['LMI_MENU_BASE_SOURCE'])
ROOT=Path(os.environ['LMI_MENU_BUILD_ROOT'])
DEST=ROOT/'source/edk2-msm'
RECIPE=Path(__file__).resolve().parent

def git(root,*args):
    return subprocess.check_output(['git','-c','safe.directory='+str(root),'-C',str(root),*args],text=True).strip()

def main():
    lock=json.loads((RECIPE/'sources.lock.json').read_text());expected=lock['revision'];records=[]
    if ROOT.is_symlink() or DEST.is_symlink():raise ValueError('source symlink')
    if DEST.exists():
        manifest=json.loads((ROOT/'SOURCE_RESULT.json').read_text())
        for record in manifest['repositories']:
            target=Path(record['target'])
            if not target.is_relative_to(DEST):raise ValueError('source outside expected root')
            if git(target,'rev-parse','HEAD')!=record['commit'] or git(target,'diff','--name-only','--ignore-submodules=dirty'):
                raise ValueError('existing candidate source changed')
        print('ISOLATED_SOURCES_REUSED_AFTER_REVISION_CHECK');return
    DEST.parent.mkdir(parents=True,exist_ok=True)
    def clone(source,target,commit):
        if not source.resolve().is_relative_to(BASE.resolve()):raise ValueError('unexpected source tree')
        if git(source,'rev-parse',commit+'^{commit}')!=commit:raise ValueError('missing pinned source object')
        subprocess.run(['git','-c','safe.directory='+str(source),'clone','--shared','--no-checkout',str(source),str(target)],check=True)
        subprocess.run(['git','-C',str(target),'checkout','--detach',commit],check=True)
        records.append({'source':str(source),'target':str(target),'commit':commit})
        data=subprocess.check_output(['git','-C',str(target),'ls-tree','-rz',commit])
        for entry in data.split(b'\0'):
            if not entry:continue
            info,path=entry.split(b'\t',1);mode,kind,sha=info.decode().split()
            if mode!='160000':continue
            rel=Path(path.decode())
            if rel.is_absolute() or '..' in rel.parts:raise ValueError('invalid submodule path')
            clone(source/rel,target/rel,sha)
    clone(BASE,DEST,expected)
    for rel,commit in lock['submodules'].items():
        if git(DEST/rel,'rev-parse','HEAD')!=commit:raise ValueError('submodule revision mismatch')
    (DEST/'.lmi-source-ready').touch()
    (ROOT/'SOURCE_RESULT.json').write_text(json.dumps({'repositories':records,'network_fetch':False},indent=2)+'\n')
    print('ISOLATED_PINNED_LOCAL_SOURCES_PREPARED',len(records))

if __name__=='__main__':main()
