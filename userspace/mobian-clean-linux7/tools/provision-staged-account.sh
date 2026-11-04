#!/bin/sh
# Run interactively against a freshly extracted staging root, before packing.
set -eu
root=${1:?staging root required}
[ "$(id -u)" = 0 ] || { echo 'root required' >&2; exit 1; }
[ -t 0 ] && [ -t 1 ] || { echo 'interactive terminal required' >&2; exit 1; }
root=$(realpath -e "$root")
case "$root" in /|/proc|/sys|/dev|/run) echo 'unsafe staging root' >&2; exit 1 ;; esac
[ -f "$root/etc/shadow" ] && [ -f "$root/etc/passwd" ] && [ -x "$root/usr/bin/passwd" ] || {
    echo 'staged Mobian account files missing' >&2; exit 1;
}
awk -F: '$1 == "mobian" && $3 == 1000 { found++ } END { exit found != 1 }' "$root/etc/passwd" || {
    echo 'mobian UID is not 1000' >&2; exit 1;
}
echo 'Choose the Mobian account password for the new image.'
chroot "$root" /usr/bin/passwd mobian
awk -F: '$1 == "mobian" { found++; if ($2 == "" || $2 ~ /^[!*]/) exit 1 } END { if (found != 1) exit 1 }' "$root/etc/shadow" || {
    echo 'the staged account remains locked' >&2; exit 1;
}
echo STAGED_ACCOUNT_PROVISIONED
