"""Host fixtures execute the deployed sampler's actual branches; no phone I/O."""
import ast,json,tempfile,types,contextlib,io
from pathlib import Path
source=Path(__file__).with_name('off-comparison-one-shot.py').read_text(encoding='utf-8-sig');tree=ast.parse(source)
branch=next(n for n in tree.body if isinstance(n,ast.If));code=compile(ast.Module(body=[branch],type_ignores=[]),'sampler-branches','exec')
def run(mode,scenario):
 with tempfile.TemporaryDirectory() as d:
  root=Path(d);(root/'armed').write_text('armed');clock=[0.0]
  def read(path):
   if path.endswith('/usb/online'):
    if scenario=='never-unplug':return '1'
    if scenario=='reconnect':return '1' if clock[0]>=12 else '0'
    if scenario=='usb-at-boot':return '1'
    return '0'
   if path.endswith('/battery/capacity'):return None if scenario=='missing-battery' or (scenario=='delayed-battery' and clock[0]<3) else '88'
   return None
  def sample(label):return {'label':label,'usb_online':read('/sys/class/power_supply/usb/online'),'fixture_time':clock[0]}
  def save(name,data):
   with (root/name).open('x') as f:json.dump(data,f)
  env={'sys':types.SimpleNamespace(argv=['sampler',mode]),'ROOT':root,'read':read,'sample':sample,'save':save,'time':types.SimpleNamespace(monotonic=lambda:clock[0],sleep=lambda s:clock.__setitem__(0,clock[0]+s))}
  failure=None
  try:
   with contextlib.redirect_stdout(io.StringIO()):exec(code,env)
  except (RuntimeError,SystemExit) as e:failure=str(e)
  before=root/'before-off.json';after=root/'next-boot.json'
  if scenario in ('never-unplug','reconnect','missing-battery'):
   assert failure and not before.exists() and not after.exists()
  else:
   assert failure is None
   if mode=='--before-off':assert json.loads(before.read_text())['fixture_time']==12
   else:
    rows=json.loads(after.read_text());assert len(rows)==3 and rows[-1]['fixture_time']-rows[0]['fixture_time']==15
    if scenario=='usb-at-boot':assert all(x['usb_online']=='1' for x in rows)
  if mode=='--next-boot':assert not (root/'armed').exists()
for mode,scenario in [('--before-off','success'),('--before-off','never-unplug'),('--before-off','reconnect'),('--next-boot','success'),('--next-boot','delayed-battery'),('--next-boot','missing-battery'),('--next-boot','usb-at-boot')]:run(mode,scenario)
print('Deployed sampler branches: 7 host fixture cases PASS; no hardware access')
