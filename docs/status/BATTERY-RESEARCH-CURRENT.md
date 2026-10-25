# Battery research checkpoint — evening 25 October 2026

This checkpoint separates accepted behavior from hypotheses. Historical
next-action files must not override it or the coordinator's latest private
state. No physical residual-current calibration or culprit is established.

## Accepted behavior and current boundaries

The IRQ-name userspace fixes return naturally from gauge wakes to suspension
in about 15 s between D-Bus callbacks, about 16 s in retained kernel boundaries.
Seven natural callback cycles are available across two current short/long
windows. The historical ~1201s dwell has not recurred in those windows.
This is a real behavior improvement, not proof of a particular mA reduction.

The accepted handset remains on Phosh irqnames1+drawerpreview1, accepted
GSD IRQ-name handling and accepted private-target Phoc thumbnails.
drawersearch1+draweremptysearch1 is built (36 package tests, none skipped)
but NOT installed or touch-accepted. Full-image pins remain on accepted input.

The current passive night preserves normal settings and Wi-Fi. While unplugged,
do not contact the phone, including by Wi-Fi, install, restart or alter logging.
On explicit return, preserve the existing capture before any other device work.
The local coordinator records the exact fetch command and receipt identities.

## Next decisions, in order

1. Analyze the preserved night: clock-paired sleep and natural wake accounting,
   early/late reported-channel progression, USB/charging boundary exclusions.
   Display change, learned capacity, raw/software/shadow counters and endpoint
   ADC/filter readings must retain their different meanings.
2. If useful afterward, read only the generic cached Wi-Fi PS policy. The source
   review establishes why that request can matter, not that it is wrong on this
   phone. No scan, reconnect, setter or repeated radio-off test is selected.
3. Install the already-built empty-search UI candidate separately when the user
   can test it, keeping accepted rollback and avoiding a battery-window restart.

## Avoid rediscovering or over-closing these branches

| Topic | What is established | What must not be inferred |
| --- | --- | --- |
| ADC retry boundary | Known since 7 October; shared source bug, host repro now32 cases | New cause or reason for an immediate kernel build |
| Gauge capacity scales | Distinct source state/multipliers; SW counter can be primed | Learned/design ratio is physical wear or a universal correction factor |
| Displayed full state | Optional full-extension DT flags absent; normal tracking remains | All100->95loss is display-only, or percentage is calibrated energy |
| Modem / DSP labels | Availability/startup information and known interfaces | Missing enumeration, OFFLINING or missing SMEM means physically off |
| GPIO32 / WCD938x | Android binds despite invalid func2 warning | Binding asymmetry or an audio-current exclusion |
| Camera idle rails | Awake supply/pin observations | A complete deep-state electrical exclusion |
| GPU / RPMh | Static wiring and cached request evidence | Getters measure physical sleep rails |
| UFS / CNSS | Driver paths and retained transition evidence | A mainline patch automatically applies, or HIBERN8/DRV calibrates current |
| EUD debug USB | Matched sources/DT; explicit noirq clock-vote callbacks; secure mode can override default zero | Missing boot flag proves off, or callback presence measures physical power |
| Wi-Fi PS | Host suspend flush is conditional; generic getter is cached | Same INI means same runtime policy, or current policy has been measured |
| Grouped radio-off trial | No robust matched gain established | Every radio is electrically excluded, or identical repeat is justified |

## Current source/analysis records

- [Quiet long baseline](../validation/lmi-quiet-wake-long-baseline-2026-10-25.md)
- [Offline gauge recheck](../validation/lmi-offline-gauge-recheck-2026-10-25.md)
- [Wi-Fi host policy](../validation/lmi-wifi-sta-powersave-source-review-2026-10-25.md)
- [Pending UI candidate](../validation/lmi-empty-search-drawer-close-candidate-2026-10-25.md)

No automatic new experiment follows from an inconclusive night or missing
debug log. Name the remaining mechanism and what a proposed observation can
actually distinguish before involving the handset again.


### EUD infrastructure follow-up

The exact EUD source files at both retained kernel revisions are byte-identical
(SHA256 624232b87b13f26674ae655cd6201c22f47a962fb14cfff71c6e32aa56202da8).
Saved EUD DT properties also match. Its noirq suspend/resume callbacks release
and restore the optional ahb2phy clock vote. This contradicts only the proposed
missing-callback mechanism, not every possible EUD electrical contribution.

The default-zero enable parameter can inherit secure firmware mode at probe.
A conditional UART registration guard anomaly was noted against the inspected
serial-core return contract, but its runtime path is unobserved and changing it
could enable debug hardware. No patch, getter, control or new trial is selected.
See the [pinned source](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/a5b3099017ae581aae8bf597b2f9c8c765026af1/drivers/soc/qcom/eud.c).
