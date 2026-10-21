#!/usr/bin/env python3
"""Host-only artifact/invariant tests. No mounts, devices or image builds."""
import argparse,copy,gzip,hashlib,json,struct,unittest
from pathlib import Path
import prepare

def unpack_cpio(data):
    entries={};pos=0
    while pos<len(data):
        h=data[pos:pos+110];assert h[:6]==b'070701'
        v=[int(h[i:i+8],16) for i in range(6,110,8)]
        ns=pos+110;st=prepare.align(ns+v[11],4)
        name=data[ns:ns+v[11]-1].decode()
        entries[name]=(v,data[st:st+v[6]])
        pos=prepare.align(st+v[6],4)
        if name=='TRAILER!!!':break
    return entries

class Checks(unittest.TestCase):
    def test_layout_is_contained_and_aligned(self):
        p=prepare.layout_plan(layout);a=p['userdata'];b=p['mobian']
        self.assertEqual(a['new_end_lba']+1,b['start_lba'])
        self.assertEqual((b['end_lba']-b['start_lba']+1)*4096,16*1024**3)
        self.assertEqual(b['start_lba']%256,0)
        self.assertLessEqual(b['end_lba'],layout['last_usable_lba'])
        self.assertEqual(a['start_lba'],2883584)
    def test_wrong_geometry_rejected(self):
        d=copy.deepcopy(layout);d['sector_bytes']=512
        with self.assertRaises(ValueError):prepare.layout_plan(d)
    def test_existing_target_rejected(self):
        d=copy.deepcopy(layout);d['entries'].append({'label':'mobian','number':35,'start_lba':1,'end_lba':2})
        with self.assertRaises(ValueError):prepare.layout_plan(d)
    def test_userdata_not_last_rejected(self):
        d=copy.deepcopy(layout);d['entries'][-1]['end_lba']-=256
        with self.assertRaises(ValueError):prepare.layout_plan(d)
    def test_boot_and_archive_only_expected_file_changes(self):
        before=prepare.boot_parts(boot)[1];result,manifest=prepare.repack(boot,replacement)
        after=prepare.boot_parts(result)[1]
        for i in (0,2,3,4):self.assertEqual(before[i],after[i])
        a=unpack_cpio(gzip.decompress(before[1]));b=unpack_cpio(gzip.decompress(after[1]))
        self.assertEqual(set(a),set(b))
        changed=[n for n in a if a[n]!=b[n]]
        self.assertEqual([n.lstrip('./') for n in changed],['init_functions.sh'])
        n=changed[0];v1,c1=a[n];v2,c2=b[n]
        for i in range(len(v1)):
            if i!=6:self.assertEqual(v1[i],v2[i])
        text=c2.decode();start=text.index('mount_subpartitions() {\n');end=text.index('\n# Rewrite /dev/dm-X paths',start)
        self.assertNotIn('userdata',text[start:end].replace('# This boot MUST NOT discover, mount or resize Android userdata.','').replace('userdata untouched.',''))
        self.assertIn('/dev/disk/by-partlabel/mobian',text[start:end])
        ident=hashlib.sha1()
        for p in after:ident.update(p);ident.update(struct.pack('<I',len(p)))
        self.assertEqual(result[576:596],ident.digest())
        self.assertEqual(manifest['kernel_sha256'],'87c53d33202d4607591fa0ba6d2bf091dc2dfc4673a3326436740a1f0e7bae6a')
    def test_wrong_boot_rejected(self):
        with self.assertRaises(ValueError):prepare.repack(boot[:-1]+b'X',replacement)
    def test_source_drift_rejected(self):
        data=gzip.decompress(prepare.boot_parts(boot)[1][1])
        data=data.replace(b'mount_subpartitions() {',b'mount_subpartitions()!{',1)
        with self.assertRaises(ValueError):prepare.cpio_replace(data,'init_functions.sh',replacement)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--boot',type=Path,required=True);p.add_argument('--layout',type=Path,required=True);a=p.parse_args()
    boot=a.boot.read_bytes();layout=json.loads(a.layout.read_text());replacement=Path(__file__).with_name('mount-dualboot.sh').read_text()
    unittest.main(argv=['test_prepare.py'])
