# Battery campaign: USB comparison and idle behavior

## Measurements from 17–18 November

The reported L1 and L2 repetitions each lasted 45 minutes at a reported 100% battery level. L1 inhibited charging while USB data remained connected; L2 additionally disabled the phone's USB data interface. Both retained VBUS. The reported mean battery currents were approximately -3.76 mA and -3.62 mA respectively. These are **battery currents with USB power present**, not the handset's total power consumption and not a replacement for physical disconnection.

A physically unplugged, awake, screen-off observation reported approximately -122 mA with WLAN active; another reported approximately -124 mA with radios blocked. Different battery levels and temperatures limit comparison. These results do not establish a quantitative upper bound on Wi-Fi power.

One experimental CPU load remained active for almost seven hours after an SSH interruption. Affected observations were marked contaminated or repeated. Test harness cleanup and guards were subsequently changed. Sample currents are estimates subject to sensor calibration and sampling limitations.

## 21–22 November: CPU idle and sleep

A controlled physical-disconnection comparison measured CPU0's WFI state disabled versus enabled for 30 minutes per condition, excluding the first three minutes. The respective mean battery currents were -131.77 mA and -132.56 mA (322 samples each). Start/end reported battery levels were 100–97% and 97–94%. The 0.79 mA difference is not enough to establish a saving; the high initial state of charge and sequential design are limitations. The original CPU0 setting was restored.

The test's sleep inhibitor caused a suspend request at 22:35 to be refused. Although the inhibitor was released at 23:30, no subsequent suspend was recorded during the night. This is not a measurement of s2idle consumption. The installed GSD refusal fix restores the logical idle mode but does not automatically guarantee another attempt after the inhibitor disappears.

## Installed software and open work

MiniMax reports that the Mobian v4 image was flashed and checked on 21 November. Its image receipt still lists the whole-image SHA-256 as pending; the receipt alone does not establish a whole-image hash. The full v4 recipe is not yet present in this repository.

The CPU guard on the running phone was changed to alert-only, avoiding termination of legitimate applications. A candidate GSD retry fix exists locally, but compilation and behavioral checks must not be confused with validation on the handset. Do not deploy it without testing inhibitor handling, activity, session changes and rollback.

The modem's contribution remains unmeasured. An `apps_rsc` interrupt count alone does not prove modem activity or its power consumption. RTC, deep-sleep domain statistics and the existence of a usable charge counter remain separate questions.
