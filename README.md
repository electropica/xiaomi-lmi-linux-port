# Xiaomi lmi Linux port

Mobian/Phosh and kernel reconstruction work for the Xiaomi Redmi K30 Pro /
POCO F2 Pro (`lmi`, Snapdragon 865 / Qualcomm SM8250, Adreno 650).
The active integration branch is `developpement`.

## Current state — October 27, 2026

Mobian is usable on the test handset, with working touch/unlock, GPU rendering,
USB networking/SSH, Wi-Fi and a customized Phosh home screen. This remains an
experimental port: battery autonomy, telephony and other hardware functions
are not all qualified. Historical D-v43/OpenRC and Weston results are retained
separately and must not be read as the current Mobian runtime.

| Area | Validated result | Remaining boundary |
| --- | --- | --- |
| Permanent dualboot | Installed menu, Mobian default after 15 seconds, direct Mobian/LineageOS entries and Fastboot/Recovery trials; installed boot-prefix readback verified | Build/flash only through the pinned, device-specific operator workflow |
| Display and input | Phosh, touch, unlock, power button and GLES2 through Zink/Turnip on KGSL/Adreno 650 | This is the qualified downstream kernel stack, not a mainline hardware-support claim |
| Home and drawer | Favorites at the bottom, up to five; home shortcuts; drag/reorder/move without duplicates; scrolling before downward close; previews hidden on closed home | Search clearing on completed close is operator-confirmed for matching and empty queries |
| Application previews | Private-target Phoc thumbnails accepted clear and correctly oriented; application activation and favorite dragging remain responsive | Exact underlying Mesa/driver corruption mechanism is not established |
| Power menu | Shutdown/restart menu usable while locked, with cancellable restart confirmation | No claim that every power-management issue is solved |
| Automatic suspend | IRQ-name handling sustains approximately 15-second return gaps after 35 natural gauge wakes in the latest night | Remaining battery consumption and physical gauge calibration are unresolved |
| Connectivity | USB networking/SSH and Wi-Fi exercised | GPS, automatic rotation, modem/SMS/MMS are not established as working by these validations |
| Audio, torch and camera | Speaker playback and torch have dated device validations; camera integration has its own build/bundle workflow | Do not infer full microphone/headset/UCM2 or camera-mode qualification from package inclusion |
| Linux 7.2.12 session | Phosh desktop and working drawer on a read-only Mobian rootfs, pixman software rendering, RAM home | Diagnostic RAM session bounded to 90 seconds; no GPU acceleration, no autonomous boot, no suspend or battery qualification, permanent default unchanged |

### Linux 7 community track

A separate upstream line is being brought up in parallel on the `lmi-linux7`
branch, while the qualified downstream 4.19 Mobian system above stays
recoverable on `developpement`. Two RAM-only community boots have now produced
real display and USB journal output on the handset: Linux 7.1.0-lmi-ccc-ram1
and the 7.2.12-lmi-community-port1 port of that tree. Both reach DSI, DRM MSM
and a framebuffer console, with the USB observer transport working and UFS
probing successfully.

On top of those, the combined display and touch candidate passes on the
handset: 46 tracking-ID starts and 46 releases over 3131 event records, with no
active slot left at the end, BTN_TOUCH=0 and no SYN_DROPPED. The latest trial
goes further and runs the real Mobian userspace: the Phosh desktop appeared and
the drawer worked, with pixman software rendering on a read-only rootfs and a
temporary home in RAM.

These are diagnostic RAM boots, not a usable system. Rendering is software only,
the session is bounded to 90 seconds and cannot retain settings, the GPU and
radio firmware are absent, and no autonomous boot, suspend or battery result
follows. The permanent Mobian/Lineage installation was not flashed and its 4.19
default is unchanged, even though Linux 7 is requested as the future default.
See the [Linux 7 status](kernel/experimental/linux7/README.md) and the
[hardware records](docs/validation/).

### Battery: improvement and unresolved work

The latest preserved night spans 9h48m42s between USB markers, with 95.824%
inferred suspension and displayed battery 100 -> 82 percent. The historical
approximately 1201-second awake delay did not recur in the 35 observed natural
gauge return gaps. This validates sustained return-to-suspend behavior.

It does **not** establish a calibrated standby current. Raw counter progression
is nearly unchanged early/late, while software/SOC-model counters slow by about
33%. Those channels use different state and cannot be treated as independent
electrical meters. No physical residual consumer or battery-life solution is
claimed. Older mA figures in dated notes are conditional gauge estimates.

Read the [current battery checkpoint](docs/status/BATTERY-RESEARCH-CURRENT.md)
and [overnight result and limits](docs/validation/lmi-quiet-wake-night-2026-10-26.md).

### Installed system versus next build

The accepted installed shell now includes Phosh `irqnames1+drawerpreview1` plus
`drawersearch1+draweremptysearch1+searchclose1`, with GSD
IRQ-name handling and the accepted private-target Phoc renderer. The complete
image recipe still pins the earlier preview1 shell; incremental search acceptance
does not silently promote new packages into that qualified image.

The intended `j11sun_4700mah` profile is published on the current temporary
October 7 kernel through the reviewed DT-order diagnostic. That does not make
the diagnostic a newly qualified permanent kernel or resolve gauge accuracy.

Clearing every search after a completed downward drawer close is now installed
in [the search-close candidate](userspace/phosh/drawer-search-close-candidate/README.md).
It supersedes the earlier empty-result-only requirement. Both matching and
zero-result closure cases pass operator testing; 36 package tests pass.
Cancelled gestures are host-checked, not separately operator-confirmed.

## Build and installation entry points

- [Current build identities and boundaries](docs/status/CURRENT-BUILD.md).
- Complete Mobian image: `build/build-complete-lmi.sh`; follow the
  [complete profile instructions](build/profiles/lmi-current/COMPLETE-BUILD.md).
- Base Mobian orchestration: `build/build-mobian-image.sh`; Phosh builder:
  `userspace/phosh/scripts/build-m1-phosh.sh`.
- Permanent boot menu: [recipe](build/boot-menu/external-mobian/README.md) and
  [guarded operator workflow](build/boot-menu/permanent/README.md).
- Derived userdata without rebuilding the kernel:
  [build/userdata/README.md](build/userdata/README.md).
- Optional applications: `userspace/apps/scripts/install.sh`.

Heavy kernel, package and image builds are run manually by the operator.
Generated images, installable packages and required private/vendor inputs are
external artifacts. An incremental package acceptance is not automatically a
fresh complete-image validation. Follow the pinned recipe and rescue rules;
historical commands are not the current installation procedure.

## Repository map

- `kernel/`: configurations, patches and diagnostics.
- `userspace/`: Phosh, power, graphics, audio, camera, radios and applications.
- `build/`: image/menu/userdata recipes, profiles and text-only input locks.
- `docs/`: status, architecture, provenance and dated validation records.
- `historical/`: superseded OpenRC, Weston and earlier porting work.
- `tools/`: generic project utilities.

Start with the [architecture guide](docs/architecture/ARCHITECTURE.md),
[Mobian status](docs/status/MOBIAN-STATUS.md) and
[hardware validation records](docs/validation/).

## Reproducibility and exclusions

Recipes, exact identities and text locks are tracked. Complete bit-for-bit
source reconstruction of all kernel/userspace/vendor components is not
demonstrated. Kernel/boot, rootfs, menu and incremental packages are distinct
layers with separate validation boundaries.

Keep generated images/rootfs trees, package caches, proprietary firmware,
credentials, device identifiers and full private logs outside Git. Supply build
credentials externally; never commit them or expose them in shell logs. Keep
one qualified build and compatible rescue according to the
[artifact retention policy](docs/maintenance/ARTIFACT-RETENTION.md).
See `NOTICE` and `LICENSE` for licensing information.
