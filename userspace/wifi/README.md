# lmi Wi-Fi integration

scripts/lmi-wlan-firmware-prepare exposes the stock QCA6390 firmware and
standard WLAN configuration paths without adding proprietary files to Git.
It checks required inputs and the resolved vendor INI/MAC-data targets.

Firmware preparation is not a promise that Android and Linux select identical
runtime power policy. Device-tree votes, WoW/DRV and cached nl80211 requests
are distinct from physical radio sleep state.

See the [STA power-save source review](../../docs/validation/lmi-wifi-sta-powersave-source-review-2026-10-25.md)
for the inspected host paths and the limited future cached getter. No power-save
change or new radio-off test is selected by that review.
