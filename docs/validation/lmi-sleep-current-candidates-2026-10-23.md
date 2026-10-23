> **Review correction, October23:** stronger exclusions below are superseded by [the evidence review](lmi-battery-evidence-review-2026-10-23.md). Gauge effects and unobserved kernel/peripheral demand remain open; the retained RPMh differences are WAKE commands, not SLEEP differences.

# The sleep current, after three eliminations and one independent check

## What the rails and the requests show, and what they do not

**The USB rails' requests are released at the unplug.** The connected baseline showed 21 rails requested and
open, among them the three USB rails: `hsphy@88e3000`, `usb30_prim_gdsc`
and `pm8150_l2`, held by the USB stack. The unplug releases their enable
requests, so they are not what the unplugged period keeps alive.

**The GPU core rail is not requested in the unplugged and awake state.** Its parent level, `pm8150a_s3_level`, loses its
enable request at the unplug and the rail is not requested once
unplugged. The candidate that survived the suspend-path comparison,
`gpu_cx_gdsc`, concerns a plugged suspend.

**The always-on set comes from the shared device tree.** `vdd_boost_vreg` and the other rails requested
exclusively by a `deviceless` consumer come from the device tree or the
bootloader, and the device tree is the same on the two platforms. What
remains requested and open once unplugged is the WLAN rails, the CPU
`limits-dcvs` rails, the UFS rails, the codec rail, the camera rails, the
touch rail, the PCIe rail and the DSI PHYs, all with the same kind of
holders on both sides.

**The peripheral sleep requests are identical, and they do not establish the bank states.** The RPMh traffic of a suspend window
is the same on both platforms: the Android trace gives **26 messages, 6
BCM messages, zero valid non-zero**, with the same tcs masks
(5: 12, 2: 12, 56: 2) in each of its four sleep windows, and the Mobian
observer trial gives **26 messages and 6 BCM messages** in its window. The
addresses differ on a handful of registers, in the 0x3xxxx, 0x4xxxx and
0x5xxxx families, which the two kernel revisions
(`a5b3099017ae` on Mobian, `71b13e62f057` on LineageOS) explain. The
The requests are therefore the same on both platforms. That is not a
statement about the materials: the observed sleep-request handshake
carries no decodable bank coordinates on either side, so the ACTIVE, SLEEP
and WAKE state of each bank during the suspend is **unknown on both
platforms**. Identical requests do not prove identical states.

## The independent check on the scale

The night readings carry the gauge's own current, and they agree with
the counter rather than contradicting it. Over the detached period
`current_now` reads 48.8 mA to 330.1 mA, median 87.9 mA, at the sample
instants, and the counter implies about 106 mA over the awake blocks and
33.6 to 57.1 mA over the sleeps. The two agree, which is an internal
consistency of the gauge and nothing more: `current_now` and
`charge_counter` come from the same gauge, so their agreement cannot
calibrate either of them, and it says nothing about the absolute scale.

The scale was then compared with something that is not the gauge. The
USB supply exposes `input_current_now`, and the battery exposes its own
current, so the phone's own consumption can be computed from the power
path: 460 mA in from the cable at 5.04 V, 289 mA into the battery at
4.47 V, that is **2.32 W in, 1.29 W to the battery, about 1.03 W for the
phone itself**, while plugged and awake. The gauge's figures for the
same phone, 193 mW during a sleep and 456 mW while awake and unplugged,
are of the same order as that 1.03 W. The check says the two are not
separated by orders of magnitude; it does not calibrate the gauge. The
1.03 W is the difference of two powers that include the conversion
losses, the USB-PD path and the cable, and the load varies with the
charge current, which was tapering. **A plugged snapshot does not
calibrate the current during the suspend.**

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

The sleep rate difference is not explained by the requests, by the
always-on set or by the wake frequency. What is left is what the kernel
traces do not show:

* the **state the resources are left in**: the requests are identical on
  the two platforms and the driver is byte identical, but a SLEEP request
  is cached and only transmitted in the ACTIVE_ONLY state, so the request
  log cannot say whether a resource actually went to sleep;
* the **modem's own behaviour**: the RPMh request that puts the modem to
  sleep is identical on the two platforms, but what the modem does with
  it is in its firmware;
* the **APSS's deeper states**: the same requests, a different internal
  sleep configuration;
* the **gauge's own consumption** during the sleep, its comparator and
  its ESR detection staying armed;
* and the **scale** of the two gauges, which the USB check supports but
  does not establish.

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

**Read the state the resources are left in, on both platforms, instead
of the requests.** The RPMh master has three request states, ACTIVE_ONLY,
SLEEP and WAKE_ONLY, and it caches the SLEEP and WAKE_ONLY requests to
send them when the state is ACTIVE_ONLY
(`drivers/soc/qcom/rpmh.c`, the exact revision `a5b3099017ae`, byte
identical between the two platforms). A request that was made is
therefore not proof that the resource was put to sleep: if the system
goes down before the cached request is flushed, the resource stays
ACTIVE, and the request log still shows the SLEEP request.

The instrument is the `rpmh-master-stats` device,
`b221200.qcom,rpmh-master-stats`, which appears in both traces and is the
master's own statistics. Two things have to be closed in order: what that
device exposes, since its driver was not located in the files fetched from
this revision, and whether what it reports is the state that decides the
consumption. On Mobian the reading is one `cat`, taken by the phone itself
because the phone is only reachable over the cable; on LineageOS the same
reading needs the OS switch, which is already planned.

If that device turns out not to expose the per-resource state, the next
smallest thing is the suspend-path regulator trace of the **current**
Mobian build, with the observer method of 12 October, whose Android
counterpart is already kept. That comparison would also settle the one
observed difference in the suspend paths, `gpu_cx_gdsc`.

## Limits

* One night, one build, one device, one state of charge at the start.
* The agreement between `current_now` and `charge_counter` is an internal
  consistency of the same gauge, not a calibration of it.
* The USB power check is a plugged and awake snapshot: the difference of
  the two powers includes the conversion losses and a variable load, and
  it does not calibrate the current during the suspend.
