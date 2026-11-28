#!/usr/bin/env python3
"""Preflight or apply the tested VFR syntax-predicate candidate."""
import argparse, hashlib, os, tempfile
from pathlib import Path

EXPECTED='35a8681fd3f0fe84b66da10a3b517f42d196a9ba3c6a6c7a196d88b4e0ab5ea8'
REL=Path('Common/edk2/BaseTools/Source/C/VfrCompile/VfrSyntax.g')
ap=argparse.ArgumentParser(); ap.add_argument('source_root',type=Path); ap.add_argument('--apply',action='store_true'); args=ap.parse_args()
p=args.source_root.resolve(strict=True)/REL
if p.is_symlink() or not p.is_file(): raise SystemExit('Unexpected VFR source')
raw=p.read_bytes()
if hashlib.sha256(raw).hexdigest()!=EXPECTED: raise SystemExit('Unexpected VFR grammar; no modification')
names=['vfrStatementInconsistentIf','vfrStatementNoSubmitIf','vfrStatementWarningIf',
       'vfrStatementDisableIfQuest','vfrStatementSuppressIfQuest','vfrStatementGrayOutIfQuest']
s=raw.decode('utf-8')
for name in names:
    start=s.index('\n'+name+' :'); end=s.index('\n  ;',start)+4; section=s[start:end]
    if section.count('E:EndIf {";"}')!=1: raise SystemExit('Unexpected VFR rule: '+name)
    section=section.replace('E:EndIf {";"}','E:EndIf { (";")? ";" }',1)
    s=s[:start]+section+s[end:]
if not args.apply:
    print('VFR_PREDICATES_PREFLIGHT_PASS; NO CHANGES'); raise SystemExit(0)
fd,tmp=tempfile.mkstemp(prefix='.lmi-vfr-',dir=p.parent)
try:
    with os.fdopen(fd,'wb') as f:
        f.write(s.encode('utf-8')); f.flush(); os.fsync(f.fileno())
    os.chmod(tmp,p.stat().st_mode & 0o777); os.replace(tmp,p)
finally:
    if os.path.exists(tmp): os.unlink(tmp)
print('VFR_PREDICATES_APPLIED')
