# Offline read-control log analyzer

This folder contains a standard-library-only CLI for an already available
`events.jsonl`. It writes a separate JSON analysis file and does not modify its
input. It never opens a device, imports the observer, or contains device paths.
No physical read-control result was available for this delivery.

## Run

From the Mobian repository root:

```sh
python3 -B -X utf8 userspace/power/diagnostics/gauge-read-control-candidate/analyze_read_control.py path/to/events.jsonl path/to/analysis.json
```

The input and output paths must differ. The analyzer retains parse and
structure errors, every `finished` and probe stop reason, and all resume
attempts including incomplete ones. It marks a stream without `finished` as
incomplete and potentially truncated; it never synthesizes a successful end.

A probe is usable only when `complete` is true, the expected mode plan and
label order are present without duplicates, all reads and timestamps are
consistent, USB remains `0`, status remains `Discharging`, and all four
current pre/post values are numeric. `callback_limit_reached` with a complete
probe is retained as complete data and classified separately from an error
stop. Missing, nonnumeric, non-finite, or malformed values are never replaced
with zero.

Current values come from sysfs strings and are reported as signed `uA_sysfs`.
Each value carries the midpoint of its before/after timestamps and the read
duration. Delta means post minus pre; the measurement span is the monotonic
midpoint difference. Results are descriptive distributions by wake reason and
treatment/control mode. Per reason and metric, duration ranges are checked for
overlap between modes; absent mode/data or disjoint ranges are marked
inconclusive. Even an overlap is descriptive only.

The candidate does not record SOC, temperature, or capacity scales; the output
states this explicitly and makes no context pairing claim. It separates the
logger-observed window from the unknown physical unplug-to-replug duration:
the service can stop after eight callbacks before a later replug. No
standby-consumption scalar, p-value, quantization-only threshold, or causal DMA
claim is produced. The 1e-6 second allowance applies only to floating-point
timestamp overlap arithmetic.

## Tests

Tests use synthetic JSON rows and local temporary files only. They verify
parsing, current deltas, timing overlap, incomplete/reconnected attempts,
numeric validation, callback eight, truncation, and input immutability. They
do not establish anything about the handset or gauge.

```sh
python3 -B -X utf8 -m unittest discover -s userspace/power/diagnostics/gauge-read-control-candidate -p 'test_*.py' -v
```

This mission ends once this analyzer, its tests, and this README are delivered.
No earlier task or audit is to be resumed.

## Coordinator review

The coordinator independently checked output from the actual lifecycle engine
with a fake reader: all eight completed callbacks were retained. A stream with
a finished record but no armed record is now malformed, and the CLI rejects
an output hard link to the input so the original evidence cannot be replaced.
There are 13 analyzer tests; the hard-link case runs on native Linux and may
be skipped on hosts that forbid link creation. No physical trace was fetched.
