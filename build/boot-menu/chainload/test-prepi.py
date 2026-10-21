#!/usr/bin/env python3
"""Replay the actual pinned C functions against an existing FD; no firmware build."""
import argparse, hashlib, importlib.util, json, subprocess, tempfile
from pathlib import Path


def function(s, name):
    i = s.index('\n' + name + ' (')
    start = s.rfind('\n}', 0, i) + 2
    # Keep the return type and optional STATIC/EFIAPI, discard preceding comments.
    prefix = s[start:i].rsplit('*/', 1)[-1].strip()
    brace = s.index('{', i)
    depth = 1
    end = brace + 1
    while depth:
        depth += (s[end] == '{') - (s[end] == '}')
        end += 1
    return prefix + s[i:end] + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--edk2', type=Path, required=True)
    ap.add_argument('--fd', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    a = ap.parse_args()
    spec = importlib.util.spec_from_file_location('patch_prepi', Path(__file__).with_name('patch-prepi.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    raw = subprocess.check_output(['git', '-C', str(a.edk2), 'show', 'HEAD:' + m.PATH])
    patched = m.patch(raw)
    prelude = '''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#undef NULL
#include <PiPei.h>
#define ASSERT(x) ((void)0)
#define CompareGuid(a,b) (memcmp((a),(b),sizeof(EFI_GUID))==0)
#define GET_OCCUPIED_SIZE(s,a) (((s)+(a)-1)&~((a)-1))
typedef EFI_STATUS (*FFS_CHECK_SECTION_HOOK)(EFI_COMMON_SECTION_HEADER*);
static void *Seen; static UINTN SeenSize;
static EFI_STATUS FfsProcessSection(EFI_SECTION_TYPE t,FFS_CHECK_SECTION_HOOK h,EFI_COMMON_SECTION_HEADER*s,UINTN n,VOID**o){(void)t;(void)h;Seen=s;SeenSize=n;*o=s;return EFI_SUCCESS;}
'''
    main_c = '''
int main(int argc,char **argv){
  FILE*f;long n;unsigned char*b;EFI_PEI_FILE_HANDLE file=NULL;EFI_STATUS status;void*out=NULL;
  if(argc!=3)return 90;
  f=fopen(argv[1],"rb");if(!f)return 91;fseek(f,0,SEEK_END);n=ftell(f);rewind(f);
  b=malloc(n);if(!b||fread(b,1,n,f)!=(size_t)n)return 92;fclose(f);
  if(((EFI_FIRMWARE_VOLUME_HEADER*)b)->FvLength>(UINT64)n)return 93;
  status=FindFileEx(b,NULL,EFI_FV_FILETYPE_FIRMWARE_VOLUME_IMAGE,&file);
  if(!strcmp(argv[2],"old")){if(status!=EFI_NOT_FOUND||file)return 94;puts("OLD_REJECTS_REAL_LARGE_FILE");free(b);return 0;}
  if(status!=EFI_SUCCESS||!file)return 95;
  if(!IS_FFS_FILE2(file)||CalculateHeaderChecksum(file)!=0)return 96;
  if(FfsFindSectionDataWithHook(0,NULL,file,&out)!=EFI_SUCCESS)return 97;
  if(Seen!=(UINT8*)file+sizeof(EFI_FFS_FILE_HEADER2)||SeenSize!=((EFI_FFS_FILE_HEADER2*)file)->ExtendedSize-sizeof(EFI_FFS_FILE_HEADER2))return 98;
  puts("PATCHED_FINDS_REAL_LARGE_FILE_AND_CORRECT_SECTION_BOUNDARY");
  /* Normal files still traverse correctly. */
  file=NULL;if(FindFileEx(b,NULL,EFI_FV_FILETYPE_SECURITY_CORE,&file)!=EFI_SUCCESS||IS_FFS_FILE2(file))return 99;
  if(FfsFindSectionDataWithHook(0,NULL,file,&out)!=EFI_SUCCESS||Seen!=(UINT8*)file+sizeof(EFI_FFS_FILE_HEADER))return 100;
  puts("NORMAL_FILE_COMPATIBILITY_PASS");
#ifdef PATCHED
  {UINT32 hs,fs;EFI_FFS_FILE_HEADER2 h;memset(&h,0,sizeof(h));h.Attributes=FFS_ATTRIB_LARGE_FILE;
   h.ExtendedSize=0x1000001;
   if(LmiFfsFileLayout((void*)&h,24,&hs,&fs))return 101;
   if(LmiFfsFileLayout((void*)&h,0x1000000,&hs,&fs))return 102;
   h.ExtendedSize=0x100000001ULL;if(LmiFfsFileLayout((void*)&h,0x200000000ULL,&hs,&fs))return 103;
   h.ExtendedSize=0x1000001;h.Size[0]=1;if(LmiFfsFileLayout((void*)&h,0x2000000,&hs,&fs))return 104;
   h.Size[0]=0;h.ExtendedSize=0x100;if(LmiFfsFileLayout((void*)&h,0x2000000,&hs,&fs))return 105;
   h.Attributes=0;h.Size[0]=0;if(LmiFfsFileLayout((void*)&h,24,&hs,&fs))return 106;
  }
  puts("TRUNCATION_OVERFLOW_INVALID_LENGTHS_REJECTED");
#endif
  free(b);return 0;
}
'''
    results = {}
    with tempfile.TemporaryDirectory(prefix='lmi-prepi-replay-') as tmp:
        for variant, source in [('old', raw.decode()), ('patched', patched.decode())]:
            names = ['GetFileState', 'CalculateHeaderChecksum', 'FindFileEx', 'FfsFindSectionDataWithHook']
            if variant == 'patched': names.insert(0, 'LmiFfsFileLayout')
            c = Path(tmp) / (variant + '.c'); exe = Path(tmp) / variant
            c.write_text(prelude + '\n'.join(function(source, n) for n in names) + main_c)
            cmd = ['cc', '-std=c11', '-fshort-wchar', '-Wall', '-Wextra', '-Werror', '-Wno-unused-function', '-I'+str(a.edk2/'MdePkg/Include'), '-I'+str(a.edk2/'MdePkg/Include/X64'), str(c), '-o', str(exe)]
            if variant == 'patched': cmd.insert(1, '-DPATCHED')
            subprocess.run(cmd, check=True)
            results[variant] = subprocess.check_output([str(exe), str(a.fd), variant], text=True).splitlines()
    report = {'upstream_sha256': hashlib.sha256(raw).hexdigest(), 'patched_sha256': hashlib.sha256(patched).hexdigest(), 'fd_sha256': hashlib.sha256(a.fd.read_bytes()).hexdigest(), 'results': results, 'hardware_validation': False}
    a.report.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
