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
| Graphical session / Phosh / Phoc | C: complete same-kernel three-phase A/B/A, all phases about 99.5% suspended, software estimates 49.87 / 51.49 / 52.04 mA | No unintended retained client or graphics request in sleep | No saving demonstrated by stopping the session; does not electrically exclude shared resources or gauge-model effects | Deprioritize another GUI shutdown test |
| Application CPUs, cpuidle, system collapse | T: actual suspension and firmware residency correlate; C: CPU/core_ctl controls already attempted | Enter permitted low-power states; restore normal interaction | Keep system residency as a control; avoid another identical CPU-policy test without new evidence | Existing control |
| NPU and NPU interconnect | T/C: standby vote reduction installed; normal-use restoration validated | Release unnecessary sleep votes; restore active votes | Requalify after a policy change, not a new blind disable | Existing control |
| DDR, LLCC/L3, bus bandwidth, SMMUs | S/T: firmware sleep evidence, RPMh requests; L3 control already tried | Sleep-bank requests consistent with required retained memory and clients | Associate remaining requests with actual consumers and firmware ownership; no physical-current attribution yet | Open |
| PMIC regulators, BOB, shared codec rails | S/T: 106 named regulators / 374 selected properties match reconstructed Lineage configuration; BOB bypass sleep commands; S4 shared | Correct aggregate active/sleep votes, not universal rail-off | Distinguish valid sleep requests, shared users and measured state; do not read zero invalid cache as disable | Open |
| Display panel, DSI, display PMIC | A/T: grouped-hour journal shows ESD IRQ disable; next retained modeset/ESD enable at USB return. Older trace contains VCI disable request | DCS/power sequencing and display rails low-power when screen is off | No physical panel-rail measurement during suspend; retained log absence is not electrical exclusion | Bounded, not excluded |
| FocalTech touchscreen / xiaomi-touch | S/T: actual grouped-hour POWER DOWN, IRQ disable and gesture-disabled suspend; no intermediate resume or reported sleep-write failure before USB return | Correct suspend callback / intentional wake mode | Ordinary sleep-command path supported; physical rail/pin current remains unmeasured | Software suspend verified |
| GPU Adreno650 / KGSL | S/A/T: connected same-boot force_clk_on, force_bus_on and force_rail_on are zero; force_no_nap is one. Source distinguishes NAP from full SUSPEND; historical KGSL suspend callbacks return zero | Release work and enter full GPU suspend; NAP is a separate intermediate idle state | No forced-on clock/bus/rail override observed. No-NAP alone does not block the inspected full-suspend path; actual current and current-boot sleep state remain unmeasured | Bounded, not excluded |
| UFS host / PHY / ICE | S: reviewed individual lane-clock logic; RP5 bulk-clock patch mechanism absent | Link/PHY/clock policy consistent with suspend and required retention | Actual selected low-power link/clock state is not proven by source alone | Open |
| Wi-Fi QCA6390 / CNSS / PCIe / MHI | S/A/C: DRV path, M3_FAST and runtime-suspended endpoint; radio-off votes zero, no robust short-comparison gain | Supported DRV suspend, not necessarily ordinary D3hot; radio-off releases its requests | No basis to repeat identical radio-off test; physical residual under DRV remains unmeasured | Bounded, not excluded |
| Bluetooth/FM QCA6390 / btfmslim / bt_power | S/A/C: custom HCI path requires attachment; retained no-HCI/UART-suspended evidence; original BT block preserved during grouped radio-off trial | No unintended BT/audio session, appropriate BT votes and clocks | No new harmful config branch; shared physical rails not excluded by labels or transport state | Bounded, not excluded |
| External modem / IPA / rmnet / modem-facing firmware | S: earlier modem state-label qualification; bound interfaces present | Intended modem/transport sleep state with no unintended client request | Firmware ownership, modem-specific residency and rails; a state string or bound IPA driver alone is insufficient | Open |
| ADSP / audio DSP / APR / FastRPC | S/T: prior master-residency audit; audio functionality tested | Firmware low-power with no audio client holding routes/requests | Associate active clients with retained firmware sleep counters; DSP need not be powered fully off | Open |
| SLPI/SSC / sensor firmware | S/A: SSC character open/release are no-ops and ioctl reads a timer; no direct holder found in 523-process connected scan | Firmware low-power appropriate to requested sensors | Descriptor absence is not firmware power state. Per-DSP votes/residency remain unproven by aggregate CPU/AOSS counters | Open |
| CDSP / FastRPC / secure DSP services | Bound live; separate from SSC and ADSP | Release unnecessary compute requests, preserve required secure services | Client/residency/rail evidence not yet consolidated | Inventory-only |
| WCD938x / SoundWire / Bolero macros | S/A/T: prior bias/clock audit; ordinary suspend does not assert reset. Supply-LPM helper conditionally sets requested load, not unconditional rail disable | No active unwanted route; appropriate macro/clock/supply requests | Reset mux difference alone is not a demonstrated suspend fault; physical shared-supply state remains unmeasured | Bounded, not excluded |
| TFA9874 speaker amplifier | A/S: amplifier audited; live tfa98xx driver; no standby playback | Amplifier standby and no unintended stream | Tie any hardware state evidence to sleep interval; do not substitute WSA driver assumptions | Bounded, not excluded |
| Camera sensors / CCI / ISP / IPE / BPS / OIS / actuators / EEPROM | S/A: six described sensor nodes; 13 disabled supplies/domains; 18 selected clock/reset/CCI pins low inputs with pull-down at plugged idle | No capture; release sensor and imaging pipeline requests | Suspend-time states not established by idle snapshots; six DT nodes do not prove six fitted sensors | Open |
| Front-camera DRV8846 motor | S/T: power-enable GPIO153 commanded low on suspend, callbacks succeed | Motor enable low when unused | Physical rail state not measured; do not operate motor to test standby | Bounded, not excluded |
| AKM09970 magnetic sensor at I2C5:0x0d | S/A: probe powers down; connected follow-up found associated pm8150a_l8 request disabled with zero users and no direct holder | Remain in intended power-down when not requested | Cached regulator request is not measured voltage/current; no proof of every suspend-time state or actual board role | Software idle bounded |
| Goodix fingerprint / FOD | S/A: platform driver probe leaves inherited GPIO state; sleep ioctl is a stub and disable is flag-dependent. Fresh connected GPIO23/26/27 inputs low with pull-down, mux/GPIO unclaimed | No unwanted fingerprint session; intended power/reset/pin policy | No observed Linux-held enable-high in this snapshot; sensor supply and physical sleep current remain unmeasured. No unbind/ioctl/GPIO write performed | Bounded, not excluded |
| NFC nq-nci | C: prior off/on comparison, no established residual cause | Intended radio-off or wake-capable low power | Reuse existing result; require a new mechanism before repeat | Bounded, not excluded |
| IR transmitter spi0.0 | S: regulator acquired at probe, enabled around transmission then disabled | No transmit, no sustained request | Quiescent physical current not measured; absent runtime PM is not proof of activity | Bounded, not excluded |
| AW8697 vibrator at I2C3:0x5a | S/C: activate=0 queues stop; worker requests standby. Grouped trial issued stop; no demonstrated late filtered-current reduction | No running vibration/effect/boost request while unused | Stop request is not physical boost/rail isolation; no new identical disable test justified | Bounded, not excluded |
| Two AW2015 LED controllers at I2C2/6:0x64 | S/C: reviewed all-channel disable worker; grouped trial removed ordinary LED triggers and requested zero brightness | No unintended channel/breathing/enable request | Autonomous pattern and physical sleep-current state are not proved by brightness requests alone | Bounded, not excluded |
| PMIC flash LED / tri-LED / PWM | Bound live; torch previously functional | No flash/torch/pattern requested during standby | Confirm requested state and associated supplies; generic DT child nodes do not prove active outputs | Open |
| USB controller / PHY / BAM / USB-PD | T: retained suspend traces; recent charging-isolation probe disturbed screen/power context | Appropriate disconnected policy; charging-only is not equivalent to unplugged | Reuse actual unplugged evidence; no charge-disable comparison interpreted as clean standby | Open |
| FSA4480 USB-C analog mux at I2C5:0x42 | S: disconnected routing and freezable notifier work traced; no qualified cached routing getter | Correct disconnected analog routing with no unintended work/vote | No evidence of a faulty active route or physical quiescent draw; do not infer fault from missing PM callback | Bounded source review |
| SMB5 charger / Qnovo / PD PHY | S: charge_done side effects known; explicit collector call removed | Normal protection and appropriate no-input mode | Retain protections; distinguish kernel work from observer-caused effects | Open |
| BQ25970 charge-pump family | S/A/T: conversion inactive snapshots; qualified ADC-disable trace | No unintended conversion/ADC activity in sleep | Quiescent current and other modes not measured; do not rerun same ADC test | Bounded, not excluded |
| I2C PMIC at smb1390_slave node | Parent i2c_pmic bound; charge_pump_slave child unbound. Child driver disabled in both running Mobian and retained Lineage configs. Parent without interrupt-controller can populate children without hardware detection | Intended policy for physically fitted components | Not a demonstrated Mobian-only missing-driver issue; registration does not prove chip presence or its electrical state | Qualified, not a new patch |
| FG gen4 / BMS / model accounting | S/A/C: eight valid natural-wake probes, four counter bursts/four direct controls; all immediate direct/filtered pre/post deltas zero. Retained auth-log pattern scan negative | Correct estimation and temporary telemetry cleanup | Millisecond probe does not exclude delayed/common effects or calibrate physical sleep current. No repeated identical read-order night justified | Immediate read-control completed |
| DS28E16 battery authentication / one-wire | S/A: bounded retry workers plus conditional BMS-uevent/sysfs live transaction paths; selected auth patterns absent in 2695 retained kernel rows | No unexplained recurrent verification activity | No recurring transaction source established; absent messages do not prove no calls. Do not invoke transactional getters as passive status checks | Source path qualified, runtime cause unproven |
| Thermal ADC / TSENS / BCL / QMI sensors | Bound live; BCL coarse resolution already qualified | Necessary protection/monitoring without unintended clients | Separate protection from sampling/client activity; never disable protections as a diagnostic shortcut | Open |
| RTC / alarmtimer / GPIO keys / wake sources | Protocol checks RTC alarm and reason provenance; wake-reason getter is not read-to-clear | Only intended wake requests; normal user wake functions work | Keep alarms and reason attribution as controls, not newly presumed residual consumers | Existing control |
| EUD/debug / secure services / remaining infrastructure drivers | S/T: EUD noirq clock release reviewed; retained QSEE DT disables clock support; SPSS proxy resources are framework-managed. Historical successful resume callbacks only | Required low-power requests without unwanted debug/client activity | No new harmful power branch established; secure retention and physical suspend rails not excluded. Remaining unassigned classes stay inventory-only | Bounded source review |

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

## Coordinator update after October 20 source and connected-state checks

No new peripheral was electrically isolated or independently measured in
this update. Thirteen matrix rows now distinguish completed source/control
checks from the still-open physical-current question. The grouped one-hour
trial remains the latest grouped control; its result is unchanged. No new
residual-drain cause or autonomy gain is demonstrated.

The fresh fingerprint check read existing Qualcomm GPIO summaries only:
GPIO23, GPIO26 and GPIO27 were input-low, function 0, pull-down, and unclaimed
in the connected same-boot snapshot. The prior generic pin summary had not
reported direction/level; the native gpioN format supplied those fields.
Neither snapshot establishes sensor-rail current during deep sleep.

Parallel review outputs and coordinator decisions are retained in a private
research registry with per-file SHA-256 hashes and a verified text archive.
Incorrect mixed-window and overstrong capacity-normalization conclusions were
corrected, not adopted as kernel findings. The secondary GSD awake-grace draft
is deferred; the primary objective remains residual consumption during sleep.
The full-Android comparison is complete locally: the saved 8 h 37 m night
reports 32.84 mA net / 33.53 mA sum-of-decreases; the separate post-short-charge
13 h 29 m day reports 11.12 / 13.94 mA. These are related gauge accounting
paths, not independent physical current measurements. They do not identify
a peripheral cause or justify generalizing a 10–15 mA Android baseline.



### Solo GPU override check

The connected read sampled only four cached KGSL control bits; it did not
read GPU registers, performance counters, or write a power setting. The three
forced-on controls were zero, while force_no_nap was one. In the retained
kgsl_pwrctrl.c, the latter bit gates the immediate ACTIVE-to-NAP request in
kgsl_active_count_put; _suspend instead drains work, waits for active users,
idles, calls _slumber, and selects SUSPEND without checking that NAP bit.
This distinguishes a possible awake-idle policy from a demonstrated deep-sleep
failure. It does not justify toggling the bit or claiming the GPU electrically
excluded. No new unplugged comparison was requested for this negative check.

The [completed same-kernel graphical/headless A/B/A](lmi-headless-aba-result-2026-10-21.md) reports no demonstrated reduction after stopping Phosh/Phoc; all phases and restoration passed.

## 2026-10-22 addendum — display row transition evidence

`docs/validation/lmi-panel-vci-release-timing-2026-10-22.md` adds **T** level
evidence to the display row, from the retained raw traces only. On the
LineageOS reference `display_panel_vci` and `pm8150_l14` are released at
screen-off, 255 s to 1796 s before the corresponding suspend entry; on the
2026-10-12 Mobian wide trial they are released 0.301 s before the suspend
entry, inside the suspend path, and are not re-enabled in the observed
post-resume window. The rails are off during the powered-down interval on both
platforms, so this is a difference in the **screen-off to suspend idle gap**,
not in the suspend state. It is invisible to a deep-suspend current
measurement.

The row stays **Open**: the current drawn by a requested display panel rail
is not measured, the Mobian observation comes from an uncertified older build,
and the length of the Mobian idle gap is not measured. The cheapest
discriminator is one awake, read-only observation of the panel rail state
during the idle gap on both platforms.


## 2026-10-22 addendum — UFS row narrow result

A privileged, read-only LineageOS read (operator-authorised `adb root`,
reversed with `adb unroot` in the same script) and the retained Mobian
snapshot give **the same value for every UFS policy attribute that exists on
both sides**: `clkgate_enable=1`, `clkgate_delay_ms=50`, `rpm_lvl=3`,
`spm_lvl=3`, `auto_hibern8=1000`. Neither clock-scaling spelling is
enumerated on the reference. The line "Actual selected low-power link/clock
state is not proven by source alone" is narrowed to: the **policy values**
now agree for the five shared attributes, on the reference kernel, at one
plugged awake moment.

The row stays **Open**: a plugged awake read is not a sleep observation, the
Mobian side of the newer attributes (`rpm/spm_target_link_state`,
`rpm/spm_target_dev_state`, `psa_state`, `current_power_mode`,
`qcom/power_mode`, `max_bus_bw`) is still missing, the `ufs_core.c` show/store
implementations were not compared, and the actual link and PHY state during a
qualified sleep interval is still unproven.


## 2026-10-22 addendum — UFS row closed for the policy

With the Mobian privileged capture (current kernel `a5b3099017ae`, root over
the existing SSH route, USB connected) the UFS comparison is now **complete on
the policy**: every UFS policy attribute observed on both platforms has the
**same value**, including `clkgate_enable=1`, `clkgate_delay_ms=50`,
`rpm_lvl=3`, `spm_lvl=3`, `auto_hibern8=1000`,
`rpm/spm_target_link_state=HIBERN8`, `rpm/spm_target_dev_state=SLEEP`,
`attributes/psa_state=0x00000000`, `attributes/current_power_mode=0x00000011`
and `qcom/power_mode`. The only differing reading is `qcom/clk_status`
(0 against 1), which is a live clock status, not a policy.

The **UFS policy** is therefore not a candidate for the standby difference.
The row's original gap, "actual selected low-power link/clock state is not
proven by source alone", remains open in its **state** form: a plugged awake
policy read is not a sleep observation, and the actual link and PHY state
during a qualified sleep interval is still unproven.

The same session produced the first concrete instance of the always-on
class: `vdd_boost_vreg` reads `use=1`, `open=1`, single `deviceless`
consumer, that is enabled by its own `regulator-always-on` declaration and
emits no transition at all. It is the rail class the transition comparisons
structurally cannot see.
