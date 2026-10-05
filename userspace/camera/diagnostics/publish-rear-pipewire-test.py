# Experimental userspace-only PipeWire transport diagnostic; not an installed camera service.
import gi,time,json,subprocess,threading,signal
from pathlib import Path
gi.require_version('Gst','1.0');from gi.repository import Gst
Gst.init(None);stop=threading.Event();signal.signal(signal.SIGTERM,lambda *a:stop.set())
f=Path('/run/lmi-camera/live.ppm');header=b'P6\n1280 720\n255\n';size=1280*720*3
p=Gst.parse_launch('appsrc name=source format=time is-live=true do-timestamp=true block=false max-buffers=2 leaky-type=downstream caps="video/x-raw,format=RGB,width=1280,height=720,framerate=10/1" ! queue max-size-buffers=2 leaky=downstream ! videoflip method=clockwise ! videoconvert ! video/x-raw,format=BGRx ! pipewiresink mode=provide sync=false use-bufferpool=false stream-properties="props,media.type=Video,media.category=Capture,media.class=Video/Source,media.role=Camera,node.name=lmi-camera-rear-pipewire-test,node.description=LMI-rear-camera-test"')
source=p.get_by_name('source');count=0;end=time.monotonic()+300;last=None
try:
 p.set_state(Gst.State.PLAYING)
 while not stop.wait(.1) and time.monotonic()<end:
  if not f.exists():continue
  if time.time()-f.stat().st_mtime>3:continue
  stamp=f.stat().st_mtime_ns
  if stamp==last:continue
  data=f.read_bytes()
  assert data.startswith(header) and len(data)==len(header)+size
  last=stamp;data=data[len(header):]
  b=Gst.Buffer.new_allocate(None,size,None);b.fill(0,data);b.duration=Gst.SECOND//10
  assert source.emit('push-buffer',b)==Gst.FlowReturn.OK
  count+=1
  if count==1:print('REAL_CAMERA_PIPEWIRE_SOURCE_READY',flush=True)
finally:p.set_state(Gst.State.NULL)
print('PIPEWIRE_SOURCE_STOPPED frames='+str(count),flush=True)
