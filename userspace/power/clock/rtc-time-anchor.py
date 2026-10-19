#!/usr/bin/python3
"""Restore offline UTC from a trusted anchor without writing the PMIC RTC."""
import argparse
import json
import math
import os
from pathlib import Path
import time

STATE = Path('/var/lib/lmi-time/rtc-anchor.json')
RTC = Path('/sys/class/rtc/rtc0')
MAX_ELAPSED = 366 * 86400


def evaluate(anchor, rtc_name, rtc_epoch, system_epoch):
    if set(anchor) != {'version', 'rtc_name', 'rtc_epoch', 'unix_epoch'}:
        raise ValueError('Unexpected anchor fields')
    if anchor['version'] != 1 or anchor['rtc_name'] != rtc_name:
        raise ValueError('RTC identity or anchor version mismatch')
    if type(anchor['rtc_epoch']) is not int:
        raise ValueError('Invalid anchor RTC counter')
    if type(anchor['unix_epoch']) not in (int, float) or not math.isfinite(anchor['unix_epoch']):
        raise ValueError('Invalid trusted epoch')
    if not 1577836800 <= anchor['unix_epoch'] < 4102444800:
        raise ValueError('Trusted epoch outside supported range')
    elapsed = rtc_epoch - anchor['rtc_epoch']
    if not 0 <= elapsed <= MAX_ELAPSED:
        raise ValueError('RTC reset, epoch discontinuity or expired anchor')
    target = anchor['unix_epoch'] + elapsed
    return {'action': 'advance' if target > system_epoch + 1 else 'unchanged',
            'target_epoch': target, 'correction_seconds': target-system_epoch,
            'rtc_not_written': True}


def read_rtc():
    return (RTC/'name').read_text().strip(), int((RTC/'since_epoch').read_text().strip())


def capture(path):
    before = time.time()
    name, counter = read_rtc()
    after = time.time()
    if after-before > 1 or after < before:
        raise RuntimeError('Clock changed or capture interval too long')
    anchor = {'version': 1, 'rtc_name': name, 'rtc_epoch': counter,
              'unix_epoch': (before+after)/2}
    evaluate(anchor, name, counter, after)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.new')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(anchor, handle, sort_keys=True)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return {'action': 'captured', 'rtc_not_written': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['capture', 'check', 'restore'])
    parser.add_argument('--state', type=Path, default=STATE)
    parser.add_argument('--trusted-current-time', action='store_true')
    args = parser.parse_args()
    if args.action == 'capture':
        if not args.trusted_current_time:
            parser.error('Capture requires explicitly trusted current system time')
        report = capture(args.state)
    else:
        if args.state.stat().st_size > 4096:
            raise ValueError('Oversized anchor')
        anchor = json.loads(args.state.read_text(encoding='utf-8'))
        name, counter = read_rtc()
        report = evaluate(anchor, name, counter, time.time())
        if args.action == 'restore' and report['action'] == 'advance':
            time.clock_settime(time.CLOCK_REALTIME, report['target_epoch'])
        report['dry_run'] = args.action == 'check'
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
