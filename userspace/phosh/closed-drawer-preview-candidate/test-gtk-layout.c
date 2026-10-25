
#include <gtk/gtk.h>
#include <handy.h>
static void drain(void) {for(int i=0;i<25;i++){while(gtk_events_pending())gtk_main_iteration();g_usleep(10000);}}
static void report(GtkWidget *grid,GtkWidget *outer,GtkWidget *carousel,GtkWidget *previews,const char *state,int n) {
 int x,y;gtk_widget_translate_coordinates(grid,outer,0,0,&x,&y);
 g_print("n=%d state=%s grid_y=%d grid_h=%d outer_h=%d carousel_mapped=%d preview_h=%d\n",n,state,y,gtk_widget_get_allocated_height(grid),gtk_widget_get_allocated_height(outer),gtk_widget_get_mapped(carousel),gtk_widget_get_allocated_height(previews));
}
int main(int argc,char **argv) {
 gtk_init(&argc,&argv);hdy_init();
 for(int n=0;n<=3;n++) {
  GtkBuilder *builder=gtk_builder_new();GError *err=NULL;
  if(!gtk_builder_add_from_file(builder,argv[1],&err)){g_printerr("%s\n",err->message);return 1;}
  GtkWidget *grid=GTK_WIDGET(gtk_builder_get_object(builder,"app_grid"));
  GtkWidget *previews=GTK_WIDGET(gtk_builder_get_object(builder,"lmi_drawer_previews"));
  HdyDeck *drawer=HDY_DECK(gtk_builder_get_object(builder,"lmi_favorites_drawer"));
  GtkWidget *window=gtk_window_new(GTK_WINDOW_TOPLEVEL),*outer=gtk_box_new(GTK_ORIENTATION_VERTICAL,0),*ev=gtk_event_box_new();
  GtkWidget *carousel=hdy_carousel_new();gtk_widget_set_vexpand(carousel,TRUE);gtk_widget_set_hexpand(carousel,TRUE);
  for(int i=0;i<n;i++){GtkWidget *card=gtk_drawing_area_new();gtk_widget_set_size_request(card,210,240);gtk_widget_show(card);hdy_carousel_insert(HDY_CAROUSEL(carousel),card,-1);}
  gtk_box_pack_start(GTK_BOX(previews),carousel,TRUE,TRUE,0);
  gtk_container_add(GTK_CONTAINER(ev),grid);gtk_widget_set_vexpand(ev,TRUE);gtk_container_add(GTK_CONTAINER(outer),ev);gtk_container_add(GTK_CONTAINER(window),outer);
  GtkFlowBox *slots=GTK_FLOW_BOX(gtk_builder_get_object(builder,"lmi_home_slots")),*favs=GTK_FLOW_BOX(gtk_builder_get_object(builder,"favs")),*apps=GTK_FLOW_BOX(gtk_builder_get_object(builder,"apps"));
  gtk_flow_box_set_min_children_per_line(favs,5);gtk_flow_box_set_max_children_per_line(favs,5);
  for(int i=0;i<16;i++){GtkWidget *c=gtk_drawing_area_new();gtk_widget_set_size_request(c,60,70);gtk_flow_box_insert(slots,c,-1);}
  for(int i=0;i<5;i++){GtkWidget *c=gtk_drawing_area_new();gtk_widget_set_size_request(c,50,60);gtk_flow_box_insert(favs,c,-1);}
  for(int i=0;i<48;i++){GtkWidget *c=gtk_drawing_area_new();gtk_widget_set_size_request(c,60,84);gtk_flow_box_insert(apps,c,-1);}
  gtk_window_set_default_size(GTK_WINDOW(window),360,760);gtk_widget_show_all(window);
  gtk_widget_set_visible(carousel,n>0);hdy_deck_set_transition_duration(drawer,100);drain();report(grid,outer,carousel,previews,"closed",n);
  hdy_deck_set_visible_child_name(drawer,"applications");drain();report(grid,outer,carousel,previews,"open",n);
  hdy_deck_set_visible_child_name(drawer,"home");drain();report(grid,outer,carousel,previews,"closed-again",n);
  gtk_widget_destroy(window);g_object_unref(builder);drain();
 }
 return 0;
}
