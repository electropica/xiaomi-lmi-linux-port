#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
ROOT=${AUDIO_DIAG_ROOT:-$ROOT}
PROJECT_ROOT=${AUDIO_DIAG_PROJECT_ROOT:-$(cd -- "$ROOT/../../.." && pwd -P)}
I=${AUDIO_DIAG_INPUT_DIR:-$ROOT/inputs}
P="$ROOT/patches/0001-lmi-wcd938x-rx-soundwire-diagnostic.patch"
P4="$PROJECT_ROOT/kernel/patches/audio/0001-lmi-wcd938x-reset-gpio-mux.patch"
SRC=${AUDIO_DIAG_SOURCE_DIR:-$ROOT/source-a5b3099017ae}
CFG=${AUDIO_DIAG_CONFIG:-$PROJECT_ROOT/kernel/configs/dv43-qca6390-v2.config}
P1="$PROJECT_ROOT/kernel/patches/0001-mobian-add-boot-safe-QCA6390-UART-support-and-restor.patch"
P2="$PROJECT_ROOT/kernel/patches/0002-esoc-preserve-crash-state-on-late-run-notification.patch"
BOOT="$I/D-repro-01-kernel-Dv43-qca6390-v2-complete-fcsource-boot.img"
ARCHIVE="$I/linux-xiaomi-lmi-a5b3099017ae581aae8bf597b2f9c8c765026af1.tar.gz"
TOOLS=${AUDIO_DIAG_MKBOOTIMG_TOOLS:-}
UNPACKER=${AUDIO_DIAG_UNPACK_BOOTIMG:-${TOOLS:+$TOOLS/unpack_bootimg}}
MKBOOTIMG=${AUDIO_DIAG_MKBOOTIMG:-${TOOLS:+$TOOLS/mkbootimg}}
OUTPUT_DIR=${AUDIO_DIAG_OUTPUT_DIR:-$ROOT/outputs}
STATE_ROOT=${AUDIO_DIAG_STATE_DIR:-$ROOT/state-audio}
OUTPUT_NAME=${AUDIO_DIAG_OUTPUT_NAME:-D-repro-01-audio-swr-diagnostic-boot.img}
OUT="$OUTPUT_DIR/$OUTPUT_NAME"
EXPECTED_DIAG=2d5c2188356b0708ebf88b6a2694b216b4ccb62e6e8ab74124a53ea96d3b6e79
EXPECTED_RESET=1d1859556bb05c207b70225ecccc922c9338eff485f729012abc41ba75fbfef7
EXPECTED_CONFIG=6512a0c29ebf987d25c0cceb79917df32d6fed4b67e4c3b94bfad9fdb1745e37
RESET_GPIO=${AUDIO_DIAG_RESET_GPIO:-0}
[[ $RESET_GPIO == 0 || $RESET_GPIO == 1 ]] || { printf 'ERROR: AUDIO_DIAG_RESET_GPIO must be 0 or 1\n' >&2; exit 1; }

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
sha_of() { sha256sum -- "$1" | awk '{print $1}'; }
sha_is() { [[ -f $2 ]] || die "missing $2"; [[ $(sha_of "$2") == "$1" ]] || die "SHA-256 mismatch: $2"; }
need() { command -v "$1" >/dev/null 2>&1 || die "missing command: $1"; }
usage() { printf 'Usage: bash %s [--help|--preflight|--check-only]\n' "${BASH_SOURCE[0]}"; }

# Keep this selector in sync with run-native-kconfig-check.sh. Validate
# symlink targets as they resolve inside the chroot, not against host /.
apk_package_version() {
	local database=$1 package=$2
	awk -v wanted="$package" '
		BEGIN { RS = "" }
		{
			name = version = ""
			n = split($0, lines, "\n")
			for (i = 1; i <= n; i++) {
				if (lines[i] ~ /^P:/) name = substr(lines[i], 3)
				if (lines[i] ~ /^V:/) version = substr(lines[i], 3)
			}
			if (name == wanted) { print version; found = 1; exit }
		}
		END { if (!found) exit 1 }
	' "$database"
}

native_chroot_complete() {
	local root=$1 database
	[[ -d $root && -d $root/usr/bin && -d $root/usr/lib/llvm22/bin ]] || return 1
	[[ -L $root/bin && $(readlink -- "$root/bin") == usr/bin ]] || return 1
	[[ -L $root/usr/bin/sh && $(readlink -- "$root/usr/bin/sh") == /bin/busybox && -x $root/usr/bin/busybox ]] || return 1
	[[ -x $root/lib/ld-musl-x86_64.so.1 ]] || return 1
	[[ -L $root/usr/bin/clang && $(readlink -- "$root/usr/bin/clang") == ../lib/llvm22/bin/clang ]] || return 1
	[[ -x $root/usr/lib/llvm22/bin/clang && -x $root/usr/lib/llvm22/bin/clang-22 ]] || return 1
	[[ -x $root/usr/bin/ld.lld && -x $root/usr/bin/gcc && -x $root/usr/bin/g++ ]] || return 1
	[[ -x $root/usr/bin/make && -x $root/usr/bin/bison && -x $root/usr/bin/flex ]] || return 1
	database=$root/lib/apk/db/installed
	[[ -r $database ]] || return 1
	[[ $(apk_package_version "$database" clang22) == 22.1.8-r0 ]] || return 1
	[[ $(apk_package_version "$database" lld22) == 22.1.8-r0 ]] || return 1
	[[ $(apk_package_version "$database" llvm22) == 22.1.8-r0 ]] || return 1
	return 0
}

MODE=build
REQUESTED_CHROOT=${NATIVE_CHROOT:-}
SELF=$(readlink -f -- "${BASH_SOURCE[0]}")
if [[ ${1:-} == --help ]]; then usage; exit 0; fi
if [[ ${1:-} == --sudo-selected-chroot ]]; then
	[[ $# == 3 ]] || die 'invalid internal sudo invocation'
	(( EUID == 0 )) || die 'internal sudo chroot selector may only be used after privilege elevation'
	[[ -z $REQUESTED_CHROOT || $REQUESTED_CHROOT == "$2" ]] || die 'NATIVE_CHROOT changed during sudo re-exec'
	REQUESTED_CHROOT=$2
	MODE=$3
	[[ $MODE == build || $MODE == --check-only || $MODE == --preflight ]] || die 'invalid internal action'
else
	case $#:${1:-} in
		0:) MODE=build ;;
		1:--check-only) MODE=--check-only ;;
		1:--preflight) MODE=--preflight ;;
		*) die 'usage: build-audio-swr-diagnostic-boot.sh [--help|--preflight|--check-only]' ;;
	esac
fi

if [[ $MODE == --preflight ]]; then
	CHROOT=
elif [[ -n $REQUESTED_CHROOT ]]; then
	[[ $REQUESTED_CHROOT == /* && -d $REQUESTED_CHROOT ]] || die "NATIVE_CHROOT must name an existing absolute directory: $REQUESTED_CHROOT"
	CHROOT=$(readlink -f -- "$REQUESTED_CHROOT")
	native_chroot_complete "$CHROOT" || die "explicit native chroot is incomplete: $CHROOT"
else
	[[ -n $REQUESTED_CHROOT && $REQUESTED_CHROOT == /* && -d $REQUESTED_CHROOT ]] || die 'set NATIVE_CHROOT to an existing native Alpine chroot'
	CHROOT=$(readlink -f -- "$REQUESTED_CHROOT")
	native_chroot_complete "$CHROOT" || die "selected native chroot is incomplete: $CHROOT"
fi
if [[ $MODE != --preflight ]]; then printf 'Selected native chroot: %s\n' "$CHROOT"; fi

preflight_host() {
	for c in awk bash cat cmp cp date df du getconf grep ln mkdir patch python3 readlink rm sed sha256sum stat tar tee; do need "$c"; done
	[[ $I == /* && $SRC == /* ]] || die 'external input and source paths must be absolute; set AUDIO_DIAG_INPUT_DIR and AUDIO_DIAG_SOURCE_DIR'
	[[ -f $I/SHA256SUMS && ! -L $I/SHA256SUMS ]] || die 'external input bundle is missing SHA256SUMS; set AUDIO_DIAG_INPUT_DIR'
	(cd "$I" && sha256sum --check --status SHA256SUMS) || die 'input SHA256SUMS failed'
	sha_is 0b6c7d88b3068ae4e3d106fd4b15a1a79bf00c3e576be7b3fcd8ab62faed73ad "$BOOT"
	sha_is 9e3bde7cde952682225a0375444bd3c1d33d99ddb80fa17b6a3abf3957f36c94 "$ARCHIVE"
	sha_is "$EXPECTED_CONFIG" "$CFG"
	sha_is d193cfbaad83811703f5db5990eaa52358e1828af581e09c702f4efa10aec782 "$P1"
	sha_is c94fe70ae385e1f74fb56566b9743d4b5df23b6fc42aeabecbdbee9c3a2004aa "$P2"
	sha_is "$EXPECTED_DIAG" "$P"
	sha_is "$EXPECTED_RESET" "$P4"
	[[ -n $TOOLS && $TOOLS == /* ]] || die 'set AUDIO_DIAG_MKBOOTIMG_TOOLS to an absolute directory'
	sha_is a9d260978a63bd06a24b6347e7dee8a28ff96639793caea15dff6aa491316308 "$UNPACKER"
	sha_is 37d84b3d162e0bc62e36c1f4e1c63c85ea0caa9f29be023eb2f8efe006ad948c "$MKBOOTIMG"
	[[ -x "$UNPACKER" && -x "$MKBOOTIMG" ]] || die 'mkbootimg tools are not executable'
	if [[ $MODE != --preflight ]]; then
		[[ -d $CHROOT/home/pmos && -d $CHROOT/dev && ! -L $CHROOT/dev ]] || die 'selected native chroot lacks /home/pmos or a real /dev directory'
		for tool in llvm-ar llvm-nm llvm-objcopy llvm-objdump; do
			[[ -x $CHROOT/usr/lib/llvm22/bin/$tool ]] || die "selected native chroot lacks $tool"
		done
	fi
	python3 - "$ARCHIVE" <<'PY'
import sys,tarfile
root='android_kernel_xiaomi_sm8250-a5b3099017ae581aae8bf597b2f9c8c765026af1'
with tarfile.open(sys.argv[1], 'r:gz') as t:
    members=t.getmembers()
    if not members: raise SystemExit('empty source archive')
    for member in members:
        name=member.name
        if name.startswith('/') or '..' in name.split('/') or (name != root and not name.startswith(root+'/')):
            raise SystemExit('unsafe/unexpected archive member: '+name)
PY
	[[ -f $SRC/Makefile && -f $SRC/techpack/audio/soc/swr-mstr-ctrl.c && -f $SRC/techpack/audio/asoc/codecs/wcd938x/wcd938x.c ]] || die 'verified source tree incomplete'
	python3 - "$ARCHIVE" "$SRC" "$P1" "$P2" "$P" "$P4" <<'CHECK_SOURCE_MATCH'
from pathlib import Path
import sys, tarfile
archive, source = Path(sys.argv[1]), Path(sys.argv[2])
root = "android_kernel_xiaomi_sm8250-a5b3099017ae581aae8bf597b2f9c8c765026af1"
with tarfile.open(archive, "r:gz") as tf:
    for patch in map(Path, sys.argv[3:]):
        for line in patch.read_text().splitlines():
            if not line.startswith("--- a/"):
                continue
            rel = line[6:]
            if rel.startswith("/") or ".." in rel.split("/"):
                raise SystemExit("unsafe patch target path")
            member = tf.getmember(root + "/" + rel)
            if not member.isfile():
                raise SystemExit("patch target is not a regular archived source file: " + rel)
            archived = tf.extractfile(member)
            if archived is None or archived.read() != (source / rel).read_bytes():
                raise SystemExit("extracted source does not match verified archive at: " + rel)
CHECK_SOURCE_MATCH
	[[ ! -e $OUT && ! -L $OUT && ! -e $OUT.part && ! -L $OUT.part ]] || die "refusing to overwrite output or partial: $OUT"
	for f in kernel ramdisk dtb; do [[ -f $I/boot-unpacked/$f ]] || die "missing boot section $f"; done
	sha_is 471aeec72355094754a82d478a9c4f8b4e8edb4b0a94368fb8fd594a776bbbfb "$I/boot-unpacked/kernel"
	sha_is 301e1222e3043353a46e4b904ca8cba37c19640634d01cbb56c94acbe0e5b5b9 "$I/boot-unpacked/ramdisk"
	sha_is 212d80826ceef522aff2d967082b5708d20ddccc13ae322edce72412f1a06b51 "$I/boot-unpacked/dtb"
	grep -Fxq 'boot image header version: 2' "$I/boot-unpacked-info.txt" || die 'boot header version mismatch'
	grep -Fxq 'page size: 4096' "$I/boot-unpacked-info.txt" || die 'boot page size mismatch'
	validate_patch_sequence
}

validate_patch_sequence() {
	local checkdir stamp patchfile rel
	mkdir -p "$STATE_ROOT"
	stamp=$(date -u +%Y%m%dT%H%M%SZ)
	checkdir="$STATE_ROOT/patch-check-$stamp-$$"
	mkdir -m 0700 "$checkdir" || die "patch-check state collision: $checkdir"
	mkdir -m 0700 "$checkdir/tree" "$checkdir/tmp"
	printf 'RUNNING\n' >"$checkdir/STATUS"
	for patchfile in "$P1" "$P2" "$P"; do
		while IFS= read -r rel; do
			[[ -n $rel ]] || continue
			[[ $rel != /* && $rel != *..* && -f $SRC/$rel ]] || die "patch target missing or unsafe in verified source: $rel"
			(cd "$SRC" && cp --parents -- "$rel" "$checkdir/tree/")
		done < <(sed -n 's#^--- a/##p' "$patchfile")
	done
	{
		(cd "$checkdir/tree" && TMPDIR="$checkdir/tmp" patch --batch --fuzz=0 -p1 <"$P1")
		(cd "$checkdir/tree" && TMPDIR="$checkdir/tmp" patch --batch --fuzz=0 -p1 <"$P2")
		(cd "$checkdir/tree" && TMPDIR="$checkdir/tmp" patch --batch --fuzz=0 -p1 <"$P")
	} >"$checkdir/patch-application.log" 2>&1 || {
		printf 'FAILED\n' >"$checkdir/STATUS"
		cat "$checkdir/patch-application.log" >&2
		die "strict sequential patch application failed; evidence: $checkdir"
	}
	printf 'PASS\n' >"$checkdir/STATUS"
	printf 'PATCH_SEQUENCE_CHECK=%s\n' "$checkdir"
}

case $MODE in
	--check-only) ;;
	build) ;;
esac
preflight_host

if [[ $MODE == --preflight ]]; then
	printf 'PREFLIGHT_PASS: hashes and strict patch applicability verified; no compilation or chroot access performed.\n'
	exit 0
fi

if (( EUID != 0 )); then
	[[ -t 0 && -t 1 && -t 2 ]] || die 'sudo authentication requires an interactive terminal on stdin, stdout and stderr'
	command -v sudo >/dev/null 2>&1 || die 'sudo is unavailable'
	exec sudo -- env \
		"AUDIO_DIAG_ROOT=$ROOT" "AUDIO_DIAG_PROJECT_ROOT=$PROJECT_ROOT" \
		"AUDIO_DIAG_INPUT_DIR=$I" "AUDIO_DIAG_SOURCE_DIR=$SRC" \
		"AUDIO_DIAG_CONFIG=$CFG" "AUDIO_DIAG_MKBOOTIMG_TOOLS=$TOOLS" \
		"AUDIO_DIAG_OUTPUT_DIR=$OUTPUT_DIR" "AUDIO_DIAG_STATE_DIR=$STATE_ROOT" \
		"AUDIO_DIAG_OUTPUT_NAME=$OUTPUT_NAME" "AUDIO_DIAG_RESET_GPIO=$RESET_GPIO" \
		/bin/bash "$SELF" --sudo-selected-chroot "$CHROOT" "$MODE"
fi

need chroot
need mknod

mkdir -p "$STATE_ROOT"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
RUN_ID="$stamp-$$"
STATE="$STATE_ROOT/audio-swr-$RUN_ID"
STAGE_GUEST="/home/pmos/lmi-audio-swr-$RUN_ID"
STAGE_HOST="$CHROOT$STAGE_GUEST"
DEVNULL="$CHROOT/dev/null"
STAGE_CREATED=0
DEVNULL_CREATED=0
DEVNULL_INODE=
OK=0
[[ ! -e $STATE && ! -L $STATE ]] || die "state path already exists: $STATE"
[[ ! -e $STAGE_HOST && ! -L $STAGE_HOST ]] || die "chroot staging path already exists: $STAGE_GUEST"
mkdir -m 0700 "$STATE" || die "state collision: $STATE"
mkdir -m 0700 "$STATE/tmp" "$STATE/src" "$STATE/out" "$STATE/boot"
mkdir -m 0700 "$STATE/boot/original" "$STATE/boot/repacked"
printf 'RUNNING\n' >"$STATE/STATUS"
printf 'boot_sha256\t%s\nconfig_sha256\t%s\nsource_archive_sha256\t%s\nnative_chroot\t%s\nmode\t%s\n' \
	0b6c7d88b3068ae4e3d106fd4b15a1a79bf00c3e576be7b3fcd8ab62faed73ad \
	"$EXPECTED_CONFIG" \
	9e3bde7cde952682225a0375444bd3c1d33d99ddb80fa17b6a3abf3957f36c94 \
	"$CHROOT" "$MODE" >"$STATE/INPUTS.tsv"

persist_native_results() {
	local candidate
	if ((STAGE_CREATED)); then
		if [[ -d $STAGE_HOST && ! -L $STAGE_HOST && -f $STAGE_HOST/.lmi-audio-swr-owner ]] &&
		   [[ $(<"$STAGE_HOST/.lmi-audio-swr-owner") == "$RUN_ID" ]] &&
		   [[ $STAGE_HOST == "$CHROOT/home/pmos/lmi-audio-swr-"* ]]; then
			candidate=$STAGE_HOST/out/.config
			if [[ -f $candidate && ! -e $STATE/out/.config.after-olddefconfig ]]; then
				cp --preserve=mode,timestamps -- "$candidate" "$STATE/out/.config.after-olddefconfig" || return 1
				sha_of "$STATE/out/.config.after-olddefconfig" >"$STATE/out/.config.after-olddefconfig.sha256" || return 1
			fi
			candidate=$STAGE_HOST/out/arch/arm64/boot/Image
			if [[ -s $candidate && ! -e $STATE/out/Image ]]; then
				cp --preserve=mode,timestamps -- "$candidate" "$STATE/out/Image" || return 1
				sha_of "$STATE/out/Image" >"$STATE/out/Image.sha256" || return 1
			fi
		else
			printf 'ERROR: staging ownership marker invalid; preserved %s\n' "$STAGE_HOST" >&2
			return 1
		fi
	fi
}

cleanup() {
	local rc=$?
	trap - EXIT HUP INT TERM
	set +e
	persist_native_results || rc=1
	if ((STAGE_CREATED)); then
		if [[ -d $STAGE_HOST && ! -L $STAGE_HOST && -f $STAGE_HOST/.lmi-audio-swr-owner ]] &&
		   [[ $(<"$STAGE_HOST/.lmi-audio-swr-owner") == "$RUN_ID" ]] &&
		   [[ $STAGE_HOST == "$CHROOT/home/pmos/lmi-audio-swr-"* ]]; then
			rm -rf --one-file-system -- "$STAGE_HOST" || rc=1
		else
			printf 'ERROR: refusing to clean unverified staging path %s\n' "$STAGE_HOST" >&2
			rc=1
		fi
	fi
	if ((DEVNULL_CREATED)); then
		if [[ -c $DEVNULL && $(stat -c '%t:%T:%i' -- "$DEVNULL") == "1:3:$DEVNULL_INODE" ]]; then
			rm -- "$DEVNULL" || rc=1
		else
			printf 'ERROR: temporary chroot /dev/null identity changed; preserved %s\n' "$DEVNULL" >&2
			rc=1
		fi
	fi
	if ((rc == 0 && OK)); then
		if [[ $MODE == --check-only ]]; then printf 'CHECK_ONLY_PASS\n' >"$STATE/STATUS"; else printf 'COMPLETE\n' >"$STATE/STATUS"; fi
	else
		printf 'INCOMPLETE exit=%s\n' "$rc" >"$STATE/STATUS"
	fi
	printf 'STATE=%s\n' "$STATE"
	exit "$rc"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

JOBS=$(getconf _NPROCESSORS_ONLN)
[[ $JOBS =~ ^[1-9][0-9]*$ ]] || die 'invalid host processor count'
SOURCE_KB=$(du -sk -- "$SRC" | awk '{print $1}')
FREE_KB=$(df -Pk -- "$CHROOT/home/pmos" | awk 'NR == 2 {print $4}')
[[ $SOURCE_KB =~ ^[0-9]+$ && $FREE_KB =~ ^[0-9]+$ ]] || die 'could not determine source size or native chroot free space'
REQUIRED_KB=$((SOURCE_KB + 262144))
if [[ $MODE == build ]]; then REQUIRED_KB=$((SOURCE_KB * 2 + 2097152)); fi
((FREE_KB >= REQUIRED_KB)) || die "insufficient native chroot space: need at least $REQUIRED_KB KiB, have $FREE_KB KiB"

export TMPDIR="$STATE/tmp"
tar --no-same-owner -xzf "$ARCHIVE" --strip-components=1 -C "$STATE/src"
patch --batch --fuzz=0 -p1 -d "$STATE/src" <"$P1" >"$STATE/patch-1.log" 2>&1 || die 'historical patch 1 failed; see patch-1.log'
patch --batch --fuzz=0 -p1 -d "$STATE/src" <"$P2" >"$STATE/patch-2.log" 2>&1 || die 'historical patch 2 failed; see patch-2.log'
patch --batch --fuzz=0 -p1 -d "$STATE/src" <"$P" >"$STATE/patch-diagnostic.log" 2>&1 || die 'diagnostic patch failed; see patch-diagnostic.log'
grep -Fq 'LMI_SWR_DIAG' "$STATE/src/techpack/audio/soc/swr-mstr-ctrl.c" || die 'diagnostic patch marker missing after application'
grep -Fq 'BT_HCIUART_QCA6390_LMI' "$STATE/src/drivers/bluetooth/Kconfig" || die 'historical QCA6390 patch marker missing after application'
cp --preserve=mode,timestamps -- "$CFG" "$STATE/out/.config.locked"
printf '%s\n' '-ga5b3099017ae-dirty' >"$STATE/src/.scmversion"

STAGE_HOST="$CHROOT$STAGE_GUEST"
[[ ! -e $STAGE_HOST && ! -L $STAGE_HOST ]] || die "refusing pre-existing staging path: $STAGE_GUEST"
mkdir -m 0700 -- "$STAGE_HOST" || die 'could not create native staging directory'
STAGE_CREATED=1
printf '%s\n' "$RUN_ID" >"$STAGE_HOST/.lmi-audio-swr-owner"
mkdir -m 0700 -- "$STAGE_HOST/src" "$STAGE_HOST/out" "$STAGE_HOST/out/tmp"
cp -a -- "$STATE/src/." "$STAGE_HOST/src/" || die 'could not copy patched source into Alpine staging'
cp --preserve=mode,timestamps -- "$CFG" "$STAGE_HOST/out/.config" || die 'could not copy locked config into Alpine staging'
[[ $(sha_of "$STAGE_HOST/out/.config") == "$EXPECTED_CONFIG" ]] || die 'staged config SHA-256 mismatch'

printf 'Alpine native chroot: %s\n' "$CHROOT" >"$STATE/COMMANDS.txt"
cat >>"$STATE/COMMANDS.txt" <<EOF
CC=clang and LD=ld.lld selected by LLVM=1 inside Alpine; no musl loader wrapper is used.
HOSTCC=/usr/bin/gcc and HOSTCXX=/usr/bin/g++ inside Alpine; HOSTLD is left to Kbuild.
TMPDIR=$STAGE_GUEST/out/tmp; staging is uniquely marked and removed by the trap.
Probe dynamic: scripts/cc-can-link.sh clang -m64
Probe static: scripts/cc-can-link.sh clang -static -m64
Kconfig: make O=$STAGE_GUEST/out ARCH=arm64 CROSS_COMPILE=aarch64-alpine-linux-musl- LLVM=1 LLVM_IAS=1 HOSTCC=/usr/bin/gcc HOSTCXX=/usr/bin/g++ olddefconfig
Kernel target in build mode only: Image -j$JOBS, after both probes and exact locked-config validation.
EOF

run_chroot_step() {
	local name=$1 command=$2 rc
	set +e
	chroot "$CHROOT" /bin/sh -c "$command" sh "$STAGE_GUEST" >"$STATE/$name.stdout" 2>"$STATE/$name.stderr"
	rc=$?
	set -e
	printf '%s\n' "$rc" >"$STATE/$name.exit"
	if ((rc != 0)); then die "$name failed with exit status $rc; see $STATE/$name.stdout and .stderr"; fi
}

if [[ -e $DEVNULL || -L $DEVNULL ]]; then
	[[ -c $DEVNULL && $(stat -c '%t:%T' -- "$DEVNULL") == '1:3' ]] || die 'native chroot /dev/null exists but is not character device 1:3'
else
	mknod -m 0666 -- "$DEVNULL" c 1 3 || die 'cannot create temporary chroot /dev/null for compiler probes'
	DEVNULL_CREATED=1
	DEVNULL_INODE=$(stat -c '%i' -- "$DEVNULL")
fi

run_chroot_step toolchain-versions '
set -eu
export PATH=/usr/lib/llvm22/bin:/usr/bin:/bin TMPDIR="$1/out/tmp" LC_ALL=C
clang --version
ld.lld --version
gcc --version
g++ --version
'
grep -Fq 'Alpine clang version 22.1.8' "$STATE/toolchain-versions.stdout" || die 'native Alpine clang is not version 22.1.8'
grep -Fq 'LLD 22.1.8' "$STATE/toolchain-versions.stdout" || die 'native Alpine LLD is not version 22.1.8'

run_chroot_step probe-dynamic '
set -eu
export PATH=/usr/lib/llvm22/bin:/usr/bin:/bin TMPDIR="$1/out/tmp" LC_ALL=C
cd "$1/src"
scripts/cc-can-link.sh clang -m64
printf "DYNAMIC_LINK_PROBE=PASS\\n"
'
run_chroot_step probe-static '
set -eu
export PATH=/usr/lib/llvm22/bin:/usr/bin:/bin TMPDIR="$1/out/tmp" LC_ALL=C
cd "$1/src"
scripts/cc-can-link.sh clang -static -m64
printf "STATIC_LINK_PROBE=PASS\\n"
'
grep -Fxq 'DYNAMIC_LINK_PROBE=PASS' "$STATE/probe-dynamic.stdout" || die 'dynamic link probe did not report PASS'
grep -Fxq 'STATIC_LINK_PROBE=PASS' "$STATE/probe-static.stdout" || die 'static link probe did not report PASS'
if grep -Fq 'cannot load -cc1' "$STATE"/*.stdout "$STATE"/*.stderr; then die 'toolchain output contains the forbidden -cc1 loader failure'; fi

run_chroot_step olddefconfig '
set -eu
export PATH=/usr/lib/llvm22/bin:/usr/bin:/bin TMPDIR="$1/out/tmp" LC_ALL=C
cd "$1/src"
make O="$1/out" ARCH=arm64 CROSS_COMPILE=aarch64-alpine-linux-musl- LLVM=1 LLVM_IAS=1 HOSTCC=/usr/bin/gcc HOSTCXX=/usr/bin/g++ olddefconfig
'
[[ -f $STAGE_HOST/out/.config ]] || die 'olddefconfig did not produce .config'
cp --preserve=mode,timestamps -- "$STAGE_HOST/out/.config" "$STATE/out/.config.after-olddefconfig"
sha_of "$STATE/out/.config.after-olddefconfig" >"$STATE/out/.config.after-olddefconfig.sha256"
[[ $(<"$STATE/out/.config.after-olddefconfig.sha256") == "$EXPECTED_CONFIG" ]] || die "olddefconfig changed locked config: $(<"$STATE/out/.config.after-olddefconfig.sha256")"
cmp -s -- "$CFG" "$STATE/out/.config.after-olddefconfig" || die 'olddefconfig config differs byte-for-byte from locked config'
if [[ $MODE == --check-only ]]; then
	OK=1
	printf 'Native Kconfig validation passed; no kernel target was compiled.\n'
	exit 0
fi

run_chroot_step kernel-build '
set -eu
export PATH=/usr/lib/llvm22/bin:/usr/bin:/bin TMPDIR="$1/out/tmp" LC_ALL=C
cd "$1/src"
make O="$1/out" ARCH=arm64 CROSS_COMPILE=aarch64-alpine-linux-musl- LLVM=1 LLVM_IAS=1 HOSTCC=/usr/bin/gcc HOSTCXX=/usr/bin/g++ KBUILD_BUILD_VERSION=3 KBUILD_BUILD_USER=lmi-audio-diagnostic KBUILD_BUILD_HOST=diagnostic Image -j'"$JOBS"'
'
IMAGE="$STAGE_HOST/out/arch/arm64/boot/Image"
[[ -s $IMAGE ]] || die 'kernel Image missing from native build staging'
cp --preserve=mode,timestamps -- "$IMAGE" "$STATE/out/Image"
sha_of "$STATE/out/Image" >"$STATE/out/Image.sha256"

"$UNPACKER" --boot_img "$BOOT" --out "$STATE/boot/original" --format info >"$STATE/boot/original/info.txt"
"$UNPACKER" --boot_img "$BOOT" --out "$STATE/boot/original" --format mkbootimg -0 >"$STATE/boot/original/args.nul"
for item in 'kernel 471aeec72355094754a82d478a9c4f8b4e8edb4b0a94368fb8fd594a776bbbfb' 'ramdisk 301e1222e3043353a46e4b904ca8cba37c19640634d01cbb56c94acbe0e5b5b9' 'dtb 212d80826ceef522aff2d967082b5708d20ddccc13ae322edce72412f1a06b51'; do
	set -- $item
	sha_is "$2" "$STATE/boot/original/$1"
done
mapfile -d '' -t args <"$STATE/boot/original/args.nul"
found=0
for ((n=0; n<${#args[@]}; n++)); do
	if [[ ${args[n]} == --kernel ]]; then
		((n + 1 < ${#args[@]})) || die 'bad original boot args'
		args[n+1]=$STATE/out/Image
		found=1
	fi
done
((found)) || die 'original boot args lack kernel'
"$MKBOOTIMG" "${args[@]}" --output "$STATE/boot/repacked/diagnostic.part.img" >"$STATE/mkbootimg.log" 2>&1
[[ -s $STATE/boot/repacked/diagnostic.part.img ]] || die 'repack failed'
"$UNPACKER" --boot_img "$STATE/boot/repacked/diagnostic.part.img" --out "$STATE/boot/repacked/unpacked" --format info >"$STATE/boot/repacked/info.txt"
"$UNPACKER" --boot_img "$STATE/boot/repacked/diagnostic.part.img" --out "$STATE/boot/repacked/unpacked" --format mkbootimg -0 >"$STATE/boot/repacked/args.nul"
cmp -s -- "$STATE/boot/original/ramdisk" "$STATE/boot/repacked/unpacked/ramdisk" || die 'ramdisk changed'
cmp -s -- "$STATE/boot/original/dtb" "$STATE/boot/repacked/unpacked/dtb" || die 'DTB changed'
cmp -s -- "$STATE/out/Image" "$STATE/boot/repacked/unpacked/kernel" || die 'repacked kernel differs from built Image'
python3 - "$STATE/boot/original/args.nul" "$STATE/boot/repacked/args.nul" <<'PY'
import sys
def load(path):
    with open(path, 'rb') as f:
        return f.read().rstrip(b'\0').decode().split('\0')
def norm(args):
    result=[]; skip=False
    for arg in args:
        if skip:
            result.append('<section>'); skip=False; continue
        result.append(arg)
        if arg in ('--kernel', '--ramdisk', '--dtb'):
            skip=True
    if skip:
        raise SystemExit('truncated mkbootimg args')
    return result
if norm(load(sys.argv[1])) != norm(load(sys.argv[2])):
    raise SystemExit('boot metadata or cmdline changed')
PY
sha_is 0b6c7d88b3068ae4e3d106fd4b15a1a79bf00c3e576be7b3fcd8ab62faed73ad "$BOOT"
mkdir -p "$OUTPUT_DIR"
[[ ! -e $OUT && ! -L $OUT && ! -e $OUT.part && ! -L $OUT.part ]] || die "output appeared; refusing overwrite: $OUT"
ln -- "$STATE/boot/repacked/diagnostic.part.img" "$OUT" || die 'atomic no-overwrite publish failed'
printf 'BOOT_OUTPUT\t%s\nSIZE_BYTES\t%s\nSHA256\t%s\n' "$OUT" "$(stat -c %s "$OUT")" "$(sha_of "$OUT")" | tee "$STATE/OUTPUT-MANIFEST.tsv"
OK=1
printf 'Diagnostic boot produced. Temporary testing only: fastboot boot, never flash.\n'
