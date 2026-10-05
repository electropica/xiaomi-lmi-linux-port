#!/usr/bin/python3
"""Opt-in rear snapshot UI; privileged work belongs to one fixed service."""
import json,os,time
from pathlib import Path
import subprocess
import sys
import threading
from datetime import datetime
import gi
os.environ.setdefault('GSK_RENDERER','cairo')
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gio, GdkPixbuf, Gdk

class Camera(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='org.mobian.lmi.Camera', flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.busy=False
        self.photo=None
        self.live_pixbuf=None
        self.live_stamp=None
        self.live_running=False
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
        self.preview_button=Gtk.Button(label='Relancer l’aperçu')
        self.preview_button.connect('clicked',self.start_preview)
        box.append(self.preview_button)
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
        self.window.connect('close-request',self.close_camera)
        if not self.once:
            GLib.timeout_add(250,self.poll_preview)
            self.start_preview(None)
        if self.once:
            GLib.timeout_add(500,lambda: (self.take_photo(None),False)[1])

    def start_preview(self,button):
        if self.live_running:return
        self.live_pixbuf=None;self.live_stamp=None;self.live_running=True
        self.live_started=time.time_ns()
        self.capture.set_sensitive(False);self.preview_button.set_sensitive(False)
        self.status.set_text('Démarrage de la caméra arrière…')
        threading.Thread(target=self.launch_preview,daemon=True).start()

    def launch_preview(self):
        try:
            result=subprocess.run(['/usr/bin/systemctl','--no-ask-password','start','lmi-camera-preview.service'],capture_output=True,timeout=5)
            if result.returncode:raise RuntimeError('Impossible de démarrer l’aperçu.')
        except Exception as error:GLib.idle_add(self.preview_failed,str(error))

    def preview_failed(self,error):
        self.live_running=False;self.preview_button.set_sensitive(True)
        self.capture.set_sensitive(False);self.status.set_text(error)
        return False

    def poll_preview(self):
        if not self.live_running:return True
        try:
            source=Path('/run/lmi-camera/live.ppm')
            meta=Path('/run/lmi-camera/live.json')
            if meta.stat().st_mtime_ns<=self.live_started:return True
            metadata=json.loads(meta.read_text())
            if metadata.get('ended'):
                self.preview_failed('Aperçu arrêté. Touche Relancer l’aperçu pour continuer.')
                return True
            stamp=metadata['sequence']
            if stamp==self.live_stamp:return True
            pixbuf=GdkPixbuf.Pixbuf.new_from_file(str(source))
            if (pixbuf.get_width(),pixbuf.get_height())!=(1280,720):raise RuntimeError('Format de l’aperçu inattendu.')
            rotations={0:GdkPixbuf.PixbufRotation.NONE,90:GdkPixbuf.PixbufRotation.CLOCKWISE,180:GdkPixbuf.PixbufRotation.UPSIDEDOWN,270:GdkPixbuf.PixbufRotation.COUNTERCLOCKWISE}
            angle=metadata['sensor_orientation']
            if angle not in rotations:raise RuntimeError('Orientation de l’aperçu inconnue.')
            self.live_pixbuf=pixbuf.rotate_simple(rotations[angle]);self.live_stamp=stamp
            self.picture.set_paintable(Gdk.Texture.new_for_pixbuf(self.live_pixbuf))
            self.capture.set_sensitive(True)
            self.status.set_text('Aperçu arrière — touche Prendre une photo.')
            print('PREVIEW_FRAME '+str(stamp),flush=True)
        except FileNotFoundError:pass
        except Exception as error:self.preview_failed(str(error))
        return True

    def close_camera(self,window):
        if not self.once:
            try:subprocess.run(['/usr/bin/systemctl','--no-ask-password','--no-block','stop','lmi-camera-preview.service'],timeout=3,capture_output=True)
            except subprocess.TimeoutExpired:pass
        return False

    def take_photo(self,button):
        if self.busy:return
        if not self.once:
            if self.live_pixbuf is None or not self.live_running:return
            try:
                folder=self.photo_folder();folder.mkdir(mode=0o700,parents=True,exist_ok=True)
                destination=folder/('LMI-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.png')
                ok,data=self.live_pixbuf.save_to_bufferv('png',[],[])
                if not ok:raise RuntimeError('Impossible de préparer la photo.')
                fd=os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                with os.fdopen(fd,'wb') as stream:stream.write(data)
                self.photo=str(destination);self.open.set_sensitive(True)
                self.status.set_text('Photo enregistrée — aperçu toujours actif.')
                print('PHOTO_SAVED '+str(destination),flush=True)
            except Exception as error:self.status.set_text(str(error))
            return
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
            metadata=json.loads(Path('/run/lmi-camera/latest.json').read_text())
            orientation=metadata['sensor_orientation']
            rotations={0:GdkPixbuf.PixbufRotation.NONE,90:GdkPixbuf.PixbufRotation.CLOCKWISE,
                       180:GdkPixbuf.PixbufRotation.UPSIDEDOWN,270:GdkPixbuf.PixbufRotation.COUNTERCLOCKWISE}
            if orientation not in rotations:raise RuntimeError('Orientation du capteur inconnue.')
            pixbuf=pixbuf.rotate_simple(rotations[orientation])
            if pixbuf is None:raise RuntimeError('Impossible de redresser la photo.')
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
