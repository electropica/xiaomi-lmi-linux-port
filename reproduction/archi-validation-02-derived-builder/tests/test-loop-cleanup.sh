#!/bin/bash
set -Eeuo pipefail

BASE=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source "$BASE/lib/loop-cleanup.sh"

fail() { printf 'test-loop-cleanup: %s\n' "$*" >&2; exit 1; }

run_case() (
    local expected_detaches=$1
    shift
    MOCK_ATTACHED=$1
    shift
    MOCK_BACKING=$1
    shift
    MOCK_DETACH_RET=${1:-0}
    shift || true
    MOCK_DETACH_CALLS=0
    WORK_RAW="$BASE/build-derived-userdata.sh"
    SECTOR_SIZE=4096
    LOOP_DEV=${1:-}

    losetup() {
        if [[ ${1-} == --list ]]; then
            [[ ${MOCK_ATTACHED:-0} == 1 ]] || return 0
            printf '/dev/loop7 %s\n' "$MOCK_BACKING"
            return 0
        fi
        if [[ ${1-} == --find ]]; then
            printf '%s\n' "${MOCK_ATTACH_OUTPUT:-/dev/loop7}"
            return 0
        fi
        if [[ ${1-} == --detach ]]; then
            [[ $# == 2 && $2 =~ ^/dev/loop[0-9]+$ ]] || fail 'detach received a non-device argument'
            ((MOCK_DETACH_CALLS += 1))
            [[ $MOCK_ATTACHED == 1 && $2 == /dev/loop7 && $MOCK_BACKING == "$WORK_RAW" ]] || fail 'attempted to detach a non-owned loop'
            MOCK_ATTACHED=0
            return "$MOCK_DETACH_RET"
        fi
        fail "unexpected losetup invocation: $*"
    }

    trap 'detach_owned_loop || exit 91; [[ $MOCK_DETACH_CALLS == "$expected_detaches" ]] || exit 92' EXIT
    if [[ ${MOCK_CASE:-} == malformed_attach_output ]]; then
        MOCK_ATTACH_OUTPUT=--
        attach_work_loop && fail 'malformed attach output was accepted'
        [[ -z $LOOP_DEV ]] || fail 'invalid loop path was stored'
        detach_owned_loop || fail 'partial attach recovery failed'
    else
        detach_owned_loop || fail 'owned loop detach failed'
    fi
    [[ $LOOP_DEV =~ ^$|^/dev/loop[0-9]+$ ]] || fail 'LOOP_DEV retained an invalid path'
)

MOCK_CASE=invalid_stored_path run_case 1 1 "$BASE/build-derived-userdata.sh" 0 --
run_case 1 1 "$BASE/build-derived-userdata.sh" 0 /dev/loop7
run_case 0 1 /unrelated/image.img 0 /dev/loop8
MOCK_CASE=malformed_attach_output run_case 1 1 "$BASE/build-derived-userdata.sh" 1 ''

printf 'test-loop-cleanup: OK (simulated only; no loop device accessed)\n'
