# Mobian status

## M0 BASE — validated on hardware

Validated on Xiaomi `lmi` hardware with the downstream D-v43 kernel.

Confirmed:

- Debian GNU/Linux 13 (trixie)
- systemd as PID 1
- root filesystem on `/dev/loop0p2`
- USB RNDIS preserved across switch_root
- `usb0` configured as `172.16.42.1/16`
- SSH root login by public key
- kernel `4.19.325-cip128-st12-perf`

The M0 BASE image is intentionally not stored in Git.

## M0 DISPLAY — VALIDATED ON HARDWARE

Validated on Xiaomi `lmi` hardware:

- KMS continuous-splash release with Debian `modetest` works
- seatd with `SEATD_VTBOUND=0` works
- Weston 14.0.2 DRM/Pixman with kiosk shell works
- `DSI-1` drives the physical panel
- a red background is physically visible
- downstream `msm_drm` requires the tracked Weston workaround that
  de-duplicates indistinguishable formats in the legacy no-`IN_FORMATS`
  fallback

See `notes/mobian-m0-display-hardware-validation-2026-09-02.md` for the exact
experimental evidence and backend identities.

## M1 PHOSH — VALIDATED ON HARDWARE

The M1 graphical session and basic Phosh interaction were validated on Xiaomi
`lmi` hardware. The clear-KMS marker was visible, Phoc acquired `DSI-1` with
the Pixman renderer, and the Phosh lock screen appeared. Touch input and the
swipe-up gesture worked, the passcode prompt allowed the session to be
unlocked, and the Phosh desktop was then displayed with its applications and
icons.

This milestone validates the graphical bring-up and basic Phosh interaction.
It does not validate GPU acceleration, every Phosh function, or readiness for
daily use.

## M1 GPU — TURNIP/KGSL VULKAN ENUMERATION VALIDATED ON HARDWARE

An isolated native Debian Trixie arm64 build of Mesa 25.0.7, configured with
Gallium Zink, Vulkan Freedreno and `freedreno-kmds=msm,kgsl`, successfully
loaded Turnip's KGSL backend on Xiaomi `lmi`. Turnip opened
`/dev/kgsl-3d0`, identified `Turnip Adreno (TM) 650`, and completed
`vulkaninfo` physical-device enumeration with exit status zero. The validated
`libvulkan_freedreno.so` SHA-256 is
`dc46ac80f2322142e5ba17235e7cfd019f13c41157a34965cc5494622b84324d`.

This validates Vulkan enumeration only. GPU command submission, rendered
output, EGL, OpenGL/OpenGL ES through Zink, Wayland/dma-buf interoperability,
GBM, KMS scanout and accelerated Phoc remain unvalidated. See
`notes/mobian-m1-a650-turnip-kgsl-hardware-validation-2026-09-08.md`.

## M1 GPU — ZINK/TURNIP/KGSL OFFSCREEN RENDER VALIDATED ON HARDWARE

The isolated native Debian Trixie arm64 Mesa 25.0.7 runtime has now completed
a real OpenGL ES 3.2 offscreen render through EGL surfaceless, Gallium Zink,
Vulkan Turnip and KGSL on Adreno 650. A dedicated 16x16 pbuffer test submitted
`glClear`, synchronized with `glFinish`, read a pixel back and obtained
`PIXEL_RGBA=64,128,191,255` for the requested `(0.25, 0.50, 0.75, 1.0)`
colour. `PIXEL_CHECK=PASS` and the process returned zero.

This supersedes enumeration as the strongest validated GPU milestone, but it
remains offscreen. A subsequent GPU-58 test validated process-local dma-buf
export/re-import through Turnip/KGSL; Wayland presentation and interoperability
with downstream `msm_drm` remain separate. See
`notes/mobian-m1-a650-zink-turnip-kgsl-offscreen-hardware-validation-2026-09-08.md`.

## M1 GPU — GPU-66 PATCHED CROSS-DEVICE ZINK RENDER VALIDATED ON HARDWARE

GPU-66 separately validated the corrected cross-compiled Mesa 25.0.7 path.
Its opt-in Zink change selected the isolated GPU-53 Turnip/KGSL device when
the surfaceless EGL display could not be matched through the normal DRM
display-device path. The isolated stack created an OpenGL ES context, cleared
a 1x1 RGBA8 pbuffer to green, completed the work and read back the exact value
`0,255,0,255` with exit status zero.

This path directly links the matching `libEGL.so.1` and `libGLESv2.so.2`
frontends to `libgallium-25.0.7.so`, where Zink is built in. It does not use
`zink_dri.so`, `libdril_dri.so`, GBM, GLX, Wayland or X11. The system Vulkan
loader remained in use, while EGL, GLES, Gallium and the GPU-53 Turnip ICD
were selected from an isolated bundle. System Mesa was not replaced. Phoc and
Phosh stayed running and `DSI-1` stayed connected; no GPU fault or kernel
crash occurred. This validates one tiny offscreen GLES operation only, not
desktop acceleration or presentation. See
`notes/mobian-m1-gpu66-patched-zink-turnip-kgsl-hardware-validation-2026-09-09.md`.

## M1 GPU — TURNIP/KGSL DMA-BUF EXPORT/REIMPORT VALIDATED ON HARDWARE

The isolated ARM64 GPU-57 self-test created a 4096-byte exportable Vulkan
buffer through Turnip/KGSL, wrote a deterministic pattern with the GPU,
exported its allocation as a dma-buf, imported the same dma-buf into a second
Vulkan allocation, accessed it through the imported buffer and verified every
word through an independent readback buffer. All capability, ownership,
submission, content and cleanup checks passed; `GPU58_SELFTEST_RC=0`.

This validates Turnip/KGSL dma-buf export and same-driver re-import on real
hardware. It does not validate PRIME import by downstream `msm_drm`, KMS
framebuffer creation or scanout, display formats/modifiers, UBWC, cross-driver
synchronization, Wayland or accelerated Phoc. See
`notes/mobian-m1-a650-turnip-kgsl-dmabuf-hardware-validation-2026-09-08.md`.

## M1 PHOSH SPONTANEOUS DISPLAY WAKE — USERSPACE CAUSE AND WORKAROUND VALIDATED

WAKE7 through WAKE17 traced the spontaneous display-on cycle to the
`gnome-settings-daemon` power plugin's session-idle policy. A Mutter
`IdleMonitor` watch owned by `gsd-power` fired immediately before the
ScreenSaver/DisplayConfig activity that re-enabled `DSI-1`; the display was
disabled again roughly 15 seconds later. Changing the configured inactive
timeouts from 900 to 1200 seconds moved the long watches from 900000/450000 ms
to 1200000/600000 ms, establishing the causal mapping.

Setting both `sleep-inactive-ac-type` and `sleep-inactive-battery-type` to
`'nothing'` removed those long autosuspend watches. A passive 700-second
validation then observed no spontaneous `DSI-1` on/off event and no new
`gsd-power` error. The final validated runtime state restores both timeouts to
900 seconds while retaining type `'nothing'` for AC and battery. This explains
the observed symptom through userspace policy; it does not establish a general
kernel wake-source result or validate every suspend/resume path. See
`notes/mobian-m1-gsd-power-spontaneous-wakeup-validation-2026-09-06.md`.

## M1 WIFI — VALIDATED ON HARDWARE

Manual bring-up on `lmi` with D-v43 completed the QCA6390 CNSS/WLFW sequence,
created `wlp1s0`, scanned nearby BSS entries, associated with WPA2, obtained a
DHCP lease and default route, and preserved the independent `usb0` SSH path.
The kernel dynamically selected `bd_j11gl.elf`; it must not be overridden with
the older historical `bd_j11.elf` default.

The systemd implementation under `mobian/m1-phosh/wifi` and the integrated
Debian `wpasupplicant` are now validated on hardware in M1 REPRO v3. The image
completed firmware bring-up, `FW_READY`, qcacld probe, WLAN creation,
automatic SSID listing, CLI WPA2 association, DHCP, DNS, and Internet access
while preserving USB SSH. No Wi-Fi profile or credential is tracked. See
`notes/mobian-m1-wifi-hardware-validation-2026-09-03.md`.

## M1 REPRO v2 IMAGE — HARDWARE-TESTED / CORRECTIONS REQUIRED

The reproducible M1 Phosh/Wi-Fi rootfs and phone images were built and
validated on the host. The final ext4 has the expected `pmOS_root` label and
UUID, passes `e2fsck -fn`, and the Android sparse image round-trips bit-for-bit
to the final raw image. Package installation, service enablement, Phosh/Pixman
configuration, the AArch64 property shim, and the absence of proprietary
Android payloads in the image were checked.

This exact image subsequently booted on the phone. Its low-level systemd Wi-Fi
automation succeeded, and its Phosh/Pixman stack worked when the splash unit
was started without its stale `dev-dri-card0.device` dependency. Automatic
display startup was blocked by that inherited dependency; Wi-Fi association
needed runtime installation of `wpasupplicant`; and time synchronization
needed runtime installation of `systemd-timesyncd`. Those findings produced
the recipe corrections subsequently validated in v3. See
`notes/mobian-m1-repro-v2-hardware-validation-2026-09-04.md`.

## M1 REPRO v3 — VALIDATED ON HARDWARE

The v3 userdata image booted on Xiaomi `lmi` with D-v43 and reached Phosh
automatically without SSH intervention. The corrected splash unit has no
`dev-dri-card0.device` dependency; its bounded wait for the real character
device allowed clear-KMS, seatd, Phoc/Pixman on `DSI-1`, the lock screen, and
the unlocked Phosh desktop to start normally.

The integrated low-level QCA6390 automation and `wpasupplicant 2:2.10-24`
provided WLAN discovery, scanning, CLI WPA2 association, DHCP, routing, DNS,
and Internet access. Integrated `systemd-timesyncd 257.13-1~deb13u1`
synchronized the system clock after networking became available; this does
not repair the incorrect hardware RTC.

After the v3 image validation, a clean runtime experiment additionally
validated `PAMName=login` with `XDG_SEAT=seat0`: logind created an active
Wayland `Class=user` session on graphical `seat0` with `VTNr=0`, Phoc remained
functional through seatd, and the Phosh Polkit agent registered for that
session. NetworkManager scan, radio and network-control authorization passed
for the real GNOME Settings PID and D-Bus name, and Wi-Fi controls worked in
the UI. This setup is now tracked by the M1 recipe but still requires
post-rebuild hardware validation; it was not present in the original v3
image. `settings.modify.system` correctly remains an administrative action.

That persistent session setup was subsequently validated in v4. Still open
are timezone control, UPower/battery reporting, colored boot rectangles,
power-button suspend/wake, screenshot integration, touch/UI latency, observed
Settings launch instability, and the eventual default application set.
Administrative system-connection editing continues to require its expected
authentication rather than a policy bypass. See the v3 hardware note and
`notes/mobian-m1-phosh-logind-polkit-validation-2026-09-04.md`.

## M1 REPRO v4 — VALIDATED ON HARDWARE / KEYRING INTEGRATION TO REVALIDATE

M1 REPRO v4 was built from commit `d1469e8`; its Android sparse userdata
SHA-256 is `84361c4d7a1bced22046e8359d17865a55983ab730a15bd0489ed98d40fa8c92`.
It booted automatically into the validated clear-KMS, seatd, Phoc/Pixman and
Phosh path. The persistent PAM/seat configuration created an active Wayland
logind user session on graphical `seat0` without a VT, and the Phosh Polkit
agent registered correctly. The lock screen, touch, swipe-up, passcode unlock
and desktop remained functional.

The remaining Wi-Fi GUI failure was not caused by Phosh's process retaining
the lingering user manager's audit session. NetworkManager registered the
Phosh NetworkAgent and sent `SaveSecrets` and `GetSecrets` on the fixed
SecretAgent D-Bus path. Phosh returned
`org.freedesktop.NetworkManager.SecretAgent.Failed` because
`org.freedesktop.secrets` was unavailable: v4 contained `libsecret` but not
`gnome-keyring`. Installing Debian `gnome-keyring 48.0-1` at runtime supplied
the activatable Secret Service, and GNOME Settings Wi-Fi connection worked
immediately without reboot or manual daemon startup.

The recipe now pins `gnome-keyring 48.0-1`. Its presence and automatic Secret
Service activation remain to be validated in the next rebuilt image. No
credential, connection profile, permissive Polkit rule or forced daemon start
is tracked. Detailed evidence is in
`notes/mobian-m1-repro-v4-hardware-validation-2026-09-04.md`.

## M1 REPRO v5 — RUNTIME STARTUP FIXES VALIDATED / REBUILD REQUIRED

M1 REPRO v5 was built from commit `593676f`; its Android sparse userdata
SHA-256 is `b4adb244c686dcbbc1c10cce9087c792f69b8410080995893336ddd1f6a3f142`.
It retained the validated automatic display, PAM/logind/seat, Phosh, touch and
GUI Wi-Fi paths, including first-time PSK entry through the Secret Service.

The integrated keyring package initially added a roughly 90-second delay:
three legacy XDG autostarts requested GNOME startup notification after the
systemd user service had already started the same daemon. Runtime overrides
adding `X-GNOME-HiddenUnderSystemd=true` to the `secrets`, `pkcs11`, and `ssh`
entries removed the timeout while preserving `org.freedesktop.secrets` and GUI
Wi-Fi operation.

UPower separately delayed Phosh by two 25-second D-Bus timeouts because
systemd 257.13 could not create the `PrivateUsers=yes` user namespace on D-v43
and exited with `217/USER` before starting `upowerd`. A drop-in changing only
`PrivateUsers=no` started UPower successfully; all other sandboxing remained.
With both corrections applied, Phosh reported ready after 1.65 seconds and the
lock screen appeared at roughly 40 seconds from boot.

Both hardware-tested corrections are now represented in the recipe but still
require validation from a rebuilt image. Detailed evidence is in
`notes/mobian-m1-repro-v5-hardware-validation-2026-09-05.md`.

## M1 REPRO v6 — VALIDATED ON HARDWARE

M1 REPRO v6 was freshly built from commit `d054ba8`; its Android sparse
userdata is 1,881,808,716 bytes with SHA-256
`b6e7c3bbb57e4edd1f17c829ded37b7c8ce94b883329d34d983cb05f44a30a00`.
The build completed with a clean filesystem check, the Windows transfer hash
matched, and all three sparse userdata segments flashed successfully.

This image reproduces both persistent startup corrections. The three GNOME
Keyring autostarts no longer cause their roughly 90-second registration
timeout, while the systemd user daemon and `org.freedesktop.secrets` remain
available. The UPower drop-in reports `PrivateUsers=no`; `upower.service`
starts successfully without `217/USER`. GNOME Session started in about 120 ms,
UPower acquired its D-Bus name in under one second, and Phosh reported ready
in 1.60 seconds.

The active Wayland logind session remained attached to graphical `seat0` with
no VT. The lock screen, touch and passcode unlock worked. From a freshly
flashed image, GNOME Settings displayed the Wi-Fi secret prompt, accepted a
user-entered credential, connected successfully, and allowed automatic NTP
synchronization. No SSID, profile or credential is tracked.

The observed lock screen appeared around 50 seconds from boot. The difference
from the corrected v5 runtime boot occurred before `phosh-m0.service` and is
not attributed to Keyring or UPower. Dynamic battery tracking remains
unvalidated despite Phosh displaying 100%; `getty@tty1.service`, colored
clear-KMS rectangles, onscreen GPU presentation beyond the subsequently
validated Zink/Turnip/KGSL offscreen render, and modem/SIM remain open. See
`notes/mobian-m1-repro-v6-hardware-validation-2026-09-05.md`.

## M1 REPRO v7 — VALIDATED ON HARDWARE / FRENCH OSK DEFAULT TO REVALIDATE

M1 REPRO v7 was built from commit `d054ba8`; its Android sparse userdata
SHA-256 is `3b514d386b486137d8c730a0c6f1e970f1aa10116720669f9b66d920902d1015`.
Flash and D-v43 boot passed. The lock screen, touch, unlock, USB SSH, GUI
Wi-Fi, GNOME Keyring Secret Service, UPower with `PrivateUsers=no`, the active
Wayland logind session on `seat0`, and network-triggered NTP synchronization
remained functional. The former Keyring and UPower timeout messages did not
recur.

The measured critical chain corrects an earlier analytical assumption: WLAN
bring-up was on the path to Phosh on this boot. The effective chain was
`lmi-wlan-on.service` -> `NetworkManager.service` -> `network.target` ->
`systemd-user-sessions.service` -> `user@1000.service` ->
`phosh-m0.service`. The eight-second `fs_ready` delay and bounded WLAN wait
therefore contributed directly. Clear-KMS completed on a separate branch at
about 5.4 seconds and was not critical. This milestone does not change any of
those dependencies.

Battery data was dynamically validated while physically unplugged: capacity
fell from 100% to 95%, battery and BMS sysfs values agreed, and UPower exposed
`discharging`, `on-battery=yes`, an energy rate and a time-to-empty estimate.
Raw downstream inconsistencies remain: `battery/status` still said `Charging`
and USB still reported present/online while unplugged. Reconnection, charging,
return to 100% and low-battery behavior are not yet tested.

The French OSK cause was also validated at runtime. Changing
`org.gnome.desktop.input-sources sources` from `[('xkb', 'us')]` to
`[('xkb', 'fr')]` changed Squeekboard immediately from QWERTY to AZERTY and
survived a complete reboot without reflashing userdata. The recipe now
provides this as a textual GSettings schema override and compiles it without a
user D-Bus session or a prebuilt dconf database. Delivery from a fresh rebuilt
image remains to be validated. Full evidence is in
`notes/mobian-m1-repro-v7-hardware-validation-2026-09-05.md`.

## M1 REPRO v8 — AZERTY VALIDATED / XDG USER DIRS FIX TO REVALIDATE

The recipe-provided `[('xkb', 'fr')]` default reached Squeekboard on hardware;
the French layout loaded and AZERTY was functional. A distinct startup barrier
was then isolated: the Debian `xdg-user-dirs.desktop` entry ran in GNOME
Session's `Initialization` phase, while GLib's child watcher failed with
`waitid(..., pidfd=...) = EINVAL` on D-v43. Because process exit was not
observed, GNOME Session waited about 90 seconds before reporting that the
application had failed to register. Squeekboard started immediately after the
timeout.

The recipe now hides only that legacy autostart under systemd and preserves
`xdg-user-dirs-update` as a device-specific user oneshot before
`gnome-session-pre.target`. The global GNOME timeout, Phosh session definition,
Squeekboard, Keyring, UPower, networking and boot ordering are unchanged. The
new oneshot and removal of the 90-second barrier require validation from a
fresh image.

## M1 REPRO v9 — XDG USER DIRS FIX VALIDATED ON HARDWARE

M1 REPRO v9 was freshly built from commit `e7e63ba`; its Android sparse
userdata SHA-256 is
`17e5c0427358803beac9f2313caa008fd3303119c0020ebacc42a45a15f9b401`.
Userdata flash and D-v43 boot passed.

The device-specific `xdg-user-dirs-lmi.service` completed successfully with
exit status zero. All eight localized user directories were created under the
`mobian` home. The legacy `xdg-user-dirs.desktop` registration timeout was
absent, Squeekboard appeared immediately after unlock, loaded `Resource: fr`,
and provided the integrated French AZERTY layout on the fresh image.

This validates the targeted workaround without changing GNOME's global phase
timeout or removing `xdg-user-dirs-update`. The broader D-v43 incompatibility
where GLib child watching through `waitid(..., pidfd=...)` returns `EINVAL`
remains open for other short-lived processes. See
`notes/mobian-m1-repro-v9-hardware-validation-2026-09-05.md`.

## M1 BLUETOOTH SLIM/PDR — VALIDATED AUTOMATICALLY ON HARDWARE

A bounded post-v9 runtime experiment validated the previously missing
Qualcomm process-domain path without changing the M1 image. Before the test,
the ADSP was not running, QRTR exposed no Service Registry Locator `64/1/1`,
NGD had never runtime-resumed, and no BTFM SLIM device existed. D-v43's
service-locator client otherwise waits `3000000` ms (3000 seconds) before its
late SSR fallback, so booting the ADSP first could not provide NGD with a
timely `appsngd1` / `avs/audio` domain resolution.

The stock Android `pd-mapper`, given a private read-only view of the existing
stock `firmware_mnt`, published `64/1/1`. It consumed the stock PDR maps,
including `adspua.jsn`, and resolved `avs/audio` to
`msm/adsp/audio_pd`, QMI instance 74. After exactly one ADSP boot, the ADSP
reached `ONLINE` with `crash_count=0`; QRTR exposed notifier `66/1/74` and
SLIM control service `769/1/0`; the audio domain notified UP; and NGD recorded
runtime activity. SLIM then created `btfmslim_slave` and
`btfmslim_slave_ifd`, with the QCA6390 slave bound to `btfmslim-driver`.
Phosh, touch, Wi-Fi and general device stability were unchanged after the
experiment.

M1 REPRO v11 subsequently validated the persistent implementation from a
freshly flashed image with no manual radio-domain intervention. The three
tracked units prepared the stock firmware links, kept the stock pd-mapper
running behind a private read-only bind, passed the bounded locator/PDR
barrier, and performed exactly one guarded ADSP boot. ADSP reached `ONLINE`
with `crash_count=0`; all three QRTR services and both BTFM devices appeared;
and the QCA6390 slave bound automatically. The integrated `codex-lmi` public
diagnostic key also provided root SSH with the expected permissions and no
private key was installed by the recipe. No proprietary binary or map is
stored in Git.

Phosh, unlock, French OSK, Wi-Fi and general stability remained functional.
`getty@tty1.service` remains the sole known failed unit and is non-blocking on
the `CONFIG_VT=n` kernel. `/sys/class/bluetooth` is still empty, so HCI creation
is the next distinct problem. Occasional USB/RNDIS recovery by cable reconnect
also remains an open observation. See
`notes/mobian-m1-bluetooth-slim-pdr-runtime-validation-2026-09-05.md`.
See also `notes/mobian-m1-repro-v11-hardware-validation-2026-09-05.md` for the
fresh-image evidence.

## M1 BLUETOOTH HCI/HASTINGS — ACTIVE HCI VALIDATED

The layer following the validated BTFM SLIM binding has now been identified
statically. On `lmi`, Bluetooth HCI uses QUPv3 SE6 at `0x998000` through the
`qcom,msm-geni-serial-hs` device `/dev/ttyHS0`; there is no Bluetooth serdev
child in the Xiaomi DT. The stock QTI HAL opens that UART directly, uses the
separate `/dev/btpower` interface and identifies the controller as QCA6390
`hastings`, revision `HASTINGS_VER_2_0`.

D-v43's `btfmslim-driver` supplies only the separate SLIM audio/FM path and is
not expected to register an HCI controller. HCI uses the GENI UART and N_HCI
line discipline. The V2 micro-backport now adds the QCA6390 type, Hastings
firmware selection, protocol adaptations and a NULL-safe non-serdev path. It
enables HCI UART, H4 and QCA while keeping `SERIAL_DEV_BUS=n` and controller
power external to `hci_qca`.

The first rebuilt candidates exposed an unrelated historical downstream VFS
defect: legacy block mounts lost `fc->source` and failed with `ENOENT` before
the filesystem driver. Those failures are not Bluetooth-discriminating. The
previously hardware-validated `do_new_mount()` safety net was restored, after
which HCI UART plus H4, generic QCA without the lmi selector, and the complete
QCA6390 V2 configuration each RAM-booted through rootfs and userspace. The
complete candidate behaved normally on hardware, establishing static
integration boot-safety.

The controlled Phase A attach has now also passed. Userspace opened
`/dev/ttyHS0` at 115200 with RTS/CTS, selected `N_HCI=15`, flags `0x2` and
`HCI_UART_QCA=8`, and obtained `hci0`. Automatic `qca_setup()` selected and
successfully downloaded the stock `qca/htbtfw20.tlv` and `qca/htnv20.bin`,
then completed its final HCI Reset. Cleanup restored N_TTY and termios,
removed `hci0` and left the UART, Phosh, RNDIS and Wi-Fi stable.

The reported controller value `0x02000200` is the driver's composite
`get_soc_ver()`, not the raw Hastings `soc_id` expectation `0x400a0200`:
the 32-bit calculation combines the shifted low 16 bits of `soc_id` with
`rome_ver=0x0200`. It yields `rom_ver=0x20`, directly selecting the correct
Hastings 2.0 files; this is not an endian issue or fallback.

Levels A (boot-safety), B (controlled N_HCI attach), C (version, PATCH, NVM
and final Reset) and controlled HCI activation are therefore PASS. Phase B
brought `hci0` UP and bound a raw HCI socket. After three seconds idle, one
explicit Read Local Version command (`0x1001`) returned status `0x00` with HCI
and LMP version `0x0b`, Qualcomm manufacturer `0x001d` and LMP subversion
`0x27ec`. `CMD_TX` and `EVT_RX` each increased by exactly one, proving a real
bidirectional controller exchange rather than a cached kernel query.

No IBS debugfs counters were available. Successful traffic after an idle
period longer than the two-second IBS timeout supports only an indirect
`IBS_FUNCTIONAL=INFERRED` result, not direct sleep/wake proof. The observed
address `00:00:00:00:5a:ad` has now been traced through the stock Android
provisioning path. The stock `/vendor/bin/nv_mac` opens Xiaomi's proprietary
QMI service `0xffe4`, sends message `0x0002` with Bluetooth NV operation
`0x01bf`, receives the six-byte address payload and writes
`/data/vendor/mac_addr/bt.mac`. `init.mi.btmac.sh` then converts that binary
value and sets `persist.vendor.service.bdroid.bdaddr`, which is consumed by
the QTI Bluetooth HAL. Static decoding also identified WLAN operation
`0x1246`. The tested `htnv20.bin` contains the same observed address in its BD_ADDR
field. Separately, static analysis establishes the stock Android QMI
provisioning mechanism, but because no QMI request was executed it does not
yet prove what operation `0x01bf` returns on this individual handset. `HCIDEVDOWN` and attach rollback restored N_TTY and
termios, freed the UART and removed `hci0` without affecting Phosh, RNDIS or
Wi-Fi. BlueZ, scan, pairing and real Bluetooth connections remain untested.

One attempted re-attach without resetting the already initialized controller
timed out during PATCH. A controlled `bt_power` OFF/ON cycle disabled and
re-enabled reset, SW_CTRL and all five QCA6390 rails; the subsequent continuous
setup and Phase B passed. This establishes a power-cycle prerequisite for a
fresh repeated bring-up, not a protocol regression. A transient
`Frame reassembly failed (-84)` during the successful retry did not prevent
version, PATCH, NVM, Reset, HCI activation or later traffic.

See `notes/mobian-m1-qca6390-hastings-hci-design-2026-09-05.md` and
`notes/mobian-m1-qca6390-v2-boot-safety-validation-2026-09-06.md`. The
stock Android BD_ADDR provisioning mechanism is now statically established.
The next Bluetooth milestone is BlueZ integration followed by controlled scan
and pairing validation.

## M1 EXTERNAL MODEM SDX55 — NOMINAL ESOC/MISSION-MODE PATH VALIDATED

DV121 reached the Qualcomm Sahara loader environment on the external SDX55M.
The validated runtime DT/ESOC identity is `qcom,ext-sdx55m`, `SDX55M`, PCIe,
link information `0306_02.01.00`; `/dev/esoc-0` and `/dev/subsys_esoc0` are
present. The userspace request engine must register before opening the SSR
subsystem device because that open remains blocked in `mdm_subsys_powerup()`
during boot. DV119 implements the required split: its main thread waits for
ESOC requests while a second thread opens `/dev/subsys_esoc0`. The validated
ARM64 helper SHA256 is
`966a1810f7e43fc398e10d91fd7f3c5db25eb9d6485c3ecf67a09cbfec852bbf`.

The Xiaomi
`lmi_global_images_V14.0.1.0.SJKMIXM_20230317.0000.00_12.0_global` ROM stores
the SDX55 firmware in the FAT16 `images/NON-HLOS.bin` container under
`image/sdx55m`. Eighteen files were extracted for analysis. The MHI driver
maps PCI device `0x0306` to `sdx55m/sbl1.mbn`; the extracted SBL1 is 548056
bytes with SHA256
`0fd2fdaf19831c8ff482ca77ca236ee282101c9bdf5ab7b46dc4e24a484e84dc`.
It was exposed as `/lib/firmware/sdx55m/sbl1.mbn` and revalidated after the
current RAM boot. The earlier `Error loading fw, ret:-2` is therefore no
longer the active blocker.

The historical delayed `ESOC_RUN_STATE` experiment exposed an ESOC state race:
a late run notification overwrote an already recorded `CRASH`, causing the
following forced SSR shutdown to skip its crash teardown and leaving the SSR
worker blocked in a second `mdm_subsys_powerup()`. DV166 captured the sole
`ssr_wq` worker in that exact stack. The B1 kernel correction preserves
`CRASH` and `PEER_CRASH` on a late run notification while still completing
`pon_done` and `ssr_ready`.

B1 was reviewed adversarially, built, packaged with unchanged ramdisk/DTB and
RAM-booted. Mobian, Phoc, Phosh, USB and Wi-Fi remained functional. DV179 then
reached `ESOC_REQ_IMG`, PCI `17cb:0306`, MHI BL and Sahara with zero crashes.
A one-shot no-reset validation client completed the 17-entry Sahara transfer;
QMI0/QMI1, RMNET_CTL, DIAG, IP_HW0, `rmnet_mhi0` and the SSCTL service appeared.
DV186 sent one nominal `ESOC_BOOT_DONE`: the power-up thread returned, the
subsystem became `ONLINE`, mission mode remained present and `crash_count`
stayed zero without a new kernel error.

This validates the complete nominal SDX55 ESOC path under B1, not cellular
service, voice, SMS or data. The precise `CRASH -> late RUN_STATE -> SSR` race
has not been reproduced on B1 hardware, so it is not claimed as materially
closed. See `notes/mobian-m1-sdx55-dv121-sahara-milestone-2026-09-06.md` and
`notes/mobian-m1-sdx55-esoc-b1-validation-2026-09-06.md`.

DV191 through DV207 then audited the post-crash `remotefs_sahara` path and the
runtime EFS synchronization design entirely offline. The exact Xiaomi
`/vendor/bin/ks` was recovered and shown to write received EFS regions directly
to persistent `mdm1m9kefs*` destinations with the historical Qualcomm
invocation, so that invocation is not treated as read-only and was not
executed. Static tracing also rejected host-side close as a demonstrated
Sahara termination mechanism.

DV207 therefore extends the validated DV196 in-memory consume-all/write-none
model with the normal Sahara terminal sequence
`TRANSFER_COMPLETE -> RESET -> RESET_RESP -> PROTOCOL_COMPLETE`. RESET cannot
be constructed before exact coverage of all declared regions, RESET_RESP is
strictly validated, and the extension does not add filesystem, device or MHI
transport capability. Both 32-bit and 64-bit synthetic paths pass 290 tests
with zero failures in normal and ASan/UBSan builds. This is an offline protocol
model only: no real EFS MHI probe is authorized and `REAL_PROBE=NOT_SAFE`.
See
`notes/mobian-m1-sdx55-dv207-remotefs-reset-offline-validation-2026-09-07.md`.

## Repository policy

Generated `.img`, `.ext4`, Android sparse images, root filesystems, private
keys, caches and other build artifacts are intentionally excluded from Git.
