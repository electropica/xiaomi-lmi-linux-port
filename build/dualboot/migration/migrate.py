"""Windows recovery GPT migration. Default is read-only; no format/flash."""
import argparse,datetime,hashlib,json,shlex,subprocess,sys
from pathlib import Path
from gpt_model import SECTOR,DISK_BYTES,header,build
def run(args,timeout=20):
    p=subprocess.run([str(x) for x in args],capture_output=True,timeout=timeout)
    if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace'))
    return p.stdout
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');ap.add_argument('--discard-current-installation',action='store_true');ap.add_argument('--work-dir',type=Path,default=Path.home()/'Documents/ChatGPT/Mobian/work');a=ap.parse_args()
    if a.apply and not a.discard_current_installation:raise SystemExit('Explicit fresh-installation flag required')
    root=a.work_dir.resolve(strict=True)
    adb=Path.home()/'Downloads/platform-tools/adb.exe'
    rows=[l.split() for l in run([adb,'devices']).decode().splitlines()[1:] if l.strip()]
    if len(rows)!=1 or rows[0][1]!='recovery':raise RuntimeError('Exactly one recovery device required')
    serial=rows[0][0]
    def shell(command):return run([adb,'-s',serial,'shell','-T','sh','-c',shlex.quote(command)]).decode().strip()
    if shell('id -u')!='0' or shell('getprop ro.product.device')!='lmi' or not shell('pidof recovery'):raise RuntimeError('Root lmi recovery required')
    if shell('readlink -f /dev/block/by-name/userdata')!='/dev/block/sda34':raise RuntimeError('Unexpected userdata device')
    if shell('blockdev --getss /dev/block/sda')!=str(SECTOR) or shell('blockdev --getsize64 /dev/block/sda')!=str(DISK_BYTES):raise RuntimeError('Unexpected disk geometry')
    mounts=shell('cat /proc/mounts')
    if any(l.startswith(('/dev/block/','/dev/mapper/','/dev/loop')) for l in mounts.splitlines()):raise RuntimeError('Block-backed filesystem mounted: refusing partition change')
    def read(lba,count):
        data=run([adb,'-s',serial,'exec-out','dd','if=/dev/block/sda','bs=4096',f'skip={lba}',f'count={count}','status=none'])
        if len(data)!=count*SECTOR:raise RuntimeError('Short device read')
        return data
    last=DISK_BYTES//SECTOR-1
    ph,bh=read(1,1),read(last,1);p,b=header(ph,1),header(bh,last)
    pt,bt=read(p['table'],2),read(b['table'],2)
    expected=json.loads((root/'dualboot-layout-20261021-private.json').read_text())
    changes,plan=build(ph,bh,pt,bt,expected)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder=root/('dualboot-gpt-'+stamp+'-private');folder.mkdir()
    for n,data in [('original-primary-header.bin',ph),('original-backup-header.bin',bh),('original-table.bin',pt)]: (folder/n).write_bytes(data)
    (folder/'plan.json').write_text(json.dumps(plan,indent=2))
    print(json.dumps({'mode':'APPLY' if a.apply else 'READ_ONLY','plan':plan,'record':str(folder)}),flush=True)
    if not a.apply:return
    # A fresh reread immediately before the first write must still match.
    if read(1,1)!=ph or read(last,1)!=bh or read(p['table'],2)!=pt or read(b['table'],2)!=bt:raise RuntimeError('GPT changed during preflight; no write')
    remote='/tmp/lmi-dualboot-'+stamp
    shell('mkdir '+remote)
    completed=[]
    try:
        for i,(lba,data) in enumerate(changes):
            file=folder/f'new-{i}.bin';file.write_bytes(data)
            target=remote+f'/new-{i}.bin'
            run([adb,'-s',serial,'push',file,target])
            if shell('sha256sum '+target).split()[0]!=hashlib.sha256(data).hexdigest():raise RuntimeError('RAM transfer hash mismatch')
            shell(f'dd if={target} of=/dev/block/sda bs=4096 seek={lba} count={len(data)//SECTOR} conv=notrunc,fsync status=none')
            if read(lba,len(data)//SECTOR)!=data:raise RuntimeError('GPT write readback mismatch')
            completed.append(lba);(folder/'writes.json').write_text(json.dumps(completed))
        if read(1,1)!=changes[3][1] or read(last,1)!=changes[1][1] or read(p['table'],2)!=changes[2][1] or read(b['table'],2)!=changes[0][1]:raise RuntimeError('Final GPT differs')
        print('GPT_WRITTEN_AND_READBACK_VERIFIED. No filesystem formatted, no image flashed.',flush=True)
        print('Recovery must be restarted before using the new partition sizes.',flush=True)
    except Exception:
        print('STOP: partial GPT operation possible. Do not format, flash or retry. Preserve this record.',file=sys.stderr,flush=True)
        raise
if __name__=='__main__':main()
