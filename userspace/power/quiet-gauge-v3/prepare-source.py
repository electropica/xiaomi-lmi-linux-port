#!/usr/bin/env python3
"""Verify cumulative v3 patch in scratch space; --apply explicitly updates source."""
from pathlib import Path
import argparse,hashlib,json,os,stat,subprocess,tempfile

def sha(data):
    return hashlib.sha256(data).hexdigest()

def prepare(component,root,apply=False):
    here=Path(__file__).resolve().parent
    record=json.loads((here/'identity.json').read_text())[component]
    root=Path(root).resolve(strict=True)
    target=root/record['target']
    for p in (target,*target.parents):
        if p==root:break
        if p.is_symlink():raise ValueError('Source target and its parents must not be symlinks')
    target.resolve(strict=True).relative_to(root)
    original=target.read_bytes()
    if sha(original)==record['after_lf_sha256']:
        return {'component':component,'status':'already matches v3','changed':False}
    normalized=original.replace(b'\r\n',b'\n')
    if sha(normalized)!=record['before_lf_sha256']:
        raise ValueError('Source hash does not match the pinned Debian baseline; no file changed')
    patch=(here/record['patch']).read_bytes()
    if sha(patch)!=record['patch_sha256']:raise ValueError('Patch hash mismatch')
    with tempfile.TemporaryDirectory(prefix='lmi-quiet-source-') as directory:
        scratch=Path(directory);f=scratch/record['target'];f.parent.mkdir(parents=True)
        f.write_bytes(normalized)
        result=subprocess.run(['patch','--batch','--fuzz=0','-p1'],input=patch,cwd=scratch,capture_output=True,check=False)
        if result.returncode:raise ValueError('Exact patch failed: '+result.stderr.decode(errors='replace'))
        after=f.read_bytes()
        if sha(after)!=record['after_lf_sha256']:raise ValueError('Patched source hash mismatch')
    if apply:
        if target.read_bytes()!=original:raise ValueError('Source changed during verification')
        original_stat=target.stat();mode=stat.S_IMODE(original_stat.st_mode)
        fd,name=tempfile.mkstemp(prefix='.lmi-quiet-',dir=target.parent)
        try:
            with os.fdopen(fd,'wb') as stream:stream.write(after)
            os.chmod(name,mode)
            created=os.stat(name)
            if (created.st_uid,created.st_gid)!=(original_stat.st_uid,original_stat.st_gid):
                os.chown(name,original_stat.st_uid,original_stat.st_gid)
            os.replace(name,target)
        finally:
            if os.path.exists(name):os.unlink(name)
    return {'component':component,'status':'applied' if apply else 'verified without modification',
            'changed':apply,'result_sha256':sha(after)}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('component',choices=['phosh','gsd']);p.add_argument('source_root',type=Path)
    p.add_argument('--apply',action='store_true',help='Explicitly update the verified source file')
    args=p.parse_args()
    try:print(json.dumps(prepare(args.component,args.source_root,args.apply),indent=2))
    except (ValueError,OSError) as e:p.exit(1,str(e)+'\n')
