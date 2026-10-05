/* Experimental process-local tuning; no acquisition is started here. */
typedef unsigned int guint;
typedef struct _GValue GValue;
extern void *dlsym(void *, const char *);
extern char *getenv(const char *);
extern int strcmp(const char *, const char *);
extern const char *g_type_name_from_instance(void *);
extern void g_object_set(void *, const char *, ...);
extern void *gst_caps_from_string(const char *);
extern void gst_mini_object_unref(void *);
extern void *gst_system_clock_obtain(void);
extern void gst_pipeline_use_clock(void *, void *);
extern void gst_object_unref(void *);
typedef void *(*Create)(unsigned long, guint, const char **, const GValue *);

void *g_object_new_with_properties(unsigned long object_type, guint n,
                                                 const char **names,
                                                 const GValue *values)
{
    Create real = (Create)dlsym((void *)-1L,
                               "g_object_new_with_properties");
    if (!real) return (void *)0;
    void *element = real(object_type, n, names, values);
    const char *enabled = getenv("LMI_SNAPSHOT_TUNING");
    if (!element || !enabled || strcmp(enabled, "1")) return element;
    const char *type = g_type_name_from_instance(element);
    if (!type) return element;
    if (!strcmp(type, "GstVP8Enc")) { g_object_set(element, "target-bitrate", 4000000, "deadline", (long long)1, "threads", 2, (void *)0); } else if (!strcmp(type, "GstPulseSrc")) {
        g_object_set(element, "latency-time", (long long)50000,
                     "buffer-time", (long long)500000, (void *)0);
    } else if (!strcmp(type, "GstPipeWireSrc")) {
        g_object_set(element, "use-bufferpool", 0,
                     "do-timestamp", 1, (void *)0);
    } else if (!strcmp(type, "GstCameraBin")) {
        void *caps = gst_caps_from_string("audio/x-raw,rate=48000,channels=1");
        if (caps) {
            g_object_set(element, "audio-capture-caps", caps, (void *)0);
            gst_mini_object_unref(caps);
        }
        void *clock = gst_system_clock_obtain();
        if (clock) {
            gst_pipeline_use_clock(element, clock);
            gst_object_unref(clock);
        }
    }
    return element;
}
