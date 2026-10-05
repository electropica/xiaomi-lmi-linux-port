#!/usr/bin/python3
"""Fixed bounded rear preview publisher; no user-selected inputs."""
import json,os,re,shutil,signal,socket,stat,subprocess,tempfile,threading,time
from pathlib import Path
assert os.getuid()==0 and len(__import__('sys').argv)==1
assert os.uname().release=='4.19.325-cip128-st12-perf-ga5b3099017ae-dirty'
os.umask(0o077)
base=Path('/usr/local/lib/lmi-camera');dest=Path('/run/lmi-camera')
assert dest.is_dir() and not dest.is_symlink() and dest.stat().st_uid==0 and not dest.stat().st_mode&0o022
uid=int(os.environ['LMI_CAMERA_USER_UID']);assert uid>=1000
lease=Path('/run/user')/str(uid)/'lmi-camera'/'foreground.json'
def foreground_alive():
 try:
  fd=os.open(lease,os.O_RDONLY|os.O_NOFOLLOW)
  with os.fdopen(fd,'r') as f:
   info=os.fstat(f.fileno())
   if not stat.S_ISREG(info.st_mode) or info.st_uid!=uid or info.st_size>1024:return False
   state=json.load(f)
  age=(time.monotonic_ns()-state['updated_ns'])/1e9
  pid=state['pid']
  if state['active'] is not True or not 0<=age<4 or not isinstance(pid,int) or pid<=1:return False
  proc=Path('/proc')/str(pid)
  return (proc.stat().st_uid==uid and
          '/usr/local/bin/lmi-camera' in (proc/'cmdline').read_bytes().decode().split('\0') and
          (proc/'stat').read_text().rsplit(')',1)[1].split()[19]==state['start_ticks'])
 except (OSError,ValueError,KeyError,TypeError):return False

def notify(text):
 address=os.environ['NOTIFY_SOCKET']
 if address.startswith('@'):address='\0'+address[1:]
 with socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM) as sock:sock.sendto(text.encode(),address)

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
 assert foreground_alive(), 'No live foreground camera owner'
 notify('READY=1')
 child=subprocess.Popen(['/usr/bin/python3',str(base/'camera-test-rear-preview.py'),'--foreground'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 threading.Thread(target=watch,args=(child.stdout,),daemon=True).start()
 previous=None;last_frame=time.monotonic();last_check=0;last_notify=0
 while not stopped:
  now=time.monotonic()
  if now-last_check>=.2:
   last_check=now
   if not foreground_alive():stopped=True;break
  if now-last_frame>8:raise RuntimeError('Camera stopped returning frames')
  if now-last_notify>=1:
   notify('WATCHDOG=1');last_notify=now
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
      previous=stamp;last_frame=time.monotonic()
  if child.poll() is not None:break
  time.sleep(.02)
 if not stopped and (child.poll() is None or child.returncode or not published):
  raise RuntimeError('Bounded rear preview did not complete successfully')
 print('REAR_PREVIEW_FRAMES='+str(published),flush=True)
finally:
 if child is not None and child.poll() is None:
  child.terminate()
  try:child.wait(timeout=8)
  except subprocess.TimeoutExpired:child.kill();child.wait(timeout=2)
 publish('live.json',json.dumps({'ended':True,'sequence':published}).encode())
 if output is not None:shutil.rmtree(output)
