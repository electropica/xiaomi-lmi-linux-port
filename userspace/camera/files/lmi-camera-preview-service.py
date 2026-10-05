#!/usr/bin/python3
"""Fixed bounded rear preview publisher; no user-selected inputs."""
import json,os,re,shutil,signal,subprocess,tempfile,threading,time
from pathlib import Path
assert os.getuid()==0 and len(__import__('sys').argv)==1
assert os.uname().release=='4.19.325-cip128-st12-perf-ga5b3099017ae-dirty'
os.umask(0o077)
base=Path('/usr/local/lib/lmi-camera');dest=Path('/run/lmi-camera')
assert dest.is_dir() and not dest.is_symlink() and dest.stat().st_uid==0 and not dest.stat().st_mode&0o022
child=None;output=None;candidate=[];stopped=False;published=0
for name in ['live.ppm','live.json']:
 p=dest/name
 assert not p.is_symlink()
 if p.exists():p.unlink()
def stop(signum,frame):
 global stopped
 stopped=True
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
def watch(pipe):
 for line in pipe:
  match=re.fullmatch(r'PRIVATE_CAPTURE_DIRECTORY (/tmp/lmi-camera-capture-[a-z0-9_]+)\n',line)
  if match:candidate.append(Path(match[1]))
def publish(name,data):
 fd,tmp=tempfile.mkstemp(prefix='.live-',dir=dest)
 try:
  with os.fdopen(fd,'wb') as f:
   f.write(data);f.flush();os.fchmod(f.fileno(),0o640);os.fchown(f.fileno(),0,dest.stat().st_gid)
  os.replace(tmp,dest/name)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
try:
 child=subprocess.Popen(['/usr/bin/python3',str(base/'camera-test-rear-preview.py'),'--live'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 threading.Thread(target=watch,args=(child.stdout,),daemon=True).start()
 deadline=time.monotonic()+43;previous=None
 while not stopped and time.monotonic()<deadline:
  if candidate and output is None:
   assert len(candidate)==1
   output=candidate[0]
   assert output.parent==Path('/tmp') and output.is_dir() and not output.is_symlink()
   assert output.stat().st_uid==0 and not output.stat().st_mode&0o077
  if output is not None:
   image=output/'preview.ppm';orientation=output/'sensor-orientation'
   if image.exists() and orientation.exists():
    assert not image.is_symlink() and image.stat().st_uid==0
    with image.open('rb') as f:
     stamp=(os.fstat(f.fileno()).st_ino,os.fstat(f.fileno()).st_mtime_ns)
     if stamp!=previous:
      data=f.read(2764817)
      assert len(data)==2764816 and data[:16]==b'P6\n1280 720\n255\n'
      angle=int(orientation.read_text());assert angle in (0,90,180,270)
      publish('live.ppm',data);published+=1
      publish('live.json',json.dumps({'sensor_orientation':angle,'sequence':published}).encode())
      previous=stamp
  if child.poll() is not None:break
  time.sleep(.05)
 if not stopped and (child.poll() is None or child.returncode or not published):
  raise RuntimeError('Bounded rear preview did not complete successfully')
 print('REAR_PREVIEW_FRAMES='+str(published),flush=True)
finally:
 if child is not None and child.poll() is None:
  child.terminate()
  try:child.wait(timeout=3)
  except subprocess.TimeoutExpired:child.kill();child.wait(timeout=2)
 publish('live.json',json.dumps({'ended':True,'sequence':published}).encode())
 if output is not None:shutil.rmtree(output)
