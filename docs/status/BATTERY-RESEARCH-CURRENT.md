# Battery research checkpoint — 26 October 2026

This checkpoint separates accepted behavior from hypotheses. Historical
next-action files must not override it or the coordinator's latest private
state. No physical residual-current calibration or culprit is established.

## Accepted behavior and current boundaries

The IRQ-name userspace fixes return naturally from gauge wakes to suspension
in about 15 s between D-Bus callbacks, about 16 s in retained kernel boundaries.
Forty-two natural callback cycles are available across the accepted short,
long and overnight windows. The historical ~1201s dwell has not recurred in those windows.
This is a real behavior improvement, not proof of a particular mA reduction.

The accepted handset remains on Phosh irqnames1+drawerpreview1, accepted
GSD IRQ-name handling and accepted private-target Phoc thumbnails.
drawersearch1+draweremptysearch1 is built (36 package tests, none skipped)
but NOT installed or touch-accepted. The operator now requests clearing every
query on completed close; the superseding searchclose1 candidate is host-checked
but NOT built or installed. Full-image pins remain on accepted input.

The overnight observation is now preserved and analyzed: 9h48m42s between
USB markers, 95.824% inferred suspension, display 100 -> 82, and 35 natural
gauge return gaps around 15 seconds. Its early/late raw progression differs
by less than 1%, while software/shadow rates slow by about 33%. This is channel
divergence, not established electrical-current improvement. See the
[night validation](../validation/lmi-quiet-wake-night-2026-10-26.md).

## Next decisions, in order

1. Do not repeat an identical Mobian-only night to resolve the channel scale.
   Existing Android rounded software history lacks matching continuous raw
   endpoints. A future matched Android capture of all three channels and clocks
   could compare divergence; it still would not be an external current meter.
   No new observation or OS switch has been started.
2. The cached Wi-Fi getter was unavailable (iw absent). NetworkManager's active
   profile reads default, without an explicit powersave entry found in printed
   global config. Actual firmware PS remains unknown; no policy is changed.
3. Build the superseding searchclose1 candidate for the new clear-every-query
   request, then install separately when the user can test it. Keep accepted
   preview1 rollback and complete-image pins. Battery evidence is preserved first.

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
