#!/bin/bash
# Single operator-run entry point for the integrated current lmi image.
set -euo pipefail
[[ $# == 3 ]] || { echo 'usage: BASE_RAW M0_EXT4 OUTPUT_NAME' >&2; exit 2; }
: "${M1_CURRENT_LMI_PROFILE_INPUTS:?Supply the validated private firmware and UPower package directory}"
: "${M1_ANDROID_SUPER_REPORTS_DIR:?Supply current paired Android partition reports}"
export INSTALL_OPTIONAL_APPS=1 INSTALL_DEBUG_TOOLS=1
exec /bin/bash "$(dirname -- "$0")/build-m1-from-preserved-m0.sh" "$@"
