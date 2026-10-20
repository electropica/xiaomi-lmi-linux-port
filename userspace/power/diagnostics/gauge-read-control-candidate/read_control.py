"""Bounded read-order sensitivity probe for natural fuel-gauge wake callbacks.

No filesystem, clock, or device I/O occurs at import time. The caller supplies
all reads and clocks and invokes capture() only from an existing wake callback.
"""

MODE_SEQUENCE = (
    "treatment", "control", "control", "treatment",
    "treatment", "control", "control", "treatment",
)
MAX_PLAN_READS = 14
MAX_CALLBACKS = 8
PARENT_LIFETIME_SECONDS = 18 * 60 * 60
DEFAULT_MAX_INTERREAD_GAP_SECONDS = 0.25
DEFAULT_MAX_READ_SECONDS = 0.25

PRELUDE = (
    ("usb_pre", "usb/online", "direct_status"),
    ("status_pre", "battery/status", "direct_status"),
    ("wake_reason", "wakeup_reasons/last_resume_reason", "direct_status"),
    ("current_now_pre", "bms/current_now", "direct_register_same_gauge"),
    ("current_avg_pre", "bms/current_avg", "sram_dma_same_gauge"),
)
TREATMENT_MIDDLE = (
    ("middle_charge_counter", "bms/charge_counter", "sram_dma_same_gauge"),
    ("middle_shadow", "bms/charge_counter_shadow", "sram_dma_same_gauge"),
    ("middle_raw", "bms/charge_now_raw", "sram_dma_same_gauge"),
)
CONTROL_MIDDLE = (
    ("middle_current_now_1", "bms/current_now", "direct_register_same_gauge"),
    ("middle_current_now_2", "bms/current_now", "direct_register_same_gauge"),
    ("middle_current_now_3", "bms/current_now", "direct_register_same_gauge"),
)
EPILOGUE = (
    ("usb_mid", "usb/online", "direct_status"),
    ("status_mid", "battery/status", "direct_status"),
    ("current_avg_post", "bms/current_avg", "sram_dma_same_gauge"),
    ("current_now_post", "bms/current_now", "direct_register_same_gauge"),
    ("status_post", "battery/status", "direct_status"),
    ("usb_post", "usb/online", "direct_status"),
)


def plan_for(mode):
    if mode not in ("treatment", "control"):
        raise ValueError("mode must be treatment or control")
    middle = TREATMENT_MIDDLE if mode == "treatment" else CONTROL_MIDDLE
    return [
        {"label": label, "attribute": attr, "path": path}
        for label, attr, path in PRELUDE + middle + EPILOGUE
    ]


class ReadControl:
    """Stateful cap for a caller-owned natural-wake callback stream."""

    def __init__(self, read_attr, boottime, monotonic, epoch,
                 service_start_boottime, max_callbacks=MAX_CALLBACKS,
                 service_lifetime_s=PARENT_LIFETIME_SECONDS,
                 read_budget=MAX_PLAN_READS,
                 max_interread_gap_s=DEFAULT_MAX_INTERREAD_GAP_SECONDS,
                 max_read_s=DEFAULT_MAX_READ_SECONDS):
        if not 1 <= max_callbacks <= MAX_CALLBACKS:
            raise ValueError("max_callbacks must be 1..8")
        if not 1 <= read_budget <= MAX_PLAN_READS:
            raise ValueError("read_budget must be 1..14")
        if not 0 < service_lifetime_s <= PARENT_LIFETIME_SECONDS:
            raise ValueError("service_lifetime_s must be in (0, 18 hours]")
        if not 0 < max_interread_gap_s <= DEFAULT_MAX_INTERREAD_GAP_SECONDS:
            raise ValueError("max_interread_gap_s must be in (0, 0.25 seconds]")
        if not 0 < max_read_s <= DEFAULT_MAX_READ_SECONDS:
            raise ValueError("max_read_s must be in (0, 0.25 seconds]")
        self._read_attr = read_attr
        self._boottime = boottime
        self._monotonic = monotonic
        self._epoch = epoch
        self._service_start = float(service_start_boottime)
        self._service_deadline = self._service_start + float(service_lifetime_s)
        self.max_callbacks = max_callbacks
        self.read_budget = read_budget
        self.max_interread_gap_s = float(max_interread_gap_s)
        self.max_read_s = float(max_read_s)
        self.callbacks_attempted = 0
        self.stopped = False
        self.stop_reason = None

    def _stop(self, reason):
        self.stopped = True
        self.stop_reason = reason

    def _stamp(self):
        return {
            "epoch": float(self._epoch()),
            "boottime": float(self._boottime()),
            "monotonic": float(self._monotonic()),
        }

    def capture(self):
        """Run one bounded probe. The host must call only at an existing wake."""
        if self.stopped:
            return {"captured": False, "stop_reason": self.stop_reason,
                    "callbacks_attempted": self.callbacks_attempted, "trace": []}
        callback_start = self._stamp()
        now = callback_start["boottime"]
        if now >= self._service_deadline:
            self._stop("service_deadline")
            return {"captured": False, "stop_reason": self.stop_reason,
                    "callbacks_attempted": self.callbacks_attempted,
                    "callback_start": callback_start, "trace": []}
        if self.callbacks_attempted >= self.max_callbacks:
            self._stop("callback_limit")
            return {"captured": False, "stop_reason": self.stop_reason,
                    "callbacks_attempted": self.callbacks_attempted,
                    "callback_start": callback_start, "trace": []}

        idx = self.callbacks_attempted
        mode = MODE_SEQUENCE[idx]
        self.callbacks_attempted += 1
        plan = plan_for(mode)
        record = {
            "captured": True,
            "callback_index": idx,
            "callback_start": callback_start,
            "mode": mode,
            "plan": plan,
            "read_budget": self.read_budget,
            "max_interread_gap_s": self.max_interread_gap_s,
            "max_read_s": self.max_read_s,
            "trace": [],
            "stop_reason": None,
            "complete": False,
        }
        previous_after = None
        seen = {}

        for item in plan:
            if len(record["trace"]) >= self.read_budget:
                record["stop_reason"] = "read_budget_exhausted"
                self._stop(record["stop_reason"])
                break

            before = self._stamp()
            if before["boottime"] >= self._service_deadline:
                record["stop_reason"] = "service_deadline"
                record["guard_timestamp"] = before
                self._stop(record["stop_reason"])
                break
            if previous_after is not None:
                gap = before["monotonic"] - previous_after["monotonic"]
                if gap < 0:
                    record["stop_reason"] = "clock_reversal_between_reads"
                    record["guard_timestamp"] = before
                    self._stop(record["stop_reason"])
                    break
                if gap > self.max_interread_gap_s:
                    record["stop_reason"] = "interread_gap_over_limit"
                    record["interread_gap_s"] = gap
                    record["guard_timestamp"] = before
                    self._stop(record["stop_reason"])
                    break

            entry = {"label": item["label"], "attribute": item["attribute"],
                     "path": item["path"], "before": before,
                     "seconds_after_callback_start": before["monotonic"] - callback_start["monotonic"]}
            try:
                value = self._read_attr(item["attribute"])
                if value is None:
                    raise RuntimeError("reader returned no value")
                entry["value"] = value.decode("utf-8", "replace") if isinstance(value, bytes) else str(value)
            except Exception as exc:  # captured as evidence; never hide a read failure
                entry["error"] = {"type": type(exc).__name__, "message": str(exc)}
            after = self._stamp()
            entry["after"] = after
            entry["duration_s"] = after["monotonic"] - before["monotonic"]
            record["trace"].append(entry)
            previous_after = after

            if entry["duration_s"] < 0:
                record["stop_reason"] = "clock_reversal_during_read"
            elif "error" in entry:
                record["stop_reason"] = "read_error"
            elif entry["duration_s"] > self.max_read_s:
                # The synchronous read has already returned; it was not interrupted.
                record["stop_reason"] = "read_duration_over_limit"
            else:
                seen[item["label"]] = entry["value"]
                if item["label"].startswith("usb_") and entry["value"] != "0":
                    record["stop_reason"] = "usb_not_disconnected"
                elif item["label"].startswith("status_") and entry["value"] != "Discharging":
                    record["stop_reason"] = "status_not_discharging"

            if record["stop_reason"]:
                self._stop(record["stop_reason"])
                break

        record["observed"] = seen
        record["complete"] = len(record["trace"]) == len(plan) and not record["stop_reason"]
        if record["complete"] and float(self._boottime()) >= self._service_deadline:
            record["stop_reason"] = "service_deadline"
            self._stop(record["stop_reason"])
        if (record["complete"] and not self.stopped and
                self.callbacks_attempted >= self.max_callbacks):
            record["stop_reason"] = "callback_limit_reached"
            self._stop(record["stop_reason"])
        return record
