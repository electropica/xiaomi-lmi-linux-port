#!/usr/bin/env python3
"""Apply the reviewed intermediate-ELF segment layout to a disposable EDK tree."""
import argparse
import hashlib
import os
from pathlib import Path
import tempfile

EXPECTED='d3a7399f07179a0f643dc9e1ae28a9e92a39b7f82f3bb3d237434876a03d2ae6'
REL=Path('Common/edk2/BaseTools/Scripts/GccBase.lds')
ap=argparse.ArgumentParser(); ap.add_argument('source_root',type=Path); ap.add_argument('--apply',action='store_true'); args=ap.parse_args()
target=args.source_root.resolve(strict=True)/REL
if target.is_symlink() or not target.is_file(): raise SystemExit('Unexpected linker source')
raw=target.read_bytes()
if hashlib.sha256(raw).hexdigest()!=EXPECTED: raise SystemExit('Unexpected linker script; no modification')
s=raw.decode('utf-8')
if s.count('SECTIONS {')!=1: raise SystemExit('Unexpected sections marker')
s=s.replace('SECTIONS {','PHDRS { text PT_LOAD FLAGS(5); data PT_LOAD FLAGS(6); }\nSECTIONS {',1)
for anchor, phdr in [('  .text : ALIGN(', 'text'), ('  .data ALIGN(', 'data')]:
    if s.count(anchor)!=1: raise SystemExit('Unexpected section anchor')
    start=s.index(anchor); end=s.index('\n  }',start)+4
    s=s[:end]+' :'+phdr+s[end:]
if not args.apply:
    print('LINKER_SEGMENTS_PREFLIGHT_PASS; NO CHANGES')
    raise SystemExit(0)
fd,tmp=tempfile.mkstemp(prefix='.lmi-linker-',dir=target.parent)
try:
    with os.fdopen(fd,'wb') as f:
        f.write(s.encode('utf-8')); f.flush(); os.fsync(f.fileno())
    os.chmod(tmp,target.stat().st_mode & 0o777)
    os.replace(tmp,target)
finally:
    if os.path.exists(tmp): os.unlink(tmp)
print('LINKER_SEGMENTS_APPLIED')
