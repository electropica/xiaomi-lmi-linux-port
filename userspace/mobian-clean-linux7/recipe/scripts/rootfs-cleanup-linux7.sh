#!/bin/sh
# Final cleanup of the clean image.
#
# The apt lists are removed so the image does not ship a stale package index,
# and the machine id is cleared so that the first boot generates a fresh one
# rather than inheriting a duplicate identity.
set -eu

# Dedicated staging directory created by this image recipe.
rm -rf /var/lib/lmi-image-staging
rm -rf /var/lib/apt/lists/*
rm -f /var/cache/apt/archives/*.deb
rm -f /var/cache/debconf/*-old
rm -rf /var/lib/dpkg/info/*.triggers.bak

# The machine id must not be shipped: a duplicated id breaks journald, the
# DHCP client and the SSH host keys. It is generated on first boot.
rm -f /etc/machine-id
install -d -m 0755 /etc
: > /etc/machine-id

# Remove the build-time policy file if it survived.
rm -f /usr/sbin/policy-rc.d

echo "LMI_IMAGE_CLEANED"
