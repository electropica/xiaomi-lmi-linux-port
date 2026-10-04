# Mobian status

## Current Mobian userspace state — updated 2026-10-03

The current validated Mobian/Phosh userdata family is based on the external
`archi-validation-02` golden image and its `daily-base` derivative. The
golden image booted with the durable original D-repro D-v43 boot; Phosh,
touch/unlock, DSI-1, GPU72 GLES2/Zink/Turnip/KGSL acceleration, GNOME Console
and Calculator were exercised. `daily-base` separately validated the
time-seed correction and responsive unlock with only Chatty's daemon
autostart hidden. Exact image identities and boundaries are in
[`current build status`](CURRENT-BUILD.md).

`daily-base-audio-fw-test` is an experimental userspace profile paired with
a temporary reset-GPIO diagnostic boot, not a replacement for the durable
original boot. WCD938x and TFA9874 now bind, ALSA registers, and direct S16_LE
and S24_LE playback completes. Later S32_LE frontend tests produced clear
music, confirmed through a local PipeWire speaker route on 2026-10-03.
Microphone capture and KRecorder WAV saving were subsequently tested on
2026-10-04 (see the audio integration record below). Full UCM2, headset/earpiece
routing and durable boot deployment remain pending.

The proprietary TFA firmware is external and is never tracked. Neither the
diagnostic boot nor any userdata image is stored in Git. Kernel and userdata
bit-for-bit reconstruction from all sources is not demonstrated. See the
[`2026-09-29 audio progress note`](../validation/archi-validation-02-audio-progress-2026-09-29.md).

The M0 Weston result below belongs to a distinct Mobian/M0 environment. It is
not evidence that Weston works on the separate D-v43/OpenRC system, whose
Weston experiments remained black.

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

See `docs/validation/mobian-m0-display-hardware-validation-2026-09-02.md` for the exact
experimental evidence and backend identities.

This success is specific to that M0 Mobian rootfs and display setup. It must
not be merged with the later D-v43/OpenRC Weston 14 tests; see
[`D-v43 Weston boundary`](../validation/d-v43-weston14-boundary-2026-09-26.md).

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
`docs/validation/mobian-m1-a650-turnip-kgsl-hardware-validation-2026-09-08.md`.

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
`docs/validation/mobian-m1-a650-zink-turnip-kgsl-offscreen-hardware-validation-2026-09-08.md`.

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
`docs/validation/mobian-m1-gpu66-patched-zink-turnip-kgsl-hardware-validation-2026-09-09.md`.

## M1 GPU — GPU-67 PROGRAMMABLE GLES2 SHADER DRAW VALIDATED ON HARDWARE

Building on GPU-66's isolated clear/readback boundary, GPU-67 compiled a GLES2
vertex shader and fragment shader, linked them, and submitted exactly one
full-screen triangle through the same patched Mesa 25.0.7 Zink, system Vulkan
loader, isolated Turnip, KGSL and Adreno 650 path. The draw rasterized into a
4x4 RGBA8 pbuffer and all 16 read-back pixels matched the shader-selected
green value `0,255,0,255`; the process returned zero.

This validates one bounded shader execution, triangle rasterization,
framebuffer-write and readback path only. It does not validate general GLES2
or GLES3 correctness, textures, uniforms, VBOs/VAOs, FBOs, large targets,
performance, sustained rendering, Wayland or Phoc acceleration, dma-buf
interoperability, GBM, KMS/DSI presentation, desktop OpenGL or production
readiness. System Mesa remained unchanged, Phoc and Phosh stayed running,
`DSI-1` stayed connected, and no relevant GPU or kernel fault occurred. See
`docs/validation/mobian-m1-gpu67-shader-draw-hardware-validation-2026-09-10.md`.

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
`docs/validation/mobian-m1-a650-turnip-kgsl-dmabuf-hardware-validation-2026-09-08.md`.

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
`docs/validation/mobian-m1-gsd-power-spontaneous-wakeup-validation-2026-09-06.md`.

## M1 WIFI — VALIDATED ON HARDWARE

Manual bring-up on `lmi` with D-v43 completed the QCA6390 CNSS/WLFW sequence,
created `wlp1s0`, scanned nearby BSS entries, associated with WPA2, obtained a
DHCP lease and default route, and preserved the independent `usb0` SSH path.
The kernel dynamically selected `bd_j11gl.elf`; it must not be overridden with
the older historical `bd_j11.elf` default.

The systemd implementation under `userspace/wifi/files/systemd` and
`userspace/wifi/scripts`, together with the integrated Debian `wpasupplicant`,
is now validated on hardware in M1 REPRO v3. The image
completed firmware bring-up, `FW_READY`, qcacld probe, WLAN creation,
automatic SSID listing, CLI WPA2 association, DHCP, DNS, and Internet access
while preserving USB SSH. No Wi-Fi profile or credential is tracked. See
`docs/validation/mobian-m1-wifi-hardware-validation-2026-09-03.md`.

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
`docs/validation/mobian-m1-repro-v2-hardware-validation-2026-09-04.md`.

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
`docs/validation/mobian-m1-phosh-logind-polkit-validation-2026-09-04.md`.

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
`docs/validation/mobian-m1-repro-v4-hardware-validation-2026-09-04.md`.

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
`docs/validation/mobian-m1-repro-v5-hardware-validation-2026-09-05.md`.

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
`docs/validation/mobian-m1-repro-v6-hardware-validation-2026-09-05.md`.

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
`docs/validation/mobian-m1-repro-v7-hardware-validation-2026-09-05.md`.

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
`docs/validation/mobian-m1-repro-v9-hardware-validation-2026-09-05.md`.

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
`docs/validation/mobian-m1-bluetooth-slim-pdr-runtime-validation-2026-09-05.md`.
See also `docs/validation/mobian-m1-repro-v11-hardware-validation-2026-09-05.md` for the
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
Bluetooth address `[REDACTED-DEVICE-MAC]` has now been traced through the stock Android
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

See `docs/validation/mobian-m1-qca6390-hastings-hci-design-2026-09-05.md` and
`docs/validation/mobian-m1-qca6390-v2-boot-safety-validation-2026-09-06.md`. The
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
closed. See `docs/validation/mobian-m1-sdx55-dv121-sahara-milestone-2026-09-06.md` and
`docs/validation/mobian-m1-sdx55-esoc-b1-validation-2026-09-06.md`.

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
`docs/validation/mobian-m1-sdx55-dv207-remotefs-reset-offline-validation-2026-09-07.md`.

## Repository policy

Generated `.img`, `.ext4`, Android sparse images, root filesystems, private
keys, caches and other build artifacts are intentionally excluded from Git.

## Battery, speaker and torch updates — 2026-10-03

The full Debian ARM64 UPower `1.90.9-1+lmi1` package and phone-local activation
are installed. Seven explicit ARM64 integration tests passed; the installed
service tracked a real unplug/replug cycle correctly over 90 observations.
Capacity accuracy and autonomy remain unresolved. Automatic battery suspend
is locally enabled; frequent msoc-delta wakes remain under investigation.

Clear speaker music was operator-confirmed through an installed PipeWire
route using the S32_LE frontend and S24_LE backend on the temporary GPIO
diagnostic boot. ALSA controls restore on close. The graphical torch app's
Allumer and Éteindre buttons were operator-confirmed. Camera capture remains
blocked. These are live-phone customizations, not newly locked golden images.
See the [validation record](../validation/lmi-battery-audio-torch-2026-10-03.md).

## Additional operator confirmations — 2026-10-03

MP3/MP4 playback, hardware volume buttons and Chinese filenames in Files
are confirmed. Noto CJK fonts were installed and Files relaunched. A controlled
RTC deep-suspend test succeeded, but the gauge-derived current remained about
102 mA versus 218 mA awake idle; acceptable long-term autonomy is still not
established. See the latest battery/audio/torch validation record.

## Next-build language support — 2026-10-03

The next M1 recipe includes broad Noto core/CJK/emoji font coverage and all
Debian locales by default. Initial interface locale and XKB layout are build
parameters; document scripts do not depend on the selected interface language.
This is prepared recipe work, not a new image or phone deployment. Input
methods and runtime language switching remain separate validation work.

## CPU idle improvement — installed 2026-10-03

A legacy `lpm_levels.sleep_disabled=1` boot parameter blocks deeper CPU idle
between activities. A controlled test reported awake-idle current dropping
from 208.4 to 100.8 mA with 831 C1 entries after a runtime opt-in. Touch,
music, volume and USB remained functional. The phone-local opt-in service is
installed and enabled; stopping it restores the original parameter. Boot
images/cmdline and the historical golden are unchanged. Reboot and long-run
validation remain pending. Deep-suspend current still reports about 97 mA;
acceptable autonomy and fuel-gauge accuracy are not yet established. See
`userspace/power/README.md` and the 2026-10-03 validation record.

A subsequent private tracefs collection recorded 121.761 seconds of deep
suspend without new failures, with APSS/ADSP asleep almost throughout
and approximately 96.2 mA reported consumption. Static DDR counters
do not identify a memory-power fault; the residual consumer remains
unresolved. The trace instance was removed after reconnect. A subsequent
unplugged inspection confirmed USB runtime suspend and its power domains
disabled; an always-on boost/shared GPIO is a review lead, not a proven cause.


## Application checklist and Chatty incident — 2026-10-03

An inventory of 21 visible applications and one-at-a-time functional checks
is recorded in `docs/validation/lmi-app-checklist-2026-10-03.md`. Chatty
0.8.7-2 exhausted memory during camera enumeration through GStreamer and
libpurple. An isolated test excluding two video plugins stayed active at
approximately 108 MiB. The phone-local desktop/D-Bus helper was then installed
with an isolated registry and a requested 384 MiB systemd-user memory limit;
user memory delegation was checked after restart at 384 MiB and zero swap.
The operator subsequently confirmed normal opening, menu access and relaunch;
shortcut-window sizing remains defective. SMS/MMS remain unvalidated. SMS is not validated and no modem was detected. The new helper
is not automatically installed by the generic image recipe.

The restart interrupted the six-hour battery observer. CPU-idle and UPower
were active after restart, but no ALSA card was detected; previous music
confirmations apply to the temporary diagnostic boot, not this restart.


## Application follow-up — 2026-10-03

The operator's application and menu defects are preserved in the app checklist.
Koko's missing Qt/QML dependencies were installed on the test phone and made
explicit in the application recipe. Photos now has operator-confirmed image
opening, working Back navigation and no unsolicited keyboard. A bounded
standard-thumbnail-cache helper restores the gallery preview in a remote
screenshot; the lmi launcher uses the tested Zink runtime when available.
The bottom folder header, truncated labels and broader gallery functions remain
open. Helpers and dependencies are recorded in the recipe.
This is a live userspace repair, not a newly built or hardware-validated image.
No automatic rotation sensor or usable GPS was established in this follow-up.
See the [application checklist](../validation/lmi-app-checklist-2026-10-03.md).


The text editor's off-screen GTK Save dialog was reproduced. GNOME file-chooser
portal routing and a per-app launcher now give an accessible Save button.
Remote tests passed create/save, reopen, Save As, edit/save and normal close;
the operator also confirmed the Save As dialog usable by touch. Recipe and
builder staging include these userspace fixes; no new image was built.


## Calendar and Contacts functional follow-up — 2026-10-03

Calendar passed month navigation, Today, explicitly authorized local test-event
creation, reopening, removal and a normal close with retained exit status 0.
No test event remains; remote synchronization and reminders are unvalidated.
Contacts passed local dummy-contact creation, persistence and search, but
initial deletion crashed with SIGSEGV. An app-only Cairo launcher then passed
two deletion/normal-close cycles. This workaround is installed locally and
included in the next-build application recipe/staging; no new image was built.
No personal contacts were modified. Broader contact operations remain untested.
Console’s incomplete pidfd/waitid kernel interface remains open, with no
persistent syscall filter or global library replacement installed.
See the [application checklist](../validation/lmi-app-checklist-2026-10-03.md).


## Settings functional follow-up — 2026-10-03

Settings passed navigation to its overview, Mouse and Touchpad, Keyboard and
System pages, plus two normal closes with retained exit status 0. No system
settings were changed. Reopening still restores the last panel even after
closing from the overview; overview-on-launch remains unresolved. The mouse
test dialog has no visible close button on this display; Escape closes it,
but touch-only dismissal remains unvalidated. No renderer workaround or
launcher modification was installed. Temporary test services and USB-only
screen inhibition were stopped. See the
[application checklist](../validation/lmi-app-checklist-2026-10-03.md).


## Window close controls and mail/call UI — 2026-10-03

The live window button layout omitted Close (`appmenu:`). It is now
`appmenu:close`; Calls' VoIP dialog and the Calls/Settings main windows passed
touch-simulated close checks. A Phosh schema default and builder validation
are prepared for the next image, without running a build. Custom-header
dialogs can still omit Close; Settings' mouse-test dialog remains open work.
Geary passed empty-account startup, add-form cancellation, reopening and
normal closure; no mail account or message was created. Calls has no usable
modem/VoIP account in its UI; no actual call was attempted. See the
[application checklist](../validation/lmi-app-checklist-2026-10-03.md).


## Editor shortcut dialog recheck — 2026-10-04

The restored Close layout persists in the live session, but Text Editor's
shortcut dialog is still wider than the display and lacks a touch-accessible
dialog close control. Hiding the keyboard does not fix its width. App-local
Phoc scale-to-fit did not visibly help and was returned to false; global
scaling and embedded resources were not changed. Escape exits the dialog,
then the main window's Close button gives retained exit status 0. No test
document was changed. Other apps' shortcut dialogs remain unverified after
the layout change. See the
[application checklist](../validation/lmi-app-checklist-2026-10-03.md).


## Chatty shortcut-dialog adjustment — 2026-10-04

Phoc's oversized-window adjustment is now enabled in the live session and
prepared as a next-build schema default. Chatty's shortcut dialog fits and
passed touch-simulated close/reopen checks with the restored Close layout.
No message/account was created. Text Editor's shortcut dialog shrinks but
still clips horizontally; its touch-only exit remains unvalidated. Both
test applications closed normally and test units were stopped. Transient
black line artifacts after the preference toggle were absent on the next
Chatty capture, without establishing GPU stability. See the
[application checklist](../validation/lmi-app-checklist-2026-10-03.md).

## Root SSH build policy (2026-10-04)

The Phosh image recipe no longer embeds the workstation diagnostic public key.
It clears inherited root authorizations in the derived image by default; an
external public key can be explicitly selected with `M1_SSH_PUBLIC_KEY_FILE`.
Private keys and multi-key inputs are rejected. Existing phone access and input
rootfs trees are unchanged. Isolated tests cover defaults, explicit access and
invalid inputs; no complete image build or deployment was performed.

## Recorder and missing-card audio startup — 2026-10-04

KRecorder 25.04.0-2 opened, navigated to Configuration and returned to its
recording list. The Audio Input chooser was empty. Two simulated-touch
main-window closes, including a reopening after the service correction,
returned Result=success, ExecMainCode=1, ExecMainStatus=0. No recording was
started, no existing recording was changed and temporary test units stopped.
Configuration labels were French in the captures; full translation untested.
The on-screen keyboard appeared in Configuration without a text-entry action;
that usability defect remains open. Codec, container and recording operations
have not been validated.

This runtime had no ALSA card: /proc/asound/cards reported no soundcards and
/dev/snd contained only timer. The installed speaker adapter failed to open
lmi_speaker; PipeWire terminated with exit status 234 and WirePlumber stopped.
This does not overturn earlier clear-speaker validation on the separate
temporary diagnostic boot, nor identify the currently loaded boot image by
hash. The displayed kernel release alone cannot distinguish those images.

The adapter now declares flags = [ nofail ], as specified by the
[PipeWire configuration documentation](https://docs.pipewire.org/page_man_pipewire_conf_5.html).
After installation of this single configuration change and an audio-service
restart, PipeWire 1.4.2, pipewire-pulse and WirePlumber stayed active through
the recorder reopening/close test. wpctl showed only Dummy Output and no
audio source. The correction restores server availability when the card is
absent; it does not restore physical speaker or microphone operation. The
missing-card warning remains expected. Physical-card playback with the new
flag awaits the diagnostic boot retest. No kernel/image build or flash ran.

## Diagnostic-boot speaker retest — 2026-10-04

After a temporary Fastboot load of the preserved diagnostic boot, the ALSA
card returned and the revised nonfatal speaker adapter loaded. The operator
confirmed ten seconds of clear music without distortion. Standard ALSA
capture produced eight seconds of data with all tested controls restored;
recognizable microphone sound and application integration remain unvalidated.
No kernel was installed durably and no microphone source was installed.
See the [application checklist](../validation/lmi-app-checklist-2026-10-03.md).

## Microphone and Recorder result — 2026-10-04

Native eight-second capture was operator-recognized after amplified playback.
An opt-in PipeWire microphone source and numeric KRecorder WAV/PCM settings
then produced two complete 8.96-second recordings. The final saved trial
survived normal close/relaunch and displayed `0:08`. After replaying it,
the operator confirmed that the application-produced recording was good. Both hardware PCMs
closed at idle. This supersedes earlier no-source/microphone-unvalidated
observations on this diagnostic boot only. Full UCM2, headset/earpiece and
durable boot deployment remain pending. See the
[audio integration record](../../userspace/audio/README.md#microphone-and-recorder-capture--2026-10-04).

## Timer feedback and offline clock correction — 2026-10-04

A real five-second Clocks timer now gives an operator-confirmed audible alert
after adding Feedback and the PulseAudio backend to the app recipe and phone.
The timer test was removed; no rebuilt image is claimed. The phone clock was
aligned from Windows and saved using the existing seed service, because NTP
had no Internet route. Wi-Fi and battery settings were unchanged. See the
[validation and remaining limits](../validation/lmi-clock-feedback-2026-10-04.md).

## Files and Calculator functional checks — 2026-10-04

Simulated touch validated Files Copy/Rename/Trash on disposable fixtures and
Calculator arithmetic, angle conversion and Preferences closure. Both apps
closed normally; file/trash fixtures were removed after exact scoped checks.
Files keyboard dismissal and Calculator's clipped Shortcuts dialog remain
unresolved. Resetting Settings' last-panel preference did not provide the
requested overview; the original value was restored and no fix installed.
See the [checklist](../validation/lmi-app-checklist-2026-10-03.md#files-operations-calculator-menus-and-settings-trial--2026-10-04).

## Papers search — 2026-10-04

Positive/negative PDF text search and touch navigation to the second result
passed on the synthetic fixture, with keyboard dismissal and normal exit.
A Pixman invalid-rectangle warning remains recorded; no crash was observed.
See the [checklist](../validation/lmi-app-checklist-2026-10-03.md#papers-search--2026-10-04).

Papers Save As also created an identical test PDF through the mobile chooser;
the Save control remained visible above OSK. Keyboard dismissal and normal
closure passed, and only the disposable copy was removed after comparison.

## Keyboard home-bar gesture — 2026-10-04

A two-second simulated hold centered on the bottom white bar toggled OSK in
Text Editor and Files, with DBus visibility checks. No preference or launcher
was changed. The Files rename replay hid OSK automatically in this attempt,
so the earlier persistent-keyboard symptom was not reproduced. Operator
gesture confirmation and other dialogs remain pending. See the
[checklist](../validation/lmi-app-checklist-2026-10-03.md#keyboard-home-bar-gesture--2026-10-04).

## Files touch multiselection — 2026-10-04

The deletion report was clarified as difficulty selecting multiple files.
Terminal OSK's latched Ctrl plus touches selected three folders; Ctrl was then released and the grouped selection reduced to one item. No data was deleted and grouped Trash remains
untested. The keyboard-assisted workaround is recorded in the
[checklist](../validation/lmi-app-checklist-2026-10-03.md#files-touch-multiselection--2026-10-04).

## Portfolio mobile selection — 2026-10-04

The official Debian `portfolio-filemanager` package is installed on the test
phone and added alongside Nautilus to the next app recipe. Long press followed
by taps selects multiple disposable files without OSK. Grouped permanent
removal preserved the unselected third fixture; Trash and operator usability
confirmation are not inferred from that result. The confirmation's poor icon
and truncated label remain recorded. No new image or default-handler change.
See the [checklist](../validation/lmi-app-checklist-2026-10-03.md#portfolio-native-touch-multiselection--2026-10-04).

The operator subsequently rejected Portfolio as providing no useful
improvement. Its next-build package addition was withdrawn; the trial remains
historical evidence, not a completed fix. Existing Files touch selection is
still open. After clarification that a second app was unnecessary, Portfolio
was also uninstalled without autoremove; no user files were removed.

## Core app priority and camera blocker — 2026-10-04

The operator confirmed Files as functional. Additional features are last,
after basic operation, essential menus and translation; no second file manager
is required. Megapixels remains nonfunctional: a bounded launch exited with
status 1 due to the absent lmi-compatible configuration. Targeted source
review supports the downstream/private-interface blocker, without establishing
a usable capture backend. No camera configuration or image was changed.
See the [functional recheck](../validation/lmi-app-checklist-2026-10-03.md#functional-priority-and-camera-recheck--2026-10-04).

The camera follow-up found OEM HAL objects and a usable Android loader already
present, but missing Binder nodes/properties and a broken HIDL-manager target.
A read-only probe is now preserved; no Android service or capture was started.
The alternate CAMSS/OV13B10 source is distinct from the running kernel and is
not a validated camera. See the [backend prerequisites](../../userspace/camera/README.md#oem-backend-feasibility--2026-10-04).

The isolated HIDL follow-up located the manager in system_ext and obtained
private Binder registration with a test-only synthetic context. No camera
device/provider was exposed. High CPU and missing properties remain blockers;
all runtime processes, mounts and loop mappings were removed. Details and
source-only diagnostics are in the [camera milestone](../../userspace/camera/README.md#isolated-hidl-registration-milestone--2026-10-04).


Camera follow-up (2026-10-04): the private HIDL startup spin was traced to
waiting for an unavailable Android readiness property. A local diagnostic
token removed the spin. Real client IPC still fails: this non-SELinux kernel
cannot supply the requested transaction security context, and omitting the
request triggers Android 16's missing-caller-context assertion. All test
processes/mounts were removed; no camera provider or physical capture was
started. Megapixels remains nonfunctional. See the [measured results and
remaining runtime prerequisite](../../userspace/camera/README.md#readiness-spin-resolved-client-ipc-blocked--2026-10-04).


Camera OEM follow-up (2026-10-04): the private runtime can now query HIDL
interfaces and load CamX with the real qcom/kona properties. Correcting the
private ICP firmware lookup produced a kernel-confirmed firmware download;
several real candidate EEPROM probes succeeded. The direct camera module
now returns eight OEM IDs when the unavailable NCS/IMU service is disabled privately. These are backend
milestones, not a working photo application. See the [sensor progress and
capture gates](../../userspace/camera/README.md#oem-module-and-sensor-probe-progress--2026-10-04).
