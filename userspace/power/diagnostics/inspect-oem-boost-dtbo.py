"""Bounded read-only DTBO regulator inspection; no hardware-control writes."""
import argparse,struct,hashlib
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input',type=Path,required=True)
args=parser.parse_args()
p=args.input
with p.open('rb',buffering=0) as f:
 h=f.read(32);magic,total,hs,es,count,offset,page,version=struct.unpack('>8I',h)
 assert magic==0xd7b7ab1e and hs>=32 and es>=32 and 0<count<=64 and total<=32000000
 assert offset>=hs and offset+es*count<=total
 print('OEM_DTBO_HEADER','entries',count,'bytes',total,'version',version)
 f.seek(offset);table=f.read(es*count);assert len(table)==es*count
 for i in range(count):
  size,at,ident,rev,*custom=struct.unpack('>8I',table[i*es:i*es+32]);assert 40<=size<=8000000 and at+size<=total
  f.seek(at);data=f.read(size);assert len(data)==size
  vals=struct.unpack('>10I',data[:40]);assert vals[0]==0xd00dfeed and vals[1]<=len(data)
  _,n,so,ss,_,_,_,_,sn,stn=vals;assert so+stn<=n and ss+sn<=n;strings=data[ss:ss+sn];tree=data[so:so+stn];pos=0;stack=[];nodes={}
  while pos+4<=len(tree):
   token=struct.unpack_from('>I',tree,pos)[0];pos+=4
   if token==1:
    end=tree.index(b'\0',pos);name=tree[pos:end].decode(errors='replace');pos=(end+4)&~3;stack.append(name);nodes['/'.join(stack)]={}
   elif token==2:stack.pop()
   elif token==3:
    ln,no=struct.unpack_from('>II',tree,pos);pos+=8;assert no<len(strings) and pos+ln<=len(tree)
    end=strings.index(b'\0',no);name=strings[no:end].decode();nodes['/'.join(stack)][name]=tree[pos:pos+ln];pos=(pos+ln+3)&~3
   elif token==4:continue
   elif token==9:break
   else:raise ValueError('bad token')

  targets={}
  for path,props in nodes.items():
   if path.startswith('/__'):continue
   reg=props.get('regulator-name',b'').rstrip(b'\0').decode(errors='replace')
   if reg in ('vdd_boost_vreg','vdd_hap_boost'):
    ph=props.get('phandle',b'');gpio=props.get('gpio',b'')
    targets[reg]=(path,int.from_bytes(ph,'big'),list(struct.unpack('>'+str(len(gpio)//4)+'I',gpio)))
  summary={'entry':i,'sha256':hashlib.sha256(data).hexdigest(),'targets':{}}
  for reg,(path,ph,gpio) in targets.items():
   consumers=[]
   for np,ps in nodes.items():
    if np.startswith('/__'):continue
    for name,val in ps.items():
     if name.endswith('-supply') and len(val)==4 and int.from_bytes(val,'big')==ph:
      consumers.append({'path':np,'property':name,'status':ps.get('status',b'unspecified').rstrip(b'\0').decode(errors='replace')})
   ctrl=next((np for np,ps in nodes.items() if ps.get('phandle')==struct.pack('>I',gpio[0])),None)
   summary['targets'][reg]={'gpio_controller':ctrl,'gpio':gpio[1:],'always_on':'regulator-always-on' in nodes[path],'consumers':consumers}
  print(summary)
  if i==0:
   for np,ps in nodes.items():
    if np.startswith('/__'):continue
    if 'haptics' in np or 'aw8697' in np or 'drv8846' in np:
     show={}
     for k,v in ps.items():
      if k in ('compatible','status','pins','function','regulator-name','pinctrl-names'):show[k]=v.rstrip(b'\0').decode(errors='replace')
      elif k.endswith('-supply') or 'gpio' in k:show[k]=list(struct.unpack('>'+str(len(v)//4)+'I',v)) if len(v)%4==0 else str(v)
     if show:print('HAPTIC_OR_MOTOR_ENTRY0',np,show)
