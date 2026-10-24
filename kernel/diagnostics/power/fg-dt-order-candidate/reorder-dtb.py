"""Offline diagnostic only: reorder a passive FG profile container, never boot/flash.
Default reports the result. --output writes one new DTB from the pinned input.
"""
from pathlib import Path
import argparse,hashlib,json,struct,zlib
PIN='6452f7bc7f12d25c1717ebfba9a5566a1001adc60b8f0652bef6309a15c0b56b'
PROFILE='/soc/qcom,battery-data'
SPMI='/soc/qcom,spmi@c440000'
GAUGE=SPMI+'/qcom,pm8150b@2/qpnp,fg'

def parse(raw):
 assert len(raw)>=40
 h=struct.unpack_from('>10I',raw)
 assert h[0]==0xd00dfeed and h[1]==len(raw) and h[5]>=17
 start,limit=h[2],h[2]+h[9];assert 40<=start<limit<=len(raw)
 assert h[3]+h[8]<=len(raw)
 strings=raw[h[3]:h[3]+h[8]];pos=start;stack=[];order=[];spans={};props={}
 while pos<limit:
  at=pos;t=struct.unpack_from('>I',raw,pos)[0];pos+=4
  if t==1:
   end=raw.index(b'\0',pos,limit);name=raw[pos:end].decode();pos=(end+4)&~3
   path=('/'+'/'.join([x[0] for x in stack[1:]]+[name])) if stack else '/'
   assert path not in props
   stack.append((name,path,at));order.append(path);props[path]={}
  elif t==2:
   assert stack;name,path,a=stack.pop();spans[path]=(a,pos)
  elif t==3:
   assert stack and pos+8<=limit
   size,offset=struct.unpack_from('>II',raw,pos);pos+=8;assert pos+size<=limit and offset<len(strings)
   end=strings.index(b'\0',offset);name=strings[offset:end].decode();assert name not in props[stack[-1][1]]
   props[stack[-1][1]][name]=raw[pos:pos+size];pos=(pos+size+3)&~3
  elif t==4:pass
  elif t==9:
   assert not stack;return order,spans,props
  else:raise ValueError('Invalid FDT token')
 raise ValueError('Missing FDT END')

def legacy(order):
 return next(p for p in order[order.index(GAUGE)+1:] if p.rsplit('/',1)[-1]=='qcom,battery-data')

def transform(raw):
 assert hashlib.sha256(raw).hexdigest()==PIN,'Unpinned input refused'
 before,spans,props=parse(raw)
 assert legacy(before)=='/vendor/qcom,battery-data'
 assert 'compatible' not in props[PROFILE]
 for p in before:
  if p.startswith(PROFILE+'/'):assert 'compatible' not in props[p],'Profile subtree is not passive'
 ref=props[GAUGE]['qcom,battery-data'];assert props[PROFILE]['phandle']==ref
 assert sum(props[p].get('phandle')==ref for p in before)==1
 a,b=spans[PROFILE];c,d=spans[SPMI];assert a<b<c<d
 result=raw[:a]+raw[b:d]+raw[a:b]+raw[d:]
 after,_,newprops=parse(result)
 assert len(result)==len(raw) and result[:40]==raw[:40]
 assert props==newprops,'Property change refused'
 assert set(before)==set(after) and len(before)==len(after)
 assert [p for p in before if p!=PROFILE and not p.startswith(PROFILE+'/')]==[p for p in after if p!=PROFILE and not p.startswith(PROFILE+'/')]
 assert legacy(after)==PROFILE
 assert newprops[GAUGE]['qcom,battery-data']==ref
 return result,dict(input_sha256=PIN,output_sha256=hashlib.sha256(result).hexdigest(),bytes=len(raw),node_count=len(after),properties_unchanged=True,other_node_order_unchanged=True,legacy_before=legacy(before),legacy_after=legacy(after),phandle_target_unchanged=PROFILE,hardware_tested=False,boot_image_created=False)

MENU_SHA='be9841c76cbe34d0c72606c47877f99582aee224144744349a9e78d15cfd0a94'
PARTS={
 'mobian/kernel':'87c53d33202d4607591fa0ba6d2bf091dc2dfc4673a3326436740a1f0e7bae6a',
 'mobian/initrd':'5622088331db3e8dbd0266dedb5e1606747fdf0fa74cf7c0797ad22dd3042530',
 'mobian/dtb':PIN,
 'mobian/cmdline':'f718c08f1f3d257311ead88e60bb10b66eae170130bd36678e5cf3cf6e75dadd',
 'mobian/identity':'b21e4cfb40fb16d834aed5b2fc75a98e0b154532806364a50f222b43c4582b13'}

def extract_menu(raw):
 assert len(raw)==81051648 and hashlib.sha256(raw).hexdigest()==MENU_SHA,'Qualified menu mismatch'
 assert raw[:8]==b'ANDROID!'
 page=struct.unpack_from('<I',raw,36)[0];assert page in (2048,4096)
 kernel_size=struct.unpack_from('<I',raw,8)[0];outer_size=struct.unpack_from('<I',raw,16)[0]
 begin=page+((kernel_size+page-1)//page)*page
 outer=raw[begin:begin+outer_size]
 assert len(outer)==55054349 and zlib.crc32(outer)==1758271194
 magic,version,count,size=struct.unpack_from('<8sIIQ',outer)
 assert (magic,version,count,size)==(b'LMIBNDL1',1,5,len(outer))
 payloads={}
 for i in range(count):
  name,offset,size,crc,reserved=struct.unpack_from('<32sQQII',outer,32+i*56)
  name=name.rstrip(b'\0').decode();assert name in PARTS and name not in payloads
  data=outer[offset:offset+size]
  assert offset>=4096 and len(data)==size and zlib.crc32(data)==crc and reserved==0
  assert hashlib.sha256(data).hexdigest()==PARTS[name]
  payloads[name]=data
 assert set(payloads)==set(PARTS)
 return payloads

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('input',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args()
 result,report=transform(a.input.read_bytes())
 if a.output:
  with a.output.open('xb') as f:f.write(result)
  report['written']=str(a.output)
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
