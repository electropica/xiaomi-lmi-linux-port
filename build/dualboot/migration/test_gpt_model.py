"""Read-only fixtures for the exact constrained GPT transformation."""
import argparse,copy,json,struct,unittest
from pathlib import Path
from gpt_model import build,crc,header,SECTOR,DISK_BYTES
def fix(raw):
    h=bytearray(raw);h[16:20]=b'\0'*4;struct.pack_into('<I',h,16,crc(h[:92]));return bytes(h)
class Checks(unittest.TestCase):
    def transform(self,ph=None,bh=None,pt=None,bt=None,expect=None):
        return build(ph or primary,bh or backup,pt or table,bt or table,expect or expected)
    def test_only_intended_entries_change(self):
        changes,p=self.transform();new=changes[0][1]
        self.assertEqual(new[:33*128],table[:33*128])
        self.assertEqual(new[35*128:],table[35*128:])
        self.assertEqual(new[33*128:33*128+40],table[33*128:33*128+40])
        self.assertEqual(new[33*128+48:34*128],table[33*128+48:34*128])
        self.assertEqual(p['mobian_bytes'],16*1024**3)
        self.assertEqual(p['userdata_new_end_lba']+1,p['mobian_start_lba'])
        self.assertEqual(p['mobian_start_lba']%256,0)
        self.assertLessEqual(p['mobian_end_lba'],expected['last_usable_lba'])
    def test_headers_and_write_order(self):
        changes,p=self.transform();last=DISK_BYTES//SECTOR-1
        self.assertEqual([x[0] for x in changes],[last-4,last,2,1])
        for i,old,where in ((1,backup,last),(3,primary,1)):
            raw=changes[i][1];parsed=header(raw,where)
            self.assertEqual(parsed['table_crc'],crc(changes[0][1]))
            a=bytearray(raw);a[16:20]=old[16:20];a[88:92]=old[88:92]
            self.assertEqual(bytes(a),old)
    def test_bad_primary_crc(self):
        ph=bytearray(primary);ph[60]^=1
        with self.assertRaises(ValueError):self.transform(ph=bytes(ph))
    def test_bad_backup_crc(self):
        bh=bytearray(backup);bh[60]^=1
        with self.assertRaises(ValueError):self.transform(bh=bytes(bh))
    def test_bad_table_crc(self):
        pt=bytearray(table);pt[4]^=1
        with self.assertRaises(ValueError):self.transform(pt=bytes(pt),bt=bytes(pt))
    def test_table_copies_disagree(self):
        pt=bytearray(table);pt[4]^=1
        with self.assertRaises(ValueError):self.transform(bt=bytes(pt))
    def test_stale_geometry_snapshot(self):
        e=copy.deepcopy(expected);e['entries'][-1]['end_lba']-=1
        with self.assertRaises(ValueError):self.transform(expect=e)
    def test_different_disk_guid(self):
        bh=bytearray(backup);bh[56]^=1
        with self.assertRaises(ValueError):self.transform(bh=fix(bh))
    def test_unexpected_table_location(self):
        bh=bytearray(backup);struct.pack_into('<Q',bh,72,DISK_BYTES//SECTOR-3)
        with self.assertRaises(ValueError):self.transform(bh=fix(bh))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--record',type=Path,required=True);ap.add_argument('--expected',type=Path,required=True);a=ap.parse_args()
    primary=(a.record/'original-primary-header.bin').read_bytes();backup=(a.record/'original-backup-header.bin').read_bytes();table=(a.record/'original-table.bin').read_bytes();expected=json.loads(a.expected.read_text())
    unittest.main(argv=['test_gpt_model.py'])
