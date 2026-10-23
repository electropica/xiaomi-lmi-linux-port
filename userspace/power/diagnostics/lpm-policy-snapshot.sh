#!/bin/sh
# One pass, no explicit writes. For an already-awake Android or Mobian session.
# No cmdline, unique device identifiers, wakeup_count, mount or suspend request.
set -u
printf 'FORMAT=lmi-lpm-policy-v1\nKERNEL='
uname -r
base=/sys/module/lpm_levels
if [ ! -d "$base" ]; then
    printf 'ABSENT %s\n' "$base"
    exit 1
fi
find "$base" -maxdepth 6 -type f \( -name idle_enabled -o -name suspend_enabled -o -name sleep_disabled \) -print | sort | while IFS= read -r path; do
    if value=$(cat "$path" 2>/dev/null); then
        printf 'VALUE %s=%s\n' "$path" "$value"
    else
        code=$?
        printf 'READ_ERROR %s rc=%s\n' "$path" "$code"
    fi
done
printf 'END=lmi-lpm-policy-v1\n'
