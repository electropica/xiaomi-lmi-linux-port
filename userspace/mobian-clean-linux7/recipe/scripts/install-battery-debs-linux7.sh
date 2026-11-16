#!/bin/sh
set -eu
cd /var/lib/lmi-image-staging/lmi-battery-debs
sha256sum -c SHA256SUMS
set -- ./battery-logger_0.1.1_arm64.deb ./battery-viewer_0.1.10_arm64.deb ./battery-sleep-boundaries_0.1.0_all.deb
for package do [ -f "$package" ] || { echo "Missing $package" >&2; exit 1; }; done
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "$@"
systemctl --root=/ enable battery-logger.service
echo LMI_BATTERY_DIAGNOSTICS_INSTALLED
