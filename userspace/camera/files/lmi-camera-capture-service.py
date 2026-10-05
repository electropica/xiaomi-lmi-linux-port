#!/usr/bin/python3
"""Fixed rear capture only. No caller-controlled path or camera ID."""
import json,os,re,shutil,stat,subprocess,tempfile
from pathlib import Path

assert os.getuid()==0
assert len(__import__('sys').argv)==1
assert os.uname().release=='4.19.325-cip128-st12-perf-ga5b3099017ae-dirty'
os.umask(0o077)
base=Path('/usr/local/lib/lmi-camera')
destination=Path('/run/lmi-camera')
assert destination.is_dir() and destination.stat().st_uid==0
assert not destination.stat().st_mode & 0o022
output=None
try:
    result=subprocess.run(['/usr/bin/python3',str(base/'camera-test-rear-preview.py')],capture_output=True,text=True,timeout=46)
    matches=re.findall(r'^PRIVATE_CAPTURE_DIRECTORY (/tmp/lmi-camera-capture-[a-z0-9_]+)$',result.stdout,re.M)
    if len(matches)==1:
        candidate=Path(matches[0])
        assert candidate.parent==Path('/tmp') and candidate.is_dir() and not candidate.is_symlink()
        assert candidate.stat().st_uid==0 and not candidate.stat().st_mode & 0o077
        output=candidate
    if result.returncode or output is None:
        raise RuntimeError('Bounded rear camera backend failed')
    angles=re.findall(r'^sensor_orientation_degrees=(\d+)$',(output/'capture.log').read_text(),re.M)
    assert len(angles)==1 and int(angles[0]) in (0,90,180,270)
    orientation=int(angles[0])
    image=output/'preview.ppm'
    assert image.is_file() and not image.is_symlink() and image.stat().st_uid==0
    assert image.stat().st_size==2764816
    with image.open('rb') as source:
        assert source.read(16)==b'P6\n1280 720\n255\n'
        source.seek(0)
        fd,temp=tempfile.mkstemp(prefix='.capture-',dir=destination)
        try:
            with os.fdopen(fd,'wb') as target:
                shutil.copyfileobj(source,target)
                target.flush();os.fsync(target.fileno())
                os.fchmod(target.fileno(),0o640)
                os.fchown(target.fileno(),0,destination.stat().st_gid)
            os.replace(temp,destination/'latest.ppm')
        finally:
            if os.path.exists(temp):os.unlink(temp)
    fd,temp=tempfile.mkstemp(prefix='.metadata-',dir=destination)
    try:
        with os.fdopen(fd,'w') as target:
            json.dump({'sensor_orientation':orientation,'width':1280,'height':720},target)
            target.flush();os.fsync(target.fileno())
            os.fchmod(target.fileno(),0o640)
            os.fchown(target.fileno(),0,destination.stat().st_gid)
        os.replace(temp,destination/'latest.json')
    finally:
        if os.path.exists(temp):os.unlink(temp)
    print('REAR_SENSOR_ORIENTATION='+str(orientation),flush=True)
    print('REAR_CAPTURE_SAVED',flush=True)
finally:
    if output is not None:
        # Only the new root-owned private output directory of this invocation.
        shutil.rmtree(output)
