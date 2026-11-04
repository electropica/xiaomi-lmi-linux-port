#!/bin/sh
# Enable the non-free-firmware component for the Debian and Mobian sources.
#
# Written to be idempotent: running it twice must not produce
# "main non-free-firmware non-free-firmware".
set -eu

NONFREE=${1:-true}
[ "$NONFREE" = "true" ] || exit 0

# Debian one-line sources: the component is the last field.
if [ -f /etc/apt/sources.list ]; then
    sed -i 's/^\(deb .*[^ ]\) main$/\1 main non-free-firmware/' /etc/apt/sources.list
    sed -i '/ non-free-firmware$/! s/^\(deb .*[^ ]\) main$/\1 main non-free-firmware/' /etc/apt/sources.list
fi

# Mobian deb822 sources: the component list is a single field.
if [ -f /etc/apt/sources.list.d/mobian.sources ]; then
    sed -i 's/^Components: main$/Components: main non-free-firmware/' /etc/apt/sources.list.d/mobian.sources
    sed -i '/^Components:.*non-free-firmware$/! s/^Components: main$/Components: main non-free-firmware/' /etc/apt/sources.list.d/mobian.sources
fi

echo "NONFREE_FIRMWARE_ENABLED"
