#!/bin/sh
set -eu
umask 077

[ "${DERIVED_PROFILE:-}" = daily-base ] || { echo 'daily-base Chatty hook: wrong profile' >&2; exit 1; }

home=/home/mobian
config=$home/.config
autostart=$config/autostart
target=$autostart/sm.puri.Chatty-daemon.desktop
uid=$(id -u mobian)
gid=$(id -g mobian)

[ -d "$home" ] && [ ! -L "$home" ] || { echo 'daily-base Chatty hook: unsafe /home/mobian' >&2; exit 1; }

ensure_user_dir() {
	path=$1
	if [ -L "$path" ]; then echo "daily-base Chatty hook: refusing symlink directory $path" >&2; exit 1; fi
	if [ -e "$path" ]; then
		[ -d "$path" ] || { echo "daily-base Chatty hook: not a directory: $path" >&2; exit 1; }
		owner=$(stat -c '%u:%g' "$path")
		[ "$owner" = "$uid:$gid" ] || { echo "daily-base Chatty hook: owner mismatch: $path" >&2; exit 1; }
	else
		mkdir -m 0700 "$path"
		chown "$uid:$gid" "$path"
	fi
}

ensure_user_dir "$config"
ensure_user_dir "$autostart"

expected=$(printf '[Desktop Entry]\nType=Application\nName=Chats (daemon)\nHidden=true\n')
if [ -e "$target" ] || [ -L "$target" ]; then
	[ -f "$target" ] && [ ! -L "$target" ] || { echo 'daily-base Chatty hook: refusing non-regular override' >&2; exit 1; }
	actual=$(cat "$target")
	[ "$actual" = "$expected" ] || { echo 'daily-base Chatty hook: refusing to replace a non-identical override' >&2; exit 1; }
	[ "$(stat -c '%u:%g:%a' "$target")" = "$uid:$gid:644" ] || { echo 'daily-base Chatty hook: existing override metadata mismatch' >&2; exit 1; }
	exit 0
fi

tmp=$autostart/.sm.puri.Chatty-daemon.desktop.$$.part
cleanup() { [ ! -e "$tmp" ] || rm -f -- "$tmp"; }
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
(umask 077; set -C; printf '%s\n' '[Desktop Entry]' 'Type=Application' 'Name=Chats (daemon)' 'Hidden=true' > "$tmp") || { echo 'daily-base Chatty hook: cannot create override atomically' >&2; exit 1; }
chown "$uid:$gid" "$tmp"
chmod 0644 "$tmp"
sync "$tmp"
mv -- "$tmp" "$target"
sync "$autostart"
trap - EXIT HUP INT TERM

[ "$(stat -c '%u:%g:%a' "$target")" = "$uid:$gid:644" ] || { echo 'daily-base Chatty hook: final override metadata mismatch' >&2; exit 1; }
