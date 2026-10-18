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
parser.add_argument('--round', choices=['r2'], default='r2')
args = parser.parse_args()
root = Path(__file__).resolve().parent
output = root / 'return-r2-private.txt'
summary = root / 'analysis-r2-private.json'
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
report['retrieved_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
with summary.open('x',encoding='utf-8') as f:
    json.dump(report,f,indent=2)
print(json.dumps(report,indent=2))
