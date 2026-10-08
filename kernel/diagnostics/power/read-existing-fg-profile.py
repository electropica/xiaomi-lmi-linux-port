#!/usr/bin/env python3
"""On-demand GEN4 SRAM read: data is opened read-only; reader controls restored."""
import os,re,json,hashlib
from pathlib import Path
ROOT=Path('/sys/kernel/debug/fg/sram')
def decode(text,address,count):
 if len(text)>4096:raise ValueError('Oversized dump')
 values=[]
 for line in text.splitlines():
  parts=line.split()
  if not parts:continue
  if len(parts)<2 or len(parts)>5 or not re.fullmatch(r'[0-9]{3}',parts[0]):raise ValueError('Malformed line')
  if int(parts[0])!=address+len(values)//2:raise ValueError('Address progression')
  expected=min(4,count-len(values))
  if len(parts[1:])!=expected or not all(re.fullmatch(r'[0-9A-Fa-f]{2}',v) for v in parts[1:]):raise ValueError('Malformed or excess bytes')
  values.extend(int(v,16) for v in parts[1:])
 if len(values)!=count:raise ValueError('Incomplete SRAM read')
 return bytes(values)
def read_range(address,count):
 if (address,count) not in ((299,1),(65,416)):raise ValueError('Range not allowed')
 (ROOT/'address').write_text(hex(address)+'\n');(ROOT/'count').write_text(str(count)+'\n')
 fd=os.open(ROOT/'data',os.O_RDONLY)
 try:
  chunks=[];total=0
  while True:
   data=os.read(fd,4097-total)
   if not data:break
   chunks.append(data);total+=len(data)
   if total>4096:raise ValueError('Oversized dump')
  return decode(b''.join(chunks).decode('ascii'),address,count)
 finally:os.close(fd)
def read_snapshot():
 controls={n:(ROOT/n).read_text() for n in ('address','count')}
 try:
  before=read_range(299,1)[0];current=read_range(65,416);after=read_range(299,1)[0]
  if before!=after:raise ValueError('Integrity changed during read')
 finally:
  for n in ('address','count'):(ROOT/n).write_text(controls[n])
  if any((ROOT/n).read_text()!=controls[n] for n in controls):raise ValueError('Reader controls restoration failed')
 return before,current,after
def main():
 if 'Wed Oct 7 05:27:54 UTC 2026' not in Path('/proc/version').read_text():raise ValueError('Unexpected kernel')
 if Path('/sys/class/power_supply/usb/online').read_text().strip()!='1':raise ValueError('USB must be connected')
 container=Path('/sys/firmware/devicetree/base/soc/qcom,battery-data')
 candidates=[p for p in container.iterdir() if p.is_dir() and (p/'qcom,battery-type').exists() and (p/'qcom,battery-type').read_bytes().rstrip(b'\0')==b'j11sun_4700mah']
 if len(candidates)!=1:raise ValueError('Expected one lmi profile')
 expected=(candidates[0]/'qcom,fg-profile-data').read_bytes()
 if len(expected)!=416:raise ValueError('Unexpected profile length')
 if hashlib.sha256(expected).hexdigest()!='583d77b61a7723fe4f40990eafa42c6283a87c41ba39a69ad2be77ce70f16050':raise ValueError('Unexpected reference profile')
 before,current,after=read_snapshot()
 offsets=[i for i,(a,b) in enumerate(zip(expected,current)) if a!=b]
 print(json.dumps({'integrity':hex(after),'load_bit':bool(after&1),'valid_marker':(after&~1) in (8,2,6,12,18,22,28),'prefix24_match':current[:24]==expected[:24],'full416_match':current==expected,'differing_bytes':len(offsets),'differing_offsets':offsets,'expected_sha256':hashlib.sha256(expected).hexdigest(),'retained_sha256':hashlib.sha256(current).hexdigest(),'reader_controls_restored':True,'limit':'No profile or calibration write. SRAM transport can briefly wake hardware. Full-profile differences can include normal runtime tuning.'},indent=2))
if __name__=='__main__':main()
