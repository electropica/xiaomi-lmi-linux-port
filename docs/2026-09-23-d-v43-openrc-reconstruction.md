# D-v43 OpenRC functional reconstruction — 2026-09-23

## Result and scope

The Xiaomi lmi D-v43 configuration has been reconstructed as a Shelli/OpenRC
system. `pmbootstrap install` completed with `DONE`; the installed tree and
generated artifacts passed static validation. A subsequent operator-run phone
test reached the full OpenRC system, restored USB networking, and accepted an
SSH login as `lmi`. A subsequent manual Wi-Fi bring-up initialized the QCA6390,
created all three expected interfaces, and completed a radio scan. Finally, a
reversible rebuild removed `pmos.debug-shell`; that exact image reached OpenRC
and SSH without Telnet or `pmos_continue_boot` when launched with
`fastboot boot`.

The precise result is a **functional, evidence-based reconstruction of the
D-v43 OpenRC configuration**. It is not a bit-for-bit reproduction and is not
validated yet for display, Wi-Fi association, Wi-Fi DHCP, or Internet access.
The no-debug-shell image has been validated only as a temporary fastboot boot,
not as a persistently installed boot image.

## Correction of the earlier systemd interpretation

The previous reconstruction was a non-historical hybrid rootfs:

- `postmarketos-base-systemd` and systemd `262_rc3`;
- downstream kernel `4.19.325`;
- pmbootstrap explicitly warned: `Kernel version 4.19.325 is lower than
  systemd's minimal requirement (5.4)`.

The PID1/statx work on that rootfs remains a technically valid diagnosis of
that hybrid system. It must not be presented as diagnosis or reproduction of
historical D-v43. The historical configuration and the September correction
both select Shelli and OpenRC. The pmbootstrap prompt also stated: `Based on
your UI selection, default will result in not installing systemd.` The
recorded selection was `systemd=never`.

## Historically established facts

The June manifest, historical pmbootstrap configuration, and live Wi-Fi note
listed in `SOURCES.md` establish:

| Item | Historical D-v43 value |
| --- | --- |
| Device package | `device-xiaomi-lmi=1-r104` |
| Kernel package | `linux-xiaomi-lmi=4.19.325-r8` |
| UI / init | Shelli / OpenRC |
| User | `lmi` |
| Extra packages | `openssh-server,iw,wpa_supplicant,docker,openrc-settingsd,vim,htop` |
| Kernel SHA-256 | `38c38390ca9a474b4d29d24fb25ad9139bb58e2ad9cd88b5b601abad2f8c2d5e` |
| Userdata SHA-256 / size | `56fd50b75ff4d17c808665b3980e5dcd6b1800e9361b3bd0276fc70be31c13fb` / `1819279360` bytes |
| Boot SHA-256 | `6aee3809e2644438591f17de54d6e2c88349082239c272fb8da0f34840331cdc` |
| DTB SHA-256 | `aee89cc172734de955a11ec335b16d3a1b5da51667083b919271c2b6902d57a6` |

Historical Wi-Fi validation found `wlan0`, `p2p0`, and `wifi-aware0`; scans
succeeded, CNSS was `ONLINE`, `crash_count=0`, and the MAC address was read
from `wlan_mac.bin`.

The original June device `r104` APK, boot image, and userdata image are no
longer locally available. The September `r104` and kernel packages have
`commit=-dirty`; their identities are the September input hashes below, not
the historical hashes. Dependencies were resolved from Alpine/postmarketOS
`edge` on 2026-09-23 rather than a June repository snapshot.

## September inputs and configuration

| Input | Metadata | SHA-256 |
| --- | --- | --- |
| `postmarketos-initramfs-3.12.0-r1.apk` | `3.12.0-r1`, `noarch`, `commit=-dirty`; `init_2nd.sh` uses `init="/sbin/init"` | `888899d267302a70684251f53e2248e469c627eab73a7320c4ff30f6d1cb0afc` |
| `device-xiaomi-lmi-1-r104.apk` | `1-r104`, `aarch64`, `commit=-dirty`; OpenRC/WLAN chain; no r105 PID1 instrumentation | `dee65e97c8d56230c9507241d0a338a788bea3f804728134c45d8edb4dffc490` |
| `linux-xiaomi-lmi-4.19.325-r8.apk` | `4.19.325-r8`, `aarch64`, `commit=-dirty` | `b73209a895a826fcce058c95e9d1bff9a9ccb1f696b93f1c77eae6469201173f` |

The initial configuration hash before `pmbootstrap init` was
`2a36086d2fd988ad16cbd62fc1dbb08907fc18dbe8741fd2a70d74066b821409`.
After `init`, the effective configuration was:

```ini
aports=/home/linuxagent/pmaports-dv43-reference
work=/home/linuxagent/dv43-openrc-work
device=xiaomi-lmi
ui=shelli
user=lmi
systemd=never
build_pkgs_on_install=False
extra_packages=openssh-server,iw,wpa_supplicant,docker,openrc-settingsd,vim,htop
timezone=Europe/Paris
```

Its observed post-`init` SHA-256 on 2026-09-23 was
`f3dd2436f440bdca823c4efcde8ceeb25c332c5884393419af940da66a2be656`.

Shelli was rebuilt from the local 2026-06-24 pmaports snapshot because its UI
packages were absent from current binary `edge`. The build succeeded. Initial
indexing failed solely because the locally generated public keys were not yet
trusted; after installing those public keys in the relevant trust stores,
`pmbootstrap index` succeeded. Private keys are deliberately excluded.

## Installation command

Executed by the user:

```sh
python3 /home/linuxagent/pmbootstrap-3.10.1/pmbootstrap.py \
  --config=/home/linuxagent/dv43-openrc-reconstruction/pmbootstrap_v3.cfg \
  --work=/home/linuxagent/dv43-openrc-work \
  --aports=/home/linuxagent/pmaports-dv43-reference \
  install --no-fde --sector-size 4096 --no-sparse \
  --add "postmarketos-initramfs=3.12.0-r1,device-xiaomi-lmi=1-r104,linux-xiaomi-lmi=4.19.325-r8"
```

The install finished with `DONE`, produced a non-sparse image with 4096-byte
sectors, configured user `lmi`, and announced SSH as enabled.

## Static validation

The installed package database contains:

- `device-xiaomi-lmi=1-r104`;
- `linux-xiaomi-lmi=4.19.325-r8`;
- `postmarketos-initramfs=3.12.0-r1`;
- `postmarketos-ui-shelli=3-r8` and its OpenRC subpackage;
- `postmarketos-base-openrc`;
- `openssh-server`.

It does not contain a `systemd` package. `/sbin/init` resolves to
`/usr/bin/busybox`, and `init_2nd.sh` contains `init="/sbin/init"`.

The completion-time validation recorded `/etc/runlevels/default/sshd`. A
later read-only inspection of the still-extracted work tree found `dropbear`
in the default runlevel and no `sshd` link, while `openssh-server` remained
installed. The on-device result resolves the operational question: TCP port
22 was open, login as `lmi` succeeded, and `rc-status` showed `dropbear`
started. Thus SSH works, but the running daemon is Dropbear rather than an
OpenSSH `sshd` service.

## Initial on-device validation (debug-shell boot)

The operator performed the hardware test after the static milestone:

1. flashed `D-v43-OPENRC-20260923-rootfs.img` as userdata (SHA-256
   `7e91267713551eeec7c1790d0a100358e23b6554753d67a5df075502a69a401c`);
2. temporarily booted `D-v43-OPENRC-20260923-boot.img` (SHA-256
   `ecaa289c82840ae049ff846a5216937ffc68bd6d73b9c273dc11477c99be0075`);
3. observed the expected initramfs stop in `pmos.debug-shell`, which remains
   in the kernel command line;
4. ran `pmos_continue_boot`;
5. observed a successful `switch_root`, return of USB networking, successful
   ping to `172.16.42.1`, open TCP port 22, and successful login as `lmi`.

No phone command was issued as part of this repository update. The following
results are the operator's captured on-device evidence.

PID 1:

```text
init
```

Kernel:

```text
Linux xiaomi-lmi 4.19.325-cip128-st12-perf #9-postmarketOS SMP PREEMPT Wed Jun 24 09:10:09 UTC 2026 aarch64 Linux
```

OS:

```text
postmarketOS edge
```

Packages confirmed present:

- `device-xiaomi-lmi`;
- `linux-xiaomi-lmi`;
- `postmarketos-initramfs`;
- `postmarketos-ui-shelli`;
- `postmarketos-base-openrc`;
- `openssh-server`.

Useful services shown started in the OpenRC default runlevel:

```text
dbus
tqftpserv
openrc-settingsd
shelli
lmi-qrtr-ns
rmtfs
ofono
lmi-cnss-daemon
wpa_supplicant
networkmanager
dropbear
chronyd
rfkill
routewrangler
local
```

That initial test exposed limitations recorded at the time:

- the screen is black;
- `powerkey` is crashed;
- `postmarketos-zram-swap`, `nftables`, and `largefont` are stopped;
- `pmos.debug-shell` is still present in `/proc/cmdline`, so boot requires the
  manual `pmos_continue_boot` step;
- Wi-Fi does not start autonomously in this test and requires the manual
  trigger documented below.

## On-device Wi-Fi validation

After logging in over SSH as `lmi`, the owner manually ran:

```sh
sudo /usr/sbin/lmi-wifi-start
```

The command waited for the CNSS/WLAN sequence and completed. `iw dev` then
reported `phy#0` and all three expected interfaces:

| Interface | Type | Observation |
| --- | --- | --- |
| `wifi-aware0` | `NAN` | present |
| `p2p0` | `P2P-device` | present |
| `wlan0` | `managed` | address `[REDACTED-DEVICE-MAC]`; displayed TX power `0.00 dBm` |

CNSS reported:

```text
/sys/kernel/cnss/subsys9/state = ONLINE
/sys/kernel/cnss/subsys9/crash_count = 0
```

The owner then ran `sudo iw dev wlan0 scan`. The scan succeeded and detected
six BSS entries. No SSID was recorded, preserving local network information.

This validates complete QCA6390 initialization through interface creation,
stable CNSS operation without a recorded crash, and radio scanning. It does
not validate association with an access point, Wi-Fi DHCP, or Internet access.

## Reconstructed outputs

| Output | Size | SHA-256 |
| --- | ---: | --- |
| `xiaomi-lmi.img` | `1568669696` bytes | `7e91267713551eeec7c1790d0a100358e23b6554753d67a5df075502a69a401c` |
| `boot.img` | `52834304` bytes | `ecaa289c82840ae049ff846a5216937ffc68bd6d73b9c273dc11477c99be0075` |
| `vmlinuz` | `43233304` bytes | `47839a2bac46d3513e3b0509fe982657d93762247ecfbdc1e0386837caf1af57` |
| `initramfs` | `8714191` bytes | `38a522a2285ca1f58a0d26986d355378fbea546a2e97e3a8b41e6b862d234ded` |
| `boot-dv43-openrc-no-debug-shell-20260923.img` | `52834304` bytes | `5cc328863940b4906c94bb24969e9e0b8f37b05e0074ac339d270d9c6c4db681` |

These September hashes identify the reconstructed outputs only. None is
claimed to match a historical June artifact.

## Reversible no-debug-shell rebuild

The owner ran the reversible builder now tracked at
`scripts/build-openrc-no-debug-shell-boot.sh` (SHA-256
`9a7d17522c113394c83092441e8a1e46d7af55d6c55ba3ef6feae0fa9687ba59`).
The script is intentionally tied to the documented local paths and performs
these guarded steps:

- verifies the installed package versions, historical boot hash, deviceinfo
  layout, and single occurrence of `pmos.debug-shell`;
- archives both deviceinfo paths and the complete `/boot` tree in persistent
  state outside Git;
- temporarily removes only the exact token from the real deviceinfo target;
- runs the single pinned offline `pmbootstrap initfs build` command;
- uses the locally pinned `unpackbootimg` under QEMU to prove that the output
  cmdline equals the historical cmdline with only that token removed;
- publishes the result without overwriting an existing file, then restores and
  verifies deviceinfo and the historical `/boot` tree through an exit trap.

The build completed with `DONE`. Its persistent state is
`/home/linuxagent/dv43-openrc-reconstruction/no-debug-shell/state-20260923T183544Z-16749`.
The script reported `Validated rootfs and historical /boot restoration: OK`;
the historical boot returned to SHA-256
`ecaa289c82840ae049ff846a5216937ffc68bd6d73b9c273dc11477c99be0075`.
The copied Windows artifact was independently read back with the same new-image
SHA-256. `pmbootstrap shutdown` subsequently completed and unregistered its
binfmt handlers.

## Autonomous no-debug-shell hardware validation

The new image was launched temporarily with `fastboot boot`; it was **not**
flashed or installed persistently. Two earlier `Load Error` results occurred
while the phone was not in classic fastboot mode. After entering classic
fastboot manually, the identical image was accepted and booted immediately:

```text
Sending 'boot.img' (51596 KB) OKAY
Booting OKAY
Finished. Total time: 1.345s
```

The phone then reached the OpenRC system without a Telnet connection and
without `pmos_continue_boot`. USB networking returned automatically. TCP port
22 was open, port 23 was closed, and SSH login as `lmi` succeeded. The active
`/proc/cmdline` contained no `pmos.debug-shell` token. This validates autonomous
continuation through `switch_root` and into the previously validated OpenRC
userspace for this exact boot image.

The earlier QCA6390/CNSS/interface/scan result remains valid for the D-v43
OpenRC reconstruction, but Wi-Fi was not retriggered or retested during this
exact no-debug-shell boot. No association, Wi-Fi DHCP, or Internet access has
been validated.

## Current validation boundary and next milestone

Status: **built, statically validated, and hardware-validated through the full
OpenRC system with working USB networking, SSH access as `lmi`, complete
QCA6390 initialization, stable CNSS, a successful Wi-Fi scan, and autonomous
boot past initramfs without `pmos.debug-shell` or `pmos_continue_boot`**.

This status does not mean the new boot image is installed persistently: it was
started with `fastboot boot`. It also does not validate display output,
automatic Wi-Fi bring-up on this exact boot, access-point association, Wi-Fi
DHCP, or Internet access. The next milestone must address the black display,
the previously observed `powerkey` crash and stopped services, automate Wi-Fi
bring-up, and test association and network configuration.
