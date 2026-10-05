#!/usr/bin/python3
"""Explicit opt-in on the measured diagnostic boot; never a generic image step."""
import argparse,ast,grp,os,pwd,re,shutil,subprocess
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--user',required=True)
p.add_argument('--files',required=True)
p.add_argument('--accept-diagnostic-boot',action='store_true')
args=p.parse_args()
assert os.getuid()==0 and args.accept_diagnostic_boot
assert os.uname().release=='4.19.325-cip128-st12-perf-ga5b3099017ae-dirty'
assert re.fullmatch(r'[a-z_][a-z0-9_-]{0,30}',args.user)
account=pwd.getpwnam(args.user)
assert account.pw_uid>=1000
source=Path(args.files)
base=Path('/usr/local/lib/lmi-camera')
base.mkdir(mode=0o755,parents=True,exist_ok=True)
assert not base.is_symlink() and base.stat().st_uid==0 and not base.stat().st_mode & 0o022
def install(name,target,mode=0o644,text=None):
    src=source/name
    assert src.is_file() and not src.is_symlink()
    target=Path(target)
    assert not target.is_symlink()
    target.parent.mkdir(parents=True,exist_ok=True)
    if text is None:shutil.copyfile(src,target)
    else:target.write_text(text)
    os.chown(target,0,0);os.chmod(target,mode)

for name in ['camera-module-capture','liblmi_qti_bridge.so','lmi-camera-private-context-test.so']:
    install(name,base/name,0o755)
install('inspect-system-ext-metadata.py',base/'lmi-camera-super-metadata.py')
supervisor=(source/'camera-test-capture.py').read_text()
for name in ['lmi-camera-super-metadata.py','liblmi_qti_bridge.so','camera-module-capture','lmi-camera-private-context-test.so']:
    supervisor=supervisor.replace('/tmp/'+name,str(base/name))
ast.parse(supervisor)
install('camera-test-capture.py',base/'camera-test-capture.py',text=supervisor)
wrapper=(source/'camera-test-rear-preview.py').read_text().replace('/tmp/camera-test-capture.py',str(base/'camera-test-capture.py'))
ast.parse(wrapper)
install('camera-test-rear-preview.py',base/'camera-test-rear-preview.py',text=wrapper)
install('lmi-camera-capture-service.py',base/'capture-service.py')
install('lmi-camera-preview-service.py',base/'preview-service.py')
install('lmi-camera.py','/usr/local/bin/lmi-camera',0o755)
install('lmi-camera.desktop','/usr/local/share/applications/lmi-camera.desktop')
group=grp.getgrgid(account.pw_gid).gr_name
assert re.fullmatch(r'[a-z_][a-z0-9_-]{0,30}',group)
service=(source/'lmi-camera-capture.service').read_text().replace('__CAMERA_GROUP__',group)
install('lmi-camera-capture.service','/etc/systemd/system/lmi-camera-capture.service',text=service)
preview=(source/'lmi-camera-preview.service').read_text().replace('__CAMERA_GROUP__',group)
install('lmi-camera-preview.service','/etc/systemd/system/lmi-camera-preview.service',text=preview)
state=Path('/run/lmi-camera')
state.mkdir(mode=0o750,exist_ok=True)
assert not state.is_symlink() and state.stat().st_uid==0
os.chown(state,0,account.pw_gid);os.chmod(state,0o750)
rule='''// Fixed rear snapshot/preview actions only; never arbitrary root commands.
polkit.addRule(function(action, subject) {
    if (action.id == "org.freedesktop.systemd1.manage-units" &&
        ((action.lookup("unit") == "lmi-camera-capture.service" && action.lookup("verb") == "start") ||
         (action.lookup("unit") == "lmi-camera-preview.service" &&
          (action.lookup("verb") == "start" || action.lookup("verb") == "stop"))) &&
        subject.user == "%s" && subject.local && subject.active) {
        return polkit.Result.YES;
    }
});
'''%args.user
path=Path('/etc/polkit-1/rules.d/49-lmi-camera.rules')
assert not path.is_symlink()
path.write_text(rule);os.chown(path,0,0);os.chmod(path,0o644)
subprocess.run(['systemctl','daemon-reload'],check=True,timeout=5)
subprocess.run(['systemd-analyze','verify','/etc/systemd/system/lmi-camera-capture.service','/etc/systemd/system/lmi-camera-preview.service'],check=True,timeout=10)
print('LMI_REAR_SNAPSHOT_INSTALLED_OPT_IN_NO_BOOT_ENABLE')
