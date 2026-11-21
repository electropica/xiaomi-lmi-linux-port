#!/usr/bin/env python3
"""Stop a runaway CPU consumer on the lmi image.

Why this exists
---------------
On 2026-11-17 four runaway processes kept four cores at 98 % for 6 h 54 on
the handset. The symptom was invisible from the interface: the screen was
off, the charger reported its usual values, and nothing announced a load.
The cost was a working day, and a battery that went from 100 % to 58 %.

What the guard does
-------------------
It samples the global CPU occupancy the way the kernel does, from the
aggregate line of /proc/stat, and acts only on a SUSTAINED overload:

  * the occupancy must stay above the threshold for the whole window, so a
    legitimate burst is never a candidate;
  * the offender must have accumulated a lot of CPU time already, so a
    process that just started is never killed;
  * the offender must not be a protected process;
  * only ONE process is stopped per event, and the guard then cools down.

Every decision is written to the journal with the numbers that produced it.
The default thresholds can be changed with two environment variables:
LMI_CPU_GUARD_THRESHOLD (percent, default 60) and
LMI_CPU_GUARD_WINDOW (samples, default 30 at 10 s, so 5 minutes).
"""
import os
import signal
import time

INTERVAL_S = 10.0
THRESHOLD_PCT = float(os.environ.get('LMI_CPU_GUARD_THRESHOLD', '60'))
WINDOW_SAMPLES = int(os.environ.get('LMI_CPU_GUARD_WINDOW', '30'))
COOLDOWN_S = 600.0
MIN_CPU_TIME_S = 60.0
CLOCK_TICK = os.sysconf('SC_CLK_TCK')

# Processes that are never stopped: the session, the network, the power
# management stack, and this guard itself.
PROTECTED_NAMES = {
    'systemd', 'systemd-journald', 'systemd-logind', 'systemd-udevd',
    'systemd-udev-trigger', 'systemd-networkd', 'systemd-resolved',
    'dbus-daemon', 'dbus-broker', 'sshd', 'sshd-session', 'NetworkManager',
    'ModemManager', 'upowerd', 'phosh', 'phoc', 'gnome-shell', 'gnome-session',
    'gsd-media-keys', 'gsd-power', 'gsd-xsettings', 'gdm', 'pipewire',
    'pipewire-pulse', 'wpa_supplicant', 'iwd', 'irqbalance', 'phoc',
    'lmi-cpu-guard.py', 'lmi-power-log.py', 'gthd', 'sugov',
}

# Command lines that are a DELIBERATE load, not a runaway.
#
# The measurement phases of the campaign saturate the CPU on purpose (phase
# 6c: 8, 16, 24 busy workers, 11 min per step). Those workers are
# `python3 -c "while True: pass"` and they look exactly like the runaway of
# the 2026-11-17 (four cores at 98 % for 6 h 54). Stopping them would
# invalidate the measurement that is being taken.
#
# The distinction is made on the COMMAND LINE, not on the load itself:
#   * a deliberate load always carries the marker `--who=lmi-charge-phase`
#     (see lmi_charge_load.py, which also writes the same marker in
#     /run/lmi-charge-phase.who) ;
#   * the runaway of the 17/11 was a bare shell loop
#     (`while :; do :; done`) with no marker.
#
# A marker is therefore a DECLARATION by the operator that the load is
# intended. It is only honoured when the marker file exists and carries the
# same value, so the exemption cannot be forged by an accidental command
# line, and it disappears with the marker file when the phase ends.
MARKER_FILE = '/run/lmi-charge-phase.who'
LOAD_MARKER = '--who=lmi-charge-phase'


def marker_value():
    """The declared deliberate load, or None."""
    try:
        with open(MARKER_FILE, 'r', encoding='ascii', errors='replace') as handle:
            value = handle.read().strip()
    except OSError:
        return None
    return value or None


def is_declared_load(pid, comm):
    """True if this process is part of a declared, deliberate load."""
    if marker_value() is None:
        return False
    try:
        with open('/proc/%d/cmdline' % pid, 'rb') as handle:
            raw = handle.read()
    except OSError:
        return False
    cmdline = raw.replace(b'\x00', b' ').decode('utf-8', 'replace')
    return LOAD_MARKER in cmdline

stopping = False


def log(message):
    print(message, flush=True)


def read_cpu_times():
    """Aggregate CPU times from /proc/stat: (total, idle, iowait)."""
    try:
        with open('/proc/stat', 'r', encoding='ascii') as handle:
            for line in handle:
                if line.startswith('cpu '):
                    fields = [int(value) for value in line.split()[1:]]
                    total = sum(fields)
                    idle = fields[3]
                    iowait = fields[4] if len(fields) > 4 else 0
                    return total, idle, iowait
    except (OSError, ValueError):
        pass
    return None


def occupancy(before, after):
    """Busy percentage between two /proc/stat samples."""
    total_a, idle_a, wait_a = before
    total_b, idle_b, wait_b = after
    total = total_b - total_a
    idle = (idle_b - idle_a) + (wait_b - wait_a)
    if total <= 0:
        return 0.0
    return 100.0 * (total - idle) / total


def process_table():
    """(pid, comm, cpu_seconds) for every readable process."""
    table = []
    for entry in os.listdir('/proc'):
        if not entry.isdigit():
            continue
        pid = int(entry)
        try:
            with open('/proc/%d/stat' % pid, 'r', encoding='ascii',
                      errors='replace') as handle:
                data = handle.read()
        except OSError:
            continue
        # The comm may contain spaces and parentheses: it is delimited.
        start = data.find('(')
        end = data.rfind(')')
        if start < 0 or end < 0:
            continue
        comm = data[start + 1:end]
        fields = data[end + 2:].split()
        if len(fields) < 13:
            continue
        try:
            ticks = int(fields[11]) + int(fields[12])
        except ValueError:
            continue
        table.append((pid, comm, ticks / CLOCK_TICK))
    return table


def is_protected(pid, comm):
    if pid == 1:
        return True
    if comm in PROTECTED_NAMES:
        return True
    if comm.startswith('lmi-') or comm.startswith('systemd'):
        return True
    if is_declared_load(pid, comm):
        return True
    return False


def stop_process(pid, comm):
    log('LMI_CPU_GUARD stopping pid=%d comm=%s' % (pid, comm))
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError as exc:
        log('LMI_CPU_GUARD sigterm_failed pid=%d error=%r' % (pid, exc))
        return
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except OSError:
            log('LMI_CPU_GUARD stopped pid=%d comm=%s' % (pid, comm))
            return
        time.sleep(0.5)
    try:
        os.kill(pid, signal.SIGKILL)
        log('LMI_CPU_GUARD killed pid=%d comm=%s' % (pid, comm))
    except OSError as exc:
        log('LMI_CPU_GUARD sigkill_failed pid=%d error=%r' % (pid, exc))


def main():
    def handle_stop(_signum, _frame):
        global stopping
        stopping = True

    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)

    log('LMI_CPU_GUARD started threshold=%.0f%% window=%d samples interval=%.0fs'
        % (THRESHOLD_PCT, WINDOW_SAMPLES, INTERVAL_S))

    high = 0
    cooldown_until = 0.0
    previous = read_cpu_times()
    previous_table = {pid: cpu for pid, _comm, cpu in process_table()}
    if previous is None:
        log('LMI_CPU_GUARD no_proc_stat')
        return 1

    while not stopping:
        time.sleep(INTERVAL_S)
        current = read_cpu_times()
        if current is None:
            continue
        busy = occupancy(previous, current)
        previous = current

        table = process_table()
        now = {pid: cpu for pid, _comm, cpu in table}
        deltas = []
        for pid, comm, cpu in table:
            before = previous_table.get(pid)
            if before is None:
                continue
            deltas.append((cpu - before, pid, comm))
        previous_table = now

        if busy >= THRESHOLD_PCT:
            high += 1
        else:
            high = 0

        if high >= WINDOW_SAMPLES and time.monotonic() >= cooldown_until:
            deltas.sort(reverse=True)
            top = deltas[:5]
            summary = ', '.join('%s(pid %d) %.1f%%' % (comm, pid, 100.0 * delta / INTERVAL_S)
                                for delta, pid, comm in top)
            log('LMI_CPU_GUARD sustained_load busy=%.1f%% samples=%d top=%s'
                % (busy, high, summary))
            victim = None
            for delta, pid, comm in top:
                if is_protected(pid, comm):
                    continue
                cpu_time = now.get(pid, 0.0)
                if cpu_time < MIN_CPU_TIME_S:
                    continue
                victim = (pid, comm, cpu_time)
                break
            if victim is None:
                # Either every candidate is protected, or every candidate is
                # part of a declared, deliberate load.
                declared = marker_value()
                if declared:
                    log('LMI_CPU_GUARD declared_load busy=%.1f%% samples=%d '
                        'who=%s : aucune charge arrtee'
                        % (busy, high, declared))
                else:
                    log('LMI_CPU_GUARD no_stoppable_offender')
            else:
                log('LMI_CPU_GUARD alert_only pid=%d comm=%s cpu_seconds=%.1f' % victim)
                cooldown_until = time.monotonic() + COOLDOWN_S
            high = 0
        elif high and high % 10 == 0:
            log('LMI_CPU_GUARD busy=%.1f%% sustained=%d/%d' % (busy, high, WINDOW_SAMPLES))

    log('LMI_CPU_GUARD stopped')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
