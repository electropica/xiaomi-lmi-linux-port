#!/usr/bin/env python3
"""Operator-run isolated front-camera native tools; default is host preparation only.
No phone contact, service action, kernel/image build or installation.
"""
import argparse,ast,hashlib,importlib.util,json,shutil,subprocess,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
DEFAULT_BUNDLE=Path('/home/linuxagent/mobian-lmi-dualboot-20261021-camera-bundle')
DEFAULT_CC=Path('/home/linuxagent/android-ndk-r27d/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android35-clang')
RUNTIME='/var/tmp/lmi-front-hal-trial-20261026/backend'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replace_once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)

def prepare(bundle,output):
 identity=json.loads((HERE/'identity.json').read_text())
 assert sha(HERE/'prerequisite-r2.patch')==identity['patch_sha256']
 sums={line.split(None,1)[1].strip():line.split()[0] for line in (bundle/'SHA256SUMS').read_text().splitlines()}
 assets=['liblmi_qti_bridge.so','lmi-camera-private-context-test.so','lmi-camera-super-metadata.py']
 for name in assets:assert sha(bundle/name)==sums[name],name
 with tempfile.TemporaryDirectory(prefix='lmi-front-native-') as td:
  t=Path(td);shim=t/'repo';src=shim/'userspace/camera/diagnostics';src.mkdir(parents=True)
  names=['camera-module-capture.c','camera-module-enumerate.c','camera-qti-bridge.cpp','camera-qti-bridge.h','camera-yuv-neon.h','frame-pacing.h','native-pipewire-ppm-test.c','private-context-test.c','lmi-snapshot-tuning.c','camera-module-capture-timing.patch','camera-preview-fixed-fps-trial.patch','camera-qti-neon-trial.patch','camera-test-capture.py','camera-test-rear-preview.py','inspect-system-ext-metadata.py']
  for name in names:shutil.copyfile(REPO/'userspace/camera/diagnostics'/name,src/name)
  f=shim/'userspace/camera/files';f.mkdir()
  for name in ['lmi-camera-preview-service.py','lmi-camera-preview.service']:shutil.copyfile(REPO/'userspace/camera/files'/name,f/name)
  for item in identity['files']:assert sha(shim/item['path'])==item['before_sha256'],item['path']
  for check in (True,False):subprocess.run(['git','apply']+(['--check'] if check else [])+[str(HERE/'prerequisite-r2.patch')],cwd=shim,check=True)
  for item in identity['files']:assert sha(shim/item['path'])==item['after_sha256'],item['path']
  spec=importlib.util.spec_from_file_location('bundle_builder',REPO/'userspace/camera/snapshot-bundle/build-bundle.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  prepared=t/'prepared';module.prepare(shim,prepared)
  generated=prepared/'source/userspace/camera/diagnostics'
  assert not output.exists(),'Use a fresh output directory; existing artifacts are never overwritten'
  output.mkdir(parents=True)
  dst=output/'source';dst.mkdir()
  for name in names:
   p=generated/name
   if p.exists():shutil.copyfile(p,dst/name)
  # Private copies use a dedicated backend path; installed rear assets are untouched.
  capture=(prepared/'camera-test-capture.py').read_text().replace('/usr/local/lib/lmi-camera',RUNTIME)
  enum=replace_once(capture,'capture_command="kill -STOP $$; exec /private-camera-enumerate %d" % args.camera_id','capture_command="kill -STOP $$; exec /private-camera-enumerate"')
  enum=replace_once(enum,"'"+RUNTIME+"/camera-module-capture'","'"+RUNTIME+"/camera-module-enumerate'")
  preview=(prepared/'camera-test-rear-preview.py').read_text().replace('/usr/local/lib/lmi-camera',RUNTIME).replace(RUNTIME+'/camera-test-capture.py',RUNTIME+'/capture-private-runtime.py')
  for name,text in [('capture-private-runtime.py',capture),('enumerate-private-runtime.py',enum),('preview-private-runtime.py',preview)]:
   ast.parse(text)
   assert '/tmp/camera-test-capture.py' not in text
   if name=='preview-private-runtime.py':assert RUNTIME+'/capture-private-runtime.py' in text
   (output/name).write_text(text)
  for name in assets:shutil.copyfile(bundle/name,output/name)
  result={'preparation_only':True,'camera_started':False,'motor_started':False,'rootfs_or_kernel_built':False,'external_assets':{n:sha(output/n) for n in assets},'source_hashes':{p.name:sha(p) for p in dst.iterdir() if p.is_file()}}
  (output/'PREPARED.json').write_text(json.dumps(result,indent=2))
  return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--bundle',type=Path,default=DEFAULT_BUNDLE);p.add_argument('--cc',type=Path,default=DEFAULT_CC);p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:
  with tempfile.TemporaryDirectory(prefix='lmi-front-preflight-') as td:
   r=prepare(a.bundle,Path(td)/'candidate')
   assert a.cc.is_file(),'NDK compiler missing'
   print(json.dumps({'preflight':'PASS','source_files':len(r['source_hashes']),'ndk_present':True,'compilation_started':False,'phone_contact':False}))
  return
 out=a.output or REPO/'output/front-camera-native-candidate'
 assert a.cc.is_file()
 prepare(a.bundle,out)
 src=out/'source'
 for name,flags in [('camera-module-enumerate',[]),('camera-module-capture',['-Wl,--allow-shlib-undefined','-L'+str(out),'-llmi_qti_bridge'])]:
  subprocess.run([str(a.cc),'-Wall','-Wextra','-Werror','-O2',str(src/(name+'.c')),*flags,'-ldl','-o',str(out/name)],check=True)
  assert (out/name).read_bytes()[:4]==b'\x7fELF'
 files=[p for p in out.iterdir() if p.is_file() and p.name not in ('SHA256SUMS','BUILD_RESULT.json')]
 (out/'SHA256SUMS').write_text(''.join(sha(f)+'  '+f.name+'\n' for f in sorted(files)))
 (out/'BUILD_RESULT.json').write_text(json.dumps({'camera_started':False,'installed':False,'kernel_built':False,'binaries':{n:sha(out/n) for n in ('camera-module-capture','camera-module-enumerate')}},indent=2))
 print('FRONT_CAMERA_NATIVE_TOOLS_BUILT_NOT_INSTALLED')
 print('OUTPUT='+str(out))
if __name__=='__main__':main()
