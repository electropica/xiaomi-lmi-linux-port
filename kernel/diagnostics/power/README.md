# Power diagnostics and decision summary

## Current decision summary — 2026-10-09

The test handset is temporarily running official LineageOS
23.2-20261007-NIGHTLY-lmi (Android 16), not the Mobian RPMh diagnostic boot.
Repeated peripheral-isolation trials are historical evidence, not a checklist
to rerun. The longer Android idle interval is complete; its gauge limitations are
recorded below. No battery-health verdict follows from this comparison.

| Evidence group | Observed result | Decision |
| --- | --- | --- |
| Mobian deep idle | Several short trials around 89–95 mA; long returns show substantial discharge despite extensive deep suspend. | The idle-drain problem is real; deep suspend alone does not resolve it. |
| Wi-Fi isolation | About 93.1 mA radio-off versus 94.8 mA in an adjacent enabled trial. | Wi-Fi is not demonstrated as the sole cause; do not repeat the same pair without a new hypothesis. |
| NFC isolation | VEN-low 88.8 mA versus VEN-high 90.3 mA in one adjacent pair. | NFC enable alone does not explain the residual load. |
| CPU, ADSP and RPMh | Short trials show extensive APSS/ADSP sleep and zero final reviewed CX/MX/XO votes. | Do not assume a permanently awake CPU or cut shared power rails from awake snapshots. |
| Gauge identity | Retained 416-byte profile matches the expected profile; learned full is about 2,820 mAh on both systems versus 4,700 mAh nominal. | Profile mismatch was not observed. Learned capacity is not an independent cell-health measurement. |
| Manual-off comparisons | Charging/boot timing or a missing departure sample prevented a valid baseline pair. | No off-state drain or physical health conclusion; no need to repeat a flawed protocol. |
| First LineageOS idle interval | Displayed level stayed at 79%; battery history records about 2 mAh loss over 7 min 05 s before charging. | Preliminary evidence, supported by the longer interval below; not a cell-health test. |
| Longer LineageOS idle interval | 29 min 41 s on battery; displayed 83% unchanged before reconnect; Android reports 5.35 mAh summed gauge decreases (~10.8 mA by that accounting). | Lower apparent idle drain is supported, but an upward gauge correction prevents a reliable net endpoint-current estimate. |
| Overnight LineageOS idle interval | 8 h 37 min on battery, 100% to 91% before charging, same boot and radios off; roughly 33 mA by gauge accounting, about 99.5% system suspend. | Lower apparent drain than the historical Mobian trials is supported; gauge corrections and different trials prevent a calibrated current ratio or battery-health verdict. |
| Daytime LineageOS idle interval | 13 h 29 min, 100% to 94% before charging, same boot and radios off; 150 mAh net gauge loss (~11.1 mA), Android counts 188 mAh decreases (~13.9 mA); about 99.62% system suspend. | Confirms substantially lower apparent idle drain in another long Android interval; upward corrections and different measurement conditions prohibit a calibrated current ratio or cell-health verdict. |

The first Android baseline was recorded after unplug, with airplane mode enabled
and Wi-Fi/Bluetooth settings disabled. A finite phone-local sampler saved one
departure read and turned the screen off, then exited; no periodic measurement
logger was left running. Radio settings were restored after retrieval.

The direct return read had already resumed charging: Android classified it as
AC powered even though USB powered was false. Its counter increased and cannot
provide a discharge-current estimate. All external-power flags and charging
status must therefore be checked, not just the USB flag. The offline interpreter
under `userspace/power/diagnostics/` now rejects charging endpoints and increasing
counters; its host fixtures cover this observed AC/USB distinction.

The battery-history interval starts at a discharging, plug-none event with
2,099 mAh and ends at a not-charging reconnect event with 2,097 mAh, preceding
the plug-AC and charging events. The roughly 17 mA quotient uses whole-mAh
history values: endpoint quantization alone gives a rough 8–25 mA range.
Temperature fell from 26.2 to 24.2 C. This is not calibrated physical current,
a stable Android autonomy measurement or proof that the original cell is healthy.
It makes a battery-only explanation less compelling; battery aging and software
load may coexist. The initial Android installation includes Google applications,
so it must not be described as a bare installation without background services.

Keep one decision summary here and retain the detailed dated evidence below for
traceability. Do not generate another kernel version or repeat the full trial
series merely to reproduce the same result. Raw samples, application/process
history and device identifiers remain private.

### Longer Android idle result

The second trial started at 19:30:46 local handset time and ended at 20:00:27,
with airplane mode enabled and Wi-Fi/Bluetooth disabled. The finite baseline
sampler confirmed every external-power flag false and status discharging,
saved one reading, switched the screen off and exited. No periodic diagnostic
logger, media playback or acquisition ran during the interval.

Android's statistics were reset at this departure and report 1,780.981 seconds
on battery, including 1,770.523 seconds screen-off and 26.582 seconds uptime.
Realtime minus uptime gives approximately 98.5% system-suspend occupancy in
this accounting; it is not a measurement of every peripheral power domain.
Displayed level was 83% throughout the pre-charge history. The first host read
was already charging at 84% and is excluded from discharge-current estimates.

The charge gauge is not monotonic: rounded history fell from about 2,207 mAh
to 2,204 mAh, then rose to 2,210 mAh with a `batt-temp-delta` wake event before
ending near 2,209 mAh. Battery temperature fell from about 24 to 20.7 C.
Coincidence with this event does not establish the gauge correction's cause.
Negative endpoint loss must not be presented as zero drain or self-charging.

Android reports 5.35 mAh discharge, all screen-off, including 4.30 mAh assigned
to device deep doze. Its [upstream LineageOS 23.2 implementation](https://github.com/LineageOS/android_frameworks_base/blob/lineage-23.2/services/core/java/com/android/server/power/stats/BatteryStatsImpl.java)
sums downward charge-counter changes while ignoring increases. The quotient
is about 10.8 mA, an Android gauge-accounting estimate rather than independent
physical current. The source was reviewed to interpret the field, not proven
bit-identical to the running framework. The estimated per-component power
table reports computed drain zero here and cannot identify physical service
consumption.

The learned full capacity remains 2,820 mAh versus 4,700 mAh nominal. The idle
comparison supports a Mobian-specific load/policy difference worth pursuing,
without proving the original cell healthy or quantifying a net-current ratio.
Bluetooth and Wi-Fi settings were restored; no reboot or new kernel was needed.
Bounded battery/power/device-idle/thermal readings were retained privately.
Restricted suspend-service/logcat reads returned no usable detail; no root
access or security-setting change was attempted. The one-shot reminder is paused.

### Completed Android overnight result — 2026-10-09

The operator confirmed unplugging around 21:27 local time on October 8.
Battery history records discharge from 21:27:07.537 to the explicit
not-charging pre-plug event at 06:04:12.110 on October 9: 31,024.573 seconds
(8 h 37 min 04.573 s). The displayed level fell from 100% to 91% before
external power. Airplane mode was enabled, Wi-Fi and Bluetooth settings were
disabled, and the screen was on for about ten seconds at departure before
being switched off. No media test or periodic diagnostic logger ran overnight.

The finite sampler's completion marker was recovered. Departure and return
boot identifiers match, so no intervening reboot is indicated. The first host
return read was already AC-powered and charging; its raw counter is excluded
from a direct discharge calculation. The original radio flags were restored
and verified after the first read and history retrieval.

Rounded pre-charge history falls from 2,805 to 2,522 mAh, a net 283 mAh or
approximately 32.8 mA over the history interval. The gauge is not monotonic:
it has upward corrections of 3 and 4 mAh, with 290 mAh of summed rounded
decreases. Android separately reports 289 mAh discharge (about 33.5 mA by its
sum-of-decreases accounting), including 275 mAh assigned to deep doze. These
are related gauge estimates, not independent electrical measurements. The
earlier short trial's roughly 10.8 mA accounting must not be extrapolated to
this full night.

Android reports 31,024.572 seconds on battery and 143.212 seconds uptime,
approximately 99.54% system-suspend occupancy. Screen-off duration is
31,014.073 seconds. The composite sampler file's clock/uptime was captured
later than its battery snapshot and gives a shorter interval (about 8 h 35 min
to first host return); use the matching history/on-battery-statistics duration
above rather than treating its fields as an atomic snapshot. Battery temperature
fell from 21.2 C in departure history to 16.7 C at the charging return; learned
full remained 2,813 mAh versus 4,700 mAh nominal.

The result supports lower apparent idle drain under LineageOS than the
historical roughly 89–95 mA Mobian trials. It is not a controlled physical-current
ratio, proof of a healthy original cell or identification of a particular faulty
Mobian peripheral. Aging and a Mobian policy/integration problem may coexist.
No additional kernel, calibration reset or package installation was needed.
Detailed history, identifiers and raw readings remain private.

### Overnight discharge is not uniform

The October 8–9 history has a strongly front-loaded charge-counter decline.
Segments use actual samples nearest each hourly boundary, without interpolation:

| Segment | Net rounded counter decrease |
| --- | ---: |
| First hour | 146 mAh |
| Second hour | 55 mAh |
| Third hour | 26 mAh |
| Fourth hour | 14 mAh |
| Fifth and sixth hours | 11 mAh each |
| Seventh and eighth hours | 9 mAh each |
| Final approximately 37 minutes | 2 mAh |

The first two hours account for 201 of the net 283 mAh, about 71%.
The remaining 6 h 37 min account for 82 mAh, a net gauge quotient of about
12.4 mA. The full-night roughly 33 mA quotient therefore does not describe a
uniform idle load. Positive corrections of 3 and 4 mAh remain included;
neither the late slope nor these segments are calibrated physical current.
Extensive suspend also occurs during the early decline. Awake time alone
does not explain its shape, and the observation does not identify its cause.

The pinned kernel's
[`fg_gen4_get_charge_counter`](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/71b13e62f057a649b77fe4062feb73ee72ad609c/drivers/power/supply/qcom/qpnp-fg-gen4.c#L793)
scales `FG_SRAM_CC_SOC_SW` by learned full capacity. Its software counter can
be primed from battery SOC through the
[capacity-learning logic](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/71b13e62f057a649b77fe4062feb73ee72ad609c/drivers/power/supply/qcom/fg-alg.c#L675).
Thus this reported counter is not an independent, immutable physical-energy
measurement. No runtime trace proves that priming caused this night's early
decline; no calibration, SRAM write or learning reset has been performed.

Ordinary Android shell access also exposes read-only `cmd battery get
current_now`. A plugged, charging read succeeded, but it is not an idle-current
result. Future readings must retain timestamps, power status and measurement
conditions; `current_average` returned zero and is not treated as a validated
standby average. Battery-state simulation commands are not used.

### Completed Android daytime result — 2026-10-09

The operator extended the intended ten-hour test to approximately fourteen
hours. History establishes the actual discharge interval from 06:30:37.407
to the explicit pre-charge reconnect event at 19:59:39.564: 48,542.157 seconds,
or 13 h 29 min 02.157 s. The same boot remained active. Departure radios were
airplane enabled, Wi-Fi and Bluetooth disabled; the returned settings still
matched, and the original settings were then restored and verified.
The finite sampler's saved-baseline/exit marker was recovered. No periodic
diagnostic logger or media acquisition ran during the interval.

Displayed level changed from 100% to 94% before charging. Rounded history
counter changed from 2,626 to 2,476 mAh: 150 mAh net, approximately 11.1 mA
as a gauge quotient. Five positive corrections total 39 mAh; summed rounded
decreases total 189 mAh. Android separately counts 188 mAh discharge,
approximately 13.9 mA by its sum-of-decreases accounting, including 184 mAh
in deep doze. The first host return read was already charging and is excluded
from a direct discharge-endpoint calculation. These are gauge-based estimates,
not independently measured physical currents.

The first two roughly hourly segments lose 45 and 18 mAh, compared with
146 and 55 mAh in the preceding night. Thus that night's initial large decline
is not reproduced at the same magnitude. Corrections produce two later
negative-net segments; these must not be called self-charging or zero load.
Both trials display 100% at departure but have different counters, temperatures
and charging histories. A controlled physical-current ratio is not established.

Android reports 48,542.132 seconds on battery and 183.892 seconds uptime:
approximately 99.62% system-suspend occupancy. Screen-off time is
48,531.649 seconds. Departure temperature was 17.7 C; the first charging
return reports 16.7 C. Learned full remains 2,813 mAh versus 4,700 mAh nominal.
Composite sampler clock/uptime again occurs later than its battery/history
departure; use the matching history and Android-statistics interval above.

This second long Android trial reinforces a Mobian integration/runtime-policy
investigation rather than a battery-only explanation. It does not establish
cell health, identify a peripheral responsible for Mobian drain or validate
an autonomy fix. Reuse the existing Mobian kernel; inspect runtime ownership
and supply votes before a new targeted isolation trial. No new build, firmware,
calibration reset or Android security change was performed. Raw logs remain
private.

### Existing kernel configuration comparison

The embedded IKCONFIG payloads were extracted from the already downloaded
LineageOS boot and the existing reviewed RPMh boot, without building or booting
another image. Their decompressed LF-byte SHA-256 values are respectively
`6c168341dfa9987656c6f738dbd8e4a58a72a0381a3c0cdf072a5a3a7fba3a90` and
`c6da6e71cc7418f36997325ff5d72693d9861945cc4999b6be9661a150451e78`.
Both enable PM, suspend, CPU idle, CPU frequency, ARM cpuidle and QCOM RPMh;
both use `CONFIG_HZ=250` and preemption. This does not support a simple
missing-suspend-configuration explanation for Mobian's higher observed drain.

Differences include Mobian's UART Bluetooth/RNDIS support and debugfs/idle
statistics, and Android's SELinux/LTO/hardening configuration. These are leads,
not demonstrated power causes. The configurations do not prove identical
kernel source, device trees, firmware behavior or runtime power policy. Do not
disable security or rebuild a kernel based on this comparison alone.

### Current Android source comparison

The running Android release contains the source suffix `g71b13e62f057`.
The [official common-device dependency](https://github.com/LineageOS/android_device_xiaomi_sm8250-common/blob/lineage-23.2/lineage.dependencies)
names `android_kernel_xiaomi_sm8250`; the prefix resolves there to
[`71b13e62f057a649b77fe4062feb73ee72ad609c`](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/commit/71b13e62f057a649b77fe4062feb73ee72ad609c).
Three complete files at that commit are byte-identical to the preserved
`a5b3099017ae` Mobian source base:

| File | SHA-256 on both sides |
| --- | --- |
| `drivers/power/supply/qcom/qpnp-fg-gen4.c` | `0f5676829cb2a40daa191a456998c700d744afe8346e07dd3c7af2a7e8685957` |
| `drivers/cpuidle/lpm-levels.c` | `0899a58cc28945431fddd68c914b187719f99f2d49f831132382cd7401679aa3` |
| `drivers/bluetooth/bluetooth-power.c` | `8bb4375cbea588d52a3d39e936bfcd9bfedb1e1f5379da0039d9a9acb47c515b` |

Three further gauge-support files were subsequently compared at the same
pinned commit and are also byte-identical:

| File | SHA-256 on both sides |
| --- | --- |
| `drivers/power/supply/qcom/fg-alg.c` | `436db2892f19c0055bcb1f21916bbfe3bbcdb9429db694aad0cabbb4c79166f1` |
| `drivers/power/supply/qcom/fg-util.c` | `c969590d0f30c2746a725497969eb49cad9a951e2426b1753b670c2bf7f94837` |
| `drivers/power/supply/qcom/fg-memif.c` | `6eb7626265aa2bfa8b7a85a3c2e175d79500d7f5fea10464cad92de641488526` |

This is source-file evidence, not binary equivalence or proof that every
dependent function, device tree, patch, firmware and runtime setting matches.
It offers no new gauge/suspend-driver fix to transplant from this commit.
The existing Mobian boot was not rebuilt or replaced.

The common Bluetooth power driver has two distinct software state caches:
rfkill's `previous` and the power ioctl's `pwr_state`. Initial soft blocking sets
`previous=true`; the rfkill callback calls hardware power control only when
that cache changes. The power ioctl tracks its own state. Therefore the earlier
observation that Bluetooth was soft-blocked is not, on its own, a measurement
that its physical supplies/GPIOs were off. This is an untested integration lead,
not proof of a Bluetooth fault or instruction to force a GPIO/ioctl.

Before any Bluetooth isolation trial on a restored Mobian runtime, inspect
its existing reset/enable GPIO state and named supply consumer votes, reconcile
them with rfkill/HCI ownership, and retain the original state for restoration.
Do not repeat the existing Wi-Fi/NFC trials, unbind shared hardware or stop the
working audio DSP solely on the basis of this source comparison.

The package's QCA6390 Bluetooth bindings provide concrete read targets for
that later investigation: TLMM reset line 21 and software-control line 124,
with supplies AON=`pm8150_s6`, RFA1=`pm8150_s5`, RFA2=`pm8150a_s8` and
ASD=`pm8150_l16`. The digital supply is `pm8150_s6` in entries
0/1/2/4/5/6/8/9 and `pm8009_s2` in entries 3/7/10/11. GPIO numbers are
controller-local binding cells, not assumed Linux global GPIO numbers.
Resolve the active runtime binding and regulator consumers first; package
variants are not a reason to manipulate either supply directly. The driver's
off path drives its reset low, whereas software-control is configured as an
input during power-on; it is not a second independent enable output.

### Android package overlays and startup policy

Memory-only inspection of the official October 7 LineageOS archive's DTBO
table found twelve entries. Every entry declares `vdd_boost_vreg` always-on;
`vdd_hap_boost` is not always-on, and both refer to PM8150B GPIO 5. Entries
0 and 11 have SHA-256 values
`524d131cb916a73bb5a44aa44c18faae89af14a51cfc9ae6145c3b16a131f571` and
`ebef7c8ecdc14fe096e69d2c6d570edae681c48462c74e715e0fc8a9734022a6`,
matching the two previously recorded OEM-style entries in the
[boost review](../../../docs/validation/lmi-boost-diagnostic-candidate-2026-10-06.md).
The archive SHA-256 is
`c182c6f8ed1ccb1821be38e764e189f3d58f65dd9bea8aa21f1381c791395a29`.
No image was extracted to disk, flashed or modified for this comparison.

The always-on declaration is therefore not exclusive to the Mobian test
environment. This narrows the hypothesis; it does not establish the selected
merged runtime tree, actual GPIO state, rail current or complete equivalence
of every overlay. It does not justify forcing the shared boost GPIO off.

Read-only inspection of Android's installed `init.qcom.power.rc` shows UFS
clock scaling/gating disabled during `on init`, then enabled in the
`sys.boot_completed=1` block and charger mode. The init block also requests
`sleep_disabled=1`; `enable-low-power` requests Power HAL initialization.
These are startup instructions, not measured steady-state values. The current
boot reports `sys.boot_completed=1`, but the Power HAL initialization property
was empty and reading the sleep parameter was denied. The system init file
imports the vendor hardware init file using `ro.hardware=qcom`, and that file
imports the inspected power file. This establishes an import chain, not success
of individual writes or the final runtime value. Do not infer disabled
runtime sleep from the isolated init write or assume every instruction succeeded.
The completed Android trial's suspend accounting remains the observed evidence.

Installed init files expose permissions for UFS auto-hibernation and Bluetooth
rfkill, but no `rpm_lvl`/`spm_lvl` assignment was found in the five inspected
files. The post-boot script and actual UFS power-level attributes were denied
to the ordinary ADB shell. Their runtime values remain unknown; no Android
root/security setting or Mobian policy was changed to obtain them.

### Existing storage and USB source comparison

At the same pinned Android kernel commit, five further complete source files
are byte-identical to the preserved Mobian base:

| File | SHA-256 on both sides |
| --- | --- |
| `drivers/scsi/ufs/ufshcd.c` | `cc3b00465c2cf0f096521d010150fb87b248119670fe8ed259eea4e56f38594e` |
| `drivers/scsi/ufs/ufs-qcom.c` | `5914361ac55598d1e2ffb6105bbe161d93536aba7144310cc67cb94d400ac739` |
| `drivers/usb/dwc3/core.c` | `c1315c8af7cb8b0f8efb2df5d51c5169f63257621840b8b40bea688e67a3f6ab` |
| `drivers/usb/phy/phy-msm-ssusb-qmp.c` | `692f6cfb62866b928eb5e305fa478570ab8561eec21615963081a2bae167c34e` |
| `drivers/usb/phy/phy-msm-qusb.c` | `b89ed9c718c8c0c9bd83b98e1057005fe52d89f9bee2791095ce8bff689653db` |

The sixth file, `drivers/usb/dwc3/dwc3-msm.c`, differs only in
`dwc3_otg_start_host`: the Mobian base checks `IS_ERR(vbus_reg)` before
comparing `PTR_ERR(vbus_reg)` with `-EPROBE_DEFER`; the Android source omits
the first guard. The reviewed delta is in host-mode regulator acquisition,
not an altered suspend/resume implementation. It supplies no demonstrated
idle-drain fix to transplant. These comparisons cover the named source files,
not every compiled dependency, local patch or device-tree property.

The common UFS core selects device SLEEP plus link Hibern8 when the runtime
or system power level is not already valid. That fallback matches the states
represented by Mobian's previously observed level 3; it does not prove which
level Android selected or whether either system physically reaches it in every
trial. Android's protected runtime attributes remain unreadable. No lower-level
storage power policy, USB driver or kernel was changed from this comparison.

The RPMh command layer, resource-state controller, RPMh regulator provider
and GDSC power-domain implementation also match byte for byte at the pinned
commit:

| File | SHA-256 on both sides |
| --- | --- |
| `drivers/soc/qcom/rpmh.c` | `a6921d6e2f2a13aef6206228c8b2703c852f163171c15576c4a82411e85f75ed` |
| `drivers/soc/qcom/rpmh-rsc.c` | `b37f390dbe93903c4a7884e605b76b507134c09d33a147d0c34648f1efd83cc0` |
| `drivers/regulator/qcom-rpmh-regulator.c` | `856e7515d860f15482b4246dda69cc2953ef19e99488879e71b3e542f078ad8c` |
| `drivers/clk/qcom/gdsc.c` | `be0de8d6e48bd6b4eb459821767c764ad9edb14e34a26ebc5429aa471752b8bc` |

Across the thirteen selected files reviewed so far, twelve are identical and
the remaining USB delta is the host-mode error guard described above. This is
a targeted comparison, not a complete kernel audit. It supplies no demonstrated
power fix from these implementations and does not exclude differences elsewhere
in the kernel or in compiled patches. The next Mobian investigation should
prioritize actual peripheral enable/supply states and their userspace ownership,
starting with the unproven Bluetooth-off state, rather than another rebuild of
these unchanged implementations. It requires a restored Mobian runtime; Android
cannot validate that runtime's GPIO/consumer state on its behalf.

### Xiaomi post-boot policy and profile follow-up

The same official archive contains one `j11sun_4700mah` profile, in DTBO
entry 7. Its 416-byte payload SHA-256 is
`583d77b61a7723fe4f40990eafa42c6283a87c41ba39a69ad2be77ce70f16050`,
identical to the retained profile read on Mobian before the OS switch.
This does not identify Android's current retained SRAM contents or independently
measure battery health, but provides no different package profile to explain
the idle comparison. No profile or calibration was written.

The [official common-device post-boot script](https://github.com/LineageOS/android_device_xiaomi_sm8250-common/blob/da4ba935256abcc07973fb17d6b7729058fc9f9b/rootdir/bin/init.qcom.post_boot.sh)
has a Kona-specific branch that requests `sleep_disabled=N`, alongside CPU and
memory-bus governor tuning. Its companion power init file matches the installed
file's normalized text. The post-boot script itself was not readable on the
handset, so this is pinned source-policy evidence, not confirmation of every
deployed write. It explains why the earlier init request of `1` must not be
treated as the final intended policy. Mobian already used `N` in the completed
diagnostic trials; copying that request again is not a new residual-drain fix.

The reviewed common-device `powerhint.json` also defines interaction, audio,
camera and performance hints. Its active deployment was not established and
its Android framework-specific hints must not be copied wholesale into Mobian.
The lmi variant initializer selects device identity rather than adding a separate
power implementation. These sources supply comparison targets, not a validated
replacement Linux userspace power manager.

The tracked Mobian ADSP/BTFM startup unit is a guarded one-shot, not a periodic
poller, and BTFM readiness alone does not establish QCA6390 HCI power-off.
No explicit rfkill/BT attach or `/dev/btpower` control was found in the tracked
userspace scripts. Earlier experimental attach results and externally retained
tools must be reconciled with the restored live runtime before any isolation.

### Overnight protocol and completion

The finite LineageOS overnight trial completed on October 9, using the same
airplane, Wi-Fi-off and Bluetooth-off settings as the longer daytime trial.
Both arm and return actions succeeded; the sampler's saved baseline and exit
marker were recovered. The result and timing limits are recorded above.

The opt-in [Windows host helper](../../../userspace/power/diagnostics/android-idle-trial.py)
and [finite baseline sampler](../../../userspace/power/diagnostics/android-idle-baseline.sh)
preserve the trial ID, original radio settings, boot ID, uptime, local device
clock and battery-service fields in private files. The host helper requires
explicit `--adb`, `--output` and `--trial-id` arguments. Its `arm` action must
run only after the operator is ready to unplug; it requires external power and
validates the requested radio state before starting the sampler. Do not arm
hours in advance or invoke it as an unattended schedule.

The sampler waits at most 15 minutes while plugged in, then confirms all four
external-power flags are false and status is discharging, settles for ten
seconds, saves one baseline, switches the screen off and exits. If it fails,
it requests restoration of the original radios; their state must be checked
at return. No periodic overnight diagnostic logger remains running.

After the operator confirms reconnection, `return` preserves the first reading
before collecting baseline, history and Android statistics, and restores the
recorded radio settings even if later retrieval fails. It rejects reused output
and unsafe trial IDs. A boot-ID change invalidates a same-boot comparison;
charge-counter increases, temperature changes, Android statistic resets and
charging at return must still be handled explicitly in analysis. Displayed
percentage alone cannot diagnose cell health.

Host guards and shell syntax checks pass. The unified helper's first overnight
arm, baseline completion and return retrieval now have hardware evidence,
including verified radio restoration. Its composite baseline fields are not
atomic, as the overnight timing observation above makes explicit.
It is neither an installed image service nor a power-saving fix. Private trial
outputs, identifiers and detailed histories must stay outside Git.

## Historical debugfs candidate design

The historical D-repro configuration disables `CONFIG_DEBUG_FS`, preventing
inspection of downstream clock and regulator debug summaries. The preparer
creates a private reset-GPIO diagnostic boot recipe without changing the canonical
locked configuration or either canonical audio constructor. Historical source
patches, audio instrumentation and functional reset-GPIO correction are retained.
No boost/GPIO, regulator policy, gauge calibration or thermal setting is changed.

## Reviewed Kconfig delta

The [config patch](power-debugfs-config.patch) enables debugfs. In this source,
`MSM_PM` selects `MSM_IDLE_STATS` when debugfs is enabled; therefore the candidate
also enables Qualcomm idle statistics with the four existing default bucket
values. Other newly visible optional debug features, including block and
Bluetooth debugfs, are explicitly disabled. Existing functional options stay
unchanged. Enabling idle statistics may add observation overhead; this is a
diagnostic kernel, not a claimed power-saving change.

The preparer verifies the original constructor/config and reviewed delta hashes,
refuses an existing generation directory and retains original input/toolchain
checks. The derived builder still requires byte-identical configuration after
`olddefconfig`. Unexpected changes stop the check rather than relaxing its gates.

Debugfs exposes writable controls: enabling it is not a read-only security
boundary. The intended protocol reads only `clk/clk_summary` and
`regulator/regulator_summary`, with no writes to debugfs controls. Source review
found that clock summary traversal takes transient bus votes when the clock
provider implements them; regulator summary reads voltage/current information.
Snapshots can affect measured state and awake snapshots after resume do not prove
domain residency during deep suspend. Compare diagnostic and original boots
under the same conditions before interpreting current.

## Manual stages

Prepare a new private directory; this stage writes text files only.

?? WSL / Linux ? ??? Prepare only ? suggested model: GPT-6 Luna high

```sh
python3 kernel/diagnostics/power/prepare-debugfs-variant.py \
  --output-directory "$PWD/kernel/diagnostics/audio/state-power-debugfs-reviewed"
```

Use external inputs and the native Alpine toolchain described in the
[existing audio recipe](../audio/README.md). Set `AUDIO_DIAG_ROOT` to the generated
directory and `AUDIO_DIAG_PROJECT_ROOT` to the canonical repository root; set
input/source/tool paths explicitly. Invoke the generated reset-GPIO constructor
first with `--preflight`, then `--check-only`. The latter compiles only Kconfig
host utilities/probes, not a kernel. A heavy build without an option is a
separate manual user operation after those checks pass. It produces
`D-repro-01-power-debugfs-reset-gpio-diagnostic-boot.img`, preserving the ramdisk
and boot metadata. The candidate must not replace the durable boot. No flash or
phone operation is included.

## Validation - 2026-10-06

Initial generation passed exact one-symbol delta, Bash syntax, reset-variant
transformation anchors, preserved output/config gates and overwrite refusal.
External-input preflight then passed all checks, including strict sequential
patch application. Native dynamic/static toolchain probes passed, but initial
`olddefconfig` rejected the one-symbol configuration because newly visible defaults
changed it. The reviewed config patch includes the obligatory Qualcomm statistics
and disables optional Bluetooth/block defaults. Its candidate SHA-256 is
`c6da6e71cc7418f36997325ff5d72693d9861945cc4999b6be9661a150451e78`.
The second native check passed both link probes and byte-identical
`olddefconfig` validation. The later manual build completed successfully; see below. Hardware boot
validation remains pending.


## Manual build - 2026-10-06

The operator ran the heavy build. Both inner and wrapper states are COMPLETE;
post-olddefconfig configuration is byte-identical to the reviewed candidate.
The repacked ramdisk matches the original and the repacked DTB matches the
reset-GPIO-corrected DTB. The resulting temporary diagnostic boot has size
54,652,928 bytes and SHA-256
`147258b2df751cbcdb3c0cb2a10d10f2b0bcacaeee1fe13fdf3bdc79e71e06b0`.
A separate Windows Downloads copy was verified with the same hash. Neither
binary nor raw build logs are tracked. No boot, flash or hardware validation
has occurred yet; a successful build does not establish power improvement.


## Hardware startup - 2026-10-06

After the operator's temporary boot and USB reconnect, SSH reported
`4.19.325-cip128-st12-perf-ga5b3099017ae-dirty`, build timestamp
October 6 16:41:37 UTC. The live IKCONFIG SHA-256 matches the reviewed candidate
`c6da6e71cc7418f36997325ff5d72693d9861945cc4999b6be9661a150451e78`.
Debugfs is mounted and both clock/regulator summaries are readable.
CPU idle remains `sleep_disabled=N`; UPower and the existing CPU-idle opt-in
service are active. Initial state was USB online, 97% charging, 27 C.
The anticipated `/proc/msm_pm_stats` interface is absent, but debugfs
`lpm_stats` is present. Interface names alone are not proof of counters' validity.

An awake, USB-connected snapshot shows zero camera/GPU regulator use counts,
active primary USB and PCIe-0 domain use counts, and the known always-on boost.
These are software use counts under connected conditions, not direct power
measurements or residency during suspend. No regulator/clock debugfs control
was written. A separate bounded unplug/suspend observation is being prepared;
no consumption improvement or diagnostic-kernel long-run validation is claimed.


## First bounded suspend trial - 2026-10-06

A private, 180-second derivative of the existing gauge trial retained USB-off,
settled USB runtime status, capacity, input-quiet and logind-inhibitor checks.
It requested one initial suspend and disabled the gauge re-suspend branch for
this observation. An owned RTC end alarm was cleared on completion; the
transient service finished successfully and is inactive. No debugfs control,
radio or charge policy was changed. Camera and microphone were not opened.

The observed interval was 181.821441 boottime seconds and 0.675646 monotonic
seconds, implying approximately 181.145795 seconds suspended. The newly
available `lpm_stats/suspend` independently reported one successful L3 suspend
lasting 181.169277 seconds. USB stayed offline at both sample endpoints.
The gauge charge-counter decrease was 4,868 uAh, approximately 96.38 mA over
the interval; instantaneous samples were 104.98 mA before initial suspend and
95.703 mA at completion. This short gauge-derived estimate is not an independent
current measurement or a controlled cross-boot comparison. No improvement is
established against the previous approximately 94-97 mA observations.

Before initial suspend, software use counts for primary USB and its PHY had
fallen to zero. PCIe-0, the known always-on boost and several shared storage/radio
rails retained positive use counts. Camera/GPU regulator use counts were zero
in that pre-suspend snapshot. Post-resume snapshots can include display/GPU
activity and must not be described as deep-suspend residency. These summaries
identify consumers/votes, not actual current in individual rails; PCIe DRV
firmware ownership is especially relevant when interpreting a retained vote.
The directory `lpm_stats` cannot be read as a scalar file: future collection
must read its specific read-only `suspend`/`stats` children, with compact parsed
output. Raw logs remain private. After operator reconnection, status was
Charging with USB online and no remaining RTC alarm.


## Read-only consumer follow-up - 2026-10-06

Wi-Fi runtime diagnostics report SUSPENDED, PM usage count zero,
prevent_suspend_cnt zero, 1,663 runtime_get and 1,663 runtime_put, and zero
suspend/runtime_get errors at the inspected instant. The radio interface was
unassociated. This does not establish minimum radio power throughout the trial,
but no outstanding host runtime-PM reference was found.

Source `drivers/pci/controller/pci-msm.c:msm_pcie_drv_suspend` delegates link
management through RPMsg, disables non-suppressible clocks and removes PCIe
vreg/bandwidth votes. It does not take the same GDSC-off path as ordinary
suspend. A retained PCIe GDSC use count under DRV therefore is not sufficient
proof of failed sleep. CNSS `DISABLE_DRV` is enum bit 9 and is read from the
control-params mask, but its debug control is unavailable because
`CONFIG_CNSS2_DEBUG=n`. No quirk mask, PCIe config or driver binding was changed.
Do not imitate a missing control with direct register/GPIO writes.

UFS reported runtime suspended with `power/control=auto`, clock gating enabled
and a 50 ms gating delay. Runtime/system PM levels are both 3: in this source
that means device SLEEP plus link HIBERN8, rather than device POWERDOWN/link OFF.
Its controller snapshot showed no outstanding requests/tasks or recorded UIC/
lane/data-link errors. The live DT contains neither rpm-level nor spm-level,
so the driver's defaults apply. None of the 12 inspected OEM-style overlays
contains those properties; the uninspected OEM base DT prevents claiming full
OEM equivalence. No storage power level was changed.

The TFA9874 debug state is Stopped and firmware state Ok. Uncached regmap reads
(`REGCACHE_NONE` in this driver) found control 0x00=0x0011: PWDN=1, AMPE=0,
DCA configuration=1. Status reads found SWS=0, AMPS=0, CLKS=0, MANSTATE=0 and
DCMODE=0. A configured DCA bit is not evidence that the converter is running.
These awake idle snapshots corroborate an amplifier in powerdown; they do not
measure current in the external always-on boost supply. Only debug reads were
performed, with no sound, microphone capture, reset or register writes.

The residual current is still unexplained. Retained shared supply use counts,
static DDR residency fields and subsystem ONLINE/OFFLINING labels must not be
turned into a hardware-fault diagnosis without meaningful residency/current
measurements. No new power fix or production integration is claimed.


## DDR observation limits and next isolation step

Source review of `drivers/soc/qcom/ddr_stats.c:ddr_stats_show` confirms that it
maps the configured shared-memory table, validates its magic/count and reads
entries; it sends no refresh request to firmware. The observed residency table
sums to about 19.6 seconds even though an independently measured suspend alone
lasted 181 seconds. It therefore is not a complete live residency record for
this experiment. Static low-power counters must not be treated as evidence
that DDR failed to sleep. The firmware table's update policy remains unknown.

If the operator is available, a longer fully powered-off, unplugged interval
can test whether similar reported charge loss persists without Mobian running.
Record pre-shutdown and earliest post-startup gauge data and exact elapsed time,
and account for shutdown/startup consumption, gauge state changes and any USB
charging before comparing. A percentage-only off/on comparison is not independent
current measurement and cannot alone assign a hardware or kernel fault. No
shutdown is scheduled or performed without the operator's readiness.


## Invalidated trace trial - 2026-10-06

The second short unplugged test slept for only 4.122 seconds of a 180.135-second
interval (176.013 seconds awake). The first observed resume reason was IRQ 311,
`pon_kpdpwr_status`, the power-key status interrupt. The operator observed that
the display remained on. This identifies the reported wake source, without
establishing whether a deliberate press or an electrical event caused it.
The resulting approximately 150.37 mA gauge estimate is not a suspend-current
measurement and must not be compared with the previous deep-sleep result as a
power regression.

The trace retained 18,960 of 53,783 written entries, with 34,823 overwritten
entries across three CPU buffers. The initial suspend phases were lost; no
conclusion about rail or clock shutdown during deep sleep follows from this
trace. The transient service finished successfully, its private trace instance
was removed, the owned RTC alarm was cleared, and Charging resumed after USB
reconnection. Raw trace and gauge logs remain private.

The next bounded diagnostic removes high-volume RPMh and regulator-voltage
events, uses 512 KiB per CPU, and stops on a wake occurring more than two seconds
before the planned endpoint. The collector requests initial suspend itself;
the operator should unplug without pressing the power key or touching the
screen. This is a protocol correction, not a production power fix. Preparation
passed Python syntax checks; the following trial validates the revised protocol.


## Complete suspend trace - 2026-10-06

The revised three-minute unplugged trial completed with 181.262 seconds asleep
and 0.678 seconds awake over 181.940 seconds, approximately 99.63% suspended.
Qualcomm L3 suspend statistics independently increased by one success and
181.281 seconds. The wake reason was the planned RTC alarm (IRQ 323), with no
early-wake abort. The gauge-derived interval estimate was 95.63 mA, consistent
with the earlier approximately 96.4 mA result; a short same-gauge estimate does
not establish improved autonomy or independent current accuracy.

All 11,704 trace entries were retained, with zero per-CPU overruns and dropped
events. The initial marker, suspend phases and final marker are present. Trace
timestamps stop advancing across machine suspend in this capture; use the
boottime-minus-monotonic difference and L3 counters for sleep duration instead
of subtracting the identical machine-suspend trace timestamps.

Before machine suspend, the last observed transitions for the PCIe, display and
UFS clocks were disable-complete events. Display panel VCI, PM8150 L14, UFS PHY
GDSC and its L9/L17 supplies also had disable-complete events. No nonzero
device-PM callback result was found. These events confirm driver transitions,
not the physical current or voltage of every rail. Firmware-owned PCIe power,
shared supplies and external boost current remain unresolved; no hardware
power-policy change is justified by this trace alone.

The transient service is inactive with Result=success, its private trace instance
is removed and its owned RTC alarm is empty. Battery status returned to Charging
after reconnection. No camera, microphone or playback was started. No production
power fix or overnight alarm was installed. Raw logs remain outside Git.


## Touchscreen shutdown notification candidate - 2026-10-06

The active touch device is I2C 4-0038 (`fts_ts`), with
CONFIG_TOUCHSCREEN_FTS_MI=y and CONFIG_TOUCHSCREEN_FTS_FOD=y. A read of its
gesture-mode attribute reports Off and register 0xD0=0. That awake read does not
establish the controller's mode during suspend.

In the complete trial's kernel-time window, the touch notifier runs during
panel shutdown, followed by `FTS do resume work` and `Already in awake state`
immediately before PM suspend entry. The retained boot log contains no
`FTS do suspend` or `fts_ts_suspend` message. Source
`drivers/input/touchscreen/focaltech_touch_mi/focaltech_core.c` distinguishes
display-driven `fts_ts_suspend` (which handles gestures/FOD or writes the sleep
mode) from `fts_pm_suspend` (which sets the device-PM flag, enables IRQ wake and
resets a completion, without commanding controller sleep). A zero device-PM
callback result therefore does not prove that this controller entered sleep.

The source's `techpack/display/msm/dsi/dsi_drm.c` uses
`sde_connector_get_lp()` for shutdown notifications when FOD dimlayer is
enabled. `sde_connector_get_lp()` returns CONNECTOR_PROP_LP, not the complete
DPMS state, and can return zero. Zero is MI_DRM_BLANK_UNBLANK, which sends the
touch driver down its resume path even during bridge shutdown. The active
panel selected by cmdline is j11_38_08_0a_fhd_cmd, and its live DT contains
the FOD dimlayer property. This source mechanism is consistent with the logs;
the runtime `mi_cfg` flag and LP value at shutdown have not been directly
instrumented. Attempts to query connector properties with the available
modetest failed to open the device, so they provide no LP-value evidence.

The source-only candidate
`kernel/patches/diagnostics/lmi-dsi-powerdown-notifier-unvalidated.patch`
maps UNBLANK to POWERDOWN only within bridge disable/post-disable notifications.
It preserves LP1/LP2, the startup path, touch gesture/FOD policy, supply controls
and all charge/gauge settings. It is outside the production patch list. The
patch passes `git apply --check` on exact a5b3099017ae source, without changing
that source tree. This is not yet a compiled or hardware-validated fix and does
not establish that the tactile accounts for the residual current.

`prepare-touch-notifier-variant.py` derives a private boot constructor from the
reviewed power debugfs/reset-GPIO recipe, locks the candidate patch hash, checks
its target against the verified source archive and adds it to strict sequential
patch validation/application. The prepared private state is
`kernel/diagnostics/audio/state-power-touch-notifier-reviewed/`.
Shell/Python syntax and external-input/patch-sequence preflight pass. The first
preparation encountered an ambiguous transformation anchor and was rejected;
the corrected preparation uses unique anchors and keeps that failed state.
At preparation time no kernel compilation, source-tree patch application, boot
or flash occurred; the subsequent manual build is documented below.

The manual build will produce a separate
`D-repro-01-power-touch-notifier-diagnostic-boot.img`; retain the current boot
for recovery and use temporary Fastboot boot only. Required hardware checks
are touch suspend/resume logging, usable touch after wake, display/USB/charging,
and matched unplugged deep-suspend current measurements. Check wake/gesture
behavior separately before any production integration. A current reduction
must be measured rather than inferred from corrected notifications.


### Touch notification candidate: manual build completed

The operator's manual build on 2026-10-06 completed in inner state
`audio-swr-20261006T180037Z-66217` and wrapper state
`reset-gpio-variant-20261006T180020Z-66202`, both COMPLETE. Independent output
inspection confirms the two candidate shutdown mappings are present in the
private compiled source, post-olddefconfig configuration matches the lock,
the repacked ramdisk matches the original and the repacked DTB matches the
reset-GPIO-corrected DTB. The temporary boot is 54,652,928 bytes with SHA-256
`390dd50ab4dea33affc8386b300a3c21c4aca9bce39284b8e700a58c1e873bae`.
A separate Windows Downloads copy was verified with the same identity.
No binary or raw build output is tracked. Hardware boot, tactile suspend/resume
behavior and any current improvement remain unvalidated. No flashing occurred.


### Touch notification candidate: temporary hardware startup

After the operator's reported restart, /proc/version exactly matches the banner
embedded in the verified candidate Image: 4.19.325-cip128-st12-perf-ga5b3099017ae-dirty,
build #3 SMP PREEMPT, 2026-10-06 18:01:14 UTC. Live decompressed IKCONFIG SHA-256
matches c6da6e71cc7418f36997325ff5d72693d9861945cc4999b6be9661a150451e78.
This operational build identity distinguishes it from the earlier #3 build at
16:41:37 UTC; configuration alone would not distinguish the source-only patch.
The running kernel text itself was not hashed. USB SSH works; Charging, USB
online, capacity 100% and temperature 26.7 C were observed. UPower and the CPU
idle service are active; RTC wakealarm is empty. Tactile suspend/resume and
consumption comparison remain pending. No persistent flashing is claimed.


### Touch notification candidate: first unplugged trial

The first unplugged candidate trial on 2026-10-06 completed with 181.407 seconds
asleep and 0.676 seconds awake over 182.083 seconds. Independent L3 statistics
recorded one success lasting 181.425 seconds. RTC IRQ 323 caused the planned
wake; no early wake or nonzero device-PM callback result was observed. All
11,702 trace entries were retained with zero buffer loss. The transient service
finished successfully, its trace instance was removed and its owned RTC alarm
was cleared. Charging resumed after USB reconnection; CPU idle remains enabled.

The touch log now reports `FTS do suspend work by event POWER DOWN`, followed
by `fts_ts_suspend`, IRQ disable and a disabled-gesture branch before machine
suspend. The later `fts_ts_resume` resets the controller, reads chip ID 0x54/0x52,
restores its state and enables the IRQ. This contrasts with the earlier trial's
resume/Already-in-awake-state sequence and confirms that the candidate changes
the observed touch suspend path. Log lines tagged Error that explicitly say
register-write success are not evidence of failed writes. The operator subsequently confirmed
normal touch response after unlocking, opening an application and scrolling.
This validates one wake cycle, not repeated-cycle or gesture/fingerprint coverage.

Charge counter fell from 2,774,941 to 2,770,200 uAh while USB was offline,
giving 93.735 mA over the measured interval. Capacity remained 100%; initial
instantaneous current was 145.019 mA and final current 92.773 mA. The earlier
valid trace trial estimated 95.629 mA. This approximately 1.89 mA difference
(about 2%) is a single, non-interleaved comparison across a reboot and different
gauge state, not proof of an autonomy improvement. Wi-Fi conditions, battery
temperature and gauge settling were not controlled as matched variables.
The approximately 94-96 mA residual current remains unresolved. No production
patch or permanent boot was installed, and raw logs remain private.


### Wi-Fi shutdown isolation and October 7 overnight observation

A finite phone-local radio-off check on October 6 exercised the normal CNSS
idle-shutdown path. After 15 seconds, use counts for pm8150_s5, pm8150_s6,
pm8150a_s8, pm8009_s2 and pcie_0_gdsc were all zero; they remained zero at
45 seconds. The log recorded psoc idle timeout and CNSS idle shutdown. These
are driver-vote observations, not independent measurements of rail current.
The first restore command exceeded its eight-second timeout, but subsequent
inspection confirmed Wi-Fi enabled again and the original votes restored.
A pre-scheduled restoration timer had provided a fallback; none remains active.

The subsequent Wi-Fi-off suspend trial was invalidated by IRQ 438 msoc-delta
after only 2.944 seconds asleep over 3.625 seconds. Its trace had no buffer loss
or nonzero device-PM result, but that interval is too short to estimate or compare
idle consumption reliably. Wi-Fi was restored, the collector stopped, and its
RTC alarm and trace instance were removed. A revised bounded collector allowing
one guarded gauge-only re-suspend was prepared but not started before the night.
No persistent Wi-Fi, gauge or suspend policy was changed.

On October 7, the phone reconnected without rebooting. Its running build banner
still identifies the October 6 18:01:14 UTC touch-notifier candidate. Persisted
UPower history records 99% discharging at 21:12:26 CEST on October 6 and 66%
at 06:03:41 CEST on October 7: 33 percentage points over 8 h 51 min 15 s,
approximately 3.73 points/hour. The first inspection at 06:06 already found
68% charging and 22.5 C. Exact unplug/replug capacities were not captured.
The initial disk history ended at 01:48; a later UPower write recovered all
remaining overnight samples. The service stayed active with zero restarts,
so the apparent gap was delayed persistence rather than demonstrated data loss.

Kernel journal accounting found 66 completed suspend pairs between 21:12:39
and 06:05:01: 30,901.694 seconds suspended over a 31,941.929-second span
(96.74%). Sixty-five wake reports identified IRQ 438 msoc-delta; typical awake
intervals were about 16 seconds. The remaining current is therefore not
explained by the phone staying continuously awake. Radio state was enabled
before and after the night, but association and power votes were not continuously
sampled. This is an uncontrolled overnight observation, not the pending
fully-radio-off comparison. It does not demonstrate an autonomy improvement
from the touch notification candidate. All test services/timers were inactive,
the RTC alarm was empty, and charging worked after reconnection. Raw histories
and kernel logs remain private; no camera or microphone was started.


### Fully-radio-off suspend measurement — October 7

The repeat Wi-Fi-off trial completed without an early wake or guarded retry.
Clock accounting records 180.695 seconds asleep and 0.679 seconds awake over
181.374 seconds (99.63% suspend occupancy); independent L3 statistics increased
by one success and 180.712 seconds. Capacity remained 80%, and charge counter
fell from 2,102,047 to 2,097,408 uAh, giving approximately 92.077 mA over the
measured interval. Initial and final instantaneous readings were 91.796 and
90.331 mA. All five CNSS/PCIe supply use counts were zero both before suspend
and at the final snapshot. This establishes substantial gauge-reported residual
current even with the normal radio shutdown path, but does not independently
measure physical rail current or exclude a battery/gauge calibration issue.

The RTC produced the planned wake. Wi-Fi was restored, charging resumed, the
service and restoration timer are inactive, the owned alarm is empty, and the
trace instance was removed. The trace retained only 7,836 of 11,578 events,
with 3,742 overruns: clock/L3/gauge accounting remains independently available,
but the incomplete trace cannot support conclusions about every device transition.
No nonzero PM callback result appears in retained events; absence in an incomplete
trace is not proof that every callback succeeded. A nearby Wi-Fi-enabled arm
is pending to reduce the confounding of the older different-capacity comparison.


### Nearby Wi-Fi-enabled comparison — October 7

The enabled-radio arm on the same running candidate completed with 180.765
seconds asleep and 0.683 seconds awake over 181.448 seconds (99.62% occupancy).
L3 increased by one success and 180.782 seconds. Capacity stayed at 81%, and
charge counter fell from 2,125,537 to 2,120,758 uAh: approximately 94.817 mA.
The five CNSS/PCIe supply use counts were one at both snapshots, contrasting
with the radio-off arm's zero votes. The original enabled radio state was kept;
this is not a controlled associated-network workload comparison.

The nearby off/on difference is approximately 2.740 mA (about 2.9% of the on-arm
current). Both arms slept almost throughout and neither needed a gauge retry.
This single sequential pair, at 80% then 81% with charging between arms and
without matched temperature/association control, is insufficient to quantify
a stable Wi-Fi penalty. It does show that stopping the radio did not eliminate
the approximately 92 mA residual gauge-reported consumption in this experiment.
It does not identify the remaining consumer or independently calibrate the gauge.

The larger 1,024 KiB-per-CPU trace retained all 11,704 events without overruns
or nonzero PM callback results. The RTC caused the planned wake; the service
is inactive, its alarm is empty, the trace instance is removed, Wi-Fi remains
enabled and charging resumed. No permanent radio or suspend policy changed.


### APSS/ADSP sleep accounting — October 7

A further bounded three-minute trial retained the enabled radio state and added
RPMh master snapshots before and after suspend. Capacity stayed at 90%; charge
counter fell from 2,355,464 to 2,350,729 uAh over 181.883 seconds, approximately
93.720 mA. Clock accounting records 181.202 seconds suspended and 0.681 seconds
awake (99.63% occupancy); L3 recorded one success lasting 181.223 seconds.
No gauge retry or early reconnection occurred; the RTC caused the planned wake.

The exposed RPMh master counters were APSS and ADSP only. Using their 19.2 MHz
accumulated-duration counters, APSS added 181.240 seconds asleep (99.65% of the
interval; seven entries), and ADSP added 181.793 seconds asleep (99.95%; eight
entries). These counters support sleep of both processors despite substantial
gauge-reported residual current. They do not establish physical removal of every
DSP supply or account for unexposed masters, external peripheral loads or gauge
calibration. In particular, missing modem statistics are not proof of modem sleep.
The downstream kernel exposes msm_subsys states rather than remoteproc devices;
labels such as ONLINE/OFFLINING alone were not treated as current measurements.

The trace retained all 11,561 events without loss or nonzero PM callback results.
The collector is inactive, its RTC alarm is empty, the trace instance was removed,
Wi-Fi remains enabled and charging resumed. No processor, peripheral, driver,
regulator or gauge protection was disabled. This narrows the residual-current
investigation toward retained physical loads and measurement accuracy rather
than demonstrating an autonomy fix. Raw traces and histories remain private.


### Display chronology and codec supply policy — October 7

The completed trials were compared without another suspend or media capture.
In trials 06 and 08, `display_panel_vci` and `pm8150_l14` already had zero
use counts in the pre-suspend snapshot, then had one after wake. Trials 04
and 07 started with one and recorded their disable/enable transitions.
The missing panel-disable event in trial 08 is therefore explained by the
snapshot chronology; it is not evidence that the panel stayed powered in sleep.

The live WCD938x node lists `cdc-vdd-rxtx`, `cdc-vddio`, `cdc-vdd-buck` and
`cdc-vdd-mic-bias` as static supplies, with no per-supply `lpm-supported`
properties. The first three resolve to `pm8150_s4`; microphone bias resolves
to `pm8150a_bob`. The requested loads are 30,000, 30,000, 650,000 and
30,000 uA respectively. These are regulator policy requests, not measured
battery currents, and must not be added to estimate discharge.

In the locked source, `techpack/audio/asoc/codecs/msm-cdc-supply.c` defaults
missing `qcom,<supply>-lpm-supported` properties to zero. Its
`msm_cdc_set_supplies_lpm_mode()` only calls `regulator_set_load()` for
supplies with that flag. `wcd938x.c` registers a late-suspend callback which
requests this mode when the component was suspended. Trial 08 recorded that
callback returning zero; with the live properties, the helper cannot lower
these four load requests. This identifies a policy worth investigating, not
a demonstrated cause of the approximately 94 mA residual current.

Further inspection identified the actual live provider as
`qcom,rpmh-vrm-regulator`, implemented by `drivers/regulator/rpmh-regulator.c`,
rather than the separate upstream-style `qcom-rpmh-regulator.c`. S4's provider
has no supported-mode table; the downstream driver removes its `set_load`,
`set_mode` and `get_mode` operations when that table is absent. Reducing a
codec load request alone would therefore not change S4's hardware-mode vote.
S4 also supplies UFS and WLAN; it cannot be treated as an audio-only rail.

BOB does expose supported modes 0, 2 and 4, with load thresholds of 0,
1,000,000 and 2,000,000 uA. The driver's load mapping selects the same first
mode for both 30,000 and zero uA. Its PMIC5 mapping identifies that first mode
as PASS, exposed as framework STANDBY. The live debug view already reports
framework mode 8 (STANDBY) for both the normal and active-only BOB regulators;
the only enabled normal-regulator consumer is the codec's 30,000 uA request.
These are software votes and do not independently measure physical current.

Consequently, adding the missing codec LPM flags alone is not a justified
power-saving candidate on this live configuration: S4 cannot act on the load
change and BOB would retain the same mode. No kernel build is proposed for
that change. This does not exclude physical codec consumption while its
static supplies are enabled. Establishing whether those loads explain the
residual current requires a separately justified isolation or measurement;
blindly disabling a shared rail or converting static supplies to on-demand
would risk the validated audio and storage paths.

No supply was disabled, no DT property was changed, and no driver was unbound
during this inspection. No microphone or camera capture was performed.
Raw DT and trace dumps remain private.


### Final RPMh sleep commands — October 7

A bounded three-minute trial added the existing `rpmh_send_msg` and
`rpmh_tx_done` events without changing the radio or regulator policy.
The interval lasted 181.315 seconds, including 180.631 seconds suspended
(99.623%); L3 added one success lasting 180.649 seconds. Capacity stayed at
96%, while the charge counter fell from 2,493,460 to 2,488,679 uAh:
approximately 94.927 mA by the gauge. APSS and ADSP master counters recorded
99.636% and 99.953% asleep respectively. The RTC caused the planned wake;
no gauge retry, early reconnection or early-wake abort occurred.

All 11,937 trace events were retained without overrun, dropped events,
nonzero PM callback results or RPMh acknowledgement errors. Of these,
291 were RPMh send events. The live command database and TCS configuration
`[2,2,0,3,1,3,3,1]`, interpreted using the locked downstream driver's allocation
order, identify apps_rsc banks 0–1 as active, 2–4 as sleep and 5–7 as wake.
Bank 56 represents the separate PDC data-write path, not a regulator bank.

At the `machine_suspend` entry, the final sleep commands superseded earlier
nonzero bus commands. The final votes were:

| Resource | Sleep command | Interpretation |
|---|---|---|
| `cx.lvl` / `mx.lvl` | 0 / 0 | APSS requests level zero |
| `xo.lvl` | 0 | APSS requests level zero |
| `bobc1` mode | 2 | PMIC5 PASS; wake command is AUTO (6) |
| `ldoa12` enable | 0 | Disable request; wake command is 1 |
| `SH4`, `SN11`, `CN0` | `0x40000000` each | Commit bit, invalid/zero X and Y bandwidth votes |

The BCM interpretation follows `msm_bus_fabric_rpmh.c`: commit is bit 30,
valid is bit 29, and X/Y each occupy 14 bits. Earlier values such as
`0x60198000` are not the final sleep request. Post-reconnection `bw` sysfs
snapshots contain nonzero USB/NPU client entries, but are awake snapshots;
they must not override the final sleep trace or be treated as proof of a
sleep-time bus leak. An absent command for a resource does not establish its
state: unchanged requests can remain cached, and other masters can vote.

These observations establish the APSS software requests, not the physical
state or current of every PMIC rail, peripheral or unexposed subsystem.
The approximately 95 mA remains unexplained. No new kernel build, regulator
write, driver unbind, camera capture or microphone recording was performed.
The collector is inactive, its trace instance was removed, its RTC alarm is
empty, Wi-Fi remains enabled and charging resumed. Raw traces stay private.


### Read-only RPMh aggregate observer candidate — October 7

The existing event trace shows commands that are emitted, not a complete
snapshot of unchanged requests. The isolated diagnostic patch
`kernel/patches/diagnostics/lmi-rpmh-vote-observer-unvalidated.patch` adds a
read-only `lmi_diag_votes` sysfs attribute to each downstream RPMh provider
when DEBUG_FS is enabled. It is outside the production patch list.

The reader holds the provider's existing aggregation mutex, computes active
and sleep requests into local zeroed structures, and prints their validity
masks, register values, cached sent requests and each regulator's active/sleep
participation. It does not send RPMh commands, access PMIC registers, call
regulator setters or change enable/voltage/mode policy. The existing aggregate
helper only modifies its local output structures. Device-managed attribute
removal precedes managed provider memory release; an attribute creation failure
warns without failing regulator probe. Output is bounded to one sysfs page.

These are software requests, not measured current or physical rail states.
A cached sleep request is not valid just because its storage contains a value;
its valid mask and `sleep_request_sent` must be interpreted. Other masters'
votes remain outside this reader, and snapshots around suspend do not sample
the system continuously while it is asleep.

`prepare-rpmh-vote-observer-variant.py` derives from the current debugfs/reset-GPIO/
touch-notifier recipe, locks the observer patch hash and adds it to the archive
comparison, strict patch sequence and application steps. It prepares an ignored
private state directory and never builds or contacts hardware. The output name
is `D-repro-01-power-rpmh-votes-diagnostic-boot.img`. The private prepared state
is `kernel/diagnostics/audio/state-power-rpmh-votes-reviewed/`.

Host validation passed: preparer Python syntax, wrapper shell syntax,
`git apply --check --whitespace=error-all` on exact source, archive target
comparison, the complete sequential patch check and native Kconfig validation.
No kernel target was compiled. The initial check rejected missing environment
paths, and a subsequent noninteractive user check stopped at sudo; the fully
specified root-WSL check then completed. Failed checks are retained in ignored
private state. This validates preparation, not the C compilation or hardware.

At preparation time, the candidate was source-only pending the manual build. After temporary
Fastboot boot, verify identity, provider attributes, display, USB, charging and
touch before a bounded unplug test. Capture requests after USB runtime suspend,
then compare with the final command trace. Do not disable a retained supply
merely because its software sleep enable is nonzero.


### RPMh observer manual build and extended observation ? October 7

The operator manually produced `D-repro-01-power-rpmh-votes-diagnostic-boot.img`,
54,652,928 bytes, SHA-256
`a89ae4d9529dcef55d3969eb6b5a75c2617d9ef0e2e1f568c5f619eb1adf5c50`.
The internal builder recorded COMPLETE; kernel build, DTB build and DTB
verification each returned zero. The outer wrapper reported a missing status
file because the inner state directory was root-owned mode 0700 and unreadable
by the invoking user. Root inspection confirmed completion and the output
manifest; the Windows transfer was independently checked against the same hash.
This is a wrapper reporting/access defect, not evidence of a failed kernel build.
No global permissions were changed and no repeat compilation was started.

After the operator's temporary boot, USB SSH and charging worked and all 47
RPMh provider attributes were readable. The live banner identifies the build
of October 7 at 05:27:54 UTC; IKCONFIG SHA-256 is
`c6da6e71cc7418f36997325ff5d72693d9861945cc4999b6be9661a150451e78`.
The banner/config and observer presence corroborate the candidate but are not
cryptographic attestation of running kernel text. No new touchscreen or media
validation has yet been performed with this variant.

The operator reported approximately 10 hours 20 minutes disconnected, with
capacity falling from 100% before departure to 63% at first SSH after return:
about 3.58 percentage points per hour. This uncontrolled interval is not an
independently calibrated current measurement. The same boot remained active.
Kernel logs contain 80 completed deep-suspend intervals from 08:02:37 to
18:04:55 local time: approximately 34,889 seconds asleep over a 36,139-second
span (96.54%). Of the 80 resume causes, 76 were msoc-delta, one esr-delta,
one RTC alarm, one msoc-high and one Type-C state change. Median awake gaps
were 15.83 seconds; median sleep among the 77 intervals lasting at least two
minutes was 481.66 seconds. No panic, Oops or matching suspend-failure message
was found in the inspected current-boot kernel journal. This does not establish
absence of every possible device error. The observation provides no autonomy fix.

An awake, plugged-in observer snapshot has eleven VRM resources with a valid
computed sleep enable of one. It is not their final suspend state. In the locked
provider driver, a separate sleep request is sent only when active and sleep
requests differ or previously differed; an absent sleep command or invalid
cached sleep mask cannot be interpreted as an off request. Late-suspend changes
must be matched against the final command trace. A bounded three-minute
collector adding all 47 observer snapshots is prepared but has not been run.
No RTC alarm or collector was installed for the extended absence; raw histories
and snapshots remain private. Shared supplies must not be disabled based solely
on these software requests.


### First bounded aggregate-observer trial ? October 7

With the observer candidate and Wi-Fi enabled, the operator completed a bounded
three-minute unplugged trial. Elapsed time was 181.240 seconds, including
180.547 seconds suspended (99.617%); L3 added one success of 180.564 seconds.
Capacity remained 73%, while the charge counter fell from 1,933,009 to
1,928,237 uAh: approximately 94.787 mA by the gauge. APSS and ADSP counters
recorded 99.636% and 99.950% asleep respectively. The RTC caused the planned
wake, with no retry, early reconnect or early-wake abort.

All 47 provider snapshots were readable at armed, pre-suspend and finished
points. The trace retained all 11,892 events without overrun, dropped events,
nonzero PM callback results or RPMh acknowledgement errors. Exact begin/end
markers delimit the machine-suspend command window; substring matching of
`end` would incorrectly match `suspend` and must not be used for extraction.
The final sleep bank again requests zero CX/MX/XO levels, BOB mode PASS (2),
L12 enable zero/mode 4, and zero/invalid bandwidth for SH4/SN11/CN0.

The pre-suspend aggregate requests include enabled BOB, L5, L6, L17, the
PM8150A L1 touch supply, S4 and four Wi-Fi rails. These snapshots precede
late device suspension: the trace explicitly disables L17 before machine
suspend, while L12 already has a zero sleep enable before initial suspend.
L14 is already disabled in that snapshot and is enabled again after wake.
Consequently neither pre-suspend L17 nor post-wake L14 activation establishes
sleep-time retention. Remaining computed requests are software state, not
independent physical-current measurements, and unexposed masters remain outside
this observer.

Consumer mapping identifies L5 as shared among display/USB/UFS/PCIe PHY paths,
L6 and L17 as UFS supplies, PM8150A L1 as the touchscreen supply, S4 as shared
codec/WLAN/UFS power, and BOB as a static codec supply. The locked UFS driver
intentionally retains its I/O rails in low-power mode for device sleep with
HIBERN8 while switching off VCC. The touch driver normally sends a sleep
command rather than cutting supply power; supply cycling is confined to its
factory-build branch. These policies do not prove excessive consumption by
those consumers or justify disabling shared supplies.

The collector is inactive, the owned RTC alarm is empty, the trace instance
was removed, charging resumed and Wi-Fi remains enabled. No regulator policy,
voltage, device binding or persistent setting changed. A radio-off comparison
with the same 47 observer snapshots is prepared, not executed. Its new purpose
is to distinguish retained aggregate requests from the previous radio-off
current measurements; no autonomy improvement is claimed. Raw data stays private.


### Radio-off aggregate comparison and gauge limits ? October 7

The second aggregate-observer trial stopped Wi-Fi using NetworkManager and
verified zero software use counts for S5, S6, PM8150A S8, PM8009 S2 and PCIe
GDSC before suspend and after the planned wake. All four VRM sleep-enable
requests changed to zero in the observer as well. No driver was forcibly unbound.

Elapsed time was 182.097 seconds, including 181.390 seconds suspended
(99.612%); L3 added 181.408 seconds. Capacity stayed 77%, while the charge
counter fell from 2,026,412 to 2,021,701 uAh: approximately 93.135 mA by the
gauge. APSS and ADSP counters recorded 99.623% and 99.989% asleep. The RTC
caused the planned wake without retry or early abort. All 47 snapshots were
readable and all 11,958 trace events were retained without loss, nonzero PM
callback results or RPMh acknowledgement errors.

Compared with the preceding enabled-radio arm's 94.787 mA, the difference is
1.652 mA. These short sequential arms had intervening charging and different
capacity, without matched temperature or association control; the difference
is not a calibrated stable Wi-Fi penalty. The important result is that disabling
the four radio requests still leaves approximately 93 mA by the gauge.
BOB, L5, L6, the touch L1 supply and shared S4 requests remain comparable.
L17 is explicitly disabled during device suspension in both traces. The final
L5/L6 mode commands are PMIC5 LDO LPM (4), not HPM (7), despite the earlier
awake/pre-suspend values. BOB retains its PASS sleep-mode command.

The read-only follow-up found no modem exposed through ModemManager and
Bluetooth soft-blocked. Downstream subsystem labels were not interpreted as
physical-current measurements. Flash intensity values can remain nonzero when
its switch controls are zero: the driver getter returns cached brightness,
not a hardware light/current measurement. No flash or microphone was activated.
GPU force-clock, force-bus and force-rail settings are zero; both traces contain
GPU clock and CX GDSC disable transitions. `force_no_nap=1` affects the ACTIVE
to NAP idle path, not proof of a permanently powered GPU through system sleep.
No graphics policy was changed.

The operator confirmed the original battery. Its selected gauge profile is
`j11sun_4700mah`; reported design capacity is 4,700 mAh and learned full capacity
2,822 mAh, while the exposed cycle count is one. These values do not establish
physical battery health or lifetime cycles. No independent capacity test exists.
The active DT enables weighted learning and permits replacing a mismatched
profile; the driver does not reload an identical profile solely because
`fg-force-load-profile` is set. Profile replacement can clear cycle accounting.
The absent min/max learning-limit properties default to zero (disabled); there
is no evidence that 2,822 mAh was forced by a 60% lower clamp.

In the locked GEN4 driver, `charge_counter` is computed from the hardware
CC_SOC_SW fraction multiplied by learned capacity. Its delta is therefore not
an independent coulomb/current calibration. `current_now` uses the separate
IBATT register conversion, approximately 488.281 uA per signed count; the
pre/post-unplug readings near 92?95 mA are internally consistent with the
counter-derived interval, but both still depend on the same gauge hardware.
No learned capacity, battery profile, charging limit or calibration was reset.
Changing the reported full capacity would not demonstrate lower physical drain.

Wi-Fi was restored and confirmed enabled before reconnection; the restore timer
and collector are inactive, the owned RTC alarm is empty, the trace instance
was removed and charging resumed. Further identical short suspend trials are
not justified by these results alone. Remaining discrimination requires a
specifically justified peripheral isolation or an independent/off-state baseline;
no unsafe shared-rail shutdown is proposed. Raw data remains private.

### Completion reporting correction — 2026-10-07

The reset-GPIO wrapper now verifies private internal completion metadata with
sudo when it is inaccessible to the invoking user. It retains the private
state/output modes and still rejects missing or linked STATUS, non-success
status, nonzero builder exit, and empty or linked build outputs. Sixteen bounded
metadata regression cases passed, including a root-owned private fixture
that rejects an unprivileged reader. The same verifier accepted the existing
observer state and its expected 54,652,928-byte output without modifying them.
A newly prepared observer chain passed recipe checksums and host-only strict
patch preflight. No kernel was compiled for this correction; interactive sudo
authentication and a complete user-invoked build have not been retested.
Previously prepared recipes and their evidence remain unchanged. See the
[audio constructor documentation](../audio/README.md#private-internal-completion-metadata).

### Approximate powered-off comparison — 2026-10-07

An initial systemd poweroff reached the poweroff target but the operator reported
that the phone restarted. That attempt is not a valid powered-off discharge
test. The restart returned to the original persistent D-repro kernel, so the
temporary RPMh observer identity must be checked again before later observer
tests. The operator subsequently confirmed a manual shutdown for an unplugged
comparison; the return observations are recorded below.

The last pre-shutdown sample reported 88% and 2,273,114 uAh. It did not
include a paired host/phone clock sample; a later host reading does not establish
an exact phone-clock offset. Measure elapsed time using the trusted host/operator
interval rather than subtracting phone timestamps. Read the return battery
before any further diagnostic reboot. Startup and any connected charging still
affect that return sample: this
comparison is approximate and cannot independently calibrate the gauge or
measure powered-off current. Do not infer a battery fault or an autonomy fix
from this approximate test.

### Single read-only return snapshot — 2026-10-07

`read-power-snapshot.py` emits one bounded JSON snapshot of the battery, BMS,
USB supply, kernel release/banner, decompressed IKCONFIG hash, device compatible
strings, uptime, existing RTC alarm and CPU-idle parameter. It runs no commands,
starts no service or acquisition, makes no writes and schedules no wakeup.
Missing or invalid fields remain explicitly unavailable; a missing USB property
must not be interpreted as zero. Current signs and reported gauge capacity are
preserved without recalibration or overriding the kernel's status.

📱 SSH — Xiaomi lmi — 🔎 Read only — phone already powered on and reconnected

```sh
python3 /path/to/read-power-snapshot.py
```

Keep raw JSON outside Git: the kernel banner can contain a build-host identity.
For a powered-off comparison, collect the first return snapshot before another
diagnostic reboot. Record the off interval using a trusted host/operator clock
and note any startup/USB-charge time. This snapshot cannot measure current while
the phone is off or prove physical battery capacity. Banner/config identity also
does not establish the executable boot image's hash; retain the manual boot
artifact manifest and reconfirm the candidate before later controlled trials.

`test-power-snapshot.py` uses a temporary fixture tree, including missing fields,
negative charging current, malformed and oversized config data. It never opens
the host's live power supplies or contacts the phone. These fixture tests passed;
the first live return read also succeeded without changing phone state. No shutdown,
Android restore, battery learning reset or charging-limit change is automated.

### Shared Android gauge source and retry candidate — 2026-10-07

The selected lmi battery-profile file and five inspected gauge-read/counter
function bodies match both pinned Android references. A shared retry-boundary
defect was reproduced using the actual C functions and simulated register reads.
A separate two-loop candidate passes the same twenty cases but is not included
in any diagnostic recipe or live kernel. It addresses inconsistent-read handling,
not charge calibration or demonstrated residual consumption. See the
[source comparison and proof](../../../docs/provenance/external-lmi-source-comparison-2026-10-07.md#battery-profile-and-gauge-read-follow-up).


### Powered-off return observations — 2026-10-07

After at least one hour confirmed off, the operator reported approximately two
minutes in Fastboot while awaiting instructions, then a normal boot showing 88%.
The first SSH return snapshot, at about 174 seconds of kernel uptime after USB
reconnection, still reported 88%, Charging, 2,288,607 uAh, approximately -651 mA
and 22.2 C. The permanent D-repro banner and IKCONFIG hash
`6512a0c29ebf987d25c0cceb79917df32d6fed4b67e4c3b94bfad9fdb1745e37`
were present; the transient RPMh observer was no longer running. No further
diagnostic reboot occurred before this measurement. The RTC alarm was empty.

The percentage matches the last pre-shutdown 88% sample, so there is no visible
large percentage drop in this approximate comparison. It does not establish
zero off-state consumption, battery health or a Mobian autonomy fix. Charging
between the pre-shutdown sample and actual manual shutdown was not quantified;
Fastboot, startup and resumed USB charging also affect the return. The counter
increase of 15,493 uAh cannot be treated as an off-state gain or discharge rate.
The phone clock was not used to determine the off interval. Raw identifying
snapshot data remains outside Git. No battery calibration or profile was reset.


### Permanent-kernel profile lookup failure — 2026-10-07

The powered-off return boot reproduced the older profile-load failure: the
gauge reported `Unknown Battery`, zero design capacity, resistance ID 99,800
ohms and profile errors -6/-61 followed by the driver's OTP fallback. This is
an observed selection failure, not proof that retained gauge SRAM has been
erased or contains a particular profile. The earlier successful lmi-profile
identification must not be attributed to this permanent boot.

Read-only inspection of the live DT confirmed that the gauge's existing
`qcom,battery-data` phandle targets `/soc/qcom,battery-data`, containing
`j11sun_4700mah`, 100 kOhm ID, 4,700 mAh nominal capacity and 416 profile bytes.
The flattened tree order places that container before the gauge. The only
subsequent node named `qcom,battery-data` is `/vendor/qcom,battery-data`, whose
children are generic profiles rather than the lmi profile. In the locked
driver, `of_find_node_by_name(node, "qcom,battery-data")` searches only nodes
after `node`, not its property target. The source traversal and live ordering
therefore explain why the named lmi lookup cannot succeed on this boot.

The isolated candidate
[`lmi-fg-profile-phandle-unvalidated.patch`](../../patches/diagnostics/lmi-fg-profile-phandle-unvalidated.patch)
resolves the existing phandle first. If absent/unresolved, it retains the
legacy name search and supplies an owned node reference because that API
consumes its starting reference. The patch makes no direct changes to profile bytes, charging parameters,
learning code, capacity conversion or authentication policy. However, reaching
the existing load path can change retained gauge state, as explained below.
Patch SHA-256:
`59e357834e97f043a45c51e50e29ada59a44ca657afa9c2fcfdeafbfb56884f6`.
The locked `qpnp-fg-gen4.c` input SHA-256 is
`0f5676829cb2a40daa191a456998c700d744afe8346e07dd3c7af2a7e8685957`.

`test-fg-profile-lookup.py` verifies that exact input and applies the patch with
zero fuzz in a temporary tree. The actual changed C lookup fragment compiles
with strict warnings against bounded OF stubs. Explicit-link precedence,
legacy fallback, missing-container handling and 200 repeated reference-balanced
lookups pass; the source remains unchanged. These stubs are not a full kernel
OF implementation or a hardware test. No kernel was compiled or deployed and
the candidate is not included in any prepared constructor.

A future manual diagnostic build must first review profile-loading side
effects, including the existing force-load policy and retained gauge state.
Validation must identify the boot, inspect startup profile selection and
confirm charging before any autonomy comparison. Successful selection alone
would not prove lower physical consumption or battery health. Do not merge
this with the separate shadow-read retry candidate merely to combine trials.


#### Profile-loading side effects reviewed before deployment

The locked `is_profile_load_required()` compares only the first 24 profile
bytes when an accepted integrity marker is present. A matching prefix skips
reload even with `qcom,fg-force-load-profile`; it does not prove all 416 bytes
match. A different prefix with force-load enabled, an absent integrity bit or
an invalid integrity marker can trigger a load. SRAM read errors instead skip
the load. No live SRAM integrity or profile-prefix measurement was obtained in
this permanent boot, so its reload decision remains unknown.

If loading occurs, `profile_load_work()` can clear cycle counters, write the
416-byte profile, restart the gauge, and store nominal capacity as learned
capacity on the normal non-aged path. SDAM handling also depends on its cookie.
Even a temporary `fastboot boot` therefore does not guarantee that all gauge
state changes disappear after reboot. The candidate must not be deployed as
though it were only a cosmetic battery-name fix. A future trial needs an
explicit gauge-state preservation/observation plan before activation. No
profile reload, counter clearing or learned-capacity write was performed here.


### Guarded retained-profile observer — 2026-10-07

The separate diagnostic patch
[`lmi-fg-profile-observer-unvalidated.patch`](../../patches/diagnostics/lmi-fg-profile-observer-unvalidated.patch)
adds the root-readable, non-writable `lmi_fg_profile` device attribute when
CONFIG_DEBUG_FS is enabled. An explicit read follows the existing lmi DT
phandle, copies the named 416-byte reference into a local buffer, then reads
retained profile SRAM and the integrity marker before/after. It reports marker,
24-byte prefix and full 416-byte equality, cached profile status, force-load,
multi-profile flag and battery ID. Missing or malformed reference data and SRAM
read errors are returned explicitly; a changed integrity marker returns EAGAIN.
Stable markers are not a guarantee of an atomic 416-byte sample.

The attribute calls no profile selector/loader, setter, work scheduler, gauge
restart or gauge-data write. SRAM reads use the existing memory-interface
transport and can wake it; take this snapshot while connected, not during a
standby-consumption measurement. No periodic polling or acquisition is added.
Raw profile bytes and authentication identifiers are not emitted.

The diagnostic also blocks the existing reload-required branch before cycle
clearing and `qpnp_fg_gen4_load_profile()`. It does not bypass the existing
profile-selection failure or authentication policy. A matching retained-prefix
path can still perform the driver's normal post-profile initialization, including
its existing SDAM handling; this is not a claim that the whole boot performs
no gauge writes. Battery removal and ordinary hardware initialization remain
normal driver behavior. This temporary guard is diagnostic, not a production fix.

Host tests apply the patch with zero fuzz to the locked source and compile the
actual attribute fragment with strict warnings and bounded DT/SRAM stubs.
Twelve cases cover full/prefix/tail equality, missing data, malformed lengths,
all three read-error positions and a changing marker. References balance and
cached chip state remains unchanged. Two extracted control-flow cases confirm
that the reload-required path exits before clearing/loading, while the matching
path still reaches existing initialization. The stubs are not a full kernel or
hardware test. No kernel was built or booted for this observer.

Patch SHA-256: `ec86f4cb13d7efe78f3dfcddbe6771c09373b24b2ab868d05e04f2261de80440`.
`prepare-fg-profile-observer-variant.py` derives a new private recipe from the
already tested RPMh/touch/debugfs chain; the selection-fix and shadow-retry
candidates are explicitly excluded. The final guarded recipe passed manifest
checks and the complete strict patch preflight. Earlier prepared states were
not overwritten. The original boot's ramdisk and DTB sections are retained and
verified by the constructor. Runtime bootloader overlays still need live review.

The user performs all kernel builds. Use the guarded prepared directory,
not the earlier observer-only preparation. A full user-invoked build and
live attribute availability remain pending. Before any later standby trial,
identify the temporary boot and take a single connected profile snapshot from
`/sys/class/power_supply/bms/device/lmi_fg_profile`; retain it privately.
Report prefix equality separately from whole-profile equality and interpret
the integrity marker using the driver's whitelist. Do not infer physical
capacity, lower consumption or safe profile replacement from equality alone.


#### Single guarded-profile read and interpretation

`read-fg-profile-observer.py` reads at most 4,096 characters once from the
root-only attribute and emits parsed JSON. It rejects missing, duplicate,
unknown and inconsistent fields. Missing attributes and kernel read errors
remain explicitly unavailable rather than becoming zero or "no reload".
It emits no raw SRAM bytes and performs no writes or background sampling.

The integrity whitelist matches the locked driver's symbolic bit combinations.
For single-profile mode, `reviewed_reload_rule` reports the reviewed logic from
marker and prefix equality, including force-load behavior. It is interpretation
of this snapshot, not an observed execution of the loader; the diagnostic guard
blocks the reload-required branch. Multi-profile age state is not captured, so
that interpretation is unavailable in multi-profile mode. Full-profile equality
is reported separately because the driver checks only the first 24 bytes.

The host-only reader test derives the whitelist from the exact locked source,
then checks marker boundaries, prefix/full mismatch, forced/non-forced behavior,
multi-profile limits, malformed input, missing files and the size cap. It uses
only local fixtures. A live read awaits the user-built diagnostic boot; do not
present successful parsing as evidence that the attribute is already installed.

📱 SSH — Xiaomi lmi — 🔎 Read only — guarded diagnostic boot already confirmed

```sh
python3 /path/to/read-fg-profile-observer.py
```

Keep its result private with the manual boot manifest and first battery/kernel
snapshot. The normal permanent boot has no such diagnostic attribute. Do not
run the reader in WSL expecting it to read the phone; it must execute over SSH
on the confirmed diagnostic boot. This step needs neither camera/microphone
acquisition nor a cable manipulation.


### Reuse of the existing reviewed kernel — 2026-10-07

The operator requested persistent installation of the already built/tested
RPMh observer rather than another kernel build. The selected existing artifact
is `D-repro-01-power-rpmh-votes-diagnostic-boot.img`, 54,652,928 bytes,
SHA-256 `a89ae4d9529dcef55d3969eb6b5a75c2617d9ef0e2e1f568c5f619eb1adf5c50`.
Both existing host copies match. This does not make the diagnostic a production
autonomy fix. Its RPMh attributes are available in the previously tested boot;
the newer guarded FG attribute, phandle fix and shadow-retry candidate are not
part of this image. Do not request another build merely to change observation
detail while the operator has selected this existing baseline.

Before installation, the partition was confirmed as a single `boot`, 134,217,728 bytes; no
boot A/B label or slot token was found. Its first 52,924,416 bytes exactly match
the existing original D-repro image, SHA-256
`0b6c7d88b3068ae4e3d106fd4b15a1a79bf00c3e576be7b3fcd8ab62faed73ad`.
That image is the available rollback baseline. This comparison covers the image
prefix, not an exact backup of all partition padding or any trailing metadata.
No new kernel or full-partition backup was created; the existing rollback image
was made accessible to the host flashing tool without modifying its bytes.

The operator successfully flashed this existing image to `boot` and rebooted.
A post-reboot read at 18:50 UTC confirmed that the first 54,652,928 bytes of
`boot` match the selected RPMh SHA-256. The running banner is dated
2026-10-07 05:27:54 UTC; IKCONFIG SHA-256 is
`c6da6e71cc7418f36997325ff5d72693d9861945cc4999b6be9661a150451e78`.
All 47 RPMh observer attributes are present. These independent checks support
the installed/running identity; the partition prefix alone is not executable
identity proof. USB is online, charging resumes, CPU idle is enabled, and no
RTC alarm is armed. The newer FG observer remains absent.

The gauge reports `j11sun_4700mah`, design capacity 4,700,000 uAh and learned
full capacity 2,822,000 uAh, with 100% reported charge and 24.5 C. Unlike the
original permanent boot return, the profile is recognized. This is not proof
of improved autonomy or physical capacity, nor proof that gauge state did not
change during boot. No new unplugged measurement or operator touch check has
been performed after this installation.
The constructor's historical temporary-only message remains its default policy;
the operator specifically authorized this persistent baseline for reproducible
comparisons across shutdown/restart. The operator performs Fastboot actions.
Only the boot partition is in scope; no userdata, firmware, recovery, vbmeta,
bootloader-lock or partition-layout change is requested. The post-install build/config, attributes and gauge checks above are complete.
Operator confirmation of display/touch behavior remains pending. A reboot
alone is not proof that the requested candidate is running or that gauge state
is unchanged. Retain one working candidate and the rollback baseline; obsolete
diagnostic images can be removed after the retained installation is confirmed,
preserving the small recipes/manifests and evidence rather than daily binaries.

The guarded FG recipe/readers remain prepared research, not the next requested
manual build and not deployed functionality. Hardware profile comparison using
that new attribute is deferred unless a later justified build includes it.


### First standby measurement after persistent installation — 2026-10-07

The unchanged-radio trial on the confirmed installed RPMh baseline completed
without an early wake or gauge resuspend. From the pre-suspend to final samples,
elapsed time was 181.396 s, monotonic awake time 0.716 s and inferred suspended
time 180.679 s (99.605%). Charge counter fell by 4,504 uAh, corresponding to
89.387 mA averaged over this interval. The reported percentage stayed at 100%.
The final wake reason was the programmed RTC alarm. After reconnect, charging
resumed, the diagnostic service was inactive with success, and neither its
trace instance nor RTC alarm remained armed.

This is one short gauge-derived measurement, not an independently calibrated
physical current measurement or a proven autonomy improvement. Earlier radio-on
and radio-off samples were approximately 94.787 and 93.135 mA respectively,
at different state of charge and boot history. Their difference from this
89.387 mA sample cannot isolate a kernel, radio or profile effect. The installed
baseline now survives restart, allowing subsequent comparisons to identify and
hold the kernel constant. Raw logs remain private; no audio/video acquisition,
new kernel build or radio-state modification was performed in this trial.


### Overnight return on the persistent RPMh baseline — 2026-10-08

The 21:01:45 CEST baseline on October 7 reported 100%, charge counter
2,729,766 uAh and 24.0 C while still charging. The first SSH return on
October 8 at 05:41:45 CEST reported 69%, 1,914,318 uAh and 21.2 C, already
charging. The running banner, IKCONFIG and installed boot-image prefix still
match the confirmed RPMh baseline. Boot time was 32,127.039 seconds; the
continuous boot-time progression from the previous sample supports no intervening
restart. The profile remained `j11sun_4700mah`, with learned full capacity
2,822,000 uAh and design capacity 4,700,000 uAh.

Across the two samples, elapsed boot time was 8.666782 hours and charge counter
fell by 815,448 uAh, giving an approximate 94.089 mA. This includes the baseline
while plugged in, charging before the return read, and any operator activity;
the actual unplug instant is not yet known. It is not a calibrated off-cable
current measurement. The first return value is retained separately from the
later 70% reading taken after additional charging.

The kernel journal contains 62 completed deep-suspend pairs between 21:17:28
and 05:41:23 CEST. Their combined sleep time is 29,269.886 seconds over
30,234.989 seconds (96.808%). The 61 intervening awake gaps total 965.103
seconds and are at most 15.852 seconds each. Resume reports identify 61
`msoc-delta` interrupts and one `msoc-high` interrupt. No suspend-failure,
watchdog, BUG, Oops or thermal-shutdown message was found in the selected
current-boot interval. These journal timestamps and markers do not independently
measure rail current or exclude every possible hardware issue.

No trial logger was left active overnight. Radio was enabled before and after,
with association and supply votes not continuously sampled; this must not be
labelled a radio-off experiment. The RTC alarm was empty at return and charging
worked. The loss of 31 reported percentage points despite extensive deep suspend
confirms the autonomy problem persists on the now-persistent baseline. It does
not isolate the gauge, physical battery condition or remaining consumer. Raw
logs and first-return data remain private. No camera/microphone, new build or
live power-policy modification was performed for this observation.


### Retained profile verified using existing debugfs — 2026-10-08

No additional kernel is required to compare the retained profile on the
confirmed RPMh baseline. Its existing `/sys/kernel/debug/fg/sram` interface
exposes two software reader controls (`address`, `count`) and a data file.
The locked `fg-util.c` snapshots those controls when opening data; its read
path calls `fg_sram_read`, while SRAM writes are a separate data-file write
operation. The reader opens data with `O_RDONLY` and never invokes that write
path, profile loading, gauge restart or learned-capacity adjustment.

The bounded live read found integrity `0x03` before and after, with the load
bit set and a whitelisted marker. All 416 retained bytes equal the live lmi
`j11sun_4700mah` reference, including its first 24 bytes. Both hashes are
`583d77b61a7723fe4f40990eafa42c6283a87c41ba39a69ad2be77ce70f16050`.
The software reader controls were restored and reread successfully. This
rules out a mismatched retained profile at the time of this read, despite
continued high discharge. It does not calibrate current, establish physical
battery health or prove that learned capacity is correct. No new kernel,
SRAM data write or calibration change was performed.

`read-existing-fg-profile.py` locks the running build and expected reference
hash, requires USB online, and allows only profile word 65 / 416 bytes and
integrity word 299 / one byte. GEN4 addresses are words of two bytes; debugfs
prints decimal addresses with four bytes per full line. Strict parsing rejects
missing, malformed, misaddressed, excessive or incomplete output. This matters
because the driver's debugfs read can expose an underlying SRAM-read failure
as empty output. It validates stable integrity across the profile read and
restores the original software controls in a `finally` block. It emits hashes
and equality results rather than raw SRAM contents.

Run only as an on-demand connected-phone diagnostic with no concurrent SRAM
reader or writer. The controls are shared and do not provide isolation from
uncooperative processes. SRAM transport may briefly wake hardware; this is not
a standby logger. Full-profile differences in another read can also reflect
normal runtime tuning and must not automatically be labelled corruption.
The host test covers nine parser cases and three restoration scenarios
(success, SRAM read failure and changing integrity), without hardware access.
The newer guarded FG observer remains unbuilt and absent from this baseline;
it is not needed for this existing-interface observation.

A separate check found `fts_gesture_mode` already Off. The touch driver logs
`gesture suspend...` before checking that flag, then logs `gesture is disabled`;
the entry message alone does not prove gestures are enabled. Disabling that
already-disabled setting is not a useful isolation trial. Fingerprint/AOD
branches can select a different suspend path, so this check alone does not
prove that the touch controller or its rail is physically powered down.


### Normal NFC power-command comparison — 2026-10-08

A source-guided check found the live SN100_B controller's VEN GPIO high with
no client holding `/dev/nq-nci`. The driver's successful hardware probe leaves
`nfc_ven_enabled` true, and closing the character device does not lower VEN.
Opening it does temporarily enable its interrupt, reset software statistics
and select normal firmware-GPIO state; closing disables that interrupt for the
last client. Cached identification and `ESE_GET_PWR` on this confirmed SN100
variant were used to read VEN without a power command during discovery.
That getter maps another GPIO on other variants and must not be reused blindly.

A bounded trial then used the driver's ordinary `NFC_SET_PWR(0)` request,
verified VEN changed from one to zero, and restored it with request one after
the final sample. Restoration verified zero to one. No GPIO was exported or
written directly, driver unbound, firmware downloaded, shared rail forced off
or kernel rebuilt. A one-shot restoration timer backed up the collector's
`finally` cleanup; it was stopped after successful restoration. The power
helper's seven host guard/transition cases passed without hardware access.

| Arm | Reported charge | Elapsed / suspended seconds | Suspend share | Counter drop | Gauge average |
|---|---|---|---|---|---|
| VEN low, trial 13 | 88% | 181.503 / 180.810 | 99.619% | 4,479 uAh | 88.838 mA |
| VEN high, trial 14 | 89% | 181.727 / 181.035 | 99.619% | 4,558 uAh | 90.294 mA |

Both arms ended at the programmed RTC wake, with no early abort or gauge retry.
Wi-Fi stayed enabled. The trace retained all 11,954 and 12,088 events
respectively, with no nonzero loss statistics, PM callback errors or RPMh
acknowledgement errno. The collectors are inactive with success, RTC alarms
and trace instances are removed, charging resumed, and NFC VEN was restored.
Raw traces, snapshots and private trial scripts remain outside Git.

The 1.455 mA difference is one short sequential pair with intervening charging,
a one-point SOC difference and no matched-temperature replication. It is not
an independently calibrated or stable NFC power cost. The substantive result
is that VEN low still leaves approximately 89 mA gauge-reported consumption,
so an enabled NFC controller does not by itself explain the residual load.
This normal command does not unvote its I/O regulator; it is controller-enable
isolation, not proof that every NFC/eSE rail is electrically unpowered.

Audited `drivers/nfc/nq-nci.c` SHA-256:
`fcd4e82f6ab56da558015d03b382cf322fd902493c60f11dfad2f101dd9daed4`.
The ioctl ABI came from the corresponding locked `nq-nci.h` and
`include/uapi/linux/nfc/nfcinfo.h`. Keep the working kernel constant for further
comparisons. Retained profile mismatch and NFC VEN alone are no longer leading
explanations on the measured baseline; physical capacity, gauge accuracy and
other retained physical loads remain unresolved. No charging/calibration or
permanent NFC policy was changed.


### Short manual-off protocol with uncharged startup samples — 2026-10-08

The operator offered an approximately 15-minute powered-off interval. To avoid
USB recharge masking the return, a finite private sampler was prepared before
manual shutdown. It waits at most 120 seconds for unplug, allows 12 seconds for
USB state settling and saves one before-off sample. Operator instructions are
to unplug, wait 20 seconds, then shut down manually. At return, start on battery,
wait 30 seconds and only then reconnect. The RPMh image is permanent, so no
Fastboot interval or alternate kernel is required.

A next-boot oneshot waits at most 35 seconds for battery availability, saves
three samples at availability, five seconds later and fifteen seconds later,
then removes its one-use marker. The installed diagnostic service has a
60-second start limit and a marker condition; it is not a periodic logger.
It will be disabled and removed after result retrieval. No automatic shutdown,
restart, RTC wake or gauge write is requested. The manual-off interval was
operator-confirmed; its return result is still pending at this checkpoint.

The sampler and offline interpreter are under `userspace/power/diagnostics/`.
Seven local fixtures exercise the deployed sampler's exact mode branches,
including no unplug, reconnect, unavailable battery and USB-connected startup.
Eleven interpreter cases reject confounded USB/status readings, changed learned
capacity/profile/kernel, missing numeric values or an unconfirmed new boot.
The earliest eligible uncharged sample is selected; USB-connected samples
remain evidence but are not used as an uncharged baseline. These are diagnostic
tools, not automatic components of the M1 image.

Shutdown/startup energy, gauge settling and temperature changes remain part of
the comparison. Phone wall time is not a trusted duration reference after an
offline reboot; use operator/host timing and boot elapsed time as well. Even an
eligible pair does not independently calibrate physical current or prove
battery health. A shorter interval can resolve a gross difference but may be
inconclusive for small losses. Raw boot IDs and samples remain private.


### Manual-off return: startup captured, comparison invalid — 2026-10-08

The operator returned after an intended approximately 20-minute off interval.
All three startup samples were taken on battery, with USB offline and status
Discharging, at boot elapsed times 8.23, 13.23 and 23.23 seconds. Each reported
91%, the j11sun_4700mah profile and the installed October 7 RPMh kernel banner.
The learned full capacity was 2,820,000 uAh, compared with 2,822,000 uAh in the
preceding running-boot measurements. This change would also fail the strict
unchanged-capacity comparison guard.

The required before-off file is absent. The previous boot's service journal
shows the finite sampler being stopped during shutdown without its saved-sample
message. The exact reason it did not reach its save point is not established.
Consequently there is no eligible baseline pair, no measured off-state loss or
off-state current, and no battery-health conclusion from this attempt. Startup
charge counters alone must not be compared with a charging endpoint from the
earlier NFC trial. Phone wall-clock timestamps are not used to certify the
off interval.

The return files were retained privately. The next-boot marker was consumed;
the oneshot finished successfully and became inactive. Its enabled link,
service file and temporary executable were removed after retrieval and systemd
was reloaded. Charging was confirmed on return. No new kernel was built or
installed and no gauge calibration was changed. A future attempt must positively
acknowledge the saved unplugged baseline before the operator powers off.


### Daytime unplugged return on the persistent RPMh kernel — 2026-10-08

The operator supplied unplug/replug times of 06:46 and 18:35 Europe/Paris:
11 hours 49 minutes. The first successful return read at approximately 18:37:30
reported 54%, charge counter 1,448,759 uAh, learned full 2,820,000 uAh,
design 4,700,000 uAh, temperature 21.2 C and active charging. The boot identity
matches the morning startup; the October 7 RPMh kernel banner and
j11sun_4700mah profile are unchanged. No intervening reboot was detected.

The morning read after the manual-off test had reported 91% and counter
2,361,292 uAh while charging. The endpoint difference is 37 percentage points
and 912,533 uAh, approximately 77.2 mA if divided by the operator's unplugged
duration. This is indicative, not an exact unplugged current measurement:
the departure endpoint preceded unplug and the return endpoint followed
approximately 2.5 minutes of charging. No uncharged departure sample exists.

The selected kernel journal contains 77 complete deep-suspend pairs, totaling
39,665.4 seconds (about 11 hours 1 minute, 93.24% of the operator's interval).
This sums complete pairs only and may omit boundary-crossing sleep. Journal
realtime timestamps include suspend; journal monotonic timestamps do not and
must not be used as sleep-duration measurements. Wake messages include 76
msoc-delta, one msoc-high and one typec-cc-state-change event. No selected
suspend-failure, watchdog, BUG, Oops or thermal-shutdown message was found.

The substantial discharge persists despite extensive deep sleep. Neither
this result nor the learned-capacity value establishes physical battery health
or independently calibrates the gauge. Radio association and physical battery
condition remain uncontrolled. Raw samples, boot identity and selected journal
events remain private; this observation introduced no logger, setting change,
new kernel build or media acquisition.


### Integrated userspace first boot and Bluetooth readback — 2026-10-09

The operator completed the integrated userspace build with exit status zero,
flashed its Android-sparse userdata and the existing RPMh boot, and confirmed
Mobian startup. The sparse image is 3,645,243,684 bytes and the raw image is
4,551,868,416 bytes. The successful constructor includes sparse-to-raw byte
comparison and filesystem validation; these do not validate every application.

USB SSH works after the operator authorized the existing diagnostic public key.
The running kernel banner matches the retained October 7 RPMh build. The
installed profile marker is present; all three UPower packages report
1.90.9-1+lmi1. UPower, CPU-idle, ADSP/BTFM and pd-mapper services report successful
active states. The ALSA kona-mtp-snd-card is registered and the battery reports
Charging. The sole failed unit in the first check is getty@tty1; its cause has
not been investigated. App usability, audio quality and idle autonomy still
require validation on this newly built userspace.

Bluetooth is software-blocked, its service is inactive and no HCI interface is
present. A reviewed read-only BT_CMD_GETVAL_POWER_SRCS (0xbfb1, 28 integers)
query reports reset and SW_CTRL GPIO values zero. Configured AON, DIG, RFA1,
RFA2 and ASD current slots report -1; other unconfigured slots report -2.
In this exact driver, -1 means its cached enable flag or regulator enable
check is false, not a measured zero voltage/current. No Bluetooth power-control
ioctl or GPIO write was issued. This weakens a Bluetooth-held-on hypothesis
but does not prove that shared supplies or other masters are unpowered.
Raw snapshots and public-key identifiers remain outside Git.


### Integrated userspace short idle observation and clock floor — 2026-10-09

The first idle collection after the integrated-image return was shortened by
an RTC alarm wake. The requested 180-second comparison is **not complete**.
The usable pre-suspend to final unplugged interval is 128.528 seconds, with
0.701 seconds awake (99.455% suspended). The charge counter decreased by
3,084 uAh, yielding a gauge-derived interval average of 86.38 mA. This is a
qualified short observation consistent with the unresolved high idle load,
not a physical current measurement or a completed paired comparison.
The initial Full-to-Discharging counter discontinuity is excluded.

Wi-Fi remained enabled, no media was captured or played, and the return
reported Charging. The collector was inactive with successful cleanup;
the RTC alarm and trace-instance list were empty. The trace had 12,178
entries and no reported per-CPU overruns or dropped events. Parsed pre-suspend
VRM register values, validity masks and contributors matched the retained
trial-12 snapshot. This does not establish identical physical rail states.

The fresh system clock had regressed to April 2026 and NTP was unsynchronized.
The coordinator corrected system time from the host without directly writing
the hardware RTC or gauge. A subsequent bounded alarm-only probe scheduled
181 seconds ahead of the RTC counter and cleared its own alarm. The cause of
the earlier 128-second alarm wake remains unproven.

The integrated recipe had omitted the previously reviewed time-seed profile.
It now stages that profile's existing helper, units and initialization hook,
without maintaining another copy, and initializes a build-time floor inside
the image. The same assets are active on this handset; restore completed
successfully and the save timer is waiting. No reboot was performed to claim
fresh-image or across-reboot validation of this recipe revision. The saved
floor prevents regression below the last saved epoch, not clock drift or
elapsed-time loss while powered off. No new image or kernel build was run.
