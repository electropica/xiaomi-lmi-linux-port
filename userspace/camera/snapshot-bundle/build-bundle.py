#!/usr/bin/env python3
"""Operator-run camera bundle compilation; no device access or image flashing."""
import argparse,ast,hashlib,json,os,shutil,subprocess,tempfile
from pathlib import Path

def replace(text,old,new):
    assert old in text,old
    return text.replace(old,new)

def prepare(repo,out):
    if out.exists():
        assert out.is_dir() and not out.is_symlink(), 'Regular bundle directory required'
        # Resume only when every prepared source/runtime asset still matches.
        # Generated binaries may be rebuilt; no prior input is deleted.
        with tempfile.TemporaryDirectory(prefix='lmi-camera-resume-') as temporary:
            expected=Path(temporary)/'prepared'
            prepare(repo,expected)
            for source in expected.rglob('*'):
                target=out/source.relative_to(expected)
                assert not target.is_symlink(), target
                if source.is_file():
                    assert target.is_file() and target.read_bytes()==source.read_bytes(), target
                else:assert target.is_dir(), target
        print('VERIFIED_CAMERA_PREPARATION_RESUMED',flush=True)
        return out/'source/userspace/camera/diagnostics'
    assert not out.is_symlink();out.mkdir(parents=True)
    src=out/'source/userspace/camera/diagnostics';src.mkdir(parents=True)
    original=repo/'userspace/camera/diagnostics'
    for name in ['camera-module-capture.c','camera-module-enumerate.c','camera-qti-bridge.cpp','camera-qti-bridge.h','camera-yuv-neon.h','frame-pacing.h','native-pipewire-ppm-test.c','native-pipewire-v4l2-source.c','private-context-test.c','lmi-snapshot-tuning.c']:
        shutil.copy2(original/name,src/name)
    for name in ['camera-module-capture-timing.patch','camera-preview-fixed-fps-trial.patch','camera-qti-neon-trial.patch']:
        for dry in [True,False]:
            args=['patch','--batch','--fuzz=0','-p1']+(['--dry-run'] if dry else [])
            subprocess.run(args,cwd=out/'source',input=(original/name).read_bytes(),check=True)
    producer=(src/'native-pipewire-ppm-test.c').read_text()
    producer=replace(producer,'period={0,10000000}','period={0,40000000}')
    producer=replace(producer,'seconds<1 || seconds>90','seconds<0 || seconds>90')
    producer=replace(producer,'[SECONDS:1..90]','[SECONDS:0..90; 0=app lifetime]')
    (src/'native-pipewire-ppm-test.c').write_text(producer)
    base='/usr/local/lib/lmi-camera'
    capture=(original/'camera-test-capture.py').read_text()
    for name in ['lmi-camera-super-metadata.py','liblmi_qti_bridge.so','camera-module-capture','lmi-camera-private-context-test.so']:
        capture=capture.replace('/tmp/'+name,base+'/'+name)
    # Canonical inspector was historically installed under this explicit name.
    capture=capture.replace('/tmp/inspect-system-ext-metadata.py',base+'/lmi-camera-super-metadata.py')
    preview=(original/'camera-test-rear-preview.py').read_text().replace('/tmp/camera-test-capture.py',base+'/camera-test-capture.py')
    publisher=(repo/'userspace/camera/files/lmi-camera-preview-service.py').read_text()
    publisher=replace(publisher,"/'lmi-camera'/'foreground.json'","/'lmi-snapshot'/'foreground.json'")
    publisher=replace(publisher,"'/usr/local/bin/lmi-camera'","'/usr/local/bin/lmi-snapshot'")
    files={'camera-test-capture.py':capture,'camera-test-rear-preview.py':preview,'preview-service.py':publisher,'lmi-camera-super-metadata.py':(original/'inspect-system-ext-metadata.py').read_text()}
    assets=Path(__file__).parent
    for name in ['lmi-snapshot','snapshot-focus.c','org.gnome.Snapshot.desktop','install.sh']:shutil.copy2(assets/name,out/name)
    for name,text in files.items():ast.parse(text);(out/name).write_text(text)
    service=(repo/'userspace/camera/files/lmi-camera-preview.service').read_text().replace('__CAMERA_GROUP__','mobian').replace('__CAMERA_UID__','1000')
    (out/'lmi-camera-preview.service').write_text(service)
    (out/'49-lmi-camera.rules').write_text('''// Only the fixed camera unit may be controlled by the active local user.
polkit.addRule(function(action, subject) {
    if (action.id == "org.freedesktop.systemd1.manage-units" &&
        action.lookup("unit") == "lmi-camera-preview.service" &&
        (action.lookup("verb") == "start" || action.lookup("verb") == "stop") &&
        subject.user == "mobian" && subject.local && subject.active) {
        return polkit.Result.YES;
    }
});
''')
    return src

def build(repo,root,out,libcxx,toolchain):
    assert os.getuid()==0
    assert os.readlink('/proc/self/ns/mnt')!=os.readlink('/proc/1/ns/mnt'), 'Private mount namespace required'
    subprocess.run(['python3',str(repo/'userspace/camera/snapshot-bundle/prepare-chroot.py'),str(root)],check=True)
    src=prepare(repo,out)
    for name in ['camera-module-capture','liblmi_qti_bridge.so','lmi-camera-private-context-test.so','native-pipewire-source','snapshot-focus','lmi-snapshot-tuning.so','SHA256SUMS','BUILD-INPUTS.json']:
        target=out/name
        assert not target.is_symlink() and (not target.exists() or target.is_file()),target
    assert libcxx.is_file() and libcxx.read_bytes()[:4]==b'\x7fELF'
    cc=toolchain/'aarch64-linux-android35-clang';cxx=toolchain/'aarch64-linux-android35-clang++'
    subprocess.run([str(cxx),'-shared','-fPIC','-O2','-D_LIBCPP_ABI_NAMESPACE=__1','-Wall','-Wextra','-Werror','-nostdlib++',str(src/'camera-qti-bridge.cpp'),str(libcxx),'-ldl','-Wl,-soname,liblmi_qti_bridge.so','-o',str(out/'liblmi_qti_bridge.so')],check=True)
    subprocess.run([str(cc),'-Wall','-Wextra','-Werror','-O2',str(src/'camera-module-capture.c'),'-Wl,--allow-shlib-undefined','-L'+str(out),'-llmi_qti_bridge','-ldl','-o',str(out/'camera-module-capture')],check=True)
    subprocess.run([str(cc),'-shared','-fPIC','-O2','-Wall','-Wextra','-Werror',str(src/'private-context-test.c'),'-ldl','-o',str(out/'lmi-camera-private-context-test.so')],check=True)
    # Dependencies are installed only in the retained build chroot, never on the phone.
    if not (root/'usr/include/pipewire-0.3/pipewire/pipewire.h').exists():
        subprocess.run(['chroot',str(root),'/usr/bin/env','DEBIAN_FRONTEND=noninteractive','apt-get','-o','Dpkg::Use-Pty=0','install','-y','--no-install-recommends','libpipewire-0.3-dev'],check=True,stdin=subprocess.DEVNULL)
    scratch=root/'build/lmi-complete-camera'
    assert not scratch.is_symlink()
    scratch.mkdir(exist_ok=True)
    assert scratch.is_dir()
    for name in ['native-pipewire-ppm-test.c','frame-pacing.h','lmi-snapshot-tuning.c','snapshot-focus.c','native-pipewire-source','snapshot-focus','lmi-snapshot-tuning.so']:
        assert not (scratch/name).is_symlink()
    for name in ['native-pipewire-ppm-test.c','native-pipewire-v4l2-source.c','frame-pacing.h','lmi-snapshot-tuning.c']:shutil.copy2(src/name,scratch/name)
    shutil.copy2(out/'snapshot-focus.c',scratch/'snapshot-focus.c')
    protocol='/build/phosh-0.46.0/obj-aarch64-linux-gnu/protocol'
    commands=[
        ['cc','-O2','-Wall','-Wextra','-Werror','-I/usr/include/pipewire-0.3','-I/usr/include/spa-0.2','/build/lmi-complete-camera/native-pipewire-ppm-test.c','-lpipewire-0.3','-o','/build/lmi-complete-camera/native-pipewire-source'],
        ['cc','-O2','-Wall','-Wextra','-Werror','-I/usr/include/pipewire-0.3','-I/usr/include/spa-0.2','/build/lmi-complete-camera/native-pipewire-v4l2-source.c','-lpipewire-0.3','-o','/build/lmi-complete-camera/native-pipewire-v4l2-source'],
        ['cc','-O2','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-I'+protocol,'/build/lmi-complete-camera/snapshot-focus.c',protocol+'/wlr-foreign-toplevel-management-unstable-v1-protocol.c','-lwayland-client','-o','/build/lmi-complete-camera/snapshot-focus'],
        ['cc','-shared','-fPIC','-nostdlib','-Wall','-Wextra','-Werror','/build/lmi-complete-camera/lmi-snapshot-tuning.c','-o','/build/lmi-complete-camera/lmi-snapshot-tuning.so']]
    for command in commands:subprocess.run(['chroot',str(root),*command],check=True)
    for name in ['native-pipewire-source','native-pipewire-v4l2-source','snapshot-focus','lmi-snapshot-tuning.so']:shutil.copy2(scratch/name,out/name)
    included=['camera-module-capture','liblmi_qti_bridge.so','lmi-camera-private-context-test.so','native-pipewire-source','native-pipewire-v4l2-source','snapshot-focus','lmi-snapshot-tuning.so','camera-test-capture.py','camera-test-rear-preview.py','preview-service.py','lmi-camera-super-metadata.py','lmi-snapshot','org.gnome.Snapshot.desktop','lmi-camera-preview.service','49-lmi-camera.rules','install.sh']
    (out/'SHA256SUMS').write_text(''.join(hashlib.sha256((out/n).read_bytes()).hexdigest()+'  '+n+'\n' for n in included))
    (out/'BUILD-INPUTS.json').write_text(json.dumps({'android_libcxx_sha256':hashlib.sha256(libcxx.read_bytes()).hexdigest(),'capture_started':False,'kernel_built':False},indent=2)+'\n')
    print('CAMERA_BUNDLE_COMPILED_NO_ACQUISITION',out)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--root',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--libcxx',type=Path);p.add_argument('--toolchain',type=Path);p.add_argument('--prepare-only',action='store_true');a=p.parse_args()
    if a.prepare_only:prepare(a.repo,a.output)
    else:build(a.repo,a.root,a.output,a.libcxx,a.toolchain)
