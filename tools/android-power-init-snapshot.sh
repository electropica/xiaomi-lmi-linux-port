#!/system/bin/sh
# lmi full-Android power-initialization snapshot. No calibration or data writes.
# The two debugfs readers temporarily change address/count selectors, restored
# on exit. Their data files are ONLY read. Missing interfaces are reported.
set -eu

if ! command -v getprop >/dev/null 2>&1; then
    printf '%s\n' 'ERROR: full Android is required; do not run under Mobian.' >&2
    exit 1
fi
if [ "$(id -u)" != 0 ]; then
    printf '%s\n' 'ERROR: root shell required. No operation performed.' >&2
    exit 1
fi
device=$(getprop ro.product.device)
bootmode=$(getprop ro.bootmode)
if [ "$device" != lmi ]; then
    printf '%s\n' 'ERROR: expected ro.product.device=lmi.' >&2
    exit 1
fi
if [ "$bootmode" = recovery ] || ! pidof system_server >/dev/null 2>&1; then
    printf '%s\n' 'ERROR: use full Android, not recovery.' >&2
    exit 1
fi
if [ "$(getprop sys.boot_completed)" != 1 ]; then
    printf '%s\n' 'ERROR: wait until Android has completed startup.' >&2
    exit 1
fi
case "$(uname -r)" in
    4.19.*) ;;
    *) printf '%s\n' 'ERROR: this fixed register mapping was reviewed for downstream 4.19 only.' >&2; exit 1 ;;
esac

reg=/sys/kernel/debug/regmap/spmi0-02
sram=/sys/kernel/debug/fg/sram
reg_saved=0
sram_saved=0
cleanup() {
    result=$?
    trap - EXIT HUP INT TERM
    if [ "$reg_saved" = 1 ]; then
        printf '%s\n' "$reg_address" > "$reg/address" || result=1
        printf '%s\n' "$reg_count" > "$reg/count" || result=1
        if [ "$(cat "$reg/address")" != "$reg_address" ] || [ "$(cat "$reg/count")" != "$reg_count" ]; then
            printf '%s\n' 'ERROR: regmap selector restoration not confirmed.' >&2
            result=1
        fi
    fi
    if [ "$sram_saved" = 1 ]; then
        printf '%s\n' "$sram_address" > "$sram/address" || result=1
        printf '%s\n' "$sram_count" > "$sram/count" || result=1
        if [ "$(cat "$sram/address")" != "$sram_address" ] || [ "$(cat "$sram/count")" != "$sram_count" ]; then
            printf '%s\n' 'ERROR: SRAM selector restoration not confirmed.' >&2
            result=1
        fi
    fi
    printf 'SNAPSHOT_EXIT=%s\n' "$result"
    exit "$result"
}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM

printf '%s\n' 'LMI_POWER_INIT_SNAPSHOT_V1'
printf 'UTC='; date -u '+%Y-%m-%dT%H:%M:%SZ'
printf 'KERNEL='; uname -r
printf 'BOOT_ID='; cat /proc/sys/kernel/random/boot_id
for key in ro.product.device ro.build.fingerprint ro.bootmode persist.vendor.cp.calib_force persist.vendor.cp.calib_disable persist.vendor.cp.calib_level persist.vendor.hvdcp_opti.disallowed; do
    printf 'PROPERTY %s=%s\n' "$key" "$(getprop "$key")"
done
printf 'HVDCP_PROCESS_PRESENT='
if pidof hvdcp_opti >/dev/null 2>&1; then printf 'yes\n'; else printf 'no\n'; fi
for entry in usb/online battery/status battery/capacity battery/temp battery/voltage_now bms/calibrate bms/scale_mode_en; do
    file=/sys/class/power_supply/$entry
    printf 'POWER_SUPPLY %s=' "$entry"
    if [ -r "$file" ]; then cat "$file"; else printf 'UNAVAILABLE\n'; fi
done
for supply in charge_pump_master parallel cp_slave; do
    printf 'SUPPLY %s PRESENT=' "$supply"
    if [ -d "/sys/class/power_supply/$supply" ]; then
        printf 'yes\n'
        if [ -r "/sys/class/power_supply/$supply/model_name" ]; then
            printf 'MODEL %s=' "$supply"; cat "/sys/class/power_supply/$supply/model_name"
        fi
    else printf 'no\n'; fi
done

fg=/sys/firmware/devicetree/base/soc/qcom,spmi@c440000/qcom,pm8150b@2/qpnp,fg
for flag in qcom,soc-scale-mode-en qcom,rapid-soc-dec-en qcom,force-calib-level; do
    printf 'DT %s=' "$flag"
    if [ -e "$fg/$flag" ]; then
        printf 'PRESENT '
        od -An -tx1 "$fg/$flag" | tr -d '\n'
        printf '\n'
    else printf 'ABSENT\n'; fi
done

# Only use the fixed register mapping when the running DT confirms MEMIF.
mapping=
if [ -r "$fg/qcom,fg-memif@4300/reg" ]; then
    mapping=$(od -An -tx1 -N4 "$fg/qcom,fg-memif@4300/reg" | tr -d ' \n')
fi
if [ "$mapping" = 00004300 ] && [ -r "$reg/data" ] && [ -w "$reg/address" ] && [ -w "$reg/count" ]; then
    reg_address=$(cat "$reg/address"); reg_count=$(cat "$reg/count"); reg_saved=1
    for address in 0x41b7 0x4340 0x4350 0x4352; do
        printf '%s\n' "$address" > "$reg/address"
        printf '1\n' > "$reg/count"
        printf 'REGISTER %s ' "$address"; cat "$reg/data"
    done
else
    printf '%s\n' 'REGISTER_READS=UNAVAILABLE_OR_MAPPING_UNCONFIRMED'
fi
if [ "$mapping" = 00004300 ] && [ -r "$sram/data" ] && [ -w "$sram/address" ] && [ -w "$sram/count" ]; then
    sram_address=$(cat "$sram/address"); sram_count=$(cat "$sram/count"); sram_saved=1
    printf '0x13\n' > "$sram/address"; printf '2\n' > "$sram/count"
    printf 'SRAM_CUTOFF_CURRENT '; cat "$sram/data"
    printf '0x20\n' > "$sram/address"; printf '1\n' > "$sram/count"
    printf 'SRAM_SLOPE_LIMIT '; cat "$sram/data"
else
    printf '%s\n' 'SRAM_READS=UNAVAILABLE_OR_MAPPING_UNCONFIRMED'
fi
# No daemon is launched, no mount is made, and no Android service is changed.
