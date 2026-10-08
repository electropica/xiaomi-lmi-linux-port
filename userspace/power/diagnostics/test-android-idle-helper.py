from pathlib import Path
import runpy,tempfile,ast
d=runpy.run_path(str(Path(__file__).with_name('android-idle-trial.py'))); paths=d['trial_paths'];flags=d['flags']
for x in ('../home','a/b','a b','a;reboot','$(reboot)','', 'x'*65):
 try:paths(x,'work');raise AssertionError('Unsafe ID accepted')
 except ValueError:pass
for x in ('0\n1\n2','0\n1','0\n1\n1\n1','0;reboot\n1\n1'):
 try:flags(x);raise AssertionError('Invalid radio state accepted')
 except ValueError:pass
assert flags('0\n1\n1\n')==['0','1','1']
assert paths('overnight-20261008','work')[0]=='/data/local/tmp/lmi-android-idle-overnight-20261008'
powered=d['powered']
offline='AC powered: false\nUSB powered: false\nWireless powered: false\nDock powered: false\n'
assert not powered(offline)
assert powered(offline.replace('AC powered: false','AC powered: true'))
try:powered('USB powered: false');raise AssertionError('Incomplete power flags accepted')
except ValueError:pass
ast.parse(Path(__file__).with_name('android-idle-trial.py').read_text())
print('Host guards PASS; no phone operation.')
