
from pathlib import Path
import importlib.util,tempfile,hashlib,json,shutil
root=Path(__file__).resolve().parent
import argparse
parser=argparse.ArgumentParser(description='Test source preparation against the pinned unpacked Debian baselines; no package builds.')
parser.add_argument('phosh_source',type=Path)
parser.add_argument('gsd_source',type=Path)
args=parser.parse_args()
sources={'phosh':args.phosh_source,'gsd':args.gsd_source}
s=importlib.util.spec_from_file_location('prepare',root/'prepare-source.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
identity=json.loads((root/'identity.json').read_text())
checks=[]
for key in ('phosh','gsd'):
    record=identity[key];base=(sources[key]/record['target']).read_bytes()
    assert m.sha(base)==record['before_raw_sha256']
    with tempfile.TemporaryDirectory(prefix='lmi-quiet-verifier-test-') as tmp:
        src=Path(tmp)/'source';p=src/record['target'];p.parent.mkdir(parents=True);p.write_bytes(base);p.chmod(0o640)
        a=m.prepare(key,src);assert not a['changed'] and p.read_bytes()==base
        checks.append(key+': default preserves source')
        a=m.prepare(key,src,True);assert a['changed'] and m.sha(p.read_bytes())==record['after_lf_sha256'] and p.stat().st_mode&0o777==0o640
        checks.append(key+': full patch produces exact v3 bytes and preserves mode')
        a=m.prepare(key,src,True);assert not a['changed']
        checks.append(key+': already applied is idempotent')
        p.write_bytes(base+b'\n/* unexpected edit */\n');changed=p.read_bytes()
        try:m.prepare(key,src,True)
        except ValueError:assert p.read_bytes()==changed
        else:raise AssertionError('Changed baseline accepted')
        checks.append(key+': unknown baseline rejected unchanged')
        p.unlink();outside=Path(tmp)/'outside.c';outside.write_bytes(base);p.symlink_to(outside)
        try:m.prepare(key,src,True)
        except ValueError:assert outside.read_bytes()==base
        else:raise AssertionError('Symlink target accepted')
        checks.append(key+': symlink rejected unchanged')
        fixture=Path(tmp)/'helper';fixture.mkdir()
        for name in ('prepare-source.py','identity.json',record['patch']):shutil.copyfile(root/name,fixture/name)
        (fixture/record['patch']).write_bytes((fixture/record['patch']).read_bytes()+b'\n')
        s2=importlib.util.spec_from_file_location('tampered',fixture/'prepare-source.py');m2=importlib.util.module_from_spec(s2);s2.loader.exec_module(m2)
        p.unlink();p.write_bytes(base)
        try:m2.prepare(key,src,True)
        except ValueError:assert p.read_bytes()==base
        else:raise AssertionError('Changed patch accepted')
        checks.append(key+': tampered patch rejected unchanged')
print(json.dumps({'passed':checks,'count':len(checks),'limits':'Source preparation tests only; no compilation or phone access.'}))
