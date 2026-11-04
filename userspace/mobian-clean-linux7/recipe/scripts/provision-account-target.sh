#!/bin/sh
# Provision the desktop account on the TARGET device.
#
# The image ships with the mobian account locked. This script sets its
# password on the device itself. The password is read from stdin, never from a
# command line argument, so it never appears in the process list, in a shell
# history or in a build log.
#
# Usage:  sudo provision-account-target.sh [user]
#
# The password is prompted twice and is not echoed.
set -eu

USER_NAME=${1:-mobian}

id "$USER_NAME" >/dev/null 2>&1 || { echo "no such user: $USER_NAME" >&2; exit 1; }

echo "Setting the password for $USER_NAME on this device."
echo "The password is not stored in the image and is not passed as an argument."
passwd "$USER_NAME"

echo "== adding to the groups the session needs =="
for g in sudo plugdev audio video render input; do
    if getent group "$g" >/dev/null; then
        adduser "$USER_NAME" "$g" >/dev/null 2>&1 || true
    fi
done

echo "== summary =="
id "$USER_NAME"
echo "ACCOUNT_PROVISIONED user=$USER_NAME"
