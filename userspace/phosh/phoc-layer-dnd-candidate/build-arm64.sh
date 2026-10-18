#!/bin/bash
# Operator-run Phoc package build; never installs or restarts the phone.
set -euo pipefail
test "$(id -u)" -eq 0 || { echo 'Run with sudo.' >&2; exit 1; }
test "$#" -eq 0
root=/home/linuxagent/phosh-gauge-wake-build/rootfs
task=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo=$(CDPATH= cd -- "$task/../../.." && pwd)
exec 9>/run/lmi-phosh-gauge-build.lock
flock -n 9 || { echo 'Another package build is active.' >&2; exit 1; }
test "$(chroot "$root" dpkg --print-architecture)" = arm64
test "$(df --output=avail -B1 /home/linuxagent | tail -1)" -ge 2147483648
python3 "$task/prepare.py" "$root" "$task"
unshare --mount --fork --propagation private bash -s -- "$root" "$repo" <<'NS'
set -euo pipefail
python3 "$2/userspace/camera/snapshot-bundle/prepare-chroot.py" "$1"
chroot "$1" /bin/bash -s <<'CHROOT'
set -euo pipefail
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export DEBIAN_FRONTEND=noninteractive
apt-get -o Dpkg::Use-Pty=0 -y build-dep /build/lmi-phoc-layer-dnd-inputs/phoc_0.46.0-1.dsc </dev/null
cd /build/phoc-lmi-shell-dnd1
version=0.46.0-1+lmishelldnd1
current=$(dpkg-parsechangelog -S Version)
if [[ $current == 0.46.0-1 ]]; then
 DEBFULLNAME='Local lmi' DEBEMAIL='local@example.invalid' dch --newversion "$version" --distribution UNRELEASED 'Preserve data-device drag grabs on shell layers; keep layer swipes from cancelling active DnD.'
else
 test "$current" = "$version"
fi
id builder >/dev/null
chown -R builder:builder .
# Resume compilation, but always run upstream tests again.
rm -f -- debian/debhelper-build-stamp
runuser -u builder -- env DEB_BUILD_OPTIONS=parallel=2 dpkg-buildpackage -b -nc -us -uc -j2
CHROOT
NS
file="$root/build/phoc_0.46.0-1+lmishelldnd1_arm64.deb"
test -f "$file"
test "$(dpkg-deb -f "$file" Version)" = 0.46.0-1+lmishelldnd1
sha256sum "$file"
printf 'PHOC_DND_PACKAGE_BUILT\nNo phone installation, kernel build or full image build performed.\n'
