#!/usr/bin/env python3
"""Host C/libfdt test on pinned DTBs and the board-matched Android overlay."""
from pathlib import Path
import argparse,ctypes,importlib.util,struct,subprocess,tempfile,json,gzip,hashlib

def properties(f):
    _,size,so,st,_,_,_,_,ss,ds=struct.unpack_from('>10I',f)
    p=so;stack=[];out={}
    while p<so+ds:
        tag=struct.unpack_from('>I',f,p)[0];p+=4
        if tag==1:
            end=f.index(0,p);stack.append(f[p:end].decode());p=(end+4)&~3
        elif tag==2:stack.pop()
        elif tag==3:
            length,name=struct.unpack_from('>II',f,p);p+=8;value=f[p:p+length];p=(p+length+3)&~3
            start=st+name;end=f.index(0,start);key=f[start:end].decode()
            out['/'.join(stack)+'/'+key]=value
        elif tag==9:break
        elif tag!=4:raise ValueError(tag)
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--android',type=Path,required=True);ap.add_argument('--dtbo',type=Path,required=True);ap.add_argument('--libfdt',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);a=ap.parse_args()
    here=Path(__file__).resolve().parent
    s=importlib.util.spec_from_file_location('extract',here.parent/'extract-payloads.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    raw=a.android.read_bytes();assert hashlib.sha256(raw).hexdigest()=='9d7dd4823860f7ad73c82542669620b2cee1ca466789958175be63bb77e85411'
    parts=m.extract(raw);dtbo=a.dtbo.read_bytes();assert hashlib.sha256(dtbo).hexdigest()=='45f0989700c68afcd817a6a4569ba67225cf128e3eedd35a658bad384632eec4'
    _,_,_,esz,count,off,_,_=struct.unpack_from('>8I',dtbo);matches=[]
    for i in range(count):
        size,pos=struct.unpack_from('>II',dtbo,off+i*esz);f=dtbo[pos:pos+size]
        if properties(f).get('/qcom,board-id')==struct.pack('>II',37,0):matches.append((i,f))
    assert len(matches)==1
    lib=ctypes.CDLL(str(a.libfdt),mode=ctypes.RTLD_GLOBAL)
    for name,args in [('fdt_open_into',[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int]),('fdt_overlay_apply',[ctypes.c_void_p,ctypes.c_void_p]),('fdt_path_offset',[ctypes.c_void_p,ctypes.c_char_p]),('fdt_setprop',[ctypes.c_void_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_void_p,ctypes.c_int])]:
        getattr(lib,name).argtypes=args;getattr(lib,name).restype=ctypes.c_int
    c='''#include <stdint.h>
#include <stddef.h>
#include <string.h>
#define FDT_ERR_NOTFOUND 1
#define tlog_error(...) ((void)0)
#define tlog_notice(...) ((void)0)
typedef struct {char tag[256];} linux_config;
typedef struct {void*address;size_t size;} file_info;
typedef struct {linux_config*config;file_info dtb;} linux_boot;
extern int fdt_check_header(const void*);
extern int fdt_path_offset(const void*,const char*);
extern int fdt_subnode_offset(const void*,int,const char*);
extern const void*fdt_getprop(const void*,int,const char*,int*);
extern int fdt_del_node(void*,int);
extern const char*fdt_strerror(int);
static unsigned fdt_totalsize(const void*p){const unsigned char*b=p;return (unsigned)b[4]<<24|(unsigned)b[5]<<16|(unsigned)b[6]<<8|b[7];}
'''+(here/'lmi-android-fstab.h').read_text()+'''
int test_fix(void*p,const char*tag){linux_config cfg={0};linux_boot lb={.config=&cfg,.dtb={.address=p}};strncpy(cfg.tag,tag,255);return linux_boot_lmi_android_fstab(&lb);}
'''
    results=[]
    with tempfile.TemporaryDirectory(prefix='lmi-android-fstab-') as tmp:
        src=Path(tmp)/'test.c';so=Path(tmp)/'test.so';src.write_text(c)
        subprocess.run(['cc','-std=c11','-shared','-fPIC','-Wall','-Wextra','-Werror',str(src),str(a.libfdt),'-o',str(so)],check=True)
        test=ctypes.CDLL(str(so));test.test_fix.argtypes=[ctypes.c_void_p,ctypes.c_char_p];test.test_fix.restype=ctypes.c_int
        data=parts['dtb'];pos=0
        while pos+40<=len(data) and data[pos:pos+4]==b'\xd0\x0d\xfe\xed':
            size=struct.unpack_from('>I',data,pos+4)[0];base=ctypes.create_string_buffer(data[pos:pos+size]);buf=ctypes.create_string_buffer(4*1024*1024)
            assert lib.fdt_open_into(base,buf,len(buf))==0
            overlay=ctypes.create_string_buffer(matches[0][1]);assert lib.fdt_overlay_apply(buf,overlay)==0
            before=properties(buf.raw);original=buf.raw
            assert test.test_fix(buf,b'mobian')==-1 and buf.raw==original
            vendor=lib.fdt_path_offset(buf,b'/firmware/android/fstab/vendor');assert vendor>=0
            wrong=b'/unexpected/vendor\0';assert lib.fdt_setprop(buf,vendor,b'dev',wrong,len(wrong))==0
            malformed=buf.raw;assert test.test_fix(buf,b'android')==-1 and buf.raw==malformed
            ctypes.memmove(buf,original,len(original))
            assert test.test_fix(buf,b'android')==0
            after=properties(buf.raw)
            expected={k:v for k,v in before.items() if not k.startswith('/firmware/android/fstab/')}
            assert after==expected,'An unrelated DT property changed'
            assert test.test_fix(buf,b'android')==0
            results.append({'base_offset':pos,'board_matched_overlay':matches[0][0],'other_properties_unchanged':True,'unexpected_path_and_other_os_rejected':True})
            pos+=size
            while pos<len(data) and data[pos]==0:pos+=1
    assert len(results)==3
    ram=gzip.decompress(parts['initrd']);pos=0;fstab=None
    while pos+110<=len(ram):
        h=ram[pos:pos+110];assert h[:6] in [b'070701',b'070702'];fields=[int(h[i:i+8],16) for i in range(6,110,8)];length=fields[6];ns=fields[11]
        name=ram[pos+110:pos+110+ns-1].decode();start=(pos+110+ns+3)&~3
        if name=='TRAILER!!!':break
        if name=='system/etc/fstab.qcom':fstab=ram[start:start+length].decode()
        pos=(start+length+3)&~3
    assert fstab
    for part,fs in [('system','ext4'),('vendor','erofs')]:
        row=next(line.split() for line in fstab.splitlines() if line.split() and line.split()[0]==part)
        assert row[2]==fs and {'logical','first_stage_mount'}<=set(row[-1].split(','))
    result={'actual_c_fix_on_real_dtb_and_overlay':results,'pinned_ramdisk_has_logical_system_vendor':True,'hardware_validation':False}
    a.report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
