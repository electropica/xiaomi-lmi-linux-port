/* SPDX-License-Identifier: MIT
 * Remove only known compatibility-DT variant tokens when a later real value
 * for the same key exists. Preserve all unrelated bytes, including AVB policy.
 */
#include <stddef.h>
#include <string.h>
static int lmi_variant_args(char *args,size_t capacity){
    static const char *keys[]={"androidboot.hwc=","androidboot.hwversion=","androidboot.product.hardware.sku="};
    static const char *legacy[]={"androidboot.hwc=CN","androidboot.hwversion=3.9.0","androidboot.product.hardware.sku=pro"};
    size_t offsets[3]={0},lengths[3]={0},counts[3]={0},n,pos,i;
    if(!args||!memchr(args,0,capacity))return -1;
    n=strlen(args);
    for(pos=0;pos<n;){
        size_t begin,end;
        while(pos<n&&(args[pos]==' '||args[pos]=='\t'))pos++;
        begin=pos;while(pos<n&&args[pos]!=' '&&args[pos]!='\t')pos++;end=pos;
        for(i=0;i<3;i++){
            size_t k=strlen(keys[i]);
            if(end-begin<k||memcmp(args+begin,keys[i],k))continue;
            if(end-begin==k)return -1;
            if(!counts[i]){offsets[i]=begin;lengths[i]=end-begin;}
            counts[i]++;
        }
    }
    /* Validate every edit first: unknown ambiguity leaves the buffer intact. */
    for(i=0;i<3;i++)if(counts[i]>1){
        if(counts[i]!=2||lengths[i]!=strlen(legacy[i])||
           memcmp(args+offsets[i],legacy[i],lengths[i]))return -1;
    }
    /* Walk backwards so the offsets of remaining edits remain valid. */
    for(;;){
        size_t chosen=3;
        for(i=0;i<3;i++)if(counts[i]==2&&(chosen==3||offsets[i]>offsets[chosen]))chosen=i;
        if(chosen==3)break;
        pos=offsets[chosen];i=pos+lengths[chosen];
        if(i<n&&(args[i]==' '||args[i]=='\t'))i++;
        memmove(args+pos,args+i,n-i+1);n-=i-pos;counts[chosen]=0;
    }
    return 0;
}
