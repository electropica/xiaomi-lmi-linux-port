# Device and userspace follow-up — 2026-11-05

This note distinguishes observations on the handset from source-only candidates.

## Phosh drawer

The custom Phosh drawer sometimes activated a different application after scrolling. Disabling animations did not resolve the reported symptom. On the handset the stock Debian `phosh` and `phosh-common` 0.46.0-3+deb13u1 were installed and the graphical session restarted. The operator confirmed that an icon opened the correct application after scrolling with an application open. The previous custom packages remain available as a recovery. This single successful scenario is not exhaustive validation. Stock Phosh omits other project-specific changes, which need review before selective reintroduction. The clean-image recipe still expects the custom packages and has not been updated to reproduce this handset configuration.

## USB maintenance

The running system's `usb0` had carrier but NetworkManager was waiting for DHCP and no IPv4 was configured. A NetworkManager profile bound to `usb0`, with a static maintenance address and no default route, was activated. SSH over USB succeeded afterwards; recovery after suspend remains untested. The clean-image recipe includes a corresponding profile and verification; shell syntax and overlay ordering were checked, but no new image has been built or tested with it.

## Audio

The user confirmed audible playback and a playlist in Lollypop on the clean system. The speaker route and associated configuration were present; long playback and every track transition were not independently qualified. Lollypop playlist import was enabled on the handset.

## Power

An unplugged daytime capture went from 88% to 27% over approximately 11 hours 10 minutes; no successful suspend was recorded in that interval. Samples were spaced by 10 minutes, so they are not a continuous electrical measurement. Later, two brief suspend cycles were observed. The running kernel has an RCU command-line option without the corresponding compiled support; its impact on power is unproven.

The system chassis was set to `handset`, which the reviewed GNOME power-manager source uses to suppress its automatic-suspend warning. The running power manager reads chassis at startup; the effect after a fresh session and any effect on wakeups remain to be tested. Sleep itself was not disabled.

## Calls and modem

GNOME Calls is installed and ModemManager was observed active, but no modem was listed. Historical observations reached SDX55 SBL and MHI Sahara channels; Mission/AMSS and calls remain unconfirmed. A read-only inventory of the device's modem partition found its own SDX55 firmware set. No firmware was copied or published, and the mapping and handoff sequence must be established before attempting a modem transfer.

## Touch selection in Files

An experimental Nautilus 48.3 patch proposes a touch multi-selection mode. It passed patch replay and static checks only; it has not been compiled or tested on a device. GTK gesture ordering, long press, scrolling, and view transitions need validation before use.
