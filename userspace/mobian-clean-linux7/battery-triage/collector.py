#!/usr/bin/env python3
"""Low-rate Mobian/Linux 7 battery triage collector (read-only).

Captures battery counters, logind inhibitors, suspend counters, and process
CPU-time/cgroup attribution at a coarse interval. CPU time is context only;
this tool does not estimate watts or energy per process.
"""
import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

BATTERY_KEYS = ("status", "capacity", "current_now", "current_avg", "voltage_now",
                "charge_now", "charge_counter", "energy_now", "temp")


def deadline_reached(deadline, now):
    return now >= deadline


def run_once(callback, source_remove):
    """Invoke an idle callback once and ignore a repeating callback's return."""
    callback()
    return source_remove


def read(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError as exc:
        return {"error": type(exc).__name__, "errno": exc.errno}


def proc_stat(text):
    """Return pid, comm, CPU ticks, and process start time (field 22)."""
    # comm is parenthesized and may itself contain spaces or right parentheses.
    left, sep, rest = text.partition("(")
    end = rest.rfind(")")
    if not sep or end < 0:
        raise ValueError("malformed proc stat")
    pid = int(left.strip())
    comm = rest[:end]
    fields = rest[end + 1:].split()  # starts at field 3 (state)
    if len(fields) <= 19:
        raise ValueError("truncated proc stat")
    return pid, comm, int(fields[11]) + int(fields[12]), int(fields[19])


class ProcessTracker:
    """One stat read per PID, then bounded cgroup reads for active leaders only."""
    def __init__(self, proc_root=Path("/proc"), max_reported=20):
        self.proc_root = Path(proc_root)
        self.max_reported = max_reported
        self.previous = {}
        self.cgroup_cache = {}

    def sample(self):
        started = time.monotonic()
        had_previous = bool(self.previous)
        current = {}
        try:
            entries = list(self.proc_root.iterdir())
        except OSError:
            return {"error": "proc-unavailable", "processes": [], "baseline_only": False,
                    "collection_duration_sec": time.monotonic() - started}
        for entry in entries:
            if not entry.name.isdigit():
                continue
            try:
                pid, comm, ticks, start_ticks = proc_stat((entry / "stat").read_text())
                key = (pid, start_ticks)
                current[key] = {"pid": pid, "comm": comm[:128], "start_ticks": start_ticks,
                                "cpu_ticks_total": ticks}
            except (OSError, ValueError):
                continue

        active = []
        for key, row in current.items():
            previous = self.previous.get(key)
            if previous is None:
                continue
            delta = row["cpu_ticks_total"] - previous
            if delta > 0:
                row["cpu_ticks_delta"] = delta
                active.append((key, row))

        # First pass is a counter baseline only; avoid cgroup I/O until there is
        # an actual interval delta to rank.
        active.sort(key=lambda pair: pair[1]["cpu_ticks_delta"], reverse=True)
        leaders = active[:self.max_reported]
        result = []
        for key, row in leaders:
            if key not in self.cgroup_cache:
                try:
                    lines = (self.proc_root / str(row["pid"]) / "cgroup").read_text(
                        encoding="utf-8", errors="replace").splitlines()
                    self.cgroup_cache[key] = [line.split(":", 2)[-1] for line in lines
                                              if ".service" in line or ".scope" in line][:4]
                except OSError:
                    self.cgroup_cache[key] = []
            row["cgroup_units"] = self.cgroup_cache[key]
            result.append(row)

        # Retain only live identities to bound cache growth and prevent PID reuse.
        self.previous = {key: row["cpu_ticks_total"] for key, row in current.items()}
        self.cgroup_cache = {key: value for key, value in self.cgroup_cache.items() if key in current}
        return {"processes": result, "count_scanned": len(current),
                "active_count": len(active), "reported_count": len(result),
                "omitted_active": max(0, len(active) - len(result)),
                "baseline_only": not had_previous,
                "collection_duration_sec": time.monotonic() - started}


def battery_snapshot(root=Path("/sys/class/power_supply")):
    result = {}
    try:
        supplies = sorted(root.iterdir())
    except OSError as exc:
        return {"error": type(exc).__name__}
    for supply in supplies:
        values = {}
        for key in BATTERY_KEYS + ("type", "online"):
            p = supply / key
            if p.exists():
                values[key] = read(p)
        if values:
            result[supply.name] = values
    return result


def inhibitors():
    """Read logind's current inhibitor list through the system bus, if GI exists."""
    try:
        import gi
        gi.require_version("Gio", "2.0")
        from gi.repository import Gio
        bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        reply = bus.call_sync("org.freedesktop.login1", "/org/freedesktop/login1",
                              "org.freedesktop.login1.Manager", "ListInhibitors",
                              None, None, Gio.DBusCallFlags.NONE, 1200, None).unpack()
        return [{"what": r[0], "who": r[1], "why": r[2], "mode": r[3],
                 "uid": r[4], "pid": r[5]} for r in reply[0]]
    except Exception as exc:
        return {"unavailable": type(exc).__name__}


def snapshot(seq, process_tracker):
    started = time.monotonic()
    process_activity = process_tracker.sample()
    row = {"event": "sample", "seq": seq,
            "wall_utc": datetime.now(timezone.utc).isoformat(),
            "wall_epoch": time.time(), "boottime": time.clock_gettime(time.CLOCK_BOOTTIME),
            "boot_id": read("/proc/sys/kernel/random/boot_id"),
            "kernel": read("/proc/sys/kernel/osrelease"),
            "suspend_success": read("/sys/power/suspend_stats/success"),
            "suspend_fail": read("/sys/power/suspend_stats/fail"),
            "last_resume_reason": read("/sys/kernel/wakeup_reasons/last_resume_reason"),
            "backlights": {p.name: {k: read(p / k) for k in ("actual_brightness", "bl_power")}
                           for p in Path("/sys/class/backlight").glob("*")},
            "battery": battery_snapshot(), "logind_inhibitors": inhibitors(),
            "process_activity": process_activity,
            "clock_ticks_per_second": os.sysconf("SC_CLK_TCK"),
            "interpretation": "Cumulative CPU ticks and cgroup ownership are activity clues, not power measurements."}
    row["collection_duration_sec"] = time.monotonic() - started
    return row


def run_observer(stream, duration, interval):
    """Coarse samples plus event timestamps for logind suspend and GSD requests."""
    import gi
    gi.require_version("Gio", "2.0")
    gi.require_version("GLib", "2.0")
    from gi.repository import Gio, GLib

    system = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
    try:
        session = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    except Exception:
        session = None
    loop = GLib.MainLoop()
    seq = 0
    process_tracker = ProcessTracker()
    deadline_boottime = time.clock_gettime(time.CLOCK_BOOTTIME) + duration

    def emit(event, **data):
        row = {"event": event, "wall_utc": datetime.now(timezone.utc).isoformat(),
               "wall_epoch": time.time(), "boottime": time.clock_gettime(time.CLOCK_BOOTTIME)}
        row.update(data)
        stream.write(json.dumps(row, separators=(",", ":")) + "\n")
        stream.flush()

    def on_sleep(_conn, _sender, _path, _iface, _name, params, _data):
        suspending = bool(params.unpack()[0])
        emit("prepare-for-sleep", suspending=suspending,
             suspend_success=read("/sys/power/suspend_stats/success"),
             suspend_fail=read("/sys/power/suspend_stats/fail"))
        if not suspending and deadline_reached(deadline_boottime, time.clock_gettime(time.CLOCK_BOOTTIME)):
            emit("duration-expired-after-resume")
            loop.quit()

    system.signal_subscribe("org.freedesktop.login1", "org.freedesktop.login1.Manager",
                            "PrepareForSleep", "/org/freedesktop/login1", None,
                            Gio.DBusSignalFlags.NONE, on_sleep, None)

    # Observe logind method calls on a dedicated connection so the normal system
    # bus remains available to the collector. Include caller PID where resolvable.
    monitor = Gio.DBusConnection.new_for_address_sync(
        "unix:path=/run/dbus/system_bus_socket",
        Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT |
        Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION, None, None)
    rule = "type='method_call',destination='org.freedesktop.login1',interface='org.freedesktop.login1.Manager'"
    try:
        monitor.call_sync("org.freedesktop.DBus", "/org/freedesktop/DBus",
                          "org.freedesktop.DBus.Monitoring", "BecomeMonitor",
                          GLib.Variant("(asu)", ([rule], 0)), None,
                          Gio.DBusCallFlags.NONE, 2000, None)
        monitor.set_exit_on_close(False)
        def pid_lookup_done(connection, result, details):
            try:
                pid = connection.call_finish(result).unpack()[0]
                caller = {"pid": pid, "comm": read(f"/proc/{pid}/comm"),
                          "start_ticks": proc_identity(pid)}
            except Exception as exc:
                caller = {"lookup_error": type(exc).__name__}
            emit("logind-request", **details, caller=caller)

        def start_pid_lookup(details):
            # Start on the GLib main context so the async completion callback is
            # attached to the loop that this observer is actually running.
            system.call("org.freedesktop.DBus", "/org/freedesktop/DBus",
                        "org.freedesktop.DBus", "GetConnectionUnixProcessID",
                        GLib.Variant("(s)", (details["sender"],)), None,
                        Gio.DBusCallFlags.NONE, 1200, None,
                        pid_lookup_done, details)
            return GLib.SOURCE_REMOVE

        def message_filter(_connection, message, incoming, _data):
            if incoming and message.get_message_type() == Gio.DBusMessageType.METHOD_CALL:
                sender = message.get_sender()
                details = {"method": message.get_member(), "sender": sender,
                           "request_wall_utc": datetime.now(timezone.utc).isoformat(),
                           "request_wall_epoch": time.time(),
                           "request_boottime": time.clock_gettime(time.CLOCK_BOOTTIME),
                           "body": message.get_body().unpack() if message.get_body() else None}
                # Filters run on a GDBus worker thread. Schedule lookup on the
                # GLib main context; no nested/blocking call from the filter.
                GLib.idle_add(start_pid_lookup, details)
            return None
        monitor.add_filter(message_filter, None)
    except Exception as exc:
        emit("logind-call-monitor-unavailable", error=type(exc).__name__)

    def screen_signal(_conn, sender, _path, _iface, name, params, _data):
        emit("session-screen-signal", signal=name, sender=sender, values=params.unpack())
    if session is not None:
        session.signal_subscribe("org.gnome.ScreenSaver", "org.gnome.ScreenSaver", None,
                                 "/org/gnome/ScreenSaver", None, Gio.DBusSignalFlags.NONE,
                                 screen_signal, None)
    else:
        emit("session-screen-monitor-unavailable", reason="session bus unavailable")

    emit("armed", note="coarse samples plus logind and screen-state events; no power/wake requests")
    def sample_cb():
        nonlocal seq
        if deadline_reached(deadline_boottime, time.clock_gettime(time.CLOCK_BOOTTIME)):
            emit("duration-expired")
            loop.quit()
            return GLib.SOURCE_REMOVE
        row = snapshot(seq, process_tracker)
        stream.write(json.dumps(row, separators=(",", ":")) + "\n")
        stream.flush()
        seq += 1
        return GLib.SOURCE_CONTINUE

    GLib.idle_add(run_once, sample_cb, GLib.SOURCE_REMOVE)
    GLib.timeout_add_seconds(interval, sample_cb)
    GLib.timeout_add_seconds(duration, loop.quit)
    try:
        loop.run()
    finally:
        emit("stopped")


def proc_identity(pid):
    """Read starttime to distinguish a process from a later PID reuse."""
    try:
        actual_pid, _comm, _ticks, start = proc_stat(Path(f"/proc/{pid}/stat").read_text())
        return start if actual_pid == pid else None
    except (OSError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("output", help="new JSONL path; created exclusively")
    ap.add_argument("--interval", type=int, default=300, help="sample interval in seconds (minimum 30)")
    ap.add_argument("--duration", type=int, default=8 * 3600, help="maximum observation seconds")
    args = ap.parse_args()
    if args.interval < 30 or args.duration < args.interval:
        ap.error("interval must be >=30s and duration must be >= interval")
    os.umask(0o077)
    out = Path(args.output)
    with out.open("x", encoding="utf-8", buffering=1) as f:
        run_observer(f, args.duration, args.interval)


if __name__ == "__main__":
    main()
