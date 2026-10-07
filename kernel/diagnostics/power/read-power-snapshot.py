#!/usr/bin/env python3
"""Read one bounded power/boot snapshot; no writes, commands or acquisition.

Output can contain a kernel build-host identity: keep raw JSON outside Git.
--root supports a local fixture tree; it never changes the selected filesystem.
"""
import argparse
import datetime
import gzip
import hashlib
import io
import json
from pathlib import Path
import time
import zlib

FIELDS = {
    'capacity': 'capacity_pct', 'charge_counter': 'charge_counter_uAh',
    'charge_full': 'charge_full_uAh', 'charge_full_design': 'charge_full_design_uAh',
    'current_now': 'current_now_uA', 'voltage_now': 'voltage_now_uV',
    'temp': 'temperature_deciC', 'cycle_count': 'cycle_count',
    'online': 'online', 'present': 'present',
}


def read_bytes(path, limit=4096):
    try:
        with path.open('rb') as stream:
            value = stream.read(limit + 1)
        if len(value) > limit:
            return {'unavailable': 'size_limit'}
        return value
    except OSError as exc:
        return {'unavailable': exc.__class__.__name__}


def read_text(path):
    value = read_bytes(path)
    if isinstance(value, dict):
        return value
    try:
        return value.decode('utf-8').strip()
    except UnicodeError:
        return {'unavailable': 'invalid_utf8'}


def read_integer(path):
    value = read_text(path)
    if isinstance(value, dict):
        return value
    try:
        return int(value, 10)
    except ValueError:
        return {'unavailable': 'invalid_integer'}


def config_identity(root):
    compressed = read_bytes(root / 'proc/config.gz', 4 * 1024 * 1024)
    if isinstance(compressed, dict):
        return compressed
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
            data = stream.read(4 * 1024 * 1024 + 1)
        if len(data) > 4 * 1024 * 1024:
            return {'unavailable': 'expanded_size_limit'}
        if not data:
            return {'unavailable': 'empty_config'}
        return {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    except (OSError, EOFError, zlib.error):
        return {'unavailable': 'invalid_gzip'}


def snapshot(root):
    supplies = {}
    for name in ('battery', 'bms', 'usb'):
        base = root / 'sys/class/power_supply' / name
        # Missing fields remain unavailable rather than becoming zero.
        supplies[name] = {label: read_integer(base / field) for field, label in FIELDS.items()}
        for field in ('status', 'health', 'battery_type'):
            supplies[name][field] = read_text(base / field)
    compatible = read_bytes(root / 'sys/firmware/devicetree/base/compatible')
    if isinstance(compatible, bytes):
        compatible = compatible.decode('utf-8', errors='replace').rstrip('\0').split('\0')
    return {
        'schema_version': 1,
        'phone_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'monotonic_seconds': time.monotonic(),
        'boottime_seconds': time.clock_gettime(time.CLOCK_BOOTTIME),
        'kernel_release': read_text(root / 'proc/sys/kernel/osrelease'),
        'kernel_version': read_text(root / 'proc/version'),
        'ikconfig': config_identity(root),
        'compatible': compatible,
        'uptime': read_text(root / 'proc/uptime'),
        'rtc_alarm': read_text(root / 'sys/class/rtc/rtc0/wakealarm'),
        'cpu_idle_sleep_disabled': read_text(root / 'sys/module/lpm_levels/parameters/sleep_disabled'),
        'supplies': supplies,
        'limits': [
            'Sequential field reads are not an atomic sample.',
            'Timestamp is from this machine; elapsed off time needs a separate trusted host/operator reference.',
            'Kernel banner and IKCONFIG do not prove executable image identity.',
            'Bootup and USB charging affect a return sample; this does not independently measure off-state current or physical capacity.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('/'), help='read-only filesystem root (fixtures)')
    args = parser.parse_args()
    print(json.dumps(snapshot(args.root), indent=2))


if __name__ == '__main__':
    main()
