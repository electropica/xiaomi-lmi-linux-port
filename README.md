# Xiaomi lmi Linux port

Mobian/Phosh and Linux kernel development for the Xiaomi Redmi K30 Pro / POCO
F2 Pro (`lmi`, Qualcomm SM8250, Adreno 650).

**Branches:** `main` and `developpement` contain the Linux 7 port. The historical
downstream Linux 4.19 work is retained on `archive/linux-4.19`.

## Current status — 1 November 2026

Mobian 7.2.12 starts from the permanent boot menu on the test handset. The
menu also retains Mobian 4.19 and LineageOS rescue entries. The same Mobian
installation carries the user's settings and customized Phosh interface.
Hardware support is incomplete: this is a development system, not a claim
that every phone function is ready for daily use.

| Area | Latest reported result | Remaining work |
| --- | --- | --- |
| Display and touch | Phosh desktop, touch, unlock, application drawer and GPU rendering have been exercised. The image configuration specifies 300% scale. | Further hardware and power-management qualification. |
| Home and drawer | Scrolling, search clearing, thumbnail visibility and gestures were accepted in handset tests. | Keep these customizations when updating the shell or building a new image. |
| Rear camera | Preview works. The operator confirmed upright, non-mirrored text with the installed lmi4 libcamera correction. | Full photo and video recording, image quality and other modes are not comprehensively qualified. |
| Flashlight | Detected and operated successfully through the application. | Further long-duration and mode qualification. |
| Wi-Fi and USB | Wi-Fi and USB networking have been exercised. USB Type-C reconnection woke the handset and restored the USB network in dated suspend tests. | Confirm repeatability across longer sleeps and other connection scenarios. |
| Audio | A combined test kernel bound the TFA9874 speaker driver and loaded its tuning container. | Audible speaker playback remains unresolved; routing, DSP and mixer behavior need further investigation. Bluetooth and microphone are not fully qualified. |
| Battery and charging | Battery percentage is exposed; charging has been observed. | USB input-current policy, gauge interpretation, standby consumption and endurance remain open. |
| Modem and location | Modem/MHI and GNSS have diagnostic work in progress. | A reliable GPS fix and cellular operation are not established. |
| Front camera | The pop-up mechanism was exercised under Linux 4.19. | Motor and front sensor support still require Linux 7 integration and testing. |

The latest reported status and its evidence boundaries are recorded in the
[Linux 7 handset checkpoint](docs/status/LINUX7-CHECKPOINT-2026-11-01.md).
Older dated notes preserve their historical context; they do not necessarily
describe the currently installed kernel or userspace. In particular, a
successful driver probe or software test does not establish audible output,
a GPS fix, a calibrated current, or a complete hardware validation.

## Power and suspend

An overnight Linux 7 capture from 31 October to 1 November recorded a displayed
battery change from 95% to 58% over about 7 h 22 min, while the suspend-success
counter did not increase. It is not a measurement of suspended drain. The
display state and collector's effect on sleep need independent verification;
`bl_power=4` must not be treated by itself as proof that the screen was lit.
An earlier `s2idle` interval was observed, but s2idle alone does not establish
deep hardware residency or calibrated electrical consumption.

## Build and installation

Heavy kernel, package and image builds are run manually by the operator.
Kernel, boot menu, root filesystem and incremental userspace packages are
separate layers: a successful build or an accepted incremental change does not
automatically qualify a complete image. Verify the current device, artifact
identities, input availability and retained rescue paths before installation.

- [Linux 7 kernel and experimental work](kernel/experimental/linux7/README.md)
- [Complete Mobian image profile](build/profiles/lmi-current/COMPLETE-BUILD.md)
- [Permanent boot menu workflow](build/boot-menu/permanent/README.md)
- [Derived userdata builder](build/userdata/README.md)
- [Build and validation status](docs/status/CURRENT-BUILD.md)
- [Linux 7 handset checkpoint](docs/status/LINUX7-CHECKPOINT-2026-11-01.md)

Some build inputs and firmware are retained externally. Complete bit-for-bit
reconstruction of every kernel, userspace and vendor component has not been
demonstrated. Do not infer that an old local recipe is complete or current
without checking it against the installed build and available inputs.

## Repository map

- `kernel/`: configurations, patches and diagnostics.
- `userspace/`: Phosh, power, graphics, audio, camera, radios and applications.
- `build/`: image, menu and userdata recipes and profiles.
- `docs/`: status, architecture, provenance and dated validation records.
- `historical/`: earlier postmarketOS, OpenRC and Weston work.
- `tools/`: project utilities.

See the [architecture guide](docs/architecture/ARCHITECTURE.md),
[hardware validation records](docs/validation/), [NOTICE](NOTICE) and
[LICENSE](LICENSE). Generated images, package caches, proprietary firmware,
credentials, device identifiers and private logs stay outside Git. Retain one
qualified build and compatible rescue according to the
[artifact retention policy](docs/maintenance/ARTIFACT-RETENTION.md).
