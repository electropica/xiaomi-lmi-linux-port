# Grouped minimal-scope standby observation — October 20, 2026

## Result

The grouped shutdown did **not demonstrate a reduction in the late filtered
gauge-current samples**: the three unplugged resume samples after 30 minutes
were 48.933, 49.061 and 49.040 mA, median 49.040 mA. This resembles the earlier
quiet-night filtered level around 49.3 mA; it is not a matched causal A/B or
an independent battery-current measurement.

The observed stable-unplug window lasted 3,714.954 seconds, with 3,564.957
seconds accounted as suspended (95.96% of that whole window, including the
initial awake delay and natural wake gaps). There were six natural msoc-delta
resumes before the USB return. Displayed capacity went from 100% to 96%.
The same boot was retained; no accounting-clock warning was produced.

Six adjacent unplugged, discharging prepare/resume brackets with at least 99%
suspend residency cover 3,160.080 seconds. Their differently modeled estimates
were:

| Gauge output | Counter-derived average |
|---|---:|
| Software charge counter | 86.71 mA |
| Shadow charge counter | 85.60 mA |
| Nominal-scaled raw charge counter | 85.99 mA |

These are not three independent ammeters. The filtered resume samples are
endpoint values, not integrated interval current. The software-counter rate
differs from earlier lower-SOC nights, while the nominal-scaled raw level
remains close to its earlier ~86 mA level. Initial SOC was 100%, temperature
21 C and learned capacity 2686 mAh, versus 2710 mAh in the earlier reference.
Temperature fell to about 18.2 C. Those SOC, model-scale, temperature and
charging-history differences prevent claiming a physical consumption increase
or saving from the historical comparison. USB-return charging endpoints were
excluded from discharge accounting.

## Actual intervention and limits

At arming, Wi-Fi was disabled and both exposed rfkill entries were blocked;
Bluetooth was already blocked beforehand. PipeWire services/sockets,
WirePlumber, the filter-chain service and the camera volume monitor were
stopped. No process held a camera capture or ALSA PCM device at the check.
The vibrator received an activate=0 stop request; ordinary notification LED
triggers/output and lamp switches were commanded off. Location remained
disabled (it already was), and the previously inactive GeoClue service was
temporarily runtime-masked. No IIO sensor proxy was loaded.

This is a grouped software-control experiment, not proof every component was
electrically isolated. NFC has no exposed rfkill here and was not demonstrated
off. Neither GNSS/SSC firmware, gyroscope/magnetometer hardware nor every
camera/audio rail was demonstrated off. Unit and client state was checked at
arming; it was not sampled continuously throughout suspension. Critical power,
thermal, charging and calibration protections were not changed. The NPU
standby fix remained installed.

Automatic suspend temporarily used a 60-second inactivity delay, rather than
900 seconds. There was no scheduled RTC wake and no audio/video capture.
After the explicit reconnect the observer was inactive with Result=success.
The 900-second delay, enabled Wi-Fi, prior Bluetooth block and previously
active audio/monitor services were restored. GeoClue was verified unmasked,
location retained its original false setting, the RTC alarm was empty, the
phone was charging, no NPU recovery state remained, and all seven checked
torch/switch brightness requests were zero. Original evidence SHA-256:
`950db6cc02b588c43de897cf408f72661149e3b1b7038e00f0995fca9af25122`.

## Follow-up: unbound charge-pump child

The running configuration has `CONFIG_MFD_I2C_PMIC=y` but
`CONFIG_SMB1390_CHARGE_PUMP_PSY` disabled. Both settings match the retained
official Lineage boot configuration. The `qcom,smb1390-slave` child is created
but unbound, no SMB1390 platform driver is registered, and there is no cp_slave
power supply. This is not a demonstrated Mobian-only missing-driver difference.

The parent DT node lacks interrupt-controller. In the reviewed
`drivers/mfd/qcom-i2c-pmic.c`, that condition jumps directly from regmap setup
to child population, bypassing the hardware interrupt/status initialization.
Consequently the successful parent-probe journal line is not a hardware
presence test. The disabled child's source contains a separate hello read in
its slave probe; it was not executed for this follow-up. No bus probe, register
transaction, driver bind or kernel change was requested. The inventory alone
does not justify enabling a driver or asserting that a physical SMB1390 is
fitted and consuming power.

## Interpretation

The observed filtered level persists after the applied group of software
controls. This reduces the value of repeating the same audio/Wi-Fi/lighting
shutdown without a new causal condition. It does not exclude unisolated
peripherals or resolve the discrepancy between modeled counters and filtered
current. No residual-drain fix or cause has been demonstrated.

See the [peripheral checklist](lmi-standby-peripheral-checklist-2026-10-20.md)
and [getter qualifications](lmi-read-control-getter-review-2026-10-20.md).
