# The sleep current, after three eliminations and one independent check

## What has been eliminated

**The USB rails.** The connected baseline showed 21 rails requested and
open, among them the three USB rails: `hsphy@88e3000`, `usb30_prim_gdsc`
and `pm8150_l2`, held by the USB stack. The unplug releases their enable
requests, so they are not what the unplugged period keeps alive.

**The GPU core rail.** Its parent level, `pm8150a_s3_level`, loses its
enable request at the unplug and the rail is not requested once
unplugged. The candidate that survived the suspend-path comparison,
`gpu_cx_gdsc`, concerns a plugged suspend.

**The always-on set.** `vdd_boost_vreg` and the other rails requested
exclusively by a `deviceless` consumer come from the device tree or the
bootloader, and the device tree is the same on the two platforms. What
remains requested and open once unplugged is the WLAN rails, the CPU
`limits-dcvs` rails, the UFS rails, the codec rail, the camera rails, the
touch rail, the PCIe rail and the DSI PHYs, all with the same kind of
holders on both sides.

**The peripheral sleep requests.** The RPMh traffic of a suspend window
is the same on both platforms: the Android trace gives **26 messages, 6
BCM messages, zero valid non-zero**, with the same tcs masks
(5: 12, 2: 12, 56: 2) in each of its four sleep windows, and the Mobian
observer trial gives **26 messages and 6 BCM messages** in its window. The
addresses differ on a handful of registers, in the 0x3xxxx, 0x4xxxx and
0x5xxxx families, which the two kernel revisions
(`a5b3099017ae` on Mobian, `71b13e62f057` on LineageOS) explain. The
remote-master requests are therefore not the difference.

## The independent check on the scale

The night readings carry the gauge's own current, and they corroborate the
counter rather than contradicting it. Over the detached period
`current_now` reads 48.8 mA to 330.1 mA, median 87.9 mA, at the sample
instants, and the counter implies about 106 mA over the awake blocks and
33.6 to 57.1 mA over the sleeps. The counter is therefore not a lagging
model of the state of charge: the gauge's own current measurement and its
coulomb count agree.

The scale was then checked against something that is not the gauge. The
USB supply exposes `input_current_now`, and the battery exposes its own
current, so the phone's own consumption can be computed from the power
path: 460 mA in from the cable at 5.04 V, 289 mA into the battery at
4.47 V, that is **2.32 W in, 1.29 W to the battery, about 1.03 W for the
phone itself**, while plugged and awake. The gauge's figures for the
same phone, 193 mW during a sleep and 456 mW while awake and unplugged,
are of the same order. The gauge's scale is therefore plausible, and a
scale error large enough to explain the whole difference is not supported
by this check.

That check has a limit too: it is taken while plugged and awake, a
different state from the unplugged sleep, and the input current includes
the charger's own losses, the USB-PD path and the cable.

## What the night says about the budget

Over the detached period, 28,306 s, the counter fell 369.243 mAh, that is
47.0 mA, against the reference night's 118 mAh over 8.524 h, that is
13.84 mA. The ratio is 3.4, and the night splits it:

| term | Mobian | reference |
|---|---|---|
| rate during the sleep | 33.6 to 57.1 mA, median 45.3 | about 14 mA |
| rate while awake | about 106 mA | of the same order as its sleep rate |
| wake cycles | 30 gauge wakes, 1388 s awake in all | deep idle periods of one to nine hours |
| asleep | 95.1 % | 98.9 % |

The sleep rate is the dominant term. The wake frequency is a duty-cycle
cost: 30 cycles and their grace timers account for a few tens of mAh, not
for hundreds.

## What remains, and what cannot be settled with what we have

The sleep rate difference is not explained by the rails, by the
peripheral sleep requests, by the always-on set or by the wake frequency.
What is left is what the kernel traces do not show:

* the **modem's own behaviour**: the RPMh request that puts the modem to
  sleep is identical on the two platforms, but what the modem does with
  it is in its firmware;
* the **APSS's deeper states**: the same requests, a different internal
  sleep configuration;
* the **gauge's own consumption** during the sleep, its comparator and
  its ESR detection staying armed;
* and the **scale** of the two gauges, which the USB check supports but
  does not establish.

And the structural limit has to be stated: the phone cannot sleep while
it is plugged in, so during an unplugged sleep the gauge is the **only**
instrument available. The Mobian sleep current can therefore be estimated
only through the same gauge whose scale is in question. The comparison
with the reference rests on the fact that both platforms run the same
gauge driver, on the same battery, and report the same full value, which
is a strong argument but not a measurement.

## The one discriminating verification proposed

**Calibrate the gauge's current scale against the USB path, in the
state that matters.** The check above was taken while plugged and awake.
The same check in the state of the measurement would settle whether the
gauge's scale is right: it needs the phone asleep and unplugged, with the
consumption read by something that is not the gauge.

There is one way that does not disturb the measurement and needs no
instrument on the phone: read the gauge's current and counter over a
**known load**. The current is already sampled every five seconds by the
collector during a window, and the phone's own load is known in the awake
phases. Comparing the two over the same window ties the counter's slope
to the gauge's current reading in the state where both are available, and
the remaining uncertainty is only the ratio between the two platforms,
which the same driver and the same battery already make small.

Everything else needs an instrument the project does not have: the
Android point in time reading waits for an OS change, the two systems
sharing the phone.

## Limits

* One night, one build, one device, one state of charge at the start.
* The sleep brackets carry about five seconds of awake time, so the
  per-sleep slope is a slope over the sleep plus that awake time.
* The same `charge_full` on the two platforms does not prove a
  comparable coulomb scale; the USB check supports it, it does not prove
  it.
* The factor of about 3.4 is a difference of gauge readings. It is not an
  established electrical measurement, and the sleep rate itself moves
  during the night, 54.9 to 37.1 mA of median per third.
* The USB check was taken while plugged and awake, and the input current
  includes the charger's losses.
