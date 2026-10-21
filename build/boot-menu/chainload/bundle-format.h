/* SPDX-License-Identifier: MIT
 * Bounded RAM bundle parser shared by firmware and host validation.
 */
#ifndef LMI_BUNDLE_FORMAT_H
#define LMI_BUNDLE_FORMAT_H
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#define LMI_BUNDLE_HEADER 4096u
#define LMI_BUNDLE_ROWS 5u
#define LMI_BUNDLE_ROW_SIZE 56u
static uint64_t lmi_u64(const unsigned char*p){
    uint64_t v=0;unsigned i;for(i=0;i<8;i++)v|=(uint64_t)p[i]<<(i*8);return v;
}
static uint32_t lmi_u32(const unsigned char*p){
    return (uint32_t)lmi_u64((const unsigned char[8]){p[0],p[1],p[2],p[3],0,0,0,0});
}
static int lmi_bundle_find(const void*buffer,size_t length,const char*name,
                          const void**data,size_t*size,uint32_t*crc){
    const unsigned char*b=buffer;uint64_t previous=LMI_BUNDLE_HEADER;
    unsigned i,j;int found=0;
    if(!buffer||!data||!size||!crc||length<LMI_BUNDLE_HEADER||length>128u*1024u*1024u)return -1;
    if(memcmp(b,"LMIBNDL1",8)||lmi_u32(b+8)!=1||lmi_u32(b+12)!=LMI_BUNDLE_ROWS||lmi_u64(b+16)!=length)return -1;
    for(i=0;i<LMI_BUNDLE_ROWS;i++){
        const unsigned char*r=b+32+i*LMI_BUNDLE_ROW_SIZE;
        uint64_t off=lmi_u64(r+32),len=lmi_u64(r+40);
        if(!memchr(r,0,32)||!r[0]||off<previous||off%4096||!len||off>length||len>length-off)return -1;
        for(j=0;j<i;j++)if(!strcmp((const char*)r,(const char*)(b+32+j*LMI_BUNDLE_ROW_SIZE)))return -1;
        previous=off+len;
        if(!strcmp((const char*)r,name)){
            if(found)return -1;
            *data=b+(size_t)off;*size=(size_t)len;*crc=lmi_u32(r+48);found=1;
        }
    }
    return found?0:-1;
}
#endif
