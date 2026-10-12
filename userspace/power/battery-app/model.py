"""Read-only battery data; charge-counter quotients are modelled estimates."""
import csv, datetime, html, json, math, os, time
from collections import deque
from pathlib import Path

FIELDS = ('capacity', 'status', 'charge_counter', 'charge_full', 'charge_full_design',
          'temp', 'current_now', 'voltage_now')
METHODS = ('charge_counter', 'charge_counter_shadow', 'charge_now_raw')
STATE = Path(os.environ.get('XDG_STATE_HOME', str(Path.home()/'.local/state')))/'lmi-battery'
MAX_VIEW_ROWS = 5000
MAX_VIEW_BYTES = 8 * 1024 * 1024

def read(path):
    try: return Path(path).read_text().strip()
    except OSError: return None

def number(value):
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (ValueError, TypeError): return None

def snapshot(event='sample', root=Path('/sys')):
    supplies = {}
    for name in ('battery', 'bms'):
        fields = FIELDS + (('charge_counter_shadow', 'charge_now_raw') if name=='bms' else ())
        supplies[name] = {key:read(root/'class/power_supply'/name/key) for key in fields}
    return {'event':event, 'epoch':time.time(), 'boottime':time.clock_gettime(time.CLOCK_BOOTTIME),
            'monotonic':time.monotonic(), 'boot_id':read('/proc/sys/kernel/random/boot_id'),
            'usb':read(root/'class/power_supply/usb/online'), 'supplies':supplies,
            'wake_reason':read(root/'kernel/wakeup_reasons/last_resume_reason')}

def iter_rows(path, offset=0):
    try:
        with Path(path).open('rb') as stream:
            if offset:
                stream.seek(offset)
                stream.readline(65536)  # Skip the partial first record in a tail view.
            while True:
                line=stream.readline(65536)
                if not line:break
                if not line.endswith(b'\n'):
                    while line and not line.endswith(b'\n'):line=stream.readline(65536)
                    continue  # Oversized or unfinished records are not trusted.
                try:
                    row=json.loads(line)
                    if isinstance(row,dict) and 'boottime' in row:yield row
                except (ValueError, TypeError):pass
    except OSError: pass

def load(path, max_rows=MAX_VIEW_ROWS, max_bytes=MAX_VIEW_BYTES):
    try:offset=max(0,Path(path).stat().st_size-max_bytes)
    except OSError:return []
    return list(deque(iter_rows(path,offset),maxlen=max_rows))

def analyze(rows):
    totals={k:{'delta_uah':0, 'duration_s':0, 'rejected':0, 'estimated_ma':None} for k in METHODS}
    sleep=0.; pending=None; warnings=[]; valid_sleep_pairs=0
    for row in rows:
        if row.get('event')=='prepare-sleep':
            if pending: warnings.append('unpaired prepare')
            pending=row
        elif row.get('event')=='resume-signal':
            if not pending: warnings.append('unpaired resume');continue
            dt=row['boottime']-pending['boottime']; awake=row['monotonic']-pending['monotonic']
            if row.get('boot_id')==pending.get('boot_id') and 0<=awake<=dt+.05 and dt>0:
                sleep+=max(0,dt-awake)
                valid_sleep_pairs+=1
            else: warnings.append('invalid sleep clocks or changed boot')
            pending=None
    if pending: warnings.append('sleep interval not yet complete')
    for a,b in zip(rows,rows[1:]):
        dt=b['boottime']-a['boottime']
        if dt<10: continue
        left=a.get('supplies',{}).get('bms',{}); right=b.get('supplies',{}).get('bms',{})
        def status(row,bms):
            return bms.get('status') if bms.get('status') is not None else row.get('supplies',{}).get('battery',{}).get('status')
        common=(a.get('usb')==b.get('usb')=='0' and status(a,left)==status(b,right)=='Discharging'
                and a.get('boot_id') and a.get('boot_id')==b.get('boot_id'))
        for key in METHODS:
            x,y=number(left.get(key)),number(right.get(key))
            scale='charge_full_design' if key=='charge_now_raw' else 'charge_full'
            sx,sy=number(left.get(scale)),number(right.get(scale))
            valid=common and x is not None and y is not None and x>=y and sx is not None and sx>0 and sx==sy
            if valid:
                totals[key]['delta_uah']+=x-y;totals[key]['duration_s']+=dt
            else: totals[key]['rejected']+=1
    for item in totals.values():
        if item['duration_s']:item['estimated_ma']=item['delta_uah']*3.6/item['duration_s']
    duration=(rows[-1]['boottime']-rows[0]['boottime']) if len(rows)>1 and rows[0].get('boot_id')==rows[-1].get('boot_id') else 0
    return {'duration_s':max(0,duration),'sleep_s':sleep,'valid_sleep_pairs':valid_sleep_pairs,'methods':totals,'warnings':warnings}

def export_csv(rows,path):
    columns=['time_utc','event','usb','capacity_percent','status','current_ua','voltage_uv','temperature_decic',
             *METHODS,'charge_full_uah','charge_full_design_uah','wake_reason','boottime_s','monotonic_s']
    with Path(path).open('x',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader()
        for row in rows:
            battery=row.get('supplies',{}).get('battery',{});bms=row.get('supplies',{}).get('bms',{})
            writer.writerow({'time_utc':datetime.datetime.fromtimestamp(row['epoch'],datetime.timezone.utc).isoformat(),
                'event':row.get('event'),'usb':row.get('usb'),'capacity_percent':battery.get('capacity'),
                'status':battery.get('status'),'current_ua':battery.get('current_now'),'voltage_uv':battery.get('voltage_now'),
                'temperature_decic':battery.get('temp'),**{key:bms.get(key) for key in METHODS},
                'charge_full_uah':bms.get('charge_full'),'charge_full_design_uah':bms.get('charge_full_design'),
                'wake_reason':row.get('wake_reason'),'boottime_s':row['boottime'],'monotonic_s':row['monotonic']})

def graph_svg(rows,dark=False):
    points=[]
    for row in rows:
        y=number(row.get('supplies',{}).get('battery',{}).get('capacity'))
        x=number(row.get('boottime'))
        if y is not None and x is not None and 0<=y<=100:points.append((x,y))
    bg,fg=('#20232a','#eeeeee') if dark else ('#ffffff','#333333')
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="210" viewBox="0 0 600 210"><rect width="600" height="210" rx="12" fill="{bg}"/>']
    for y in (0,50,100):
        cy=175-y*1.5
        parts.append(f'<path d="M42 {cy} H580" stroke="{fg}" opacity=".16"/><text x="6" y="{cy+4}" font-size="12" fill="{fg}">{y}%</text>')
    if points:
        lo=min(x for x,y in points);hi=max(x for x,y in points);span=max(1,hi-lo)
        for x,y in points[-3000:]:parts.append(f'<circle cx="{42+(x-lo)/span*538:.2f}" cy="{175-y*1.5:.2f}" r="2.5" fill="#3584e4"/>')
        parts.append(f'<text x="42" y="199" font-size="12" fill="{fg}">0 h</text><text x="535" y="199" font-size="12" fill="{fg}">{span/3600:.1f} h</text>')
    parts.append('</svg>');return ''.join(parts).encode()
