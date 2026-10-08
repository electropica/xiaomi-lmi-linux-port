"""Offline interpretation of private before-off and uncharged boot samples."""
import json,sys
from pathlib import Path

def compare(before,returns):
 issues=[]
 if before.get('usb_online')!='0':issues.append('Before-off USB was online or unknown')
 if before.get('battery',{}).get('status')!='Discharging':issues.append('Before-off status not confirmed discharging')
 full=before.get('battery',{}).get('charge_full');profile=before.get('bms',{}).get('battery_type');kernel=before.get('kernel')
 if not isinstance(full,str) or not full.isdecimal() or int(full)<=0:issues.append('Missing valid before-off learned capacity')
 if profile!='j11sun_4700mah':issues.append('Before-off profile not confirmed')
 if not before.get('boot_id'):issues.append('Before-off boot ID missing')
 for key in ('capacity','charge_counter','voltage_now','temp'):
  try:value=int(before.get('battery',{}).get(key))
  except (TypeError,ValueError):issues.append('Missing numeric before-off '+key);continue
  if key=='capacity' and not 0<=value<=100:issues.append('Before-off capacity out of range')
 reasons=[];eligible=[]
 for row in returns:
  why=[];battery=row.get('battery',{})
  if row.get('usb_online')!='0':why.append('USB already online or unknown')
  if battery.get('status')!='Discharging':why.append('Discharging not confirmed')
  if row.get('bms',{}).get('battery_type')!=profile:why.append('Profile changed or unavailable')
  if battery.get('charge_full')!=full:why.append('Learned capacity changed or unavailable')
  if row.get('kernel')!=kernel:why.append('Kernel banner changed')
  if not row.get('boot_id') or row.get('boot_id')==before.get('boot_id'):why.append('New boot not confirmed')
  for key in ('capacity','charge_counter','voltage_now','temp'):
   v=battery.get(key)
   try:int(v)
   except (TypeError,ValueError):why.append('Missing numeric '+key)
  try:
   if not 0<=int(battery.get('capacity'))<=100:why.append('Capacity out of range')
  except (TypeError,ValueError):pass
  reasons.append({'label':row.get('label'),'excluded':why})
  if not why:eligible.append(row)
 if issues or not eligible:return {'comparable':False,'issues':issues,'samples':reasons,'limit':'No off-state current can be inferred from confounded or mismatched samples.'}
 after=eligible[0];a=before['battery'];b=after['battery']
 return {'comparable':True,'selected':after['label'],'charge_counter_drop_uAh':int(a['charge_counter'])-int(b['charge_counter']),'reported_capacity_drop_pp':int(a['capacity'])-int(b['capacity']),'before_temperature_C':int(a['temp'])/10,'return_temperature_C':int(b['temp'])/10,'before_voltage_uV':int(a['voltage_now']),'return_voltage_uV':int(b['voltage_now']),'return_boot_elapsed_s':after['boottime'],'samples':reasons,'limit':'Includes shutdown and startup consumption, gauge settling and temperature change. Duration needs trusted host/operator timing. This is not independent physical current or battery-health proof.'}
if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('Use private before-off.json and next-boot.json paths')
 print(json.dumps(compare(json.loads(Path(sys.argv[1]).read_text()),json.loads(Path(sys.argv[2]).read_text())),indent=2))
