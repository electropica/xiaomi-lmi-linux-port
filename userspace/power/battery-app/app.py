"""Mobile battery viewer. Logging starts only through an explicit user action."""
import datetime, json, subprocess
from pathlib import Path
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk, GdkPixbuf
from model import STATE, snapshot, number, load, analyze, graph_svg, export_csv, iter_rows


class Battery(Adw.Application):
    def __init__(self):
        super().__init__(application_id='local.lmi.Battery')
        self.connect('activate', self.open)
        self.cache = {}

    def open(self, app):
        if self.get_active_window():
            self.get_active_window().present()
            return
        self.window = Adw.ApplicationWindow(application=self, title='Batterie lmi', default_width=360, default_height=720)
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        self.toasts = Adw.ToastOverlay()
        scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=16, margin_bottom=16, margin_start=16, margin_end=16)
        scroll.set_child(box)
        self.toasts.set_child(scroll)
        toolbar.set_content(self.toasts)
        self.window.set_content(toolbar)
        self.level = Gtk.Label()
        self.level.add_css_class('title-1')
        box.append(self.level)
        self.live = Gtk.Label(wrap=True)
        box.append(self.live)
        self.logging = Gtk.Label(wrap=True)
        box.append(self.logging)
        buttons = Gtk.Box(spacing=8, homogeneous=True)
        for title, command in [('Démarrer le suivi', 'start'), ('Arrêter', 'stop')]:
            button = Gtk.Button(label=title)
            button.connect('clicked', self.control, command)
            buttons.append(button)
        box.append(buttons)
        self.auto_updating = False
        self.auto = Adw.SwitchRow(title='Suivi automatique au démarrage', subtitle='À la prochaine ouverture de session')
        try:
            enabled = subprocess.run(['systemctl','--user','is-enabled','lmi-battery-recorder.service'],capture_output=True,text=True,timeout=8)
            automatic = enabled.stdout.strip()=='enabled'
        except subprocess.TimeoutExpired:
            automatic = False
        self.auto.set_active(automatic)
        self.auto.connect('notify::active', self.automatic)
        box.append(self.auto)
        self.sessions = Gtk.DropDown()
        self.sessions.connect('notify::selected', lambda *_: self.history())
        box.append(self.sessions)
        self.chart = Gtk.Picture(can_shrink=True)
        box.append(self.chart)
        self.summary = Gtk.Label(wrap=True, xalign=0)
        box.append(self.summary)
        export = Gtk.Button(label='Exporter cette session en CSV')
        export.connect('clicked', self.export)
        box.append(export)
        note = Gtk.Label(label='Le suivi continue si cette fenêtre est fermée. Les relevés périodiques attendent le réveil du téléphone. La vue montre au maximum les 5 000 derniers relevés ; le CSV exporte la session complète. Les estimations de jauge couvrent seulement les intervalles de décharge valides.', wrap=True, xalign=0)
        note.add_css_class('dim-label')
        box.append(note)
        self.files = []
        self.refresh(force=True)
        GLib.timeout_add_seconds(3, self.tick)
        self.window.present()

    def tick(self):
        if self.window.is_active():
            self.refresh()
        return bool(self.get_windows())

    def refresh(self, force=False):
        row = snapshot()
        data = row['supplies']['battery']
        self.level.set_text((data.get('capacity') or '—') + ' %')
        status = {'Charging':'En charge', 'Discharging':'Décharge', 'Full':'Chargée', 'Not charging':'Sans charge'}.get(data.get('status'), data.get('status') or 'État inconnu')
        values = []
        for key, scale, suffix in [('current_now',1000,'mA'),('voltage_now',1000000,'V'),('temp',10,'°C')]:
            value = number(data.get(key))
            values.append('—' if value is None else f'{value/scale:.2f} {suffix}')
        self.live.set_text(status + '\n' + ' · '.join(values) + '\nCourant signé tel que fourni par le pilote')
        try:
            state = json.loads((STATE/'status.json').read_text())
            running = state.get('active') and 'lmi-battery/recorder.py' in Path(f"/proc/{int(state['pid'])}/cmdline").read_text()
        except (OSError, ValueError, KeyError):
            running = False
        self.logging.set_text('Suivi actif : un relevé par minute éveillée' if running else 'Suivi arrêté')
        files = sorted((STATE/'sessions').glob('*.jsonl'), key=lambda p:p.stat().st_mtime, reverse=True)
        if force or files != self.files:
            self.files = files
            self.sessions.set_model(Gtk.StringList.new([datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime('%d/%m %H:%M') for p in files] or ['Aucune session']))
        self.history()

    def selected_rows(self):
        index = self.sessions.get_selected()
        if index >= len(self.files):
            return []
        path = self.files[index]
        stamp = path.stat().st_mtime_ns
        if self.cache.get('key') != (path, stamp):
            self.cache = {'key':(path, stamp), 'rows':load(path)}
        return self.cache['rows']

    def history(self):
        rows = self.selected_rows()
        result = analyze(rows)
        lines = [f"Veille observée : {result['sleep_s']/60:.1f} min" if result['valid_sleep_pairs'] else 'Veille : aucun intervalle complet observé']
        if result['warnings']:
            lines.append('Certaines transitions de veille sont incomplètes ou invalides')
        names = {'charge_counter':'Compteur logiciel', 'charge_counter_shadow':'Compteur shadow', 'charge_now_raw':'Compteur brut'}
        for name, item in result['methods'].items():
            value = item['estimated_ma']
            lines.append(f"{names[name]} : " + ('données insuffisantes' if value is None else f"{value:.1f} mA estimés sur {item['duration_s']/60:.1f} min"))
        self.summary.set_text('\n'.join(lines))
        try:
            loader = GdkPixbuf.PixbufLoader.new_with_type('svg')
            loader.write(graph_svg(rows, Adw.StyleManager.get_default().get_dark()))
            loader.close()
            self.chart.set_paintable(Gdk.Texture.new_for_pixbuf(loader.get_pixbuf()))
        except GLib.Error:
            self.chart.set_visible(False)

    def control(self, button, action):
        try:
            result = subprocess.run(['systemctl','--user',action,'lmi-battery-recorder.service'],capture_output=True,text=True,timeout=8)
            failed = result.returncode != 0
        except subprocess.TimeoutExpired:
            failed = True
        if failed:
            self.toasts.add_toast(Adw.Toast(title='Impossible de modifier le suivi'))
        self.refresh(force=True)

    def export(self, button):
        rows = self.selected_rows()
        if not rows:
            self.toasts.add_toast(Adw.Toast(title='Aucune donnée à exporter'))
            return
        folder = Path.home()/'Documents/Batterie-lmi'
        folder.mkdir(parents=True,exist_ok=True)
        path = folder/('session-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.csv')
        export_csv(iter_rows(self.files[self.sessions.get_selected()]),path)
        self.toasts.add_toast(Adw.Toast(title='CSV enregistré dans Documents/Batterie-lmi'))

    def automatic(self, row, pspec):
        if self.auto_updating:
            return
        active = row.get_active()
        try:
            result = subprocess.run(['systemctl','--user','enable' if active else 'disable','lmi-battery-recorder.service'],capture_output=True,text=True,timeout=8)
            failed = result.returncode != 0
        except subprocess.TimeoutExpired:
            failed = True
        if failed:
            self.auto_updating = True
            row.set_active(not active)
            self.auto_updating = False
            self.toasts.add_toast(Adw.Toast(title='Impossible de modifier le démarrage automatique'))
        else:
            self.toasts.add_toast(Adw.Toast(title='Suivi prévu au prochain démarrage' if active else 'Démarrage automatique désactivé'))


if __name__ == '__main__':
    Battery().run()
