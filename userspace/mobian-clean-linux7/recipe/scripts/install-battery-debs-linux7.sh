#!/bin/sh
set -eu
cd "${LMI_BATTERY_STAGE_DIR:-/var/lib/lmi-image-staging/lmi-battery-debs}"
set -- ./battery-logger_0.1.1_arm64.deb ./battery-viewer_0.1.13_arm64.deb ./battery-sleep-boundaries_0.1.0_all.deb
for package do
    [ -f "$package" ] || { echo "Missing $package" >&2; exit 1; }
    awk -v name="${package#./}" 'length($1) == 64 && $1 !~ /[^[:xdigit:]]/ { f=$2; sub(/\r$/, "", f); sub(/^\*/, "", f); sub(/^\.\//, "", f); if (f == name) found=1 } END { exit !found }' SHA256SUMS || {
        echo "Missing SHA256SUMS entry for $package" >&2; exit 1;
    }
done
sha256sum -c SHA256SUMS
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "$@"
systemctl --root=/ enable battery-logger.service
echo LMI_BATTERY_DIAGNOSTICS_INSTALLED
