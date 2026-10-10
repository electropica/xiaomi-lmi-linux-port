#!/usr/bin/env python3
"""Validate private package/firmware inputs and stage an offline image profile."""
import argparse, hashlib, shutil, subprocess
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--inputs', type=Path, required=True)
p.add_argument('--destination', type=Path, required=True)
a=p.parse_args()
repo=Path(__file__).resolve().parents[3]
names=['upower', 'libupower-glib3', 'gir1.2-upowerglib-1.0']
files=[]
for name in names:
    f=a.inputs/(name+'_1.90.9-1+lmi1_arm64.deb')
    if not f.is_file() or f.is_symlink(): raise SystemExit('Missing regular input: '+str(f))
    fields=subprocess.check_output(['dpkg-deb', '-f', str(f), 'Package', 'Version', 'Architecture'], text=True).splitlines()
    expected=['Package: '+name, 'Version: 1.90.9-1+lmi1', 'Architecture: arm64']
    if fields != expected: raise SystemExit('Unexpected package identity: '+str(f))
    files.append(f)
fw=a.inputs/'tfa98xx.cnt'
if not fw.is_file() or fw.is_symlink() or hashlib.sha256(fw.read_bytes()).hexdigest() != '07abfca151aaa296595fff35d53c2aa2999e7d16cdc373ade2fd5954ff90c9a9':
    raise SystemExit('Missing or incorrect TFA firmware input')
files.append(fw)
# Verify the saved private package identities, not only their Debian metadata.
manifest=a.inputs/'SHA256SUMS'
lines=manifest.read_text().splitlines()
expected={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
parsed={}
for line in lines:
    digest, name=line.split('  ', 1)
    if name in parsed: raise SystemExit('Duplicate input manifest entry')
    parsed[name]=digest
if parsed != expected: raise SystemExit('Private input manifest mismatch')
if a.destination.exists(): raise SystemExit('Refusing existing profile staging directory')
a.destination.mkdir(parents=True)
shutil.copytree(repo/'build/profiles/lmi-current', a.destination/'profile')
shutil.copytree(repo/'userspace/audio/files', a.destination/'audio')
(a.destination/'apps').mkdir()
for name in ['lmi-flashlight.py','lmi-flashlight.desktop','lmi-chatty-safe']:
    shutil.copy2(repo/'userspace/apps/files'/name, a.destination/'apps'/name)
(a.destination/'power').mkdir()
shutil.copy2(repo/'userspace/power/scripts/lmi-cpu-idle', a.destination/'power/lmi-cpu-idle')
shutil.copy2(repo/'userspace/power/files/lmi-cpu-idle.service', a.destination/'power/lmi-cpu-idle.service')
for source in ['scripts/lmi-npu-suspend', 'files/lmi-npu-suspend-hook', 'files/90-lmi-npu-suspend.conf']:
    shutil.copy2(repo/'userspace/power'/source, a.destination/'power'/Path(source).name)
for name in ['99-lmi-upower-status.rules','94_lmi-current-power.gschema.override']:
    shutil.copy2(repo/'build/profiles/lmi-current'/name, a.destination/'power'/name)
shutil.copy2(repo/'build/profiles/lmi-current/PROFILE.txt', a.destination/'PROFILE.txt')
# Reuse the reviewed clock-floor assets rather than maintaining another copy.
shutil.copytree(repo/'build/userdata/profiles/time-seed/overlay/rootfs', a.destination/'time-seed')
shutil.copy2(repo/'build/userdata/profiles/time-seed/hooks.d/10-initialize-lmi-time-seed.sh', a.destination/'initialize-time-seed.sh')
(a.destination/'inputs').mkdir()
for f in files+[manifest]: shutil.copy2(f, a.destination/'inputs'/f.name)
print('CURRENT_PROFILE_INPUTS_VALIDATED')
