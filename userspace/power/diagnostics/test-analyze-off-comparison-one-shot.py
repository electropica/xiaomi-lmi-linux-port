import importlib.util,copy
from pathlib import Path
p=Path(__file__).with_name('analyze-off-comparison-one-shot.py');s=importlib.util.spec_from_file_location('analysis',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
a={'usb_online':'0','boot_id':'old','kernel':'same','battery':{'status':'Discharging','charge_full':'2822000','capacity':'90','charge_counter':'2400000','voltage_now':'4000000','temp':'220'},'bms':{'battery_type':'j11sun_4700mah'}}
b=copy.deepcopy(a);b.update(boot_id='new',label='first',boottime=8);b['battery'].update(capacity='89',charge_counter='2399000')
r=m.compare(a,[b]);assert r['comparable'] and r['charge_counter_drop_uAh']==1000
for field,value in [('usb_online','1'),('boot_id','old'),('kernel','different')]:
 bad=copy.deepcopy(b);bad[field]=value;assert not m.compare(a,[bad])['comparable']
for field,value in [('charge_full','3000000'),('status','Charging'),('charge_counter',None)]:
 bad=copy.deepcopy(b);bad['battery'][field]=value;assert not m.compare(a,[bad])['comparable']
bad=copy.deepcopy(b);bad['bms']['battery_type']='Unknown Battery';assert not m.compare(a,[bad])['comparable']
bad=copy.deepcopy(b);bad['usb_online']='1';r=m.compare(a,[bad,b]);assert r['comparable'] and r['selected']=='first'
bad=copy.deepcopy(a);bad['battery']['charge_counter']=None;assert not m.compare(bad,[b])['comparable']
bad=copy.deepcopy(b);bad['battery']['capacity']='101';assert not m.compare(a,[bad])['comparable']
print('Off comparison interpretation: 11 cases PASS; no hardware access')
