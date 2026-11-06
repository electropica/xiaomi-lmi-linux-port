#!/usr/bin/env python3
"""Optional read-only systemd-sleep hook; never enabled or installed by this tool."""
import json
import os
import stat
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


QCOM_COUNTERS = ("aosd", "cxsd", "ddr", "ddr_stats", "adsp")
SUSPEND_COUNTERS = ("success", "fail", "last_failed_dev", "last_failed_errno",
                    "last_failed_step", "time_total", "time_last", "max_depth", "counter")
SUPPLY_KEYS = ("type", "status", "online", "present", "capacity", "current_now",
               "current_avg", "voltage_now", "temp", "charge_counter", "charge_now",
               "charge_full", "energy_now", "energy_full")
BACKLIGHT_KEYS = ("brightness", "actual_brightness", "bl_power")


def read_value(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError as exc:
        return {"unavailable": type(exc).__name__, "errno": exc.errno}


def snapshot(phase, verb, root=Path("/"), now=None):
    """Read a bounded set of kernel counters under root (supports synthetic tests)."""
    root = Path(root)

    def p(absolute):
        return root / absolute.lstrip("/")

    qcom = {name: read_value(p(f"/sys/kernel/debug/qcom_stats/{name}"))
            for name in QCOM_COUNTERS}
    suspend = {name: read_value(p(f"/sys/power/suspend_stats/{name}"))
               for name in SUSPEND_COUNTERS}
    supplies = {}
    supply_root = p("/sys/class/power_supply")
    try:
        supply_entries = sorted(x for x in supply_root.iterdir() if x.is_dir())
    except OSError:
        supply_entries = []
    for entry in supply_entries:
        supplies[entry.name] = {key: read_value(entry / key) for key in SUPPLY_KEYS
                                if (entry / key).exists()}
    backlights = {}
    light_root = p("/sys/class/backlight")
    try:
        light_entries = sorted(x for x in light_root.iterdir() if x.is_dir())
    except OSError:
        light_entries = []
    for entry in light_entries:
        backlights[entry.name] = {key: read_value(entry / key) for key in BACKLIGHT_KEYS
                                  if (entry / key).exists()}
    stamp = now or datetime.now(timezone.utc)
    return {
        "event": "systemd-sleep-hook",
        "phase": phase,
        "verb": verb,
        "wall_utc": stamp.astimezone(timezone.utc).isoformat(),
        "boottime_seconds": time.clock_gettime(time.CLOCK_BOOTTIME),
        "monotonic_seconds": time.monotonic(),
        "boot_id": read_value(p("/proc/sys/kernel/random/boot_id")),
        "uptime": read_value(p("/proc/uptime")),
        "suspend_stats": suspend,
        "qcom_stats": qcom,
        "backlights": backlights,
        "power_supplies": supplies,
        "interpretation": "Boundary counters only; zero or unchanged values are not evidence of zero energy use.",
    }


def append_private(path, record):
    path = Path(path)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise OSError("hook log is not a single-link regular file")
        if metadata.st_uid != os.geteuid():
            raise OSError("hook log has an unexpected owner")
        os.fchmod(fd, 0o600)
        payload = (json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
        offset = 0
        while offset < len(payload):
            offset += os.write(fd, payload[offset:])
    finally:
        os.close(fd)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    phase = argv[0] if argv else ""
    verb = argv[1] if len(argv) > 1 else "unknown"
    # systemd-sleep calls hooks with pre/post and a verb. Ignore all other calls.
    if phase not in ("pre", "post"):
        return 0
    os.umask(0o077)
    out = Path(os.environ.get(
        "MOBIAN_TRIAGE_SLEEP_HOOK_LOG",
        "/var/tmp/mobian-battery-triage-sleep-hook.jsonl"))
    try:
        append_private(out, snapshot(phase, verb))
    except OSError:
        # Never obstruct suspend/resume because diagnostics cannot be written.
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
