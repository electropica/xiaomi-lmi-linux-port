import importlib.util,struct,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('payload',Path(__file__).with_name('extract-payloads.py'))
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)

def image():
    b=bytearray(4*4096);b[:8]=b'ANDROID!'
    for off,val in [(8,4),(16,4),(36,4096),(40,2),(1644,1660),(1648,4)]:struct.pack_into('<I',b,off,val)
    b[64:68]=b'a=b\0';b[608:613]=b' c=d\0'
    b[4096:4100]=b'KERN';b[8192:8196]=b'INIT';b[12288:12292]=b'DTB!'
    return b

class PayloadBounds(unittest.TestCase):
    def test_components_and_extra_command_line(self):
        x=p.extract(image())
        self.assertEqual(x,{'kernel':b'KERN','initrd':b'INIT','dtb':b'DTB!','cmdline.txt':b'a=b c=d\n'})
    def test_truncated_dtb_rejected(self):
        with self.assertRaises(ValueError):p.extract(image()[:12290])
    def test_unsupported_version_rejected(self):
        b=image();struct.pack_into('<I',b,40,4)
        with self.assertRaises(ValueError):p.extract(b)
    def test_non_power_of_two_page_rejected(self):
        b=image();struct.pack_into('<I',b,36,3000)
        with self.assertRaises(ValueError):p.extract(b)
    def test_second_stage_rejected(self):
        b=image();struct.pack_into('<I',b,24,100)
        with self.assertRaises(ValueError):p.extract(b)
    def test_missing_dtb_rejected(self):
        b=image();struct.pack_into('<I',b,1648,0)
        with self.assertRaises(ValueError):p.extract(b)
    def test_recovery_offset_inconsistency_rejected(self):
        b=image();struct.pack_into('<I',b,1632,4);struct.pack_into('<Q',b,1636,50)
        with self.assertRaises(ValueError):p.extract(b)
if __name__=='__main__':unittest.main()
