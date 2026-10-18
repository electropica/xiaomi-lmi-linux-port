"""Parse private recovery control log; do not interpret plugged endpoints."""
import argparse
import json
from pathlib import Path


def analyze(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    samples = {}
    current = None
    previous = ''
    for line in lines:
        if line.startswith('SNAPSHOT:'):
            current = {'fields': {}}
            samples[line.split(':', 1)[1]] = current
            previous = 'SNAPSHOT'
            continue
        if current is None:
            continue
        if previous == 'SNAPSHOT':
            current['uptime'] = float(line.split()[0])
        elif line.startswith(('battery:', 'bms:', 'usb:')) and '=' in line:
            key, value = line.split('=', 1)
            current['fields'][key] = value
        elif previous == 'LAST_SUSPEND':
            values = [float(x) for x in line.split()]
            if len(values) == 2:
                current['last_sleep'] = values
        previous = line
    report = {'completed': 'FINISHED' in lines,
              'restoration_logged': 'RESTORATION' in lines,
              'samples': samples, 'limits': [
                  'Gauge-derived estimates, not calibrated physical current.',
                  'Counter intervals include brief awake endpoint reads.',
                  'Recovery is not full Android initialization.']}
    if not all(name in samples for name in ('BEFORE', 'AFTER')):
        report['valid_control'] = False
        report['reason'] = 'Incomplete endpoint pair'
        return report
    before, after = samples['BEFORE'], samples['AFTER']
    dt = after['uptime'] - before['uptime']
    wake_samples = [sample for name, sample in samples.items() if name.startswith('WAKE_')]
    sleep = sum(sample.get('last_sleep', [0, 0])[1] for sample in wake_samples) if wake_samples else after.get('last_sleep', [0, 0])[1]
    disconnected = all(s['fields'].get('usb:online') == '0' for s in (before, after))
    discharging = all(s['fields'].get('battery:status') == 'Discharging' for s in (before, after))
    report.update(interval_seconds=dt, last_suspend_seconds=sleep,
                  endpoints_unplugged=disconnected, endpoints_discharging=discharging,
                  valid_control=(report['completed'] and disconnected and discharging and
                                 dt >= 150 and sleep >= 150 and sleep <= dt + 2))
    if dt > 0 and disconnected and discharging:
        report['counter_estimates_mA'] = {}
        for field in ('charge_counter', 'charge_counter_shadow', 'charge_now_raw'):
            key = 'bms:' + field
            if key in before['fields'] and key in after['fields']:
                delta = int(before['fields'][key]) - int(after['fields'][key])
                report['counter_estimates_mA'][field] = delta * 3.6 / dt
        report['raw_capacity_scale_warning'] = 'Raw and learned counters use different capacity scales; no direct equivalence asserted.'
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = analyze(args.input.read_text(encoding='utf-8'))
    with args.output.open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))
