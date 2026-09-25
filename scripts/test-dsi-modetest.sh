#!/bin/sh
# One-shot D-v43/OpenRC DSI modeset test. Run as the unprivileged lmi user.
# It changes display state only while modetest owns the DRM resources and does
# not persist configuration or write any backlight control.

set -u

CARD=/dev/dri/card0
CONNECTOR=/sys/class/drm/card0-DSI-1
BACKLIGHT=/sys/class/backlight/panel0-backlight
MODETEST=/usr/bin/modetest
DRIVER=msm_drm
CONNECTOR_ID=29
CRTC_ID=129
MODE=1080x2400x60x184345cmd

fail()
{
	printf 'ERROR: %s\n' "$*" >&2
	exit 1
}

show_state()
{
	label=$1
	printf '%s: status=%s enabled=%s brightness=%s actual_brightness=%s\n' \
		"$label" \
		"$(cat "$CONNECTOR/status")" \
		"$(cat "$CONNECTOR/enabled")" \
		"$(cat "$BACKLIGHT/brightness")" \
		"$(cat "$BACKLIGHT/actual_brightness")"
}

[ "$(id -u)" -ne 0 ] || fail "run this test as lmi, not as root"
[ -x "$MODETEST" ] || fail "$MODETEST is not installed or executable"
[ -c "$CARD" ] || fail "$CARD is not a DRM character device"
[ -r "$CARD" ] && [ -w "$CARD" ] || fail "$CARD is not accessible to $(id -un)"
[ -d "$CONNECTOR" ] || fail "DSI-1 sysfs connector is absent"
[ -d "$BACKLIGHT" ] || fail "panel backlight sysfs directory is absent"
[ "$(cat "$CONNECTOR/status")" = connected ] || fail "DSI-1 is not connected"
[ "$(cat "$CONNECTOR/enabled")" = disabled ] || fail "DSI-1 is already enabled; refusing to interfere"

connector_inventory=$("$MODETEST" -M "$DRIVER" -c 2>&1) || fail "cannot inspect $DRIVER connectors"
printf '%s\n' "$connector_inventory" | grep -Eq \
	"^[[:space:]]*${CONNECTOR_ID}[[:space:]]+[^[:space:]]+[[:space:]]+connected[[:space:]]+DSI-1" || \
	fail "connector $CONNECTOR_ID is no longer connected DSI-1"
printf '%s\n' "$connector_inventory" | grep -Fq "$MODE" || \
	fail "expected DSI mode $MODE is absent"

printf 'Identity: '
id
show_state BEFORE
printf '%s\n' 'Setting one test pattern on DSI-1 for about eight seconds; observe the panel.'

(sleep 8; printf '\n') | "$MODETEST" -M "$DRIVER" \
	-s "${CONNECTOR_ID}@${CRTC_ID}:${MODE}"
test_rc=$?

show_state AFTER
printf 'modetest exit status: %s\n' "$test_rc"
printf '%s\n' 'Recent display-related kernel messages:'
dmesg 2>&1 | grep -Ei 'drm|dsi|mdss|sde|panel|backlight' | tail -n 100

exit "$test_rc"
