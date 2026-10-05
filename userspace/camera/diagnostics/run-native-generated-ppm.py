import os,subprocess,time,threading
from pathlib import Path
stop=threading.Event();file=Path('/tmp/lmi-generated-ppm-test.ppm');tmp=Path('/tmp/lmi-generated-ppm-test.next')
def feed():
 pixels=bytearray(b'\x30\x80\xb0'*(1280*720));seq=0;next_time=time.monotonic()
 while not stop.is_set():
  seq+=1;pixels[:3]=bytes([seq%256,128,176])
  with tmp.open('wb') as f:f.write(b'P6\n1280 720\n255\n');f.write(pixels)
  tmp.replace(file)
  next_time+=.04;stop.wait(max(0,next_time-time.monotonic()))
 print('GENERATED_PPM_FRAMES',seq,flush=True)
thread=threading.Thread(target=feed);thread.start();time.sleep(.2)
producer=subprocess.Popen(['/tmp/native-pipewire-ppm-test',str(file)])
try:
 time.sleep(2);env=os.environ.copy();env['LD_PRELOAD']='/tmp/lmi-snapshot-tuning.so';env['LMI_SNAPSHOT_TUNING']='1'
 result=subprocess.run(['timeout','25','python3','/tmp/test-native-ppm-consumer.py'],env=env,timeout=28)
 print('CONSUMER_EXIT',result.returncode,flush=True)
finally:
 producer.terminate()
 try:producer.wait(timeout=3)
 except subprocess.TimeoutExpired:producer.kill();producer.wait(timeout=2)
 stop.set();thread.join(timeout=2)
 print('NATIVE_PPM_TEST_STOPPED',producer.returncode,flush=True)
