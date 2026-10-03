#!/bin/bash
# Build a local Debian UPower package; never installs it or enables its quirk.
set -euo pipefail
mode=build
if [[ ${1:-} == --check ]]; then mode=check; shift; fi
if [[ $# != 1 ]]; then
    printf 'Usage: %s [--check] EXTRACTED_DEBIAN_UPOWER_SOURCE\n' "$0" >&2
    exit 2
fi
source_dir=$(realpath -- "$1")
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
patch_file="$script_dir/../patches/0001-trust-validated-battery-status-opt-in.patch"
base_version=1.90.9-1
local_version=1.90.9-1+lmi1
[[ -f "$source_dir/debian/changelog" && -f "$source_dir/debian/rules" ]]
[[ $(dpkg-parsechangelog -l "$source_dir/debian/changelog" -S Source) == upower ]]
[[ $(dpkg-parsechangelog -l "$source_dir/debian/changelog" -S Version) == "$base_version" ]]
[[ $(cat "$source_dir/debian/source/format") == '3.0 (quilt)' ]]
grep -q -- '-Dpolkit=enabled' "$source_dir/debian/rules"
grep -q -- 'libimobiledevice-dev' "$source_dir/debian/control"
patch --directory="$source_dir" --strip=1 --fuzz=0 --dry-run --batch --input="$patch_file"
if [[ $mode == check ]]; then
    printf 'Source identity, packaging features and patch applicability checked; no build started.\n'
    exit 0
fi
[[ $(dpkg --print-architecture) == arm64 ]] || {
    printf 'Build in a disposable native Debian 13 arm64 environment, not Ubuntu or the phone.\n' >&2
    exit 1
}
[[ $(. /etc/os-release; printf '%s:%s' "$ID" "$VERSION_ID") == debian:13 ]]
command -v dch >/dev/null
(cd "$source_dir" && dpkg-checkbuilddeps)
[[ ! -e "$source_dir/debian/patches/0001-trust-validated-battery-status-opt-in.patch" ]]
mkdir -p "$source_dir/debian/patches"
install -m 644 "$patch_file" "$source_dir/debian/patches/0001-trust-validated-battery-status-opt-in.patch"
printf '\n0001-trust-validated-battery-status-opt-in.patch\n' >> "$source_dir/debian/patches/series"
(
    cd "$source_dir"
    DEBFULLNAME='Mobian lmi local build' DEBEMAIL='noreply@example.invalid' \
        dch --newversion "$local_version" --distribution UNRELEASED \
        'Add opt-in for hardware-validated battery status; disabled by default.'
    dpkg-source --before-build .
    # Preserve Debian's Polkit, libimobiledevice, introspection and hardening.
    # Debian's rules disable automatic test execution: run the documented
    # integration checks separately before any deployment.
    dpkg-buildpackage --build=binary --no-sign
)
