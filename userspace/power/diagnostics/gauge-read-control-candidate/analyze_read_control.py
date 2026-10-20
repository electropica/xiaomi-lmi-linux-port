"""Offline JSONL analyzer for read-control logs; importing performs no I/O."""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

# Fixed protocol schema copied from read_control.py. This tool never imports or
# executes the device observer and contains no device paths.
PRELUDE_LABELS = (
    "usb_pre", "status_pre", "wake_reason", "current_now_pre", "current_avg_pre",
)
TREATMENT_MIDDLE_LABELS = (
    "middle_charge_counter", "middle_shadow", "middle_raw",
)
CONTROL_MIDDLE_LABELS = (
    "middle_current_now_1", "middle_current_now_2", "middle_current_now_3",
)
EPILOGUE_LABELS = (
    "usb_mid", "status_mid", "current_avg_post", "current_now_post",
    "status_post", "usb_post",
)
MODE_SEQUENCE = ("treatment", "control", "control", "treatment",
                 "treatment", "control", "control", "treatment")
CURRENT_LABELS = {
    "current_avg": ("current_avg_pre", "current_avg_post"),
    "current_now": ("current_now_pre", "current_now_post"),
}
USB_LABELS = ("usb_pre", "usb_mid", "usb_post")
STATUS_LABELS = ("status_pre", "status_mid", "status_post")
ACCEPTED_COMPLETE_STOPS = (None, "callback_limit_reached", "service_deadline")
CLOCKS = ("epoch", "boottime", "monotonic")
CLOCK_TOLERANCE_S = 0.05


def expected_labels(mode):
    middle = TREATMENT_MIDDLE_LABELS if mode == "treatment" else CONTROL_MIDDLE_LABELS
    return PRELUDE_LABELS + middle + EPILOGUE_LABELS


def finite_number(value):
    """Return (number, state); missing/nonnumeric/nonfinite are never zero."""
    if value is None:
        return None, "missing"
    if isinstance(value, bool):
        return None, "non_numeric"
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        if not value.strip():
            return None, "non_numeric"
        try:
            number = float(value.strip())
        except ValueError:
            return None, "non_numeric"
    else:
        return None, "non_numeric"
    if not math.isfinite(number):
        return None, "non_finite"
    return number, "numeric"


def numeric_stamp(stamp):
    if not isinstance(stamp, dict):
        return None
    values = {}
    for clock in CLOCKS:
        value, state = finite_number(stamp.get(clock))
        if state != "numeric":
            return None
        values[clock] = value
    return values


def midpoint_stamp(before, after):
    left, right = numeric_stamp(before), numeric_stamp(after)
    if left is None or right is None:
        return None
    return {clock: (left[clock] + right[clock]) / 2.0 for clock in CLOCKS}


def _append_once(items, item):
    if item not in items:
        items.append(item)


def _validate_trace_timing(probe, trace, issues):
    callback_start = numeric_stamp(probe.get("callback_start"))
    if callback_start is None and probe.get("captured") is True:
        _append_once(issues, "callback_start_missing_or_invalid")
    previous_after = None
    for index, entry in enumerate(trace):
        if not isinstance(entry, dict):
            _append_once(issues, "trace_entry_not_object")
            continue
        before = numeric_stamp(entry.get("before"))
        after = numeric_stamp(entry.get("after"))
        if before is None or after is None:
            _append_once(issues, "trace_timestamp_missing_or_invalid")
            previous_after = after
            continue
        elapsed_mono = after["monotonic"] - before["monotonic"]
        elapsed_boot = after["boottime"] - before["boottime"]
        if elapsed_mono < 0 or elapsed_boot < 0:
            _append_once(issues, "clock_reversal_during_read")
        if elapsed_boot + CLOCK_TOLERANCE_S < elapsed_mono:
            _append_once(issues, "boottime_monotonic_incoherent_during_read")
        recorded, state = finite_number(entry.get("duration_s"))
        if state != "numeric" or abs(recorded - elapsed_mono) > 1e-6:
            _append_once(issues, "recorded_read_duration_inconsistent")
        if callback_start is not None:
            if before["monotonic"] + 1e-6 < callback_start["monotonic"]:
                _append_once(issues, "read_precedes_callback_start")
            after_callback, state = finite_number(entry.get("seconds_after_callback_start"))
            expected_after_callback = before["monotonic"] - callback_start["monotonic"]
            if state != "numeric" or abs(after_callback - expected_after_callback) > 1e-6:
                _append_once(issues, "callback_relative_timestamp_inconsistent")
        if previous_after is not None:
            if (before["monotonic"] + 1e-6 < previous_after["monotonic"] or
                    before["boottime"] + 1e-6 < previous_after["boottime"]):
                _append_once(issues, "clock_reversal_between_reads")
            gap = before["monotonic"] - previous_after["monotonic"]
            if gap < -1e-6:
                _append_once(issues, "clock_reversal_between_reads")
            max_gap, gap_state = finite_number(probe.get("max_interread_gap_s"))
            if gap_state == "numeric" and gap > max_gap + 1e-6:
                _append_once(issues, "interread_gap_over_limit_in_trace")
        max_read, max_state = finite_number(probe.get("max_read_s"))
        if max_state == "numeric" and elapsed_mono > max_read + 1e-6:
            _append_once(issues, "read_duration_over_limit_in_trace")
        previous_after = after


def _sample_for_label(trace_by_label, label, issues, require=False):
    entry = trace_by_label.get(label)
    if not isinstance(entry, dict):
        if require:
            _append_once(issues, label + "_missing")
        return {
            "label": label, "raw_value": None, "numeric_value_uA": None,
            "numeric_state": "missing", "timestamp": None, "read_duration_s": None,
        }
    raw = entry.get("value")
    numeric, state = finite_number(raw)
    if require and state != "numeric":
        _append_once(issues, label + "_" + state)
    timestamp = midpoint_stamp(entry.get("before"), entry.get("after"))
    duration, duration_state = finite_number(entry.get("duration_s"))
    if require and timestamp is None:
        _append_once(issues, label + "_timestamp_invalid")
    return {
        "label": label, "raw_value": raw, "numeric_value_uA": numeric,
        "numeric_state": state, "timestamp": timestamp,
        "read_duration_s": duration if duration_state == "numeric" else None,
    }


def _attempt_record(row, event_index):
    probe = row.get("probe")
    issues = []
    if not isinstance(probe, dict):
        return {
            "event_index": event_index, "probe_present": False, "captured": False,
            "probe_complete": False, "mode": None, "callback_index": None,
            "wake_reason": row.get("wake_reason"), "read_count": 0,
            "plan_read_count": 0, "stop_reason": None,
            "stop_class": "missing_probe", "usable": False,
            "quality_issues": ["probe_missing_or_not_object"], "current": {},
        }

    captured = probe.get("captured") is True
    complete = probe.get("complete") is True
    mode = probe.get("mode")
    callback_index, callback_index_state = finite_number(probe.get("callback_index"))
    if callback_index_state == "numeric" and not callback_index.is_integer():
        callback_index_state = "non_integer"
    if callback_index_state != "numeric":
        callback_index = None
    else:
        callback_index = int(callback_index)

    trace = probe.get("trace")
    if not isinstance(trace, list):
        trace = []
        _append_once(issues, "trace_missing_or_not_array")
    plan = probe.get("plan")
    if not isinstance(plan, list):
        plan = []
        _append_once(issues, "plan_missing_or_not_array")
    trace_labels = [entry.get("label") if isinstance(entry, dict) else None for entry in trace]
    plan_labels = [entry.get("label") if isinstance(entry, dict) else None for entry in plan]
    duplicates = sorted({label for label in trace_labels if label is not None and trace_labels.count(label) > 1})
    if duplicates:
        _append_once(issues, "duplicate_trace_labels:" + ",".join(duplicates))

    stop_reason = probe.get("stop_reason")
    if mode not in ("treatment", "control"):
        _append_once(issues, "unknown_mode")
        canonical = []
    else:
        canonical = list(expected_labels(mode))
        if plan_labels != canonical:
            _append_once(issues, "plan_labels_mismatch")
    if complete:
        if trace_labels != canonical:
            _append_once(issues, "complete_trace_labels_mismatch")
    elif canonical and trace_labels != canonical[:len(trace_labels)]:
        _append_once(issues, "incomplete_trace_not_plan_prefix")

    if not captured and complete:
        _append_once(issues, "complete_without_captured")
    if complete and stop_reason not in ACCEPTED_COMPLETE_STOPS:
        _append_once(issues, "complete_with_error_or_unknown_stop_reason")

    _validate_trace_timing(probe, trace, issues)

    by_label = {}
    for entry in trace:
        if not isinstance(entry, dict) or not isinstance(entry.get("label"), str):
            continue
        by_label.setdefault(entry["label"], entry)
        if "error" in entry:
            _append_once(issues, "trace_contains_read_error")
    if complete:
        for label in canonical:
            entry = by_label.get(label)
            if not isinstance(entry, dict) or "value" not in entry or "error" in entry:
                _append_once(issues, "complete_trace_has_missing_or_failed_read")
                break
    for label in USB_LABELS:
        entry = by_label.get(label)
        if complete and (not isinstance(entry, dict) or entry.get("value") != "0"):
            _append_once(issues, label + "_not_usb_zero")
    for label in STATUS_LABELS:
        entry = by_label.get(label)
        if complete and (not isinstance(entry, dict) or entry.get("value") != "Discharging"):
            _append_once(issues, label + "_not_discharging")
    if complete and row.get("usb") != "0":
        _append_once(issues, "resume_event_usb_not_zero")
    if complete and row.get("status") != "Discharging":
        _append_once(issues, "resume_event_status_not_discharging")
    if complete and isinstance(by_label.get("usb_pre"), dict):
        if row.get("usb") != by_label["usb_pre"].get("value"):
            _append_once(issues, "resume_event_usb_trace_mismatch")
    if complete and isinstance(by_label.get("status_pre"), dict):
        if row.get("status") != by_label["status_pre"].get("value"):
            _append_once(issues, "resume_event_status_trace_mismatch")

    observed = probe.get("observed")
    if not isinstance(observed, dict):
        observed = {}
        if complete:
            _append_once(issues, "observed_values_missing")
    if complete:
        for label in canonical:
            entry = by_label.get(label)
            if isinstance(entry, dict) and "value" in entry and observed.get(label) != entry["value"]:
                _append_once(issues, "observed_trace_value_mismatch")

    event_wake = row.get("wake_reason")
    observed_wake = observed.get("wake_reason")
    if event_wake is not None and observed_wake is not None and event_wake != observed_wake:
        _append_once(issues, "wake_reason_mismatch")
    wake_reason = observed_wake if observed_wake is not None else event_wake

    if captured and callback_index is None:
        _append_once(issues, "callback_index_missing_or_invalid")
    if callback_index is not None and callback_index < len(MODE_SEQUENCE):
        if mode != MODE_SEQUENCE[callback_index]:
            _append_once(issues, "mode_does_not_match_callback_sequence")
    elif callback_index is not None:
        _append_once(issues, "callback_index_out_of_range")

    current = {}
    for metric, (pre_label, post_label) in CURRENT_LABELS.items():
        pre = _sample_for_label(by_label, pre_label, issues, require=complete)
        post = _sample_for_label(by_label, post_label, issues, require=complete)
        span = None
        pre_stamp, post_stamp = pre["timestamp"], post["timestamp"]
        if pre_stamp is not None and post_stamp is not None:
            span = post_stamp["monotonic"] - pre_stamp["monotonic"]
            if complete and span <= 0:
                _append_once(issues, metric + "_nonpositive_measurement_span")
                span = None
        if complete and (pre["numeric_state"] != "numeric" or post["numeric_state"] != "numeric"):
            _append_once(issues, metric + "_pre_post_not_numeric")
        current[metric] = {
            "unit": "uA_sysfs",
            "delta_definition": "post_minus_pre",
            "pre": pre, "post": post,
            "delta_uA": None, "measurement_span_s": span,
        }

    row_stamp = numeric_stamp(row)
    callback_stamp = numeric_stamp(probe.get("callback_start"))
    if complete and (row_stamp is None or callback_stamp is None):
        _append_once(issues, "resume_or_callback_timestamp_missing")
    if row_stamp is not None and callback_stamp is not None:
        if (callback_stamp["monotonic"] + 1e-6 < row_stamp["monotonic"] or
                callback_stamp["boottime"] + 1e-6 < row_stamp["boottime"]):
            _append_once(issues, "callback_precedes_resume_event")

    usable = (
        captured and complete and stop_reason in ACCEPTED_COMPLETE_STOPS and
        not issues and
        all(current[m]["pre"]["numeric_state"] == "numeric" and
            current[m]["post"]["numeric_state"] == "numeric" and
            current[m]["measurement_span_s"] is not None
            for m in CURRENT_LABELS)
    )
    if usable:
        for metric in CURRENT_LABELS:
            current[metric]["delta_uA"] = (
                current[metric]["post"]["numeric_value_uA"] -
                current[metric]["pre"]["numeric_value_uA"]
            )

    if not complete:
        stop_class = "incomplete_or_stopped"
    elif stop_reason == "callback_limit_reached":
        stop_class = "complete_callback_limit_reached"
    elif stop_reason == "service_deadline":
        stop_class = "complete_service_deadline"
    elif stop_reason is None:
        stop_class = "complete_no_stop_reason"
    else:
        stop_class = "complete_error_stop"

    event_stamp = {clock: row_stamp[clock] for clock in CLOCKS} if row_stamp else None
    return {
        "event_index": event_index, "probe_present": True, "captured": captured,
        "probe_complete": complete, "mode": mode, "callback_index": callback_index,
        "wake_reason": wake_reason, "resume_timestamp": event_stamp,
        "read_count": len(trace), "plan_read_count": len(plan),
        "stop_reason": stop_reason, "stop_class": stop_class,
        "usable": usable, "quality_issues": issues, "current": current,
    }


def _walk_errors(value, location, event_index, errors):
    if isinstance(value, dict):
        error = value.get("error")
        if error is not None:
            record = {"event_index": event_index, "location": location + ".error",
                      "details": error}
            if isinstance(error, dict):
                record["type"] = error.get("type")
                record["message"] = error.get("message")
            errors.append(record)
        for key, child in value.items():
            if key != "error":
                _walk_errors(child, location + "." + str(key), event_index, errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_errors(child, location + "[" + str(index) + "]", event_index, errors)


def _event_diagnostics(events, parse_errors):
    issues = []
    finished_positions = [i for i, row in enumerate(events) if row.get("event") == "finished"]
    if not finished_positions:
        issues.append("finished_event_missing")
    elif any(events[i].get("reason") is None for i in finished_positions):
        issues.append("finished_reason_missing")
    elif len(finished_positions) > 1:
        issues.append("multiple_finished_events")
    if finished_positions and finished_positions[0] < len(events) - 1:
        issues.append("event_after_finished")
    if not any(row.get("event") == "armed" for row in events):
        issues.append("armed_event_missing")
    elif events and events[0].get("event") != "armed":
        issues.append("armed_event_not_first")
    if parse_errors:
        issues.append("malformed_jsonl_rows")
    possible_truncation = not finished_positions or bool(parse_errors) or "event_after_finished" in issues
    return issues, possible_truncation, finished_positions


def _describe(values):
    if not values:
        return None
    return {
        "count": len(values), "min": min(values), "max": max(values),
        "mean": statistics.fmean(values), "median": statistics.median(values),
        "population_stdev": statistics.pstdev(values) if len(values) > 1 else 0.0,
    }


def _group_results(attempts):
    usable = [attempt for attempt in attempts if attempt["usable"]]
    causes = sorted({str(a["wake_reason"]) if a["wake_reason"] is not None else "<missing>"
                     for a in attempts})
    by_cause = {}
    for cause in causes:
        cause_attempts = [a for a in attempts
                          if (str(a["wake_reason"]) if a["wake_reason"] is not None else "<missing>") == cause]
        modes = {}
        for mode in ("treatment", "control"):
            these = [a for a in cause_attempts if a["mode"] == mode]
            valid = [a for a in these if a["usable"]]
            metrics = {}
            for metric in CURRENT_LABELS:
                samples = []
                for attempt in valid:
                    current = attempt["current"][metric]
                    samples.append(current)
                metrics[metric] = {
                    "unit": "uA_sysfs", "delta_definition": "post_minus_pre",
                    "usable_attempts": len(samples),
                    "pre_uA": _describe([s["pre"]["numeric_value_uA"] for s in samples]),
                    "post_uA": _describe([s["post"]["numeric_value_uA"] for s in samples]),
                    "delta_uA": _describe([s["delta_uA"] for s in samples]),
                    "measurement_span_s": _describe([s["measurement_span_s"] for s in samples]),
                }
            modes[mode] = {
                "attempts": len(these), "usable_attempts": len(valid), "metrics": metrics,
            }
        comparisons = {}
        for metric in CURRENT_LABELS:
            t = [a["current"][metric]["measurement_span_s"] for a in cause_attempts
                 if a["mode"] == "treatment" and a["usable"]]
            c = [a["current"][metric]["measurement_span_s"] for a in cause_attempts
                 if a["mode"] == "control" and a["usable"]]
            record = {
                "treatment_duration_range_s": _describe(t),
                "control_duration_range_s": _describe(c),
                "status": None, "overlap_range_s": None,
                "interpretation": "descriptive_only",
            }
            if not t or not c:
                record["status"] = "inconclusive_missing_mode_or_usable_data"
            else:
                low, high = max(min(t), min(c)), min(max(t), max(c))
                if low <= high + 1e-6:
                    # Tolerate floating-point timestamp arithmetic only; this is
                    # not a measurement or quantization threshold.
                    if low > high:
                        low = high = (low + high) / 2.0
                    record["status"] = "descriptive_duration_overlap"
                    record["overlap_range_s"] = {"min": low, "max": high}
                else:
                    record["status"] = "inconclusive_no_duration_overlap"
            comparisons[metric] = record
        by_cause[cause] = {"attempts": len(cause_attempts), "modes": modes,
                           "duration_overlap": comparisons}

    global_mode_counts = {
        mode: {
            "attempts": sum(a["mode"] == mode for a in attempts),
            "usable_attempts": sum(a["mode"] == mode and a["usable"] for a in attempts),
        }
        for mode in ("treatment", "control")
    }
    return {
        "by_wake_reason": by_cause,
        "mode_coverage": global_mode_counts,
        "global_mode_comparison": (
            "descriptive_only_both_modes_present"
            if all(global_mode_counts[m]["usable_attempts"] for m in global_mode_counts)
            else "inconclusive_missing_mode_or_usable_data"
        ),
        "inferential_statistics": "none",
    }


def analyze(events, parse_errors=None, source_info=None):
    parse_errors = list(parse_errors or [])
    structural_issues, possible_truncation, finished_positions = _event_diagnostics(events, parse_errors)
    attempts = []
    stop_causes = []
    errors = []
    for index, row in enumerate(events):
        event = row.get("event")
        reason = row.get("reason")
        if event == "finished" and reason is not None:
            stop_causes.append({"event_index": index, "source": "finished.reason", "reason": reason})
        if event == "resume-signal":
            probe = row.get("probe")
            if isinstance(probe, dict) and probe.get("stop_reason") is not None:
                stop_causes.append({
                    "event_index": index, "source": "probe.stop_reason",
                    "reason": probe.get("stop_reason"),
                })
            attempts.append(_attempt_record(row, index))
        elif row.get("stop_reason") is not None:
            stop_causes.append({"event_index": index, "source": "event.stop_reason",
                                "reason": row.get("stop_reason")})
        _walk_errors(row, "events[" + str(index) + "]", index, errors)

    captured_indices = [a["callback_index"] for a in attempts
                        if a["captured"] and a["callback_index"] is not None]
    seen_indices = set()
    for attempt in attempts:
        index = attempt["callback_index"]
        if not attempt["captured"] or index is None:
            continue
        if index in seen_indices:
            _append_once(attempt["quality_issues"], "duplicate_callback_index")
            attempt["usable"] = False
            for other in attempts:
                if other is not attempt and other["callback_index"] == index:
                    _append_once(other["quality_issues"], "duplicate_callback_index")
                    other["usable"] = False
        seen_indices.add(index)
    if captured_indices and (captured_indices[0] != 0 or captured_indices != list(range(len(captured_indices)))):
        structural_issues.append("callback_index_sequence_gap_or_reordering")
        possible_truncation = True
    for attempt in attempts:
        if not attempt["usable"]:
            continue
        for metric in CURRENT_LABELS:
            current = attempt["current"][metric]
            current["delta_uA"] = (
                current["post"]["numeric_value_uA"] - current["pre"]["numeric_value_uA"]
            )

    unplugged = next((row for row in events if row.get("event") == "unplugged"), None)
    finished = next((row for row in reversed(events) if row.get("event") == "finished"), None)
    replugged = next((row for row in events if row.get("event") == "replugged"), None)
    observed_window = None
    if unplugged and finished:
        u = finite_number(unplugged.get("boottime"))[0]
        f = finite_number(finished.get("boottime"))[0]
        if u is not None and f is not None and f >= u:
            observed_window = {"from": "unplugged_detection", "to": "finished",
                               "seconds": f - u}
    unplug_to_replug_detection = None
    if unplugged and replugged:
        u = finite_number(unplugged.get("boottime"))[0]
        r = finite_number(replugged.get("boottime"))[0]
        if u is not None and r is not None and r >= u:
            unplug_to_replug_detection = r - u

    return {
        "schema_version": 1,
        "source": source_info or {},
        "stream": {
            "event_count": len(events), "finished_count": len(finished_positions),
            "finished_reason": finished.get("reason") if finished else None,
            "structural_issues": structural_issues,
            "parse_errors": parse_errors,
            "possible_truncation": possible_truncation,
            "status": "complete_structurally" if finished_positions and len(finished_positions) == 1
                      and not parse_errors and not structural_issues
                      else "incomplete_or_malformed",
        },
        "stop_causes": stop_causes,
        "errors": errors,
        "attempts": attempts,
        "descriptive_results": _group_results(attempts),
        "context": {
            "soc_collected": False, "temperature_collected": False,
            "capacity_scales_collected": False,
            "context_measurements_paired": False,
            "note": "The candidate records no SOC, temperature, or capacity-scale context; none is inferred or paired here.",
        },
        "observation_window": {
            "unplug_to_finished_detection": observed_window,
            "unplug_to_replug_detection_seconds": unplug_to_replug_detection,
            "replug_event_observed": replugged is not None,
            "physical_unplug_to_replug_duration": "unknown",
            "note": "This is the logger's observed window. It does not establish the physical unplug instant or how long until a later replug when the service stops earlier.",
        },
        "limits": [
            "All current values and deltas are descriptive sysfs samples in uA; they are not a single standby-consumption estimate.",
            "A duration-range overlap only describes comparable observed timing; it does not establish significance or causality.",
            "No p-value, DMA causal claim, or quantization-only decision threshold is computed.",
            "Synthetic tests validate parsing and calculations only, not the handset or gauge behavior.",
        ],
    }


def parse_jsonl_text(text):
    events, parse_errors = [], []
    blank_lines = 0

    def reject_nonstandard_constant(value):
        raise ValueError("non-standard JSON constant " + value)

    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            blank_lines += 1
            continue
        try:
            row = json.loads(line, parse_constant=reject_nonstandard_constant)
        except (json.JSONDecodeError, ValueError) as exc:
            message = exc.msg if isinstance(exc, json.JSONDecodeError) else str(exc)
            column = exc.colno if isinstance(exc, json.JSONDecodeError) else None
            parse_errors.append({
                "line": line_number, "error": "invalid_json",
                "message": message, "column": column,
                "raw_excerpt": line[:300],
            })
            continue
        if not isinstance(row, dict):
            parse_errors.append({
                "line": line_number, "error": "row_not_object",
                "message": "Each JSONL row must be an object.",
                "raw_excerpt": line[:300],
            })
            continue
        if not isinstance(row.get("event"), str):
            parse_errors.append({
                "line": line_number, "error": "event_missing_or_not_string",
                "message": "Each JSONL object must have a string event field.",
                "raw_excerpt": line[:300],
            })
            continue
        events.append(row)
    return events, parse_errors, blank_lines


def analyze_file(input_path):
    path = Path(input_path)
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    events, parse_errors, blank_lines = parse_jsonl_text(text)
    result = analyze(events, parse_errors=parse_errors, source_info={
        "name": path.name, "bytes": len(raw), "ends_with_newline": raw.endswith(b"\n"),
        "blank_lines_ignored": blank_lines,
        "utf8_decode_replacement_used": "\ufffd" in text,
    })
    if result["source"]["utf8_decode_replacement_used"]:
        result["stream"]["structural_issues"].append("invalid_utf8_replaced")
        result["stream"]["possible_truncation"] = True
        result["stream"]["status"] = "incomplete_or_malformed"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Analyze an existing read-control events.jsonl offline."
    )
    parser.add_argument("input_jsonl", help="existing JSONL file")
    parser.add_argument("output_json", help="distinct output JSON path")
    args = parser.parse_args(argv)
    input_path = Path(args.input_jsonl)
    output_path = Path(args.output_json)
    try:
        if (input_path.resolve() == output_path.resolve() or
                (input_path.exists() and output_path.exists() and input_path.samefile(output_path))):
            parser.error("output_json must be a different file from input_jsonl")
        result = analyze_file(input_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                               encoding="utf-8")
    except (OSError, UnicodeError, ValueError) as exc:
        print("analysis failed: " + str(exc), file=sys.stderr)
        return 1
    print("Wrote offline analysis JSON to " + str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
