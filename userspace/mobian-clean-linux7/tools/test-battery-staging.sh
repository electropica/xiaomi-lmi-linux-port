#!/bin/sh
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")/../recipe" && pwd)
tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT
mkdir -p "$tmp/stage" "$tmp/bin"
for p in battery-logger_0.1.1_arm64.deb battery-viewer_0.1.12_arm64.deb battery-sleep-boundaries_0.1.0_all.deb; do
    printf '%s\n' "$p" > "$tmp/stage/$p"
done
(cd "$tmp/stage" && sha256sum ./*.deb > SHA256SUMS)
for command in apt-get systemctl; do
    printf '#!/bin/sh\nprintf "%%s\\n" invoked >> "$LMI_TEST_CALLS"\n' > "$tmp/bin/$command"
    chmod 755 "$tmp/bin/$command"
done
export PATH="$tmp/bin:$PATH" LMI_BATTERY_STAGE_DIR="$tmp/stage" LMI_TEST_CALLS="$tmp/calls"
sh "$base/scripts/install-battery-debs-linux7.sh" >/dev/null
[ "$(wc -l < "$tmp/calls")" -eq 2 ]
: > "$tmp/calls"
sed -i '/battery-viewer/d' "$tmp/stage/SHA256SUMS"
if sh "$base/scripts/install-battery-debs-linux7.sh" >/dev/null 2>&1; then
    echo 'missing checksum accepted' >&2; exit 1
fi
[ ! -s "$tmp/calls" ]
(cd "$tmp/stage" && sha256sum ./*.deb > SHA256SUMS)
printf 'corrupt\n' >> "$tmp/stage/battery-logger_0.1.1_arm64.deb"
if sh "$base/scripts/install-battery-debs-linux7.sh" >/dev/null 2>&1; then
    echo 'corrupt package accepted' >&2; exit 1
fi
[ ! -s "$tmp/calls" ]
echo BATTERY_STAGING_TEST_PASS
