"""Host-only restart and archive checks. No chroot, package build or device IO."""
from pathlib import Path
import importlib.util,json,shutil,subprocess,tempfile
task=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('recipe',task/'build-packages.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
manifest=json.loads((task/'identity.json').read_text());realroot=m.ROOT
checks=[]
with tempfile.TemporaryDirectory(prefix='lmi-esr-host-check-') as td:
 root=Path(td);m.ROOT=root/'root'
 for spec in manifest['sources']:
  p=m.ROOT/'build'/spec['tree']/spec['file'];p.parent.mkdir(parents=True,exist_ok=True)
  assert m.sha(realroot/'build'/spec['tree']/spec['file'])==spec['before']
  shutil.copyfile(realroot/'build'/spec['tree']/spec['file'],p)
 first=root/'first';first.mkdir();m.patched_sources(manifest,first);checks.append('clean_patch_replay')
 for spec in manifest['sources']:shutil.copyfile(first/spec['file'],m.ROOT/'build'/spec['tree']/spec['file'])
 second=root/'second';second.mkdir();m.patched_sources(manifest,second);checks.append('already_patched_reverse_then_replay')
 assert all(m.sha(first/s['file'])==m.sha(second/s['file']) for s in manifest['sources'])
 # A new patch digest alone cannot silently bless an old already-patched tree.
 revised=root/'revised';revised.mkdir()
 (revised/'esr-delta-accept.patch').write_text((task/'esr-delta-accept.patch').read_text().replace('445 esr-delta','446 esr-delta'))
 m.TASK=revised;attempt=root/'revised-attempt';attempt.mkdir()
 try:m.patched_sources(manifest,attempt)
 except (AssertionError,subprocess.CalledProcessError):checks.append('changed_patch_with_stale_after_rejected')
 else:raise AssertionError('Changed patch accepted against stale source')
 m.TASK=task
 # Reject a source/changelog mismatch before any archive or build operation.
 spec=manifest['sources'][0];tree=m.ROOT/'build'/spec['tree']
 (tree/'debian').mkdir();(tree/'debian/changelog').write_text(spec['package']+' ('+spec['old']+') UNRELEASED; urgency=medium\n')
 try:m.verify(manifest)
 except AssertionError as error:
  assert 'Source/changelog state mismatch' in str(error);checks.append('source_changelog_mismatch_rejected')
 else:raise AssertionError('Mismatched changelog accepted')
 spec=manifest['sources'][0]
 shutil.copyfile(realroot/'build'/spec['tree']/spec['file'],m.ROOT/'build'/spec['tree']/spec['file'])
 mixed=root/'mixed';mixed.mkdir()
 try:m.patched_sources(manifest,mixed)
 except AssertionError:checks.append('mixed_state_rejected')
 else:raise AssertionError('Mixed sources accepted')
m.ROOT=realroot
for spec in manifest['sources']:
 p=realroot/'build'/f'{spec["package"]}_{spec["old"]}_arm64.deb'
 binary={'phosh':'usr/libexec/phosh','gnome-settings-daemon':'usr/libexec/gsd-power'}[spec['package']]
 entries,data=m.payload_identity(p,binary)
 assert entries and data and b'445 esr-delta' not in data
 checks.append(spec['package']+'_rollback_binary_extraction')
record={'result':'PASS','checks':checks,'package_build':False,'phone_contact':False}
(task/'host-checks.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
