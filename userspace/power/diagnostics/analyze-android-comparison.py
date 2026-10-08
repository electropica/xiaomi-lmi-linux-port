import re,json
def parse(text):
 fields={}
 for line in text.splitlines():
  m=re.match(r'\s*([^:]+):\s*(.*?)\s*$',line)
  if m:fields[m.group(1)]=m.group(2)
 return fields
def compare(before,after):
 a=parse(before);b=parse(after);issues=[]
 for key in ('AC powered','USB powered','Wireless powered','Dock powered'):
  if a.get(key)!='false':issues.append('Departure external-power state not offline: '+key)
  if b.get(key)!='false':issues.append('Return external-power state not offline: '+key)
 if a.get('status')!='3':issues.append('Departure not confirmed discharging')
 if b.get('status')!='3':issues.append('Return not confirmed discharging')
 for key in ('Charge counter','level','temperature','Maximum capacity'):
  for label,fields in (('before',a),('after',b)):
   try:value=int(fields[key])
   except (KeyError,ValueError):issues.append('Missing numeric '+label+' '+key)
   else:
    if key=='level' and not 0<=value<=100:issues.append('Invalid level '+label)
    if key=='Maximum capacity' and value<=0:issues.append('Invalid learned full '+label)
 if a.get('Maximum capacity')!=b.get('Maximum capacity'):issues.append('Learned capacity changed')
 def uptime(text):
  m=re.search(r'BOOT_UPTIME\s*\n\s*([0-9.]+)',text)
  return float(m.group(1)) if m else None
 start=uptime(before);end=uptime(after)
 if start is None or end is None or end<=start:issues.append('Elapsed boot time invalid or restarted')
 if not issues and int(b['Charge counter'])>int(a['Charge counter']):issues.append('Counter increased; recharge or gauge drift prevents a discharge-current estimate')
 if issues:return {'comparable':False,'issues':issues,'before_level':a.get('level'),'after_level':b.get('level')}
 seconds=end-start;drop=int(a['Charge counter'])-int(b['Charge counter'])
 return {'comparable':True,'elapsed_s':seconds,'counter_drop_uAh':drop,'indicative_mA':drop*3.6/seconds,'before_level':int(a['level']),'after_level':int(b['level']),'before_temp_C':int(a['temperature'])/10,'after_temp_C':int(b['temperature'])/10,'learned_full_uAh':int(a['Maximum capacity']),'return_usb':b.get('USB powered'),'limit':'Return may already be charging. Counter is gauge-derived; short duration and temperature/radio differences limit comparison.'}
if __name__=='__main__':
 import sys
 from pathlib import Path
 print(json.dumps(compare(Path(sys.argv[1]).read_text(),Path(sys.argv[2]).read_text()),indent=2))
