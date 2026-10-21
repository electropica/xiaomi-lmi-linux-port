/* SPDX-License-Identifier: MIT */
#include <stdio.h>
#include <stdlib.h>
#include "bundle-format.h"
static void put64(unsigned char*p,uint64_t v){unsigned i;for(i=0;i<8;i++)p[i]=(unsigned char)(v>>(i*8));}
static void valid(unsigned char*b,size_t n){
 unsigned i;memset(b,0,n);memcpy(b,"LMIBNDL1",8);b[8]=1;b[12]=9;put64(b+16,n);
 for(i=0;i<9;i++){
  unsigned char*r=b+32+i*56;snprintf((char*)r,32,"item%u",i);put64(r+32,4096+i*4096);put64(r+40,1);
 }
}
#define CHECK(c) do{if(!(c)){fprintf(stderr,"failed line %d\n",__LINE__);return 1;}}while(0)
int main(int argc,char**argv){
 const void*data=NULL;size_t size=0;uint32_t crc=0;unsigned i;
 size_t n=10*4096;unsigned char*b=malloc(n);CHECK(b);
 valid(b,n);CHECK(!lmi_bundle_find(b,n,"item8",&data,&size,&crc));CHECK(size==1);
 CHECK(lmi_bundle_find(b,n,"missing",&data,&size,&crc));
 CHECK(lmi_bundle_find(b,100,"item0",&data,&size,&crc));
 b[0]='X';CHECK(lmi_bundle_find(b,n,"item0",&data,&size,&crc));valid(b,n);
 put64(b+32+32,UINT64_MAX);CHECK(lmi_bundle_find(b,n,"item0",&data,&size,&crc));valid(b,n);
 put64(b+32+40,UINT64_MAX);CHECK(lmi_bundle_find(b,n,"item0",&data,&size,&crc));valid(b,n);
 memset(b+32,'x',32);CHECK(lmi_bundle_find(b,n,"item0",&data,&size,&crc));valid(b,n);
 memcpy(b+32+56,"item0",6);CHECK(lmi_bundle_find(b,n,"item0",&data,&size,&crc));valid(b,n);
 put64(b+32+56+32,4096);CHECK(lmi_bundle_find(b,n,"item0",&data,&size,&crc));
 free(b);
 if(argc==2){
  FILE*f=fopen(argv[1],"rb");long len;CHECK(f);CHECK(!fseek(f,0,SEEK_END));len=ftell(f);CHECK(len>0&&len<=128*1024*1024);
  rewind(f);b=malloc((size_t)len);CHECK(b);CHECK(fread(b,1,(size_t)len,f)==(size_t)len);fclose(f);
  for(i=0;i<9;i++){char name[32];memcpy(name,b+32+i*56,32);name[31]=0;CHECK(!lmi_bundle_find(b,(size_t)len,name,&data,&size,&crc));}
  free(b);
 }
 puts("BUNDLE_C_BOUNDS_AND_LAYOUT_PASS");return 0;
}
