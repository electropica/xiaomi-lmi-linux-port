# Collector revision 3: the review of 2026-10-22, checked against the sources

## Why

The independent API review of 2026-10-22 confirmed five defects in
revision 2 of `userspace/power/diagnostics/collect-matched-standby-window.py`
and rejected several of its claims. The review results are kept outside the
repository, in `work/MINIMAX-API-REVIEW-RESULTS-20261022.md`.

The collector is the only instrument that can produce a Mobian window
figure comparable to the LineageOS reference, so a defect in it is a
defect of the measurement itself. This note records what was checked
against the sources, what was changed, what the tests show, and what is
still unknown.

## The sources were checked, not taken on trust

The UFS finding was checked against the exact sources kept in
`work/minimax-api/packets/exact-power-sources/`, whose manifest records
the origin, the size and the SHA256 of every file.

* `drivers/scsi/ufs/ufs-sysfs.c`, Mobian revision `a5b3099017ae…` and
  Android revision `71b13e62f057…`, byte-identical between the two
  revisions, sha256
  `3e5307ab1eea1014f61da4e04a34a2cd53b246ba018fd14d11482658960352dc`.
  Lines 711-726 define the macro:

  ```
  #define UFS_ATTRIBUTE(_name, _uname)
      ...
      pm_runtime_get_sync(hba->dev);
      ret = ufshcd_query_attr(hba, UPIU_QUERY_OPCODE_READ_ATTR, ...);
      pm_runtime_put_sync(hba->dev);
  ```

  `current_power_mode` (line 729) and `psa_state` (line 742) instantiate
  that macro.
* `drivers/scsi/ufs/ufshcd.c`, sha256
  `cc3b00465c2cf0f096521d010150fb87b248119670fe8ed259eea4e56f38594e`,
  line 4229: `ufshcd_query_attr` is documented as "API function for sending
  attribute requests".

So each read of those two attributes runtime-resumes the UFS device and
sends a hardware query. It is not a passive observation of a sleeping
device.

The removal does not go further than the defect. The attributes that stay
in the sampling loop are not hardware queries: `power_mode_show` in the
Mobian `ufs-qcom` copy (sha256
`5914361ac55598d1e2ffb6105bbe161d93536aba7144310cc67cb94d400ac739`) formats
the cached `hba->pwr_info` structure, `clkgate_enable` is a platform knob
written by `init.qcom.power.rc` (line 74, sha256
`86780f04dd6da0161165997240610bd10951dec41beee142034fc4626ff37669`) and not
a UFS query, and `power/runtime_status` is the runtime PM state of the
device.

What stands of the review's own qualification: this does not prove that
ordinary polling wakes the suspended system CPU, and it does not prove
that these reads explain the historical battery drain.

## The five defects, fixed

1. One pair of samples could carry a suspend gap or a USB transition, not
   both. The presence of a suspend skipped the transition handling, so a
   detach that happened inside a suspend interval was lost, with the
   counter readings on both sides of it, and the collector could not stop
   on the reconnection either. The two detections are now independent and
   both are kept.
2. The event log was bounded by dropping events. A saturated log could
   hide the terminal transition, and the suspended total was the sum of
   the surviving events, so a full log also shortened the measured sleep.
   The retained log now keeps the most recent events, the USB transitions
   have their own bounded list, and the totals live in counters that do
   not depend on the log.
3. `deadline_utc` printed a boot-clock value through `gmtime()`, which
   produced a date in 1970. The deadline now carries an explicit
   boot-clock value and a wall-clock value obtained by pairing the two
   clocks at start.
4. The result was written only when an event happened, and the write was
   not atomic: an interrupted run could leave nothing behind or a
   truncated file. The result is now written before the first event, every
   write is atomic, and SIGTERM and SIGINT write the final result.
5. The two UFS hardware-query attributes were read on every poll. They are
   no longer read during the window. A one-shot snapshot is available
   behind `--ufs-hardware-snapshot`, and it says what it is.

## The claims that were rejected, corrected

* Both clocks are derived from adjusted monotonic time, so neither is
  exempt from the timekeeping adjustments, and two sequential reads carry
  a sampling skew. The collector uses only the change of the difference
  between two readings, never the difference itself.
* A normal timer is not a wake source that would prevent a system
  suspend. The polling still costs energy and perturbs the device under
  study, which is what the limits now say.
* The USB boolean is a proxy. Transport, power and charge are reported
  apart, and only a reading taken with no power source attached is kept
  as a discharge endpoint.
* The difference across the unplug mixes consumption and any
  discontinuity. It is not a pure discontinuity and not a consumption
  figure. The field is now named `difference_across_unplug_uah`, and the
  note next to it says so.
* The result does not claim to keep every sample. It keeps a bounded
  sequence of the readings taken while detached, and it reports how many
  were kept and how many were dropped.

## The tests

`userspace/power/diagnostics/test-collect-matched-standby-window.py` now
holds 28 tests. The collector under test is selected by the
`MINIMAX_COLLECTOR` environment variable, so the same suite can be run
against the previous revision, taken from the repository history.

* against revision 2 (`32bc1c2c73d2c620ebef59afaa69deb7c9ffbd3f88474cd67ffa710f3b67e095`,
  the commit `94d20a8`): **28 tests, 13 failures**, and every failure is
  one of the confirmed defects.
* against revision 3 (`67d0dca6250f6f587b90b70decdbc9d3bafeefd51f86da56cd8ef34e0d44cfb7`):
  **28 tests, 0 failures**.

Both runs are kept outside the repository, as
`collector-tests-before-fix-rev2.txt` and `collector-tests-after-fix-rev3.txt`.
The other suite, `test-ufs-policy-reader.py`, still passes with 10 tests.

No test is a mirror of the implementation: each one drives the module with
synthetic samples and checks an observable. The persistence tests run the
command line in a temporary directory and read the file it leaves behind.

One test of the previous revision was extended rather than replaced:
`test_event_sequence_is_bounded` now also checks the total count, because
the retained list alone could no longer prove that nothing was lost.

## What was not touched

The ESR IRQ, the charge protections, the normal sleep delay and the Phosh
and GSD thresholds are unchanged. The `50000` threshold is **50 ms, not
50 s**: `lmi_sleep_total` counts microseconds, and the threshold was not
modified on the strength of a unit misreading. No RTC wake alarm was
added to the device. No policy, setting or permission was changed, and no
kernel code was modified.

## The armed run, and what it did and did not produce

A revision-2 collector was started on the phone at 17:08:10 UTC to catch
a second window. It ran its full hour and stopped on its own deadline at
18:08:13 UTC, writing its JSON, kept outside the repository as
`standby-window-idle-hour-20261022T180813Z.json`.

It produced **no window**: the cable was never removed. The phone stayed
plugged in and charging and **did not suspend for a single second** in
the hour, so `suspended_seconds_total` is 0 and the accumulated suspend
time did not move (436.2216 s before and after, the value carried over
from the first window). The counter went from 2676996 to 2677000, that is
up to `charge_full`: one more observation of the same behaviour, the
counter is remaining charge and it rises back while charging.

That run also shows the perturbation of defect 5 in the open: it read
`current_power_mode` and `psa_state` on every poll for an hour, each read
runtime-resuming the UFS device.

## Limits

* Revision 3 has not run on a handset yet. Nothing about the physical
  standby draw follows from this work.
* The window remains a gauge reading. No calibrated current is measured
  on either platform, and the scale of the counter against the design
  capacity is still not established.
* Removing the two UFS queries means the window no longer reports a live
  UFS power mode. That is the point: the value could not be read without
  changing the state it was supposed to describe.
* The first window is still void as a collector result. Its kernel-log
  analysis stands on its own.
* On the sleep duty cycle: with a 900 s inactivity delay, a 1554.1 s
  unplugged interval could reach at most (1554.1 − 900)/1554.1 ≈ 42.1 %
  asleep if the delay had started at the unplug. The observed sleep was
  436.222 s, about 28.1 %, that is about 217.9 s of awake time beyond
  that hypothetical bound. These are conditional arithmetic, not proof
  that the timer started at the unplug.

## Next

Deploy revision 3 and run the second window: unplug, let the phone
suspend and wake by itself, replug. Then cross-check the collector's
suspend gaps against the frozen gaps of the kernel log, and read the
counter on both sides of the unplug.
