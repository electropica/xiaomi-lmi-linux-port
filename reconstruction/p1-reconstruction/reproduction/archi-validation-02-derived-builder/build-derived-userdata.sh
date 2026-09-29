#!/bin/bash
set -Eeuo pipefail
shopt -s extglob

BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
source "$BASE/lib/loop-cleanup.sh"
INPUTS="$BASE/manifests/INPUTS.tsv"
PARTITIONS="$BASE/manifests/GOLDEN-PARTITIONS.tsv"
PROTECTED="$BASE/manifests/GOLDEN-PROTECTED.tsv"
IDENTITIES="$BASE/manifests/CRITICAL-IDENTITIES.tsv"
PROTECTED_PACKAGES="$BASE/manifests/PROTECTED-PACKAGES.tsv"
OUTPUT_DIR="$BASE/outputs"
SECTOR_SIZE=4096
BOOT_TYPE=c12a7328-f81f-11d2-ba4b-00a0c93ec93b
ROOT_TYPE=b921b045-1df0-41c3-af44-4c6f280d3fae
GOLDEN_DISK_GUID=20F69D00-01EF-4F28-98D5-152E69F32DDF
# The golden images and complete .deb cache are external inputs, never part of
# this versioned directory. Set these ARCHI_* variables explicitly per host.
GOLDEN_RAW=${ARCHI_GOLDEN_RAW:-}
GOLDEN_SPARSE=${ARCHI_GOLDEN_SPARSE:-}
DEB_CACHE=${ARCHI_DEB_CACHE:-}
DEB_ARCHIVE=${ARCHI_DEB_ARCHIVE:-}
LOCK_DIR=${ARCHI_LOCK_DIR:-"$BASE/../archi-validation-02-lock"}

PROFILE=
VERSION=
CHECK_ONLY=0
ENABLE_HOOKS=0
PROFILE_REQUIRES_HOOKS=no
BUILD_EPOCH=
STATE=
MOUNT_DIR=
LOOP_DEV=
ROOT_DEV=
BOOT_DEV=
ROOT_MOUNTED=0
POLICY_TOUCHED=0
POLICY_EXISTED=0
PACKAGE_STAGE=
OUTPUT_RAW_PART=
OUTPUT_SPARSE_PART=
OUTPUT_RAW_CREATED=0
OUTPUT_SPARSE_CREATED=0

usage() {
    cat <<'EOF'
Usage:
  build-derived-userdata.sh --profile NAME --version SUFFIX [--enable-hooks]
  build-derived-userdata.sh --profile NAME --version SUFFIX --check-only
  build-derived-userdata.sh --help

--check-only performs read-only input/profile/tool validation. A real build
requires root, creates a timestamped state directory, mounts only the copied
root partition and never mounts the embedded boot partition.
EOF
}

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
need_file() { [[ -f $1 ]] || fail "missing regular file: $1"; }
need_dir() { [[ -d $1 ]] || fail "missing directory: $1"; }
hash_file() { sha256sum "$1" | awk '{print $1}'; }

while (($#)); do
    case $1 in
        --profile) (($# >= 2)) || fail '--profile requires a value'; PROFILE=$2; shift 2 ;;
        --version) (($# >= 2)) || fail '--version requires a value'; VERSION=$2; shift 2 ;;
        --enable-hooks) ENABLE_HOOKS=1; shift ;;
        --check-only) CHECK_ONLY=1; shift ;;
        --help|-h) usage; exit 0 ;;
        *) fail "unknown argument: $1" ;;
    esac
done

[[ $PROFILE =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || fail 'invalid or missing profile name'
[[ $VERSION =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || fail 'invalid or missing output version/suffix'
PROFILE_DIR="$BASE/profiles/$PROFILE"
need_dir "$PROFILE_DIR"
need_file "$PROFILE_DIR/profile.conf"
need_file "$PROFILE_DIR/packages.install"
need_file "$PROFILE_DIR/packages.remove"
need_dir "$PROFILE_DIR/overlay/rootfs"
need_dir "$PROFILE_DIR/hooks.d"

profile_id=$(sed -n "s/^PROFILE_ID=//p" "$PROFILE_DIR/profile.conf")
[[ $profile_id == "$PROFILE" ]] || fail "profile.conf ID does not match $PROFILE"
profile_requires_hooks=$(sed -n 's/^PROFILE_REQUIRES_HOOKS=//p' "$PROFILE_DIR/profile.conf")
[[ -z $profile_requires_hooks ]] || PROFILE_REQUIRES_HOOKS=$profile_requires_hooks
[[ $PROFILE_REQUIRES_HOOKS == yes || $PROFILE_REQUIRES_HOOKS == no ]] || fail 'PROFILE_REQUIRES_HOOKS must be yes or no'
if [[ $PROFILE_REQUIRES_HOOKS == yes && $ENABLE_HOOKS == 0 ]]; then
    fail "profile $PROFILE requires explicit hook authorization (--enable-hooks)"
fi

for cmd in awk basename blkid cat chmod chroot cmp cp cut date dd diff dpkg-deb \
    dpkg-query e2fsck fdisk find findmnt grep img2simg install lsblk losetup mkdir mount mountpoint \
    mv od readlink rm sed sfdisk sha256sum simg2img sleep sort stat sync tail tar \
    tr umount unshare wc; do
    command -v "$cmd" >/dev/null || fail "required command unavailable: $cmd"
done

validate_specs() {
    local file=$1 kind=$2 line name version
    while IFS= read -r line || [[ -n $line ]]; do
        line=${line%%#*}
        line=${line%$'\r'}
        [[ $line =~ ^[[:space:]]*$ ]] && continue
        line=${line##+([[:space:]])}
        line=${line%%+([[:space:]])}
        if [[ $kind == install ]]; then
            [[ $line == *=* ]] || fail "packages.install requires package=version: $line"
            name=${line%%=*}; version=${line#*=}
            [[ $name =~ ^[a-z0-9][a-z0-9+.-]*$ && -n $version ]] || fail "invalid install spec: $line"
            awk -F '\t' -v p="$name" -v v="$version" 'NR>1 && $1==p && $2==v {n++} END{exit n==1?0:1}' \
                "$DEB_CACHE/PACKAGES.tsv" || fail "install spec is not uniquely locked: $line"
        else
            [[ $line =~ ^[a-z0-9][a-z0-9+.-]*$ ]] || fail "invalid remove spec: $line"
            awk -F '\t' -v p="$line" 'NR>1 && $1==p {n++} END{exit n==1?0:1}' \
                "$LOCK_DIR/PACKAGES.tsv" || fail "remove package is not uniquely present in golden lock: $line"
            ! awk -F '\t' -v p="$line" 'NR>1 && $1==p {found=1} END{exit found?0:1}' \
                "$PROTECTED_PACKAGES" || fail "refusing to remove protected display/GPU package: $line"
        fi
    done < "$file"
}

validate_overlay() {
    local entry rel target
    while IFS= read -r -d '' entry; do
        rel=${entry#"$PROFILE_DIR/overlay/rootfs/"}
        [[ $rel == .keep ]] && continue
        [[ $rel != /* && $rel != *'/../'* && $rel != ../* && $rel != */.. ]] || fail "unsafe overlay path: $rel"
        if [[ -L $entry ]]; then
            target=$(readlink "$entry")
            [[ $target != *$'\n'* ]] || fail "newline in overlay symlink target: $rel"
        elif [[ ! -f $entry && ! -d $entry ]]; then
            fail "unsupported overlay object (only file/directory/symlink): $rel"
        fi
    done < <(find "$PROFILE_DIR/overlay/rootfs" -mindepth 1 -print0)
}

validate_hooks() {
    local hook
    while IFS= read -r -d '' hook; do
        [[ $(basename "$hook") =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || fail "unsafe hook name: $hook"
        [[ -x $hook ]] || fail "profile hook is not executable: $hook"
        sh -n "$hook" || fail "profile hook has invalid POSIX shell syntax: $hook"
    done < <(find "$PROFILE_DIR/hooks.d" -maxdepth 1 -type f ! -name README.md -print0 | LC_ALL=C sort -z)
}

verify_input_file() {
    local path=$1 size=$2 sha=$3 actual
    need_file "$path"
    actual=$(stat -c %s "$path")
    [[ $actual == "$size" ]] || fail "size mismatch for $path: $actual, expected $size"
    actual=$(hash_file "$path")
    [[ $actual == "$sha" ]] || fail "SHA-256 mismatch for $path: $actual"
}

validate_gpt_file() {
    local image=$1 dump
    dump=$(sfdisk --sector-size "$SECTOR_SIZE" --dump "$image")
    printf '%s\n' "$dump" | grep -qx 'label: gpt' || fail "not GPT at 4096-byte sectors: $image"
    printf '%s\n' "$dump" | grep -qx "label-id: $GOLDEN_DISK_GUID" || fail "disk GUID mismatch: $image"
    printf '%s\n' "$dump" | grep -qx 'sector-size: 4096' || fail "GPT sector size mismatch: $image"
    [[ $(printf '%s\n' "$dump" | grep -c ' : start=') == 2 ]] || fail "expected exactly two GPT partitions: $image"
    printf '%s\n' "$dump" | grep -Eq 'start=[[:space:]]*2048, size=[[:space:]]*60416, type=C12A7328-F81F-11D2-BA4B-00A0C93EC93B, uuid=64337B4D-7BEA-4971-B03E-9083882C054C' || fail 'boot GPT entry mismatch'
    printf '%s\n' "$dump" | grep -Eq 'start=[[:space:]]*62464, size=[[:space:]]*1048576, type=B921B045-1DF0-41C3-AF44-4C6F280D3FAE, uuid=EF24217A-CF15-4F61-9633-CD279569A647' || fail 'root GPT entry mismatch'
}

validate_embedded_filesystems() {
    local image=$1 boot_off root_off boot_size root_size got
    boot_off=$((2048 * SECTOR_SIZE)); boot_size=$((60416 * SECTOR_SIZE))
    root_off=$((62464 * SECTOR_SIZE)); root_size=$((1048576 * SECTOR_SIZE))
    got=$(blkid -p -O "$boot_off" -S "$boot_size" -s UUID -o value "$image")
    [[ $got == 7bd723c2-51d6-4015-b28b-2b38191bf765 ]] || fail "embedded boot UUID mismatch: $got"
    got=$(blkid -p -O "$root_off" -S "$root_size" -s UUID -o value "$image")
    [[ $got == dba94dfe-0fb9-4f95-970e-22949f4e69dc ]] || fail "embedded root UUID mismatch: $got"
}

verify_deb_cache_readonly() {
    local p v a file
    [[ $(cat "$DEB_CACHE/STATUS") == COMPLETE ]] || fail 'deb cache STATUS is not COMPLETE'
    [[ $(hash_file "$DEB_CACHE/PACKAGES.tsv") == 95d8db66ae31759de0ea4179262693cf31779d41292401b50219878c0cb6b39d ]] || fail 'deb cache PACKAGES.tsv SHA mismatch'
    [[ $(hash_file "$DEB_CACHE/SOURCES.tsv") == e65c86154d2bb5f50be5672de5fed3f4ac3c5bbe7ceb9569b7ce8367fa4dee09 ]] || fail 'deb cache SOURCES.tsv SHA mismatch'
    [[ $(hash_file "$DEB_CACHE/SHA256SUMS") == c688fa2e17e849a006429b438664c88e931020b6794876869bcecede20028b4e ]] || fail 'deb cache SHA256SUMS manifest mismatch'
    [[ $(find "$DEB_CACHE" -maxdepth 1 -type f -name '*.deb' | wc -l) == 1086 ]] || fail 'deb cache does not contain exactly 1086 .deb files'
    [[ $(find "$DEB_CACHE" -maxdepth 1 -type f -name '*.part' | wc -l) == 0 ]] || fail 'deb cache contains .part files'
    cmp -s <(tail -n +2 "$DEB_CACHE/PACKAGES.tsv" | cut -f1-3) <(tail -n +2 "$LOCK_DIR/PACKAGES.tsv") || fail 'deb cache is not bijective with canonical package lock'
    while IFS=$'\t' read -r p v a file; do
        [[ $p == package ]] && continue
        need_file "$DEB_CACHE/$file"
        [[ $(dpkg-deb -f "$DEB_CACHE/$file" Package) == "$p" ]] || fail "deb Package mismatch: $file"
        [[ $(dpkg-deb -f "$DEB_CACHE/$file" Version) == "$v" ]] || fail "deb Version mismatch: $file"
        [[ $(dpkg-deb -f "$DEB_CACHE/$file" Architecture) == "$a" ]] || fail "deb Architecture mismatch: $file"
    done < "$DEB_CACHE/PACKAGES.tsv"
    (cd "$DEB_CACHE" && sha256sum -c SHA256SUMS --quiet) || fail 'deb cache payload SHA mismatch'
}

verify_lock_manifest_readonly() {
    local package_count package_sha
    need_dir "$LOCK_DIR"
    need_file "$LOCK_DIR/PACKAGES.tsv"
    need_file "$LOCK_DIR/SHA256SUMS"
    (cd "$LOCK_DIR" && sha256sum -c SHA256SUMS --quiet) || fail 'canonical lock text manifest SHA mismatch'
    package_count=$(tail -n +2 "$LOCK_DIR/PACKAGES.tsv" | wc -l | tr -d ' ')
    [[ $package_count == 1086 ]] || fail "canonical lock package count mismatch: $package_count"
    package_sha=$(tail -n +2 "$LOCK_DIR/PACKAGES.tsv" | sha256sum | awk '{print $1}')
    [[ $package_sha == 88e4cc3561749773188e22e05d4a997e539233f5dd67495af4b763473f84a0fc ]] ||
        fail "canonical lock package fingerprint mismatch: $package_sha"
}

check_inputs() {
    local cache_bytes sparse_magic
    [[ -n $GOLDEN_RAW && -n $GOLDEN_SPARSE && -n $DEB_CACHE && -n $DEB_ARCHIVE ]] ||
        fail 'set ARCHI_GOLDEN_RAW, ARCHI_GOLDEN_SPARSE, ARCHI_DEB_CACHE and ARCHI_DEB_ARCHIVE to external inputs'
    need_file "$INPUTS"; need_file "$PARTITIONS"; need_file "$PROTECTED"; need_file "$IDENTITIES"; need_file "$PROTECTED_PACKAGES"
    verify_input_file "$GOLDEN_RAW" 4551868416 329e2124f97032a2f4b15167bbd9bbbd9395bb422f2794a2117ee610a2368f27
    verify_input_file "$GOLDEN_SPARSE" 2960036280 84182b57edb7be8e49c29e0f0b472e9b6a54f7efa645ef99664dc0e004759f78
    verify_input_file "$DEB_ARCHIVE" 523274240 65058c4bc74c6aea3854060a8e7b9a7617ea6aee66d503d90564bcee214a69fd
    sparse_magic=$(od -An -tx1 -N4 "$GOLDEN_SPARSE" | tr -d ' \n')
    [[ $sparse_magic == 3aff26ed ]] || fail 'golden sparse Android magic mismatch'
    verify_lock_manifest_readonly
    need_dir "$DEB_CACHE"; verify_deb_cache_readonly
    cache_bytes=$(find "$DEB_CACHE" -maxdepth 1 -type f -name '*.deb' -printf '%s\n' | awk '{s+=$1} END{print s+0}')
    [[ $cache_bytes == 521861380 ]] || fail "locked .deb payload size mismatch: $cache_bytes"
    validate_gpt_file "$GOLDEN_RAW"
    validate_embedded_filesystems "$GOLDEN_RAW"
    validate_specs "$PROFILE_DIR/packages.install" install
    validate_specs "$PROFILE_DIR/packages.remove" remove
    validate_overlay
    validate_hooks
    "$BASE/verify-derived-userdata.sh" --manifest-only
}

if ((CHECK_ONLY)); then
    check_inputs
    printf 'OK: check-only passed for profile=%s version=%s; no image was copied or mounted\n' "$PROFILE" "$VERSION"
    exit 0
fi

[[ $(id -u) == 0 ]] || fail 'real builds require root (use --check-only for unprivileged validation)'
mkdir -p "$OUTPUT_DIR"
OUTPUT_RAW="$OUTPUT_DIR/archi-validation-02-derived-$VERSION.img"
OUTPUT_SPARSE="$OUTPUT_DIR/archi-validation-02-derived-$VERSION.img.android-sparse.img"
[[ ! -e $OUTPUT_RAW && ! -e $OUTPUT_SPARSE && ! -e $OUTPUT_RAW.part && ! -e $OUTPUT_SPARSE.part ]] || fail 'refusing to overwrite an output or .part file'
OUTPUT_RAW_PART=$OUTPUT_RAW.part
OUTPUT_SPARSE_PART=$OUTPUT_SPARSE.part
stamp=$(date -u +%Y%m%dT%H%M%SZ)
STATE="$BASE/state-$PROFILE-$VERSION-$stamp-$$"
[[ ! -e $STATE ]] || fail "state path already exists: $STATE"
mkdir -m 0700 "$STATE"
MOUNT_DIR="$STATE/rootfs"
mkdir -m 0700 "$MOUNT_DIR"
printf 'IN_PROGRESS\n' > "$STATE/STATUS"

restore_policy() {
    ((POLICY_TOUCHED)) || return 0
    if ((POLICY_EXISTED)); then
        rm -f -- "$MOUNT_DIR/usr/sbin/policy-rc.d"
        cp -a --no-dereference -- "$STATE/policy-rc.d.original" "$MOUNT_DIR/usr/sbin/policy-rc.d"
    else
        rm -f -- "$MOUNT_DIR/usr/sbin/policy-rc.d"
    fi
    POLICY_TOUCHED=0
}

root_mount_is_owned() {
    local mounted_source
    mountpoint -q -- "$MOUNT_DIR" || return 1
    [[ -n $ROOT_DEV ]] || return 2
    mounted_source=$(findmnt -nro SOURCE --target "$MOUNT_DIR") || return 2
    [[ $mounted_source == "$ROOT_DEV" ]]
}

unmount_owned_root() {
    local rc
    if ! mountpoint -q -- "$MOUNT_DIR"; then
        ROOT_MOUNTED=0
        return 0
    fi
    if root_mount_is_owned; then
        :
    else
        rc=$?
        printf 'ERROR: root mount ownership cannot be proven; leaving it mounted\n' >&2
        return "$((rc == 1 ? 1 : rc))"
    fi
    sync -f "$MOUNT_DIR" || return 1
    umount -- "$MOUNT_DIR" || return 1
    ROOT_MOUNTED=0
}

cleanup() {
    local rc=$? cleanup_failed=0
    trap - EXIT HUP INT TERM
    set +e
    if mountpoint -q -- "$MOUNT_DIR"; then
        if root_mount_is_owned; then
            [[ -z $PACKAGE_STAGE ]] || rm -rf -- "$MOUNT_DIR$PACKAGE_STAGE"
            restore_policy || cleanup_failed=1
            unmount_owned_root || cleanup_failed=1
        else
            printf 'ERROR: refusing cleanup of a mount not attributable to this attempt\n' >&2
            cleanup_failed=1
        fi
    else
        ROOT_MOUNTED=0
        ((POLICY_TOUCHED == 0)) || cleanup_failed=1
    fi
    detach_owned_loop || cleanup_failed=1
    [[ -z $OUTPUT_RAW_PART ]] || rm -f -- "$OUTPUT_RAW_PART"
    [[ -z $OUTPUT_SPARSE_PART ]] || rm -f -- "$OUTPUT_SPARSE_PART"
    if ((rc != 0)); then
        ((OUTPUT_RAW_CREATED == 0)) || rm -f -- "$OUTPUT_RAW"
        ((OUTPUT_SPARSE_CREATED == 0)) || rm -f -- "$OUTPUT_SPARSE"
    fi
    if ((rc != 0 || cleanup_failed)); then
        printf 'FAILED rc=%s cleanup_failed=%s\n' "$rc" "$cleanup_failed" > "$STATE/STATUS"
    fi
    ((rc != 0)) && exit "$rc"
    ((cleanup_failed == 0)) || exit 1
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

check_inputs
if ((ENABLE_HOOKS)); then
    BUILD_EPOCH=$(date -u +%s)
    [[ $BUILD_EPOCH =~ ^[0-9]{1,12}$ ]] || fail "host returned an invalid UTC build epoch: $BUILD_EPOCH"
    printf '%s\n' "$BUILD_EPOCH" > "$STATE/build-epoch.txt"
fi
WORK_RAW="$STATE/working.img"
cp --reflink=auto -- "$GOLDEN_RAW" "$WORK_RAW"
[[ $(hash_file "$WORK_RAW") == 329e2124f97032a2f4b15167bbd9bbbd9395bb422f2794a2117ee610a2368f27 ]] || fail 'working reflink copy differs from golden'

attach_work_loop || fail 'losetup failed or returned a path that cannot be safely attributed to this working image'
[[ -b $LOOP_DEV ]] || fail 'losetup did not return a block device'
for _ in {1..20}; do
    mapfile -t boot_matches < <(lsblk -nrpo NAME,TYPE,PARTTYPE "$LOOP_DEV" | awk -v t="$BOOT_TYPE" 'tolower($2)=="part" && tolower($3)==t {print $1}')
    mapfile -t root_matches < <(lsblk -nrpo NAME,TYPE,PARTTYPE "$LOOP_DEV" | awk -v t="$ROOT_TYPE" 'tolower($2)=="part" && tolower($3)==t {print $1}')
    ((${#boot_matches[@]} == 1 && ${#root_matches[@]} == 1)) && break
    sleep 0.1
done
((${#boot_matches[@]} == 1)) || fail 'GPT must expose exactly one EFI/boot partition'
((${#root_matches[@]} == 1)) || fail 'GPT must expose exactly one ARM64 root partition'
BOOT_DEV=${boot_matches[0]}; ROOT_DEV=${root_matches[0]}
[[ $(lsblk -dnro PARTUUID "$BOOT_DEV" | tr '[:lower:]' '[:upper:]') == 64337B4D-7BEA-4971-B03E-9083882C054C ]] || fail 'boot PARTUUID mismatch'
[[ $(lsblk -dnro PARTUUID "$ROOT_DEV" | tr '[:lower:]' '[:upper:]') == EF24217A-CF15-4F61-9633-CD279569A647 ]] || fail 'root PARTUUID mismatch'
[[ $(blkid -s UUID -o value "$BOOT_DEV") == 7bd723c2-51d6-4015-b28b-2b38191bf765 ]] || fail 'boot filesystem UUID mismatch'
[[ $(blkid -s UUID -o value "$ROOT_DEV") == dba94dfe-0fb9-4f95-970e-22949f4e69dc ]] || fail 'root filesystem UUID mismatch'
sha256sum "$BOOT_DEV" > "$STATE/boot-before.sha256"
[[ $(awk '{print $1}' "$STATE/boot-before.sha256") == 6e2a1555a629126907c452a455ba12e78ee7e3862bbc39e376215569d9e7e03b ]] || fail 'embedded boot partition differs from golden'
sfdisk --dump "$LOOP_DEV" > "$STATE/gpt-before.sfdisk"

ROOT_MOUNTED=1
mount -t ext4 -o rw,nodev,nosuid -- "$ROOT_DEV" "$MOUNT_DIR"
[[ $(findmnt -nro SOURCE --target "$MOUNT_DIR") == "$ROOT_DEV" ]] || fail 'unexpected rootfs mount source'
[[ $(findmnt -nro FSTYPE --target "$MOUNT_DIR") == ext4 ]] || fail 'unexpected rootfs mount type'
if findmnt -rn -S "$BOOT_DEV" | grep -q .; then fail 'embedded boot partition must never be mounted'; fi

snapshot_protected() {
    local root=$1 out=$2 path type mode uid gid link expected_sha obj actual
    printf 'target_path\ttype\tmode\tuid\tgid\tlink_target\tsha256\n' > "$out"
    tail -n +2 "$PROTECTED" | while IFS=$'\t' read -r path type mode uid gid link expected_sha; do
        obj=$root$path
        [[ -e $obj || -L $obj ]] || fail "protected object missing: $path"
        actual=$(stat -c %a "$obj"); [[ $actual == "$mode" ]] || fail "protected mode mismatch: $path ($actual)"
        actual=$(stat -c %u "$obj"); [[ $actual == "$uid" ]] || fail "protected uid mismatch: $path ($actual)"
        actual=$(stat -c %g "$obj"); [[ $actual == "$gid" ]] || fail "protected gid mismatch: $path ($actual)"
        if [[ $type == file ]]; then
            [[ -f $obj && ! -L $obj ]] || fail "protected object is not a regular file: $path"
            actual=$(hash_file "$obj"); [[ $actual == "$expected_sha" ]] || fail "protected SHA mismatch: $path"
            printf '%s\tfile\t%s\t%s\t%s\t-\t%s\n' "$path" "$mode" "$uid" "$gid" "$actual" >> "$out"
        elif [[ $type == link ]]; then
            [[ -L $obj ]] || fail "protected object is not a symlink: $path"
            actual=$(readlink "$obj"); [[ $actual == "$link" ]] || fail "protected link mismatch: $path"
            printf '%s\tlink\t%s\t%s\t%s\t%s\t-\n' "$path" "$mode" "$uid" "$gid" "$actual" >> "$out"
        else fail "unsupported protected type: $type"; fi
    done
}

snapshot_identities() {
    local root=$1 out=$2 db name expected actual file
    cp -- "$IDENTITIES" "$out"
    tail -n +2 "$IDENTITIES" | while IFS=$'\t' read -r db name expected; do
        case $db in passwd) file=$root/etc/passwd ;; group) file=$root/etc/group ;; *) fail "unknown identity database: $db" ;; esac
        actual=$(awk -F: -v n="$name" '$1==n {print; c++} END{if(c!=1)exit 1}' "$file") || fail "identity absent or duplicated: $db/$name"
        [[ $actual == "$expected" ]] || fail "critical identity changed: $db/$name"
    done
}

package_inventory() {
    dpkg-query --admindir="$MOUNT_DIR/var/lib/dpkg" -W -f='${Package}\t${Version}\t${Architecture}\n' | LC_ALL=C sort -t $'\t' -k1,1 -k3,3 -k2,2 > "$1"
}

verify_protected_packages() {
    local inventory=$1 p v a
    tail -n +2 "$PROTECTED_PACKAGES" | while IFS=$'\t' read -r p v a; do
        awk -F '\t' -v p="$p" -v v="$v" -v a="$a" '$1==p && $2==v && $3==a {found=1} END{exit found?0:1}' \
            "$inventory" || fail "protected package identity changed: $p=$v/$a"
    done
}

snapshot_protected "$MOUNT_DIR" "$STATE/protected-before.tsv"
snapshot_identities "$MOUNT_DIR" "$STATE/identities-before.tsv"
package_inventory "$STATE/packages-before.tsv"
cmp -s "$STATE/packages-before.tsv" <(tail -n +2 "$LOCK_DIR/PACKAGES.tsv" | LC_ALL=C sort -t $'\t' -k1,1 -k3,3 -k2,2) || fail 'mounted golden package inventory differs from canonical lock'
verify_protected_packages "$STATE/packages-before.tsv"

install_specs=(); remove_specs=()
while IFS= read -r line || [[ -n $line ]]; do
    line=${line%%#*}; line=${line%$'\r'}; [[ $line =~ ^[[:space:]]*$ ]] && continue
    line=${line##+([[:space:]])}; line=${line%%+([[:space:]])}; install_specs+=("$line")
done < "$PROFILE_DIR/packages.install"
while IFS= read -r line || [[ -n $line ]]; do
    line=${line%%#*}; line=${line%$'\r'}; [[ $line =~ ^[[:space:]]*$ ]] && continue
    line=${line##+([[:space:]])}; line=${line%%+([[:space:]])}; remove_specs+=("$line")
done < "$PROFILE_DIR/packages.remove"

if ((${#install_specs[@]} || ${#remove_specs[@]})); then
    unshare --net -- chroot "$MOUNT_DIR" /bin/true || fail 'aarch64 chroot/binfmt is unavailable for offline package operations'
    mkdir -p "$MOUNT_DIR/usr/sbin"
    if [[ -e $MOUNT_DIR/usr/sbin/policy-rc.d || -L $MOUNT_DIR/usr/sbin/policy-rc.d ]]; then
        cp -a --no-dereference -- "$MOUNT_DIR/usr/sbin/policy-rc.d" "$STATE/policy-rc.d.original"
        POLICY_EXISTED=1
    fi
    printf '#!/bin/sh\nexit 101\n' > "$MOUNT_DIR/usr/sbin/policy-rc.d"
    chmod 0755 "$MOUNT_DIR/usr/sbin/policy-rc.d"
    POLICY_TOUCHED=1
    PACKAGE_STAGE=/var/tmp/archi-derived-packages-$$
    mkdir -m 0700 "$MOUNT_DIR$PACKAGE_STAGE"
    if ((${#remove_specs[@]})); then
        unshare --net -- chroot "$MOUNT_DIR" /usr/bin/dpkg --remove -- "${remove_specs[@]}"
    fi
    debs=()
    for spec in "${install_specs[@]}"; do
        name=${spec%%=*}; version=${spec#*=}
        file=$(awk -F '\t' -v p="$name" -v v="$version" 'NR>1 && $1==p && $2==v {print $4}' "$DEB_CACHE/PACKAGES.tsv")
        [[ -n $file && -f $DEB_CACHE/$file ]] || fail "locked .deb unavailable for $spec"
        cp --reflink=auto -- "$DEB_CACHE/$file" "$MOUNT_DIR$PACKAGE_STAGE/$file"
        debs+=("$PACKAGE_STAGE/$file")
    done
    if ((${#debs[@]})); then unshare --net -- chroot "$MOUNT_DIR" /usr/bin/dpkg --install -- "${debs[@]}"; fi
    unshare --net -- chroot "$MOUNT_DIR" /usr/bin/dpkg --configure --pending
    rm -rf -- "$MOUNT_DIR$PACKAGE_STAGE"; PACKAGE_STAGE=
    restore_policy
fi

# Apply only declared overlay content; .keep is bookkeeping, not rootfs data.
if find "$PROFILE_DIR/overlay/rootfs" -mindepth 1 ! -name .keep -print -quit | grep -q .; then
    tar -C "$PROFILE_DIR/overlay/rootfs" --exclude='./.keep' -cf - . | tar -C "$MOUNT_DIR" -xpf -
fi

if ((ENABLE_HOOKS)); then
    mapfile -d '' hooks < <(find "$PROFILE_DIR/hooks.d" -maxdepth 1 -type f -perm /111 ! -name README.md -print0 | LC_ALL=C sort -z)
    for hook in "${hooks[@]}"; do
        hook_name=$(basename "$hook")
        [[ $hook_name =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || fail "unsafe hook name: $hook_name"
        hook_target=/var/tmp/archi-derived-hook-$hook_name
        install -m 0700 -- "$hook" "$MOUNT_DIR$hook_target"
        unshare --net -- chroot "$MOUNT_DIR" /usr/bin/env DERIVED_PROFILE="$PROFILE" DERIVED_VERSION="$VERSION" DERIVED_BUILD_EPOCH="$BUILD_EPOCH" /bin/sh "$hook_target"
        rm -f -- "$MOUNT_DIR$hook_target"
    done
else
    if find "$PROFILE_DIR/hooks.d" -maxdepth 1 -type f -perm /111 -print -quit | grep -q .; then
        printf 'NOTICE: executable hooks exist but are disabled; use --enable-hooks only after review\n' >&2
    fi
fi

snapshot_protected "$MOUNT_DIR" "$STATE/protected-after.tsv"
snapshot_identities "$MOUNT_DIR" "$STATE/identities-after.tsv"
cmp -s "$STATE/protected-before.tsv" "$STATE/protected-after.tsv" || fail 'a protected GPU/display artifact changed'
cmp -s "$STATE/identities-before.tsv" "$STATE/identities-after.tsv" || fail 'a critical account/group identity changed'
package_inventory "$STATE/packages-after.tsv"
verify_protected_packages "$STATE/packages-after.tsv"

printf '%s\n' "${install_specs[@]%%=*}" "${remove_specs[@]}" | sed '/^$/d' | LC_ALL=C sort -u > "$STATE/allowed-package-names.txt"
awk -F '\t' 'FILENAME==ARGV[1] {allowed[$1]=1; next} FILENAME==ARGV[2] {before[$1]=$2 FS $3; next} {after[$1]=$2 FS $3} END {for(n in before) if(before[n]!=after[n] && !allowed[n]) exit 1; for(n in after) if(before[n]!=after[n] && !allowed[n]) exit 1}' \
    "$STATE/allowed-package-names.txt" "$STATE/packages-before.tsv" "$STATE/packages-after.tsv" || fail 'package inventory changed outside declared package names'
for spec in "${install_specs[@]}"; do
    name=${spec%%=*}; version=${spec#*=}
    awk -F '\t' -v p="$name" -v v="$version" '$1==p && $2==v {found=1} END{exit found?0:1}' "$STATE/packages-after.tsv" || fail "requested package/version not installed: $spec"
done
for name in "${remove_specs[@]}"; do
    ! awk -F '\t' -v p="$name" '$1==p {found=1} END{exit found?0:1}' "$STATE/packages-after.tsv" || fail "requested package still installed: $name"
done

unmount_owned_root || fail 'could not safely unmount the copied rootfs'
e2fsck -fn "$ROOT_DEV" > "$STATE/e2fsck.txt" 2>&1 || fail "read-only ext4 check failed; see $STATE/e2fsck.txt"
[[ $(blkid -s UUID -o value "$ROOT_DEV") == dba94dfe-0fb9-4f95-970e-22949f4e69dc ]] || fail 'root UUID changed'
[[ $(blkid -s UUID -o value "$BOOT_DEV") == 7bd723c2-51d6-4015-b28b-2b38191bf765 ]] || fail 'boot UUID changed'
sha256sum "$BOOT_DEV" > "$STATE/boot-after.sha256"
cmp -s "$STATE/boot-before.sha256" "$STATE/boot-after.sha256" || fail 'embedded boot partition changed'
sfdisk --dump "$LOOP_DEV" > "$STATE/gpt-after.sfdisk"
cmp -s "$STATE/gpt-before.sfdisk" "$STATE/gpt-after.sfdisk" || fail 'GPT changed'
detach_owned_loop || fail 'could not safely detach the working-image loop device'

mv -- "$WORK_RAW" "$OUTPUT_RAW_PART"
raw_size=$(stat -c %s "$OUTPUT_RAW_PART"); raw_sha=$(hash_file "$OUTPUT_RAW_PART")
img2simg "$OUTPUT_RAW_PART" "$OUTPUT_SPARSE_PART" "$SECTOR_SIZE"
roundtrip="$STATE/sparse-roundtrip.raw"
simg2img "$OUTPUT_SPARSE_PART" "$roundtrip"
roundtrip_sha=$(hash_file "$roundtrip")
[[ $roundtrip_sha == "$raw_sha" ]] || fail 'Android sparse round-trip differs from derived raw'
rm -f -- "$roundtrip"
printf '%s  %s\n' "$roundtrip_sha" "$(basename "$OUTPUT_RAW")" > "$STATE/sparse-roundtrip.sha256"
sparse_size=$(stat -c %s "$OUTPUT_SPARSE_PART"); sparse_sha=$(hash_file "$OUTPUT_SPARSE_PART")
mv -- "$OUTPUT_RAW_PART" "$OUTPUT_RAW"; OUTPUT_RAW_PART=; OUTPUT_RAW_CREATED=1
mv -- "$OUTPUT_SPARSE_PART" "$OUTPUT_SPARSE"; OUTPUT_SPARSE_PART=; OUTPUT_SPARSE_CREATED=1
printf 'role\tpath\tsize_bytes\tsha256\nraw\t%s\t%s\t%s\nsparse\t%s\t%s\t%s\n' \
    "$OUTPUT_RAW" "$raw_size" "$raw_sha" "$OUTPUT_SPARSE" "$sparse_size" "$sparse_sha" > "$STATE/OUTPUTS.tsv"
printf '%s  %s\n%s  %s\n' "$raw_sha" "$OUTPUT_RAW" "$sparse_sha" "$OUTPUT_SPARSE" > "$STATE/SHA256SUMS.outputs"
printf 'COMPLETE\n' > "$STATE/STATUS"
"$BASE/verify-derived-userdata.sh" --state "$STATE"
OUTPUT_RAW_CREATED=0; OUTPUT_SPARSE_CREATED=0
printf 'DONE: raw=%s\nDONE: sparse=%s\nDONE: state=%s\n' "$OUTPUT_RAW" "$OUTPUT_SPARSE" "$STATE"
