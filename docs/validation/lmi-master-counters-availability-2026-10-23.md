> **Review correction, October23:** stronger exclusions below are superseded by [the evidence review](lmi-battery-evidence-review-2026-10-23.md). Gauge effects and unobserved kernel/peripheral demand remain open; the retained RPMh differences are WAKE commands, not SLEEP differences.

# The master counters: what exists, what is missing, and the one cheap reading left

## Why this note

The previous note proposed reading `master_stats` before and after an
unplugged interval, to compare the residency of the masters that the
14 October trial did not cover. That proposal was made before checking
whether those counters are populated at all. This note does the check,
with the kept evidence and the exact sources, and withdraws the proposal
if it cannot answer the question.

## What the driver expects, what the firmware reports, what our phone shows

**The driver expects nine masters.**
`drivers/soc/qcom/rpmh_master_stat.c`, revision `a5b3099017ae`, byte
identical between the two platforms per the packet manifest. It prints
the APSS master's own statistics first (line 135) and then every entry
of its table (lines 64 to 73): MPSS, ADSP, ADSP_ISLAND, CDSP, SLPI,
SLPI_ISLAND, GPU and DISPLAY, each read from SMEM with
`qcom_smem_get()` (lines 141 to 143) at the smem ids 605 to 613.

**The firmware reports two of them.** The raw snapshots of the retained
trial 36, in `claude-coverage-review-20261014-private.json` under
`retained_trial36_master_snapshots`, hold exactly two masters in every
snapshot, before the initial suspend and at the end:

```
APSS: Version 1, Sleep Count 1454036, Sleep Last Entered At 2710484185614,
      Sleep Last Exited At 2710486237174, Sleep Accumulated Duration 2558056407330
ADSP: Version 1, Sleep Count 19118, Sleep Last Entered At 2710461684664,
      Sleep Last Exited At 2710461666999, Sleep Accumulated Duration 2704067484291
```

The five fields are the ones the show function prints, lines 119 to 121:
the name, the version, the sleep count, the last sleep entry, the last
sleep exit and the accumulated duration.

**So GPU, DISPLAY, SLPI, SLPI_ISLAND, ADSP_ISLAND, CDSP and MPSS are
not reported on our phone, because the firmware writes no SMEM record
for them.** The reader skips a master whose SMEM read returns nothing;
it is not a failed read and not a read of zeros.

**A new unplug cannot change that.** The counters are cumulative since
the driver probe and are reset only by a reboot, so a further
unplugged interval would produce the same two masters. **The proposed
master_stats control is therefore withdrawn**: it would not produce the
missing records, and it would not have measured the residency of the GPU
master in the first place.

**There is no LineageOS capture to compare the availability with.** The
reference packet contains the script that reads the path,
`policies-start.sh` and `policies-return.sh`, which include
`/sys/kernel/debug/rpm_master_stats`, but the kept `start.json`,
`return.json` and `lineage-menu-night-20261022-return-private.json`
contain no master statistics block. The availability of the masters on
the reference platform is therefore **unknown**, and it is the one
thing a single read there would settle.

## The scope of what a residency does and does not establish

The 14 October audit is explicit, and my previous wording was too
strong. A residency close to the elapsed time shows that the master was
powered down for that share of the interval. It does **not** show a
complete electrical shutdown of the subsystem: the retained votes of the
other resources, the clock gating of the domain and the state of the
rails are not covered by a master's power state. It does not show zero
consumption. The audit says the same: residency "does not establish
rail voltage, retained votes, physical current, or coverage of the
latest full-day trial". So the sentence "it closes that master as a
consumer" has to go: it closes the master as a **powered-down remote
processor**, and nothing more.

The same distinction applies to the RPMh flush. There are four different
things, and the previous note mixed them:

* the **intended path**: the documentation of `rpmh_flush()`, lines 552
  to 554, says it is "always called from the sleep code from the last
  CPU that is powering down the entire system";
* the **proof of a call**: the kept traces do show the submissions, the
  `rpmh_send_msg` events, 26 per suspend window on both platforms;
* the **result**: `rpmh_flush()` can return an error, `-EBUSY` while the
  controller waits for an earlier request (lines 549 to 550), and the
  per-command sends at lines 589 and 592 can fail and return early;
* the **material effect**: that the controller was told, and what the
  hardware did with it. A submission in the trace is not the material
  state.

The "missing flush" hypothesis has no support in any of the four, and it
is not reintroduced.

## The RPMh differences cannot be decoded with our evidence

The two declarations that differ between the platforms sit at `0x50004`
and `0x50014`, inside the `0x50000` to `0x5ffff` block, and the third
address, `0x50000`, **changes between the LineageOS windows
themselves**, `0x60003f55` then `0x6024ca6f`. The values are therefore
state-dependent, and a difference of values is not shown to be a
difference of policy.

Decoding them is not possible from what we hold. The tree of this exact
revision contains no TCM or TCS register map: the files matching "tcm"
are the Trusted Computing Module, the touch controller, the USB gadget and
the s390 iSCSI ones. The RPMh client in `drivers/soc/qcom/rpmh.c` builds
and submits the commands but does not decode their payloads; the meaning
of the fields and the meaning of the addresses belong to the AOSS Traffic
Channel Manager, which is firmware, not kernel source.

**The missing datum is therefore the AOSS TCM register map and the
semantics of the fourteen-bit fields.** Without it, no attribution of
`0x50004` or `0x50014` to a resource or to a policy is possible, and
none is made here.

What can be compared: the structure. Same addresses, same tcs masks,
same number of declarations per window, one differing value in two
registers, and one register that varies between windows of the same
platform. The Mobian side is a single window, from 12 October, on a
build that is not certified to be the current one, so the comparison
cannot separate a build difference from a policy difference.

## Decision table

| question | existing evidence | permitted conclusion | remaining unknown | next discriminating action |
|---|---|---|---|---|
| Did the APSS and the ADSP stay down during a suspend? | 14 October audit, trial 36: APSS 99.90 % of the Linux window, ADSP 100.00 % | They were down for that interval, on both | Nothing for those two masters | none, already exploitable |
| Was the GPU, the DISPLAY or the SLPI master down? | The same trial reports only APSS and ADSP | **Unknown, not zero**: the firmware writes no SMEM record for them | Their residency, and why the firmware does not report them | **One read of `master_stats` on LineageOS**, to see whether the reference firmware reports more masters. One `cat`, no unplug, no test |
| Was the RPMh SLEEP declaration flushed at each suspend? | The comment says the flush is called by the sleep code; the traces show the submissions | The submissions are observed in the traced cycles; a comment is not a proof of a call, and a submission is not a material state | Whether the controller applied it at every cycle | none worth a new test |
| Do the platforms declare different resources to sleep? | Two differing values, one varying register, one old-build Mobian window | Not decidable: the values are state-dependent and the decoding is missing | The TCM register map and the field semantics; a state-controlled comparison | only if a state-controlled capture becomes cheap, with the 12 October observer method |
| Is the 3.4 difference a gauge normalisation artefact? | The 14 October audit: the raw and software estimates of the same Mobian interval differ by the reported capacity ratio, 0.5752324 against 0.5844681 | **No.** Both platforms run the same gauge driver on the same battery and the reference figure is a software figure, like ours, so the normalisation cancels | The absolute scale of the gauge against the design capacity | none |
| What draws the difference while asleep? | The rails, the RPMh requests and the master residency all match or are unobservable | It is not in what the kernel asks for | The behaviour of the firmware and of the domains it leaves powered | only an instrument that can measure a rail or a domain, which the project does not have |

## What is justified now

**One read of `master_stats` on LineageOS, at the next boot.** It needs
no unplug, no test, no change and no wakeup: the reader is already
prepared, `master-stats-once.sh`, one file, one read. It answers the
availability question, which is the only remaining question that this
interface can answer, and if the reference firmware reports the GPU
master, the comparison of the residencies becomes possible at all.

The two readers stay in the private area. The Mobian one is not needed
for that reading, the Mobian side being already known; the LineageOS one
is the tool for the next boot.

**No other manipulation is justified now.** The unplugged interval that
the previous note proposed is withdrawn, because the counters it would
have read are not populated on this phone.

## Limits

* The availability of the masters on the reference platform is unknown,
  the kept packet having no master statistics output.
* The Mobian declaration comparison rests on one window from 12 October,
  on a build that is not certified to be the current one.
* The TCM register map is not in the kernel sources of this revision, so
  no address is attributed to a resource.
* The factor of about 3.4 remains a difference of gauge readings, not an
  established electrical measurement.
* Nothing was measured on a handset for this note, and nothing was
  changed on either system.
