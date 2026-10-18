#!/usr/bin/env python3
"""Prepare a reviewed-source candidate; never compile or modify the source tree."""
import argparse,hashlib,json,xml.etree.ElementTree as E
from pathlib import Path

VERSION='0.46.0-3+deb13u1+lmigaugewake3+homedrag6'
QUIET='f8cbde684bd1920eebcfab70c39d2adef8696498fadc5443e6d2bde37669f019'

def once(text,before,after):
    if text.count(before)!=1:raise ValueError('Source anchor is not unique: '+before[:90])
    return text.replace(before,after,1)

def prepare(source,output,ui):
    assert not output.exists()
    assert hashlib.sha256((source/'src/screen-saver-manager.c').read_bytes()).hexdigest()==QUIET
    assert (source/'debian/changelog').read_text().splitlines()[0]=='phosh (0.46.0-3+deb13u1+lmigaugewake3) UNRELEASED; urgency=medium'
    assets=Path(__file__).parent
    paths=['src/home.c','src/ui/app-grid-button.ui','tests/test-app-grid-button.c','src/app-grid.c','src/app-grid-button.c','src/ui/app-grid.ui','data/mobi.phosh.shell.gschema.xml']
    before={p:hashlib.sha256((source/p).read_bytes()).hexdigest() for p in paths}
    expected={
        'src/home.c':'195850693746df310dcea46cecf1fb76f6c53fa115ccfd70323cc7036db3dabf',
        'src/ui/app-grid-button.ui':'bae4207416087217554f0586da11191cc627185c3def5680d69c8b3c3e48324d',
        'tests/test-app-grid-button.c':'5cdfad9e94095d5347f50ccf0346fea2f2b9ec87d1b3989b3dc09949364a6fc5',
        'src/app-grid.c':'6a8d619de8fb24bb9fbcd322b2dd70e283535568918b0783ba1d5432ad09198f',
        'src/app-grid-button.c':'0eeeb3371757346c86313bceb6afb8da2a61a216899aeb6fc961b8da9e399438',
        'src/ui/app-grid.ui':'abbcd12612c8ff86f8b4a1ea46c3577ab5ea3fd4615e266043a8b7661ae11fac',
        'data/mobi.phosh.shell.gschema.xml':'8986e79452c7dd2946a6d9c68073ff04e68304e76147e347c5948fdc011447cc'}
    assert before==expected,'Unreviewed Phosh source baseline'
    c=(source/'src/app-grid-button.c').read_text()
    c=once(c,'#include "favorite-list-model.h"','#include "favorite-list-model.h"\n#include "lmi-home-dnd.h"')
    old='''  return g_object_new (PHOSH_TYPE_APP_GRID_BUTTON,
                       "app-info", info,
                       NULL);'''
    new='''  GtkWidget *widget = g_object_new (PHOSH_TYPE_APP_GRID_BUTTON,
                                    "app-info", info, NULL);
  GtkWidget *button = GTK_WIDGET (gtk_widget_get_template_child (widget,
                                      PHOSH_TYPE_APP_GRID_BASE_BUTTON, "button"));

  lmi_home_enable_source (button, info);
  return widget;'''
    c=once(c,old,new)
    old='''  return g_object_new (PHOSH_TYPE_APP_GRID_BUTTON,
                       "app-info", info,
                       "mode", PHOSH_APP_GRID_BUTTON_FAVORITES,
                       NULL);'''
    new='''  GtkWidget *widget = g_object_new (PHOSH_TYPE_APP_GRID_BUTTON,
                                    "app-info", info,
                                    "mode", PHOSH_APP_GRID_BUTTON_FAVORITES, NULL);
  GtkWidget *button = GTK_WIDGET (gtk_widget_get_template_child (widget,
                                      PHOSH_TYPE_APP_GRID_BASE_BUTTON, "button"));

  lmi_home_enable_source (button, info);
  lmi_home_enable_target (button, info ? g_app_info_get_id (info) : NULL, -1);
  g_object_set_data (G_OBJECT (button), "lmi-home-origin-key", "favorites");
  lmi_home_compact_cell (widget);
  /* Five favorites fit a 360px logical screen without wrapping. */
  g_object_set (gtk_widget_get_parent (button), "natural-size", 64, "width-request", 64, NULL);
  gtk_image_set_pixel_size (GTK_IMAGE (phosh_app_grid_base_button_get_child (
                                      PHOSH_APP_GRID_BASE_BUTTON (widget))), 48);
  return widget;'''
    c=once(c,old,new)
    c=once(c,'static void\nfavorite_remove_activated','#include "lmi-home-remove.inc"\n\nstatic void\nfavorite_remove_activated')
    c=once(c,'  { .name = "favorite-remove", .activate = favorite_remove_activated },','  { .name = "home-remove", .activate = lmi_home_remove_activated },\n  { .name = "favorite-remove", .activate = favorite_remove_activated },')
    c=once(c,'  g_menu_remove_all (priv->folders);','  GAction *remove = g_action_map_lookup_action (priv->action_map, "home-remove");\n  g_simple_action_set_enabled (G_SIMPLE_ACTION (remove),\n                               g_object_get_data (G_OBJECT (self), "lmi-home-remove-slot") != NULL);\n\n  g_menu_remove_all (priv->folders);')
    c=once(c,'  phosh_favorite_list_model_add_app (NULL, priv->info);',
        '  g_autoptr (GSettings) settings = g_settings_new ("sm.puri.phosh");\n  g_auto (GStrv) favorites = g_settings_get_strv (settings, "favorites");\n\n  if (g_strv_length (favorites) >= LMI_FAVORITE_LIMIT) return;\n  phosh_favorite_list_model_add_app (NULL, priv->info);')
    c=once(c,'  g_menu_remove_all (priv->folders);',
        '  g_autoptr (GSettings) settings = g_settings_new ("sm.puri.phosh");\n  g_auto (GStrv) favorites = g_settings_get_strv (settings, "favorites");\n  GAction *add = g_action_map_lookup_action (priv->action_map, "favorite-add");\n  g_simple_action_set_enabled (G_SIMPLE_ACTION (add),\n                               !priv->is_favorite && g_strv_length (favorites) < LMI_FAVORITE_LIMIT);\n\n  g_menu_remove_all (priv->folders);')
    outputs={'src/app-grid-button.c':c}
    home=(source/'src/home.c').read_text()
    home=once(home,'  if (phosh_overview_has_running_activities (PHOSH_OVERVIEW (self->overview)) == FALSE &&\n    self->state == PHOSH_HOME_STATE_UNFOLDED', '  /* The app grid owns its icon drags; keep the edge gesture when folded. */\n  if (self->state == PHOSH_HOME_STATE_UNFOLDED')
    outputs['src/home.c']=home
    menu=(source/'src/ui/app-grid-button.ui').read_text()
    item='''      <item>
        <attribute name="label">Retirer de l’accueil</attribute>
        <attribute name="action">app-btn.home-remove</attribute>
        <attribute name="hidden-when">action-disabled</attribute>
      </item>
'''
    outputs['src/ui/app-grid-button.ui']=once(menu,'    <section id="actions"/>','    <section id="actions"/>\n    <section>\n'+item+'    </section>')
    c=(source/'src/app-grid.c').read_text()
    c=once(c,'#include "favorite-list-model.h"','#include "favorite-list-model.h"\n#include "lmi-home-dnd.h"')
    c=once(c,'  GtkWidget *favs_revealer;','  GtkWidget *favs_revealer;\n  GtkWidget *lmi_home_slots;\n  GtkWidget *lmi_favorites_drawer;')
    c=once(c,'static GtkWidget *\ncreate_favorite_launcher','#include "lmi-home-grid.inc"\n\nstatic GtkWidget *\ncreate_favorite_launcher')
    start=c.index('static void\nphosh_app_grid_init');end=c.index('static void\nphosh_app_grid_dispose',start)
    body=c[start:end];body=once(body,'  toggle_favorites_revealer (self);','  toggle_favorites_revealer (self);\n  lmi_home_setup (self);');c=c[:start]+body+c[end:]
    c=once(c,'  gtk_widget_class_bind_template_child_private (widget_class, PhoshAppGrid, favs);','  gtk_widget_class_bind_template_child_private (widget_class, PhoshAppGrid, lmi_home_slots);\n  gtk_widget_class_bind_template_child_private (widget_class, PhoshAppGrid, lmi_favorites_drawer);\n  gtk_widget_class_bind_template_child_private (widget_class, PhoshAppGrid, favs);')
    outputs['src/app-grid.c']=c
    test=(source/'tests/test-app-grid-button.c').read_text()
    anchor='  btn = phosh_app_grid_button_new (NULL);\n  g_assert_null (phosh_app_grid_button_get_app_info (\n                   PHOSH_APP_GRID_BUTTON (btn)));\n  gtk_widget_destroy (btn);'
    outputs['tests/test-app-grid-button.c']=once(test,anchor,anchor+'\n\n  btn = phosh_app_grid_button_new_favorite (NULL);\n  g_assert_null (phosh_app_grid_button_get_app_info (\n                   PHOSH_APP_GRID_BUTTON (btn)));\n  gtk_widget_destroy (btn);')
    test=outputs['tests/test-app-grid-button.c']
    test=once(test,'#include "favorite-list-model.h"','#include "favorite-list-model.h"\n#include "lmi-home-dnd.h"')
    test=once(test,'int\nmain (', (assets/'test-remove.inc').read_text()+'\n\n'+'int\nmain (')
    test=once(test,'  gtk_test_init (&argc, &argv, NULL);','  gtk_test_init (&argc, &argv, NULL);\n  g_test_add_func ("/phosh/app-grid-button/home-remove", test_phosh_home_remove);\n  g_test_add_func ("/phosh/app-grid-button/home-row-width", test_phosh_home_row_width);\n  g_test_add_func ("/phosh/app-grid-button/home-transfer", test_phosh_home_transfer);')
    outputs['tests/test-app-grid-button.c']=test
    schema=(source/'data/mobi.phosh.shell.gschema.xml').read_text()
    key='''    <key name="lmi-home-slots" type="as">
      <default>['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']</default>
      <summary>Application desktop IDs in the sixteen home shortcut slots</summary>
      <description>Empty entries preserve unused cells. Moving a shortcut does not uninstall its application.</description>
    </key>
'''
    outputs['data/mobi.phosh.shell.gschema.xml']=once(schema,'    <key name="favorites" type="as">',key+'    <key name="favorites" type="as">')
    root=E.fromstring(ui.read_text());home=next(o for o in root.iter('object') if o.get('id')=='lmi_favorites_home')
    space=home.findall('child')[0].find('object');assert space.get('class')=='GtkBox'
    space.attrib={'class':'GtkFlowBox','id':'lmi_home_slots'}
    for p in list(space):space.remove(p)
    for name,value in [('visible','1'),('hexpand','1'),('vexpand','1'),('homogeneous','1'),('min-children-per-line','4'),('max-children-per-line','4'),('selection-mode','none'),('activate-on-single-click','0'),('column-spacing','6'),('row-spacing','8')]:E.SubElement(space,'property',name=name).text=value
    favs=next(o for o in root.iter('object') if o.get('id')=='favs')
    for prop in favs.findall('property'):
        if prop.get('name')=='max-children-per-line':prop.text='5'
    E.indent(root,space='  ');outputs['src/ui/app-grid.ui']=E.tostring(root,encoding='unicode')+'\n'
    for name,target in [('lmi-home-order.h','src/lmi-home-order.h'),('lmi-home-dnd.h','src/lmi-home-dnd.h'),('home-grid.inc','src/lmi-home-grid.inc'),('home-remove.inc','src/lmi-home-remove.inc')]:outputs[target]=(assets/name).read_text()
    output.mkdir(parents=True)
    for path,text in outputs.items():
        p=output/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    metadata={'version':VERSION,'quiet_source_sha256':QUIET,'before':before,'after':{p:hashlib.sha256((output/p).read_bytes()).hexdigest() for p in outputs}}
    (output/'identity.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print('HOME_DRAG_SOURCE_PREPARED',VERSION)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--ui',type=Path,required=True);a=p.parse_args();prepare(a.source,a.output,a.ui)
