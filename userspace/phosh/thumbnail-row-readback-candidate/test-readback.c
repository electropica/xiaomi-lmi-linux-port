#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <limits.h>
#define G_MAXUINT32 UINT32_MAX
#define DRM_FORMAT_ARGB8888 0x34325241u
struct wlr_texture { bool gles; };
struct wlr_box { int32_t x,y,width,height; };
struct wlr_texture_read_pixels_options { void *data; uint32_t format,stride,dst_x,dst_y; struct wlr_box src_box; };
static int live_allocs,calls;
static bool alloc_fail,read_fail;
static uint32_t last_stride;
static bool wlr_texture_is_gles2(struct wlr_texture *t) { return t->gles; }
static void *g_try_malloc_n(size_t n,size_t s) {
 if(alloc_fail || (s && n>SIZE_MAX/s) || n*s>2000000) return NULL;
 void *p=malloc(n*s);if(p)live_allocs++;return p;
}
static void g_free(void *p) { if(p)live_allocs--;free(p); }
static bool wlr_texture_read_pixels(struct wlr_texture *t,const struct wlr_texture_read_pixels_options *o) {
 (void)t;calls++;last_stride=o->stride;if(read_fail)return false;
 assert(o->src_box.x==0 && o->src_box.y==0);
 assert(o->stride >= (uint32_t)o->src_box.width*4);
 unsigned char *p=o->data;
 for(int y=0;y<o->src_box.height;y++)for(int x=0;x<o->src_box.width*4;x++)p[(size_t)y*o->stride+x]=(unsigned char)((y*17+x*3)%256);
 return true;
}
#include "thumbnail-readback-helper.inc"
int main(void) {
 int cases=0;struct wlr_texture gpu={true},software={false};
 int widths[]={1,2,63,64,65,127,128,129},heights[]={1,2,31};
 for(size_t wi=0;wi<sizeof(widths)/sizeof(widths[0]);wi++)for(size_t hi=0;hi<sizeof(heights)/sizeof(heights[0]);hi++)for(int pad=0;pad<=12;pad+=4) {
  int w=widths[wi],h=heights[hi];size_t stride=(size_t)w*4+pad,n=stride*h;
  unsigned char *raw=malloc(n+16),*dst=raw+8;memset(raw,0xa5,n+16);
  assert(phoc_renderer_read_thumbnail_pixels(&gpu,dst,DRM_FORMAT_ARGB8888,stride,w,h));
  assert(last_stride==(uint32_t)w*4+4);
  for(int y=0;y<h;y++) {
   for(int x=0;x<w*4;x++)assert(dst[(size_t)y*stride+x]==(unsigned char)((y*17+x*3)%256));
   for(size_t x=(size_t)w*4;x<stride;x++)assert(dst[(size_t)y*stride+x]==0xa5);
  }
  for(int i=0;i<8;i++)assert(raw[i]==0xa5 && raw[n+8+i]==0xa5);
  assert(live_allocs==0);free(raw);cases++;
 }
 unsigned char dst[128];memset(dst,0xa5,sizeof(dst));
 int before=calls;alloc_fail=true;
 assert(!phoc_renderer_read_thumbnail_pixels(&gpu,dst,DRM_FORMAT_ARGB8888,16,4,2));assert(calls==before);alloc_fail=false;
 read_fail=true;assert(!phoc_renderer_read_thumbnail_pixels(&gpu,dst,DRM_FORMAT_ARGB8888,16,4,2));assert(live_allocs==0);
 for(size_t i=0;i<sizeof(dst);i++) { assert(dst[i]==0xa5); }
 read_fail=false;
 assert(!phoc_renderer_read_thumbnail_pixels(NULL,dst,DRM_FORMAT_ARGB8888,16,4,2));
 assert(!phoc_renderer_read_thumbnail_pixels(&gpu,NULL,DRM_FORMAT_ARGB8888,16,4,2));
 assert(!phoc_renderer_read_thumbnail_pixels(&gpu,dst,DRM_FORMAT_ARGB8888,15,4,2));
 assert(!phoc_renderer_read_thumbnail_pixels(&gpu,dst,DRM_FORMAT_ARGB8888,16,0,2));
 assert(!phoc_renderer_read_thumbnail_pixels(&gpu,dst,DRM_FORMAT_ARGB8888,16,4,-1));
 assert(!phoc_renderer_read_thumbnail_pixels(&gpu,dst,DRM_FORMAT_ARGB8888,UINT32_MAX,INT32_MAX,2));
 assert(phoc_renderer_read_thumbnail_pixels(&software,dst,DRM_FORMAT_ARGB8888,20,4,2));assert(last_stride==20);
 assert(phoc_renderer_read_thumbnail_pixels(&gpu,dst,12345,20,4,2));assert(last_stride==20);
 assert(live_allocs==0);
 printf("ROW_READBACK_TEST_PASS: %d layout cases plus failure/overflow/fallback controls\n",cases);
 return 0;
}
