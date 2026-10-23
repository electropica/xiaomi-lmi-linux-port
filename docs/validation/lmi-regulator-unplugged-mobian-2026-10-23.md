> **Review correction, October23:** stronger exclusions below are superseded by [the evidence review](lmi-battery-evidence-review-2026-10-23.md). Gauge effects and unobserved kernel/peripheral demand remain open; the retained RPMh differences are WAKE commands, not SLEEP differences.

# The Mobian regulator requests, connected and unplugged: what the unplug releases

## What was observed

Three summaries of the regulator framework, taken by the phone itself, on
2026-10-23: the connected baseline at 04:49:51 UTC, and the unplugged
state at 04:59:02 UTC (+30 s after the unplug) and 05:01:32 UTC (+180 s).
The phone has no Wi-Fi address and is only reachable over the cable, so a
reading taken from outside would vanish at the unplug; the phone takes its
own snapshots. The two unplugged snapshots are identical to each other:
the state settled within thirty seconds.

The connected baseline has **21 rails requested and open**. The unplugged
state has **16**.

## What the unplug releases

Six rails lose an enable request at the unplug, with their open
references and their consumer lists unchanged:

| rail | use | open | what it is |
|---|---|---|---|
| `hsphy@88e3000` | 1 -> 0 | 3 -> 3 | the USB high-speed PHY |
| `usb30_prim_gdsc` | 1 -> 0 | 2 -> 2 | the USB 3.0 primary PHY |
| `pm8150_l2` | 2 -> 0 | 3 -> 3 | the USB-PD rail |
| `pm8150_l12` | 1 -> 0 | 2 -> 2 | the high-speed PHY's rail |
| `pm8150a_s3_level` | 1 -> 0 | 5 -> 5 | the level that carries the GPU core rail |
| `pm8150_l5` | 2 -> 1 | 7 -> 7 | the DSI, PCIe and UFS memory rail |

**The USB rails' requests are released at the unplug.** The three
USB rails were the most plausible candidate in the connected baseline,
because they are requested while the cable is plugged and are held by
the USB stack. The unplug releases their enable requests, so the USB
stack is no longer among the requesters in the state observed. That is
a statement about the requests: it does not physically exclude the USB
blocks from drawing, because a request state and a material state are
different things, and both readings were taken while the processor was
up.
**The GPU core rail is not requested once unplugged either.** Its
parent level, `pm8150a_s3_level`, loses its enable request at the
unplug, and the rail itself does not appear among the requested ones.
In the state observed, the unplugged and awake one, the rail is not
requested. That is all this shows about it: the suspend path is a
different code path, and an awake reading does not describe it.
## What stays requested and open once unplugged

`vdd_boost_vreg`, the only rail requested exclusively by a `deviceless`
consumer, and therefore the one that comes from the device tree or the
bootloader and never released. Beside it: the WLAN rails `pm8150_s5`,
`pm8150_s6` and `pm8009_s2`, held by `b0000000.qcom,cnss-qca6390`; the
CPU rails `pm8150_l5_ao` and `pm8150_l12_ao`, held by
`18591000.qcom,cpufreq-hw:qcom,limits-dcvs`; the UFS rails `pm8150_l6`,
`pm8150_l17` and `pm8150a_s8`; the codec rail `pm8150_s4`; the camera
rails `pm8150a_bob`; the touch rail `pm8150a_l1`; the PCIe rail
`pcie_0_gdsc`; `pm8150_l5`, `pm8150a_s3_level_ao` and `regulator-dummy`,
which carries the DSI PHYs.

`vdd_boost_vreg` remains the candidate it was, and it remains excluded
as an explanation: a `deviceless` consumer means the request comes from
the device tree or the bootloader, and the device tree is the same on
the two platforms.

## What this does and does not say

It says that **the USB stack releases its rails at the unplug**, and
that the GPU core rail is not requested in the unplugged and awake
state. It eliminates two candidates for the unplugged period.

It does **not** bound what is held while the processor is down. The
requests and the modes of the rails can change in both directions, so
the suspend state does not follow from an awake unplugged reading. It
does not tell whether the sixteen remaining rails are more than the
reference platform holds, because that needs the same reading there,
and LineageOS and Mobian share the same phone in dual boot: the Android
half waits for an OS change.

And nothing here is an electrical measurement. Every current column of
the summary reads 0 mA, the regulator framework does not report currents
on this platform, and a rail that is requested is not a rail that draws.

## Where the question stands now

**What the rails give, and what they do not.** The USB rails'
requests are released at the unplug, the GPU core rail is not requested
in the unplugged and awake state, and the always-on set comes from the
shared device tree. All three are statements about the **requests**,
observed in an awake state. They narrow what may still be asked; they do
not exclude a difference of consumption. What is left is the behaviour
that is not a rail:
* the **wake frequency**: the Mobian night had 30 gauge wakes, the
  Android night had deep idle periods of one to nine hours. That is a
  duty-cycle cost, about 460 s of grace timers over the night, and it
  cannot explain a sleep current that is about three times higher;
* the **peripheral states and the remote-master votes**, which the
  regulator summary does not show. Both traces carry them: the Android
  one has RPMh commands and the 12 October Mobian observer trials have
  `rpmh-sleep-analysis.json`, so the comparison is available offline
  and needs no OS change;
* the **gauge's own behaviour during the suspend**, which the review
  already pointed at: the ESR handler reads the resistance and may vote
  awake and schedule calibration.

The next step is the second one: compare the peripheral sleep requests
of the two platforms from the traces already kept. The Android point in
time reading stays deferred to an OS change.

## Limits

* One observation, one build, one state of charge.
* The reading is of the requests in the unplugged and awake state.
* The connected baseline was taken while charging, and the unplugged
  ones while discharging, so the battery state differs between them as
  well as the USB.
* The Android half of the point in time comparison is deferred to an OS
  change, the two systems sharing the phone.
