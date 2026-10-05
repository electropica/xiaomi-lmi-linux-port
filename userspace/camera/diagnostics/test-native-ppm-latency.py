# Generated PPM input and a non-rendering video sink only. No hardware capture.
import gi,os,json,subprocess,time,threading,statistics
from pathlib import Path
gi.require_version('Gst','1.0');from gi.repository import Gst
Gst.init(None);stop=threading.Event();stamps={};samples=[];keys=set();seen=[]
file=Path('/tmp/lmi-generated-latency.ppm');tmp=Path('/tmp/lmi-generated-latency.next')
def feed():
 pixels=bytearray(b'\x30\x80\xb0'*(1280*720));seq=0;deadline=time.monotonic()
 while not stop.is_set():
  seq+=1;key=seq%256;pixels[:3]=bytes([key,128,176])
  with tmp.open('wb') as f:f.write(b'P6\n1280 720\n255\n');f.write(pixels)
  stamps[key]=time.monotonic();tmp.replace(file)
  deadline+=.04;stop.wait(max(0,deadline-time.monotonic()))
thread=threading.Thread(target=feed);thread.start();time.sleep(.2)
producer=subprocess.Popen(['/tmp/native-pipewire-ppm-test',str(file)]);pipeline=None
try:
 time.sleep(1)
 nodes=json.loads(subprocess.check_output(['pw-dump'],timeout=4));node=next(x for x in nodes if x.get('info',{}).get('props',{}).get('node.name')=='lmi-camera-rear-pipewire-test')
 serial=node['info']['props']['object.serial']
 print('NODE_LOCATION',node['info']['props'].get('api.libcamera.location'))
 monitor=Gst.DeviceProviderFactory.get_by_name('pipewiredeviceprovider');monitor.start()
 try:
  for device in monitor.get_devices():
   props=device.get_properties()
   if props and props.has_field('api.libcamera.location'):print('GST_DEVICE_LOCATION',props.get_value('api.libcamera.location'))
 finally:monitor.stop()
 pipeline=Gst.parse_launch(f'pipewiresrc target-object={serial} use-bufferpool=false do-timestamp=true ! video/x-raw,format=BGRx,width=720,height=1280,framerate=25/1 ! fakesink name=sink sync=false signal-handoffs=true')
 def frame(sink,buf,pad):
  ok,info=buf.map(Gst.MapFlags.READ)
  if not ok:return
  try:
   key=info.data[719*4+2];now=time.monotonic();seen.append(now)
   if key in stamps:
    samples.append((now-stamps[key])*1000);keys.add(key)
  finally:buf.unmap(info)
 pipeline.get_by_name('sink').connect('handoff',frame)
 pipeline.set_state(Gst.State.PLAYING)
 m=pipeline.get_bus().timed_pop_filtered(7*Gst.SECOND,Gst.MessageType.ERROR)
 if m:raise RuntimeError(str(m.parse_error()))
 assert len(samples)>20
 ordered=sorted(samples)
 print('SAMPLES',len(samples),'UNIQUE_KEYS',len(keys),'SINK_FPS',(len(seen)-1)/(seen[-1]-seen[0]))
 print('FILE_TO_SINK_MS mean=%.2f p95=%.2f max=%.2f'%(statistics.mean(samples),ordered[int(.95*(len(ordered)-1))],max(samples)))
finally:
 if pipeline:pipeline.set_state(Gst.State.NULL)
 producer.terminate()
 try:producer.wait(timeout=3)
 except subprocess.TimeoutExpired:producer.kill();producer.wait(timeout=2)
 stop.set();thread.join(timeout=2)
 print('GENERATED_LATENCY_TEST_STOPPED',flush=True)
