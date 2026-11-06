import unittest
import tempfile
from pathlib import Path

from collector import ProcessTracker, proc_stat, run_once
from analyze import analyze


def fake_stat(pid, comm, utime, stime, start):
    # Tail starts at field 3 (state); assign fields 14, 15, and 22.
    fields = ["S"] + ["0"] * 19
    fields[11], fields[12], fields[19] = str(utime), str(stime), str(start)
    return f"{pid} ({comm}) " + " ".join(fields)


class ProcStatTests(unittest.TestCase):
    def test_comm_with_spaces_and_right_paren_and_starttime(self):
        pid, comm, ticks, start = proc_stat(fake_stat(4242, "worker ) helper", 21, 8, 9876))
        self.assertEqual((pid, comm, ticks, start), (4242, "worker ) helper", 29, 9876))

    def test_malformed_and_truncated(self):
        with self.assertRaises(ValueError):
            proc_stat("not a proc stat")
        with self.assertRaises(ValueError):
            proc_stat("7 (short) S")

    def test_initial_idle_callback_is_one_shot_even_if_worker_repeats(self):
        calls = []
        def repeating_callback():
            calls.append("sample")
            return 1  # GLib.SOURCE_CONTINUE from the recurring sample function.
        self.assertEqual(run_once(repeating_callback, 0), 0)
        self.assertEqual(calls, ["sample"])


class ProcessTrackerTests(unittest.TestCase):
    def test_baseline_then_cap_and_cache_cgroups(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            p1, p2 = root / "11", root / "12"
            p1.mkdir(); p2.mkdir()
            stat1, stat2 = p1 / "stat", p2 / "stat"
            stat1.write_text(fake_stat(11, "busy", 10, 0, 101))
            stat2.write_text(fake_stat(12, "also-busy", 5, 0, 202))
            tracker = ProcessTracker(root, max_reported=1)
            baseline = tracker.sample()
            self.assertTrue(baseline["baseline_only"])
            self.assertEqual(baseline["processes"], [])
            # Only the top active process needs cgroup access.
            (p1 / "cgroup").write_text("0::/user.slice/busy.service\n")
            stat1.write_text(fake_stat(11, "busy", 30, 0, 101))
            stat2.write_text(fake_stat(12, "also-busy", 15, 0, 202))
            second = tracker.sample()
            self.assertEqual((second["active_count"], second["reported_count"],
                              second["omitted_active"]), (2, 1, 1))
            self.assertEqual(second["processes"][0]["pid"], 11)
            self.assertEqual(second["processes"][0]["cgroup_units"], ["/user.slice/busy.service"])
            # The cached identity remains attributable even if its cgroup file vanishes.
            (p1 / "cgroup").unlink()
            stat1.write_text(fake_stat(11, "busy", 31, 0, 101))
            third = tracker.sample()
            self.assertEqual(third["processes"][0]["cpu_ticks_delta"], 1)
            self.assertEqual(third["processes"][0]["cgroup_units"], ["/user.slice/busy.service"])


class ReportTests(unittest.TestCase):
    def test_cpu_deltas_require_same_boot_pid_and_starttime(self):
        def sample(seq, processes):
            return {"event": "sample", "seq": seq, "boot_id": "boot-A",
                    "suspend_success": "3", "suspend_fail": "0",
                    "process_activity": {"processes": processes},
                    "logind_inhibitors": [], "battery": {}}

        before = [
            {"pid": 10, "start_ticks": 100, "comm": "app", "cpu_ticks_total": 200,
             "cgroup_units": ["app-demo.scope"]},
            {"pid": 20, "start_ticks": 200, "comm": "old", "cpu_ticks_total": 50,
             "cgroup_units": ["old.service"]},
        ]
        after = [
            {"pid": 10, "start_ticks": 100, "comm": "app", "cpu_ticks_total": 245,
             "cgroup_units": ["app-demo.scope"]},
            # PID reused: this must not be attributed as 1000 ticks of activity.
            {"pid": 20, "start_ticks": 201, "comm": "new", "cpu_ticks_total": 1050,
             "cgroup_units": ["new.service"]},
        ]
        report = analyze([sample(0, before), sample(1, after)])
        activity = next(x for x in report["findings"] if x["kind"] == "observed_cpu_activity")
        self.assertEqual(activity["processes"][0]["cpu_tick_delta"], 45)
        self.assertEqual(activity["unit_cpu_tick_delta"], {"app-demo.scope": 45})
        self.assertIn("not watts", activity["meaning"])

    def test_actionable_inhibitor_and_event_correlation(self):
        common = {"boot_id": "boot-A", "suspend_success": "8", "suspend_fail": "0",
                  "battery": {"bat": {"capacity": "80"}},
                  "process_activity": {"processes": [{"pid": 31, "start_ticks": 700,
                      "comm": "usb-gadget", "cpu_ticks_total": 12,
                      "cgroup_units": ["usb-gadget.service"]}]}}
        rows = [
            {"event": "sample", "seq": 0, **common, "logind_inhibitors": [
                {"what": "sleep", "who": "USB gadget", "why": "active session", "mode": "block", "pid": 31}]},
            {"event": "logind-request", "method": "Suspend", "caller": {"pid": 55, "comm": "gsd-power"}},
            {"event": "prepare-for-sleep", "wall_utc": "t1", "boottime": 12, "suspending": True},
            {"event": "prepare-for-sleep", "wall_utc": "t2", "boottime": 30, "suspending": False},
            {"event": "sample", "seq": 1, **common, "battery": {"bat": {"capacity": "79"}},
             "logind_inhibitors": [{"what": "sleep", "who": "USB gadget", "why": "active session", "mode": "block", "pid": 31}]},
        ]
        report = analyze(rows)
        kinds = [x["kind"] for x in report["findings"]]
        self.assertIn("sleep_inhibitors_seen_without_success_delta", kinds)
        self.assertIn("logind_requests", kinds)
        self.assertIn("sleep_wake_events", kinds)
        blocker = next(x for x in report["findings"] if x["kind"] == "sleep_inhibitors_seen_without_success_delta")
        self.assertEqual(blocker["holders"][0]["who"], "USB gadget")
        self.assertEqual(blocker["holders"][0]["cgroup_units"], "usb-gadget.service")

    def test_v1_without_start_ticks_is_skipped_with_explicit_warning(self):
        def old_sample(seq, boot_id, pid, cpu):
            return {"event": "sample", "seq": seq, "boot_id": boot_id,
                    "suspend_success": "2", "suspend_fail": "0", "battery": {},
                    "logind_inhibitors": [], "process_activity": {"processes": [
                        {"pid": pid, "comm": "legacy", "cpu_ticks_total": cpu,
                         "cgroup_units": ["legacy.service"]}]}}
        report = analyze([old_sample(0, "boot-A", 42, 10), old_sample(1, "boot-A", 42, 1000)])
        self.assertFalse(any(x["kind"] == "observed_cpu_activity" for x in report["findings"]))
        self.assertTrue(any("lack start_ticks" in warning for warning in report["warnings"]))

    def test_missing_or_changed_boot_id_never_joins_pid_counters(self):
        def sample(seq, boot, ticks):
            return {"event": "sample", "seq": seq, "boot_id": boot,
                    "suspend_success": "1", "suspend_fail": "0", "battery": {},
                    "logind_inhibitors": [], "process_activity": {"processes": [
                        {"pid": 9, "start_ticks": 30, "comm": "worker",
                         "cpu_ticks_total": ticks, "cgroup_units": ["worker.service"]}]}}
        report = analyze([sample(0, "boot-A", 10), sample(1, "boot-B", 500)])
        self.assertFalse(any(x["kind"] == "observed_cpu_activity" for x in report["findings"]))
        counters = next(x for x in report["findings"] if x["kind"] == "suspend_counter_delta")
        self.assertIsNone(counters["success"])
        self.assertIsNone(counters["fail"])
        missing = analyze([sample(0, None, 10), sample(1, None, 500)])
        self.assertFalse(any(x["kind"] == "observed_cpu_activity" for x in missing["findings"]))
        self.assertTrue(any("boot_id missing" in warning for warning in missing["warnings"]))
        failed_read = analyze([sample(0, {"error": "missing"}, 10),
                               sample(1, {"error": "missing"}, 500)])
        self.assertFalse(any(x["kind"] == "observed_cpu_activity" for x in failed_read["findings"]))

    def test_delay_inhibitor_is_reported_without_calling_it_a_blocker(self):
        sample = {"event": "sample", "boot_id": "boot-A", "suspend_success": "0",
                  "suspend_fail": "0", "battery": {}, "process_activity": {"processes": []},
                  "logind_inhibitors": [{"what": "sleep", "who": "session", "why": "finish", "mode": "delay", "pid": 7}]}
        report = analyze([sample, {**sample, "seq": 1}])
        kinds = [x["kind"] for x in report["findings"]]
        self.assertIn("sleep_delay_inhibitors_observed", kinds)
        self.assertNotIn("sleep_inhibitors_seen_without_success_delta", kinds)

    def test_explicit_interval_deltas_are_analyzed_without_joining_snapshots(self):
        sample = {"event": "sample", "boot_id": "boot-A", "suspend_success": "0",
                  "suspend_fail": "0", "battery": {}, "logind_inhibitors": [],
                  "process_activity": {"baseline_only": False, "omitted_active": 2,
                      "processes": [{"pid": 13, "start_ticks": 8, "comm": "worker",
                                     "cpu_ticks_total": 28, "cpu_ticks_delta": 4,
                                     "cgroup_units": ["worker.service"]}]}}
        report = analyze([sample])
        activity = next(x for x in report["findings"] if x["kind"] == "observed_cpu_activity")
        self.assertEqual(activity["processes"][0]["cpu_tick_delta"], 4)
        self.assertEqual(activity["omitted_active_entries"], 2)


if __name__ == "__main__":
    unittest.main()
