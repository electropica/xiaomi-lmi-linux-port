#!/usr/bin/env python3
"""Compare matching pre/post sleep snapshots without inferring electrical power."""
import argparse
import json
import re
from analyze import records


def scalar(text, label):
    if not isinstance(text, str):
        return None
    match = re.search(r'^' + re.escape(label) + r':\s*(\d+)\s*$', text, re.MULTILINE)
    return int(match.group(1)) if match else None


def ddr_rows(text):
    if not isinstance(text, str):
        return {}
    result = {}
    for line in text.splitlines():
        match = re.search(r'^(DDR (?:LPM Stat Name:0x[0-9a-fA-F]+|Freq \d+Mhz):?)(?:\s+CP IDX:\d+)?\s+count:(\d+)\s+Duration \(ticks\):(\d+)', line)
        if match:
            result[match.group(1).rstrip(':')] = (int(match.group(2)), int(match.group(3)))
    return result


def compare(rows):
    pending = None
    results = []
    for row in rows:
        if row.get('event') != 'systemd-sleep-hook':
            continue
        if row.get('phase') == 'pre':
            pending = row
        elif row.get('phase') == 'post' and pending:
            before, pending = pending, None
            boot = before.get('boot_id')
            if not isinstance(boot, str) or not boot or boot != row.get('boot_id'):
                results.append({'status': 'identifiant de démarrage différent ou indisponible'})
                continue
            clocks = (before.get('boottime_seconds'), row.get('boottime_seconds'),
                      before.get('monotonic_seconds'), row.get('monotonic_seconds'))
            if all(isinstance(x, (int, float)) for x in clocks):
                elapsed = clocks[1] - clocks[0]
                suspended = elapsed - (clocks[3] - clocks[2])
                if elapsed < 0 or suspended < 0:
                    elapsed = suspended = None
            else:
                elapsed = suspended = None
            counters = {}
            for name in ('aosd', 'cxsd', 'ddr', 'adsp'):
                pre = before.get('qcom_stats', {}).get(name)
                post = row.get('qcom_stats', {}).get(name)
                values = {}
                for label in ('Count', 'Accumulated Duration'):
                    a, b = scalar(pre, label), scalar(post, label)
                    values[label] = (b - a) if a is not None and b is not None and b >= a else None
                counters[name] = values
            pre_ddr = ddr_rows(before.get('qcom_stats', {}).get('ddr_stats'))
            post_ddr = ddr_rows(row.get('qcom_stats', {}).get('ddr_stats'))
            ddr = {}
            for key in sorted(pre_ddr.keys() & post_ddr.keys()):
                old, new = pre_ddr[key], post_ddr[key]
                ddr[key] = {'count': new[0] - old[0] if new[0] >= old[0] else None,
                            'duration_ticks': new[1] - old[1] if new[1] >= old[1] else None}
            results.append({'status': 'paire comparable', 'pre_utc': before.get('wall_utc'),
                            'post_utc': row.get('wall_utc'), 'interval_seconds': elapsed,
                            'suspended_seconds_estimate': suspended, 'counter_deltas_raw': counters,
                            'ddr_deltas_raw': ddr})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture')
    args = parser.parse_args()
    print(json.dumps({'transitions': compare(list(records(args.capture))),
                      'limites': 'Les compteurs bruts ne mesurent pas les watts ; un zéro peut signaler un compteur non renseigné. Les horloges encadrent les hooks, pas les rails matériels.'},
                     indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
