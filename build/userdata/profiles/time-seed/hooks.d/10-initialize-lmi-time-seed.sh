#!/bin/sh
set -eu
umask 077

[ "${DERIVED_PROFILE:-}" = time-seed ] || { echo 'time-seed hook: wrong profile' >&2; exit 1; }
epoch=${DERIVED_BUILD_EPOCH:-}
case $epoch in ''|*[!0-9]*) echo 'time-seed hook: invalid build epoch' >&2; exit 1 ;; esac
[ "${#epoch}" -ge 9 ] && [ "${#epoch}" -le 12 ] || { echo 'time-seed hook: invalid epoch length' >&2; exit 1; }
canonical=$(date -u -d "@$epoch" +%s) || { echo 'time-seed hook: epoch is not representable' >&2; exit 1; }
[ "$canonical" = "$epoch" ] || { echo 'time-seed hook: epoch is not canonical' >&2; exit 1; }

state_dir=/var/lib/lmi-time-seed
seed_file=$state_dir/last-good-utc
if [ -e "$state_dir" ] || [ -L "$state_dir" ]; then
	[ -d "$state_dir" ] && [ ! -L "$state_dir" ] || { echo 'time-seed hook: unsafe state directory' >&2; exit 1; }
else
	mkdir -m 0700 "$state_dir"
fi
chown 0:0 "$state_dir"
chmod 0700 "$state_dir"
[ ! -e "$seed_file" ] && [ ! -L "$seed_file" ] || { echo 'time-seed hook: refusing to replace an existing seed' >&2; exit 1; }

tmp=$state_dir/.last-good-utc.$$
cleanup() { [ ! -e "$tmp" ] || rm -f -- "$tmp"; }
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
(umask 077; set -C; printf '%s\n' "$epoch" > "$tmp") || { echo 'time-seed hook: cannot create seed atomically' >&2; exit 1; }
chown 0:0 "$tmp"
chmod 0600 "$tmp"
sync "$tmp"
mv -- "$tmp" "$seed_file"
sync "$state_dir"
trap - EXIT HUP INT TERM

enable_link() {
	dest=$1
	target=$2
	if [ -e "$dest" ] || [ -L "$dest" ]; then
		echo "time-seed hook: refusing to replace $dest" >&2
		exit 1
	fi
	mkdir -p "$(dirname "$dest")"
	ln -s "$target" "$dest"
}

enable_link /etc/systemd/system/basic.target.wants/lmi-time-seed.service ../lmi-time-seed.service
enable_link /etc/systemd/system/timers.target.wants/lmi-time-seed-save.timer ../lmi-time-seed-save.timer
