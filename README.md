# Mobian on the POCO F2 Pro

**A modern Linux phone, built in the open.** This project brings Mobian, Phosh and Linux 7 to the Xiaomi Redmi K30 Pro / POCO F2 Pro (`lmi`), powered by the Qualcomm Snapdragon 865 and Adreno 650.

From early boot experiments to an interactive mobile desktop, each improvement is built, tested on the phone and documented here. The project is actively developed, with ongoing work on power management, hardware support and a cleaner, easier-to-maintain system.

## The phone today

The Linux 7 port boots Mobian from a persistent menu and runs a personalized Phosh desktop. Recent handset tests have demonstrated:

- **A touch-friendly desktop:** display, touchscreen, unlock, gestures, application drawer and GPU rendering.
- **A tailored home screen:** favorites, drawer scrolling, search and the requested 300% display scale.
- **Rear camera and flashlight:** a working camera preview with corrected orientation, plus flashlight control through its app.
- **Sound and media:** audible speaker playback, including two consecutive tracks in Amberol.
- **Connectivity and power:** Wi-Fi and USB networking, battery reporting, charging and observed `s2idle` suspend.
- **Recovery choices:** a boot menu with Android/LineageOS and recovery paths alongside Mobian.

These are results observed during development, not a guarantee that every mode works on every build. The [current build status](docs/status/CURRENT-BUILD.md) and dated [validation records](docs/validation/) provide the details.

## What we're building next

Current work focuses on reducing standby drain, improving charging and wake-up behavior, advancing modem and GPS support, and bringing the pop-up front camera to Linux 7. An experimental [clean Mobian 7 root filesystem](userspace/mobian-clean-linux7/README.md) has also been built and checked off-device to make future updates and maintenance easier.

## Explore the project

| Start here | What's inside |
| --- | --- |
| [Linux 7 development](kernel/experimental/linux7/README.md) | Kernel configuration, patches and hardware bring-up. |
| [Mobian status](docs/status/MOBIAN-STATUS.md) | Recent milestones and device observations. |
| [Build status](docs/status/CURRENT-BUILD.md) | Build identities, status and validation context. |
| [Boot menu](build/boot-menu/permanent/README.md) | Permanent menu workflow and recovery context. |
| [Clean Mobian 7 recipe](userspace/mobian-clean-linux7/README.md) | Experimental userspace recipe and image checks. |
| [Architecture](docs/architecture/ARCHITECTURE.md) | How the project fits together. |

`main` follows Linux 7 development. Earlier Linux 4.19 work is retained on `archive/linux-4.19`. Proprietary firmware, generated images, personal data and credentials are kept outside the public repository. See [NOTICE](NOTICE) and [LICENSE](LICENSE) for project and licensing information.
