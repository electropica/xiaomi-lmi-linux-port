/* SPDX-License-Identifier: GPL-3.0-or-later */
#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <drm_fourcc.h>
#include <wayland-server-core.h>
#include <wlr/backend.h>
#include <wlr/backend/headless.h>
#include <wlr/render/allocator.h>
#include <wlr/render/drm_format_set.h>
#include <wlr/render/gles2.h>
#include <wlr/render/pass.h>
#include <wlr/render/wlr_renderer.h>
#include <wlr/render/wlr_texture.h>
#include <wlr/types/wlr_buffer.h>
#include <wlr/util/log.h>
int main(int argc,char **argv) {
 if(argc!=2)return 1;
 alarm(15);wlr_log_init(WLR_ERROR,NULL);
 int fd=open("/dev/dri/card0",O_RDWR|O_CLOEXEC);
 if(fd<0){perror("open render device");return 2;}
 struct wl_display *display=wl_display_create();
 struct wlr_backend *backend=wlr_headless_backend_create(wl_display_get_event_loop(display));
 struct wlr_renderer *renderer=wlr_gles2_renderer_create_with_drm_fd(fd);
 if(!backend || !renderer){fprintf(stderr,"headless/GLES renderer unavailable\n");return 3;}
 struct wlr_allocator *allocator=wlr_allocator_autocreate(backend,renderer);
 if(!allocator){fprintf(stderr,"headless allocator unavailable\n");return 4;}
 struct wlr_drm_format_set formats={0};
 wlr_drm_format_set_add(&formats,DRM_FORMAT_ARGB8888,DRM_FORMAT_MOD_LINEAR);
 const struct wlr_drm_format *fmt=wlr_drm_format_set_get(&formats,DRM_FORMAT_ARGB8888);
 int widths[]={192,210,256};
 for(int mode=0;mode<3;mode++)for(int k=0;k<3;k++) {
  int width=widths[k],height=439;size_t size=(size_t)width*height*4;
  struct wlr_buffer *buffer=wlr_allocator_create_buffer(allocator,width,height,fmt);
  if(!buffer){fprintf(stderr,"target allocation failed\n");return 5;}
  struct wlr_texture *source=NULL;
  if(mode) {
   int sw=mode==1?32:1080,sh=mode==1?64:2259;
   unsigned char *green=malloc((size_t)sw*sh*4);assert(green);
   for(size_t i=0;i<(size_t)sw*sh;i++){green[4*i]=0;green[4*i+1]=255;green[4*i+2]=0;green[4*i+3]=255;}
   source=wlr_texture_from_pixels(renderer,DRM_FORMAT_ARGB8888,sw*4,sw,sh,green);free(green);
   if(!source){fprintf(stderr,"source upload failed\n");return 6;}
  }
  struct wlr_render_pass *pass=wlr_renderer_begin_buffer_pass(renderer,buffer,NULL);
  if(!pass)return 7;
  wlr_render_pass_add_rect(pass,&(struct wlr_render_rect_options){.box={0,0,width,height},.color={1,0,0,1},.blend_mode=WLR_RENDER_BLEND_MODE_NONE});
  if(source)wlr_render_pass_add_texture(pass,&(struct wlr_render_texture_options){.texture=source,.dst_box={0,0,width,height},.blend_mode=WLR_RENDER_BLEND_MODE_NONE});
  if(!wlr_render_pass_submit(pass))return 8;
  struct wlr_texture *texture=wlr_texture_from_buffer(renderer,buffer);if(!texture)return 9;
  unsigned char *pixels=malloc(size);assert(pixels);memset(pixels,0xa5,size);
  bool ok=wlr_texture_read_pixels(texture,&(struct wlr_texture_read_pixels_options){.data=pixels,.format=DRM_FORMAT_ARGB8888,.stride=width*4,.src_box={0,0,width,height}});
  size_t bad=0;
  for(size_t i=0;i<size;i+=4)if(pixels[i]!=0 || pixels[i+1]!=(mode?255:0) || pixels[i+2]!=(mode?0:255) || pixels[i+3]!=255)bad++;
  char path[512];snprintf(path,sizeof(path),"%s/mode%d-%d.bgra",argv[1],mode,width);FILE *f=fopen(path,"wx");if(!f)return 10;assert(fwrite(pixels,1,size,f)==size);fclose(f);
  printf("{\"mode\":%d,\"width\":%d,\"height\":%d,\"read_ok\":%s,\"bad_pixels\":%zu,\"pixels\":%zu}\n",mode,width,height,ok?"true":"false",bad,size/4);fflush(stdout);
  free(pixels);wlr_texture_destroy(texture);if(source)wlr_texture_destroy(source);wlr_buffer_drop(buffer);
 }
 wlr_drm_format_set_finish(&formats);wlr_allocator_destroy(allocator);wlr_renderer_destroy(renderer);wlr_backend_destroy(backend);wl_display_destroy(display);close(fd);return 0;
}
