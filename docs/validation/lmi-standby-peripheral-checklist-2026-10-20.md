# lmi standby peripheral checklist — October 20, 2026

## Scope and evidence rules

This is the common audit ledger, not a list of excluded physical consumers.
The connected handset inventory contains 849 compatible DT nodes and 697 bus
entries, of which 607 have bound drivers. Entries include controllers, child
interfaces and virtual devices; they are not counts of physical chips. The
inventory covers 15 named Linux bus namespaces, not every possible Linux class
or firmware-owned device. The complete private inventory preserves every entry,
including unbound entries, its DT link and cached runtime PM status.

The running DT declares 247 single-phandle supply references, all resolved,
and 197 pinctrl-state reference properties. An additional suffix match,
`qcom,use-ext-supply`, is an empty flag rather than a supply phandle. These
dependencies identify candidate paths; they do not establish the state selected
in suspend. Shared rails, firmware ownership and required wake functions mean
that an enabled rail or missing runtime-PM flag is not automatically a fault.

Evidence levels below: **S** source/declared wiring; **A** awake snapshot;
**T** retained suspend-transition evidence; **C** consumption comparison using
the gauge. None is a calibrated per-rail electrical measurement. Existing traces
can come from older boots: their result is historical evidence to requalify,
not an assertion about every transition in today's image.

## Audit matrix

| Block / actual implementation | Existing evidence | Expected idle/suspend behavior to verify | Remaining gap / next evidence | Priority |
|---|---|---|---|---|
| Application CPUs, cpuidle, system collapse | T: actual suspension and firmware residency correlate; C: CPU/core_ctl controls already attempted | Enter permitted low-power states; restore normal interaction | Keep system residency as a control; avoid another identical CPU-policy test without new evidence | Existing control |
| NPU and NPU interconnect | T/C: standby vote reduction installed; normal-use restoration validated | Release unnecessary sleep votes; restore active votes | Requalify after a policy change, not a new blind disable | Existing control |
| DDR, LLCC/L3, bus bandwidth, SMMUs | S/T: firmware sleep evidence, RPMh requests; L3 control already tried | Sleep-bank requests consistent with required retained memory and clients | Associate remaining requests with actual consumers and firmware ownership; no physical-current attribution yet | Open |
| PMIC regulators, BOB, shared codec rails | S/T: 106 named regulators / 374 selected properties match reconstructed Lineage configuration; BOB bypass sleep commands; S4 shared | Correct aggregate active/sleep votes, not universal rail-off | Distinguish valid sleep requests, shared users and measured state; do not read zero invalid cache as disable | Open |
| Display panel, DSI, display PMIC | A/T: display domain off snapshot and retained transition evidence | DCS/power sequencing and display rails low-power when screen is off | Panel-specific sequence and rail requests during a qualified sleep interval; software screen-off alone insufficient | Open |
| FocalTech touchscreen / xiaomi-touch | Bound live; historical notifier correction and post-resume interaction tests | Correct suspend callback / intentional wake mode | Trace selected pin/power path and correlate any wake IRQ; no new unbind planned | Open |
| GPU Adreno650 / KGSL | Bound live; no GPU workload in standby protocol | No outstanding rendering/performance request; appropriate GPU rail/clock state | Join retained GPU/clock evidence to sleep windows and clients before adding a test | Open |
| UFS host / PHY / ICE | S: reviewed individual lane-clock logic; RP5 bulk-clock patch mechanism absent | Link/PHY/clock policy consistent with suspend and required retention | Actual selected low-power link/clock state is not proven by source alone | Open |
| Wi-Fi QCA6390 / CNSS / PCIe / MHI | S/A/C: DRV path, M3_FAST and runtime-suspended endpoint; radio-off votes zero, no robust short-comparison gain | Supported DRV suspend, not necessarily ordinary D3hot; radio-off releases its requests | No basis to repeat identical radio-off test; physical residual under DRV remains unmeasured | Bounded, not excluded |
| Bluetooth/FM QCA6390 / btfmslim / bt_power | Bound live; distinct from Wi-Fi path | No unintended BT/audio session, appropriate BT votes and clocks | Separate BT-client/clock proof from Wi-Fi-off result | Open |
| External modem / IPA / rmnet / modem-facing firmware | S: earlier modem state-label qualification; bound interfaces present | Intended modem/transport sleep state with no unintended client request | Firmware ownership, modem-specific residency and rails; a state string or bound IPA driver alone is insufficient | Open |
| ADSP / audio DSP / APR / FastRPC | S/T: prior master-residency audit; audio functionality tested | Firmware low-power with no audio client holding routes/requests | Associate active clients with retained firmware sleep counters; DSP need not be powered fully off | Open |
| SLPI/SSC / sensor firmware | S/A: sensors-ssc loader identified; generic pm_genpd exposes no SSC domain | Firmware low-power appropriate to requested sensors | Obtain applicable firmware/client evidence; absent generic debugfs does not prove off or on | Open |
| CDSP / FastRPC / secure DSP services | Bound live; separate from SSC and ADSP | Release unnecessary compute requests, preserve required secure services | Client/residency/rail evidence not yet consolidated | Inventory-only |
| WCD938x / SoundWire / Bolero macros | S/A/T: component bias Off, card Standby, late-suspend callback; shared-supply policy reviewed | No active unwanted route; appropriate macro/clock/supply requests | A bias snapshot and callback success do not establish all sleep-rail states | Bounded, not excluded |
| TFA9874 speaker amplifier | A/S: amplifier audited; live tfa98xx driver; no standby playback | Amplifier standby and no unintended stream | Tie any hardware state evidence to sleep interval; do not substitute WSA driver assumptions | Bounded, not excluded |
| Camera sensors / CCI / ISP / IPE / BPS / OIS / actuators / EEPROM | S/A: six described sensor nodes; 13 disabled supplies/domains; 18 selected clock/reset/CCI pins low inputs with pull-down at plugged idle | No capture; release sensor and imaging pipeline requests | Suspend-time states not established by idle snapshots; six DT nodes do not prove six fitted sensors | Open |
| Front-camera DRV8846 motor | S/T: power-enable GPIO153 commanded low on suspend, callbacks succeed | Motor enable low when unused | Physical rail state not measured; do not operate motor to test standby | Bounded, not excluded |
| AKM09970 magnetic sensor at I2C5:0x0d | Bound live; S: power-up/down and user activation code, active/suspend pin definitions | Remain in intended power-down when not requested | Establish actual role, consumers, selected pins and rail votes; name/comment alone does not establish use as a navigation compass | Newly consolidated gap |
| Goodix fingerprint / FOD | S/A: platform device, not SPI0.0; no holder found in bounded earlier scan | No unwanted fingerprint session; intended power/reset/pin policy | Initial pin/physical sleep state not proved by no open descriptor | Open |
| NFC nq-nci | C: prior off/on comparison, no established residual cause | Intended radio-off or wake-capable low power | Reuse existing result; require a new mechanism before repeat | Bounded, not excluded |
| IR transmitter spi0.0 | S: regulator acquired at probe, enabled around transmission then disabled | No transmit, no sustained request | Quiescent physical current not measured; absent runtime PM is not proof of activity | Bounded, not excluded |
| AW8697 vibrator at I2C3:0x5a | Bound live; source has effect/timer/work queues | No running vibration/effect/boost request while unused | Read full idle/stop/probe paths and audit safe cached status before any hardware query | Newly consolidated gap |
| Two AW2015 LED controllers at I2C2/6:0x64 | Both bound live; source brightness work identified | No unintended channel/breathing/enable request | Determine active logical channels, GPIO enables and autonomous pattern behavior; no register dump yet | Newly consolidated gap |
| PMIC flash LED / tri-LED / PWM | Bound live; torch previously functional | No flash/torch/pattern requested during standby | Confirm requested state and associated supplies; generic DT child nodes do not prove active outputs | Open |
| USB controller / PHY / BAM / USB-PD | T: retained suspend traces; recent charging-isolation probe disturbed screen/power context | Appropriate disconnected policy; charging-only is not equivalent to unplugged | Reuse actual unplugged evidence; no charge-disable comparison interpreted as clean standby | Open |
| FSA4480 USB-C analog mux at I2C5:0x42 | Bound live; S: defaults at probe, USB notifier, freezable workqueue | Correct disconnected analog routing with no unintended work/vote | Compare default/disconnected settings and notifier path; no proof of sleep analog current | Newly consolidated gap |
| SMB5 charger / Qnovo / PD PHY | S: charge_done side effects known; explicit collector call removed | Normal protection and appropriate no-input mode | Retain protections; distinguish kernel work from observer-caused effects | Open |
| BQ25970 charge-pump family | S/A/T: conversion inactive snapshots; qualified ADC-disable trace | No unintended conversion/ADC activity in sleep | Quiescent current and other modes not measured; do not rerun same ADC test | Bounded, not excluded |
| I2C PMIC at smb1390_slave node | Parent i2c_pmic bound; charge_pump_slave child unbound. Child driver disabled in both running Mobian and retained Lineage configs. Parent without interrupt-controller can populate children without hardware detection | Intended policy for physically fitted components | Not a demonstrated Mobian-only missing-driver issue; registration does not prove chip presence or its electrical state | Qualified, not a new patch |
| FG gen4 / BMS / model accounting | S/A/C: learned/nominal scales, direct/filtered reads, read side effects and calibration callers qualified | Correct estimation and temporary telemetry cleanup | Planned incremental read-order test; no independent electrical calibration available | Active investigation |
| DS28E16 battery authentication / one-wire | Bound live; S: initial verification with at most five delayed retries in inspected worker | No unexplained recurrent verification activity | Checked worker alone is bounded, not an endless periodic poll; other calls and runtime activity remain to map | Newly consolidated gap |
| Thermal ADC / TSENS / BCL / QMI sensors | Bound live; BCL coarse resolution already qualified | Necessary protection/monitoring without unintended clients | Separate protection from sampling/client activity; never disable protections as a diagnostic shortcut | Open |
| RTC / alarmtimer / GPIO keys / wake sources | Protocol checks RTC alarm and reason provenance; wake-reason getter is not read-to-clear | Only intended wake requests; normal user wake functions work | Keep alarms and reason attribution as controls, not newly presumed residual consumers | Existing control |
| EUD/debug / secure services / remaining infrastructure drivers | Present in full driver inventory; includes msm-eud, QSEE, SPSS, QUP, clocks and transport services | Required low-power requests without unwanted debug/client activity | Each unassigned driver remains inventory-only until reviewed; presence is not a fault | Inventory-only |

## Work order

1. Resolve the newly consolidated auxiliary gaps from source and existing
   evidence first: FSA4480, AW8697, the two AW2015 controllers, AKM09970 and
   the actual I2C PMIC driver. A missing system-suspend callback is not by
   itself evidence of continuous power: hardware may already be in standby.
2. Map each candidate to the live DT supply/pinctrl dependencies and its real
   activation/stop path. Verify that any proposed getter is safe before reading
   it. Do not bulk-read sysfs controls or register maps.
3. Review shared-rail, display, UFS, modem and firmware evidence at the actual
   sleep boundary. Keep firmware-owned state separate from Linux runtime flags.
4. Choose a new physical comparison only after naming a candidate state and
   predicted difference. Prefer one bounded observation covering multiple
   passive transitions rather than disabling components one by one blindly.
5. A subsequent grouped one-hour trial completed after the operator's
   unplug: Wi-Fi off, exposed rfkill blocked, audio services and camera monitor
   stopped, no capture/PCM holder at arming, vibration/lighting commanded off,
   location requests disabled and GeoClue masked. This is not a universal
   hardware power-off: no NFC rfkill or IIO sensor proxy was exposed, and
   GNSS/SSC firmware or every camera rail is not demonstrated off. Automatic
   suspension temporarily uses 60 seconds, with restoration to 900 seconds.
   Late filtered resume samples remained around 49 mA, with 95.96% of the whole
   window suspended. The settings were restored and verified. See the
   [result and accounting qualifications](lmi-minimal-scope-result-2026-10-20.md).
   The separate read-order run remains deferred. The
   inventory itself added no alarm or power-policy change.

The first grouped-trial arming attempt failed before observation on a generic
LED-trigger write. A subsequent attempt to restore nominal nonzero flash LED
brightness values briefly illuminated the torch, reported by the operator.
Off commands completed successfully. The corrected protocol never restores
nonzero torch/flash current settings as brightness requests, and edits triggers
only for ordinary notification LEDs. Initial normal services/radio/timeout and
notification LED settings were verified restored before the corrected trial.
This failed attempt is not a consumption measurement.

## Evidence references

### Offline auxiliary source review

A fresh, bounded review traced the four retained driver implementations. It
does not demonstrate a cause of the residual gauge estimate:

- AW8697 `activate=0` cancels the duration timer, changes cached state and
  queues vibrator work. The worker's stop path requests controller standby,
  not verified supply removal. The I2C registration has no PM callback.
- AW2015 brightness work disables the controller when all channel-enable bits
  are clear. Its breathing/pattern engine can progress in hardware. No suspend
  callback is registered; shutdown/reset is a different path. Zero requested
  brightness must be interpreted with queued work and all controller channels.
- AKM09970 probe temporarily powers the device to check its ID, then explicitly
  powers down and initializes the power-enabled state false. User activation
  can later enable continuous measurement, IRQ, timer and work; deactivation
  reverses them. Active/suspend pin definitions alone do not prove a suspend
  transition: the I2C registration has no PM callback. Its cached `chip_rev` and
  `debug` show methods do not perform a sensor transaction.
- FSA4480 initializes defaults, then handles USB-mode changes on a freezable
  workqueue with a temporary wake reference. The no-adapter path requests
  disconnected routing. There is no cached routing getter or PM callback in
  the inspected source, and no proof of physical rail shutdown.

Missing PM callbacks alone do not establish a bug when a device is already in
standby. The review does not authorize register dumps or new controls. No
additional phone observation is made during the unplugged hour. Follow-up
state/consumer checks, if useful, wait until the operator reconnects.

### Retained validation notes

- [Earlier peripheral, supply, pin and firmware review](quiet-gauge-night-2026-10-13.md)
- [Complete transition and USB-cycle qualification](quiet-gauge-overnight-2026-10-12.md)
- [UFS and charger/gauge follow-up](lmi-standby-followup-2026-10-19.md)
- [Getter side-effect review](lmi-read-control-getter-review-2026-10-20.md)
- [Complete bound-driver coverage list](lmi-standby-driver-coverage-2026-10-20.md)

Private evidence: topology-private.json, dt-dependencies-private.json and
auxiliary-sources-private.json under the coordinator's peripheral-audit folder.
These raw connected observations are retained locally, not published as proof
of physical sleep-current exclusion. No new power setting, unbind, calibration,
build, flash, camera capture, microphone recording or register dump was used.

The [subsequent idle-path review](lmi-standby-idle-followup-2026-10-20.md) qualifies touch/display journal evidence, auxiliary ownership, the SSC character interface and ordinary codec reset/supply paths. No new power fix or physical-current exclusion is established.
