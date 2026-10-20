"""Injectable lifecycle engine plus opt-in Linux GI/DBus adapter.

Importing this module does not access sysfs, clocks, DBus, GI or services.
"""
import json

from read_control import ReadControl, PARENT_LIFETIME_SECONDS

WAITING_UNPLUG = "waiting_unplug"
OBSERVING = "observing"
STOPPED = "stopped"
MAX_UNPLUG_WAIT_SECONDS = 3 * 60 * 60
MAX_TOTAL_SECONDS = PARENT_LIFETIME_SECONDS
MAX_PARENT_METADATA_READS = 20000
PARENT_METADATA_READ_MAX_SECONDS = 0.25
POLL_INTERVAL_SECONDS = 5
MIN_UNPLUG_STABLE_SECONDS = 20


class LifecycleEngine:
    """State machine driven only by injected natural events and awake polls."""

    def __init__(self, read_attr, boottime, monotonic, epoch, sink,
                 close_sink=None, max_parent_metadata_reads=MAX_PARENT_METADATA_READS,
                 control_options=None):
        if not 1 <= max_parent_metadata_reads <= MAX_PARENT_METADATA_READS:
            raise ValueError("parent metadata read budget must be 1..20000")
        self.read_attr = read_attr
        self.boottime = boottime
        self.monotonic = monotonic
        self.epoch = epoch
        self.sink = sink
        self.close_sink = close_sink
        self.max_parent_metadata_reads = max_parent_metadata_reads
        self.control_options = dict(control_options or {})
        self.phase = "new"
        self.armed_at = None
        self.control = None
        self.parent_metadata_reads = 0
        self._unplug_candidate = None
        self.records = []
        self.stopped = False
        self.stop_reason = None
        self._sink_failed = False
        self._close_called = False
        self._finished_emitted = False

    def _stamp(self):
        return {"epoch": float(self.epoch()),
                "boottime": float(self.boottime()),
                "monotonic": float(self.monotonic())}

    def _emit(self, row):
        row.setdefault("parent_metadata_reads_total", self.parent_metadata_reads)
        self.records.append(row)
        if self._sink_failed or self.sink is None:
            return not self._sink_failed
        try:
            self.sink(row)
            return True
        except Exception as exc:
            self._sink_failed = True
            self.records.append({"event": "sink-error", "error": {
                "type": type(exc).__name__, "message": str(exc)}})
            return False

    def arm(self):
        if self.phase != "new":
            raise RuntimeError("engine can only be armed once")
        self.armed_at = self._stamp()
        self.phase = WAITING_UNPLUG
        self.control = ReadControl(
            self.read_attr, self.boottime, self.monotonic, self.epoch,
            service_start_boottime=self.armed_at["boottime"],
            **self.control_options)
        row = {"event": "armed", **self.armed_at,
               "limits": {"unplug_wait_s": MAX_UNPLUG_WAIT_SECONDS,
                          "unplug_stability_s": MIN_UNPLUG_STABLE_SECONDS,
                          "total_from_arm_s": MAX_TOTAL_SECONDS,
                          "natural_resume_attempts": self.control.max_callbacks,
                          "probe_property_reads": self.control.read_budget,
                          "parent_metadata_reads": self.max_parent_metadata_reads,
                          "awake_poll_interval_s": POLL_INTERVAL_SECONDS}}
        if not self._emit(row):
            self.finish("sink_error")
        return not self.stopped

    def _read_metadata(self, attribute):
        """One timed parent metadata read; never reads a gauge property here."""
        if self.parent_metadata_reads >= self.max_parent_metadata_reads:
            return {"attribute": attribute, "attempted": False,
                    "error": {"type": "ReadBudgetExceeded",
                              "message": "parent metadata read budget exhausted"},
                    "stop_reason": "parent_metadata_budget"}
        before = self._stamp()
        if before["boottime"] >= self.armed_at["boottime"] + MAX_TOTAL_SECONDS:
            return {"attribute": attribute, "attempted": False,
                    "before": before,
                    "error": {"type": "DeadlineExceeded",
                              "message": "total observation deadline reached"},
                    "stop_reason": "total_timeout"}
        self.parent_metadata_reads += 1
        entry = {"attribute": attribute, "attempted": True, "before": before}
        try:
            value = self.read_attr(attribute)
            if value is None:
                raise RuntimeError("reader returned no value")
            entry["value"] = value.decode("utf-8", "replace") if isinstance(value, bytes) else str(value)
        except Exception as exc:
            entry["error"] = {"type": type(exc).__name__, "message": str(exc)}
        after = self._stamp()
        entry["after"] = after
        entry["duration_s"] = after["monotonic"] - before["monotonic"]
        if "error" in entry:
            entry["stop_reason"] = "parent_metadata_read_error"
        elif entry["duration_s"] < 0:
            entry["stop_reason"] = "parent_clock_reversal"
        elif entry["duration_s"] > PARENT_METADATA_READ_MAX_SECONDS:
            # Synchronous sysfs reads are detected after return, never interrupted here.
            entry["stop_reason"] = "parent_metadata_read_over_limit"
        return entry

    def _deadline_reason(self, stamp):
        if self.armed_at is None:
            return "not_armed"
        if stamp["boottime"] >= self.armed_at["boottime"] + MAX_TOTAL_SECONDS:
            return "total_timeout"
        if (self.phase == WAITING_UNPLUG and
                stamp["boottime"] >= self.armed_at["boottime"] + MAX_UNPLUG_WAIT_SECONDS):
            return "unplug_wait_timeout"
        return None

    def _record_and_stop(self, row, reason):
        if not self._emit(row):
            reason = "sink_error"
        self.finish(reason)

    def poll_while_awake(self):
        """Called by an awake-only parent timer; this method never wakes the CPU."""
        if self.stopped or self.phase == "new":
            return False
        entry = self._stamp()
        deadline = self._deadline_reason(entry)
        if deadline:
            self.finish(deadline, at=entry)
            return False
        meta = self._read_metadata("usb/online")
        row = {"event": "parent-poll", **entry, "usb_read": meta}
        if meta.get("stop_reason"):
            self._record_and_stop(row, meta["stop_reason"])
            return False
        after = meta["after"]
        deadline = self._deadline_reason(after)
        if deadline:
            row["event"] = "poll-deadline"
            self._record_and_stop(row, deadline)
            return False
        usb = meta["value"]
        if usb not in ("0", "1"):
            row["event"] = "poll-invalid-usb"
            self._record_and_stop(row, "invalid_usb_value")
            return False
        if self.phase == WAITING_UNPLUG:
            if usb == "1":
                if self._unplug_candidate is not None:
                    row["event"] = "unplug-candidate-cancelled"
                    row["candidate_start"] = self._unplug_candidate
                    self._unplug_candidate = None
                    if not self._emit(row):
                        self.finish("sink_error")
                        return False
                return True
            if self._unplug_candidate is None:
                self._unplug_candidate = after
                row["event"] = "unplug-candidate"
                if not self._emit(row):
                    self.finish("sink_error")
                    return False
                return True
            elapsed = after["boottime"] - self._unplug_candidate["boottime"]
            if elapsed < MIN_UNPLUG_STABLE_SECONDS:
                return True
            self.phase = OBSERVING
            row["event"] = "unplugged"
            row["candidate_start"] = self._unplug_candidate
            row["observed_stability_seconds"] = elapsed
            row["boottime"] = after["boottime"]
            row["monotonic"] = after["monotonic"]
            row["epoch"] = after["epoch"]
            if not self._emit(row):
                self.finish("sink_error")
                return False
        elif self.phase == OBSERVING and usb == "1":
            row["event"] = "replugged"
            row["boottime"] = after["boottime"]
            row["monotonic"] = after["monotonic"]
            row["epoch"] = after["epoch"]
            self._record_and_stop(row, "usb_reconnected")
            return False
        return not self.stopped

    def on_prepare_for_sleep(self, suspending):
        """Handle an injected login1 signal; resume control precedes all parent reads."""
        if self.stopped or self.phase != OBSERVING:
            return not self.stopped
        entry = self._stamp()  # preserve callback entry before any read/control
        deadline = self._deadline_reason(entry)
        if deadline:
            self.finish(deadline, at=entry)
            return False

        if suspending:
            meta = self._read_metadata("usb/online")
            row = {"event": "prepare-sleep", **entry,
                   "suspending": True, "usb_read": meta}
            if meta.get("stop_reason"):
                self._record_and_stop(row, meta["stop_reason"])
                return False
            if meta["value"] == "1":
                row["event"] = "replugged-during-prepare"
                self._record_and_stop(row, "usb_reconnected")
                return False
            if meta["value"] != "0":
                row["event"] = "prepare-invalid-usb"
                self._record_and_stop(row, "invalid_usb_value")
                return False
            if not self._emit(row):
                self.finish("sink_error")
                return False
            deadline = self._deadline_reason(meta["after"])
            if deadline:
                self.finish(deadline, at=meta["after"])
                return False
            return True

        # No parent counters()/snapshot call here. The first gauge property reads
        # are exactly the read-control plan; entry is retained separately.
        try:
            probe = self.control.capture()
        except Exception as exc:
            probe = {"captured": False, "stop_reason": "control_exception",
                     "error": {"type": type(exc).__name__, "message": str(exc)},
                     "trace": []}
        seen = probe.get("observed", {})
        row = {"event": "resume-signal", **entry,
               "wake_reason": seen.get("wake_reason"),
               "usb": seen.get("usb_pre", seen.get("usb_mid", seen.get("usb_post"))),
               "status": seen.get("status_pre"),
               "probe": probe,
               "parent_metadata_reads_total": self.parent_metadata_reads}
        if not self._emit(row):
            self.finish("sink_error")
            return False
        reason = self._map_probe_stop(probe.get("stop_reason"))
        if reason:
            self.finish(reason)
            return False
        deadline = self._deadline_reason(self._stamp())
        if deadline:
            self.finish(deadline)
            return False
        return True

    @staticmethod
    def _map_probe_stop(reason):
        if not reason:
            return None
        return {
            "usb_not_disconnected": "usb_reconnected",
            "status_not_discharging": "status_changed",
            "read_error": "gauge_read_error",
            "read_duration_over_limit": "probe_read_over_limit",
            "interread_gap_over_limit": "probe_interread_gap_over_limit",
            "read_budget_exhausted": "probe_read_budget",
            "service_deadline": "total_timeout",
            "callback_limit_reached": "callback_limit",
            "callback_limit": "callback_limit",
        }.get(reason, reason)

    def finish(self, reason, at=None):
        """Idempotent final event and one close callback."""
        if self.stopped:
            return False
        self.stopped = True
        self.phase = STOPPED
        self.stop_reason = reason
        stamp = at if at is not None else self._stamp()
        if not self._finished_emitted:
            self._finished_emitted = True
            row = {"event": "finished", **stamp, "reason": reason,
                   "control_callbacks_attempted": (self.control.callbacks_attempted
                                                    if self.control else 0),
                   "parent_metadata_reads_total": self.parent_metadata_reads}
            self._emit(row)
        if not self._close_called:
            self._close_called = True
            if self.close_sink is not None:
                try:
                    self.close_sink()
                except Exception as exc:
                    self.records.append({"event": "close-error", "error": {
                        "type": type(exc).__name__, "message": str(exc)}})
        return True


def _run_linux_adapter():
    """Explicit --run adapter. Never reached by import or tests."""
    import os
    import sys
    import time
    from pathlib import Path

    import gi
    gi.require_version("Gio", "2.0")
    from gi.repository import Gio, GLib

    root = Path("/sys/class/power_supply")
    log_path = Path("/var/tmp/lmi-gauge-read-control-candidate-20261020b.jsonl")
    os.umask(0o077)
    log = log_path.open("x", encoding="utf-8")
    loop = GLib.MainLoop()
    system_bus = None
    engine = None

    def read_attr(name):
        if name.startswith("wakeup_reasons/"):
            path = Path("/sys/kernel") / name
        else:
            path = root / name
        return path.read_text(encoding="utf-8").strip()

    def sink(row):
        log.write(json.dumps(row, ensure_ascii=False) + "\n")
        log.flush()

    def close_sink():
        if not log.closed:
            log.flush()
            log.close()
        loop.quit()

    try:
        system_bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        engine = LifecycleEngine(
            read_attr,
            lambda: time.clock_gettime(time.CLOCK_BOOTTIME),
            time.monotonic,
            time.time,
            sink,
            close_sink=close_sink,
        )

        def poll_cb():
            keep = engine.poll_while_awake()
            if not keep:
                loop.quit()
            return keep

        def sleep_cb(connection, sender, path, iface, signal, params, data):
            engine.on_prepare_for_sleep(bool(params.unpack()[0]))
            if engine.stopped:
                loop.quit()

        system_bus.signal_subscribe(
            "org.freedesktop.login1", "org.freedesktop.login1.Manager",
            "PrepareForSleep", "/org/freedesktop/login1", None,
            Gio.DBusSignalFlags.NONE, sleep_cb, None)
        GLib.timeout_add_seconds(POLL_INTERVAL_SECONDS, poll_cb)
        if not engine.arm():
            return 1
        loop.run()
        return 0
    finally:
        if engine is not None and not engine.stopped:
            engine.finish("adapter_exit")
        if system_bus is not None:
            system_bus.close_sync(None)
        if not log.closed:
            log.close()


def main(argv=None):
    """No-op without the explicit device-side --run argument."""
    import sys
    args = sys.argv[1:] if argv is None else list(argv)
    if args != ["--run"]:
        print("Offline-safe candidate. Use --run explicitly only when separately approved.", file=sys.stderr)
        return 2
    return _run_linux_adapter()


if __name__ == "__main__":
    raise SystemExit(main())
