#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "camera-yuv-neon.h"
static unsigned char clamp(int x){return x<0?0:x>255?255:x;}
static void scalar(const uint8_t *y,const uint8_t *u,const uint8_t *v,unsigned step,unsigned w,uint8_t *out){
    for(unsigned x=0;x<w;x++) {
        int l=y[x]-16,cb=u[(x/2)*step]-128,cr=v[(x/2)*step]-128;
        out[3*x]=clamp((298*l+409*cr+128)>>8);
        out[3*x+1]=clamp((298*l-100*cb-208*cr+128)>>8);
        out[3*x+2]=clamp((298*l+516*cb+128)>>8);
    }
}
int main(void) {
    uint8_t y[1280],u[1280],v[1280],a[3840],b[3840];
    unsigned rng=20261006,cases=0;
    for(unsigned step=1;step<=2;step++) for(unsigned c=0;c<100;c++) {
        for(unsigned x=0;x<1280;x++) {
            rng=rng*1664525+1013904223;y[x]=rng>>24;
            rng=rng*1664525+1013904223;u[x]=rng>>24;
            rng=rng*1664525+1013904223;v[x]=rng>>24;
        }
        scalar(y,u,v,step,1280,a);lmi_yuv_row_neon(y,u,v,step,1280,b);
        if(memcmp(a,b,sizeof(a)))return 1;
        cases++;
    }
    unsigned levels[]={0,16,128,235,255};
    for(unsigned ly=0;ly<5;ly++)for(unsigned lu=0;lu<5;lu++)for(unsigned lv=0;lv<5;lv++) {
        memset(y,levels[ly],sizeof(y));memset(u,levels[lu],sizeof(u));memset(v,levels[lv],sizeof(v));
        scalar(y,u,v,1,1280,a);lmi_yuv_row_neon(y,u,v,1,1280,b);
        if(memcmp(a,b,sizeof(a)))return 1;
        cases++;
    }
    /* Minimal plane allocations: step 2 needs seven accessible bytes for four samples. */
    uint8_t *tiny_u=malloc(7),*tiny_v=malloc(7);
    if(!tiny_u || !tiny_v)return 2;
    memset(tiny_u,128,7);memset(tiny_v,128,7);
    scalar(y,tiny_u,tiny_v,2,8,a);lmi_yuv_row_neon(y,tiny_u,tiny_v,2,8,b);
    if(memcmp(a,b,24))return 1;
    free(tiny_u);free(tiny_v);
    printf("NEON_SCALAR_EXACT_MATCH cases=%u plus_minimal_plane_case\n",cases);
    return 0;
}
