#!/bin/bash
set -euo pipefail

usage() {
	echo "usage: $0 WESTON_TARBALL LIBDISPLAY_INFO_DEV_DEB LIBDISPLAY_INFO_RUNTIME_DEB DEVELOPMENT_DEB_DIR DEVELOPMENT_MANIFEST NATIVE_DEB_DIR NATIVE_MANIFEST OUTPUT_DIR" >&2
	exit 2
}

[ "$#" -eq 8 ] || usage
tarball=$1
display_dev=$2
display_runtime=$3
deb_dir=$4
manifest=$5
native_deb_dir=$6
native_manifest=$7
output=$8
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
lock=$script_dir/source-lock.json
patch_file=$script_dir/patches/0001-dedupe-legacy-plane-formats.patch

[ -d "$deb_dir" ]
[ -f "$manifest" ]
[ -d "$native_deb_dir" ]
[ -f "$native_manifest" ]
[ ! -e "$output" ] || { echo "refusing to overwrite $output" >&2; exit 1; }

locked_hash() {
	python3 - "$lock" "$1" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
value = data["reproduction_inputs"]
for component in sys.argv[2].split("."):
    value = value[component]
print(value)
PY
}

check_hash() {
	actual=$(sha256sum "$1" | awk '{print $1}')
	expected=$2
	[ "$actual" = "$expected" ] || {
		echo "SHA-256 mismatch: $1" >&2
		exit 1
	}
}

check_hash "$tarball" "$(locked_hash weston.sha256)"
check_hash "$patch_file" "$(locked_hash patch.sha256)"
check_hash "$display_dev" "$(locked_hash libdisplay_info_dev.sha256)"
check_hash "$display_runtime" "$(locked_hash libdisplay_info_runtime.sha256)"
check_hash "$native_manifest" "$(locked_hash native_tools.manifest_sha256)"

check_deb_identity() {
	deb=$1
	expected_package=$2
	expected_version=$3
	expected_architecture=$4
	[ "$(dpkg-deb -f "$deb" Package)" = "$expected_package" ]
	[ "$(dpkg-deb -f "$deb" Version)" = "$expected_version" ]
	[ "$(dpkg-deb -f "$deb" Architecture)" = "$expected_architecture" ]
}

check_deb_identity "$display_dev" libdisplay-info-dev 0.2.0-2 arm64
check_deb_identity "$display_runtime" libdisplay-info2 0.2.0-2 arm64

grep -Fx '# status=complete' "$manifest" >/dev/null || {
	echo 'development sysroot manifest is not marked complete' >&2
	exit 1
}
grep -Fx '# status=complete' "$native_manifest" >/dev/null || {
	echo 'native tools manifest is not marked complete' >&2
	exit 1
}

work=$(mktemp -d "${TMPDIR:-/tmp}/mobian-m0-weston.XXXXXX")
trap 'rm -rf -- "$work"' EXIT
mkdir -p "$work/src" "$work/sysroot" "$work/native-root" \
	"$work/native-bin" "$work/native-pkgconfig" "$work/build" "$output"

while IFS=$'\t' read -r filename package version architecture sha256 provenance; do
	case "$filename" in
		''|'#'*) continue ;;
		*/*) echo "manifest filename must be a basename: $filename" >&2; exit 1 ;;
	esac
	[ -n "$provenance" ] || { echo "manifest provenance is missing: $filename" >&2; exit 1; }
	deb=$deb_dir/$filename
	[ -f "$deb" ]
	check_hash "$deb" "$sha256"
	check_deb_identity "$deb" "$package" "$version" "$architecture"
	case "$architecture" in arm64|all) ;; *) echo "non-arm64 package in manifest: $filename" >&2; exit 1 ;; esac
	dpkg-deb -x "$deb" "$work/sysroot"
done < "$manifest"

while IFS=$'\t' read -r filename package version architecture sha256 provenance; do
	case "$filename" in
		''|'#'*) continue ;;
		*/*) echo "native manifest filename must be a basename: $filename" >&2; exit 1 ;;
	esac
	[ -n "$provenance" ] || { echo "native manifest provenance is missing: $filename" >&2; exit 1; }
	deb=$native_deb_dir/$filename
	[ -f "$deb" ]
	check_hash "$deb" "$sha256"
	check_deb_identity "$deb" "$package" "$version" "$architecture"
	[ "$architecture" = amd64 ] || { echo "non-amd64 package in native manifest: $filename" >&2; exit 1; }
	dpkg-deb -x "$deb" "$work/native-root"
done < "$native_manifest"

# Re-extract the two independently locked ABI inputs and verify that the
# manifest includes the exact same packages rather than relying on host data.
dpkg-deb -x "$display_runtime" "$work/sysroot"
dpkg-deb -x "$display_dev" "$work/sysroot"
grep -F $'\tlibdisplay-info-dev\t0.2.0-2\tarm64\tbc397ec057cc03e4ab8ceab570a28ee1eadd9b269298e0d4e6ab67e95bad0be7' "$manifest" >/dev/null
grep -F $'\tlibdisplay-info2\t0.2.0-2\tarm64\t9719d01a5eaef520f41ee576af111c8f4c59246a8861178504d066b86d2ba7c9' "$manifest" >/dev/null

tar -xf "$tarball" --strip-components=1 -C "$work/src"
patch --batch --forward --fuzz=0 -d "$work/src" -p1 < "$patch_file"

sed \
	-e "s|@SYSROOT@|$work/sysroot|g" \
	-e "s|@WORKDIR@|$work|g" \
	"$script_dir/arm64-cross.ini.in" > "$work/arm64-cross.ini"

native_loader=$work/native-root/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2
native_libdir=$work/native-root/usr/lib/x86_64-linux-gnu
native_scanner=$work/native-root/usr/bin/wayland-scanner
scanner_wrapper=$work/native-bin/wayland-scanner
[ -x "$native_loader" ]
[ -x "$native_scanner" ]
file "$native_scanner" | grep -F 'x86-64'
check_hash "$native_scanner" "$(locked_hash native_tools.wayland_scanner.sha256)"
readelf -n "$native_scanner" | grep -F "Build ID: $(locked_hash native_tools.wayland_scanner.build_id)"
printf '#!/bin/sh\nexec "%s" --library-path "%s" "%s" "$@"\n' \
	"$native_loader" "$native_libdir" "$native_scanner" > "$scanner_wrapper"
chmod 0755 "$scanner_wrapper"
[ "$("$scanner_wrapper" --version 2>&1)" = "wayland-scanner $(locked_hash native_tools.wayland_scanner.version)" ]

printf '%s\n' \
	'prefix=/usr' \
	"wayland_scanner=$scanner_wrapper" \
	'Name: Wayland Scanner' \
	'Description: locked native Wayland scanner' \
	"Version: $(locked_hash native_tools.wayland_scanner.version)" \
	> "$work/native-pkgconfig/wayland-scanner.pc"
sed -e "s|@NATIVE_PKGCONFIG@|$work/native-pkgconfig|g" \
	"$script_dir/amd64-native.ini.in" > "$work/amd64-native.ini"

target_pc_libdir=$work/sysroot/usr/lib/aarch64-linux-gnu/pkgconfig:$work/sysroot/usr/share/pkgconfig
[ "$(env PKG_CONFIG_PATH= PKG_CONFIG_SYSROOT_DIR="$work/sysroot" \
	PKG_CONFIG_LIBDIR="$target_pc_libdir" pkg-config --modversion libdisplay-info)" = 0.2.0 ]
case "$(env PKG_CONFIG_PATH= PKG_CONFIG_SYSROOT_DIR="$work/sysroot" \
	PKG_CONFIG_LIBDIR="$target_pc_libdir" pkg-config --variable=pcfiledir libdisplay-info)" in
	"$work/sysroot"/*) ;;
	*) echo 'libdisplay-info pkg-config metadata escaped the sysroot' >&2; exit 1 ;;
esac

unset PKG_CONFIG_LIBDIR PKG_CONFIG_SYSROOT_DIR PKG_CONFIG_LIBDIR_FOR_BUILD PKG_CONFIG_SYSROOT_DIR_FOR_BUILD
export PKG_CONFIG_PATH=
export PKG_CONFIG_PATH_FOR_BUILD=

meson setup "$work/build" "$work/src" \
	--cross-file "$work/arm64-cross.ini" \
	--native-file "$work/amd64-native.ini" \
	--wrap-mode=nodownload \
	-Dbackend-drm-screencast-vaapi=false \
	-Dbackend-pipewire=false \
	-Dbackend-rdp=false \
	-Dbackend-vnc=false \
	-Dbackend-x11=false \
	-Dcolor-management-lcms=false \
	-Ddemo-clients=false \
	-Dimage-jpeg=false \
	-Dimage-webp=false \
	-Dpipewire=false \
	-Dremoting=false \
	-Drenderer-gl=false \
	-Dsimple-clients= \
	-Dsystemd=false \
	-Dtest-junit-xml=false \
	-Dxwayland=false
meson compile -C "$work/build" drm-backend

backend=$work/build/libweston/backend-drm/drm-backend.so
file "$backend" | grep -F 'ARM aarch64'
readelf -d "$backend" | grep -F 'Shared library: [libdisplay-info.so.2]'
if readelf -d "$backend" | grep -F 'Shared library: [libdisplay-info.so.3]'; then
	echo 'unexpected libdisplay-info.so.3 dependency' >&2
	exit 1
fi
max_glibc=$(readelf --version-info "$backend" | grep -o 'GLIBC_[0-9.]*' | sort -Vu | tail -1)
[ "$(printf '%s\n' "$max_glibc" GLIBC_2.38 | sort -V | tail -1)" = GLIBC_2.38 ]

install -m 0755 "$backend" "$output/drm-backend.so"
sha256sum "$output/drm-backend.so" > "$output/drm-backend.so.sha256"
printf 'maximum_glibc_symbol_version=%s\n' "$max_glibc" > "$output/abi.txt"
printf '%s\n' 'The locked hardware-tested hash is a reference, not a promised bit-for-bit output.' >> "$output/abi.txt"
