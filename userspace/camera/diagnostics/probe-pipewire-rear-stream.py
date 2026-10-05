# Experimental userspace-only PipeWire transport diagnostic; not an installed camera service.
import gi,time,json,subprocess,threading,hashlib
from pathlib import Path
gi.require_version('Gst','1.0');from gi.repository import Gst
Gst.init(None)
f=Path('/run/lmi-camera/live.ppm')
for _ in range(40):
 if f.exists() and time.time()-f.stat().st_mtime<2:break
 time.sleep(.2)
assert f.exists() and time.time()-f.stat().st_mtime<2,'rear preview is not live'
header=b'P6\n1280 720\n255\n';size=1280*720*3
p=Gst.parse_launch('appsrc name=source format=time is-live=true do-timestamp=true block=false max-buffers=2 leaky-type=downstream caps="video/x-raw,format=RGB,width=1280,height=720,framerate=10/1" ! queue max-size-buffers=2 leaky=downstream ! pipewiresink mode=provide sync=false use-bufferpool=false stream-properties="props,media.type=Video,media.category=Capture,media.class=Video/Source,media.role=Camera,node.name=lmi-camera-bridge-test,node.description=LMI-rear-camera-test"')
c=None;stop=threading.Event();sent=set();published=[0];errors=[];thread=None
source=p.get_by_name('source')
def feed():
 last=None
 try:
  while not stop.wait(.1):
   stamp=f.stat().st_mtime_ns
   if stamp==last:continue
   data=f.read_bytes()
   if not data.startswith(header) or len(data)!=len(header)+size:raise ValueError('bad preview frame')
   last=stamp;data=data[len(header):]
   sent.add(hashlib.sha256(data).hexdigest())
   buffer=Gst.Buffer.new_allocate(None,size,None);buffer.fill(0,data);buffer.duration=Gst.SECOND//10
   if source.emit('push-buffer',buffer)!=Gst.FlowReturn.OK:raise RuntimeError('publisher stopped')
   published[0]+=1
 except Exception as e:errors.append(str(e))
try:
 p.set_state(Gst.State.PLAYING);thread=threading.Thread(target=feed,daemon=True);thread.start()
 node=None
 for _ in range(20):
  data=json.loads(subprocess.check_output(['pw-dump'],timeout=3))
  nodes=[x for x in data if x.get('info',{}).get('props',{}).get('node.name')=='lmi-camera-bridge-test']
  if nodes:node=nodes[0];break
  time.sleep(.2)
 assert node,'no camera node'
 c=Gst.parse_launch(f'pipewiresrc target-object={node["info"]["props"]["object.serial"]} stream-properties="props,media.type=Video,media.category=Capture,media.role=Camera" ! video/x-raw,format=RGB,width=1280,height=720,framerate=10/1 ! appsink name=frames sync=false max-buffers=2 drop=true')
 c.set_state(Gst.State.PLAYING);sink=c.get_by_name('frames');count=0;received=set();end=time.monotonic()+8
 while count<10 and time.monotonic()<end:
  sample=sink.emit('try-pull-sample',Gst.SECOND)
  if sample:
   b=sample.get_buffer();assert b.get_size()==size
   digest=hashlib.sha256(b.extract_dup(0,size)).hexdigest()
   assert digest in sent,'received frame differs from input'
   received.add(digest);count+=1
 print('PUBLISHED',published[0],'RECEIVED',count,'DISTINCT',len(received),'FRAME_SIZE',size,flush=True)
 assert count==10 and len(received)>1 and not errors,(count,len(received),errors)
finally:
 stop.set()
 if thread:thread.join(timeout=2)
 if c:c.set_state(Gst.State.NULL)
 p.set_state(Gst.State.NULL)
print('PIPEWIRE_REAL_REAR_FRAMES_PASSED')
