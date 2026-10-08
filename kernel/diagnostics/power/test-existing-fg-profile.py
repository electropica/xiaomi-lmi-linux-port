import importlib.util
from pathlib import Path
p=Path(__file__).with_name('read-existing-fg-profile.py');spec=importlib.util.spec_from_file_location('reader',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert m.decode('299 09\n',299,1)==b'\x09'
blob=bytes(range(256))+bytes(range(160));text=''.join(str(65+i//2).zfill(3)+' '+' '.join(f'{v:02X}' for v in blob[i:i+4])+'\n' for i in range(0,416,4));assert m.decode(text,65,416)==blob
bad=['','299 ZZ\n','298 09\n','299 09 00\n','299 09\n300 00\n','x'*4097]
for text in bad:
 try:m.decode(text,299,1)
 except ValueError:pass
 else:raise AssertionError(text)
try:m.decode('065 00 00 00 00\n',65,416)
except ValueError:pass
else:raise AssertionError('Incomplete accepted')
import tempfile
with tempfile.TemporaryDirectory() as d:
 m.ROOT=Path(d)
 for scenario in ('success','read-failure','changed-marker'):
  (m.ROOT/'address').write_text('0x00000000\n');(m.ROOT/'count').write_text('0\n');calls=[]
  def fake_range(address,count):
   calls.append((address,count))
   (m.ROOT/'address').write_text(hex(address)+'\n');(m.ROOT/'count').write_text(str(count)+'\n')
   if scenario=='read-failure' and count==416:raise OSError('Simulated SRAM failure')
   if count==416:return blob
   return b'\x03' if scenario!='changed-marker' or len(calls)==1 else b'\x09'
  m.read_range=fake_range
  try:result=m.read_snapshot()
  except (ValueError,OSError):assert scenario!='success'
  else:assert scenario=='success' and result==(3,blob,3)
  assert (m.ROOT/'address').read_text()=='0x00000000\n'
  assert (m.ROOT/'count').read_text()=='0\n'
print('GEN4 parser: 9 cases PASS; restoration: 3 cases PASS; no hardware access')
