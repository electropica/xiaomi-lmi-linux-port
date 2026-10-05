import argparse,json,os,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('phase',choices=['wifi-on','wifi-off']);a=p.parse_args()
out=Path('/var/tmp/lmi-battery-ab-20261005-'+a.phase+'.jsonl')
if out.exists():raise SystemExit('Existing result: refusing overwrite')
def read(p):
 try:return Path(p).read_text().strip()
 except OSError:return None
def call(argv,timeout=10):return subprocess.run(argv,capture_output=True,text=True,timeout=timeout)
radio=call(['nmcli','radio','wifi']); original=radio.stdout.strip()
if radio.returncode or original not in ('enabled','disabled'):raise SystemExit('Unknown original Wi-Fi state')
if read('/sys/class/rtc/rtc0/wakealarm') not in ('',None,'0'):raise SystemExit('Existing RTC alarm: refusing overwrite')
os.umask(0o077)
def record(label,extra=None):
 d={'phase':a.phase,'event':label,'boottime':time.clock_gettime(time.CLOCK_BOOTTIME),'monotonic':time.monotonic()}
 for supply in ('battery','bms','usb'):
  for field in ('capacity','current_now','voltage_now','charge_counter','temp','online','status'):
   d[supply+'/'+field]=read('/sys/class/power_supply/'+supply+'/'+field)
 for name in ('success','fail'):d['suspend/'+name]=read('/sys/power/suspend_stats/'+name)
 for name,path in [('wake_reason','/sys/kernel/wakeup_reasons/last_resume_reason'),('suspend_time','/sys/kernel/wakeup_reasons/last_suspend_time'),('cpu_idle_disabled','/sys/module/lpm_levels/parameters/sleep_disabled')]:d[name]=read(path)
 d['wifi']=call(['nmcli','radio','wifi']).stdout.strip()
 if extra:d.update(extra)
 with out.open('a') as f:f.write(json.dumps(d)+'\n');f.flush()
 print(label,flush=True)
 return d
try:
 r=call(['nmcli','radio','wifi','on' if a.phase=='wifi-on' else 'off'])
 if r.returncode:raise RuntimeError('Unable to set Wi-Fi state')
 record('armed',{'original_wifi':original})
 deadline=time.monotonic()+600
 while read('/sys/class/power_supply/usb/online')!='0':
  if time.monotonic()>deadline:record('cancelled-no-unplug');raise SystemExit(2)
  time.sleep(1)
 record('unplugged');time.sleep(12)
 record('before-deep')
 r=call(['rtcwake','-m','mem','-s','300'],timeout=380)
 record('after-deep',{'rtcwake_returncode':r.returncode,'rtcwake_stderr':r.stderr[-600:]})
 if r.returncode:raise RuntimeError('Suspend test did not complete normally')
 record('finished')
finally:
 r=call(['nmcli','radio','wifi','on' if original=='enabled' else 'off'],timeout=45)
 record('radio-restored',{'restore_returncode':r.returncode})
