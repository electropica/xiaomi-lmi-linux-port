# Current validated build and userspace state

This document distinguishes the validated Mobian userdata family from the
separate D-v43/OpenRC reconstruction and from temporary diagnostic boots.
Generated images are not stored in Git.

## Current hardware state

The `archi-validation-02` Debian 13/Mobian userdata was booted on Xiaomi
`lmi` with the D-repro D-v43 boot. Phosh was visible and usable; touch/unlock,
DSI-1, and GLES2 → Zink → Vulkan Turnip → KGSL → Adreno 650 were validated.
GNOME Console and Calculator were exercised. The original D-repro boot
(`D-repro-01-kernel-Dv43-qca6390-v2-complete-fcsource-boot.img`, SHA-256
`0b6c7d88b3068ae4e3d106fd4b15a1a79bf00c3e576be7b3fcd8ab62faed73ad`) is
the durable boot identity for the golden and `daily-base` validations. The
boot image embedded in userdata is a distinct artifact.

## Golden userdata: `archi-validation-02`

The external raw and Android-sparse images were verified as a matching pair:

| Form | Size | SHA-256 |
| --- | ---: | --- |
| Raw `archi-validation-02.img` | 4,551,868,416 bytes | `329e2124f97032a2f4b15167bbd9bbbd9395bb422f2794a2117ee610a2368f27` |
| Sparse `archi-validation-02.img.android-sparse.img` | 2,960,036,280 bytes | `84182b57edb7be8e49c29e0f0b472e9b6a54f7efa645ef99664dc0e004759f78` |

The sparse image was flashed as userdata and booted with the D-repro boot.
The text lock records its packages, persistent customizations, GPU72 runtime
and boot/userspace contract at
[`build/locks/userspace/`](../../build/locks/userspace/README.md).
The golden is not in Git. A bit-for-bit rebuild from all historical sources
is not demonstrated.

## Derived profile: `daily-base`

`daily-base` was derived from the golden userdata without rebuilding the
kernel. It adds the validated time-seed floor and a per-user XDG override
that disables only automatic Chatty-daemon startup; Chatty remains installed
and manually launchable.

| Form | Size | SHA-256 |
| --- | ---: | --- |
| Raw `archi-validation-02-derived-daily-base-20260927.img` | 4,551,868,416 bytes | `5cc226cd96c324b68d74e33eec461a091e7f5dd69b80e0529c2d0267cfa3cad5` |
| Sparse `archi-validation-02-derived-daily-base-20260927.img.android-sparse.img` | 2,960,466,444 bytes | `172a4f950252e810f408bf4d5caf5075c699020e6a2198999f7f0b30c7f19928` |

The raw/sparse round trip and hardware boot were validated. The images remain
external. See
[`daily-base` validation](../validation/archi-validation-02-daily-base-validation-2026-09-27.md).

## Experimental profile: `daily-base-audio-fw-test`

This separate experimental derivative adds the proprietary TFA9874 container
to the kernel's active firmware lookup path. It was tested with a distinct
reset-GPIO diagnostic boot loaded temporarily using `fastboot boot`; that
boot was not installed durably. The firmware binary, userdata and diagnostic
boot remain external and must never be added to Git.

The WCD938x/TFA9874 path now supports clear speaker music through direct
S32_LE ALSA and an installed opt-in PipeWire route (2026-10-03). A complete
UCM2 profile and microphone/headset validation remain pending; see
[`archi-validation-02` audio progress](../validation/archi-validation-02-audio-progress-2026-09-29.md).

## Earlier build: `archi-validation-01` (superseded as current pointer)

The prior Android-sparse build remains a historical artifact identity, not
the current golden:

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| Work ext4 | 4,294,967,296 bytes | `60de98660991379cb1d463ebadc7de43b73242d68f73502308e3891d2350844d` |
| Raw userdata | 4,551,868,416 bytes | `559d6c44f2aa2223f91fd8af1db7a838b8183d7a223ceb80f7bdd13a9b6e31e4` |
| Android sparse userdata | 2,834,813,356 bytes | `f61c19a09881c9a7ac165cc5e36ab08f146d65acddae2de18a6bb555c10663b3` |

Its two `e2fsck` validation passes completed cleanly. It is superseded as the
current userspace reference by `archi-validation-02` and its validated
`daily-base` derivative.

## Build entry points

Repository orchestrator:

    build/build-mobian-image.sh

Current Phosh/userspace builder:

    userspace/phosh/scripts/build-m1-phosh.sh

Optional application installer:

    userspace/apps/scripts/install.sh

The optional application layer is enabled with:

    INSTALL_OPTIONAL_APPS=1

## Current optional application set

The current selected optional application packages are:

- epiphany-browser
- gnome-console
- gnome-calculator
- gnome-text-editor
- papers
- showtime
- gnome-clocks
- gnome-weather
- gnome-contacts
- gnome-calls
- chatty
- megapixels
- gnome-calendar
- gnome-maps
- geary
- amberol
- krecorder
- koko

## GPU source state

The active GPU72 runtime is stored under:

    userspace/gpu/files/gpu72/

Its canonical source provenance is documented in:

    userspace/gpu/files/gpu72/SOURCE-PROVENANCE.md

The validated source reconstruction is upstream Mesa 25.0.7 plus the canonical
GPU72 patch.

## Important separation of concerns

The current M0/base-rootfs chain, current Phosh/userspace chain and kernel
build are separate.

The separate Mobian device workflow is not a replacement for the current
`userspace/phosh/scripts/build-m1-phosh.sh` image-production chain.

## Known deferred work

The following remain separate deferred items:

- full UCM2 routing, microphone/headset and durable audio-boot deployment
- camera configuration and a usable downstream capture pipeline

The historical M0 Weston display validation and the later D-v43/OpenRC Weston
failures are different environments and must not be conflated.

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

## Next-build multilingual baseline — prepared 2026-10-03

The M1 recipe now includes core/CJK/emoji Noto fonts and all Debian locales
without requiring optional apps. Initial interface locale and XKB layout are
build parameters. Korean-interface/Turkish-document rendering is an intended
validation scenario, not yet an image/hardware result. No new image was built
and the battery-test phone was not changed. See the Phosh recipe README for
remaining input-method, runtime language selection and translation limits.

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
