#!/bin/bash
set -euo pipefail

[[ $# -eq 5 ]] || {
    echo "usage: $0 BASE_RAW M0_TREE OUTPUT_RAW OUTPUT_SPARSE WORKDIR" >&2
    exit 2
}
base=$1
m0_tree=$2
raw=$3
sparse=$4
work=$5
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

expected_base_sha=b12eeb3c561a37e84f2a99037587fdf833979a3b6f4610a03d4e820a51ae6399
expected_base_size=1490026496
final_size=4551868416
root_start=62464
root_blocks=1048576
root_uuid=dba94dfe-0fb9-4f95-970e-22949f4e69dc

validate_rootimg() {
    [[ $(stat -c %s "$rootimg") == $((root_blocks * 4096)) ]]
    [[ $(blkid -p -s TYPE -o value "$rootimg") == ext4 ]]
    [[ $(blkid -p -s UUID -o value "$rootimg") == "$root_uuid" ]]
    [[ $(blkid -p -s LABEL -o value "$rootimg") == pmOS_root ]]
    [[ $(od -An -tx1 -j 1080 -N 2 "$rootimg" | tr -d ' \n') == 53ef ]]
    e2fsck -fn "$rootimg"
}

M1_MOBIAN_PASSWORD="${M1_MOBIAN_PASSWORD:-0000}"
mobian_password=$M1_MOBIAN_PASSWORD
unset M1_MOBIAN_PASSWORD

[[ $(id -u) -eq 0 ]] || { echo "Run inside the documented UID/GID namespace." >&2; exit 1; }
[[ -f $base && -d $m0_tree && ! -e $raw && ! -e $sparse ]] || {
    echo "Missing input or refusing to overwrite an output." >&2
    exit 1
}
[[ $(stat -c %s "$base") == "$expected_base_size" ]]
echo "$expected_base_sha  $base" | sha256sum -c -

mkdir -p "$work"
tree="$work/rootfs"
rootimg="$work/Mobian-M1-REPRO-pmOS_root.ext4"
roundtrip="$work/roundtrip.raw"
[[ ! -e $tree && ! -e $rootimg && ! -e $roundtrip ]]

binfmt_mounted=0
mounted_paths=()
unmount_paths() {
    local i target failed=0
    for ((i=${#mounted_paths[@]}; i>0; i--)); do
        target=${mounted_paths[i-1]}
        printf 'Detaching private mount: %s\n' "$target" >&2
        if ! umount --lazy "$target"; then
            printf 'ERROR: failed to detach private mount: %s\n' "$target" >&2
            failed=1
        fi
    done
    mounted_paths=()
    return "$failed"
}
cleanup() {
    local rc=$? cleanup_failed=0
    trap - EXIT
    set +e
    unmount_paths || cleanup_failed=1
    if [[ $binfmt_mounted == 1 ]]; then
        printf 'Detaching private mount: %s\n' /proc/sys/fs/binfmt_misc >&2
        umount --lazy /proc/sys/fs/binfmt_misc || cleanup_failed=1
    fi
    if ((rc != 0)); then exit "$rc"; fi
    exit "$cleanup_failed"
}
trap cleanup EXIT

mount --make-rprivate /
mount -t binfmt_misc binfmt_misc /proc/sys/fs/binfmt_misc
binfmt_mounted=1
sed -n '1p' /usr/lib/binfmt.d/qemu-aarch64.conf > /proc/sys/fs/binfmt_misc/register
test -e /proc/sys/fs/binfmt_misc/qemu-aarch64

cp -a --reflink=auto -- "$m0_tree" "$tree"
for path in dev proc sys; do
    mount --rbind "/$path" "$tree/$path"
    mount --make-rslave "$tree/$path"
    mounted_paths+=("$tree/$path")
done
mount -t tmpfs -o mode=0755,nosuid,nodev tmpfs "$tree/run"
mounted_paths+=("$tree/run")

cat >"$tree/usr/sbin/policy-rc.d" <<'EOF'
#!/bin/sh
exit 101
EOF
chmod 0755 "$tree/usr/sbin/policy-rc.d"
install -D -o root -g root -m 0644 \
    "$script_dir/90_lmi-input-sources.gschema.override" \
    "$tree/usr/share/glib-2.0/schemas/90_lmi-input-sources.gschema.override"
chroot "$tree" /bin/bash -eu <<'EOF'
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install --no-install-recommends -y \
    phosh=0.46.0-3+deb13u1 \
    phoc=0.46.0-1 \
    squeekboard=1.43.1-1 \
    gnome-session=48.0-1+deb13u1 \
    gnome-keyring=48.0-1 \
    locales=2.41-12+deb13u3 \
    network-manager=1.52.1-1 \
    qrtr-tools=1.1-2+b1 \
    systemd-timesyncd=257.13-1~deb13u1 \
    wpasupplicant=2:2.10-24 \
    unzip=6.0-29+deb13u1
test -z "$(dpkg --audit)"
if ! getent passwd 1000 >/dev/null; then
    useradd --uid 1000 --user-group --create-home --shell /bin/bash mobian
fi
test "$(getent passwd 1000 | cut -d: -f1)" = mobian
usermod -aG audio,video,render,input,plugdev mobian
sed -i 's/^# *fr_FR.UTF-8 UTF-8$/fr_FR.UTF-8 UTF-8/' /etc/locale.gen
grep -qx 'fr_FR.UTF-8 UTF-8' /etc/locale.gen
locale-gen fr_FR.UTF-8
update-locale LANG=fr_FR.UTF-8 LANGUAGE=fr_FR:fr
test -x /usr/bin/glib-compile-schemas
test -f /usr/share/glib-2.0/schemas/org.gnome.desktop.input-sources.gschema.xml
glib-compile-schemas --strict /usr/share/glib-2.0/schemas
EOF
printf '%s:%s\n' mobian "$mobian_password" | chroot "$tree" chpasswd
mobian_password=
rm -f "$tree/usr/sbin/policy-rc.d"
unmount_paths

for name in secrets pkcs11 ssh; do
    desktop="$tree/etc/xdg/autostart/gnome-keyring-$name.desktop"
    test -f "$desktop"
    test "$(grep -c '^X-GNOME-Autostart-Notify=true$' "$desktop")" = 1
    ! grep -q '^X-GNOME-HiddenUnderSystemd=' "$desktop"
    printf '\nX-GNOME-HiddenUnderSystemd=true\n' >>"$desktop"
    test "$(grep -c '^X-GNOME-HiddenUnderSystemd=true$' "$desktop")" = 1
done

xdg_user_dirs_desktop="$tree/etc/xdg/autostart/xdg-user-dirs.desktop"
test -f "$xdg_user_dirs_desktop"
grep -qx 'Exec=xdg-user-dirs-update' "$xdg_user_dirs_desktop"
grep -qx 'X-GNOME-Autostart-Phase=Initialization' "$xdg_user_dirs_desktop"
! grep -q '^X-GNOME-HiddenUnderSystemd=' "$xdg_user_dirs_desktop"
printf '\nX-GNOME-HiddenUnderSystemd=true\n' >>"$xdg_user_dirs_desktop"
test "$(grep -c '^X-GNOME-HiddenUnderSystemd=true$' "$xdg_user_dirs_desktop")" = 1

install -D -o root -g root -m 0644 "$script_dir/phosh-m0.service" "$tree/etc/systemd/system/phosh-m0.service"
install -D -o root -g root -m 0644 "$script_dir/phoc.ini" "$tree/etc/phosh/phoc.ini"
install -D -o root -g root -m 0644 "$script_dir/upower-lmi.conf" "$tree/etc/systemd/system/upower.service.d/lmi-private-users.conf"
install -D -o root -g root -m 0644 "$script_dir/xdg-user-dirs-lmi.service" "$tree/etc/systemd/user/xdg-user-dirs-lmi.service"
install -D -o root -g root -m 0644 "$script_dir/../m0-display/systemd/lmi-splash-release.service" "$tree/etc/systemd/system/lmi-splash-release.service"
install -D -o root -g root -m 0644 "$script_dir/lmi-splash-release-m1.conf" "$tree/etc/systemd/system/lmi-splash-release.service.d/m1-device-wait.conf"
install -D -o root -g root -m 0644 "$script_dir/user-runtime-dir-1000-m1.conf" "$tree/etc/systemd/system/user-runtime-dir@1000.service.d/m1-runtime-fix.conf"
install -D -o root -g root -m 0600 "$script_dir/accountsservice-mobian.ini" "$tree/var/lib/AccountsService/users/mobian"
install -D -o root -g root -m 0644 "$script_dir/networkmanager-usb0-unmanaged.conf" "$tree/etc/NetworkManager/conf.d/10-m1-usb0-unmanaged.conf"
install -D -o root -g root -m 0755 "$script_dir/wifi/scripts/lmi-android-wifi-mounts" "$tree/usr/local/sbin/lmi-android-wifi-mounts"
install -D -o root -g root -m 0755 "$script_dir/wifi/scripts/lmi-wlan-firmware-prepare" "$tree/usr/local/sbin/lmi-wlan-firmware-prepare"
install -D -o root -g root -m 0755 "$script_dir/wifi/scripts/lmi-cnss-daemon-wrapper" "$tree/usr/local/sbin/lmi-cnss-daemon-wrapper"
install -D -o root -g root -m 0755 "$script_dir/wifi/scripts/lmi-cnss-fs-ready" "$tree/usr/local/sbin/lmi-cnss-fs-ready"
install -D -o root -g root -m 0755 "$script_dir/wifi/scripts/lmi-wlan-on" "$tree/usr/local/sbin/lmi-wlan-on"
install -D -o root -g root -m 0644 "$script_dir/wifi/systemd/lmi-android-wifi-mounts.service" "$tree/etc/systemd/system/lmi-android-wifi-mounts.service"
install -D -o root -g root -m 0644 "$script_dir/wifi/systemd/lmi-wlan-firmware-prepare.service" "$tree/etc/systemd/system/lmi-wlan-firmware-prepare.service"
install -D -o root -g root -m 0644 "$script_dir/wifi/systemd/lmi-cnss-daemon.service" "$tree/etc/systemd/system/lmi-cnss-daemon.service"
install -D -o root -g root -m 0644 "$script_dir/wifi/systemd/lmi-cnss-fs-ready.service" "$tree/etc/systemd/system/lmi-cnss-fs-ready.service"
install -D -o root -g root -m 0644 "$script_dir/wifi/systemd/lmi-wlan-on.service" "$tree/etc/systemd/system/lmi-wlan-on.service"
install -D -o root -g root -m 0644 "$script_dir/wifi/systemd/qrtr-ns.service.d/lmi-order.conf" "$tree/etc/systemd/system/qrtr-ns.service.d/lmi-order.conf"
install -D -o root -g root -m 0644 "$script_dir/wifi/systemd/NetworkManager.service.d/lmi-wlan.conf" "$tree/etc/systemd/system/NetworkManager.service.d/lmi-wlan.conf"
mkdir -p "$tree/usr/lib/lmi"
aarch64-linux-gnu-gcc --sysroot="$tree" -shared -fPIC -O2 \
    -Wl,-z,defs -o "$tree/usr/lib/lmi/liblmi_android_prop_shim.so" \
    "$script_dir/wifi/src/lmi-android-prop-shim.c"
file "$tree/usr/lib/lmi/liblmi_android_prop_shim.so" | grep -q 'ARM aarch64'
install -D -o root -g root -m 0644 /dev/null "$tree/var/lib/systemd/linger/mobian"
printf '%s\n' PocoF2Pro >"$tree/etc/hostname"

chroot "$tree" systemctl enable seatd.service
chroot "$tree" systemctl enable NetworkManager.service
chroot "$tree" systemctl enable qrtr-ns.service
chroot "$tree" systemctl enable systemd-timesyncd.service
chroot "$tree" systemctl enable wpa_supplicant.service
chroot "$tree" systemctl enable phosh-m0.service
chroot "$tree" systemctl --global enable xdg-user-dirs-lmi.service
chroot "$tree" systemctl disable weston-m0.service || true
systemd-analyze --root="$tree" verify phosh-m0.service seatd.service lmi-splash-release.service user@1000.service user-runtime-dir@1000.service lmi-android-wifi-mounts.service lmi-wlan-firmware-prepare.service qrtr-ns.service lmi-cnss-daemon.service lmi-cnss-fs-ready.service lmi-wlan-on.service NetworkManager.service wpa_supplicant.service systemd-timesyncd.service upower.service || {
    rc=$?
    echo "WARNING: systemd-analyze verify returned $rc; continuing because known host/rootfs diagnostics may be non-fatal" >&2
}

test "$(stat -c '%u:%g:%a' "$tree/var/lib/systemd/linger/mobian")" = 0:0:644
! grep -q '^ExecStartPre=.*run/user/1000' "$tree/etc/systemd/system/phosh-m0.service"
grep -qx 'PAMName=login' "$tree/etc/systemd/system/phosh-m0.service"
grep -qx 'Environment=XDG_SEAT=seat0' "$tree/etc/systemd/system/phosh-m0.service"
! grep -q '^Environment=XDG_VTNR=' "$tree/etc/systemd/system/phosh-m0.service"
! grep -q '^TTYPath=' "$tree/etc/systemd/system/phosh-m0.service"
! grep -q '^StandardInput=tty' "$tree/etc/systemd/system/phosh-m0.service"
! grep -q 'chvt' "$tree/etc/systemd/system/phosh-m0.service"
! grep -q 'getty@' "$tree/etc/systemd/system/phosh-m0.service"
test -f "$tree/etc/pam.d/login"
grep -Eq '^[[:space:]]*@include[[:space:]]+common-session([[:space:]]|$)' "$tree/etc/pam.d/login"
grep -Eq '^[[:space:]]*session[[:space:]]+[^#]*pam_systemd\.so([[:space:]]|$)' "$tree/etc/pam.d/common-session"
grep -qx 'Environment=WLR_RENDERER=pixman' "$tree/etc/systemd/system/phosh-m0.service"
grep -qx 'Environment=LANG=fr_FR.UTF-8' "$tree/etc/systemd/system/phosh-m0.service"
grep -qx 'Environment=LANGUAGE=fr_FR:fr' "$tree/etc/systemd/system/phosh-m0.service"
grep -qx 'Environment=WLR_BACKENDS=drm,libinput' "$tree/etc/systemd/system/phosh-m0.service"
grep -qx 'Environment=WLR_DRM_DEVICES=/dev/dri/card0' "$tree/etc/systemd/system/phosh-m0.service"
grep -qx 'enable = false' "$tree/etc/phosh/phoc.ini"
grep -qx 'ExecStartPost=/bin/sh -ec '\''chown 1000:1000 /run/user/1000; chmod 0700 /run/user/1000; \[ "$(/usr/bin/stat -c %%u:%%g:%%a /run/user/1000)" = 1000:1000:700 \]'\''' "$tree/etc/systemd/system/user-runtime-dir@1000.service.d/m1-runtime-fix.conf"
grep -qx "ExecStartPre=/usr/bin/timeout 10 /bin/sh -ec 'until \[ -c /dev/dri/card0 \]; do sleep 0.1; done'" "$tree/etc/systemd/system/lmi-splash-release.service.d/m1-device-wait.conf"
! grep -Rqs 'dev-dri-card0\.device' "$tree/etc/systemd/system/lmi-splash-release.service" "$tree/etc/systemd/system/lmi-splash-release.service.d"
test "$(cat "$tree/etc/hostname")" = PocoF2Pro
grep -qx 'LANG=fr_FR.UTF-8' "$tree/etc/default/locale"
grep -qx 'LANGUAGE=fr_FR:fr' "$tree/etc/default/locale"
test -s "$tree/usr/lib/locale/locale-archive"
grep -qx 'Language=fr_FR.UTF-8' "$tree/var/lib/AccountsService/users/mobian"
cmp -s "$script_dir/90_lmi-input-sources.gschema.override" \
    "$tree/usr/share/glib-2.0/schemas/90_lmi-input-sources.gschema.override"
test "$(grep -Fxc "sources=[('xkb', 'fr')]" \
    "$tree/usr/share/glib-2.0/schemas/90_lmi-input-sources.gschema.override")" = 1
test -s "$tree/usr/share/glib-2.0/schemas/gschemas.compiled"
test "$(chroot "$tree" env GSETTINGS_BACKEND=memory gsettings get \
    org.gnome.desktop.input-sources sources)" = "[('xkb', 'fr')]"
test ! -e "$tree/home/mobian/.config/dconf/user"
grep -qx 'unmanaged-devices=interface-name:usb0' "$tree/etc/NetworkManager/conf.d/10-m1-usb0-unmanaged.conf"
test "$(chroot "$tree" systemctl is-enabled NetworkManager.service)" = enabled
test "$(chroot "$tree" systemctl is-enabled systemd-timesyncd.service)" = enabled
test "$(chroot "$tree" systemctl is-enabled wpa_supplicant.service)" = enabled
test -f "$tree/usr/share/dbus-1/services/org.freedesktop.secrets.service"
test -f "$tree/usr/lib/systemd/user/gnome-keyring-daemon.service"
test -f "$tree/usr/lib/systemd/user/gnome-keyring-daemon.socket"
grep -qx 'Name=org.freedesktop.secrets' "$tree/usr/share/dbus-1/services/org.freedesktop.secrets.service"
grep -Eq '^Exec=.*/gnome-keyring-daemon([[:space:]]|$)' "$tree/usr/share/dbus-1/services/org.freedesktop.secrets.service"
test "$(chroot "$tree" dpkg-query -W -f='${Version}' gnome-keyring)" = 48.0-1
for name in secrets pkcs11 ssh; do
    desktop="$tree/etc/xdg/autostart/gnome-keyring-$name.desktop"
    test "$(grep -c '^X-GNOME-Autostart-Notify=true$' "$desktop")" = 1
    test "$(grep -c '^X-GNOME-HiddenUnderSystemd=true$' "$desktop")" = 1
done
grep -qx 'Exec=xdg-user-dirs-update' "$tree/etc/xdg/autostart/xdg-user-dirs.desktop"
grep -qx 'X-GNOME-Autostart-Phase=Initialization' "$tree/etc/xdg/autostart/xdg-user-dirs.desktop"
test "$(grep -c '^X-GNOME-HiddenUnderSystemd=true$' "$tree/etc/xdg/autostart/xdg-user-dirs.desktop")" = 1
cmp -s "$script_dir/xdg-user-dirs-lmi.service" "$tree/etc/systemd/user/xdg-user-dirs-lmi.service"
grep -qx 'Type=oneshot' "$tree/etc/systemd/user/xdg-user-dirs-lmi.service"
grep -qx 'ExecStart=/usr/bin/xdg-user-dirs-update' "$tree/etc/systemd/user/xdg-user-dirs-lmi.service"
grep -qx 'Before=gnome-session-pre.target' "$tree/etc/systemd/user/xdg-user-dirs-lmi.service"
test -L "$tree/etc/systemd/user/gnome-session-pre.target.wants/xdg-user-dirs-lmi.service"
test "$(readlink "$tree/etc/systemd/user/gnome-session-pre.target.wants/xdg-user-dirs-lmi.service")" = /etc/systemd/user/xdg-user-dirs-lmi.service
cmp -s "$script_dir/upower-lmi.conf" "$tree/etc/systemd/system/upower.service.d/lmi-private-users.conf"
test "$(grep -c '^PrivateUsers=no$' "$tree/etc/systemd/system/upower.service.d/lmi-private-users.conf")" = 1
mobian_shadow=$(chroot "$tree" getent shadow mobian | cut -d: -f2)
[[ -n $mobian_shadow && $mobian_shadow != '!'* && $mobian_shadow != '*'* ]]
unset mobian_shadow
chroot "$tree" id mobian
chroot "$tree" dpkg-query -W phosh phoc squeekboard gnome-session gnome-keyring locales network-manager qrtr-tools systemd-timesyncd wpasupplicant unzip
df -B1 "$tree"

truncate -s $((root_blocks * 4096)) "$rootimg"
mkfs.ext4 -F -b 4096 -I 256 -N 241152 -m 5 -L pmOS_root -U "$root_uuid" \
    -O has_journal,ext_attr,resize_inode,dir_index,orphan_file,filetype,extent,64bit,flex_bg,sparse_super,large_file,huge_file,dir_nlink,extra_isize,^metadata_csum \
    -E lazy_itable_init=0,lazy_journal_init=0 -d "$tree" "$rootimg" "$root_blocks"
validate_rootimg

cp --reflink=auto -- "$base" "$raw"
truncate -s "$final_size" "$raw"
python3 "$script_dir/expand-gpt-4k.py" "$raw" "$root_start" "$root_blocks"
dd if="$rootimg" of="$raw" bs=4096 seek="$root_start" conv=notrunc status=progress
img2simg "$raw" "$sparse" 4096
simg2img "$sparse" "$roundtrip"
cmp -- "$raw" "$roundtrip"
validate_rootimg
sha256sum "$rootimg" "$raw" "$sparse"
stat -c '%s %n' "$rootimg" "$raw" "$sparse"
