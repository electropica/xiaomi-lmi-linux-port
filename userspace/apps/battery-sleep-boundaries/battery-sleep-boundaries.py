#!/usr/bin/env python3
"""Capture battery values at systemd sleep boundaries; never wake the system."""
import csv
import datetime
import io
import os
import re
import stat
import sys
import time
from pathlib import Path

FIELDS = ('phase', 'boot_id', 'wall_utc', 'boottime_s', 'monotonic_s',
          'capacity_pct', 'status', 'voltage_uv', 'current_ua',
          'charge_counter_uah', 'temp_deci_c', 'suspend_success', 'msoc', 'msoc_mirror')
ROOT = Path('/')
OUTPUT_DIR = Path('/var/lib/battery-diag')


def read_value(root, path):
    try:
        value = (root / path.lstrip('/')).read_text(encoding='utf-8').strip()
        return value if value else 'N/A:empty'
    except OSError as exc:
        return 'N/A:' + str(exc.errno)


def read_msoc(root):
    path = root / 'sys/kernel/debug/regmap/0-02/registers'
    try:
        fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
        try:
            result = []
            for address in (0x4009, 0x400a):
                line = os.pread(fd, 9, address * 9)
                match = re.fullmatch(rb'([0-9a-fA-F]{4}): ([0-9a-fA-F]{2}|XX)\n', line)
                if not match or int(match.group(1), 16) != address or match.group(2) == b'XX':
                    result.append('N/A:format')
                else:
                    result.append(str(int(match.group(2), 16)))
            return result
        finally:
            os.close(fd)
    except OSError as exc:
        return ['N/A:' + str(exc.errno)] * 2


def snapshot(root, phase, clock=time.clock_gettime):
    if phase not in ('pre', 'post'):
        raise ValueError('invalid phase')
    battery = '/sys/class/power_supply/qcom-battery/'
    raw, mirror = read_msoc(root)
    return (phase, read_value(root, '/proc/sys/kernel/random/boot_id'),
            datetime.datetime.now(datetime.timezone.utc).isoformat(),
            f'{clock(time.CLOCK_BOOTTIME):.6f}', f'{clock(time.CLOCK_MONOTONIC):.6f}',
            read_value(root, battery+'capacity'), read_value(root, battery+'status'),
            read_value(root, battery+'voltage_now'), read_value(root, battery+'current_now'),
            read_value(root, battery+'charge_counter'), read_value(root, battery+'temp'),
            read_value(root, '/sys/power/suspend_stats/success'), raw, mirror)


def append_record(directory, record):
    # The containing directory must be created by the package as root-owned;
    # never follow an untrusted final path while running as root.
    dfd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        info = os.fstat(dfd)
        if info.st_uid != 0 or info.st_mode & 0o022:
            raise PermissionError('unsafe output directory')
        fd = os.open('sleep-boundaries.csv', os.O_RDWR | os.O_APPEND | os.O_CREAT |
                     os.O_CLOEXEC | os.O_NOFOLLOW, 0o640, dir_fd=dfd)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
                raise PermissionError('unsafe output file')
            if info.st_size and os.pread(fd, 4096, 0).split(b'\n', 1)[0] != ','.join(FIELDS).encode():
                raise ValueError('existing CSV header does not match')
            text = io.StringIO(newline='')
            writer = csv.writer(text, lineterminator='\n')
            if info.st_size == 0:
                writer.writerow(FIELDS)
            writer.writerow(record)
            payload = text.getvalue().encode('utf-8')
            if os.write(fd, payload) != len(payload):
                raise OSError('short write')
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        os.close(dfd)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ('pre', 'post'):
        raise SystemExit('expected pre or post')
    append_record(OUTPUT_DIR, snapshot(ROOT, sys.argv[1]))


if __name__ == '__main__':
    main()
