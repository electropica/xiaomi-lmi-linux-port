#!/usr/bin/env python3
"""Bounded gauge-wake resuspend trial. No input values are logged."""
import json,os,select,subprocess,time
from pathlib import Path

def read(p):
 try:return Path(p).read_text().strip()
 except OSError:return None

def allowed(reason,usb,capacity,quiet,blocked):
 return (reason=='438 msoc-delta' and usb=='0' and capacity is not None
         and 20<=capacity<=100 and quiet>=6 and not blocked)

def tests():
 assert allowed('438 msoc-delta','0',70,7,False)
 for a in [('311 pon_kpdpwr_status','0',70,7,False),('438 msoc-delta','1',70,7,False),('438 msoc-delta','0',15,7,False),('438 msoc-delta','0',70,2,False),('438 msoc-delta','0',70,7,True),('438 msoc-delta','0',None,7,False)]:assert not allowed(*a)
 print('GUARD_CASES=7 PASS')

if '--self-test' in __import__('sys').argv:
 tests();raise SystemExit()
if '--run' not in __import__('sys').argv:raise SystemExit('Explicit --run required')
from gi.repository import Gio,GLib
import signal
def interrupted(signum,frame):raise SystemExit('Trial interrupted')
signal.signal(signal.SIGTERM,interrupted)
signal.signal(signal.SIGINT,interrupted)
os.umask(0o077)
out=Path('/var/tmp/lmi-gauge-resuspend-20261006-corrected.jsonl')
f=out.open('x')
fds=[]
for p in Path('/sys/class/input').glob('event*/device/name'):
 if read(p) in ('fts_ts','gpio-keys','qpnp_pon','xiaomi-touch','uinput-goodix'):
  fds.append(os.open('/dev/input/'+p.parent.parent.name,os.O_RDONLY|os.O_NONBLOCK))
if len(fds)<3:raise SystemExit('Input safety monitor incomplete')
bus=Gio.bus_get_sync(Gio.BusType.SYSTEM,None)
def inhibitors():
 try:
  rows=bus.call_sync('org.freedesktop.login1','/org/freedesktop/login1','org.freedesktop.login1.Manager','ListInhibitors',None,None,Gio.DBusCallFlags.NONE,1500,None).unpack()[0]
  return any(mode=='block' and 'sleep' in what.split(':') for what,who,why,mode,uid,pid in rows)
 except Exception:return True

def record(event,**extra):
 d={'event':event,'boottime':time.clock_gettime(time.CLOCK_BOOTTIME),'monotonic':time.monotonic()}
 for field in ('capacity','charge_counter','current_now','voltage_now','status'):
  d[field]=read('/sys/class/power_supply/battery/'+field)
 d['usb']=read('/sys/class/power_supply/usb/online')
 d['wake_reason']=read('/sys/kernel/wakeup_reasons/last_resume_reason')
 d['last_suspend_time']=read('/sys/kernel/wakeup_reasons/last_suspend_time')
 d.update(extra);f.write(json.dumps(d)+'\n');f.flush();print(event,flush=True)

alarm=Path('/sys/class/rtc/rtc0/wakealarm');owned_alarm=None
last_input=time.monotonic()
def drain():
 global last_input
 ready,_,_=select.select(fds,[],[],0)
 for fd in ready:
  try:
   data=os.read(fd,4096)
   if data:last_input=time.monotonic()
  except BlockingIOError:pass
try:
 if read(alarm) not in ('','0'):raise RuntimeError('RTC alarm already present')
 if inhibitors():raise RuntimeError('Sleep blocked or inhibitor query unavailable')
 record('armed')
 wait=time.monotonic()+600
 while read('/sys/class/power_supply/usb/online')!='0':
  drain()
  if time.monotonic()>wait:raise RuntimeError('No unplug before deadline')
  time.sleep(.5)
 record('unplugged')
 end=time.clock_gettime(time.CLOCK_BOOTTIME)+600
 r=subprocess.run(['rtcwake','-m','no','-s','600'],capture_output=True,text=True,timeout=4)
 if r.returncode:raise RuntimeError('Unable to set bounded end alarm')
 owned_alarm=read(alarm)
 prev=read('/sys/kernel/wakeup_reasons/last_suspend_time');handled=None;seen=time.monotonic();saw_resume=False
 # Explicit initial suspend: an automatic 15-minute idle policy cannot start a shorter trial.
 quiet_deadline=time.monotonic()+30
 while time.monotonic()-last_input<6:
  drain()
  if time.monotonic()>quiet_deadline:raise RuntimeError('User remains active')
  time.sleep(.5)
 drain()
 if read('/sys/class/power_supply/usb/online')!='0' or inhibitors():raise RuntimeError('Initial suspend no longer eligible')
 capacity=int(read('/sys/class/power_supply/battery/capacity'))
 if capacity<20 or time.monotonic()-last_input<6:raise RuntimeError('Initial suspend safety check failed')
 record('before-initial-suspend')
 bus.call_sync('org.freedesktop.login1','/org/freedesktop/login1','org.freedesktop.login1.Manager','Suspend',GLib.Variant('(b)',(False,)),None,Gio.DBusCallFlags.NONE,5000,None)
 while time.clock_gettime(time.CLOCK_BOOTTIME)<end:
  drain()
  if read('/sys/class/power_supply/usb/online')!='0':record('early-reconnect');break
  current=read('/sys/kernel/wakeup_reasons/last_suspend_time')
  if current!=prev:
   prev=current;seen=time.monotonic();record('wake-observed');handled=None;saw_resume=True
  reason=read('/sys/kernel/wakeup_reasons/last_resume_reason')
  try:capacity=int(read('/sys/class/power_supply/battery/capacity'))
  except (TypeError,ValueError):capacity=None
  now=time.monotonic()
  if saw_resume and current and current!=handled and now-seen>=6 and allowed(reason,'0',capacity,now-last_input,False) and not inhibitors():
   handled=current
   drain()
   if not allowed(reason,read('/sys/class/power_supply/usb/online'),capacity,time.monotonic()-last_input,False):
    record('resuspend-skipped-final-activity-check');continue
   record('resuspend-request')
   try:
    bus.call_sync('org.freedesktop.login1','/org/freedesktop/login1','org.freedesktop.login1.Manager','Suspend',GLib.Variant('(b)',(False,)),None,Gio.DBusCallFlags.NONE,5000,None)
   except Exception as e:record('resuspend-call-error',error_type=type(e).__name__)
  time.sleep(.5)
 record('finished')
finally:
 if owned_alarm and read(alarm)==owned_alarm:alarm.write_text('0\n')
 for fd in fds:os.close(fd)
 f.close()
