//! battery-viewer : affiche les courbes et anomalies du CSV de battery-logger.
//!
//! Le lecteur lit *tous* les fichiers de relevés : le fichier courant et ceux
//! que le logger a archivés quand son format a changé.  Un changement de
//! format ne doit pas rendre les relevés précédents invisibles.
//!
//! Les durées de suspension sont affichées lorsqu'elles sont disponibles.
//! La veille profonde matérielle n'est pas établie par ces relevés.

use std::cell::{Cell, RefCell};
use std::fs;
use std::io::Read;
use std::path::PathBuf;
use std::rc::Rc;

use adw::prelude::*;
use gtk::{cairo, glib};

/// Seuil d'anomalie : puissance (W) écran éteint au-delà duquel on alerte.
const ANOMALY_W: f64 = 1.2;
const MAX_ANOMALIES: usize = 100;

// ───────────────────────── Données ─────────────────────────

#[derive(Clone, Default, Debug)]
struct Sample {
    t: i64, // secondes depuis l'epoch
    reason: String,
    status: String,
    capacity: Option<f64>,
    power_w: Option<f64>,
    temp_c: Option<f64>,
    screen_on: Option<bool>,
    procs: String,
    wake: String,
    modem_signal: Option<f64>,
    modem_tech: String,
    // Version 2 du format : temps de suspension et preuve de veille profonde.
    interval_s: Option<f64>,
    suspend_s: Option<f64>,
    suspend_count: Option<f64>,
    deep_sleep_proof: String, // "yes", "no" ou "n/a"
}

fn data_dir() -> PathBuf {
    glib::user_data_dir().join("battery-diag")
}

/// Tous les fichiers de relevés : le fichier courant et ses archives.
///
/// Le logger archive le fichier précédent quand ses colonnes changent, sous
/// le nom `discharge_diag.csv.old-<horodatage>`.  Sans cette lecture, un
/// changement de format ferait disparaître les relevés passés.
fn data_files() -> Vec<PathBuf> {
    let dir = data_dir();
    let mut files: Vec<PathBuf> = Vec::new();
    if let Ok(entries) = fs::read_dir(&dir) {
        for entry in entries.flatten() {
            let name = entry.file_name().to_string_lossy().to_string();
            if name == "discharge_diag.csv" || name.starts_with("discharge_diag.csv.old-") {
                files.push(entry.path());
            }
        }
    }
    files.sort();
    files
}

fn num(s: &str) -> Option<f64> {
    s.trim().parse::<f64>().ok().filter(|v| v.is_finite())
}

/// Lit le CSV par NOM de colonne : l'ordre des colonnes importe peu.
fn parse_samples(input: impl Read) -> Result<Vec<Sample>, String> {
    let mut rdr = csv::ReaderBuilder::new().flexible(true).from_reader(input);
    let headers = rdr.headers().map_err(|e| e.to_string())?.clone();
    let idx = |name: &str| headers.iter().position(|h| h == name);
    let (i_ts, i_reason, i_status) = (idx("timestamp"), idx("reason"), idx("status"));
    let (i_cap, i_pow, i_temp) = (idx("capacity_pct"), idx("power_w"), idx("temp_c"));
    let i_screen = idx("screen_on");
    let (i_procs, i_wake) = (idx("top_procs"), idx("wake_sources"));
    let (i_msig, i_mtech) = (idx("modem_signal_pct"), idx("modem_tech"));
    // Colonnes de la version 2 : absentes dans les fichiers anciens, ce qui
    // est toléré (les valeurs restent « N/A »).
    let (i_interval, i_suspend) = (idx("interval_s"), idx("suspend_s"));
    let (i_count, i_proof) = (idx("suspend_count"), idx("deep_sleep"));
    if i_ts.is_none() {
        return Err("colonne « timestamp » absente : ce n'est pas un CSV de battery-logger".into());
    }

    let mut out = Vec::new();
    for rec in rdr.records().flatten() {
        let get = |i: Option<usize>| i.and_then(|i| rec.get(i)).unwrap_or("N/A");
        let Ok(dt) = chrono::DateTime::parse_from_rfc3339(get(i_ts)) else { continue };
        out.push(Sample {
            t: dt.timestamp(),
            reason: get(i_reason).to_string(),
            status: get(i_status).to_string(),
            capacity: num(get(i_cap)),
            power_w: num(get(i_pow)),
            temp_c: num(get(i_temp)),
            screen_on: match get(i_screen) {
                "1" => Some(true),
                "0" => Some(false),
                _ => None,
            },
            procs: get(i_procs).to_string(),
            wake: get(i_wake).to_string(),
            modem_signal: num(get(i_msig)),
            modem_tech: get(i_mtech).to_string(),
            interval_s: num(get(i_interval)),
            suspend_s: num(get(i_suspend)),
            suspend_count: num(get(i_count)),
            deep_sleep_proof: get(i_proof).to_string(),
        });
    }
    out.sort_by_key(|s| s.t);
    Ok(out)
}

/// Lit tous les fichiers de relevés et les fusionne.
fn load_samples() -> Result<Vec<Sample>, String> {
    let files = data_files();
    if files.is_empty() {
        return Err("aucun fichier de relevé dans le dossier de données".into());
    }
    let mut out: Vec<Sample> = Vec::new();
    let mut errors: Vec<String> = Vec::new();
    for path in files {
        match fs::File::open(&path).map_err(|e| e.to_string()).and_then(parse_samples) {
            Ok(mut v) => out.append(&mut v),
            Err(e) => errors.push(format!("{}: {}", path.display(), e)),
        }
    }
    if out.is_empty() {
        return Err(if errors.is_empty() {
            "aucun relevé".to_string()
        } else {
            errors.join(" ; ")
        });
    }
    out.sort_by_key(|s| s.t);
    out.dedup_by_key(|s| s.t);
    Ok(out)
}

fn mean(it: impl Iterator<Item = f64>) -> Option<f64> {
    let (sum, n) = it.fold((0.0, 0u32), |(s, n), v| (s + v, n + 1));
    if n > 0 { Some(sum / n as f64) } else { None }
}

/// Un relevé « resume » est pris au réveil : son courant est naturellement élevé,
/// il ne reflète pas la consommation pendant le sommeil.
fn is_screen_off_discharge(s: &Sample) -> bool {
    s.screen_on == Some(false) && s.status == "Discharging" && s.reason != "resume"
}

fn is_anomaly(s: &Sample) -> bool {
    is_screen_off_discharge(s) && s.power_w.map_or(false, |p| p > ANOMALY_W)
}

/// Le temps de suspension mesuré sur l'intervalle, en secondes.
fn suspend_seconds(s: &Sample) -> Option<f64> {
    s.suspend_s.filter(|v| *v > 0.0)
}

/// Legacy label supplied by older CSVs; it does not establish deep sleep.

fn legacy_deep_sleep_flag(s: &Sample) -> bool {
    s.deep_sleep_proof.eq_ignore_ascii_case("yes")
}

fn human_duration(seconds: f64) -> String {
    let total = seconds.round() as i64;
    if total < 60 {
        format!("{total} s")
    } else if total < 3600 {
        format!("{} min {:02} s", total / 60, total % 60)
    } else if total < 86400 {
        format!("{} h {:02}", total / 3600, (total % 3600) / 60)
    } else {
        format!("{} j {:02} h", total / 86400, (total % 86400) / 3600)
    }
}

fn local_time(t: i64, fmt: &str) -> String {
    chrono::DateTime::from_timestamp(t, 0)
        .map(|d| d.with_timezone(&chrono::Local).format(fmt).to_string())
        .unwrap_or_else(|| "?".into())
}

// ───────────────────────── Dessin Cairo ─────────────────────────

type Rgb = (f64, f64, f64);
const C_BATT: Rgb = (0.21, 0.52, 0.89);
const C_POWER: Rgb = (0.90, 0.38, 0.00);
const C_SCREEN: Rgb = (0.96, 0.77, 0.06);
/// Temps de suspension mesuré : une barre par intervalle.
const C_SUSPEND: Rgb = (0.45, 0.45, 0.55);


fn fg_color(dark: bool) -> Rgb {
    if dark { (0.92, 0.92, 0.92) } else { (0.12, 0.12, 0.12) }
}

struct Plot {
    x0: f64,
    y0: f64,
    x1: f64,
    y1: f64,
    tmin: f64,
    tmax: f64,
}

impl Plot {
    fn new(w: i32, h: i32, tmin: i64, tmax: i64) -> Self {
        Plot {
            x0: 36.0,
            y0: 30.0,
            x1: (w as f64 - 36.0).max(80.0),
            y1: (h as f64 - 24.0).max(60.0),
            tmin: tmin as f64,
            tmax: tmax as f64,
        }
    }
    fn px(&self, t: i64) -> f64 {
        self.x0 + (t as f64 - self.tmin) / (self.tmax - self.tmin).max(1.0) * (self.x1 - self.x0)
    }
    fn py(&self, v: f64, lo: f64, hi: f64) -> f64 {
        self.y1 - ((v - lo) / (hi - lo)).clamp(0.0, 1.0) * (self.y1 - self.y0)
    }
}

/// `align` : 0.0 = texte à droite de x, 0.5 = centré, 1.0 = texte à gauche de x.
fn text(cr: &cairo::Context, s: &str, x: f64, y: f64, align: f64, color: Rgb, alpha: f64) {
    cr.select_font_face("Sans", cairo::FontSlant::Normal, cairo::FontWeight::Normal);
    cr.set_font_size(11.0);
    let width = cr.text_extents(s).map(|e| e.width()).unwrap_or(0.0);
    cr.set_source_rgba(color.0, color.1, color.2, alpha);
    cr.move_to(x - width * align, y);
    let _ = cr.show_text(s);
}

fn legend(cr: &cairo::Context, x: f64, y: f64, items: &[(&str, Rgb)], fg: Rgb) {
    let mut x = x;
    for (label, color) in items {
        cr.set_source_rgb(color.0, color.1, color.2);
        cr.rectangle(x, y - 9.0, 10.0, 10.0);
        let _ = cr.fill();
        text(cr, label, x + 14.0, y, 0.0, fg, 0.9);
        let w = cr.text_extents(label).map(|e| e.width()).unwrap_or(40.0);
        x += 14.0 + w + 14.0;
    }
}

/// Grille, graduations gauche (obligatoires) et droite (optionnelles) et axe du temps.
fn draw_frame(
    cr: &cairo::Context,
    p: &Plot,
    fg: Rgb,
    left: (f64, f64, Rgb),
    right: Option<(f64, f64, Rgb)>,
) {
    cr.set_line_width(1.0);
    for i in 0..=4 {
        let f = i as f64 / 4.0;
        let y = p.y1 - f * (p.y1 - p.y0);
        cr.set_source_rgba(fg.0, fg.1, fg.2, 0.12);
        cr.move_to(p.x0, y);
        cr.line_to(p.x1, y);
        let _ = cr.stroke();
        let lv = left.0 + (left.1 - left.0) * f;
        let tick = if left.1 - left.0 < 4.0 { format!("{lv:.1}") } else { format!("{lv:.0}") }; text(cr, &tick, p.x0 - 5.0, y + 4.0, 1.0, left.2, 0.95);
        if let Some((lo, hi, color)) = right {
            text(cr, &format!("{:.1}", lo + (hi - lo) * f), p.x1 + 5.0, y + 4.0, 0.0, color, 0.95);
        }
    }
    let span = (p.tmax - p.tmin) as i64;
    let fmt = if span > 36 * 3600 { "%d/%m" } else { "%H:%M" };
    for i in 0..=3 {
        let t = (p.tmin + (p.tmax - p.tmin) * i as f64 / 3.0) as i64;
        let align = match i { 0 => 0.0, 3 => 1.0, _ => 0.5 };
        text(cr, &local_time(t, fmt), p.px(t), p.y1 + 16.0, align, fg, 0.7);
    }
}

// Avoid inventing values across suspend or collector downtime.
fn continuous_samples(previous: i64, current: i64) -> bool {
    current >= previous && current - previous <= 360
}

fn polyline(cr: &cairo::Context, p: &Plot, pts: &[(i64, f64)], lo: f64, hi: f64, color: Rgb) {
    if pts.len() < 2 {
        return;
    }
    cr.set_source_rgb(color.0, color.1, color.2);
    cr.set_line_width(2.0);
    cr.set_line_join(cairo::LineJoin::Round);
    for (i, (t, v)) in pts.iter().enumerate() {
        let (x, y) = (p.px(*t), p.py(*v, lo, hi));
        if i == 0 || !continuous_samples(pts[i - 1].0, *t) { cr.move_to(x, y) } else { cr.line_to(x, y) }
    }
    let _ = cr.stroke();
}

fn no_data(cr: &cairo::Context, w: i32, h: i32, fg: Rgb) {
    text(cr, "Pas assez de données pour cette période", w as f64 / 2.0, h as f64 / 2.0, 0.5, fg, 0.7);
}

/// Graphique 1 : batterie (%, axe gauche) et puissance (W, axe droit).
fn draw_battery_chart(cr: &cairo::Context, w: i32, h: i32, data: &[Sample], dark: bool) {
    let fg = fg_color(dark);
    if data.len() < 2 {
        return no_data(cr, w, h, fg);
    }
    let p = Plot::new(w, h, data[0].t, data[data.len() - 1].t);
    let max_p = data.iter().filter_map(|s| s.power_w).fold(0.0_f64, f64::max);
    let p_hi = ((max_p / 2.0).ceil() * 2.0).max(2.0);

    draw_frame(cr, &p, fg, (0.0, 100.0, C_BATT), Some((0.0, p_hi, C_POWER)));
    legend(cr, p.x0, 16.0, &[("Batterie %", C_BATT), ("Puissance W", C_POWER)], fg);

    // Ligne pointillée du seuil d'anomalie.
    let y = p.py(ANOMALY_W, 0.0, p_hi);
    cr.set_source_rgba(C_POWER.0, C_POWER.1, C_POWER.2, 0.6);
    cr.set_line_width(1.0);
    cr.set_dash(&[4.0, 4.0], 0.0);
    cr.move_to(p.x0, y);
    cr.line_to(p.x1, y);
    let _ = cr.stroke();
    cr.set_dash(&[], 0.0);

    let cap: Vec<_> = data.iter().filter_map(|s| s.capacity.map(|v| (s.t, v))).collect();
    let pow: Vec<_> = data.iter().filter_map(|s| s.power_w.map(|v| (s.t, v))).collect();
    polyline(cr, &p, &cap, 0.0, 100.0, C_BATT);
    polyline(cr, &p, &pow, 0.0, p_hi, C_POWER);
}

/// Graphique 2 : temps de suspension si disponible, sans preuve de veille profonde.
fn draw_sleep_chart(cr: &cairo::Context, w: i32, h: i32, data: &[Sample], dark: bool) {
    let fg = fg_color(dark);
    if data.len() < 2 {
        return no_data(cr, w, h, fg);
    }
    let p = Plot::new(w, h, data[0].t, data[data.len() - 1].t);
    if !data.iter().any(|s| s.interval_s.is_some()) {
        return no_data(cr, w, h, fg);
    }
    let max_s = data
        .iter()
        .filter_map(|s| s.interval_s)
        .fold(1.0_f64, f64::max)
        .max(1.0);
    draw_frame(cr, &p, fg, (0.0, max_s, C_SUSPEND), None);
    legend(cr, p.x0, 16.0,
           &[("Suspension (s)", C_SUSPEND), ("Écran allumé", C_SCREEN)],
           fg);

    // Bandes « écran allumé » : de ce relevé jusqu'au suivant.
    cr.set_source_rgba(C_SCREEN.0, C_SCREEN.1, C_SCREEN.2, 0.35);
    for pair in data.windows(2) {
        if pair[0].screen_on == Some(true) && continuous_samples(pair[0].t, pair[1].t) {
            let (xa, xb) = (p.px(pair[0].t), p.px(pair[1].t));
            cr.rectangle(xa, p.y0, (xb - xa).max(1.0), p.y1 - p.y0);
            let _ = cr.fill();
        }
    }

    // Une barre par intervalle : hauteur = durée de l'intervalle, remplissage
    // = temps qui a été passé suspendu.
    let n = data.len();
    let slot = ((p.x1 - p.x0) / n as f64).max(1.0);
    for pair in data.windows(2) {
        let (xa, xb) = (p.px(pair[0].t), p.px(pair[1].t));
        let width = (xb - xa).max(1.0).min(slot.max(3.0));
        let interval = pair[1].interval_s.unwrap_or(0.0);
        let suspended = suspend_seconds(&pair[1]).unwrap_or(0.0);
        if interval <= 0.0 {
            continue;
        }
        let y_full = p.py(interval, 0.0, max_s);
        let y_susp = p.py(suspended.min(interval), 0.0, max_s);
        // Barre : intervalle complet en gris clair.
        cr.set_source_rgba(C_SUSPEND.0, C_SUSPEND.1, C_SUSPEND.2, 0.25);
        cr.rectangle(xa, y_full, width, p.y1 - y_full);
        let _ = cr.fill();
        // Partie réellement suspendue.
        let color = C_SUSPEND;
        cr.set_source_rgba(color.0, color.1, color.2, 0.9);
        cr.rectangle(xa, y_susp, width, p.y1 - y_susp);
        let _ = cr.fill();
    }
}

// ───────────────────────── Interface ─────────────────────────

struct Ui {
    all: RefCell<Vec<Sample>>,
    view: Rc<RefCell<Vec<Sample>>>,
    hours: Cell<Option<i64>>,
    info: gtk::Label,
    latest: gtk::Label,
    v_power: gtk::Label,
    v_suspend: gtk::Label,
    v_proof: gtk::Label,
    v_temp: gtk::Label,
    list: gtk::ListBox,
    chart1: gtk::DrawingArea,
    chart2: gtk::DrawingArea,
}

fn opt(v: Option<f64>, unit: &str, decimals: usize) -> String {
    v.map(|x| format!("{x:.decimals$} {unit}")).unwrap_or_else(|| "N/A".into())
}

fn esc(s: &str) -> String {
    glib::markup_escape_text(s).to_string()
}

impl Ui {
    fn reload(&self) {
        match load_samples() {
            Ok(v) => {
                *self.all.borrow_mut() = v;
            }
            Err(e) => {
                self.all.borrow_mut().clear();
                self.info.set_text(&format!(
                    "Aucune donnée : {e}. Le service battery-logger tourne-t-il ?"
                ));
            }
        }

        let now = chrono::Utc::now().timestamp();
        let cutoff = self.hours.get().map(|h| now - h * 3600);
        let view: Vec<Sample> = self
            .all
            .borrow()
            .iter()
            .filter(|s| cutoff.map_or(true, |c| s.t >= c))
            .cloned()
            .collect();

        if let Some(last) = view.last() {
            let level = last.capacity.map(|v| format!("{v:.0} %")).unwrap_or_else(|| "– %".into());
            let state = match last.status.as_str() {
                "Charging" => "En charge",
                "Discharging" => "Sur batterie",
                "Full" => "Charge terminée",
                "Not charging" => "Charge arrêtée",
                _ => "État indisponible",
            };
            self.latest.set_text(&format!("{level} · {state}"));
        } else {
            self.latest.set_text("Aucun relevé sur cette période");
        }
        if !view.is_empty() {
            let suspensions = view.iter().filter_map(|s| s.suspend_count).fold(0.0_f64, f64::max);
            self.info.set_text(&format!(
                "{} relevés · dernier à {} · suspensions du noyau : {}",
                view.len(),
                local_time(view[view.len() - 1].t, "%d/%m %H:%M"),
                if suspensions > 0.0 { format!("{suspensions:.0}") } else { "N/A".to_string() }
            ));
        } else if !self.all.borrow().is_empty() {
            self.info.set_text("Aucun relevé sur cette période.");
        }

        // Cartes de résumé.
        let off_power = mean(view.iter().filter(|s| is_screen_off_discharge(s)).filter_map(|s| s.power_w));
        let tmax = view.iter().filter_map(|s| s.temp_c).fold(None, |m: Option<f64>, v| {
            Some(m.map_or(v, |x| x.max(v)))
        });
        // Temps de suspension : la somme des durées réellement passées
        // suspendues, mesurées par l'écart BOOTTIME/MONOTONIC.
        let suspend_total: f64 = view.iter().filter_map(suspend_seconds).sum();

self.v_power.set_text(&opt(off_power, "W", 2));
        self.v_suspend.set_text(&if suspend_total > 0.0 {
            human_duration(suspend_total)
        } else {
            "N/A".into()
        });
        self.v_proof.set_text("Non mesurée");
        self.v_temp.set_text(&opt(tmax, "°C", 1));

        // Liste des anomalies (les plus récentes d'abord).
        while let Some(child) = self.list.first_child() {
            self.list.remove(&child);
        }
        let mut shown = 0;
        for s in view.iter().rev().filter(|s| is_anomaly(s)).take(MAX_ANOMALIES) {
            let modem = match s.modem_signal {
                Some(sig) => format!("{sig:.0} % ({})", s.modem_tech),
                None => format!("N/A ({})", s.modem_tech),
            };
            let sleep = match suspend_seconds(s) {
                Some(sec) if sec > 0.0 => format!("\nSuspension : {}", human_duration(sec)),
                _ => String::new(),
            };
            let subtitle = format!(
                "Processus : {}\nRéveils : {}\nModem : {}{}",
                esc(&s.procs.replace('|', ", ")),
                esc(&s.wake.replace('|', ", ")),
                esc(&modem),
                esc(&sleep),
            );
            let row = adw::ActionRow::builder()
                .title(format!(
                    "{} · {:.2} W",
                    local_time(s.t, "%d/%m %H:%M"),
                    s.power_w.unwrap_or(0.0)
                ))
                .subtitle(subtitle)
                .build();
            self.list.append(&row);
            shown += 1;
        }
        if shown == 0 {
            let row = adw::ActionRow::builder()
                .title("Aucune anomalie")
                .subtitle(format!("Aucun relevé > {ANOMALY_W} W écran éteint sur cette période."))
                .build();
            self.list.append(&row);
        }

        *self.view.borrow_mut() = view;
        self.chart1.queue_draw();
        self.chart2.queue_draw();
    }
}

fn card(title: &str) -> (gtk::Box, gtk::Label) {
    let b = gtk::Box::new(gtk::Orientation::Vertical, 2);
    b.add_css_class("card");
    b.set_hexpand(true);
    b.set_homogeneous(false);
    let value = gtk::Label::new(Some("–"));
    value.add_css_class("title-3");
    value.set_margin_top(10);
    value.set_ellipsize(gtk::pango::EllipsizeMode::End);
    let label = gtk::Label::new(Some(title));
    label.add_css_class("caption");
    label.add_css_class("dim-label");
    label.set_wrap(true);
    label.set_justify(gtk::Justification::Center);
    label.set_margin_bottom(10);
    b.append(&value);
    b.append(&label);
    (b, value)
}

fn section(title: &str, child: &impl IsA<gtk::Widget>) -> gtk::Box {
    let b = gtk::Box::new(gtk::Orientation::Vertical, 6);
    let l = gtk::Label::new(Some(title));
    l.add_css_class("heading");
    l.set_halign(gtk::Align::Start);
    b.append(&l);
    b.append(child);
    b
}

fn chart_area() -> gtk::DrawingArea {
    let a = gtk::DrawingArea::builder().content_height(230).hexpand(true).build();
    a.add_css_class("card");
    a
}

fn build_ui(app: &adw::Application) {
    let view = Rc::new(RefCell::new(Vec::<Sample>::new()));

    let chart1 = chart_area();
    let chart2 = chart_area();
    let v = view.clone();
    chart1.set_draw_func(move |_, cr, w, h| {
        draw_battery_chart(cr, w, h, &v.borrow(), adw::StyleManager::default().is_dark())
    });
    let v = view.clone();
    chart2.set_draw_func(move |_, cr, w, h| {
        draw_sleep_chart(cr, w, h, &v.borrow(), adw::StyleManager::default().is_dark())
    });
    {
        let (c1, c2) = (chart1.clone(), chart2.clone());
        adw::StyleManager::default().connect_dark_notify(move |_| {
            c1.queue_draw();
            c2.queue_draw();
        });
    }

    let (card_power, v_power) = card("Batterie · écran éteint");
    let (card_suspend, v_suspend) = card("Temps de suspension");
    let (card_proof, v_proof) = card("Veille profonde");
    let (card_temp, v_temp) = card("Température max");
    let cards = gtk::Grid::builder().column_spacing(8).row_spacing(8).column_homogeneous(true).build();
    cards.attach(&card_power, 0, 0, 1, 1);
    cards.attach(&card_suspend, 1, 0, 1, 1);
    cards.attach(&card_proof, 0, 1, 1, 1);
    cards.attach(&card_temp, 1, 1, 1, 1);

    let list = gtk::ListBox::new();
    list.add_css_class("boxed-list");
    list.set_selection_mode(gtk::SelectionMode::None);

    let latest = gtk::Label::new(None);
    latest.add_css_class("title-2");
    latest.set_wrap(true);
    latest.set_xalign(0.0);
    let info = gtk::Label::new(None);
    info.add_css_class("caption");
    info.add_css_class("dim-label");
    info.set_wrap(true);

    let ui = Rc::new(Ui {
        all: RefCell::new(Vec::new()),
        view,
        hours: Cell::new(Some(24)),
        info: info.clone(),
        latest: latest.clone(),
        v_power,
        v_suspend,
        v_proof,
        v_temp,
        list: list.clone(),
        chart1: chart1.clone(),
        chart2: chart2.clone(),
    });

    // Filtre de période : 3 boutons « segmentés ».
    let b6 = gtk::ToggleButton::with_label("6 h");
    let b24 = gtk::ToggleButton::with_label("24 h");
    let ball = gtk::ToggleButton::with_label("Tout");
    b24.set_group(Some(&b6));
    ball.set_group(Some(&b6));
    b24.set_active(true);
    let seg = gtk::Box::new(gtk::Orientation::Horizontal, 0);
    seg.add_css_class("linked");
    seg.set_halign(gtk::Align::Center);
    for (btn, hours) in [(&b6, Some(6)), (&b24, Some(24)), (&ball, None)] {
        seg.append(btn);
        let ui = ui.clone();
        btn.connect_toggled(move |b| {
            if b.is_active() {
                ui.hours.set(hours);
                ui.reload();
            }
        });
    }

    let content = gtk::Box::new(gtk::Orientation::Vertical, 14);
    content.set_margin_top(12);
    content.set_margin_bottom(12);
    content.set_margin_start(12);
    content.set_margin_end(12);
    content.append(&seg);
    content.append(&latest);
    content.append(&info);
    content.append(&cards);
    content.append(&section("Batterie et puissance", &chart1));
    let power_note = gtk::Label::new(Some("Puissance estimée à la batterie : tension × courant. En charge, elle ne représente pas la consommation totale. Les courbes s'interrompent sans relevé."));
    power_note.add_css_class("caption");
    power_note.add_css_class("dim-label");
    power_note.set_wrap(true);
    power_note.set_xalign(0.0);
    content.append(&power_note);
    content.append(&section("Temps de suspension", &chart2));
    content.append(&section(
        &format!("Anomalies (> {ANOMALY_W} W, écran éteint)"),
        &list,
    ));

    let clamp = adw::Clamp::builder().maximum_size(640).child(&content).build();
    let scroll = gtk::ScrolledWindow::builder()
        .child(&clamp)
        .vexpand(true)
        .hscrollbar_policy(gtk::PolicyType::Never)
        .build();

    let header = adw::HeaderBar::new();
    header.set_title_widget(Some(&adw::WindowTitle::new("Diagnostic batterie", "")));
    let refresh = gtk::Button::from_icon_name("view-refresh-symbolic");
    refresh.set_tooltip_text(Some("Rafraîchir"));
    {
        let ui = ui.clone();
        refresh.connect_clicked(move |_| ui.reload());
    }
    header.pack_start(&refresh);

    let root = gtk::Box::new(gtk::Orientation::Vertical, 0);
    root.append(&header);
    root.append(&scroll);

    let window = adw::ApplicationWindow::builder()
        .application(app)
        .title("Diagnostic batterie")
        .default_width(360)
        .default_height(720)
        .content(&root)
        .build();

    ui.reload();
    window.present();
}

fn main() -> glib::ExitCode {
    let app = adw::Application::builder()
        .application_id("org.battery_diag.Viewer")
        .build();
    app.connect_activate(build_ui);
    app.run()
}

// ───────────────────────── Tests ─────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    const OLD_CSV: &str = "timestamp,reason,uptime_s,status,capacity_pct,voltage_v,current_ma,current_avg_ma,power_w,cap_now,cap_full,cap_unit,charge_counter_uah,temp_c,deep_sleep_pct,load1,cpu_freq_mhz,brightness,brightness_pct,screen_on,net,top_procs,wake_sources,cpu_online,cstate_name,cstate_ms,modem_signal_pct,modem_tech\n\
2026-11-14T12:13:05+01:00,start,301,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A,1.17,N/A,N/A,N/A,N/A,eth0=up,claude(+2510ms),N/A,2,N/A,N/A,N/A,N/A\n\
2026-11-14T12:15:05+01:00,periodic,421,Discharging,80,3.900,-400.0,-390.0,1.560,3000000,4000000,uAh,3000000,31.5,12.5,0.2,1000,0,0.0,0,wlan0=up,phosh(+900ms)|mm(+300ms),a(+50ms),4,WFI,1000,78,4G\n";

    const NEW_CSV: &str = "timestamp,reason,uptime_s,status,capacity_pct,voltage_v,current_ma,current_avg_ma,power_w,cap_now,cap_full,cap_unit,charge_counter_uah,temp_c,deep_sleep_pct,load1,cpu_freq_mhz,brightness,brightness_pct,screen_on,net,top_procs,wake_sources,cpu_online,cstate_name,cstate_ms,modem_signal_pct,modem_tech,interval_s,suspend_s,suspend_count,wakeup_count,mem_sleep,deep_sleep\n\
2026-11-15T23:10:05+01:00,resume,9001,Discharging,60,3.800,-120.0,-110.0,0.456,3000000,4000000,uAh,3000000,30.0,97.5,0.1,800,0,0.0,0,wlan0=up,none,2,4,WFI,1000,78,4G,7200.0,7000.0,42,3,s2idle,yes\n\
2026-11-15T23:20:05+01:00,periodic,9601,Discharging,59,3.800,-100.0,-95.0,0.380,3000000,4000000,uAh,3000000,30.0,10.0,0.1,800,0,0.0,0,wlan0=up,none,2,4,WFI,1000,78,4G,600.0,60.0,42,3,s2idle,no\n";

    #[test]
    fn parses_na_and_values() {
        let v = parse_samples(OLD_CSV.as_bytes()).unwrap();
        assert_eq!(v.len(), 2);
        assert_eq!(v[0].capacity, None);
        assert_eq!(v[1].capacity, Some(80.0));
        assert_eq!(v[1].screen_on, Some(false));
        assert!(is_anomaly(&v[1]));
        assert!(!is_anomaly(&v[0]));
    }

    #[test]
    fn old_files_have_no_sleep_columns_and_stay_readable() {
        let v = parse_samples(OLD_CSV.as_bytes()).unwrap();
        for s in &v {
            assert!(s.suspend_s.is_none());
            assert!(s.interval_s.is_none());
            assert!(s.suspend_count.is_none());
            assert!(!legacy_deep_sleep_flag(s));
        }
    }

    #[test]
    fn new_files_preserve_legacy_flag_and_suspend_time() {
        let v = parse_samples(NEW_CSV.as_bytes()).unwrap();
        assert_eq!(v.len(), 2);
        assert_eq!(suspend_seconds(&v[0]), Some(7000.0));
        assert!(legacy_deep_sleep_flag(&v[0]));
        // Le second intervalle a du temps de suspension, mais pas de preuve.
        assert_eq!(suspend_seconds(&v[1]), Some(60.0));
        assert!(!legacy_deep_sleep_flag(&v[1]));
    }

    #[test]
    fn legacy_deep_sleep_flag_is_not_hardware_proof() {
        let mut s = Sample::default();
        s.suspend_s = Some(3600.0);
        s.deep_sleep_proof = "n/a".into();
        assert!(!legacy_deep_sleep_flag(&s));
        s.deep_sleep_proof = "yes".into();
        assert!(legacy_deep_sleep_flag(&s));
    }

    #[test]
    fn graph_does_not_bridge_missing_intervals() {
        assert!(continuous_samples(1000, 1120));
        assert!(continuous_samples(1000, 1360));
        assert!(!continuous_samples(1000, 1361));
        assert!(!continuous_samples(1000, 999));
    }

    #[test]
    fn human_duration_reads_well() {
        assert_eq!(human_duration(30.0), "30 s");
        assert_eq!(human_duration(600.0), "10 min 00 s");
        assert_eq!(human_duration(231.6), "3 min 52 s");
        assert_eq!(human_duration(7200.0), "2 h 00");
        assert_eq!(human_duration(90000.0), "1 j 01 h");
    }

    fn fake(hours: i64) -> Vec<Sample> {
        let t0 = 1_800_000_000;
        (0..hours * 30)
            .map(|i| {
                let f = i as f64 / (hours * 30) as f64;
                let screen = (i / 25) % 4 == 0;
                Sample {
                    t: t0 + i * 120,
                    reason: "periodic".into(),
                    status: "Discharging".into(),
                    capacity: Some(100.0 - 60.0 * f),
                    power_w: Some(if screen { 1.8 } else if i % 40 == 0 { 1.6 } else { 0.25 }),
                    screen_on: Some(screen),
                    interval_s: Some(120.0),
                    suspend_s: Some(if screen { 0.0 } else { 110.0 }),
                    deep_sleep_proof: if screen { "no".into() } else { "yes".into() },
                    ..Default::default()
                }
            })
            .collect()
    }

    #[test]
    fn render_charts_to_png() {
        let dir = std::env::var("BATTERY_TEST_OUT").unwrap_or_else(|_| std::env::temp_dir().display().to_string());
        let data = fake(24);
        for dark in [false, true] {
            for (name, f) in [
                ("battery", draw_battery_chart as fn(&cairo::Context, i32, i32, &[Sample], bool)),
                ("sleep", draw_sleep_chart),
            ] {
                let (w, h) = (336, 230);
                let surface = cairo::ImageSurface::create(cairo::Format::ARgb32, w, h).unwrap();
                let cr = cairo::Context::new(&surface).unwrap();
                if dark { cr.set_source_rgb(0.14, 0.14, 0.14) } else { cr.set_source_rgb(1.0, 1.0, 1.0) }
                cr.paint().unwrap();
                f(&cr, w, h, &data, dark);
                let mut file = std::fs::File::create(format!("{dir}/{name}-{}.png", if dark { "dark" } else { "light" })).unwrap();
                surface.write_to_png(&mut file).unwrap();
            }
        }
    }
}
