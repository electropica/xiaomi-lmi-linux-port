#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

# Separate reset-GPIO variant.  It derives a private, auditable builder from
# the validated diagnostic constructor and asserts every transformation.
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
ROOT=${AUDIO_DIAG_ROOT:-$SCRIPT_DIR}
PROJECT_ROOT=${AUDIO_DIAG_PROJECT_ROOT:-$(cd -- "$ROOT/../../.." && pwd -P)}
BASE=$ROOT/build-audio-swr-diagnostic-boot.sh
RESET_PATCH=$PROJECT_ROOT/kernel/patches/audio/0001-lmi-wcd938x-reset-gpio-mux.patch
EXPECTED_BASE=c92da38b49b345ad996799af4d6de7319071f2822ff321affc763fb50241afdc
EXPECTED_RESET=1d1859556bb05c207b70225ecccc922c9338eff485f729012abc41ba75fbfef7

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
sha() { sha256sum -- "$1" | awk '{print $1}'; }
[[ ${1:-} == --help ]] && { printf 'Usage: bash %s [--preflight|--check-only]\n' "$0"; exit 0; }
[[ $# -le 1 && ( $# == 0 || $1 == --check-only || $1 == --preflight ) ]] || die 'usage: [--preflight|--check-only]'
[[ -f $BASE && -f $RESET_PATCH ]] || die 'validated constructor or reset patch missing'
[[ $(sha "$RESET_PATCH") == "$EXPECTED_RESET" ]] || die 'reset patch SHA mismatch'
[[ $(sha "$BASE") == "$EXPECTED_BASE" ]] || die 'validated constructor changed; refusing derived variant'

STATE_ROOT=${AUDIO_DIAG_STATE_DIR:-$ROOT/state-audio}
OUTPUT_DIR=${AUDIO_DIAG_OUTPUT_DIR:-$ROOT/outputs}
AUDIO_DIAG_ROOT=$ROOT
AUDIO_DIAG_PROJECT_ROOT=$PROJECT_ROOT
AUDIO_DIAG_INPUT_DIR=${AUDIO_DIAG_INPUT_DIR:-$ROOT/inputs}
AUDIO_DIAG_SOURCE_DIR=${AUDIO_DIAG_SOURCE_DIR:-$ROOT/source-a5b3099017ae}
AUDIO_DIAG_CONFIG=${AUDIO_DIAG_CONFIG:-$PROJECT_ROOT/kernel/configs/dv43-qca6390-v2.config}
AUDIO_DIAG_MKBOOTIMG_TOOLS=${AUDIO_DIAG_MKBOOTIMG_TOOLS:-}
export AUDIO_DIAG_ROOT AUDIO_DIAG_PROJECT_ROOT AUDIO_DIAG_INPUT_DIR AUDIO_DIAG_SOURCE_DIR
export AUDIO_DIAG_CONFIG AUDIO_DIAG_MKBOOTIMG_TOOLS AUDIO_DIAG_STATE_DIR=$STATE_ROOT
export AUDIO_DIAG_OUTPUT_DIR=$OUTPUT_DIR
mkdir -p -- "$STATE_ROOT"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)-$$
STATE=$STATE_ROOT/reset-gpio-variant-$STAMP
[[ ! -e $STATE && ! -L $STATE ]] || die "state collision: $STATE"
mkdir -m 0700 -- "$STATE"
printf 'RUNNING\n' >"$STATE/STATUS"
RESULT_OK=0
completion_valid() {
	local mode=$1 rc=$2 inner_status=$3 output=$4
	((rc == 0)) || return 1
	if [[ $mode == --preflight ]]; then
		[[ $inner_status == PREFLIGHT_PASS ]]
		return
	fi
	if [[ $mode == --check-only ]]; then
		[[ $inner_status == CHECK_ONLY_PASS ]]
	else
		[[ $inner_status == COMPLETE && -f $output && ! -L $output && -s $output ]]
	fi
}

verify_inner_completion() {
	local mode=$1 rc=$2 inner_state=$3 output=$4 inner_status
	[[ -d $inner_state && ! -L $inner_state && -f $inner_state/STATUS && ! -L $inner_state/STATUS ]] || {
		printf 'ERROR: internal builder status is missing or unsafe\n' >&2
		return 1
	}
	[[ -r $inner_state/STATUS ]] || {
		printf 'ERROR: internal builder status is not readable\n' >&2
		return 1
	}
	inner_status=$(<"$inner_state/STATUS")
	completion_valid "$mode" "$rc" "$inner_status" "$output" || {
		printf 'ERROR: internal builder did not complete successfully (status=%s, output=%s)\n' "$inner_status" "$output" >&2
		return 1
	}
	printf '%s\n' "$inner_status"
}

cleanup() {
	local rc=$?
	trap - EXIT HUP INT TERM
	if [[ -f $STATE/variant-builder.sh ]]; then sha "$STATE/variant-builder.sh" >"$STATE/variant-builder.sha256"; fi
	if ((rc == 0 && RESULT_OK == 1)); then
		printf 'COMPLETE\n' >"$STATE/STATUS"
	else
		((rc != 0)) || rc=1
		printf 'INCOMPLETE exit=%s\n' "$rc" >"$STATE/STATUS"
	fi
	printf 'STATE=%s\n' "$STATE"
	exit "$rc"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

python3 - "$BASE" "$STATE/variant-builder.sh" "$ROOT" <<'PY'
from pathlib import Path
import sys
base, output, root = map(Path, sys.argv[1:])
s = base.read_text()
repls = [
    ('P="$ROOT/patches/0001-lmi-wcd938x-rx-soundwire-diagnostic.patch"',
     'P="$ROOT/patches/0001-lmi-wcd938x-rx-soundwire-diagnostic.patch"\nP4="$PROJECT_ROOT/kernel/patches/audio/0001-lmi-wcd938x-reset-gpio-mux.patch"'),
    ('OUT="$OUTPUT_DIR/$OUTPUT_NAME"',
     'OUT="$OUTPUT_DIR/D-repro-01-audio-swr-reset-gpio-diagnostic-boot.img"'),
    ("grep -Fxq 'page size: 4096' \"$I/boot-unpacked-info.txt\" || die 'boot page size mismatch'",
     "grep -Fxq 'page size: 4096' \"$I/boot-unpacked-info.txt\" || die 'boot page size mismatch'\n\tgrep -Fxq 'second bootloader size: 0' \"$I/boot-unpacked-info.txt\" || die 'unexpected second bootloader section'\n\tgrep -Fxq 'recovery dtbo size: 0' \"$I/boot-unpacked-info.txt\" || die 'unexpected recovery DTBO section'"),
    ('EXPECTED_DIAG=2d5c2188356b0708ebf88b6a2694b216b4ccb62e6e8ab74124a53ea96d3b6e79',
     'EXPECTED_DIAG=2d5c2188356b0708ebf88b6a2694b216b4ccb62e6e8ab74124a53ea96d3b6e79\nEXPECTED_RESET=1d1859556bb05c207b70225ecccc922c9338eff485f729012abc41ba75fbfef7'),
    ('sha_is "$EXPECTED_DIAG" "$P"', 'sha_is "$EXPECTED_DIAG" "$P"\n\tsha_is "$EXPECTED_RESET" "$P4"'),
    ('for patchfile in "$P1" "$P2" "$P"; do', 'for patchfile in "$P1" "$P2" "$P" "$P4"; do'),
    ('(cd "$checkdir/tree" && TMPDIR="$checkdir/tmp" patch --batch --fuzz=0 -p1 <"$P")\n',
     '(cd "$checkdir/tree" && TMPDIR="$checkdir/tmp" patch --batch --fuzz=0 -p1 <"$P")\n\t\t(cd "$checkdir/tree" && TMPDIR="$checkdir/tmp" patch --batch --fuzz=0 -p1 <"$P4")\n'),
    ("patch --batch --fuzz=0 -p1 -d \"$STATE/src\" <\"$P\" >\"$STATE/patch-diagnostic.log\" 2>&1 || die 'diagnostic patch failed; see patch-diagnostic.log'",
     "patch --batch --fuzz=0 -p1 -d \"$STATE/src\" <\"$P\" >\"$STATE/patch-diagnostic.log\" 2>&1 || die 'diagnostic patch failed; see patch-diagnostic.log'\npatch --batch --fuzz=0 -p1 -d \"$STATE/src\" <\"$P4\" >\"$STATE/patch-reset-gpio.log\" 2>&1 || die 'reset GPIO patch failed; see patch-reset-gpio.log'"),
    ('grep -Fq \'BT_HCIUART_QCA6390_LMI\' "$STATE/src/drivers/bluetooth/Kconfig" || die \'historical QCA6390 patch marker missing after application\'',
     'grep -Fq \'BT_HCIUART_QCA6390_LMI\' "$STATE/src/drivers/bluetooth/Kconfig" || die \'historical QCA6390 patch marker missing after application\'\npython3 - "$STATE/src/arch/arm64/boot/dts/vendor/qcom/kona-pinctrl.dtsi" <<\'CHECK_DTS\'\nfrom pathlib import Path\nimport re,sys\ns=Path(sys.argv[1]).read_text()\ndef body(label):\n m=re.search(r\'(?m)^\\s*(?:[A-Za-z0-9_]+:\\s*)?\'+re.escape(label)+r\'\\s*\\{\',s)\n if not m: raise SystemExit("missing source node "+label)\n pos=s.find("{",m.start()); depth=0\n for i in range(pos,len(s)):\n  if s[i]=="{": depth+=1\n  elif s[i]=="}":\n   depth-=1\n   if depth==0: return s[pos+1:i]\n raise SystemExit("unterminated source node "+label)\nfor label in ("wcd938x_reset_active","wcd938x_reset_sleep"):\n b=body(label)\n if not re.search(r\'(?m)^\\s*pins\\s*=\\s*"gpio32";\',b): raise SystemExit("gpio32 missing in "+label)\n funcs=re.findall(r\'(?m)^\\s*function\\s*=\\s*"([^"]+)";\',b)\n if funcs != ["gpio"]: raise SystemExit("unexpected mux in "+label+": "+repr(funcs))\nCHECK_DTS'),
    ('Kernel target in build mode only: Image -j$JOBS, after both probes and exact locked-config validation.',
     'Kernel targets in build mode only: Image and arch/arm64/boot/dts/vendor/qcom/kona-v2.1.dtb after both probes and exact locked-config validation.'),
    ('candidate=$STAGE_HOST/out/arch/arm64/boot/Image\n\t\t\tif [[ -s $candidate && ! -e $STATE/out/Image ]]; then\n\t\t\t\tcp --preserve=mode,timestamps -- "$candidate" "$STATE/out/Image" || return 1\n\t\t\t\tsha_of "$STATE/out/Image" >"$STATE/out/Image.sha256" || return 1\n\t\t\tfi',
     'candidate=$STAGE_HOST/out/arch/arm64/boot/Image\n\t\t\tif [[ -s $candidate && ! -e $STATE/out/Image ]]; then\n\t\t\t\tcp --preserve=mode,timestamps -- "$candidate" "$STATE/out/Image" || return 1\n\t\t\t\tsha_of "$STATE/out/Image" >"$STATE/out/Image.sha256" || return 1\n\t\t\tfi\n\t\t\tcandidate=$STAGE_HOST/out/arch/arm64/boot/dts/vendor/qcom/kona-v2.1.dtb\n\t\t\tif [[ -s $candidate && ! -e $STATE/out/kona-v2.1.dtb ]]; then\n\t\t\t\tcp --preserve=mode,timestamps -- "$candidate" "$STATE/out/kona-v2.1.dtb" || return 1\n\t\t\t\tsha_of "$STATE/out/kona-v2.1.dtb" >"$STATE/out/kona-v2.1.dtb.sha256" || return 1\n\t\t\tfi\n\t\t\tcandidate=$STAGE_HOST/out/kona-v2.1.dts\n\t\t\tif [[ -s $candidate && ! -e $STATE/out/kona-v2.1.dts ]]; then cp --preserve=mode,timestamps -- "$candidate" "$STATE/out/kona-v2.1.dts" || return 1; fi'),
    ('IMAGE="$STAGE_HOST/out/arch/arm64/boot/Image"\n[[ -s $IMAGE ]] || die \'kernel Image missing from native build staging\'',
     'run_chroot_step dtb-build \'\nset -eu\nexport PATH=/usr/lib/llvm22/bin:/usr/bin:/bin TMPDIR="$1/out/tmp" LC_ALL=C\ncd "$1/src"\nmake O="$1/out" ARCH=arm64 CROSS_COMPILE=aarch64-alpine-linux-musl- LLVM=1 LLVM_IAS=1 HOSTCC=/usr/bin/gcc HOSTCXX=/usr/bin/g++ vendor/qcom/kona-v2.1.dtb\'\nrun_chroot_step dtb-verify \'\nset -eu\n"$1/out/scripts/dtc/dtc" -I dtb -O dts -o "$1/out/kona-v2.1.dts" "$1/out/arch/arm64/boot/dts/vendor/qcom/kona-v2.1.dtb"\'\ncp --preserve=mode,timestamps -- "$STAGE_HOST/out/kona-v2.1.dts" "$STATE/out/kona-v2.1.dts" || die \'could not persist DTB decompilation\'\nIMAGE="$STAGE_HOST/out/arch/arm64/boot/Image"\n[[ -s $IMAGE ]] || die \'kernel Image missing from native build staging\'\nDTB="$STAGE_HOST/out/arch/arm64/boot/dts/vendor/qcom/kona-v2.1.dtb"\n[[ -s $DTB ]] || die \'corrected kona-v2.1 DTB missing from native build staging\'\n[[ -s $STATE/out/kona-v2.1.dts ]] || die \'decompiled DTB evidence missing\'\ngrep -Fq \'model = "Qualcomm Technologies, Inc. kona v2.1 SoC";\' "$STATE/out/kona-v2.1.dts" || die \'DTB model identity mismatch\'\ngrep -Fq \'qcom,msm-id = <0x164 0x20001>;\' "$STATE/out/kona-v2.1.dts" || die \'DTB SoC revision mismatch\'\npython3 - "$STATE/out/kona-v2.1.dts" <<\'CHECK_BUILT_DTB\'\nfrom pathlib import Path\nimport re,sys\ns=Path(sys.argv[1]).read_text()\ndef body(label):\n m=re.search(r\'(?m)^\\s*(?:[A-Za-z0-9_]+:\\s*)?\'+re.escape(label)+r\'\\s*\\{\',s)\n if not m: raise SystemExit("DTB missing node "+label)\n pos=s.find("{",m.start()); depth=0\n for i in range(pos,len(s)):\n  if s[i]=="{": depth+=1\n  elif s[i]=="}":\n   depth-=1\n   if depth==0: return s[pos+1:i]\n raise SystemExit("unterminated DTB node "+label)\nfor label in ("wcd938x_reset_active","wcd938x_reset_sleep"):\n b=body(label)\n if not re.search(r\'(?m)^\\s*pins\\s*=\\s*"gpio32";\',b): raise SystemExit("gpio32 absent from DTB node "+label)\n funcs=re.findall(r\'(?m)^\\s*function\\s*=\\s*"([^"]+)";\',b)\n if funcs != ["gpio"]: raise SystemExit("wrong DTB mux in "+label+": "+repr(funcs))\nCHECK_BUILT_DTB\nsha_of "$DTB" >"$STATE/out/kona-v2.1.dtb.sha256"\ncmp -s -- "$STATE/boot/original/dtb" "$DTB" && die \'corrected DTB is unchanged from the original\''),
    ('found=0\nfor ((n=0; n<${#args[@]}; n++)); do', 'found=0\nfound_dtb=0\nfor ((n=0; n<${#args[@]}; n++)); do'),
    ('args[n+1]=$STATE/out/Image\n\t\tfound=1\n\tfi', 'args[n+1]=$STATE/out/Image\n\t\tfound=1\n\telif [[ ${args[n]} == --dtb ]]; then\n\t\t((n + 1 < ${#args[@]})) || die \'bad original boot args\'\n\t\targs[n+1]=$STATE/out/kona-v2.1.dtb\n\t\tfound_dtb=1\n\tfi'),
    ("((found)) || die 'original boot args lack kernel'", "((found)) || die 'original boot args lack kernel'\n((found_dtb)) || die 'original boot args lack DTB'"),
    ('cmp -s -- "$STATE/boot/original/dtb" "$STATE/boot/repacked/unpacked/dtb" || die \'DTB changed\'',
     'cmp -s -- "$STATE/out/kona-v2.1.dtb" "$STATE/boot/repacked/unpacked/dtb" || die \'repacked DTB differs from corrected kona-v2.1.dtb\'\ncmp -s -- "$STATE/boot/original/dtb" "$STATE/out/kona-v2.1.dtb" && die \'corrected DTB is unchanged from the original\''),
    ('sha_of "$DTB" >"$STATE/out/kona-v2.1.dtb.sha256"',
     'cp --preserve=mode,timestamps -- "$DTB" "$STATE/out/kona-v2.1.dtb" || die \'could not stage DTB for repack\'\nsha_of "$STATE/out/kona-v2.1.dtb" >"$STATE/out/kona-v2.1.dtb.sha256"'),
]
for old, new in repls:
    n=s.count(old)
    if n != 1:
        raise SystemExit(f'transform anchor count {n}, expected 1: {old[:100]!r}')
    s=s.replace(old,new,1)
output.write_text(s)
PY
chmod 0700 "$STATE/variant-builder.sh"
bash -n "$STATE/variant-builder.sh"
printf '%s\n' "$EXPECTED_BASE  $BASE" "$EXPECTED_RESET  $RESET_PATCH" >"$STATE/DERIVATION-INPUTS.txt"
# Keep the internal builder's stdin/stdout/stderr attached to the caller's
# terminal: it may need to authenticate through sudo.  Identify its state by
# the unique directory it creates instead of parsing/capturing its output.
shopt -s nullglob
prior_inner_states=("$STATE_ROOT"/audio-swr-*)
shopt -u nullglob
if [[ ${1:-} == --check-only ]]; then
	if bash "$STATE/variant-builder.sh" --check-only; then INNER_RC=0; else INNER_RC=$?; fi
elif [[ ${1:-} == --preflight ]]; then
	if bash "$STATE/variant-builder.sh" --preflight; then INNER_RC=0; else INNER_RC=$?; fi
else
	if bash "$STATE/variant-builder.sh"; then INNER_RC=0; else INNER_RC=$?; fi
fi
if ((INNER_RC != 0)); then exit "$INNER_RC"; fi
if [[ ${1:-} == --preflight ]]; then
	RESULT_OK=1
	exit 0
fi
new_inner_states=()
shopt -s nullglob
for candidate in "$STATE_ROOT"/audio-swr-*; do
	[[ -d $candidate && ! -L $candidate ]] || continue
	was_present=0
	for prior in "${prior_inner_states[@]}"; do
		[[ $candidate == "$prior" ]] && { was_present=1; break; }
	done
	((was_present)) || new_inner_states+=("$candidate")
done
shopt -u nullglob
(( ${#new_inner_states[@]} == 1 )) || die 'could not identify exactly one new internal builder state'
INNER_STATE=${new_inner_states[0]}
EXPECTED_OUTPUT=$OUTPUT_DIR/D-repro-01-audio-swr-reset-gpio-diagnostic-boot.img
# The internal builder elevates through sudo and keeps its state private.
# Read only its completion metadata with the same privilege when necessary;
# do not open the state permissions or infer completion from an image alone.
if ((EUID == 0)) || [[ -r $INNER_STATE/STATUS && -x $OUTPUT_DIR ]]; then
	INNER_STATUS=$(verify_inner_completion "${1:-build}" "$INNER_RC" "$INNER_STATE" "$EXPECTED_OUTPUT") || die 'internal completion verification failed'
else
	command -v sudo >/dev/null || die 'sudo is required to verify the private internal state'
	COMPLETION_PROBE=$(declare -f completion_valid verify_inner_completion)
	COMPLETION_PROBE+=$'\nset -Eeuo pipefail\nverify_inner_completion "$@"'
	INNER_STATUS=$(sudo -- /bin/bash -c "$COMPLETION_PROBE" -- "${1:-build}" "$INNER_RC" "$INNER_STATE" "$EXPECTED_OUTPUT") || die 'privileged internal completion verification failed'
fi
RESULT_OK=1
