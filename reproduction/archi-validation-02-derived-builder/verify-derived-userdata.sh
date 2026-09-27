#!/bin/sh
set -eu

BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
MODE=manifest
STATE=

usage() {
    echo "Usage: $0 [--manifest-only | --state STATE_DIRECTORY]" >&2
}
fail() { echo "verify-derived-userdata: ERROR: $*" >&2; exit 1; }
need_file() { [ -f "$1" ] || fail "missing regular file: $1"; }
hash_file() { sha256sum "$1" | awk '{print $1}'; }

case ${1:---manifest-only} in
    --manifest-only) [ "$#" -eq 1 ] || { usage; exit 2; } ;;
    --state)
        [ "$#" -eq 2 ] || { usage; exit 2; }
        MODE=state; STATE=$2
        [ -d "$STATE" ] || fail "missing state directory: $STATE"
        ;;
    *) usage; exit 2 ;;
esac

for file in README.md .gitignore build-derived-userdata.sh verify-derived-userdata.sh \
    lib/loop-cleanup.sh tests/test-loop-cleanup.sh \
    manifests/INPUTS.tsv manifests/GOLDEN-PARTITIONS.tsv \
    manifests/GOLDEN-PROTECTED.tsv manifests/CRITICAL-IDENTITIES.tsv \
    manifests/PROTECTED-PACKAGES.tsv \
    profiles/baseline-nochange/profile.conf \
    profiles/baseline-nochange/packages.install \
    profiles/baseline-nochange/packages.remove \
    profiles/baseline-nochange/overlay/rootfs/.keep \
    profiles/baseline-nochange/hooks.d/README.md \
    profiles/time-seed/profile.conf profiles/time-seed/README.md \
    profiles/time-seed/packages.install profiles/time-seed/packages.remove \
    profiles/time-seed/hooks.d/README.md \
    profiles/time-seed/hooks.d/10-initialize-lmi-time-seed.sh \
    profiles/time-seed/overlay/rootfs/usr/local/libexec/lmi-time-seed \
    profiles/time-seed/overlay/rootfs/etc/systemd/system/lmi-time-seed.service \
    profiles/time-seed/overlay/rootfs/etc/systemd/system/lmi-time-seed-save.service \
    profiles/time-seed/overlay/rootfs/etc/systemd/system/lmi-time-seed-save.timer \
    profiles/daily-base/profile.conf profiles/daily-base/README.md \
    profiles/daily-base/packages.install profiles/daily-base/packages.remove \
    profiles/daily-base/hooks.d/README.md \
    profiles/daily-base/hooks.d/10-initialize-lmi-time-seed.sh \
    profiles/daily-base/hooks.d/20-disable-chatty-daemon.sh \
    profiles/daily-base/overlay/rootfs/usr/local/libexec/lmi-time-seed \
    profiles/daily-base/overlay/rootfs/etc/systemd/system/lmi-time-seed.service \
    profiles/daily-base/overlay/rootfs/etc/systemd/system/lmi-time-seed-save.service \
    profiles/daily-base/overlay/rootfs/etc/systemd/system/lmi-time-seed-save.timer \
    outputs/README.md SHA256SUMS; do
    need_file "$BASE/$file"
done

(cd "$BASE" && sha256sum -c SHA256SUMS --quiet) || fail 'builder SHA256SUMS mismatch'
sh -n "$BASE/verify-derived-userdata.sh" || fail 'verifier shell syntax invalid'
bash -n "$BASE/build-derived-userdata.sh" || fail 'builder Bash syntax invalid'
bash -n "$BASE/lib/loop-cleanup.sh" || fail 'loop helper Bash syntax invalid'
bash -n "$BASE/tests/test-loop-cleanup.sh" || fail 'loop cleanup test Bash syntax invalid'
sh -n "$BASE/profiles/time-seed/hooks.d/10-initialize-lmi-time-seed.sh" || fail 'time-seed hook shell syntax invalid'
sh -n "$BASE/profiles/time-seed/overlay/rootfs/usr/local/libexec/lmi-time-seed" || fail 'time-seed runtime shell syntax invalid'
[ "$(stat -c %a "$BASE/profiles/daily-base/hooks.d/10-initialize-lmi-time-seed.sh")" = 755 ] || fail 'daily-base time-seed hook must be mode 0755'
[ "$(stat -c %a "$BASE/profiles/daily-base/hooks.d/20-disable-chatty-daemon.sh")" = 755 ] || fail 'daily-base Chatty hook must be mode 0755'
[ "$(stat -c %a "$BASE/profiles/daily-base/overlay/rootfs/usr/local/libexec/lmi-time-seed")" = 755 ] || fail 'daily-base time-seed runtime command must be mode 0755'
sh -n "$BASE/profiles/daily-base/hooks.d/10-initialize-lmi-time-seed.sh" || fail 'daily-base time-seed hook shell syntax invalid'
sh -n "$BASE/profiles/daily-base/hooks.d/20-disable-chatty-daemon.sh" || fail 'daily-base Chatty hook shell syntax invalid'
sh -n "$BASE/profiles/daily-base/overlay/rootfs/usr/local/libexec/lmi-time-seed" || fail 'daily-base time-seed runtime shell syntax invalid'
[ "$(stat -c %a "$BASE/profiles/time-seed/hooks.d/10-initialize-lmi-time-seed.sh")" = 755 ] || fail 'time-seed initialization hook must be mode 0755'
[ "$(stat -c %a "$BASE/profiles/time-seed/overlay/rootfs/usr/local/libexec/lmi-time-seed")" = 755 ] || fail 'time-seed runtime command must be mode 0755'
[ "$(sed -n 's/^PROFILE_REQUIRES_HOOKS=//p' "$BASE/profiles/time-seed/profile.conf")" = yes ] || fail 'time-seed profile must require explicit hook authorization'
[ "$(sed -n 's/^PROFILE_REQUIRES_HOOKS=//p' "$BASE/profiles/daily-base/profile.conf")" = yes ] || fail 'daily-base profile must require explicit hook authorization'
if grep -Ev '^[[:space:]]*(#.*)?$' "$BASE/profiles/time-seed/packages.install" "$BASE/profiles/time-seed/packages.remove" | grep -q .; then
    fail 'time-seed must remain package-neutral'
fi
if grep -Ev '^[[:space:]]*(#.*)?$' "$BASE/profiles/daily-base/packages.install" "$BASE/profiles/daily-base/packages.remove" | grep -q .; then
    fail 'daily-base must remain package-neutral and retain Chatty'
fi
for shared in \
    overlay/rootfs/usr/local/libexec/lmi-time-seed \
    overlay/rootfs/etc/systemd/system/lmi-time-seed.service \
    overlay/rootfs/etc/systemd/system/lmi-time-seed-save.service \
    overlay/rootfs/etc/systemd/system/lmi-time-seed-save.timer; do
    cmp -s "$BASE/profiles/time-seed/$shared" "$BASE/profiles/daily-base/$shared" || fail "daily-base time-seed component drift: $shared"
done
grep -Fqx 'target=$autostart/sm.puri.Chatty-daemon.desktop' "$BASE/profiles/daily-base/hooks.d/20-disable-chatty-daemon.sh" || fail 'daily-base Chatty override target changed'
grep -Fq "'Hidden=true'" "$BASE/profiles/daily-base/hooks.d/20-disable-chatty-daemon.sh" || fail 'daily-base Chatty Hidden=true entry missing'
if grep -Eq '^[[:space:]]*Exec=' "$BASE/profiles/daily-base/hooks.d/20-disable-chatty-daemon.sh"; then
    fail 'daily-base override must not define a manual Chatty launcher'
fi
grep -qx 'After=local-fs.target' "$BASE/profiles/time-seed/overlay/rootfs/etc/systemd/system/lmi-time-seed.service" || fail 'time-seed must run after local filesystems'
grep -qx 'Before=basic.target systemd-timesyncd.service systemd-logind.service systemd-user-sessions.service' "$BASE/profiles/time-seed/overlay/rootfs/etc/systemd/system/lmi-time-seed.service" || fail 'time-seed boot ordering changed'
grep -qx 'WantedBy=basic.target' "$BASE/profiles/time-seed/overlay/rootfs/etc/systemd/system/lmi-time-seed.service" || fail 'time-seed service must be enabled in basic.target'
grep -qx 'ExecStart=/usr/local/libexec/lmi-time-seed restore' "$BASE/profiles/time-seed/overlay/rootfs/etc/systemd/system/lmi-time-seed.service" || fail 'time-seed restore command changed'
grep -qx 'ExecStop=/usr/local/libexec/lmi-time-seed save' "$BASE/profiles/time-seed/overlay/rootfs/etc/systemd/system/lmi-time-seed.service" || fail 'time-seed shutdown save command changed'
grep -qx 'OnBootSec=2min' "$BASE/profiles/time-seed/overlay/rootfs/etc/systemd/system/lmi-time-seed-save.timer" || fail 'time-seed initial save schedule changed'
grep -qx 'OnUnitActiveSec=5min' "$BASE/profiles/time-seed/overlay/rootfs/etc/systemd/system/lmi-time-seed-save.timer" || fail 'time-seed periodic save schedule changed'
if grep -Eiq 'hwclock|/dev/rtc|ntpdate' "$BASE/profiles/time-seed/hooks.d/10-initialize-lmi-time-seed.sh" "$BASE/profiles/time-seed/overlay/rootfs/usr/local/libexec/lmi-time-seed"; then
    fail 'time-seed must not rely on RTC or invoke a separate NTP client'
fi

tab=$(printf '\t')
[ "$(head -n 1 "$BASE/manifests/INPUTS.tsv")" = "role${tab}path${tab}size_bytes${tab}sha256${tab}required" ] || fail 'INPUTS.tsv header'
[ "$(tail -n +2 "$BASE/manifests/INPUTS.tsv" | wc -l | tr -d ' ')" -eq 5 ] || fail 'INPUTS.tsv count'
[ "$(head -n 1 "$BASE/manifests/GOLDEN-PARTITIONS.tsv")" = "number${tab}gpt_type_guid${tab}partition_guid${tab}start_lba${tab}sectors${tab}fs_type${tab}fs_label${tab}fs_uuid${tab}sha256" ] || fail 'GOLDEN-PARTITIONS.tsv header'
[ "$(tail -n +2 "$BASE/manifests/GOLDEN-PARTITIONS.tsv" | wc -l | tr -d ' ')" -eq 2 ] || fail 'GOLDEN-PARTITIONS.tsv count'
awk -F '\t' 'NR>1 && NF!=9 {exit 1}' "$BASE/manifests/GOLDEN-PARTITIONS.tsv" || fail 'GOLDEN-PARTITIONS.tsv columns'
awk -F '\t' 'NR>1 && NF!=7 {exit 1}' "$BASE/manifests/GOLDEN-PROTECTED.tsv" || fail 'GOLDEN-PROTECTED.tsv columns'
awk -F '\t' 'NR>1 && NF!=3 {exit 1}' "$BASE/manifests/CRITICAL-IDENTITIES.tsv" || fail 'CRITICAL-IDENTITIES.tsv columns'
awk -F '\t' 'NR>1 && NF!=3 {exit 1}' "$BASE/manifests/PROTECTED-PACKAGES.tsv" || fail 'PROTECTED-PACKAGES.tsv columns'
tail -n +2 "$BASE/manifests/GOLDEN-PROTECTED.tsv" | LC_ALL=C sort -c -t "$tab" -k1,1 || fail 'GOLDEN-PROTECTED.tsv is not sorted'
tail -n +2 "$BASE/manifests/CRITICAL-IDENTITIES.tsv" | LC_ALL=C sort -c -t "$tab" -k1,1 -k2,2 || fail 'CRITICAL-IDENTITIES.tsv is not sorted'
tail -n +2 "$BASE/manifests/PROTECTED-PACKAGES.tsv" | LC_ALL=C sort -c -t "$tab" -k1,1 || fail 'PROTECTED-PACKAGES.tsv is not sorted'

[ "$(awk -F '\t' '$1==1 {print $9}' "$BASE/manifests/GOLDEN-PARTITIONS.tsv")" = 6e2a1555a629126907c452a455ba12e78ee7e3862bbc39e376215569d9e7e03b ] || fail 'golden boot partition SHA'
[ "$(awk -F '\t' '$1==2 {print $8}' "$BASE/manifests/GOLDEN-PARTITIONS.tsv")" = dba94dfe-0fb9-4f95-970e-22949f4e69dc ] || fail 'golden root UUID'

if grep -RIE --exclude-dir='state-*' --exclude='*.img*' \
    'BEGIN (OPENSSH|RSA|EC|DSA) PRIVATE KEY' "$BASE" >/dev/null; then
    fail 'private key material found'
fi
if grep -RIE --exclude-dir='state-*' --exclude='*.img*' --exclude=README.md \
    '(^|[^A-Za-z])(password|passwd|pin|psk)[[:space:]]*=' "$BASE" >/dev/null; then
    fail 'possible credential assignment found'
fi
if find "$BASE" \( -path "$BASE/state-*" -o -path "$BASE/outputs/*.img*" \) -prune -o \
    -type f -size +10M -print | grep -q .; then
    fail 'unexpected large payload in builder'
fi

if [ "$MODE" = state ]; then
    need_file "$STATE/STATUS"
    [ "$(cat "$STATE/STATUS")" = COMPLETE ] || fail 'state is not COMPLETE'
    for file in OUTPUTS.tsv SHA256SUMS.outputs packages-before.tsv packages-after.tsv \
        protected-before.tsv protected-after.tsv identities-before.tsv identities-after.tsv \
        boot-before.sha256 boot-after.sha256 gpt-before.sfdisk gpt-after.sfdisk \
        sparse-roundtrip.sha256 e2fsck.txt; do
        need_file "$STATE/$file"
    done
    cmp -s "$STATE/protected-before.tsv" "$STATE/protected-after.tsv" || fail 'protected manifest changed'
    cmp -s "$STATE/identities-before.tsv" "$STATE/identities-after.tsv" || fail 'critical identities changed'
    cmp -s "$STATE/boot-before.sha256" "$STATE/boot-after.sha256" || fail 'embedded boot changed'
    cmp -s "$STATE/gpt-before.sfdisk" "$STATE/gpt-after.sfdisk" || fail 'GPT changed'
    awk -F '\t' 'NR==1 {if($0!="role\tpath\tsize_bytes\tsha256")exit 1;next} NF!=4 {exit 1} END{if(NR!=3)exit 1}' "$STATE/OUTPUTS.tsv" || fail 'OUTPUTS.tsv format'
    tail -n +2 "$STATE/OUTPUTS.tsv" | while IFS="$tab" read -r role path size sha; do
        need_file "$path"
        [ "$(stat -c %s "$path")" = "$size" ] || fail "$role output size mismatch"
        [ "$(hash_file "$path")" = "$sha" ] || fail "$role output SHA mismatch"
        case $role in raw) raw=$path; raw_sha=$sha ;; sparse) sparse=$path ;; *) fail "unknown output role: $role" ;; esac
    done
    (cd / && sha256sum -c "$STATE/SHA256SUMS.outputs" --quiet) || fail 'output SHA256SUMS mismatch'
    raw=$(awk -F '\t' '$1=="raw" {print $2}' "$STATE/OUTPUTS.tsv")
    sparse=$(awk -F '\t' '$1=="sparse" {print $2}' "$STATE/OUTPUTS.tsv")
    raw_sha=$(awk -F '\t' '$1=="raw" {print $4}' "$STATE/OUTPUTS.tsv")
    [ "$(od -An -tx1 -N4 "$sparse" | tr -d ' \n')" = 3aff26ed ] || fail 'derived sparse magic mismatch'
    [ "$(awk '{print $1}' "$STATE/sparse-roundtrip.sha256")" = "$raw_sha" ] || fail 'sparse round-trip fingerprint mismatch'
    gpt_check="$STATE/.verify-gpt.$$"
    trap 'rm -f "$gpt_check"' EXIT HUP INT TERM
    sfdisk --sector-size 4096 --dump "$raw" > "$gpt_check"
    grep -qx 'label-id: 20F69D00-01EF-4F28-98D5-152E69F32DDF' "$gpt_check" || fail 'derived disk GUID mismatch'
    [ "$(grep -c ' : start=' "$gpt_check")" -eq 2 ] || fail 'derived GPT partition count'
    boot_off=$((2048 * 4096)); boot_size=$((60416 * 4096)); root_off=$((62464 * 4096)); root_size=$((1048576 * 4096))
    [ "$(blkid -p -O "$boot_off" -S "$boot_size" -s UUID -o value "$raw")" = 7bd723c2-51d6-4015-b28b-2b38191bf765 ] || fail 'derived boot UUID mismatch'
    [ "$(blkid -p -O "$root_off" -S "$root_size" -s UUID -o value "$raw")" = dba94dfe-0fb9-4f95-970e-22949f4e69dc ] || fail 'derived root UUID mismatch'
    boot_sha=$(dd if="$raw" bs=4096 skip=2048 count=60416 status=none | sha256sum | awk '{print $1}')
    [ "$boot_sha" = 6e2a1555a629126907c452a455ba12e78ee7e3862bbc39e376215569d9e7e03b ] || fail 'derived embedded boot SHA mismatch'
    rm -f "$gpt_check"; trap - EXIT HUP INT TERM
fi

echo "verify-derived-userdata: OK ($MODE mode)"
