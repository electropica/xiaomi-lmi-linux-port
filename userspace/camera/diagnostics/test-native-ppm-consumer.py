# Synthetic PipeWire video plus generated audio only.
import gi,json,subprocess,time
from pathlib import Path
gi.require_version('Gst','1.0');gi.require_version('GstPbutils','1.0')
from gi.repository import Gst,GstPbutils
Gst.init(None)
nodes=json.loads(subprocess.check_output(['pw-dump'],timeout=4));node=next(x for x in nodes if x.get('info',{}).get('props',{}).get('node.name')=='lmi-camera-rear-pipewire-test')
src=Gst.ElementFactory.make('pipewiresrc');src.set_property('use-bufferpool',False);src.set_property('always-copy',True);src.set_property('do-timestamp',True);src.set_property('target-object',str(node['info']['props']['object.serial']));src.set_property('stream-properties',Gst.Structure.from_string('props,media.type=Video,media.category=Capture,media.role=Camera')[0])
w=Gst.ElementFactory.make('wrappercamerabinsrc');w.set_property('video-source',src)
c=Gst.ElementFactory.make('camerabin');c.use_clock(Gst.SystemClock.obtain());c.set_property('camera-source',w);vs=Gst.ElementFactory.make('fakesink');vs.set_property('async',False);vs.set_property('sync',False);vf_frames=[0];vs.set_property('signal-handoffs',True);vs.connect('handoff',lambda *args:vf_frames.__setitem__(0,vf_frames[0]+1));c.set_property('viewfinder-sink',vs);audio=Gst.ElementFactory.make('audiotestsrc');audio.set_property('is-live',True);audio.set_property('volume',0.05);c.set_property('audio-source',audio);c.set_property('audio-capture-caps',Gst.Caps.from_string('audio/x-raw,rate=48000,channels=1'))
profile=GstPbutils.EncodingContainerProfile.new('test','test',Gst.Caps.from_string('video/webm'),None)
profile.add_profile(GstPbutils.EncodingVideoProfile.new(Gst.Caps.from_string('video/x-vp8'),None,Gst.Caps.from_string('video/x-raw,framerate=25/1'),0))
profile.add_profile(GstPbutils.EncodingAudioProfile.new(Gst.Caps.from_string('audio/x-vorbis'),None,Gst.Caps.from_string('audio/x-raw,rate=48000,channels=1'),0))
c.set_property('video-profile',profile);c.set_property('video-capture-caps',Gst.Caps.from_string('video/x-raw,width=720,height=1280,framerate=25/1'));c.set_property('viewfinder-caps',Gst.Caps.from_string('video/x-raw,width=720,height=1280,framerate=25/1'));c.set_property('mode',2);c.set_property('location','/tmp/lmi-native-generated-ppm.webm');bus=c.get_bus();errors=[]
def poll(seconds):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  m=bus.timed_pop_filtered(Gst.SECOND//10,Gst.MessageType.ERROR)
  if m:
   errors.append(str(m.parse_error()));raise RuntimeError(errors[-1])
try:
 print('START_PIPELINE',flush=True);c.set_state(Gst.State.PLAYING);print('PIPELINE_PLAYING_REQUESTED',flush=True);poll(2)
 deadline=time.monotonic()+8
 while vf_frames[0]<5 and time.monotonic()<deadline:poll(.2)
 print('VIEWFINDER_FRAMES',vf_frames[0],flush=True)
 assert vf_frames[0]>=5,'no frames before recording'
 print('START_RECORD',flush=True);c.emit('start-capture');print('RECORD_REQUESTED',flush=True);poll(6);print('STOP_RECORD',flush=True);c.emit('stop-capture');poll(3);print('RECORD_STOPPED',flush=True)
finally:
 print('PIPELINE_TEARDOWN',flush=True);c.set_state(Gst.State.NULL);print('PIPELINE_STOPPED',flush=True)
f=Path('/tmp/lmi-native-generated-ppm.webm');assert f.stat().st_size>0
info=GstPbutils.Discoverer.new(5*Gst.SECOND).discover_uri(f.as_uri())
print('AUTOMATED_CAMERABIN_VIDEO',f.stat().st_size,info.get_duration()/Gst.SECOND,len(info.get_audio_streams()))
