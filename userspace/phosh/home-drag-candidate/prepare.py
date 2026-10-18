#!/usr/bin/env python3
"""Prepare a reviewed-source candidate; never compile or modify the source tree."""
import argparse,hashlib,json,xml.etree.ElementTree as E
from pathlib import Path

VERSION='0.46.0-3+deb13u1+lmigaugewake3+homedrag1'
QUIET='f8cbde684bd1920eebcfab70c39d2adef8696498fadc5443e6d2bde37669f019'

def once(text,before,after):
    if text.count(before)!=1:raise ValueError('Source anchor is not unique: '+before[:90])
    return text.replace(before,after,1)

def prepare(source,output,ui):
    assert not output.exists()
    assert hashlib.sha256((source/'src/screen-saver-manager.c').read_bytes()).hexdigest()==QUIET
    assert (source/'debian/changelog').read_text().splitlines()[0]=='phosh (0.46.0-3+deb13u1+lmigaugewake3) UNRELEASED; urgency=medium'
    assets=Path(__file__).parent
    paths=['src/app-grid.c','src/app-grid-button.c','src/ui/app-grid.ui','data/mobi.phosh.shell.gschema.xml']
    before={p:hashlib.sha256((source/p).read_bytes()).hexdigest() for p in paths}
    expected={
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
  lmi_home_enable_target (button, g_app_info_get_id (info), -1);
  return widget;'''
    c=once(c,old,new)
    outputs={'src/app-grid-button.c':c}
    c=(source/'src/app-grid.c').read_text()
    c=once(c,'#include "favorite-list-model.h"','#include "favorite-list-model.h"\n#include "lmi-home-dnd.h"')
    c=once(c,'  GtkWidget *favs_revealer;','  GtkWidget *favs_revealer;\n  GtkWidget *lmi_home_slots;\n  GtkWidget *lmi_favorites_drawer;\n  guint lmi_drag_home_timer;')
    c=once(c,'static GtkWidget *\ncreate_favorite_launcher','#include "lmi-home-grid.inc"\n\nstatic GtkWidget *\ncreate_favorite_launcher')
    start=c.index('static void\nphosh_app_grid_init');end=c.index('static void\nphosh_app_grid_dispose',start)
    body=c[start:end];body=once(body,'  toggle_favorites_revealer (self);','  toggle_favorites_revealer (self);\n  lmi_home_setup (self);');c=c[:start]+body+c[end:]
    start=c.index('static void\nphosh_app_grid_dispose');end=c.index('static void\nphosh_app_grid_finalize',start)
    body=c[start:end];body=once(body,'  g_clear_handle_id (&priv->debounce, g_source_remove);','  g_clear_handle_id (&priv->debounce, g_source_remove);\n  g_clear_handle_id (&priv->lmi_drag_home_timer, g_source_remove);');c=c[:start]+body+c[end:]
    c=once(c,'  gtk_widget_class_bind_template_child_private (widget_class, PhoshAppGrid, favs);','  gtk_widget_class_bind_template_child_private (widget_class, PhoshAppGrid, lmi_home_slots);\n  gtk_widget_class_bind_template_child_private (widget_class, PhoshAppGrid, lmi_favorites_drawer);\n  gtk_widget_class_bind_template_child_private (widget_class, PhoshAppGrid, favs);')
    outputs['src/app-grid.c']=c
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
    E.indent(root,space='  ');outputs['src/ui/app-grid.ui']=E.tostring(root,encoding='unicode')+'\n'
    for name,target in [('lmi-home-order.h','src/lmi-home-order.h'),('lmi-home-dnd.h','src/lmi-home-dnd.h'),('home-grid.inc','src/lmi-home-grid.inc')]:outputs[target]=(assets/name).read_text()
    output.mkdir(parents=True)
    for path,text in outputs.items():
        p=output/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    metadata={'version':VERSION,'quiet_source_sha256':QUIET,'before':before,'after':{p:hashlib.sha256((output/p).read_bytes()).hexdigest() for p in outputs}}
    (output/'identity.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print('HOME_DRAG_SOURCE_PREPARED',VERSION)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--ui',type=Path,required=True);a=p.parse_args();prepare(a.source,a.output,a.ui)
