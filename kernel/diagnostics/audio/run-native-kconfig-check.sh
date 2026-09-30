#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
ROOT=${AUDIO_DIAG_ROOT:-$SCRIPT_DIR}
BUILDER=$ROOT/build-audio-swr-diagnostic-boot.sh

if [[ ! -f $BUILDER || -L $BUILDER ]]; then
	printf 'ERROR: diagnostic builder is missing: %s\n' "$BUILDER" >&2
	exit 1
fi

case $#:${1:-} in
	0:) exec bash "$BUILDER" --check-only ;;
	1:--preflight) exec bash "$BUILDER" --preflight ;;
	*) printf 'Usage: bash %s [--preflight]\n' "$0" >&2; exit 2 ;;
esac
