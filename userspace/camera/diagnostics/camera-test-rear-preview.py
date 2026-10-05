# Explicit rear-only diagnostic; use a bounded control-group service.
# Existing OEM firmware stays external. Ordinary exit/handled signals clean links.
import os, re, signal, struct, subprocess
os.umask(0o077)
from pathlib import Path

source=Path('/mnt/vendor/firmware_mnt/image')
target=Path('/lib/firmware/postmarketos')
assert target.is_dir()
assert Path('/sys/module/firmware_class/parameters/path').read_text().strip()==str(target)
parts=sorted(p for p in source.glob('cvpss.*') if re.fullmatch(r'cvpss\.(mdt|b[0-9]{2})',p.name))
mdt=(source/'cvpss.mdt').read_bytes()
assert mdt[:6]==b'\x7fELF\x01\x01'
phoff=struct.unpack_from('<I',mdt,28)[0]
phsize,phnum=struct.unpack_from('<HH',mdt,42)
assert phsize==32 and phnum<128
required=[]
for i in range(phnum):
    typ,offset,vaddr,paddr,filesz,memsz,flags,align=struct.unpack_from('<8I',mdt,phoff+i*phsize)
    if typ==1 and filesz and (flags & (7<<24)) != (2<<24):
        part=source/('cvpss.b%02d'%i)
        assert part.is_file() and part.stat().st_size==filesz, (i,filesz)
        required.append(i)
print('CVP_ELF_SEGMENTS_MATCH '+str(required),flush=True)
assert parts and all(not os.path.lexists(target/p.name) for p in parts)
created=[]
def interrupted(signum,frame):
    raise RuntimeError('bounded test interrupted '+str(signum))
signal.signal(signal.SIGTERM,interrupted)
signal.signal(signal.SIGINT,interrupted)
try:
    for part in parts:
        link=target/part.name
        link.symlink_to(part)
        created.append((link,str(part)))
    print('TEMPORARY_HOST_CVP_LINKS '+str(len(created)),flush=True)
    result=subprocess.run(['unshare','--mount','--net','--propagation','private','python3','/tmp/camera-test-capture.py','--preview'],timeout=44)
finally:
    for link,destination in reversed(created):
        assert link.is_symlink() and os.readlink(link)==destination
        link.unlink()
    print('TEMPORARY_HOST_CVP_LINKS_REMOVED '+str(len(created)),flush=True)
raise SystemExit(result.returncode)
