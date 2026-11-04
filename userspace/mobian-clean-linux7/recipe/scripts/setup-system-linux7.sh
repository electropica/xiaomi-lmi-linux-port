#!/bin/sh
# Final system setup for the clean lmi image.
set -eu

HOSTNAME_NAME=${1:?hostname required}

echo "$HOSTNAME_NAME" > /etc/hostname

# The plymouth theme is provided by plymouth-theme-mobian, which the recipe
# installs. Fail loudly rather than leaving a broken theme behind.
if command -v plymouth-set-default-theme >/dev/null 2>&1; then
    plymouth-set-default-theme mobian || echo 'note: mobian plymouth theme not applied'
else
    echo 'note: plymouth-set-default-theme unavailable'
fi

# systemd-firstboot requires interactive input, which is not possible on a
# handset.
systemctl --root=/ mask systemd-firstboot.service

# The image boots through an initramfs that hands over to the real root, so
# /etc/fstab stays empty on purpose: the live handset also has an unconfigured
# fstab and its mounts come from the initramfs.
printf '# UNCONFIGURED FSTAB FOR BASE SYSTEM\n' > /etc/fstab

echo "LMI_SYSTEM_SETUP hostname=$HOSTNAME_NAME"
