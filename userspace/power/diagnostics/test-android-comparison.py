import runpy
from pathlib import Path
compare=runpy.run_path(str(Path(__file__).with_name('analyze-android-comparison.py')))['compare']
before='BOOT_UPTIME\n500.00 2500.00\nAC powered: false\nUSB powered: false\nWireless powered: false\nDock powered: false\nstatus: 3\nCharge counter: 2000000\nlevel: 78\ntemperature: 260\nMaximum capacity: 2820000\n'
after='BOOT_UPTIME\n800.00 2700.00\nAC powered: false\nUSB powered: false\nWireless powered: false\nDock powered: false\nstatus: 3\nCharge counter: 1995000\nlevel: 78\ntemperature: 250\nMaximum capacity: 2820000\n'
r=compare(before,after);assert r['comparable'] and r['indicative_mA']==60 and r['elapsed_s']==300
for a,b in ((before.replace('USB powered: false','USB powered: true'),after),(before.replace('status: 3','status: 2'),after),(before,after.replace('2820000','2810000')),(before,after.replace('800.00','100.00')),(before,after.replace('Charge counter: 1995000','Charge counter: unknown')),(before,after.replace('level: 78','level: 101'))):
 assert not compare(a,b)['comparable']
for key in ('AC powered','USB powered','Wireless powered','Dock powered'):
 assert not compare(before,after.replace(key+': false',key+': true'))['comparable']
assert not compare(before,after.replace('1995000','2005000'))['comparable']
assert not compare(before,after.replace('status: 3','status: 2'))['comparable']
print('Android comparison parser/guards PASS; all external-power sources and counter increases covered; no phone access')
