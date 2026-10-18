#!/bin/bash
# Operator-run package build only. No image generation or phone installation.
set -euo pipefail
test "$(id -u)" -eq 0 || { echo 'Run with sudo.' >&2; exit 1; }
test "$#" -eq 0
root=/home/linuxagent/phosh-gauge-wake-build/rootfs
task=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
stage="$root/build/lmi-home-drag2-inputs"
test "$(chroot "$root" dpkg --print-architecture)" = arm64
exec 9>/run/lmi-phosh-gauge-build.lock
flock -n 9 || { echo 'Phosh build already running.' >&2; exit 1; }
test "$(df --output=avail -B1 /home/linuxagent | tail -1)" -ge 2147483648
python3 - "$root" "$stage" "$task" <<'PY'
from pathlib import Path
import hashlib,json,subprocess,sys,shutil,tempfile
root,stage,task=map(Path,sys.argv[1:]);src=root/'build/phosh-0.46.0'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=root/'build/lmi-home-drag-inputs'
old=json.loads((prior/'identity.json').read_text()) if (prior/'identity.json').is_file() else None
if old:assert old['version']=='0.46.0-3+deb13u1+lmigaugewake3+homedrag1'
if not stage.exists():
    source=src
    with tempfile.TemporaryDirectory(prefix='lmi-home-v2-baseline-') as temporary:
        if old:
            source=Path(temporary)/'baseline'
            shutil.copytree(prior/'original-source',source)
            for name,digest in old['before'].items():assert sha(source/name)==digest,name
            shutil.copy2(src/'src/screen-saver-manager.c',source/'src/screen-saver-manager.c')
            (source/'debian').mkdir()
            (source/'debian/changelog').write_text('phosh (0.46.0-3+deb13u1+lmigaugewake3) UNRELEASED; urgency=medium\n')
        subprocess.run(['python3',str(task/'prepare.py'),'--source',str(source),'--ui','/home/linuxagent/xiaomi-lmi-linux-port/userspace/phosh/files/home-drawer/app-grid.ui','--output',str(stage)],check=True)
m=json.loads((stage/'identity.json').read_text())
assert m['version']=='0.46.0-3+deb13u1+lmigaugewake3+homedrag2'
assert sha(src/'src/screen-saver-manager.c')==m['quiet_source_sha256']
version=m['version'];head=(src/'debian/changelog').read_text().splitlines()[0]
accepted=['0.46.0-3+deb13u1+lmigaugewake3',version]+([old['version']] if old else [])
assert head in ['phosh ('+v+') UNRELEASED; urgency=medium' for v in accepted]
for name,after in m['after'].items():
    assert sha(stage/name)==after,name
    target=src/name
    if target.exists():assert sha(target) in [m['before'].get(name),after,old['after'].get(name) if old else None],name
    else:assert name not in m['before'],name
backup=stage/'original-source';backup.mkdir(exist_ok=True)
for name,digest in m['before'].items():
    b=backup/name
    if not b.exists():
        original=prior/'original-source'/name if old else src/name
        assert sha(original)==digest
        b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original,b)
for name in m['after']:shutil.copyfile(stage/name,src/name)
if head!='phosh ('+version+') UNRELEASED; urgency=medium':
    subprocess.run(['chroot',str(root),'/bin/sh','-c','cd /build/phosh-0.46.0 && DEBFULLNAME="Local lmi" DEBEMAIL="local@example.invalid" dch --newversion "$1" --distribution UNRELEASED "Reveal home at drag start and let only actual slots receive drops; retain quiet-gauge v3."','sh',version],check=True)
for name,after in m['after'].items():assert sha(src/name)==after
assert sha(src/'src/screen-saver-manager.c')==m['quiet_source_sha256']
# Re-run build/tests incrementally; do not use a stale debhelper build stamp.
stamp=src/'debian/debhelper-build-stamp'
assert not stamp.is_symlink()
if stamp.exists():assert stamp.is_file();stamp.unlink()
print('SOURCES_VERIFIED; QUIET_GAUGE_V3_UNCHANGED; INCREMENTAL_REBUILD')
PY
unshare --mount --fork --propagation private bash -c '
    set -euo pipefail
    mount -t proc proc "$1/proc"
    chroot "$1" /bin/bash -c '\''
        set -euo pipefail
        export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
        cd /build/phosh-0.46.0
        chown -R builder:builder .
        runuser -u builder -- env DEB_BUILD_OPTIONS=parallel=2 dpkg-buildpackage -b -nc -us -uc -j2
    '\''
' bash "$root"
for package in phosh phosh-common; do
    arch=arm64; [[ $package == phosh-common ]] && arch=all
    file="$root/build/${package}_0.46.0-3+deb13u1+lmigaugewake3+homedrag2_${arch}.deb"
    test -f "$file"
    test "$(dpkg-deb -f "$file" Version)" = '0.46.0-3+deb13u1+lmigaugewake3+homedrag2'
    sha256sum "$file"
done
printf 'HOME_DRAG_PACKAGES_BUILT\nNo phone installation or full image build performed.\n'
