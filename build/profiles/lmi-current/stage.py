#!/usr/bin/env python3
"""Validate private package/firmware inputs and stage an offline image profile."""
import argparse, hashlib, shutil, subprocess, os
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--inputs', type=Path, required=True)
p.add_argument('--destination', type=Path, required=True)
a=p.parse_args()
repo=Path(__file__).resolve().parents[3]
complete=os.environ.get('M1_COMPLETE_LMI_PROFILE','0')=='1'
camera_bundle=None
if complete:
    camera_bundle=Path(os.environ['M1_COMPLETE_CAMERA_BUNDLE'])
    subprocess.run(['python3',str(repo/'userspace/camera/snapshot-bundle/check-bundle.py'),str(camera_bundle)],check=True)
phosh_version='0.46.0-3+deb13u1+lmigaugewake3'+('+homedrag8+esrquiet1+drawerscroll1+irqnames1+drawerpreview1' if complete else '')
gsd_version='48.1-1+lmiquietgauge3'+('+esrquiet1+irqnames1' if complete else '')
packages=[
    ('upower', '1.90.9-1+lmi1', 'arm64'),
    ('libupower-glib3', '1.90.9-1+lmi1', 'arm64'),
    ('gir1.2-upowerglib-1.0', '1.90.9-1+lmi1', 'arm64'),
    ('phosh', phosh_version, 'arm64'),
    ('phosh-common', phosh_version, 'all'),
    ('gnome-settings-daemon', gsd_version, 'arm64'),
    ('gnome-settings-daemon-common', gsd_version, 'all'),
]
if complete:
    packages.append(('phoc', '0.46.0-1+lmishelldnd1+thumblinear1+thumbrows1+thumbfbo1', 'arm64'))
files=[]
for name, version, arch in packages:
    f=a.inputs/(name+'_'+version+'_'+arch+'.deb')
    if not f.is_file() or f.is_symlink(): raise SystemExit('Missing regular input: '+str(f))
    fields=subprocess.check_output(['dpkg-deb', '-f', str(f), 'Package', 'Version', 'Architecture'], text=True).splitlines()
    expected=['Package: '+name, 'Version: '+version, 'Architecture: '+arch]
    if fields != expected: raise SystemExit('Unexpected package identity: '+str(f))
    files.append(f)
fw=a.inputs/'tfa98xx.cnt'
if not fw.is_file() or fw.is_symlink() or hashlib.sha256(fw.read_bytes()).hexdigest() != '07abfca151aaa296595fff35d53c2aa2999e7d16cdc373ade2fd5954ff90c9a9':
    raise SystemExit('Missing or incorrect TFA firmware input')
files.append(fw)
# Verify the saved private package identities, not only their Debian metadata.
manifest=a.inputs/'SHA256SUMS'
if not manifest.is_file() or manifest.is_symlink(): raise SystemExit('Missing regular checksum manifest')
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
shutil.copytree(repo/'userspace/phosh/files/home-drawer', a.destination/'home-drawer')
(a.destination/'apps').mkdir()
for name in ['lmi-flashlight.py','lmi-flashlight.desktop','lmi-chatty-safe','install-chatty-safe.sh']:
    shutil.copy2(repo/'userspace/apps/files'/name, a.destination/'apps'/name)
(a.destination/'power').mkdir()
for name in ['phosh-quiet-resume.conf','gsd-quiet-resume.conf']:
    shutil.copy2(repo/'kernel/diagnostics/power/userspace'/name, a.destination/'power'/name)
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
if complete:
    import importlib.util
    spec=importlib.util.spec_from_file_location('bundle_check',repo/'userspace/camera/snapshot-bundle/check-bundle.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    (a.destination/'camera').mkdir()
    for name in sorted(module.NAMES|{'SHA256SUMS'}):
        shutil.copy2(camera_bundle/name,a.destination/'camera'/name)
    (a.destination/'COMPLETE_PROFILE').write_text('native-home-drag-irqnames-preview-and-snapshot-v9\n')
    profile=a.destination/'PROFILE.txt'
    text=profile.read_text().replace('Camera Snapshot bridge remains experimental and is not installed by this profile.',
        'Experimental Snapshot rear-camera bridge is installed; the new foreground lifecycle and native drag gestures require post-flash testing.')
    profile.write_text(text+'Native Phosh home drag homedrag8: persistent home slots, up to five favorites added by drag, favorite reorder, shortcut removal, compact labels, native drawer/dock UI, confirmed lock-screen shutdown/restart actions and Phoc shell-layer DnD grab routing; old resource overlay deliberately omitted. IRQ-independent quiet resumes, accepted closed-drawer previews and private-FBO thumbnails are selected; temporary diagnostic kernel/DT state is not promoted.\n')
print('CURRENT_PROFILE_INPUTS_VALIDATED')
