import errno, fcntl, json, os, resource, signal, struct, subprocess, tempfile, time
from pathlib import Path
import stat,re
import argparse
parser=argparse.ArgumentParser()
mode=parser.add_mutually_exclusive_group()
mode.add_argument("--manual-exposure",action="store_true")
mode.add_argument("--ae-precapture",action="store_true")
mode.add_argument("--preview",action="store_true")
args=parser.parse_args()
capture_command="kill -STOP $$; exec /private-camera-enumerate 0"
if args.manual_exposure: capture_command += " --manual-exposure"
if args.ae_precapture: capture_command += " --ae-precapture"
if args.preview: capture_command += " --preview"

def run(*args):
    return subprocess.run(args,check=True,timeout=5,stdout=subprocess.PIPE,text=True).stdout.strip()

metadata=json.loads(run('python3','/tmp/lmi-camera-super-metadata.py'))
assert 'androidboot.hardware=qcom' in Path('/proc/cmdline').read_text().split()
assert 'ro.board.platform=kona' in Path('/vendor/build.prop').read_text().splitlines()
part=metadata['slots'][0]['system_ext'][0]
assert part['name']=='system_ext' and len(part['extents'])==1
extent=part['extents'][0]
assert extent['type']==0 and extent['source']=='super'
start=extent['sector']*512
size=extent['sectors']*512
assert 0<start<start+size<=int(run('blockdev','--getsize64','/dev/block/by-name/super'))
with open('/dev/block/by-name/super','rb',buffering=0) as f:
    f.seek(start+1080)
    assert f.read(2)==b'\x53\xef'
root=Path(tempfile.mkdtemp(prefix='lmi-camera-hidl-',dir='/run'))
mounts=[]
loop=None
child=None
client=None
provider=None
try:
    run('mount','-t','tmpfs','-o','size=16M,nosuid,nodev','tmpfs',str(root)); mounts.append(root)
    for name in ['system','system_ext','vendor','apex','proc','sys','dev','dev/binderfs','data/vendor/camera','lib/firmware/postmarketos']:
        (root/name).mkdir(parents=True,exist_ok=True)
    for source,target in [('/mnt/android-system/system','system'),('/mnt/android-vendor','vendor'),('/apex/com.android.runtime','apex/com.android.runtime'),('/proc','proc'),('/sys','sys')]:
        dst=root/target; dst.mkdir(parents=True,exist_ok=True)
        run('mount','--bind',source,str(dst)); mounts.append(dst)
        run('mount','-o','remount,bind,ro',str(dst))
    settings=Path('/vendor/etc/camera/camxoverridesettings.txt').read_text()
    assert settings.splitlines().count('enableNCSService=TRUE') == 1
    replacement=root/'private-camxoverridesettings.txt'
    replacement.write_text(settings.replace('enableNCSService=TRUE','enableNCSService=FALSE'))
    target=root/'vendor/etc/camera/camxoverridesettings.txt'
    run('mount','--bind',str(replacement),str(target)); mounts.append(target)
    run('mount','-o','remount,bind,ro',str(target))
    print('PRIVATE_CAMERA_NCS_DISABLED_NO_IMU_SERVICE',flush=True)
    firmware=root/'lib/firmware/postmarketos/CAMERA_ICP.elf'
    firmware.touch()
    run('mount','--bind','/vendor/firmware/CAMERA_ICP.elf',str(firmware)); mounts.append(firmware)
    run('mount','-o','remount,bind,ro',str(firmware))
    if args.preview:
        # Existing OEM calibration/firmware only, mounted read-only in this runtime.
        for source,target_name in [('/mnt/vendor/persist','mnt/vendor/persist'),('/mnt/vendor/firmware_mnt','vendor/firmware_mnt')]:
            target=root/target_name
            target.mkdir(parents=True,exist_ok=True)
            run('mount','--bind',source,str(target)); mounts.append(target)
            run('mount','-o','remount,bind,ro',str(target))
        firmware_dir=Path('/mnt/vendor/firmware_mnt/image')
        parts=[p for p in firmware_dir.glob('cvpss.*') if re.fullmatch(r'cvpss\.(mdt|b[0-9]{2})',p.name)]
        assert any(p.name=='cvpss.mdt' for p in parts)
        for part in parts:
            target=root/'lib/firmware/postmarketos'/part.name
            target.touch()
            run('mount','--bind',str(part),str(target)); mounts.append(target)
            run('mount','-o','remount,bind,ro',str(target))
        print('PRIVATE_CVP_FIRMWARE_PARTS '+str(len(parts)),flush=True)

    output=Path(tempfile.mkdtemp(prefix='lmi-camera-capture-',dir='/tmp'))
    print('PRIVATE_CAPTURE_DIRECTORY '+str(output),flush=True)
    destination=root/'data/vendor/camera'
    run('mount','--bind',str(output),str(destination)); mounts.append(destination)
    bridge=root/'liblmi_qti_bridge.so'; bridge.touch()
    run('mount','--bind','/tmp/liblmi_qti_bridge.so',str(bridge)); mounts.append(bridge)
    run('mount','-o','remount,bind,ro',str(bridge))
    probe=root/'private-camera-enumerate'; probe.touch()
    run('mount','--bind','/tmp/camera-module-capture',str(probe)); mounts.append(probe)
    run('mount','-o','remount,bind,ro',str(probe))
    loop=run('losetup','--find','--show','--read-only','--offset',str(start),'--sizelimit',str(size),'/dev/block/by-name/super')
    assert loop.startswith('/dev/loop') and loop[9:].isdigit()
    run('mount','-t','ext4','-o','ro,noload,nosuid,nodev',loop,str(root/'system_ext')); mounts.append(root/'system_ext')
    # Sensor enumeration variant: explicitly expose camera/ION interfaces only.
    # No block storage, DRM, input, codec video32/video33 or host Binder is exposed.
    run('mount','-t','tmpfs','-o','size=1M,nosuid','tmpfs',str(root/'dev')); mounts.append(root/'dev')
    for name in ['null','urandom','ashmem']:
        dst=root/'dev'/name; dst.touch()
        run('mount','--bind','/dev/'+name,str(dst)); mounts.append(dst)
    if args.preview:
        for name in ['cvp','synx_device']:
            original=Path('/dev')/name
            device_stat=original.stat()
            assert stat.S_ISCHR(device_stat.st_mode)
            identification=Path('/sys/dev/char',str(os.major(device_stat.st_rdev))+':'+str(os.minor(device_stat.st_rdev)),'uevent').read_text().splitlines()
            assert 'DEVNAME='+name in identification
            dst=root/'dev'/name; dst.touch()
            run('mount','--bind',str(original),str(dst)); mounts.append(dst)
        print('PRIVATE_CVP_SYNX_CHAR_INTERFACES_CHECKED',flush=True)

    assert Path('/sys/class/video4linux/video0/name').read_text().strip() == 'cam-req-mgr'
    assert Path('/sys/class/video4linux/video1/name').read_text().strip() == 'cam_sync'
    devices=[Path('/dev/ion'),Path('/dev/video0'),Path('/dev/video1')]
    devices+=list(Path('/dev').glob('media[0-9]*'))+list(Path('/dev').glob('v4l-subdev[0-9]*'))
    assert len(devices)<=64 and all(path.is_char_device() for path in devices)
    for source in devices:
        dst=root/'dev'/source.name; dst.touch()
        run('mount','--bind',str(source),str(dst)); mounts.append(dst)
    print('CAMERA_ENUMERATION_NODE_COUNT '+str(len(devices)),flush=True)
    (root/'dev/binderfs').mkdir()
    run('mount','-t','binder','binder',str(root/'dev/binderfs')); mounts.append(root/'dev/binderfs')
    with (root/'dev/binderfs/binder-control').open('rb',buffering=0) as ctl:
        for name in ['binder','hwbinder','vndbinder']:
            if not (root/'dev/binderfs'/name).exists():
                data=bytearray(struct.pack('<256sII',name.encode(),0,0))
                fcntl.ioctl(ctl.fileno(),0xc1086201,data,True)
            (root/'dev'/name).symlink_to('binderfs/'+name)
    versions={}
    for name in ['binder','hwbinder','vndbinder']:
        with (root/'dev'/name).open('rb',buffering=0) as f:
            data=bytearray(4)
            fcntl.ioctl(f.fileno(),0xc0046209,data,True)
            versions[name]=struct.unpack('<I',data)[0]
    print('PRIVATE_BINDER_PROTOCOLS '+json.dumps(versions),flush=True)
    shim=root/'private-context-test.so'
    shim.touch()
    run('mount','--bind','/tmp/lmi-camera-private-context-test.so',str(shim)); mounts.append(shim)
    run('mount','-o','remount,bind,ro',str(shim))
    def limits():
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        os.chroot(root)
        os.chdir('/')
    os.environ['LMI_PRIVATE_BINDER_NO_SECCTX']='1'
    child=subprocess.Popen(['/system/bin/bootstrap/linker64','/system_ext/bin/hwservicemanager'],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True,preexec_fn=limits,env={'PATH':'/system/bin','ANDROID_ROOT':'/system','ANDROID_DATA':'/data','LD_PRELOAD':'/private-context-test.so','LMI_PRIVATE_CONTEXT_ACTIVE':'1','LMI_PRIVATE_BINDER_NO_SECCTX':'1','LMI_PRIVATE_PEER_CHECK':'1'})
    time.sleep(2)
    registered=False
    with (root/'dev/hwbinder').open('rb',buffering=0) as f:
        try:
            fcntl.ioctl(f.fileno(),0x40046207,struct.pack('<I',0))
            print('HWBINDER_CONTEXT_WAS_UNOWNED_PROBE_FD_CLOSED',flush=True)
        except OSError as error:
            print('HWBINDER_CONTEXT_PROBE_ERRNO '+str(error.errno),flush=True)
            if error.errno == errno.EBUSY:
                print('HWBINDER_CONTEXT_MANAGER_ALREADY_REGISTERED',flush=True)
                registered=True
    assert registered, 'private manager registration missing'
    print('THREAD_WAIT_STATES '+json.dumps({t.name:(t/'wchan').read_text().strip() for t in Path('/proc').joinpath(str(child.pid),'task').iterdir()}),flush=True)
    client=subprocess.Popen(['/system/bin/sh','-c','kill -STOP $$; exec /system/bin/lshal list --types=binderized --neat --interface'],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True,preexec_fn=limits,env={'PATH':'/system/bin','ANDROID_ROOT':'/system','ANDROID_DATA':'/data','LD_PRELOAD':'/private-context-test.so','LMI_PRIVATE_CONTEXT_ACTIVE':'1','LMI_PRIVATE_BINDER_NO_SECCTX':'1','LMI_PRIVATE_HIDL_READY_CHECKED':'1'})
    deadline=time.monotonic()+1
    while time.monotonic()<deadline:
        status_line=next(line for line in Path('/proc',str(client.pid),'status').read_text().splitlines() if line.startswith('State:'))
        if 'T (stopped)' in status_line:
            break
        time.sleep(0.02)
    else:
        raise RuntimeError('client did not stop at identity gate')
    (root/'checked-client.pid').write_text(str(client.pid)+'\n')
    (root/'checked-client.pid').chmod(0o400)
    os.kill(client.pid,signal.SIGCONT)
    try:
        client_output,_=client.communicate(timeout=4)
        client_status=client.returncode
    except subprocess.TimeoutExpired:
        os.killpg(client.pid,signal.SIGKILL)
        client_output,_=client.communicate(timeout=2)
        client_status='timeout'
    print('HIDL_CLIENT_RESULT '+str(client_status)+'\n'+client_output[:12000],flush=True)
    assert client_status in (0,72), 'client IPC prerequisite failed'
    assert 'FAILED_TRANSACTION' not in client_output and 'DEAD_OBJECT' not in client_output and 'interfaceChain fails' not in client_output, 'client interface IPC failed'
    if client_status == 72:
        assert 'android.hidl.manager@1.2::IServiceManager/default' in client_output
        assert 'android.hidl.token@1.0::ITokenManager/default' in client_output
        print('CLIENT_SERVICE_QUERY_WORKS_DEBUG_PID_METADATA_WARNING',flush=True)
    provider=subprocess.Popen(['/system/bin/sh','-c',capture_command],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True,preexec_fn=limits,env={'PATH':'/system/bin','ANDROID_ROOT':'/system','ANDROID_DATA':'/data','LD_PRELOAD':'/private-context-test.so','LMI_PRIVATE_CONTEXT_ACTIVE':'1','LMI_PRIVATE_BINDER_NO_SECCTX':'1','LMI_PRIVATE_HIDL_READY_CHECKED':'1','LD_LIBRARY_PATH':'/','LMI_PRIVATE_BOOT_HARDWARE':'qcom','LMI_PRIVATE_BOOT_PLATFORM':'kona'})
    deadline=time.monotonic()+1
    while time.monotonic()<deadline:
        status_line=next(line for line in Path('/proc',str(provider.pid),'status').read_text().splitlines() if line.startswith('State:'))
        if 'T (stopped)' in status_line:
            break
        time.sleep(0.02)
    else:
        raise RuntimeError('provider did not stop at identity gate')
    (root/'checked-client.pid').write_text(str(provider.pid)+'\n')
    os.kill(provider.pid,signal.SIGCONT)
    time.sleep(2)
    if provider.poll() is None:
        print('MODULE_THREAD_WAITS '+json.dumps({t.name:(t/'wchan').read_text().strip() for t in Path('/proc',str(provider.pid),'task').iterdir()}),flush=True)
        print('MANAGER_THREAD_WAITS '+json.dumps({t.name:(t/'wchan').read_text().strip() for t in Path('/proc',str(child.pid),'task').iterdir()}),flush=True)
    try:
        provider_output,_=provider.communicate(timeout=35)
        provider_status=provider.returncode
    except subprocess.TimeoutExpired:
        print('MODULE_FINAL_THREAD_WAITS '+json.dumps({t.name:(t/'wchan').read_text().strip() for t in Path('/proc',str(provider.pid),'task').iterdir()}),flush=True)
        print('MODULE_MAIN_KERNEL_STACK '+Path('/proc',str(provider.pid),'stack').read_text()[:2000],flush=True)
        os.killpg(provider.pid,signal.SIGKILL)
        provider_output,_=provider.communicate(timeout=2)
        provider_status='running until bounded enumeration stop'
    print('PROVIDER_ENUMERATION_RESULT '+str(provider_status)+'\n'+provider_output[:6000]+'\nPROVIDER_LOG_TAIL\n'+provider_output[-6000:],flush=True)
    (output/'capture.log').write_text(provider_output)
    try:
        output,_=child.communicate(timeout=4)
        status=child.returncode
    except subprocess.TimeoutExpired:
        os.killpg(child.pid,signal.SIGKILL)
        output,_=child.communicate(timeout=2)
        status='running until test stop'
    print('HIDL_MANAGER_TEST_RESULT '+str(status),flush=True)
    print(output[:12000],flush=True)
finally:
    if provider is not None and provider.poll() is None:
        os.killpg(provider.pid,signal.SIGKILL); provider.wait(timeout=2)
    if client is not None and client.poll() is None:
        os.killpg(client.pid,signal.SIGKILL); client.wait(timeout=2)
    if child is not None and child.poll() is None:
        os.killpg(child.pid,signal.SIGKILL); child.wait(timeout=2)
    for point in reversed(mounts):
        run('umount',str(point))
    if loop:
        run('losetup','--detach',loop)
    root.rmdir()
    print('ISOLATED_RUNTIME_REMOVED',flush=True)

# A cleaned-up runtime is not proof that its camera client succeeded.
if provider_status != 0:
    raise SystemExit(1)
