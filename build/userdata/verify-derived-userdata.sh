#!/bin/sh
set -eu

BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TFA_FIRMWARE_INPUT=${ARCHI_TFA_FIRMWARE_INPUT:-"$BASE/inputs/vendor-firmware/tfa98xx.cnt"}
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

for file in .gitignore README.md build-derived-userdata.sh verify-derived-userdata.sh \
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
    profiles/daily-base-audio-fw-test/profile.conf profiles/daily-base-audio-fw-test/README.md \
    profiles/daily-base-audio-fw-test/packages.install profiles/daily-base-audio-fw-test/packages.remove \
    profiles/daily-base-audio-fw-test/hooks.d/README.md \
    profiles/daily-base-audio-fw-test/hooks.d/10-initialize-lmi-time-seed.sh \
    profiles/daily-base-audio-fw-test/hooks.d/20-disable-chatty-daemon.sh \
    profiles/daily-base-audio-fw-test/hooks.d/30-install-lmi-tfa-firmware.sh \
    profiles/daily-base-audio-fw-test/overlay/rootfs/usr/local/libexec/lmi-time-seed \
    profiles/daily-base-audio-fw-test/overlay/rootfs/etc/systemd/system/lmi-time-seed.service \
    profiles/daily-base-audio-fw-test/overlay/rootfs/etc/systemd/system/lmi-time-seed-save.service \
    profiles/daily-base-audio-fw-test/overlay/rootfs/etc/systemd/system/lmi-time-seed-save.timer \
    SHA256SUMS; do
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
[ "$(stat -c %a "$BASE/profiles/daily-base-audio-fw-test/hooks.d/10-initialize-lmi-time-seed.sh")" = 755 ] || fail 'audio firmware profile time-seed hook must be mode 0755'
[ "$(stat -c %a "$BASE/profiles/daily-base-audio-fw-test/hooks.d/20-disable-chatty-daemon.sh")" = 755 ] || fail 'audio firmware profile Chatty hook must be mode 0755'
[ "$(stat -c %a "$BASE/profiles/daily-base-audio-fw-test/hooks.d/30-install-lmi-tfa-firmware.sh")" = 755 ] || fail 'TFA firmware hook must be mode 0755'
sh -n "$BASE/profiles/daily-base-audio-fw-test/hooks.d/10-initialize-lmi-time-seed.sh" || fail 'audio firmware profile time-seed hook syntax invalid'
sh -n "$BASE/profiles/daily-base-audio-fw-test/hooks.d/20-disable-chatty-daemon.sh" || fail 'audio firmware profile Chatty hook syntax invalid'
sh -n "$BASE/profiles/daily-base-audio-fw-test/hooks.d/30-install-lmi-tfa-firmware.sh" || fail 'TFA firmware hook syntax invalid'
[ "$(sed -n 's/^PROFILE_ID=//p' "$BASE/profiles/daily-base-audio-fw-test/profile.conf")" = daily-base-audio-fw-test ] || fail 'audio firmware profile ID mismatch'
[ "$(sed -n 's/^PROFILE_REQUIRES_HOOKS=//p' "$BASE/profiles/daily-base-audio-fw-test/profile.conf")" = yes ] || fail 'audio firmware profile must require explicit hook authorization'
cmp -s "$BASE/profiles/daily-base/packages.install" "$BASE/profiles/daily-base-audio-fw-test/packages.install" || fail 'audio firmware profile package additions differ from daily-base'
cmp -s "$BASE/profiles/daily-base/packages.remove" "$BASE/profiles/daily-base-audio-fw-test/packages.remove" || fail 'audio firmware profile package removals differ from daily-base'
diff -qr "$BASE/profiles/daily-base/overlay/rootfs" "$BASE/profiles/daily-base-audio-fw-test/overlay/rootfs" >/dev/null || fail 'audio firmware profile overlay differs from daily-base'
sed 's/daily-base-audio-fw-test/daily-base/g' "$BASE/profiles/daily-base-audio-fw-test/hooks.d/10-initialize-lmi-time-seed.sh" | cmp -s - "$BASE/profiles/daily-base/hooks.d/10-initialize-lmi-time-seed.sh" || fail 'audio firmware profile time-seed hook differs from daily-base'
sed 's/daily-base-audio-fw-test/daily-base/g' "$BASE/profiles/daily-base-audio-fw-test/hooks.d/20-disable-chatty-daemon.sh" | cmp -s - "$BASE/profiles/daily-base/hooks.d/20-disable-chatty-daemon.sh" || fail 'audio firmware profile Chatty hook differs from daily-base'
[ "$(find "$BASE/profiles/daily-base-audio-fw-test/hooks.d" -maxdepth 1 -type f -perm /111 ! -name README.md -printf '%f\n' | LC_ALL=C sort | tr '\n' ' ')" = '10-initialize-lmi-time-seed.sh 20-disable-chatty-daemon.sh 30-install-lmi-tfa-firmware.sh ' ] || fail 'audio firmware profile hook set differs from the expected daily-base-plus-one set'
grep -Fqx 'EXPECTED=07abfca151aaa296595fff35d53c2aa2999e7d16cdc373ade2fd5954ff90c9a9' "$BASE/profiles/daily-base-audio-fw-test/hooks.d/30-install-lmi-tfa-firmware.sh" || fail 'TFA firmware hook locked SHA mismatch'
grep -Fqx 'DEST=/lib/firmware/postmarketos/tfa98xx.cnt' "$BASE/profiles/daily-base-audio-fw-test/hooks.d/30-install-lmi-tfa-firmware.sh" || fail 'TFA firmware hook destination mismatch'
grep -Fq 'install -o 0 -g 0 -m 0644' "$BASE/profiles/daily-base-audio-fw-test/hooks.d/30-install-lmi-tfa-firmware.sh" || fail 'TFA firmware hook ownership/mode installation missing'
if grep -Fq '/vendor' "$BASE/profiles/daily-base-audio-fw-test/hooks.d/30-install-lmi-tfa-firmware.sh"; then
    fail 'TFA firmware hook must not read /vendor from the derived rootfs'
fi
if grep -Eiq 'curl|wget|apt(-get)?[[:space:]]+install|dpkg[[:space:]]+(-i|--install)' "$BASE/profiles/daily-base-audio-fw-test/hooks.d/30-install-lmi-tfa-firmware.sh"; then
    fail 'TFA firmware hook must not download or install packages'
fi
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
awk -F '\t' '
    NR==1 {if($0!="role\tpath\tsize_bytes\tsha256\trequired") exit 1; next}
    NR==2 {if($1!="deb_cache" || $2!="${ARCHI_DEB_CACHE}" || $3!="521861380" || $4!="-" || $5!="yes") exit 1; next}
    NR==3 {if($1!="deb_cache_archive" || $2!="${ARCHI_DEB_ARCHIVE}" || $3!="523274240" || $4!="65058c4bc74c6aea3854060a8e7b9a7617ea6aee66d503d90564bcee214a69fd" || $5!="yes") exit 1; next}
    NR==4 {if($1!="golden_raw" || $2!="${ARCHI_GOLDEN_RAW}" || $3!="4551868416" || $4!="329e2124f97032a2f4b15167bbd9bbbd9395bb422f2794a2117ee610a2368f27" || $5!="yes") exit 1; next}
    NR==5 {if($1!="golden_sparse" || $2!="${ARCHI_GOLDEN_SPARSE}" || $3!="2960036280" || $4!="84182b57edb7be8e49c29e0f0b472e9b6a54f7efa645ef99664dc0e004759f78" || $5!="yes") exit 1; next}
    NR==6 {if($1!="lock" || $2!="${ARCHI_LOCK_DIR:-../locks/userspace}" || $3!="-" || $4!="-" || $5!="yes") exit 1; next}
    NR==7 {if($1!="tfa_firmware" || $2!="${ARCHI_TFA_FIRMWARE_INPUT:-inputs/vendor-firmware/tfa98xx.cnt}" || $3!="510" || $4!="07abfca151aaa296595fff35d53c2aa2999e7d16cdc373ade2fd5954ff90c9a9" || $5!="daily-base-audio-fw-test") exit 1; next}
    END {if(NR!=7) exit 1}
' "$BASE/manifests/INPUTS.tsv" || fail 'INPUTS.tsv values or row count mismatch'
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

if grep -RIE --exclude-dir='state-*' --exclude-dir='inputs' --exclude-dir='outputs' --exclude='*.img*' \
    'BEGIN (OPENSSH|RSA|EC|DSA) PRIVATE KEY' "$BASE" >/dev/null; then
    fail 'private key material found'
fi
if grep -RIE --exclude-dir='state-*' --exclude-dir='inputs' --exclude-dir='outputs' --exclude='*.img*' --exclude=README.md \
    '(^|[^A-Za-z])(password|passwd|pin|psk)[[:space:]]*=' "$BASE" >/dev/null; then
    fail 'possible credential assignment found'
fi
if find "$BASE" \( -path "$BASE/state-*" -o -path "$BASE/inputs" -o -path "$BASE/outputs" \) -prune -o \
    -type f -size +10M -print | grep -q .; then
    fail 'unexpected large payload in builder'
fi

if [ "$MODE" = state ]; then
    need_file "$STATE/STATUS"
    [ "$(cat "$STATE/STATUS")" = COMPLETE ] || fail 'state is not COMPLETE'
    if [ -f "$STATE/PROFILE" ]; then
        state_profile=$(cat "$STATE/PROFILE")
        case $state_profile in
            daily-base-audio-fw-test)
                need_file "$STATE/profile-artifacts.tsv"
                need_file "$TFA_FIRMWARE_INPUT"
                [ ! -L "$TFA_FIRMWARE_INPUT" ] || fail 'TFA host input must not be a symlink'
                [ "$(stat -c %s "$TFA_FIRMWARE_INPUT")" = 510 ] || fail 'TFA host input size mismatch'
                [ "$(hash_file "$TFA_FIRMWARE_INPUT")" = 07abfca151aaa296595fff35d53c2aa2999e7d16cdc373ade2fd5954ff90c9a9 ] || fail 'TFA host input SHA mismatch'
                awk -F '\t' 'NR==1 {if($0!="role\tpath\tuid\tgid\tmode\tsha256")exit 1;next} NR==2 {if($1!="source"||$2!="external-input"||$6!="07abfca151aaa296595fff35d53c2aa2999e7d16cdc373ade2fd5954ff90c9a9")exit 1;next} NR==3 {if($1!="destination"||$2!="/lib/firmware/postmarketos/tfa98xx.cnt"||$3!="0"||$4!="0"||$5!="644"||$6!="07abfca151aaa296595fff35d53c2aa2999e7d16cdc373ade2fd5954ff90c9a9")exit 1;next} END{if(NR!=3)exit 1}' "$STATE/profile-artifacts.tsv" || fail 'TFA profile artifact evidence mismatch'
                ;;
            *) [ ! -e "$STATE/profile-artifacts.tsv" ] || fail 'unexpected profile artifact evidence for a different profile' ;;
        esac
    fi
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
