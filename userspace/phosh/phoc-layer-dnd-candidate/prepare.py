#!/usr/bin/env python3
"""Pin official Debian inputs and prepare a resumable Phoc-only candidate."""
import hashlib,subprocess,sys,urllib.request
from pathlib import Path
root,task=map(Path,sys.argv[1:]);stage=root/'build/lmi-phoc-layer-dnd-inputs';stage.mkdir(exist_ok=True)
inputs={
 'phoc_0.46.0.orig.tar.xz':'862e93ed915ffa7230db3e6fbf80c348f5d36f027e49b69d1b23220239bef899',
 'phoc_0.46.0-1.debian.tar.xz':'920d023291ad37739c048014db2b3fd1d41ca35a715fd459ac35f3530b7e26f5',
}
for name,digest in inputs.items():
 p=stage/name
 if not p.exists():p.write_bytes(urllib.request.urlopen('https://deb.debian.org/debian/pool/main/p/phoc/'+name,timeout=60).read())
 assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,name
# The DSC itself is pinned alongside the recipe; it names these exact hashes.
p=task/'phoc_0.46.0-1.dsc'
assert hashlib.sha256(p.read_bytes()).hexdigest()==(task/'dsc.sha256').read_text().strip()
(stage/p.name).write_bytes(p.read_bytes())
src=root/'build/phoc-lmi-shell-dnd1'
if not src.exists():subprocess.run(['dpkg-source','--no-check','-x',str(stage/p.name),str(src)],check=True)
original,patched=[line.split()[0] for line in (task/'cursor.sha256').read_text().splitlines()]
cursor=src/'src/cursor.c';digest=hashlib.sha256(cursor.read_bytes()).hexdigest()
assert digest in [original,patched], 'Unexpected cursor.c; refusing overwrite'
if digest==original:subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(task/'preserve-shell-dnd.patch')],cwd=src,check=True)
assert hashlib.sha256(cursor.read_bytes()).hexdigest()==patched
rules=src/'debian/rules';text=rules.read_text()
if '\tdh $@\n' in text:text=text.replace('\tdh $@\n','\tdh $@ --builddirectory=_build\n');rules.write_text(text)
assert '\tdh $@ --builddirectory=_build\n' in rules.read_text()
# Debian's space-indented LC_ALL assignment is parsed as a make variable,
# leaving the test override empty. A recipe must start with a tab.
text=rules.read_text()
text=text.replace('        LC_ALL=C.UTF-8 xvfb-run ninja -C _build test', '\tLC_ALL=C.UTF-8 xvfb-run -a ninja -C _build test')
rules.write_text(text)
assert '\tLC_ALL=C.UTF-8 xvfb-run -a ninja -C _build test' in text
print('PHOC_SOURCE_VERIFIED; UPSTREAM_TESTS_ENABLED')
