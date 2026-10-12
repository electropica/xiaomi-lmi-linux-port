"""Root installer with owned-file checks; recording is never enabled or started."""
import argparse,hashlib,json,os,pwd,subprocess
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('username')
parser.add_argument('--remove',action='store_true')
args=parser.parse_args()
assert os.geteuid()==0,'Run the installer as root'
account=pwd.getpwnam(args.username)
assert account.pw_uid>0,'Select the desktop user, not root'
source=Path(__file__).resolve().parent
targets={name:Path('/usr/local/lib/lmi-battery')/name for name in ('app.py','model.py','recorder.py')}
targets.update({'lmi-battery-recorder.service':Path('/etc/systemd/user/lmi-battery-recorder.service'),
               'local.lmi.Battery.desktop':Path('/usr/local/share/applications/local.lmi.Battery.desktop')})
manifest=Path('/var/lib/lmi-battery/install-manifest.json')
previous=json.loads(manifest.read_text()) if manifest.exists() else {}
for name,path in targets.items():
    if path.exists():
        assert not path.is_symlink()
        assert previous.get(str(path))==hashlib.sha256(path.read_bytes()).hexdigest(),f'Unowned or edited file: {path}'
base=['runuser','-u',args.username,'--','env',f'XDG_RUNTIME_DIR=/run/user/{account.pw_uid}',f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{account.pw_uid}/bus']
state=subprocess.run(base+['systemctl','--user','is-active','lmi-battery-recorder.service'],text=True,capture_output=True,timeout=8)
assert state.stdout.strip()!='active','Stop recording before updating or removing the app'
if args.remove:
    for path in targets.values():
        if path.exists():path.unlink()
    if manifest.exists():manifest.unlink()
else:
    updated={}
    for name,path in targets.items():
        raw=(source/name).read_bytes()
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(raw);path.chmod(0o644)
        updated[str(path)]=hashlib.sha256(raw).hexdigest()
    manifest.parent.mkdir(parents=True,exist_ok=True)
    manifest.write_text(json.dumps(updated,indent=2));manifest.chmod(0o644)
subprocess.run(base+['systemctl','--user','daemon-reload'],check=True,timeout=10)
subprocess.run(['update-desktop-database','/usr/local/share/applications'],check=True,timeout=10)
print('Owned application removed; private data retained' if args.remove else 'Installed; recording remains stopped and is not enabled')
