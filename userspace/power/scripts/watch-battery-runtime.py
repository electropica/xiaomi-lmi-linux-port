#!/usr/bin/env python3
"""Finite, read-only fuel-gauge sampling; no wake alarm or power-policy writes."""
import argparse
import json
import os
from pathlib import Path
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--hours', type=float, default=6)
parser.add_argument('--interval', type=float, default=600)
args = parser.parse_args()
if not 0 < args.hours <= 24 or not 10 <= args.interval <= 3600:
    parser.error('hours must be in (0,24], interval in [10,3600] seconds')
os.umask(0o077)

def read(path):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None

start = time.clock_gettime(time.CLOCK_BOOTTIME)
with args.output.open('x') as stream:
    while True:
        boot = time.clock_gettime(time.CLOCK_BOOTTIME)
        sample = {'boottime': boot, 'monotonic': time.monotonic()}
        for supply in ('battery','usb'):
            for key in ('online','status','capacity','charge_counter','current_now','voltage_now','temp'):
                value = read('/sys/class/power_supply/'+supply+'/'+key)
                if value is not None:
                    sample[supply+'/'+key] = value
        for key in ('success','fail'):
            sample['suspend/'+key] = read('/sys/power/suspend_stats/'+key)
        sample['cpu_idle'] = read('/sys/module/lpm_levels/parameters/sleep_disabled')
        sample['finished'] = boot-start >= args.hours*3600
        stream.write(json.dumps(sample)+'\n')
        stream.flush()
        if sample['finished']:
            break
        # CLOCK_MONOTONIC sleep pauses during system suspend; this is not a
        # wake alarm. A delayed sample is taken only after a normal resume.
        time.sleep(min(args.interval,args.hours*3600-(boot-start)))
