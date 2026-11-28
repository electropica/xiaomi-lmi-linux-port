#!/usr/bin/env python3
"""Read-only input audit; does not clone, build or contact a device."""
import hashlib,json,os,subprocess,sys
from pathlib import Path

p=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(p/'write-recipe-manifest.py')],check=True)
def env(name):
    value=os.environ.get(name,'')
    if not value.startswith('/'): raise SystemExit('Set absolute '+name)
    return Path(value)
tool=env('LMI_MENU_TOOLCHAIN_ROOT'); build=env('LMI_MENU_BUILD_ROOT'); bundle=env('LMI_MENU_BUNDLE_DIR')
expected=os.environ.get('LMI_MENU_BUNDLE_SHA256','')
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
if len(expected)!=64 or any(c not in '0123456789abcdef' for c in expected): raise SystemExit('Invalid bundle SHA-256')
if (build/'output').exists(): raise SystemExit('Output already exists')
if not (tool/'rootfs/.lmi-bootstrap-complete').is_file(): raise SystemExit('Missing toolchain rootfs')
if digest(bundle/'lmi-outer-linux7.bin')!=expected: raise SystemExit('Bundle SHA-256 mismatch')
if json.loads((bundle/'BUNDLE_RESULT.json').read_text())['sha256']!=expected: raise SystemExit('Bundle manifest mismatch')
lock=json.loads((p/'sources.lock.json').read_text())
if digest(tool/'inputs/android.img')!=lock['os_images']['android']: raise SystemExit('Android input mismatch')
if digest(tool/'inputs/android-dtbo.img')!='ff610fa3bcedfaa735c045adfa422d53a68bde8d609a2a1e143891998ea31753': raise SystemExit('Android DTBO mismatch')
base=tool/'source/edk2-msm'
for rel,commit in [('',lock['revision'])]+list(lock['submodules'].items()):
    repo=base/rel
    subprocess.run(['git','-c','safe.directory='+str(repo),'-C',str(repo),'cat-file','-e',commit+'^{commit}'],check=True)
print('MENU_INPUT_PREFLIGHT_PASS; NO BUILD OR PHONE CONTACT')
