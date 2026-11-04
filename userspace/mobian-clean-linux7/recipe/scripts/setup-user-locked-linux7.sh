#!/bin/sh
# Create the desktop user for the clean image.
#
# The account is created LOCKED on purpose. The upstream Mobian recipe ships a
# default password of 1234 and also accepts the password as a command line
# argument, which puts the secret in the process list and in the build log.
# Neither is reproduced here.
#
# The operator provisions the credentials on the target device with
# scripts/provision-account-target.sh, which reads them from stdin.
set -eu

username=${1:?username required}

adduser --gecos "$username" --disabled-password --shell /bin/bash "$username"

# The groups are added only when they exist in the base system. A debootstrap
# minbase image has no bluetooth group, and an unguarded "adduser mobian
# bluetooth" aborts the whole build under set -e.
for g in sudo plugdev audio video render input feedbackd bluetooth; do
    if getent group "$g" >/dev/null; then
        adduser "$username" "$g"
    else
        echo "note: group $g does not exist in this base image, skipped"
    fi
done

# Deliberately no password is set here.
echo "USER_CREATED_LOCKED user=$username uid=$(id -u "$username")"
