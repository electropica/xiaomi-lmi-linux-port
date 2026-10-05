import os,subprocess,time
producer=subprocess.Popen(['/tmp/native-pipewire-synthetic'])
try:
 time.sleep(2)
 env=os.environ.copy();env['LD_PRELOAD']='/tmp/lmi-snapshot-tuning.so';env['LMI_SNAPSHOT_TUNING']='1'
 result=subprocess.run(['timeout','25','python3','/tmp/test-synthetic-pipewire-consumer.py'],env=env,timeout=28)
 print('CONSUMER_EXIT',result.returncode,flush=True)
finally:
 producer.terminate()
 try:producer.wait(timeout=3)
 except subprocess.TimeoutExpired:producer.kill();producer.wait(timeout=2)
 print('NATIVE_SYNTHETIC_STOPPED',producer.returncode,flush=True)
