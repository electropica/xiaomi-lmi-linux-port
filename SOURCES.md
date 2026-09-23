# Evidence and source inventory

## Historical evidence (June 2026)

These paths identify the primary records used to establish the historical
D-v43 configuration. They were on the original workstation and were not
readable under these paths on the machine used to create this repository on
2026-09-23:

- `/home/julien/redmi-k30-pro-postmarketos/artifacts/images/pmos-lmi-v43-downstream-wlan-mac-persist-full-20260624.manifest`
- `/home/julien/redmi-k30-pro-postmarketos/artifacts/wsl-pmaports/pmbootstrap_v3.cfg`
- `/home/julien/redmi-k30-pro-postmarketos/notes/wifi-bringup-live-2026-06-24.md`

The records establish:

- `device-xiaomi-lmi=1-r104` and `linux-xiaomi-lmi=4.19.325-r8`;
- UI `shelli`, init system OpenRC, and user `lmi`;
- extra packages `openssh-server`, `iw`, `wpa_supplicant`, `docker`,
  `openrc-settingsd`, `vim`, and `htop`;
- successful Wi-Fi bring-up with `wlan0`, `p2p0`, and `wifi-aware0`, successful
  scans, CNSS `ONLINE`, `crash_count=0`, and the MAC read from `wlan_mac.bin`.

The historical artifact identities are recorded in `SHA256SUMS`. They are
reference identities only; the corresponding original APK/images are not
stored here and their hashes must not be attributed to September outputs.

## Frozen local inputs (September 2026)

- `/home/linuxagent/dv43-pmbootstrap-work/packages/edge/x86_64/postmarketos-initramfs-3.12.0-r1.apk`
  (`pkgver=3.12.0-r1`, `arch=noarch`, `commit=-dirty`)
- `/home/linuxagent/dv43-pmbootstrap-work/packages/edge/aarch64/device-xiaomi-lmi-1-r104.apk`
  (`pkgver=1-r104`, `arch=aarch64`, `commit=-dirty`)
- `/home/linuxagent/dv43-pmbootstrap-work/packages/edge/aarch64/linux-xiaomi-lmi-4.19.325-r8.apk`
  (`pkgver=4.19.325-r8`, `arch=aarch64`, `commit=-dirty`)
- `/home/linuxagent/dv43-openrc-reconstruction/pmbootstrap_v3.cfg`
- pmaports snapshot/work tree: `/home/linuxagent/pmaports-dv43-reference`
- pmbootstrap: `/home/linuxagent/pmbootstrap-3.10.1/pmbootstrap.py`

The September `r104` package contains the OpenRC services and D-v43 WLAN
chain, but not the PID1 instrumentation introduced in `r105`. Its `-dirty`
metadata and its different checksum prove that it is not the missing original
June package. Likewise, the reconstructed kernel package has the historical
version number but not a demonstrated historical binary identity.

`postmarketos-ui-shelli` was no longer available from current binary `edge`.
The user rebuilt `postmarketos-ui-shelli=3-r8` and
`postmarketos-ui-shelli-openrc=3-r8` from the local 2026-06-24 pmaports
snapshot. Local indexing first failed because the generated public signing
keys were not trusted. Adding the public keys to the relevant local trust
stores allowed `pmbootstrap index` to succeed. No private key, and currently
no public key, is versioned here.

## Final local package index

- `device-xiaomi-lmi=1-r104`
- `linux-xiaomi-lmi=4.19.325-r8`
- `postmarketos-initramfs=3.12.0-r1`
- `postmarketos-ui-shelli=3-r8`
- `postmarketos-ui-shelli-openrc=3-r8`

## Hardware validation record (2026-09-23)

The on-device observations in the dated milestone note were supplied directly
by the operator after flashing the reconstructed userdata image and temporarily
booting the reconstructed boot image. No phone command was run while preparing
this repository. The record includes PID 1, `uname`, OS identification,
installed package names, `rc-status`, USB-network reachability, TCP port 22,
and a successful SSH login as `lmi`.

The operator then supplied a second on-device record for the same reconstructed
userdata and boot artifacts. It covers the manual `lmi-wifi-start` invocation,
`iw dev`, CNSS state and crash count, and a successful scan with the BSS count.
SSID values were deliberately not recorded. The tested artifact identities
were:

- userdata SHA-256: `7e91267713551eeec7c1790d0a100358e23b6554753d67a5df075502a69a401c`;
- boot image SHA-256: `ecaa289c82840ae049ff846a5216937ffc68bd6d73b9c273dc11477c99be0075`.
