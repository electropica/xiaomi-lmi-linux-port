/* SPDX-License-Identifier: MIT
 * Native PPM-to-PipeWire diagnostic. Reads an explicitly supplied PPM path.
 * Does not start camera acquisition or open any microphone.
 * Uses the public PipeWire stream API; terminates after 30 seconds.
 */
#include <stdio.h>
#include <signal.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <string.h>
#include <spa/param/video/format-utils.h>
#include <pipewire/pipewire.h>

struct app {
    struct pw_main_loop *loop;
    struct pw_context *context;
    struct pw_core *core;
    struct pw_stream *stream;
    struct spa_hook listener;
    struct spa_source *tick;
    struct spa_video_info_raw format;
    unsigned frames;
    const char *input;
    unsigned char *rgb;
    struct timespec last_stamp;
    ino_t last_inode;
    bool fresh;
    double first_frame,last_frame,age_sum,age_max;
};
static void quit(void *opaque, uint64_t expirations) {
    (void)expirations; struct app *a=opaque; pw_main_loop_quit(a->loop);
}
static void interrupted(void *opaque, int sig) {
    (void)sig; struct app *a=opaque; pw_main_loop_quit(a->loop);
}
static bool read_new_frame(struct app *a);
static void tick(void *opaque, uint64_t expirations) {
    (void)expirations; struct app *a=opaque;
    if(read_new_frame(a)){a->fresh=true;pw_stream_trigger_process(a->stream);}
}
static bool read_new_frame(struct app *a) {
    int fd=open(a->input,O_RDONLY|O_NOFOLLOW|O_NONBLOCK);
    if(fd<0)return false;
    struct stat st;bool valid=false;char header[16];size_t total=0;
    if(fstat(fd,&st)<0 || !S_ISREG(st.st_mode) || st.st_size!=2764816)goto done;
    if(st.st_ino==a->last_inode && st.st_mtim.tv_sec==a->last_stamp.tv_sec &&
       st.st_mtim.tv_nsec==a->last_stamp.tv_nsec)goto done;
    if(read(fd,header,sizeof(header))!=sizeof(header) || memcmp(header,"P6\n1280 720\n255\n",16))goto done;
    while(total<2764800) {
        ssize_t n=read(fd,a->rgb+total,2764800-total);
        if(n<=0)goto done;
        total+=(size_t)n;
    }
    a->last_inode=st.st_ino;a->last_stamp=st.st_mtim;valid=true;
 done:close(fd);return valid;
}
static void process(void *opaque) {
    struct app *a=opaque;if(!a->fresh)return;
    struct pw_buffer *b=pw_stream_dequeue_buffer(a->stream);
    if (!b) return;
    a->fresh=false;
    struct spa_buffer *buf=b->buffer;
    unsigned w=a->format.size.width,h=a->format.size.height,stride=w*4;
    if (!buf->n_datas || !buf->datas[0].data || !buf->datas[0].chunk ||
        !w || !h || buf->datas[0].maxsize < stride*h) {
        pw_stream_queue_buffer(a->stream,b); return;
    }
    unsigned char *p=buf->datas[0].data;
    /* Clockwise rotation: portrait (x,y) reads landscape (y,719-x). */
    for(unsigned y=0;y<h;y++) for(unsigned x=0;x<w;x++) {
        unsigned i=y*stride+x*4,source=((719-x)*1280+y)*3;
        p[i]=a->rgb[source+2];p[i+1]=a->rgb[source+1];
        p[i+2]=a->rgb[source];p[i+3]=255;
    }
    struct spa_meta_header *head=spa_buffer_find_meta_data(buf,SPA_META_Header,sizeof(*head));
    if (head) { head->pts=-1;head->flags=0;head->seq=a->frames;head->dts_offset=0; }
    buf->datas[0].chunk->offset=0;buf->datas[0].chunk->size=stride*h;
    buf->datas[0].chunk->stride=stride;buf->datas[0].chunk->flags=0;
    struct timespec now,wall;clock_gettime(CLOCK_MONOTONIC,&now);clock_gettime(CLOCK_REALTIME,&wall);
    double when=now.tv_sec+now.tv_nsec/1e9;
    double age=(wall.tv_sec-a->last_stamp.tv_sec)*1000.0+(wall.tv_nsec-a->last_stamp.tv_nsec)/1e6;
    if(!a->frames)a->first_frame=when;
    a->last_frame=when;a->age_sum+=age;if(age>a->age_max)a->age_max=age;
    b->size=1; a->frames++; pw_stream_queue_buffer(a->stream,b);
}
static void state(void *opaque, enum pw_stream_state old, enum pw_stream_state now,const char *error) {
    (void)old;struct app *a=opaque;
    fprintf(stderr,"STATE %s %s\n",pw_stream_state_as_string(now),error?error:"");
    if (now==PW_STREAM_STATE_ERROR) {pw_main_loop_quit(a->loop);return;}
    if (now==PW_STREAM_STATE_STREAMING) {
        struct timespec first={0,1},period={0,10000000};
        pw_loop_update_timer(pw_main_loop_get_loop(a->loop),a->tick,&first,&period,false);
    } else pw_loop_update_timer(pw_main_loop_get_loop(a->loop),a->tick,NULL,NULL,false);
}
static void format(void *opaque,uint32_t id,const struct spa_pod *param) {
    struct app *a=opaque;if(id!=SPA_PARAM_Format || !param)return;
    if(spa_format_video_raw_parse(param,&a->format)<0 || a->format.format!=SPA_VIDEO_FORMAT_BGRx)return;
    uint8_t storage[512];struct spa_pod_builder builder=SPA_POD_BUILDER_INIT(storage,sizeof(storage));
    const struct spa_pod *params[2];unsigned stride=a->format.size.width*4;
    params[0]=spa_pod_builder_add_object(&builder,SPA_TYPE_OBJECT_ParamBuffers,SPA_PARAM_Buffers,
        SPA_PARAM_BUFFERS_buffers,SPA_POD_CHOICE_RANGE_Int(8,2,16),
        SPA_PARAM_BUFFERS_blocks,SPA_POD_Int(1),
        SPA_PARAM_BUFFERS_size,SPA_POD_Int(stride*a->format.size.height),
        SPA_PARAM_BUFFERS_stride,SPA_POD_Int(stride));
    params[1]=spa_pod_builder_add_object(&builder,SPA_TYPE_OBJECT_ParamMeta,SPA_PARAM_Meta,
        SPA_PARAM_META_type,SPA_POD_Id(SPA_META_Header),
        SPA_PARAM_META_size,SPA_POD_Int(sizeof(struct spa_meta_header)));
    pw_stream_update_params(a->stream,params,2);
}
static const struct pw_stream_events events={PW_VERSION_STREAM_EVENTS,
    .state_changed=state,.param_changed=format,.process=process};
int main(int argc,char **argv) {
    if(argc!=2){fprintf(stderr,"Usage: native-pipewire-ppm-test INPUT.ppm\n");return 2;}
    struct app a={0};a.input=argv[1];a.rgb=malloc(2764800);
    if(!a.rgb)return 1;
    pw_init(&argc,&argv);a.loop=pw_main_loop_new(NULL);
    if(!a.loop)return 1;
    struct pw_loop *loop=pw_main_loop_get_loop(a.loop);
    pw_loop_add_signal(loop,SIGINT,interrupted,&a);pw_loop_add_signal(loop,SIGTERM,interrupted,&a);
    a.context=pw_context_new(loop,NULL,0);a.core=pw_context_connect(a.context,NULL,0);
    if(!a.core){fprintf(stderr,"No user PipeWire core\n");return 1;}
    a.tick=pw_loop_add_timer(loop,tick,&a);
    struct spa_source *expiry=pw_loop_add_timer(loop,quit,&a);
    struct timespec limit={30,0};pw_loop_update_timer(loop,expiry,&limit,NULL,false);
    a.stream=pw_stream_new(a.core,"LMI PPM diagnostic source",pw_properties_new(
        PW_KEY_MEDIA_CLASS,"Video/Source",PW_KEY_MEDIA_TYPE,"Video",
        PW_KEY_MEDIA_CATEGORY,"Capture",PW_KEY_MEDIA_ROLE,"Camera",
        PW_KEY_NODE_NAME,"lmi-camera-rear-pipewire-test",
        PW_KEY_NODE_DESCRIPTION,"LMI-PPM-diagnostic",
        "api.libcamera.location","back",
        PW_KEY_NODE_SUPPORTS_REQUEST,"1",NULL));
    pw_stream_add_listener(a.stream,&a.listener,&events,&a);
    uint8_t storage[512];struct spa_pod_builder builder=SPA_POD_BUILDER_INIT(storage,sizeof(storage));
    const struct spa_pod *param=spa_pod_builder_add_object(&builder,SPA_TYPE_OBJECT_Format,SPA_PARAM_EnumFormat,
        SPA_FORMAT_mediaType,SPA_POD_Id(SPA_MEDIA_TYPE_video),
        SPA_FORMAT_mediaSubtype,SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw),
        SPA_FORMAT_VIDEO_format,SPA_POD_Id(SPA_VIDEO_FORMAT_BGRx),
        SPA_FORMAT_VIDEO_size,SPA_POD_Rectangle(&SPA_RECTANGLE(720,1280)),
        SPA_FORMAT_VIDEO_framerate,SPA_POD_Fraction(&SPA_FRACTION(25,1)));
    int rc=pw_stream_connect(a.stream,PW_DIRECTION_OUTPUT,PW_ID_ANY,
        PW_STREAM_FLAG_DRIVER|PW_STREAM_FLAG_MAP_BUFFERS,&param,1);
    if(rc>=0)pw_main_loop_run(a.loop);
    fprintf(stderr,"UNIQUE_PPM_FRAMES %u\n",a.frames);
    if(a.frames>1 && a.last_frame>a.first_frame)
        fprintf(stderr,"PUBLICATION_FPS %.3f FILE_AGE_MEAN_MS %.3f FILE_AGE_MAX_MS %.3f\n",
                (a.frames-1)/(a.last_frame-a.first_frame),a.age_sum/a.frames,a.age_max);
    pw_stream_destroy(a.stream);pw_core_disconnect(a.core);pw_context_destroy(a.context);
    pw_main_loop_destroy(a.loop);pw_deinit();free(a.rgb);return rc<0?1:0;
}
