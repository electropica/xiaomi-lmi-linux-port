#!/bin/sh
set -eu

LOCK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOTFS=${ARCHI_ROOTFS:-/home/linuxagent/ProjetMobian/output/archi-validation-02-work/rootfs}
TAB=$(printf '\t')
EXPECTED_PACKAGE_COUNT=1086
EXPECTED_PACKAGE_SHA=88e4cc3561749773188e22e05d4a997e539233f5dd67495af4b763473f84a0fc
EXPECTED_APT_EXTENDED_SHA=e70a69400b30ef04d9746542fefce728452831b058cf240efc52e80ac7ebf72f

case ${1:---manifest-only} in
	--manifest-only) MODE=manifest ;;
	--full) MODE=full ;;
	*)
		printf 'Usage: %s [--manifest-only|--full]\n' "$0" >&2
		exit 2
		;;
esac
[ "$#" -le 1 ] || {
	printf 'Usage: %s [--manifest-only|--full]\n' "$0" >&2
	exit 2
}

fail() {
	printf 'ERROR: %s\n' "$*" >&2
	exit 1
}

need_file() {
	[ -f "$1" ] || fail "missing regular file: $1"
}

hash_file() {
	sha256sum "$1" | awk '{print $1}'
}

check_sorted_body() {
	file=$1
	keys=$2
	tail -n +2 "$file" | LC_ALL=C sort -c -t "$TAB" $keys 2>/dev/null ||
		fail "unstable or unsorted body: $file"
}

for name in README.md ARTIFACTS.tsv PACKAGES.tsv APT-SOURCES.txt \
	LOCAL-FILES.tsv SYSTEMD-UNITS.tsv GPU72.tsv BOOT-USERSPACE-CONTRACT.md \
	EXCLUSIONS.md verify-archi-validation-02-lock.sh SHA256SUMS; do
	need_file "$LOCK_DIR/$name"
done
for name in README.md DEB-CACHE-PRESENT.tsv DEB-CACHE-MISSING.tsv \
	DEB-DOWNLOAD-PLAN.tsv DEB-UNRESOLVED-PLAN.tsv PACKAGES.tsv SOURCES.tsv \
	SHA256SUMS STATUS verify-deb-cache.sh; do
	need_file "$LOCK_DIR/deb-cache/$name"
done

# The lock is metadata only: no large payload, symlink, device, socket or FIFO.
# The single deb-cache directory groups the package provenance manifests.
find "$LOCK_DIR" -mindepth 1 ! -type f ! -path "$LOCK_DIR/deb-cache" -print | grep -q . &&
	fail "non-regular entry found in lock directory"
large=$(find "$LOCK_DIR" -type f -size +10M -print)
[ -z "$large" ] || fail "large payload found in lock directory: $large"

# Reject secret material, not ordinary documentation that names excluded classes.
if grep -RIE 'BEGIN (OPENSSH|RSA|EC|DSA) PRIVATE KEY' "$LOCK_DIR" >/dev/null; then
	fail "private key material found"
fi
if grep -RIE --exclude=EXCLUSIONS.md --exclude=verify-archi-validation-02-lock.sh \
	'(^|[^A-Za-z])(psk|password|passwd|pin)[[:space:]]*=' "$LOCK_DIR" >/dev/null; then
	fail "possible secret material found"
fi
if grep -E '/(\.ssh|shadow)(/|$)|/etc/NetworkManager/system-connections/|/etc/machine-id|/var/(log|cache|lib/systemd/coredump)/|^/run/' \
	"$LOCK_DIR/LOCAL-FILES.tsv" "$LOCK_DIR/GPU72.tsv" >/dev/null; then
	fail "forbidden persistent or secret-bearing path listed"
fi

[ "$(head -n 1 "$LOCK_DIR/PACKAGES.tsv")" = "package${TAB}version${TAB}architecture" ] ||
	fail "invalid PACKAGES.tsv header"
package_count=$(tail -n +2 "$LOCK_DIR/PACKAGES.tsv" | wc -l | tr -d ' ')
[ "$package_count" -eq "$EXPECTED_PACKAGE_COUNT" ] ||
	fail "PACKAGES.tsv has $package_count packages, expected $EXPECTED_PACKAGE_COUNT"
check_sorted_body "$LOCK_DIR/PACKAGES.tsv" '-k1,1 -k3,3 -k2,2'
package_sha=$(tail -n +2 "$LOCK_DIR/PACKAGES.tsv" | sha256sum | awk '{print $1}')
[ "$package_sha" = "$EXPECTED_PACKAGE_SHA" ] ||
	fail "package inventory fingerprint mismatch: $package_sha"

check_sorted_body "$LOCK_DIR/ARTIFACTS.tsv" '-k1,1 -k2,2'
check_sorted_body "$LOCK_DIR/LOCAL-FILES.tsv" '-k1,1'
check_sorted_body "$LOCK_DIR/SYSTEMD-UNITS.tsv" '-k1,1 -k2,2'
check_sorted_body "$LOCK_DIR/GPU72.tsv" '-k1,1 -k2,2'

awk -F '\t' 'NR == 1 { next } NF != 5 { exit 1 }' "$LOCK_DIR/ARTIFACTS.tsv" ||
	fail "ARTIFACTS.tsv field count mismatch"
awk -F '\t' 'NR == 1 { next } NF != 9 { exit 1 }' "$LOCK_DIR/LOCAL-FILES.tsv" ||
	fail "LOCAL-FILES.tsv field count mismatch"
awk -F '\t' 'NR == 1 { next } NF != 9 { exit 1 }' "$LOCK_DIR/SYSTEMD-UNITS.tsv" ||
	fail "SYSTEMD-UNITS.tsv field count mismatch"
awk -F '\t' 'NR == 1 { next } NF != 8 { exit 1 }' "$LOCK_DIR/GPU72.tsv" ||
	fail "GPU72.tsv field count mismatch"

if [ "$MODE" = full ]; then
	[ -d "$ROOTFS" ] || fail "offline extracted rootfs unavailable: $ROOTFS"

	tail -n +2 "$LOCK_DIR/ARTIFACTS.tsv" |
	while IFS="$TAB" read -r role path expected_size expected_sha availability; do
		[ "$availability" = present ] || continue
		need_file "$path"
		actual_size=$(stat -c %s "$path")
		[ "$actual_size" = "$expected_size" ] ||
			fail "$role size mismatch for $path: $actual_size"
		actual_sha=$(hash_file "$path")
		[ "$actual_sha" = "$expected_sha" ] ||
			fail "$role SHA-256 mismatch for $path: $actual_sha"
	done

	validated_sparse=$(awk -F '\t' '$1 == "validated_userdata_sparse" { print $2 }' "$LOCK_DIR/ARTIFACTS.tsv")
	root_ext4=$(awk -F '\t' '$1 == "root_ext4" { print $2 }' "$LOCK_DIR/ARTIFACTS.tsv")
	[ -n "$validated_sparse" ] || fail "validated_userdata_sparse role absent"
	[ -n "$root_ext4" ] || fail "root_ext4 role absent"
	sparse_magic=$(od -An -tx1 -N4 "$validated_sparse" | tr -d ' \n')
	[ "$sparse_magic" = 3aff26ed ] || fail "userdata is not Android sparse v1 magic"
	root_type=$(blkid -s TYPE -o value "$root_ext4")
	[ "$root_type" = ext4 ] || fail "root filesystem image is not ext4"
	root_uuid=$(blkid -s UUID -o value "$root_ext4")
	[ "$root_uuid" = dba94dfe-0fb9-4f95-970e-22949f4e69dc ] ||
		fail "root filesystem UUID mismatch: $root_uuid"

	tail -n +2 "$LOCK_DIR/LOCAL-FILES.tsv" |
	while IFS="$TAB" read -r target type mode uid gid owner group link_target file_sha; do
	source=$ROOTFS$target
	[ -e "$source" ] || [ -L "$source" ] || fail "local target absent from offline rootfs: $target"
	actual_mode=$(stat -c %a "$source")
	[ "$actual_mode" = "$mode" ] || fail "mode mismatch for $target: $actual_mode"
	case $type in
		file)
			[ -f "$source" ] && [ ! -L "$source" ] || fail "expected regular file: $target"
			actual=$(hash_file "$source")
			[ "$actual" = "$file_sha" ] || fail "SHA-256 mismatch for $target: $actual"
			;;
		link|symlink)
			[ -L "$source" ] || fail "expected symlink: $target"
			actual=$(readlink "$source")
			[ "$actual" = "$link_target" ] || fail "symlink target mismatch for $target: $actual"
			;;
		*) fail "unsupported LOCAL-FILES.tsv type for $target: $type" ;;
	esac
	# The extracted rootfs uses a user namespace: host UID/GID 1001 map to target root.
	host_uid=$(stat -c %u "$source")
	host_gid=$(stat -c %g "$source")
	if [ "$uid" = 0 ]; then [ "$host_uid" = 0 ] || [ "$host_uid" = 1001 ] || fail "UID mismatch for $target: $host_uid"; fi
	if [ "$gid" = 0 ]; then [ "$host_gid" = 0 ] || [ "$host_gid" = 1001 ] || fail "GID mismatch for $target: $host_gid"; fi
	[ "$owner" = root ] || fail "unexpected target owner for $target: $owner"
	[ "$group" = root ] || fail "unexpected target group for $target: $group"
done

	tail -n +2 "$LOCK_DIR/GPU72.tsv" |
	while IFS="$TAB" read -r class target type mode uid gid link_or_value file_sha; do
	case $class in
		runtime|firmware)
			file=$ROOTFS$target
			[ -e "$file" ] || [ -L "$file" ] || fail "GPU72 target absent: $target"
			actual_mode=$(stat -c %a "$file")
			[ "$actual_mode" = "$mode" ] || fail "GPU72 mode mismatch for $target: $actual_mode"
			if [ "$type" = file ]; then
				actual=$(hash_file "$file")
				[ "$actual" = "$file_sha" ] || fail "GPU72 SHA-256 mismatch for $target: $actual"
			elif [ "$type" = link ] || [ "$type" = symlink ]; then
				actual=$(readlink "$file")
				[ "$actual" = "$link_or_value" ] || fail "GPU72 link mismatch for $target: $actual"
			else
				fail "unsupported GPU72 type for $target: $type"
			fi
			;;
		source)
			case $link_or_value in
				http://*|https://*) : ;;
				*)
					need_file "$link_or_value"
					actual=$(hash_file "$link_or_value")
					[ "$actual" = "$file_sha" ] || fail "GPU72 source SHA-256 mismatch for $link_or_value: $actual"
					;;
			esac
			;;
		environment|device|account) : ;;
		*) fail "unknown GPU72 class: $class" ;;
	esac
done

	apt_extended=$ROOTFS/var/lib/apt/extended_states
	need_file "$apt_extended"
	[ "$(hash_file "$apt_extended")" = "$EXPECTED_APT_EXTENDED_SHA" ] ||
		fail "APT extended_states fingerprint mismatch"
fi

(cd "$LOCK_DIR" && sha256sum -c SHA256SUMS)
printf 'OK: archi-validation-02 reproduction lock verified offline (%s mode)\n' "$MODE"
printf 'OK: packages=%s package-body-sha256=%s\n' "$package_count" "$package_sha"
if [ "$MODE" = full ]; then
	printf 'OK: rootfs-uuid=%s\n' "$root_uuid"
fi
