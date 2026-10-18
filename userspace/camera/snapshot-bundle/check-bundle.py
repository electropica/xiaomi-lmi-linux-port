#!/usr/bin/env python3
"""Validate one fixed, externally built ARM64 camera bundle before image staging."""
import ast,hashlib,subprocess,sys
from pathlib import Path
NAMES={'camera-module-capture','liblmi_qti_bridge.so','lmi-camera-private-context-test.so','native-pipewire-source','snapshot-focus','lmi-snapshot-tuning.so','camera-test-capture.py','camera-test-rear-preview.py','preview-service.py','lmi-camera-super-metadata.py','lmi-snapshot','org.gnome.Snapshot.desktop','lmi-camera-preview.service','49-lmi-camera.rules','install.sh'}
BINARIES={'camera-module-capture','liblmi_qti_bridge.so','lmi-camera-private-context-test.so','native-pipewire-source','snapshot-focus','lmi-snapshot-tuning.so'}
def check(root):
    assert root.is_dir() and not root.is_symlink(), 'Regular bundle directory required'
    manifest=root/'SHA256SUMS'
    assert manifest.is_file() and not manifest.is_symlink()
    expected={}
    for line in manifest.read_text().splitlines():
        digest,name=line.split('  ',1)
        assert name in NAMES and name not in expected
        assert len(digest)==64 and all(c in '0123456789abcdef' for c in digest)
        expected[name]=digest
    assert set(expected)==NAMES, 'Incomplete bundle manifest'
    for name,digest in expected.items():
        p=root/name
        assert p.is_file() and not p.is_symlink(), name
        data=p.read_bytes()
        assert hashlib.sha256(data).hexdigest()==digest, name
        if name in BINARIES:
            assert data[:6]==b'\x7fELF\x02\x01' and int.from_bytes(data[18:20],'little')==183, name+' must be AArch64 ELF'
        elif name.endswith('.py') or name=='lmi-snapshot':ast.parse(data,filename=name)
    subprocess.run(['bash','-n',str(root/'install.sh')],check=True)
    assert 'Exec=/usr/local/bin/lmi-snapshot' in (root/'org.gnome.Snapshot.desktop').read_text()
    print('COMPLETE_CAMERA_BUNDLE_VALIDATED')
if __name__=='__main__':check(Path(sys.argv[1]))
