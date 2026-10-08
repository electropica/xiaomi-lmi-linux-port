#!/usr/bin/env python3
"""Private finite off-state comparison: no suspend, restart or gauge writes."""
import json,time,os,sys
from pathlib import Path
ROOT=Path('/var/lib/lmi-power-tests/off-comparison-20261008')
def read(path):
 try:return Path(path).read_text().strip()
 except OSError:return None
def sample(label):
 d={'label':label,'epoch':time.time(),'boottime':time.clock_gettime(time.CLOCK_BOOTTIME),'monotonic':time.monotonic(),'boot_id':read('/proc/sys/kernel/random/boot_id'),'kernel':read('/proc/version'),'usb_online':read('/sys/class/power_supply/usb/online')}
 for supply in ('battery','bms'):
  d[supply]={n:read('/sys/class/power_supply/'+supply+'/'+n) for n in ('capacity','charge_counter','charge_full','charge_full_design','current_now','voltage_now','temp','status','battery_type')}
 return d
def save(name,data):
 p=ROOT/name
 with p.open('x') as f:json.dump(data,f,indent=2)
 p.chmod(0o600)
if sys.argv[1:]==['--before-off']:
 end=time.monotonic()+120
 while read('/sys/class/power_supply/usb/online')!='0':
  if time.monotonic()>end:raise SystemExit('No unplug before deadline')
  time.sleep(.5)
 time.sleep(12)
 d=sample('before-manual-poweroff')
 if d['usb_online']!='0':raise SystemExit('Reconnected before sample')
 save('before-off.json',d)
 print('BEFORE_OFF_SAVED',flush=True)
elif sys.argv[1:]==['--next-boot']:
 try:
  samples=[]
  end=time.monotonic()+35
  while read('/sys/class/power_supply/battery/capacity') is None:
   if time.monotonic()>end:raise RuntimeError('Battery unavailable at boot')
   time.sleep(.5)
  samples.append(sample('first-battery-available'))
  time.sleep(5);samples.append(sample('five-seconds-later'))
  time.sleep(10);samples.append(sample('fifteen-seconds-later'))
  save('next-boot.json',samples)
 finally:(ROOT/'armed').unlink(missing_ok=True)
else:raise SystemExit('Explicit mode required')
