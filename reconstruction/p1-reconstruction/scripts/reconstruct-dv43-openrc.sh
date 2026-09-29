#!/usr/bin/env bash
set -euo pipefail

# This script contains no key material. It assumes the Shelli packages have
# already been built/indexed and the corresponding public keys are trusted.
# Default mode only verifies the recorded installation. Pass --install to run
# the pinned pmbootstrap install first; this can modify the configured workdir.

mode=${1:---verify-only}
case "$mode" in
    --verify-only|--install) ;;
    *) printf 'usage: %s [--verify-only|--install]\n' "$0" >&2; exit 2 ;;
esac

pmbootstrap_py=${PMBOOTSTRAP_PY:-/home/linuxagent/pmbootstrap-3.10.1/pmbootstrap.py}
config=${PMBOOTSTRAP_CONFIG:-/home/linuxagent/dv43-openrc-reconstruction/pmbootstrap_v3.cfg}
work=${PMBOOTSTRAP_WORK:-/home/linuxagent/dv43-openrc-work}
aports=${PMBOOTSTRAP_APORTS:-/home/linuxagent/pmaports-dv43-reference}
package_root=${PACKAGE_ROOT:-/home/linuxagent/dv43-pmbootstrap-work/packages/edge}
rootfs=${ROOTFS_DIR:-$work/chroot_rootfs_xiaomi-lmi}
image=${ROOTFS_IMAGE:-$work/chroot_native/home/pmos/rootfs/xiaomi-lmi.img}

die() { printf 'error: %s\n' "$*" >&2; exit 1; }

check_sha256() {
    local expected=$1 path=$2 actual
    [[ -f "$path" ]] || die "missing input/output: $path"
    actual=$(sha256sum "$path")
    actual=${actual%% *}
    [[ "$actual" == "$expected" ]] ||
        die "SHA-256 mismatch for $path (expected $expected, got $actual)"
}

require_config() {
    local key=$1 value=$2
    grep -Eq "^[[:space:]]*${key}[[:space:]]*=[[:space:]]*${value}[[:space:]]*$" "$config" ||
        die "configuration mismatch: expected $key=$value"
}

package_version() {
    local wanted=$1 db=$rootfs/lib/apk/db/installed
    awk -v wanted="$wanted" 'BEGIN { RS=""; FS="\n" }
        { p=""; v=""; for (i=1; i<=NF; i++) {
            if ($i ~ /^P:/) p=substr($i,3)
            if ($i ~ /^V:/) v=substr($i,3)
          }
          if (p == wanted) { print v; found=1 }
        }
        END { if (!found) exit 1 }' "$db"
}

expect_package() {
    local package=$1 expected=$2 actual
    actual=$(package_version "$package") || die "missing installed package: $package"
    [[ "$actual" == "$expected" ]] ||
        die "installed version mismatch for $package (expected $expected, got $actual)"
}

check_sha256 888899d267302a70684251f53e2248e469c627eab73a7320c4ff30f6d1cb0afc \
    "$package_root/x86_64/postmarketos-initramfs-3.12.0-r1.apk"
check_sha256 dee65e97c8d56230c9507241d0a338a788bea3f804728134c45d8edb4dffc490 \
    "$package_root/aarch64/device-xiaomi-lmi-1-r104.apk"
check_sha256 b73209a895a826fcce058c95e9d1bff9a9ccb1f696b93f1c77eae6469201173f \
    "$package_root/aarch64/linux-xiaomi-lmi-4.19.325-r8.apk"

check_sha256 f3dd2436f440bdca823c4efcde8ceeb25c332c5884393419af940da66a2be656 "$config"
require_config aports /home/linuxagent/pmaports-dv43-reference
require_config work /home/linuxagent/dv43-openrc-work
require_config device xiaomi-lmi
require_config ui shelli
require_config user lmi
require_config systemd never
require_config build_pkgs_on_install False
require_config extra_packages openssh-server,iw,wpa_supplicant,docker,openrc-settingsd,vim,htop
require_config timezone Europe/Paris

if [[ "$mode" == --install ]]; then
    [[ -f "$pmbootstrap_py" ]] || die "pmbootstrap not found: $pmbootstrap_py"
    [[ -d "$aports" ]] || die "aports not found: $aports"
    mkdir -p "$work"
    python3 "$pmbootstrap_py" \
        --config="$config" \
        --work="$work" \
        --aports="$aports" \
        install --no-fde --sector-size 4096 --no-sparse \
        --add "postmarketos-initramfs=3.12.0-r1,device-xiaomi-lmi=1-r104,linux-xiaomi-lmi=4.19.325-r8"
fi

expect_package device-xiaomi-lmi 1-r104
expect_package linux-xiaomi-lmi 4.19.325-r8
expect_package postmarketos-initramfs 3.12.0-r1
expect_package postmarketos-ui-shelli 3-r8
expect_package postmarketos-ui-shelli-openrc 3-r8
package_version postmarketos-base-openrc >/dev/null || die 'postmarketos-base-openrc is absent'
package_version openssh-server >/dev/null || die 'openssh-server is absent'
if package_version systemd >/dev/null 2>&1; then
    die 'systemd must be absent'
fi

[[ $(readlink "$rootfs/sbin/init") == /bin/busybox ]] ||
    die '/sbin/init does not resolve to /bin/busybox'
grep -Fqx 'init="/sbin/init"' "$rootfs/usr/share/initramfs/init_2nd.sh" ||
    die 'init_2nd.sh does not select /sbin/init'

check_sha256 7e91267713551eeec7c1790d0a100358e23b6554753d67a5df075502a69a401c "$image"
[[ $(stat -c %s "$image") == 1568669696 ]] || die 'unexpected rootfs image size'
check_sha256 ecaa289c82840ae049ff846a5216937ffc68bd6d73b9c273dc11477c99be0075 "$rootfs/boot/boot.img"
check_sha256 47839a2bac46d3513e3b0509fe982657d93762247ecfbdc1e0386837caf1af57 "$rootfs/boot/vmlinuz"
check_sha256 38a522a2285ca1f58a0d26986d355378fbea546a2e97e3a8b41e6b862d234ded "$rootfs/boot/initramfs"

printf 'D-v43 OpenRC reconstruction: recorded static checks passed\n'
printf 'This script does not perform the separately documented hardware validation.\n'
