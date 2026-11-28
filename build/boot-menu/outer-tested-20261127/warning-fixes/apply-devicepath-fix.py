#!/usr/bin/env python3
"""Preflight or apply the reviewed BaseTools fix to a disposable source tree."""
import argparse
import hashlib
import os
from pathlib import Path
import tempfile

ORIGINAL = 'c17e67247eb9f94eee8dd61121d0ede5aa95574b4fac3a57e960dd1f399a6ca0'
FIXED = '45d935657cafb688de31c5a2450d835d40c0b9768715e5e59ef4e6af2d1c27a1'
RELATIVE = Path('Common/edk2/BaseTools/Source/C/DevicePath/DevicePathUtilities.c')
candidate = Path(__file__).resolve().parent / 'DevicePathUtilities-warning-candidate.c'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('source_root', type=Path, help='edk2-msm source tree')
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()
    root = args.source_root.resolve(strict=True)
    target = root / RELATIVE
    if target.is_symlink() or not target.is_file():
        raise SystemExit('Unexpected target')
    current = target.read_bytes()
    replacement = candidate.read_bytes()
    if sha(replacement) != FIXED:
        raise SystemExit('Candidate hash mismatch')
    if sha(current) != ORIGINAL:
        raise SystemExit('Original hash mismatch; no modification')
    if args.apply:
        fd, tmp = tempfile.mkstemp(prefix='.lmi-devicepath-', dir=target.parent)
        try:
            with os.fdopen(fd, 'wb') as out:
                out.write(replacement)
                out.flush()
                os.fsync(out.fileno())
            os.chmod(tmp, target.stat().st_mode & 0o777)
            os.replace(tmp, target)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        if sha(target.read_bytes()) != FIXED:
            raise SystemExit('Post-write hash mismatch')
        print('DEVICEPATH_FIX_APPLIED')
    else:
        print('DEVICEPATH_FIX_PREFLIGHT_PASS; NO CHANGES')

if __name__ == '__main__':
    main()
