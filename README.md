# Xiaomi lmi Linux port

This repository unifies the kernel-side reconstruction records and the
Mobian/Phosh userspace work for the Xiaomi Redmi K30 Pro / POCO F2 Pro
(`lmi`, Qualcomm SM8250). It preserves historical D-v43/OpenRC and Weston
experiments separately from the current Debian/Mobian userspace line.

## Current validated state

The external `archi-validation-02` Debian 13/Mobian userdata booted with the
D-repro D-v43 boot. Phosh, touch/unlock, DSI-1, and GLES2 → Zink → Turnip →
KGSL/Adreno 650 were observed working. Its `daily-base` derivative was also
hardware-validated, including the time-seed clock floor and responsive
lock/unlock with only Chatty daemon autostart disabled. The golden,
`daily-base`, and experimental audio-profile images are external artifacts;
none is stored in Git.
GNOME Console and Calculator were also exercised on the golden userspace.

The distinct `daily-base-audio-fw-test` profile loads a proprietary TFA9874
container kept outside the repository. WCD938x/TFA9874 bind, ALSA registers,
and clear speaker music was confirmed through both direct S32_LE ALSA and
an installed opt-in PipeWire route on the temporary reset-GPIO diagnostic
boot. Microphone/headset routing, UCM2 and durable boot deployment remain
unvalidated. See the [installed battery, speaker and torch validation](docs/validation/lmi-battery-audio-torch-2026-10-03.md).

The D-v43/OpenRC reconstruction separately validated USB networking, SSH,
Wi-Fi scanning, and direct DRM/KMS test rectangles on DSI-1. Weston on that
system remained black. This is not the successful Weston 14 display result
from the separate historical M0 Mobian environment. The kernel and userdata
are not claimed to be bit-for-bit reproducible from all sources.
The dated [D-v43 reconstruction](docs/validation/d-v43-openrc-reconstruction-2026-09-23.md),
[DRM/KMS validation](docs/validation/d-v43-drm-kms-validation-2026-09-25.md),
and [Weston boundary record](docs/validation/d-v43-weston14-boundary-2026-09-26.md)
keep those milestones and their evidence limits explicit.

See [current build identities](docs/status/CURRENT-BUILD.md),
[Mobian status](docs/status/MOBIAN-STATUS.md), and the dated
[hardware validation records](docs/validation/).

## Repository layout

- `kernel/` — tracked kernel config, patches, and kernel-side diagnostics or tools
- `userspace/` — Phosh, GPU, display, audio, camera, Wi-Fi, Bluetooth, base, and app integration
- `build/kernel/` — kernel build status and future entry points
- `build/userdata/` — portable derived-userdata builder and profiles
- `build/locks/userspace/` — the text-only archi-validation-02 userspace lock
- `docs/` — current status, architecture, provenance, and dated validation
- `historical/` — superseded D-v43/OpenRC, Weston, and earlier porting work
- `tools/` — generic project utilities

The canonical structure and active entry points are described in
[the architecture guide](docs/architecture/ARCHITECTURE.md).

## Build entry points

The Mobian image orchestrator is `build/build-mobian-image.sh`; its Phosh
builder is `userspace/phosh/scripts/build-m1-phosh.sh`. Optional apps are
installed by `userspace/apps/scripts/install.sh`. The M0/base-rootfs scripts
are under `userspace/base/scripts/`.

The separate `build/userdata/build-derived-userdata.sh` derives userdata from
the locked external golden and package cache without rebuilding the kernel.
Its four profiles and required external inputs are documented in
[`build/userdata/README.md`](build/userdata/README.md). Heavy image and kernel
builds are run manually by the operator; this repository does not contain the
generated images or private build state.

The active Mobian builder requires `M1_MOBIAN_PASSWORD` to be supplied via
the environment; credentials must never be stored in the repository or shell
logs.

## Reproducibility and exclusions

The text lock records exact package and persistent-file identities, external
artifact hashes, and the boot/userspace compatibility boundary. Exact cloning
from the validated sparse userdata is possible; functional derivation is
specified by the builder. Rebuilding the full userspace bit-for-bit from
source is not demonstrated. The boot/kernel is a separate layer and is not
rebuilt by the userdata derivation workflow.

Do not add raw/sparse/boot images, root filesystems, `.deb`/APK payloads,
package caches, proprietary firmware (including the TFA container), private
inputs, build states, generated outputs, full device logs, credentials, PINs,
machine IDs, or real device MAC addresses to Git. See `NOTICE` and `LICENSE`
for licensing information.

## Battery state correction

The [UPower status opt-in](userspace/power/README.md) passed selected host
tests and private hardware checks. The full Debian ARM64 package is now
installed with a phone-local opt-in, and the installed service passed a real
unplug/replug cycle. Profile recognition, capacity accuracy and autonomy
remain unresolved. The graphical torch buttons are also hardware-confirmed;
see the [installed battery, speaker and torch validation](docs/validation/lmi-battery-audio-torch-2026-10-03.md).

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
unresolved. The trace instance was removed after reconnect.
