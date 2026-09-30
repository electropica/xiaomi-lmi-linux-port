#!/bin/sh
set -eu

REPO=${WESTON14_REPO:-$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)}
DEPS=${WESTON14_DEPS:-/home/linuxagent/dv43-openrc-reconstruction/display-diagnostic/apks}
APK=${1:-}
[ -f "$APK" ] || { echo 'usage: package-overlay-crtc129.sh weston14-lmi-14.0.2-r1.apk' >&2; exit 64; }
LIBSEAT=$DEPS/libseat-0.9.3-r1.apk
SEATD=$DEPS/seatd-0.9.3-r1.apk
[ -f "$LIBSEAT" ] && [ -f "$SEATD" ] || { echo 'missing libseat/seatd APK' >&2; exit 1; }
printf '%s  %s\n%s  %s\n' \
	5c3d839610c0fe00d66fe414681f215e1863833f015ffb120e9a9b51367f08c1 "$LIBSEAT" \
	5474892bcd5393bc0a77df55a870da56aeeed364d7c2cd62c4f1a590bde01076 "$SEATD" | sha256sum -c -
pkginfo=$(tar -xOzf "$APK" .PKGINFO)
printf '%s\n' "$pkginfo" | grep -qx 'pkgname = weston14-lmi'
printf '%s\n' "$pkginfo" | grep -qx 'pkgver = 14.0.2-r1'
stamp=$(date -u +%Y%m%dT%H%M%SZ)
state=$REPO/.state-crtc129-$stamp-$$
out=$REPO/weston14-lmi-overlay-14.0.2-r1-crtc129.tar.gz
[ ! -e "$out" ] || { echo "refusing to overwrite: $out" >&2; exit 1; }
trap 'rm -rf -- "$state" "$out.part"' EXIT HUP INT TERM
mkdir -m 0700 "$state" "$state/stage" "$state/deps"
tar -xzf "$APK" -C "$state"
mkdir -p "$state/stage/opt"
cp -a "$state/opt/weston14-lmi" "$state/stage/opt/"
install -Dm644 "$REPO/weston-lmi.ini" "$state/stage/opt/weston14-lmi/etc/weston.ini"
install -Dm755 "$state/usr/bin/weston" "$state/stage/opt/weston14-lmi/bin/weston"
tar -xzf "$LIBSEAT" -C "$state/deps" usr/lib/libseat.so.1
tar -xzf "$SEATD" -C "$state/deps" usr/bin/seatd
mkdir -p "$state/stage/opt/weston14-lmi/lib" "$state/stage/opt/weston14-lmi/libexec"
cp -a "$state/deps/usr/lib/libseat.so.1" "$state/stage/opt/weston14-lmi/lib/"
cp -a "$state/deps/usr/bin/seatd" "$state/stage/opt/weston14-lmi/libexec/seatd"
chmod 0755 "$state/stage/opt/weston14-lmi/lib/libseat.so.1" "$state/stage/opt/weston14-lmi/libexec/seatd"
printf '%s\n' 'weston=14.0.2-r1-crtc129' 'prefix=/opt/weston14-lmi' 'backend=drm' 'renderer=pixman' 'shell=kiosk' 'crtc-preference=DSI-1:129' 'assertions=NDEBUG' >"$state/stage/opt/weston14-lmi/VERSION-MANIFEST.txt"
tar --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner -C "$state/stage" -cf - opt | gzip -n -9 >"$out.part"
mv "$out.part" "$out"
trap - EXIT HUP INT TERM
rm -rf -- "$state"
printf 'overlay=%s\nsha256=%s\n' "$out" "$(sha256sum "$out" | awk '{print $1}')"
