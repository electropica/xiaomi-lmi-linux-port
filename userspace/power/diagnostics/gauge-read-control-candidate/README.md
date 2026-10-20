# Gauge read-control candidate

## Status

This directory contains an offline candidate for the previously reviewed read-order probe. The lifecycle engine is injectable and has no I/O at import. `read_control.py` and its nine deterministic unit tests are byte-identical copies of the earlier reviewed files; see `provenance.json` for their raw SHA-256 values.

**The Linux `--run` path was not executed.** No service, device, sysfs path, DBus bus, or physical measurement was touched. Running `observer.py` without exactly `--run` exits with an offline-safe message. No service unit or arming script is included.

## Local test command

```powershell
python3 -B -X utf8 -m unittest discover -s userspace/power/diagnostics/gauge-read-control-candidate -p 'test_*.py' -v
```

Result from this candidate: **17 tests passed** (the nine copied module tests plus eight lifecycle integration tests). All readers, clocks, and sinks in both test files are fake; the tests do not open `/sys` or import GI.

## Lifecycle and access ordering

`LifecycleEngine` receives `read_attr`, CLOCK_BOOTTIME, CLOCK_MONOTONIC, epoch, a sink and an optional close callback. `arm()` timestamps and emits metadata only. It does not read USB or battery supplies. The engine then waits for unplug and invokes the probe only from an injected `resume-signal` while observing.

The resume handler captures its entry timestamp before invoking the probe and performs no parent gauge snapshot. This timestamp is kept as the event's boottime/monotonic boundary even though the bounded probe runs immediately afterwards. The probe's first **gauge** read is direct-register `bms/current_now`; its plan then contains SRAM fields. Parent-side work after the probe only emits the returned JSON record and checks clocks; it does not call `counters()` or make another gauge read. A reconnect/error in the probe is persisted with its partial trace and stops the engine without a following snapshot. In the retained Gen4 source, `current_now` reads BATT_INFO_IBATT and its shadow-copy registers directly (`fg-util.c:1014–1053`); `current_avg` and counter getters use the SRAM property path (`qpnp-fg-gen4.c:5239–5241, 5289–5294`; `fg-util.c:628–660`). PM8150B selects DMA for that path (`qpnp-fg-gen4.c:6708–6718`). These are two paths into the same gauge, not independent current meters.

The parent read budget is explicit:

- The awake-only parent poll performs at most one `usb/online` metadata read per poll callback. It is scheduled every five seconds in the GI adapter, and has a total cap of 20,000 parent metadata reads, including one USB read for each observed `prepare-sleep` callback.
- A successful probe has at most 14 logical sysfs property reads; eight attempted callbacks therefore have a maximum of 112 probe property reads. The exact per-read plan, values/errors and before/after epoch, boottime and monotonic stamps are embedded in each resume event.
- No parent SOC, temperature, capacity-scale, or full-supply snapshot follows the probe. Its separate added-read budget is zero. `current_now` can perform up to five paired register attempts internally; a counter getter can perform several SRAM transactions. The logical budgets do not equal bus transactions or energy cost.

The engine stops at unplug-wait expiry (three hours from arm), total expiry (18 hours from arm), USB reconnect, non-Discharging status, reader error, metadata/probe budget, inter-read gap or per-read duration limit, or the eighth attempted natural resume callback. A `finished` event and close callback occur at most once.

## Proposed future integration

1. When a future observer is requested, instantiate this engine in its normal startup path and route `PrepareForSleep` signals to it. Keep the signal callback entry timestamp before any probe work.
2. On resume, call the engine before any existing `record()` implementation that reads gauge attributes. Do not call the old full `counters()` snapshot before the probe. For this candidate, omit the later full snapshot as well; retain only the probe and boundary metadata.
3. If a later task requires SOC, temperature or capacity scales, give those post-window reads a separate explicit count and timestamp budget, perform none after a stop cause, and mark them outside the measured probe window.
4. Use a one-shot service with an outer `RuntimeMaxSec=18h` guard. That unit is a proposal only and was not created. The existing five-second GLib timer runs only while the CPU/event loop is awake; it is not an RTC alarm and does not wake the phone. A three-hour unplug deadline may only be noticed on a later awake callback if the CPU is suspended.
5. Stop through the engine's single finish path on timeout/replug/error; close the log once. Remove the callback integration to roll back; there are no setting writes or persistent device changes in this candidate.

A service-manager `RuntimeMaxSec` is an outer lifetime guard, not a way to interrupt a synchronous sysfs call. The engine detects a slow read only after it returns and will not start the next read. If a read is stuck in uninterruptible kernel D-state, neither the in-process deadline nor a service-manager signal can guarantee immediate termination.

## Limits

This candidate only tests whether `current_avg` changes across a bounded mixed-access window relative to its time-control order. It does not estimate current through suspend, establish DMA causality, or calibrate gauge counters. Eight callbacks cap attempts but do not define a wall duration or guarantee eight usable pairs. T/C durations and wake contexts must overlap before comparison; otherwise report inconclusive. No claim from simulated tests substitutes for later review of a real observer integration.
