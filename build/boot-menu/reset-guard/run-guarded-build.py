#!/usr/bin/env python3
"""Operator-invoked firmware build with a temporary, pinned reset-source edit."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('reset_patch', here / 'patch-reset.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
root = Path('/source/edk2-msm')
source = root / module.RELATIVE_SOURCE
original = source.read_bytes()
patched = module.patch(original)
digest = lambda raw: hashlib.sha256(raw).hexdigest()
record = {'schema': 1, 'source': module.RELATIVE_SOURCE,
          'before': digest(original), 'after': digest(patched),
          'baseline_commit': '78e8328dfb09bbbce109bd0a4accf8561d44af94',
          'variant': 'android-working-32MiB-resetguard1',
          'restored': False, 'hardware_validated': False}
manifest = Path('/output/reset-guard-manifest.json')
manifest.write_text(json.dumps(record, indent=2) + '\n')
code = 1
source.write_bytes(patched)
try:
    code = subprocess.run(['bash', 'build.sh', '--device', 'lmi', '--toolchain',
                           'CLANG38', '--release', 'RELEASE',
                           '--outputdir', '/output'], cwd=root).returncode
finally:
    if digest(source.read_bytes()) != record['after']:
        raise RuntimeError('Reset source changed during build; refusing restoration')
    source.write_bytes(original)
    record['restored'] = digest(source.read_bytes()) == record['before']
    record['builder_exit'] = code
    manifest.write_text(json.dumps(record, indent=2) + '\n')
sys.exit(code)
