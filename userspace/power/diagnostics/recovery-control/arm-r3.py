"""Attended, opt-in recovery control. Transfer only to tmpfs; no flash/reboot."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--adb', type=Path, required=True)
parser.add_argument('--duration', type=int, choices=[1800,3600,7200], required=True)
args = parser.parse_args()
folder = Path(__file__).resolve().parent
tag = 'r3-' + str(args.duration)
output = folder / ('armed-' + tag + '-private.json')
if output.exists():
    raise RuntimeError('Preserve earlier arm evidence; do not arm the same round twice')
adb = str(args.adb.resolve(strict=True))
listing = subprocess.run([adb,'devices'],capture_output=True,check=True,timeout=10).stdout.decode()
devices = [line.split() for line in listing.splitlines()[1:] if line.strip()]
if len(devices)!=1 or devices[0][1]!='recovery':
    raise RuntimeError('Exactly one authorized recovery device is required')
serial = devices[0][0]
def run(*parts):
    result = subprocess.run([adb,'-s',serial,*parts],capture_output=True,timeout=15)
    if result.returncode:
        raise RuntimeError((result.stdout+result.stderr).decode(errors='replace'))
    return result.stdout.decode('utf-8').replace('\r','')
def shell(code):
    return run('shell','-T','sh','-c',shlex.quote(code))
remote_script = '/dev/lmi-recovery-measure-' + tag + '.sh'
remote_root = '/dev/lmi-recovery-power-control-' + tag
launch_log = '/dev/lmi-recovery-launch-' + tag + '.log'
preflight = """set -e
[ "$(id -u)" = 0 ]
case "$(getprop ro.product.device)" in lmi) ;; *) exit 1;; esac
pidof recovery >/dev/null
grep -q ' /dev tmpfs ' /proc/mounts
[ "$(cat /sys/class/power_supply/usb/online)" = 1 ]
[ "$(cat /sys/module/lpm_levels/parameters/sleep_disabled)" = Y ]
[ -z "$(cat /sys/class/rtc/rtc0/wakealarm)" ]
"""
preflight += 'test ! -e '+shlex.quote(remote_script)+'\ntest ! -e '+shlex.quote(remote_root)+'\n'
preflight += 'ps -A -o ARGS | grep -E "^sh /dev/lmi-recovery-measure" && exit 1; exit 0'
shell(preflight)
source = folder/'measure-r3.sh'
expected = hashlib.sha256(source.read_bytes()).hexdigest()
run('push',str(source),remote_script)
actual = shell('sha256sum '+shlex.quote(remote_script)).split()[0]
if actual != expected:
    raise RuntimeError('Transferred source checksum mismatch')
shell('sh -n '+shlex.quote(remote_script))
shell('nohup setsid sh '+shlex.quote(remote_script)+' '+str(args.duration)+' </dev/null >'+shlex.quote(launch_log)+' 2>&1 &')
text = shell('sleep 1; cat '+shlex.quote(launch_log)+'; cat '+shlex.quote(remote_root+'/result.txt')+'; ps -A -o PID,PPID,ARGS')
if 'WAITING_FOR_UNPLUG' not in text or not any(('sh '+remote_script) in l and 'sh -c' not in l for l in text.splitlines()):
    raise RuntimeError('Collector did not confirm a detached waiting process; inspect before unplug')
report={'armed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'duration_seconds':args.duration,'source_sha256':expected,
        'waiting_for_unplug':True,'limits':'Waiting only; physical action still required. No measurement result yet.'}
with output.open('x',encoding='utf-8') as f:
    json.dump(report,f,indent=2)
print(json.dumps(report,indent=2))
