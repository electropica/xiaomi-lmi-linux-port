
#include <gtk/gtk.h>
typedef struct { GtkBox parent_instance; } LmiProbe;
typedef struct { GtkBoxClass parent_class; } LmiProbeClass;
static gboolean bind_target = FALSE;
G_DEFINE_TYPE (LmiProbe, lmi_probe, GTK_TYPE_BOX)
static void lmi_probe_class_init (LmiProbeClass *klass) {
 const char *ui="<interface><template class='LmiProbe' parent='GtkBox'><property name='orientation'>vertical</property><child><object class='GtkBox' id='target'><property name='visible'>1</property></object></child></template></interface>";
 GBytes *bytes=g_bytes_new_static(ui,strlen(ui));
 gtk_widget_class_set_template(GTK_WIDGET_CLASS(klass),bytes);g_bytes_unref(bytes);
 if (bind_target) gtk_widget_class_bind_template_child_full(GTK_WIDGET_CLASS(klass),"target",FALSE,0);
}
static void lmi_probe_init (LmiProbe *self) { gtk_widget_init_template(GTK_WIDGET(self)); }
int main (int argc,char **argv) {
 gtk_init(&argc,&argv);bind_target=argc>1 && strcmp(argv[1],"bound")==0;
 GtkWidget *probe=g_object_new(lmi_probe_get_type(),NULL);
 GObject *target=gtk_widget_get_template_child(probe,lmi_probe_get_type(),"target");
 GtkWidget *box=gtk_box_new(GTK_ORIENTATION_VERTICAL,0),*child=gtk_box_new(GTK_ORIENTATION_VERTICAL,0);
 gtk_widget_set_vexpand(child,TRUE);gtk_box_pack_start(GTK_BOX(box),child,FALSE,TRUE,0);
 g_print("bound=%d lookup_found=%d vexpand_after_pack_false=%d\n",bind_target,target!=NULL,gtk_widget_get_vexpand(child));
 return 0;
}
