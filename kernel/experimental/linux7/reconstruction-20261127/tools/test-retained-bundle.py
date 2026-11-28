#!/usr/bin/env python3
"""Recreate the retained bundle in a temporary directory and check its hash."""
import hashlib, subprocess, sys, tempfile
from pathlib import Path
if len(sys.argv)!=3: raise SystemExit('Usage: test-retained-bundle.py WORKING_BUNDLE TESTED_KERNEL_IMAGE')
recipe=Path(__file__).resolve().parent.parent/'prepare-bundle.py'
with tempfile.TemporaryDirectory(prefix='lmi-bundle-check-') as tmp:
    out=Path(tmp)/'bundle'
    subprocess.run([sys.executable,str(recipe),sys.argv[1],sys.argv[2],str(out)],check=True)
    digest=hashlib.sha256((out/'lmi-outer-linux7.bin').read_bytes()).hexdigest()
    if digest!='6008823c4a4d62ca6bcd33066bfceb68a61c606efc5430c7a1015d7e6c693dba':
        raise SystemExit('Reconstructed bundle differs from retained test bundle: '+digest)
    print('RETAINED_BUNDLE_REBUILT_AND_VERIFIED')
