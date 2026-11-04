#!/bin/sh
# Set the permissions of the proprietary firmware layer and make sure the
# ADSP starter is present and consistent with the shipped firmware.
#
# The firmware itself is overlaid by the recipe from overlays/lmi-private-
# firmware/. It is proprietary and is never published to a repository.
#
# Permissions are set explicitly rather than inherited: the kernel firmware
# loader reads these files as root, and the ADSP helper verifies their
# SHA-256 before it starts the remoteproc.
set -eu

PRIVATE_DIR=${1:-PRIVATE/firmware}

echo "== firmware tree =="
[ -d /usr/lib/firmware/qcom/sm8250 ] || { echo 'missing ADSP firmware' >&2; exit 1; }
[ -d /usr/lib/firmware/ath11k/QCA6390/hw2.0 ] || { echo 'missing ath11k firmware' >&2; exit 1; }
[ -f /usr/lib/firmware/tfa98xx.cnt ] || { echo 'missing TFA firmware' >&2; exit 1; }

# The kernel firmware loader refuses world-writable files and refuses files
# that are not owned by root.
find /usr/lib/firmware -type d -exec chmod 0755 {} +
find /usr/lib/firmware -type f -exec chmod 0644 {} +
chown -R root:root /usr/lib/firmware

echo "== ADSP firmware set =="
n=$(ls /usr/lib/firmware/qcom/sm8250/adsp.b* 2>/dev/null | wc -l)
[ "$n" -eq 19 ] || { echo "expected 19 ADSP segments, found $n" >&2; exit 1; }
[ -f /usr/lib/firmware/qcom/sm8250/adsp.mdt ] || { echo 'missing adsp.mdt' >&2; exit 1; }
[ -f /usr/lib/firmware/qcom/sm8250/adsp.mbn ] || { echo 'missing adsp.mbn' >&2; exit 1; }

echo "== ADSP starter =="
[ -x /usr/local/libexec/lmi-clean-adsp-start ] || { echo 'missing ADSP starter' >&2; exit 1; }

echo "LMI_FIRMWARE_READY"
