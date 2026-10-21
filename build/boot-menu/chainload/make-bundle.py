#!/usr/bin/env python3
"""Package exact pinned components into RAM assets; never access a phone."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,struct,zlib
here=Path(__file__).resolve().parent;parent=here.parent
s=importlib.util.spec_from_file_location('payloads',parent/'extract-payloads.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
DTBO_SHA='45f0989700c68afcd817a6a4569ba67225cf128e3eedd35a658bad384632eec4'
def bundle(inputs):
 lock=json.loads((parent/'sources.lock.json').read_text());entries=[]
 for os,file in [('mobian','mobian.img'),('android','android.img')]:
  raw=(inputs/file).read_bytes()
  if hashlib.sha256(raw).hexdigest()!=lock['os_images'][os]:raise ValueError('Wrong '+os+' boot image')
  parts=p.extract(raw)
  if 'recovery-dtbo' in parts:raise ValueError('Unexpected recovery overlay')
  for name in ('kernel','initrd','dtb','cmdline.txt'):
   data=parts[name]
   if name=='cmdline.txt':data=data[:-1]+b'\0';name='cmdline'
   entries.append((os+'/'+name,data))
 raw=(inputs/'android-dtbo.img').read_bytes()
 if len(raw)!=33554432 or hashlib.sha256(raw).hexdigest()!=DTBO_SHA:raise ValueError('Wrong installed Android DTBO')
 magic,total,header,esize,count,eoffset,page,version=struct.unpack_from('>8I',raw)
 if magic!=0xd7b7ab1e or header!=32 or esize!=32 or not 0<count<=128 or eoffset<32 or eoffset+count*esize>total or total>=24*1024**2:raise ValueError('Invalid DTBO table')
 for i in range(count):
  size,off=struct.unpack_from('>II',raw,eoffset+i*esize)
  if off<eoffset+count*esize or not size or off+size>total:raise ValueError('Invalid DTBO entry')
 # The pinned reader requires total_size < supplied size. Retain all meaningful
 # bytes and pad after the table; do not alter headers, DTBs or overlay IDs.
 data=raw[:total]+b'\0'*(4096-total%4096)
 entries.append(('android/dtbo',data))
 out=bytearray(4096);manifest={}
 for i,(name,data) in enumerate(entries):
  out.extend(b'\0'*(-len(out)%4096));off=len(out);out.extend(data)
  struct.pack_into('<32sQQII',out,32+i*56,name.encode(),off,len(data),zlib.crc32(data),0)
  manifest[name]={'offset':off,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
 struct.pack_into('<8sIIQ',out,0,b'LMIBNDL1',1,len(entries),len(out))
 if len(out)>=120*1024**2:raise ValueError('Asset volume exceeds reserved budget')
 return bytes(out),manifest
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--inputs',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 data,manifest=bundle(a.inputs)
 a.output.write_bytes(data)
 a.output.with_suffix('.json').write_text(json.dumps({'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'components':manifest},indent=2))
 print('RAM_ASSETS_BYTES',len(data))
if __name__=='__main__':main()
