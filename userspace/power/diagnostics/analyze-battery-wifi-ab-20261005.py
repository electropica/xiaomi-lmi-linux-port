import json
from pathlib import Path
for phase in ('wifi-on','wifi-off'):
 p=Path('/var/tmp/lmi-battery-ab-20261005-'+phase+'.jsonl')
 if not p.exists():continue
 rows=[json.loads(l) for l in p.read_text().splitlines()]
 print('EVENTS',phase,[r['event'] for r in rows])
 by={r['event']:r for r in rows}
 if 'before-deep' not in by or 'after-deep' not in by:continue
 a,b=by['before-deep'],by['after-deep']
 sec=b['boottime']-a['boottime'];mono=b['monotonic']-a['monotonic']
 charge=int(a['battery/charge_counter'])-int(b['battery/charge_counter'])
 d={'phase':phase,'elapsed_seconds':sec,'awake_monotonic_seconds':mono,'charge_drop_uAh':charge,'average_current_mA':charge*3.6/sec,'capacity_before':a['battery/capacity'],'capacity_after':b['battery/capacity'],'current_after_uA':b['battery/current_now'],'temperature_before':a['battery/temp'],'temperature_after':b['battery/temp'],'suspend_success_delta':int(b['suspend/success'])-int(a['suspend/success']),'suspend_fail_delta':int(b['suspend/fail'])-int(a['suspend/fail']),'wake_reason':b['wake_reason'],'rtcwake_returncode':b['rtcwake_returncode'],'radio_restored':by.get('radio-restored',{}).get('wifi'),'usb_before':a['usb/online'],'usb_after':b['usb/online']}
 print('RESULT',json.dumps(d))
