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
#include <GLES2/gl2.h>
#include <GLES2/gl2ext.h>
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
 for(int mode=0;mode<4;mode++)for(int k=0;k<3;k++) {
  int width=widths[k],height=439;size_t size=(size_t)width*height*4;
  struct wlr_buffer *buffer=wlr_allocator_create_buffer(allocator,width,height,fmt);
  if(!buffer){fprintf(stderr,"target allocation failed\n");return 5;}
  struct wlr_texture *source=NULL;
  if(mode && mode<3) {
   int sw=mode==1?32:1080,sh=mode==1?64:2259;
   unsigned char *green=malloc((size_t)sw*sh*4);assert(green);
   for(size_t i=0;i<(size_t)sw*sh;i++){green[4*i]=0;green[4*i+1]=255;green[4*i+2]=0;green[4*i+3]=255;}
   source=wlr_texture_from_pixels(renderer,DRM_FORMAT_ARGB8888,sw*4,sw,sh,green);free(green);
   if(!source){fprintf(stderr,"source upload failed\n");return 6;}
  }
  struct wlr_render_pass *pass=wlr_renderer_begin_buffer_pass(renderer,buffer,NULL);
  if(!pass)return 7;
  GLint original_fbo;glGetIntegerv(GL_FRAMEBUFFER_BINDING,&original_fbo);
  GLuint internal_texture,internal_fbo;
  glGenTextures(1,&internal_texture);glBindTexture(GL_TEXTURE_2D,internal_texture);
  glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);
  glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,width,height,0,GL_RGBA,GL_UNSIGNED_BYTE,NULL);
  glGenFramebuffers(1,&internal_fbo);glBindFramebuffer(GL_FRAMEBUFFER,internal_fbo);glFramebufferTexture2D(GL_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,internal_texture,0);
  assert(glCheckFramebufferStatus(GL_FRAMEBUFFER)==GL_FRAMEBUFFER_COMPLETE);

  wlr_render_pass_add_rect(pass,&(struct wlr_render_rect_options){.box={0,0,width,height},.color={1,0,0,1},.blend_mode=WLR_RENDER_BLEND_MODE_NONE});
  if(source)wlr_render_pass_add_texture(pass,&(struct wlr_render_texture_options){.texture=source,.dst_box={0,0,width,height},.blend_mode=WLR_RENDER_BLEND_MODE_NONE});
  if(mode==3) {
   wlr_render_pass_add_rect(pass,&(struct wlr_render_rect_options){.box={width/2,0,width-width/2,height/2},.color={0,1,0,1},.blend_mode=WLR_RENDER_BLEND_MODE_NONE});
   wlr_render_pass_add_rect(pass,&(struct wlr_render_rect_options){.box={0,height/2,width/2,height-height/2},.color={0,0,1,1},.blend_mode=WLR_RENDER_BLEND_MODE_NONE});
   wlr_render_pass_add_rect(pass,&(struct wlr_render_rect_options){.box={width/2,height/2,width-width/2,height-height/2},.color={1,1,1,1},.blend_mode=WLR_RENDER_BLEND_MODE_NONE});
  }
  unsigned char *pixels=malloc(size);assert(pixels);memset(pixels,0xa5,size);
  glPixelStorei(GL_PACK_ALIGNMENT,1);glReadPixels(0,0,width,height,GL_BGRA_EXT,GL_UNSIGNED_BYTE,pixels);
  bool ok=glGetError()==GL_NO_ERROR;
  glBindFramebuffer(GL_FRAMEBUFFER,(GLuint)original_fbo);glDeleteFramebuffers(1,&internal_fbo);glDeleteTextures(1,&internal_texture);
  if(!wlr_render_pass_submit(pass))return 8;
  size_t bad=0;
  for(int y=0;y<height;y++)for(int x=0;x<width;x++) {
   size_t i=((size_t)y*width+x)*4;
   int red=mode?0:255,green=mode?255:0,blue=0;
   if(mode==3){bool bottom=y>=height/2,right=x>=width/2;red=(!bottom&&!right)||(bottom&&right)?255:0;green=right?255:0;blue=bottom?255:0;}
   if(pixels[i]!=blue || pixels[i+1]!=green || pixels[i+2]!=red || pixels[i+3]!=255)bad++;
  }
  char path[512];snprintf(path,sizeof(path),"%s/mode%d-%d.bgra",argv[1],mode,width);FILE *f=fopen(path,"wx");if(!f)return 10;assert(fwrite(pixels,1,size,f)==size);fclose(f);
  printf("{\"mode\":%d,\"width\":%d,\"height\":%d,\"read_ok\":%s,\"bad_pixels\":%zu,\"pixels\":%zu}\n",mode,width,height,ok?"true":"false",bad,size/4);fflush(stdout);
  free(pixels);if(source)wlr_texture_destroy(source);wlr_buffer_drop(buffer);
 }
 wlr_drm_format_set_finish(&formats);wlr_allocator_destroy(allocator);wlr_renderer_destroy(renderer);wlr_backend_destroy(backend);wl_display_destroy(display);close(fd);return 0;
}
