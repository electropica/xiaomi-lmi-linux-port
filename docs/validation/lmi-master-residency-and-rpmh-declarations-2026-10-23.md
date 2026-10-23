> **Review correction, October23:** stronger exclusions below are superseded by [the evidence review](lmi-battery-evidence-review-2026-10-23.md). Gauge effects and unobserved kernel/peripheral demand remain open; the retained RPMh differences are WAKE commands, not SLEEP differences.

# The RPMh declarations and the master residency: what the sources say, what the kept evidence already answers, and the one question left

## What I correct in my own conclusions

**A wrong sentence about the RPMh requests.** I wrote that the SLEEP and
WAKE_ONLY requests "are only sent in the ACTIVE_ONLY state". That is
wrong. `drivers/soc/qcom/rpmh.c` caches every declaration
(`cache_rpm_request()`, line 228) and sends only the ACTIVE_ONLY one
immediately (line 235). The others are **deferred to the next flush**,
and the flush sends each one **with its own state**: the SLEEP
declaration at line 589 and the WAKE_ONLY declaration at line 592. The
comment at lines 212 to 214 says "SLEEP/WAKE_ONLY requests are not sent
to the controller at" this point, that is deferred, not suppressed.

**A wrong sentence about the requests being identical.** The addresses
and the tcs masks are the same on the two platforms, but the **values
are not**. In the four kept LineageOS windows and the one kept Mobian
window, 26 declarations each, the mask 5 declarations differ at two
addresses:

| address | LineageOS | Mobian |
|---|---|---|
| `0x50004` | `0x2018d2bf` | `0x20003e7f` |
| `0x50014` | `0x6018c95f` | `0x60001f3f` |

and the value at `0x50000` **changes between the LineageOS windows
themselves**, `0x60003f55` then `0x6024ca6f`. So these values are
state-dependent, and the difference between the platforms is not shown
to be a policy difference.

**An overstated sentence about `master_stats`.** It is not an
independent electrical accounting. The APSS values are computed in the
kernel from the profiling units, and the other masters' values are read
out of SMEM, where their own firmware wrote them. The durations are in
**architectural counter ticks**, not in seconds.

## The mechanism, traced

`drivers/soc/qcom/rpmh.c`, revision `a5b3099017ae`, byte identical
between the two platforms per the packet manifest.

* The **request state** is one of `RPMH_ACTIVE_ONLY_STATE`,
  `RPMH_WAKE_ONLY_STATE`, `RPMH_SLEEP_STATE` (cases at lines 177, 183,
  189). It is a per-master-state declaration of what a resource should
  be, not a command to transition: the clock driver sends one declaration
  per state, `for (; state <= RPMH_ACTIVE_ONLY_STATE; state++)`
  (`drivers/clk/qcom/clk-rpmh.c` line 133), and the regulator driver does
  the same (`drivers/regulator/rpmh-regulator.c` lines 749, 794, 807).
* Every declaration is cached (line 228) and sets the dirty flag (lines
  180, 186, 192). Only an ACTIVE_ONLY declaration is submitted on the
  spot (line 235).
* `rpmh_flush()` (lines 556 to 601) submits the deferred ones, each with
  its own state (lines 589 and 592), and its documentation says, at
  lines 552 to 554: "This function is always called from the sleep code
  from the last CPU that is powering down the entire system."
* `check_ctrlr_state()` (lines 81 to 87) refuses an ACTIVE_ONLY request
  with `-EBUSY` while the controller is in solver mode.

**The hypothesis of a missing flush is therefore not compatible with the
suspend path that is actually executed**, and it is retired. The flush is
part of the sleep code, by the last CPU powering the system down.

## What the kept evidence already answers

The audit of 2026-10-14 is already in the private area
(`master-residency-audit-20261014-private.json`,
`audit-master-residency-20261014.py`,
`power-counter-master-audit-20261014-public.md`), and it covers a
**current-build** trial, the retained trial 36:

| master | residency over the 721.244 s window | share |
|---|---|---|
| APSS | 720.556 s | 99.90 % of the Linux window, 9.3 ms from the Linux sleep |
| ADSP | 721.271 s | 100.00 %, the 26 ms excess being the sequential reads |

So the APSS and the ADSP were down for the whole interval, and the
question "did a master stay awake" is **already answered for those two**.

Its own limits say what is not answered: "Only APSS and ADSP are present
here; absent firmware records do not establish power-off." The masters
**MPSS, ADSP_ISLAND, CDSP, SLPI, SLPI_ISLAND, GPU and DISPLAY** have no
record in that trial, so their residency during a suspend is **unknown**,
not zero.

## What `master_stats` measures, exactly

`drivers/soc/qcom/rpmh_master_stat.c`, one attribute, `master_stats`,
mode 0444 (lines 216 to 222), on the kobject of the device
`b221200.qcom,rpmh-master-stats`.

The printed fields (lines 119 to 121) are the name, the version, the
sleep count, the last sleep entry, the last sleep exit and the
accumulated duration, for the APSS master first (line 135) and then for
every master of the table at lines 64 to 73: MPSS, ADSP, ADSP_ISLAND,
CDSP, SLPI, SLPI_ISLAND, GPU and DISPLAY, each read from SMEM with
`qcom_smem_get()` (lines 141 to 143) at the smem ids 605 to 613.

* **Provenance.** The APSS values are updated in the kernel by
  `msm_rpmh_apss_master_stats_update()` (lines 156 to 165) from the
  profile units `POWER_DOWN_END` and `POWER_UP_START`. The other
  masters' values are written into SMEM by their own firmware.
* **Unit.** The durations are architectural counter ticks: the print
  function mixes them with `arch_counter_get_cntvct()` (lines 110 to
  112). The retained `rpm_stats.c` gives 19.2 MHz; no fresh CNTFRQ read
  is performed, so the conversion inherits that qualification.
* **Frequency.** The update runs on the power management callback of the
  device, so once per suspend and resume, which is what the trace shows
  as `device_pm_callback_start: msm_rpmh_master_stats`.
* **Update conditions.** The APSS update is rejected when the
  power-profile validity bits are not set, the source describing the
  rejected case as a sequence that did not execute cx-off. **The sleep
  count is therefore not a count of Linux system-suspend cycles.**
* **Overflow.** The count is a `uint32_t`, the durations `uint64_t`
  (header lines 75 to 80). A reboot resets everything, the counters being
  accumulated in a static structure from the driver probe.
* **Scope.** The APSS, and the seven masters that report themselves in
  SMEM, which includes the **GPU** and the **DISPLAY** masters.

## What a good residency would let us conclude, and what it would not

A residency close to the elapsed time for a master would show that the
master was powered down for that share of the interval. It would not
close it as a consumer: it says nothing about the retained votes of
the other resources, about the rail voltages or about the current. It would **not**
exclude the rails: the regulator summary describes requests, the profiling
units describe the power state of a master, and neither is a rail
voltage or a current. The audit says the same: residency "does not
establish rail voltage, retained votes, physical current".

## The one question left, and the minimal control

**The question**: what is the residency of the masters the 14 October
trial did not cover, the **GPU master** in particular, during a suspend?
The GPU core rail is the one rail where the two suspend paths differ
observably, LineageOS disabling `gpu_cx_gdsc` and Mobian not, and the
declarations at `0x50004` and `0x50014` differ between the platforms,
even if state-dependently.

**The control is withdrawn.** The counters are not populated on this
phone: the firmware writes no SMEM record for the GPU, the DISPLAY, the
SLPI, the CDSP, the MPSS or the islands, so a further unplugged interval
would produce the same two masters and would not measure the residency
of the GPU master. The reasoning and the references are in
`docs/validation/lmi-master-counters-availability-2026-10-23.md`. Two tools are
prepared and validated off-device, `master-stats-once.py` for Mobian and
`master-stats-once.sh` for LineageOS, in the private area. They print the
attribute verbatim with the wall time and the uptime, they read one file,
they do not poll, they do not wake anything, they read no register and
they change no setting. The validation ran them against a fixture and
checked the output, the missing-path case, that there is no write open and
no polling loop.

The protocol rules, from the audit and not optional: the **displayed**
duration already includes a running sleep, so the pair must be
differenced as printed and must record whether a master was asleep at
each read; the durations are ticks at 19.2 MHz per the retained source
and not a fresh CNTFRQ read; the counters are reset by a reboot, so no
reboot may happen inside a pair; and a master absent from the output is
not reported, not off.

**The next discriminating question** is now a single read of
`master_stats` on LineageOS, at the next boot: it needs no unplug, no
test and no change, and it answers whether the reference firmware
reports the masters that ours does not. If it does, the residency
comparison becomes possible at all.:
the two differing declarations, captured on the **current** Mobian build
with the observer method of 12 October, whose LineageOS counterpart is
already kept. The 12 October Mobian trace is from an older build, so it
cannot settle a difference that the build itself could explain, and the
comparison must be state-controlled, since the same register varies
between the LineageOS windows.

## Limits

* One Mobian window in the declaration comparison, from 12 October and
  not certified to be the current build, against four LineageOS windows
  from 2026-10-07.
* The declarations are state-dependent, so a difference in the values is
  not a difference in policy.
* The residency evidence of 14 October covers the APSS and the ADSP only.
* The factor of about 3.4 between the platforms remains a difference of
  gauge readings, not an established electrical measurement, and the
  counter scale question is the one the 14 October audit already names:
  a qualified distinction between the internal gauge normalization and
  the retained peripheral demand.
* Nothing was measured on a handset for this note, and nothing was
  changed on either system.
