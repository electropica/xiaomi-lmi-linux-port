#!/usr/bin/env bash
set -Eeuo pipefail

# Build one D-v43/OpenRC boot image without the exact pmos.debug-shell token.
# All backups and validation evidence remain below STATE_ROOT; /tmp is not used.

readonly STATE_ROOT=/home/linuxagent/dv43-openrc-reconstruction/no-debug-shell
readonly ROOTFS=/home/linuxagent/dv43-openrc-work/chroot_rootfs_xiaomi-lmi
readonly BOOT_DIR="$ROOTFS/boot"
readonly BOOT_IMAGE="$BOOT_DIR/boot.img"
readonly DEVICEINFO_DIR="$ROOTFS/usr/share/deviceinfo"
readonly DEVICEINFO_LINK="$DEVICEINFO_DIR/deviceinfo"
readonly DEVICEINFO_REAL="$DEVICEINFO_DIR/device-xiaomi-lmi"
readonly INIT_2ND="$ROOTFS/usr/share/initramfs/init_2nd.sh"
readonly APK_DB="$ROOTFS/lib/apk/db/installed"
readonly TOKEN=pmos.debug-shell
readonly HISTORIC_BOOT_SHA=ecaa289c82840ae049ff846a5216937ffc68bd6d73b9c273dc11477c99be0075
readonly OUTPUT="$STATE_ROOT/boot-dv43-openrc-no-debug-shell-20260923.img"

readonly QEMU_SOURCE=/home/linuxagent/dv43-openrc-work/chroot_buildroot_aarch64/usr/bin/qemu-aarch64-static
readonly QEMU_SHA=b0cf5f4a1459f65e279aac883dc7fdc7eb2950c77ee7e1a14e6e9842d51f30cd
readonly UNPACK_SOURCE="$ROOTFS/usr/bin/unpackbootimg"
readonly UNPACK_SHA=f7cd0b12eaf3afae4b239e180b710658139d95a91fc43b467de861d3243e7b42

die() {
    printf 'error: %s\n' "$*" >&2
    exit 1
}

sha256_of() {
    sha256sum "$1" | awk '{print $1}'
}

require_sha256() {
    local expected=$1 path=$2 actual
    [[ -f "$path" ]] || die "missing file: $path"
    actual=$(sha256_of "$path")
    [[ "$actual" == "$expected" ]] ||
        die "SHA-256 mismatch for $path (expected $expected, got $actual)"
}

package_version() {
    local wanted=$1
    awk -v wanted="$wanted" 'BEGIN { RS=""; FS="\n" }
        {
            p=""; v=""
            for (i=1; i<=NF; i++) {
                if ($i ~ /^P:/) p=substr($i, 3)
                if ($i ~ /^V:/) v=substr($i, 3)
            }
            if (p == wanted) { print v; found=1 }
        }
        END { if (!found) exit 1 }' "$APK_DB"
}

expect_package() {
    local package=$1 expected=$2 actual
    actual=$(package_version "$package") || die "missing installed package: $package"
    [[ "$actual" == "$expected" ]] ||
        die "installed version mismatch for $package (expected $expected, got $actual)"
}

count_exact_token() {
    local path=$1
    awk -v token="$TOKEN" '
        {
            for (i=1; i<=NF; i++)
                if ($i == token) count++
        }
        END { print count+0 }' "$path"
}

extract_cmdline() {
    local image=$1 output_dir=$2 cmdline_file
    mkdir "$output_dir"
    "$QEMU" -L "$ROOTFS" "$UNPACK" -i "$image" -o "$output_dir" \
        > "$output_dir/unpackbootimg.stdout" \
        2> "$output_dir/unpackbootimg.stderr"
    cmdline_file=$(find "$output_dir" -maxdepth 1 -type f -name '*-cmdline' -print)
    [[ -n "$cmdline_file" && "$cmdline_file" != *$'\n'* && -f "$cmdline_file" ]] ||
        die "unpackbootimg did not produce exactly one cmdline file in $output_dir"
    printf '%s\n' "$cmdline_file"
}

restore_needed=0
lock_held=0

restore_rootfs() {
    local failed=0

    set +e
    if [[ -e "$BOOT_DIR" || -L "$BOOT_DIR" ]]; then
        if [[ -e "$RUN_STATE/boot-after-build" || -L "$RUN_STATE/boot-after-build" ]]; then
            printf 'error: preservation target already exists: %s\n' \
                "$RUN_STATE/boot-after-build" >&2
            failed=1
        else
            sudo mv "$BOOT_DIR" "$RUN_STATE/boot-after-build" || failed=1
        fi
    fi

    sudo tar --numeric-owner --xattrs --acls -xpf "$BOOT_BACKUP" -C "$ROOTFS" || failed=1
    sudo tar --numeric-owner --xattrs --acls -xpf "$DEVICEINFO_BACKUP" \
        -C "$DEVICEINFO_DIR" || failed=1
    set -e

    return "$failed"
}

verify_restoration() {
    local current_link

    require_sha256 "$HISTORIC_BOOT_SHA" "$BOOT_IMAGE"
    require_sha256 "$DEVICEINFO_LINK_SHA" "$DEVICEINFO_LINK"
    require_sha256 "$DEVICEINFO_REAL_SHA" "$DEVICEINFO_REAL"

    [[ -L "$DEVICEINFO_LINK" ]] || die "$DEVICEINFO_LINK was not restored as a symlink"
    current_link=$(readlink "$DEVICEINFO_LINK")
    [[ "$current_link" == "$DEVICEINFO_LINK_TARGET" ]] ||
        die "deviceinfo symlink target changed (expected $DEVICEINFO_LINK_TARGET, got $current_link)"

    [[ $(count_exact_token "$DEVICEINFO_LINK") == 1 ]] ||
        die "$DEVICEINFO_LINK was not restored with exactly one $TOKEN token"
    [[ $(count_exact_token "$DEVICEINFO_REAL") == 1 ]] ||
        die "$DEVICEINFO_REAL was not restored with exactly one $TOKEN token"
    grep -Fqx 'init="/sbin/init"' "$INIT_2ND" ||
        die 'init_2nd.sh no longer selects /sbin/init'
    if package_version systemd >/dev/null 2>&1; then
        die 'systemd is installed after restoration'
    fi
}

on_exit() {
    local rc=$?
    trap - EXIT

    if [[ "$restore_needed" -eq 1 ]]; then
        printf 'Restoring the validated rootfs and complete /boot tree...\n' >&2
        if restore_rootfs && (verify_restoration); then
            restore_needed=0
            printf 'Restoration verified.\n' >&2
        else
            printf 'error: automatic restoration failed; backups remain in %s\n' \
                "$RUN_STATE" >&2
            rc=1
        fi
    fi

    if [[ "$lock_held" -eq 1 ]]; then
        rmdir "$LOCK_DIR" 2>/dev/null || true
    fi
    exit "$rc"
}

trap on_exit EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

mkdir -p "$STATE_ROOT"
LOCK_DIR="$STATE_ROOT/.build-openrc-no-debug-shell.lock"
mkdir "$LOCK_DIR" 2>/dev/null || die "another run may be active: $LOCK_DIR exists"
lock_held=1

[[ ! -e "$OUTPUT" && ! -L "$OUTPUT" ]] || die "refusing to overwrite output: $OUTPUT"
[[ -d "$ROOTFS" ]] || die "missing rootfs: $ROOTFS"
[[ -d "$BOOT_DIR" ]] || die "missing boot directory: $BOOT_DIR"
[[ -f "$APK_DB" ]] || die "missing installed package database: $APK_DB"
[[ -L "$DEVICEINFO_LINK" ]] || die "$DEVICEINFO_LINK is expected to be a symlink"
DEVICEINFO_LINK_TARGET=$(readlink "$DEVICEINFO_LINK")
[[ "$DEVICEINFO_LINK_TARGET" == device-xiaomi-lmi ]] ||
    die "unexpected deviceinfo symlink target: $DEVICEINFO_LINK_TARGET"
[[ -f "$DEVICEINFO_REAL" ]] || die "missing deviceinfo target: $DEVICEINFO_REAL"

expect_package device-xiaomi-lmi 1-r104
expect_package linux-xiaomi-lmi 4.19.325-r8
expect_package postmarketos-initramfs 3.12.0-r1
if package_version systemd >/dev/null 2>&1; then
    die 'systemd must be absent before the build'
fi
grep -Fqx 'init="/sbin/init"' "$INIT_2ND" ||
    die 'init_2nd.sh does not select /sbin/init'
require_sha256 "$HISTORIC_BOOT_SHA" "$BOOT_IMAGE"

[[ $(count_exact_token "$DEVICEINFO_LINK") == 1 ]] ||
    die "$DEVICEINFO_LINK must contain exactly one $TOKEN token"
[[ $(count_exact_token "$DEVICEINFO_REAL") == 1 ]] ||
    die "$DEVICEINFO_REAL must contain exactly one $TOKEN token"
[[ $(grep -Foc " $TOKEN " "$DEVICEINFO_REAL") == 1 ]] ||
    die "$DEVICEINFO_REAL must contain exactly one space-delimited $TOKEN token"

require_sha256 "$QEMU_SHA" "$QEMU_SOURCE"
require_sha256 "$UNPACK_SHA" "$UNPACK_SOURCE"

run_id=$(date -u +%Y%m%dT%H%M%SZ)-$$
RUN_STATE="$STATE_ROOT/state-$run_id"
mkdir "$RUN_STATE"
BOOT_BACKUP="$RUN_STATE/boot-before-build.tar"
DEVICEINFO_BACKUP="$RUN_STATE/deviceinfo-before-build.tar"

DEVICEINFO_LINK_SHA=$(sha256_of "$DEVICEINFO_LINK")
DEVICEINFO_REAL_SHA=$(sha256_of "$DEVICEINFO_REAL")
printf '%s  %s\n%s  %s\n' \
    "$DEVICEINFO_LINK_SHA" "$DEVICEINFO_LINK" \
    "$DEVICEINFO_REAL_SHA" "$DEVICEINFO_REAL" \
    > "$RUN_STATE/deviceinfo-before-build.sha256"

sudo -v
sudo tar --numeric-owner --xattrs --acls -cpf - -C "$ROOTFS" boot \
    > "$BOOT_BACKUP"
sudo tar --numeric-owner --xattrs --acls -cpf - -C "$DEVICEINFO_DIR" \
    deviceinfo device-xiaomi-lmi > "$DEVICEINFO_BACKUP"
sha256sum "$BOOT_BACKUP" "$DEVICEINFO_BACKUP" > "$RUN_STATE/backup-archives.sha256"
restore_needed=1

QEMU="$RUN_STATE/qemu-aarch64-static"
UNPACK="$RUN_STATE/unpackbootimg"
cp --preserve=mode "$QEMU_SOURCE" "$QEMU"
cp --preserve=mode "$UNPACK_SOURCE" "$UNPACK"

historic_cmdline=$(extract_cmdline "$BOOT_IMAGE" "$RUN_STATE/unpacked-historic-boot")
[[ $(count_exact_token "$historic_cmdline") == 1 ]] ||
    die 'historical boot cmdline does not contain exactly one pmos.debug-shell token'
sed 's/ pmos\.debug-shell / /' "$historic_cmdline" \
    > "$RUN_STATE/expected-no-debug-shell.cmdline"

sed 's/ pmos\.debug-shell / /' "$DEVICEINFO_REAL" \
    > "$RUN_STATE/device-xiaomi-lmi.modified"
[[ $(count_exact_token "$RUN_STATE/device-xiaomi-lmi.modified") == 0 ]] ||
    die 'temporary deviceinfo edit did not remove pmos.debug-shell'
sudo cp "$RUN_STATE/device-xiaomi-lmi.modified" "$DEVICEINFO_REAL"

[[ $(count_exact_token "$DEVICEINFO_LINK") == 0 ]] ||
    die "$DEVICEINFO_LINK still contains $TOKEN after temporary edit"
[[ $(count_exact_token "$DEVICEINFO_REAL") == 0 ]] ||
    die "$DEVICEINFO_REAL still contains $TOKEN after temporary edit"

python3 /home/linuxagent/pmbootstrap-3.10.1/pmbootstrap.py \
    --config=/home/linuxagent/dv43-openrc-reconstruction/pmbootstrap_v3.cfg \
    --work=/home/linuxagent/dv43-openrc-work \
    --aports=/home/linuxagent/pmaports-dv43-reference \
    --offline initfs build

[[ -f "$BOOT_IMAGE" ]] || die "pmbootstrap did not produce $BOOT_IMAGE"
new_boot_sha=$(sha256_of "$BOOT_IMAGE")
[[ "$new_boot_sha" != "$HISTORIC_BOOT_SHA" ]] ||
    die 'rebuilt boot image is byte-identical to the historical debug-shell boot'

CANDIDATE="$RUN_STATE/boot-no-debug-shell.candidate.img"
cp --reflink=auto --sparse=always "$BOOT_IMAGE" "$CANDIDATE"
chmod 0444 "$CANDIDATE"

new_cmdline=$(extract_cmdline "$CANDIDATE" "$RUN_STATE/unpacked-new-boot")
[[ $(count_exact_token "$new_cmdline") == 0 ]] ||
    die 'rebuilt boot cmdline still contains the exact pmos.debug-shell token'
cmp -s "$RUN_STATE/expected-no-debug-shell.cmdline" "$new_cmdline" ||
    die 'rebuilt boot cmdline differs from the historical cmdline by more than token removal'

# A hard link makes publication atomic and fails rather than overwriting OUTPUT.
ln "$CANDIDATE" "$OUTPUT"

restore_rootfs
verify_restoration
restore_needed=0

printf 'New boot image: %s\n' "$OUTPUT"
printf 'Size: %s bytes\n' "$(stat -c %s "$OUTPUT")"
printf 'SHA-256: %s\n' "$(sha256_of "$OUTPUT")"
printf 'Persistent state and backups: %s\n' "$RUN_STATE"
printf 'Validated rootfs and historical /boot restoration: OK\n'
