"""Retrieve recovery result and restoration state using native Windows ADB."""
import argparse
import datetime
import json
from pathlib import Path
import shlex
import subprocess
from analyze import analyze

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--adb', type=Path, required=True)
parser.add_argument('--round', choices=['r3-1800','r3-3600','r3-7200'], default='r3-1800')
args = parser.parse_args()
root = Path(__file__).resolve().parent
output = root / ('return-' + args.round + '-private.txt')
summary = root / ('analysis-' + args.round + '-private.json')
if output.exists() or summary.exists():
    raise RuntimeError('Preserve existing result files')
code = """set -e
pidof recovery >/dev/null
cat /dev/lmi-recovery-power-control-r2/result.txt
printf '\nCURRENT_STATE\n'
printf 'sleep_disabled='; cat /sys/module/lpm_levels/parameters/sleep_disabled
for n in soc:qcom,npu-npu-llcc-bw soc:qcom,npu-llcc-ddr-bw soc:qcom,npudsp-npu-ddr-bw; do
 printf 'governor:%s=' "$n"; cat /sys/class/devfreq/$n/governor
done
printf 'rtc_alarm='; cat /sys/class/rtc/rtc0/wakealarm; printf '\n'
printf 'usb_online='; cat /sys/class/power_supply/usb/online
printf 'battery_status='; cat /sys/class/power_supply/battery/status
printf '\nLAUNCH_LOG\n'; cat /dev/lmi-recovery-launch-r2.log
"""
code = code.replace('-r2', '-' + args.round)
result = subprocess.run([str(args.adb), 'shell', '-T', 'sh', '-c', shlex.quote(code)],
                        capture_output=True, timeout=15)
if result.returncode:
    raise RuntimeError((result.stdout+result.stderr).decode(errors='replace'))
text = result.stdout.decode('utf-8').replace('\r', '')
output.write_text(text, encoding='utf-8')
if 'CURRENT_STATE' not in text:
    raise RuntimeError('Missing restoration state')
report = analyze(text.split('CURRENT_STATE',1)[0])
state = text.split('CURRENT_STATE',1)[1].split('LAUNCH_LOG',1)[0]
values = dict(line.split('=',1) for line in state.splitlines() if '=' in line)
expected = {'sleep_disabled':'Y', 'rtc_alarm':'', 'usb_online':'1', 'battery_status':'Charging'}
for node in ('soc:qcom,npu-npu-llcc-bw','soc:qcom,npu-llcc-ddr-bw','soc:qcom,npudsp-npu-ddr-bw'):
    expected['governor:'+node] = 'performance'
report['restoration_current_values'] = values
report['restoration_verified'] = all(values.get(key)==value for key,value in expected.items())
duration = int(args.round.split('-')[1])
report['requested_seconds'] = duration
report['valid_control'] = (report['valid_control'] and
                           report.get('interval_seconds', 0) >= duration - 3 and
                           report.get('last_suspend_seconds', 0) >= duration * .95)
intervals = []
samples = report['samples']
previous = samples.get('BEFORE')
for name, current in samples.items():
    if not name.startswith('WAKE_'):
        continue
    if previous is None:
        break
    dt = current['uptime'] - previous['uptime']
    slept = current.get('last_sleep', [0, 0])[1]
    supplies = [s['fields'] for s in (previous, current)]
    valid = (dt > 0 and slept > 0 and slept <= dt + 2 and slept / dt > .99 and
             all(s.get('usb:online') == '0' and s.get('battery:status') == 'Discharging' for s in supplies))
    item = {'end_sample': name, 'seconds': dt, 'suspended_seconds': slept,
            'qualified': valid, 'counter_rates_ma': {}, 'filtered_endpoint_ma': None}
    if valid:
        for field in ('charge_counter', 'charge_counter_shadow', 'charge_now_raw'):
            key = 'bms:' + field
            scale = 'bms:charge_full_design' if field == 'charge_now_raw' else 'bms:charge_full'
            if all(key in s and scale in s for s in supplies) and supplies[0][scale] == supplies[1][scale]:
                delta = int(supplies[0][key]) - int(supplies[1][key])
                item['counter_rates_ma'][field] = delta * 3.6 / dt if delta >= 0 else None
        value = current['fields'].get('bms:current_avg')
        if value is not None:
            item['filtered_endpoint_ma'] = int(value) / 1000
    intervals.append(item)
    previous = current
report['intervals'] = intervals
report['limits'].append('The30min variant does not establish the later1-2h Android regime; filtered endpoints are not interval-average current.')
report['retrieved_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
with summary.open('x',encoding='utf-8') as f:
    json.dump(report,f,indent=2)
print(json.dumps(report,indent=2))
