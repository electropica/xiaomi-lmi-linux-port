#!/bin/bash
# Operator-run package build only. No image generation or phone installation.
set -euo pipefail
test "$(id -u)" -eq 0 || { echo 'Run with sudo.' >&2; exit 1; }
test "$#" -eq 0
root=/home/linuxagent/phosh-gauge-wake-build/rootfs
task=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
stage="$root/build/lmi-home-drag-inputs"
test "$(chroot "$root" dpkg --print-architecture)" = arm64
exec 9>/run/lmi-phosh-gauge-build.lock
flock -n 9 || { echo 'Phosh build already running.' >&2; exit 1; }
test "$(df --output=avail -B1 /home/linuxagent | tail -1)" -ge 2147483648
if [[ ! -e $stage ]]; then
    python3 "$task/prepare.py" --source "$root/build/phosh-0.46.0" \
        --ui /home/linuxagent/xiaomi-lmi-linux-port/userspace/phosh/files/home-drawer/app-grid.ui \
        --output "$stage"
fi
python3 - "$root" "$stage" <<'PY'
from pathlib import Path
import hashlib,json,subprocess,sys,shutil
root,stage=map(Path,sys.argv[1:]);src=root/'build/phosh-0.46.0'
m=json.loads((stage/'identity.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(src/'src/screen-saver-manager.c')==m['quiet_source_sha256']
version=m['version'];head=(src/'debian/changelog').read_text().splitlines()[0]
assert head in ['phosh (0.46.0-3+deb13u1+lmigaugewake3) UNRELEASED; urgency=medium','phosh ('+version+') UNRELEASED; urgency=medium']
for name,after in m['after'].items():
    assert sha(stage/name)==after
    target=src/name
    if target.exists():assert sha(target) in [m['before'].get(name),after],name
    else:assert name not in m['before'],name
backup=stage/'original-source';backup.mkdir(exist_ok=True)
for name in m['before']:
    b=backup/name
    if not b.exists():b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src/name,b)
for name in m['after']:
    shutil.copyfile(stage/name,src/name)
if head.startswith('phosh (0.46.0-3+deb13u1+lmigaugewake3)'):
    subprocess.run(['chroot',str(root),'/bin/sh','-c','cd /build/phosh-0.46.0 && DEBFULLNAME="Local lmi" DEBEMAIL="local@example.invalid" dch --newversion "$1" --distribution UNRELEASED "Add favorite drag ordering and persistent home shortcuts; retain quiet-gauge v3."','sh',version],check=True)
for name,after in m['after'].items():assert sha(src/name)==after
assert sha(src/'src/screen-saver-manager.c')==m['quiet_source_sha256']
print('SOURCES_VERIFIED; QUIET_GAUGE_V3_UNCHANGED')
PY
unshare --mount --fork --propagation private bash -c '
    set -euo pipefail
    mount -t proc proc "$1/proc"
    chroot "$1" /bin/bash -c '\''
        set -euo pipefail
        export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
        cd /build/phosh-0.46.0
        chown -R builder:builder .
        runuser -u builder -- env DEB_BUILD_OPTIONS=parallel=2 dpkg-buildpackage -b -us -uc -j2
    '\''
' bash "$root"
for package in phosh phosh-common; do
    arch=arm64; [[ $package == phosh-common ]] && arch=all
    file="$root/build/${package}_0.46.0-3+deb13u1+lmigaugewake3+homedrag1_${arch}.deb"
    test -f "$file"
    test "$(dpkg-deb -f "$file" Version)" = '0.46.0-3+deb13u1+lmigaugewake3+homedrag1'
    sha256sum "$file"
done
printf 'HOME_DRAG_PACKAGES_BUILT\nNo phone installation or full image build performed.\n'
