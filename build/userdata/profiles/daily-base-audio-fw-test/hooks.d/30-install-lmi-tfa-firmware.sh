#!/bin/sh
set -eu

PROFILE=daily-base-audio-fw-test
EXPECTED=07abfca151aaa296595fff35d53c2aa2999e7d16cdc373ade2fd5954ff90c9a9
DEST=/lib/firmware/postmarketos/tfa98xx.cnt
DEST_DIR=${DEST%/*}
SOURCE=${DERIVED_TFA_SOURCE:-}
ROOT=${LMI_TFA_TEST_ROOT:-}

[ "${DERIVED_PROFILE:-}" = "$PROFILE" ] || {
	echo 'lmi-tfa-firmware hook: wrong profile' >&2
	exit 1
}
[ -n "$SOURCE" ] || {
    echo 'lmi-tfa-firmware hook: DERIVED_TFA_SOURCE was not provided' >&2
    exit 1
}
[ "${SOURCE##*/}" = tfa98xx.cnt ] || {
    echo 'lmi-tfa-firmware hook: invalid staged source path' >&2
    exit 1
}
case $SOURCE in
    /var/tmp/archi-derived-tfa-*/tfa98xx.cnt) ;;
    *) echo 'lmi-tfa-firmware hook: source must be the builder staging input' >&2; exit 1 ;;
esac
SOURCE_PATH=$ROOT$SOURCE
DEST_PATH=$ROOT$DEST
DEST_DIR_PATH=$ROOT$DEST_DIR

[ -f "$SOURCE_PATH" ] && [ ! -L "$SOURCE_PATH" ] || {
    echo "lmi-tfa-firmware hook: expected regular staged source missing: $SOURCE" >&2
    exit 1
}
[ "$(stat -c %s "$SOURCE_PATH")" = 510 ] || {
    echo 'lmi-tfa-firmware hook: staged source size mismatch' >&2
    exit 1
}
source_sha=$(sha256sum "$SOURCE_PATH" | awk '{print $1}')
[ "$source_sha" = "$EXPECTED" ] || {
	echo "lmi-tfa-firmware hook: source SHA mismatch: $source_sha" >&2
	exit 1
}

[ ! -L "$DEST_DIR_PATH" ] || {
	echo "lmi-tfa-firmware hook: refusing symlink destination directory: $DEST_DIR" >&2
	exit 1
}

if [ -e "$DEST_PATH" ] || [ -L "$DEST_PATH" ]; then
    [ -f "$DEST_PATH" ] && [ ! -L "$DEST_PATH" ] || {
		echo "lmi-tfa-firmware hook: refusing non-regular destination: $DEST" >&2
		exit 1
	}
    dest_sha=$(sha256sum "$DEST_PATH" | awk '{print $1}')
	[ "$dest_sha" = "$EXPECTED" ] || {
		echo "lmi-tfa-firmware hook: refusing different pre-existing destination: $DEST" >&2
		exit 1
	}
else
    mkdir -p "$DEST_DIR_PATH"
    install -o 0 -g 0 -m 0644 "$SOURCE_PATH" "$DEST_PATH"
fi

chown 0:0 "$DEST_PATH"
chmod 0644 "$DEST_PATH"
dest_sha=$(sha256sum "$DEST_PATH" | awk '{print $1}')
[ "$dest_sha" = "$EXPECTED" ] || {
	echo "lmi-tfa-firmware hook: installed SHA mismatch: $dest_sha" >&2
	exit 1
}
[ "$(stat -c '%u:%g:%a' "$DEST_PATH")" = 0:0:644 ] || {
	echo 'lmi-tfa-firmware hook: installed ownership/mode mismatch' >&2
	exit 1
}
echo "lmi-tfa-firmware hook: installed verified TFA container at $DEST"
