#!/usr/bin/env bash
set -Eeuo pipefail

# Build only when explicitly invoked by the operator. Binary sources and APKs
# remain outside Git; WESTON14_INPUTS points at the prepared local input tree.
REPO=${WESTON14_REPO:-$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)}
INPUTS=${WESTON14_INPUTS:-/home/linuxagent/dv43-openrc-reconstruction/display-diagnostic/weston14-build/aport}
APORTS=${PMBOOTSTRAP_APORTS:-/home/linuxagent/pmaports-dv43-reference}
WORK=${PMBOOTSTRAP_WORK:-/home/linuxagent/dv43-openrc-work}
CONFIG=${PMBOOTSTRAP_CONFIG:-/home/linuxagent/dv43-openrc-reconstruction/pmbootstrap_v3.cfg}
PMBOOTSTRAP=${PMBOOTSTRAP_PY:-/home/linuxagent/pmbootstrap-3.10.1/pmbootstrap.py}
APORT_DST=$APORTS/temp/weston14-lmi
EXPECTED_APK=$WORK/packages/edge/aarch64/weston14-lmi-14.0.2-r1.apk
OUT=$REPO/weston14-lmi-overlay-14.0.2-r1-crtc129.tar.gz
MARKER=.weston14-lmi-crtc129-repo-aport
CREATED=0

cleanup() {
	local rc=$?
	trap - EXIT INT TERM HUP
	if [[ $CREATED == 1 && -f $APORT_DST/$MARKER ]]; then rm -rf -- "$APORT_DST"; fi
	exit "$rc"
}
trap cleanup EXIT INT TERM HUP

[[ -d $INPUTS && -f $PMBOOTSTRAP && -f $CONFIG && -d $APORTS ]] || { echo 'missing build inputs' >&2; exit 1; }
[[ ! -e $APORT_DST && ! -e $EXPECTED_APK && ! -e $OUT ]] || { echo 'refusing to overwrite existing build state' >&2; exit 1; }
for f in weston-14.0.2.tar.xz libdisplay-info-0.3.patch weston-lmi.ini; do [[ -f $INPUTS/$f ]] || { echo "missing input: $INPUTS/$f" >&2; exit 1; }; done

mkdir -p "$(dirname "$APORT_DST")"
cp -a "$INPUTS" "$APORT_DST"
cp "$REPO/APKBUILD" "$APORT_DST/APKBUILD"
cp "$REPO/prefer-dsi-crtc-129.patch" "$APORT_DST/prefer-dsi-crtc-129.patch"
: >"$APORT_DST/$MARKER"
CREATED=1

python3 "$PMBOOTSTRAP" --config="$CONFIG" --work="$WORK" --aports="$APORTS" \
	build --arch=aarch64 weston14-lmi
[[ -f $EXPECTED_APK ]] || { echo "missing APK: $EXPECTED_APK" >&2; exit 1; }
bash "$REPO/package-overlay-crtc129.sh" "$EXPECTED_APK"
echo "apk=$EXPECTED_APK"
sha256sum "$EXPECTED_APK"
