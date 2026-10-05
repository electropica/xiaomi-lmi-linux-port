#!/usr/bin/python3
"""Opt-in rear snapshot UI; privileged work belongs to one fixed service."""
import os
from pathlib import Path
import subprocess
import sys
import threading
from datetime import datetime
import gi
os.environ.setdefault('GSK_RENDERER','cairo')
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gio, GdkPixbuf

class Camera(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='org.mobian.lmi.Camera', flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.busy=False
        self.photo=None
        self.once='--capture-once' in sys.argv
        self.capture_exit=1
        self.connect('activate',self.activate)

    def activate(self,app):
        if hasattr(self,'window'):
            self.window.present()
            return
        self.window=Gtk.ApplicationWindow(application=self,title='Appareil photo lmi')
        self.window.set_default_size(360,640)
        header=Gtk.HeaderBar()
        header.set_title_widget(Gtk.Label(label='Appareil photo lmi'))
        self.window.set_titlebar(header)
        box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12)
        for side in ['top','bottom','start','end']:
            getattr(box,'set_margin_'+side)(12)
        self.window.set_child(box)
        title=Gtk.Label(label='Caméra arrière')
        title.add_css_class('title-2')
        box.append(title)
        self.picture=Gtk.Picture()
        self.picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        self.picture.set_can_shrink(True)
        self.picture.set_vexpand(True)
        self.picture.set_size_request(1,180)
        box.append(self.picture)
        self.status=Gtk.Label(label='Oriente le téléphone, puis prends une photo.')
        self.status.set_wrap(True)
        box.append(self.status)
        self.capture=Gtk.Button(label='Prendre une photo')
        self.capture.add_css_class('suggested-action')
        self.capture.set_size_request(-1,52)
        self.capture.connect('clicked',self.take_photo)
        box.append(self.capture)
        self.open=Gtk.Button(label='Ouvrir la photo')
        self.open.set_sensitive(False)
        self.open.set_size_request(-1,44)
        self.open.connect('clicked',self.open_photo)
        box.append(self.open)
        folder=self.photo_folder()
        previous=sorted(folder.glob('LMI-*.png')) if folder.is_dir() else []
        if previous:
            self.photo=str(previous[-1])
            self.picture.set_filename(self.photo)
            self.open.set_sensitive(True)
            self.status.set_text('Dernière photo — prête pour une nouvelle prise.')
        self.window.present()
        if self.once:
            GLib.timeout_add(500,lambda: (self.take_photo(None),False)[1])

    def take_photo(self,button):
        if self.busy:return
        self.busy=True
        self.capture.set_sensitive(False)
        self.open.set_sensitive(False)
        self.status.set_text('Prise de vue… attends quelques secondes.')
        threading.Thread(target=self.capture_worker,daemon=True).start()

    def capture_worker(self):
        try:
            result=subprocess.run(['/usr/bin/systemctl','--no-ask-password','start','lmi-camera-capture.service'],capture_output=True,text=True,timeout=55)
            if result.returncode:
                raise RuntimeError('La capture a échoué. Le téléphone et la caméra doivent être disponibles.')
            source=Path('/run/lmi-camera/latest.ppm')
            pixbuf=GdkPixbuf.Pixbuf.new_from_file(str(source))
            if (pixbuf.get_width(),pixbuf.get_height())!=(1280,720):
                raise RuntimeError('Format de photo inattendu.')
            folder=self.photo_folder()
            folder.mkdir(mode=0o700,parents=True,exist_ok=True)
            name='LMI-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.png'
            destination=folder/name
            ok,data=pixbuf.save_to_bufferv('png',[],[])
            if not ok:raise RuntimeError('Impossible de préparer la photo.')
            fd=os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'wb') as stream:
                stream.write(data)
            GLib.idle_add(self.finished,str(destination),None)
        except Exception as error:
            GLib.idle_add(self.finished,None,str(error))

    def photo_folder(self):
        pictures=GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES)
        return Path(pictures or str(Path.home()/'Pictures'))/'Camera'

    def finished(self,path,error):
        self.busy=False
        self.capture.set_sensitive(True)
        if path:
            self.capture_exit=0
            self.photo=path
            self.picture.set_filename(path)
            self.open.set_sensitive(True)
            self.status.set_text('Photo enregistrée dans Images / Camera.')
            print('PHOTO_SAVED '+path,flush=True)
        else:
            self.status.set_text(error)
            print('PHOTO_FAILED '+error,flush=True)
        if self.once:GLib.timeout_add(1000,lambda:(self.quit(),False)[1])
        return False

    def open_photo(self,button):
        if self.photo:
            try:
                self.viewer=Gio.Subprocess.new(['/usr/local/bin/lmi-photos',self.photo],Gio.SubprocessFlags.NONE)
            except GLib.Error:
                self.status.set_text('Impossible d’ouvrir Photos. La photo reste dans Images / Camera.')

app=Camera()
result=app.run([sys.argv[0]])
raise SystemExit(app.capture_exit if app.once else result)
