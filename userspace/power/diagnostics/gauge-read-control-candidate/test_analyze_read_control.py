import copy
import json
import tempfile
import unittest
from pathlib import Path

import analyze_read_control as analyzer


HERE = Path(__file__).resolve().parent


def make_event(mode="treatment", callback_index=0, *,
               values=None, step=0.01, complete=True, stop_reason=None,
               stop_at_label=None, usb_mid="0", status_mid="Discharging",
               event_wake="438 test", start=100.0):
    labels = analyzer.expected_labels(mode)
    values = {
        "usb_pre": "0", "usb_mid": usb_mid, "usb_post": "0",
        "status_pre": "Discharging", "status_mid": status_mid, "status_post": "Discharging",
        "wake_reason": event_wake,
        "current_now_pre": "10000", "current_avg_pre": "-20000",
        "current_avg_post": "-20000", "current_now_post": "10000",
        "middle_charge_counter": "900000", "middle_shadow": "900000",
        "middle_raw": "1200000", "middle_current_now_1": "10000",
        "middle_current_now_2": "10000", "middle_current_now_3": "10000",
        **(values or {}),
    }
    callback = {"epoch": start, "boottime": start, "monotonic": start}
    trace = []
    observed = {}
    t = start
    for label in labels:
        before_t = t
        after_t = t + 0.001
        entry = {
            "label": label, "attribute": label, "path": "synthetic",
            "before": {"epoch": before_t, "boottime": before_t, "monotonic": before_t},
            "seconds_after_callback_start": before_t - start,
            "value": values[label] if values and label in values else {
                "usb_pre": "0", "usb_mid": usb_mid, "usb_post": "0",
                "status_pre": "Discharging", "status_mid": status_mid, "status_post": "Discharging",
                "wake_reason": event_wake,
                "current_now_pre": "10000", "current_avg_pre": "-20000",
                "current_avg_post": "-20000", "current_now_post": "10000",
                "middle_charge_counter": "900000", "middle_shadow": "900000",
                "middle_raw": "1200000", "middle_current_now_1": "10000",
                "middle_current_now_2": "10000", "middle_current_now_3": "10000",
            }[label],
            "after": {"epoch": after_t, "boottime": after_t, "monotonic": after_t},
            "duration_s": 0.001,
        }
        trace.append(entry)
        observed[label] = entry["value"]
        t = after_t + step
        if stop_at_label == label:
            break
    trace = trace[:]
    if stop_at_label is not None:
        complete = False
    probe = {
        "captured": True, "callback_index": callback_index, "callback_start": callback,
        "mode": mode, "plan": [{"label": label} for label in labels],
        "read_budget": 14, "max_interread_gap_s": 0.25, "max_read_s": 0.25,
        "trace": trace, "stop_reason": stop_reason, "complete": complete,
        "observed": observed,
    }
    if complete and stop_at_label is None:
        # Model the candidate's post-capture cap on callback eight.
        pass
    row_time = start - 0.01
    return {
        "event": "resume-signal", "epoch": row_time, "boottime": row_time,
        "monotonic": row_time, "wake_reason": event_wake, "usb": "0",
        "status": "Discharging", "probe": probe,
    }


def make_log(attempts, reason="callback_limit", *, include_unplugged=True):
    events = [{"event": "armed", "epoch": 10.0, "boottime": 10.0, "monotonic": 10.0}]
    if include_unplugged:
        events.append({"event": "unplugged", "epoch": 11.0, "boottime": 11.0, "monotonic": 11.0})
    events.extend(attempts)
    events.append({"event": "finished", "epoch": 30.0, "boottime": 30.0,
                   "monotonic": 30.0, "reason": reason,
                   "control_callbacks_attempted": len(attempts)})
    return events


class ReadControlAnalyzerTests(unittest.TestCase):
    def test_time_only_coherent_treatment_control_is_descriptive(self):
        events = make_log([
            make_event("treatment", 0, start=100.0),
            make_event("control", 1, start=200.0),
        ])
        result = analyzer.analyze(events)
        attempts = result["attempts"]
        self.assertEqual([a["usable"] for a in attempts], [True, True])
        self.assertEqual(attempts[0]["current"]["current_avg"]["delta_uA"], 0.0)
        group = result["descriptive_results"]["by_wake_reason"]["438 test"]
        self.assertEqual(group["duration_overlap"]["current_avg"]["status"],
                         "descriptive_duration_overlap")
        self.assertEqual(result["descriptive_results"]["inferential_statistics"], "none")
        self.assertNotIn("p_value", json.dumps(result))

    def test_synthetic_shift_is_reported_as_distribution_only(self):
        t = make_event("treatment", 0, start=100.0, values={
            "current_avg_pre": "100", "current_avg_post": "300",
            "current_now_pre": "1000", "current_now_post": "1400",
        })
        c = make_event("control", 1, start=200.0, values={
            "current_avg_pre": "100", "current_avg_post": "50",
            "current_now_pre": "1000", "current_now_post": "900",
        })
        result = analyzer.analyze(make_log([t, c]))
        group = result["descriptive_results"]["by_wake_reason"]["438 test"]
        self.assertEqual(group["modes"]["treatment"]["metrics"]["current_avg"]["delta_uA"]["mean"], 200.0)
        self.assertEqual(group["modes"]["control"]["metrics"]["current_avg"]["delta_uA"]["mean"], -50.0)
        self.assertEqual(group["duration_overlap"]["current_now"]["interpretation"], "descriptive_only")
        self.assertIn("not a single standby-consumption estimate", result["limits"][0])

    def test_disjoint_durations_are_inconclusive(self):
        t = make_event("treatment", 0, start=100.0, step=0.002)
        c = make_event("control", 1, start=200.0, step=0.1)
        result = analyzer.analyze(make_log([t, c]))
        comparison = result["descriptive_results"]["by_wake_reason"]["438 test"]["duration_overlap"]["current_avg"]
        self.assertEqual(comparison["status"], "inconclusive_no_duration_overlap")
        self.assertIsNone(comparison["overlap_range_s"])

    def test_single_mode_is_inconclusive(self):
        result = analyzer.analyze(make_log([make_event("treatment", 0)]))
        self.assertEqual(result["descriptive_results"]["global_mode_comparison"],
                         "inconclusive_missing_mode_or_usable_data")
        comparison = result["descriptive_results"]["by_wake_reason"]["438 test"]["duration_overlap"]["current_now"]
        self.assertEqual(comparison["status"], "inconclusive_missing_mode_or_usable_data")

    def test_reconnection_mid_attempt_is_retained_as_incomplete(self):
        event = make_event("control", 1, complete=False, stop_reason="usb_not_disconnected",
                           stop_at_label="usb_mid", usb_mid="1")
        result = analyzer.analyze(make_log([event], reason="usb_reconnected"))
        attempt = result["attempts"][0]
        self.assertFalse(attempt["probe_complete"])
        self.assertFalse(attempt["usable"])
        self.assertEqual(attempt["read_count"], 9)
        self.assertEqual(attempt["stop_reason"], "usb_not_disconnected")
        self.assertIn("usb_not_disconnected", [c["reason"] for c in result["stop_causes"]])

    def test_missing_and_nonnumeric_current_values_are_not_zero(self):
        missing = make_event("treatment", 0, start=100.0)
        del missing["probe"]["trace"][4]["value"]  # current_avg_pre
        nonnumeric = make_event("control", 1, start=200.0, values={"current_now_post": "not-an-int"})
        nonnumeric["probe"]["observed"]["current_avg_pre"] = nonnumeric["probe"]["trace"][4]["value"]
        result = analyzer.analyze(make_log([missing, nonnumeric]))
        self.assertFalse(result["attempts"][0]["usable"])
        self.assertIsNone(result["attempts"][0]["current"]["current_avg"]["pre"]["numeric_value_uA"])
        self.assertEqual(result["attempts"][0]["current"]["current_avg"]["pre"]["numeric_state"], "missing")
        self.assertFalse(result["attempts"][1]["usable"])
        self.assertIsNone(result["attempts"][1]["current"]["current_now"]["post"]["numeric_value_uA"])
        self.assertEqual(result["attempts"][1]["current"]["current_now"]["post"]["numeric_state"], "non_numeric")

    def test_eighth_complete_callback_limit_attempt_is_usable_and_kept(self):
        attempts = []
        for index, mode in enumerate(analyzer.MODE_SEQUENCE):
            reason = "callback_limit_reached" if index == 7 else None
            attempts.append(make_event(mode, index, start=100.0 + index * 10, stop_reason=reason))
        result = analyzer.analyze(make_log(attempts, reason="callback_limit"))
        self.assertEqual(len(result["attempts"]), 8)
        final = result["attempts"][-1]
        self.assertTrue(final["probe_complete"])
        self.assertTrue(final["usable"])
        self.assertEqual(final["stop_class"], "complete_callback_limit_reached")
        self.assertEqual(final["stop_reason"], "callback_limit_reached")
        self.assertEqual(result["stream"]["finished_reason"], "callback_limit")
        self.assertFalse(result["stream"]["possible_truncation"])

    def test_trace_order_and_duplicate_labels_invalidate_attempt(self):
        event = make_event("treatment", 0)
        event["probe"]["trace"][1]["label"] = event["probe"]["trace"][0]["label"]
        result = analyzer.analyze(make_log([event]))
        attempt = result["attempts"][0]
        self.assertFalse(attempt["usable"])
        self.assertTrue(any(issue.startswith("duplicate_trace_labels:") for issue in attempt["quality_issues"]))
        self.assertIn("complete_trace_labels_mismatch", attempt["quality_issues"])

    def test_status_qualification_and_clock_coherence(self):
        bad_status = make_event("treatment", 0, status_mid="Unknown")
        result = analyzer.analyze(make_log([bad_status]))
        self.assertFalse(result["attempts"][0]["usable"])
        self.assertIn("status_mid_not_discharging", result["attempts"][0]["quality_issues"])

        bad_clock = make_event("control", 1, start=200.0)
        bad_clock["probe"]["trace"][0]["after"]["monotonic"] = 199.0
        result = analyzer.analyze(make_log([bad_clock]))
        self.assertFalse(result["attempts"][0]["usable"])
        self.assertTrue(any("clock" in issue or "duration" in issue
                            for issue in result["attempts"][0]["quality_issues"]))

    def test_truncated_trace_cli_keeps_source_unchanged(self):
        partial = make_event("treatment", 0, complete=False, stop_reason="read_error",
                             stop_at_label="current_now_pre")
        partial["probe"]["trace"][-1]["error"] = {"type": "OSError", "message": "synthetic"}
        partial["probe"]["trace"][-1].pop("value", None)
        events = [
            {"event": "armed", "boottime": 1, "monotonic": 1, "epoch": 1},
            {"event": "unplugged", "boottime": 2, "monotonic": 2, "epoch": 2},
            partial,
        ]
        raw = ("\n".join(json.dumps(row) for row in events) + "\n" +
               '{"event":"resume-signal","probe":').encode("utf-8")
        with tempfile.TemporaryDirectory(prefix=".analyzer-test-", dir=HERE) as temp:
            source = Path(temp) / "events.jsonl"
            output = Path(temp) / "analysis.json"
            source.write_bytes(raw)
            before = source.read_bytes()
            self.assertEqual(analyzer.main([str(source), str(output)]), 0)
            self.assertEqual(source.read_bytes(), before)
            result = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(result["stream"]["finished_count"], 0)
        self.assertTrue(result["stream"]["possible_truncation"])
        self.assertEqual(result["stream"]["parse_errors"][0]["error"], "invalid_json")
        self.assertEqual(len(result["attempts"]), 1)
        self.assertFalse(result["attempts"][0]["probe_complete"])
        self.assertFalse(result["attempts"][0]["usable"])
        self.assertTrue(result["errors"])
        self.assertIn("finished_event_missing", result["stream"]["structural_issues"])

    def test_context_absence_and_physical_window_unknown_are_explicit(self):
        result = analyzer.analyze(make_log([make_event("treatment", 0)]))
        self.assertFalse(result["context"]["soc_collected"])
        self.assertFalse(result["context"]["temperature_collected"])
        self.assertFalse(result["context"]["capacity_scales_collected"])
        self.assertEqual(result["observation_window"]["physical_unplug_to_replug_duration"], "unknown")
        self.assertFalse(result["observation_window"]["replug_event_observed"])

    def test_finished_without_start_is_not_structurally_complete(self):
        result = analyzer.analyze([{"event": "finished", "reason": "callback_limit",
                                    "epoch": 1, "boottime": 1, "monotonic": 1}])
        self.assertIn("armed_event_missing", result["stream"]["structural_issues"])
        self.assertEqual(result["stream"]["status"], "incomplete_or_malformed")

    def test_output_hardlink_cannot_overwrite_input_evidence(self):
        import os
        from contextlib import redirect_stderr
        from io import StringIO
        with tempfile.TemporaryDirectory(prefix=".analyzer-test-", dir=HERE) as temp:
            source = Path(temp) / "events.jsonl"
            output = Path(temp) / "alias.json"
            original = b'{"event":"armed"}\n'
            source.write_bytes(original)
            try:
                os.link(source, output)
            except (PermissionError, NotImplementedError):
                self.skipTest("Hard-link creation is unavailable on this host; run on native Linux")
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as error:
                analyzer.main([str(source), str(output)])
            self.assertEqual(error.exception.code, 2)
            self.assertEqual(source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
