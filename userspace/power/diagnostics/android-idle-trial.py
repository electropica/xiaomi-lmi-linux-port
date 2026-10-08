"""Windows-only operator-triggered Android idle baseline/return helper.

Arm shortly before unplugging, not hours ahead. No scheduler or recording.
Private output files are never published or overwritten.
"""
from pathlib import Path
import argparse,datetime,json,os,re,subprocess,shlex

def trial_paths(trial_id,output):
 if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',trial_id):
  raise ValueError('Use a short alphanumeric trial ID; no paths or shell syntax.')
 return '/data/local/tmp/lmi-android-idle-'+trial_id,Path(output).resolve()/trial_id

def flags(text):
 items=text.strip().splitlines()
 if len(items)!=3 or any(x not in ('0','1') for x in items):
  raise ValueError('Radio states must be three stable boolean values.')
 return items

def powered(text):
 fields=dict(re.findall(r'^\s*(AC powered|USB powered|Wireless powered|Dock powered):\s*(true|false)\s*$',text,re.M))
 if len(fields)!=4:raise ValueError('Incomplete external-power flags; cannot arm safely.')
 return any(value=='true' for value in fields.values())

RADIOS='settings get global airplane_mode_on; settings get global wifi_on; settings get global bluetooth_on'
FIRST='echo BOOT_ID; cat /proc/sys/kernel/random/boot_id; echo BOOT_UPTIME; cat /proc/uptime; echo DEVICE_CLOCK; date -Iseconds; echo BATTERY; dumpsys battery'

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('action',choices=['arm','return'])
 parser.add_argument('--trial-id',required=True)
 parser.add_argument('--output',type=Path,required=True)
 parser.add_argument('--adb',type=Path,required=True)
 args=parser.parse_args()
 if os.name!='nt':parser.error('Run from Windows; this does not use WSL to contact the phone.')
 adb=args.adb.resolve();assert adb.is_file() and adb.name.lower()=='adb.exe'
 base,out=trial_paths(args.trial_id,args.output)
 def run(*arguments):
  return subprocess.run([str(adb),'-d',*arguments],capture_output=True,text=True,timeout=25,check=True).stdout
 def radios():return flags(run('shell',RADIOS))
 def restore(original):
  commands=['cmd connectivity airplane-mode '+('enable' if original[0]=='1' else 'disable'),
            'cmd wifi set-wifi-enabled '+('enabled' if original[1]=='1' else 'disabled'),
            'cmd bluetooth_manager '+('enable' if original[2]=='1' else 'disable')]
  run('shell','; '.join(commands))
  actual=radios();assert actual==original,'Original radio state not yet restored'
  print('RESTORED_RADIOS='+repr(actual))
 assert run('get-state').strip()=='device'
 if args.action=='arm':
  assert not out.exists(),'Trial ID already used; no overwrite'
  version=run('shell','getprop ro.lineage.version').strip()
  assert version,'Expected LineageOS test handset'
  original=radios()
  out.mkdir(parents=True)
  metadata={'trial_id':args.trial_id,'phone_directory':base,'host_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original_radios':original,'lineage_version':version}
  (out/'metadata-private.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
  plugged=run('shell',FIRST)
  assert powered(plugged),'Expected external power before arming'
  (out/'plugged-before-arm-private.txt').write_text(plugged,encoding='utf-8')
  assert run('shell','test ! -e '+shlex.quote(base)+' && mkdir -m 700 '+shlex.quote(base))==''
  run('push',str(Path(__file__).with_name('android-idle-baseline.sh')),base+'/baseline.sh')
  try:
   run('shell','cmd connectivity airplane-mode enable; cmd wifi set-wifi-enabled disabled; cmd bluetooth_manager disable')
   assert radios()==['1','0','0']
   command='nohup /system/bin/sh '+shlex.quote(base+'/baseline.sh')+' '+shlex.quote(base)+' '+' '.join(original)+' >'+shlex.quote(base+'/collector.log')+' 2>&1 </dev/null & echo $!'
   pid=run('shell',command).strip(); assert pid.isdigit()
   metadata['baseline_pid']=int(pid)
   (out/'metadata-private.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
   print('ARMED: unplug within 15 minutes. Baseline ends after unplug; no overnight logger.')
  except Exception:
   restore(original);raise
 else:
  metadata=json.loads((out/'metadata-private.json').read_text())
  assert metadata['trial_id']==args.trial_id
  assert metadata['phone_directory']==base
  original=flags('\n'.join(metadata['original_radios']))
  assert not (out/'first-return-private.txt').exists(),'First return preserved; recover missing data separately.'
  # Preserve battery immediately, before any other phone reads or radio changes.
  after=run('shell',FIRST)
  with (out/'first-return-private.txt').open('x',encoding='utf-8') as f:f.write(after)
  (out/'return-host-time-private.json').write_text(json.dumps({'host_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}))
  try:
   for name,command in [('before-private.txt','cat '+shlex.quote(base+'/before.txt')),('collector-private.log','cat '+shlex.quote(base+'/collector.log')),('history-private.txt','dumpsys batterystats --history'),('batterystats-private.txt','dumpsys batterystats --charged'),('radios-before-restoration-private.txt',RADIOS)]:
    (out/name).write_text(run('shell',command),encoding='utf-8')
   print('PRIVATE_RETURN_DATA_SAVED='+str(out))
  finally:restore(original)

if __name__=='__main__':main()
