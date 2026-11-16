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
use gtk::{cairo, gio, glib};

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
    current_ma: Option<f64>,
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

#[derive(Clone, Debug)]
struct SleepBoundary {
    phase: String,
    boot_id: String,
    t: i64,
    boottime: f64,
    monotonic: f64,
    capacity: Option<f64>,
    status: String,
    msoc: Option<f64>,
    mirror: Option<f64>,
}

fn parse_boundaries(input: impl Read) -> Result<Vec<SleepBoundary>, String> {
    let mut rdr = csv::ReaderBuilder::new().flexible(true).from_reader(input);
    let headers = rdr.headers().map_err(|e| e.to_string())?.clone();
    let idx = |name: &str| headers.iter().position(|h| h == name);
    let mut out = Vec::new();
    for record in rdr.records().flatten() {
        let get = |name: &str| idx(name).and_then(|i| record.get(i)).unwrap_or("");
        let (Ok(t), Some(boottime), Some(monotonic)) = (
            chrono::DateTime::parse_from_rfc3339(get("wall_utc")),
            num(get("boottime_s")), num(get("monotonic_s")),
        ) else { continue };
        out.push(SleepBoundary {
            phase: get("phase").into(), boot_id: get("boot_id").into(),
            t: t.timestamp(), boottime, monotonic,
            capacity: num(get("capacity_pct")), status: get("status").into(),
            msoc: num(get("msoc")), mirror: num(get("msoc_mirror")),
        });
    }
    Ok(out)
}

fn last_sleep_pair(records: &[SleepBoundary], cutoff: Option<i64>, now: i64) -> Option<(SleepBoundary, SleepBoundary, f64)> {
    let mut pre: Option<&SleepBoundary> = None;
    let mut last = None;
    for record in records {
        if record.phase == "pre" { pre = Some(record); }
        else if record.phase == "post" {
            if let Some(start) = pre.take() {
                let elapsed = record.boottime - start.boottime;
                let awake = record.monotonic - start.monotonic;
                let suspended = elapsed - awake;
                let boot_valid = start.boot_id.len() == 36 && start.boot_id.chars().enumerate()
                    .all(|(i, c)| if [8, 13, 18, 23].contains(&i) { c == '-' } else { c.is_ascii_hexdigit() });
                if boot_valid && start.boot_id == record.boot_id && start.t <= record.t && record.t <= now
                    && cutoff.map_or(true, |c| start.t >= c)
                    && elapsed > 0.0 && awake >= 0.0 && suspended > 0.05 && suspended <= elapsed {
                    last = Some((start.clone(), record.clone(), suspended));
                }
            }
        }
    }
    last
}

fn sleep_pair_text(start: &SleepBoundary, end: &SleepBoundary, seconds: f64) -> String {
    let level = |v: Option<f64>| v.map(|n| format!("{n:.0} %")).unwrap_or_else(|| "indisponible".into());
    let mut text = format!("{} · {}\nBatterie : {} → {}", local_time(end.t, "%d/%m %H:%M"), human_duration(seconds), level(start.capacity), level(end.capacity));
    if start.status != "Discharging" || end.status != "Discharging" {
        text.push_str("\nCharge ou état incertain à une borne : comparaison limitée.");
    }
    if let (Some(a), Some(am), Some(b), Some(bm)) = (start.msoc, start.mirror, end.msoc, end.mirror) {
        if a == am && b == bm && (0.0..=255.0).contains(&a) && (0.0..=255.0).contains(&b) {
            text.push_str(&format!("\nJauge brute : {a:.0} → {b:.0} / 255"));
        }
    }
    text
}

/// Lit le CSV par NOM de colonne : l'ordre des colonnes importe peu.
fn parse_samples(input: impl Read) -> Result<Vec<Sample>, String> {
    let mut rdr = csv::ReaderBuilder::new().flexible(true).from_reader(input);
    let headers = rdr.headers().map_err(|e| e.to_string())?.clone();
    let idx = |name: &str| headers.iter().position(|h| h == name);
    let (i_ts, i_reason, i_status) = (idx("timestamp"), idx("reason"), idx("status"));
    let (i_cap, i_pow, i_temp) = (idx("capacity_pct"), idx("power_w"), idx("temp_c"));
    let i_current = idx("current_ma");
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
            current_ma: num(get(i_current)),
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

fn cpu_entries(raw: &str) -> Vec<(String, u64)> {
    raw.split('|').filter_map(|entry| {
        let (name, duration) = entry.rsplit_once("(+")?;
        let millis = duration.strip_suffix("ms)")?.parse::<u64>().ok()?;
        if name.trim().is_empty() { return None; }
        Some((name.to_string(), millis))
    }).collect()
}

fn cpu_totals(samples: &[Sample]) -> Vec<(String, u64)> {
    let mut totals = std::collections::HashMap::<String, u64>::new();
    for pair in samples.windows(2) {
        let sample = &pair[1];
        if sample.reason == "start" { continue; }
        for (name, millis) in cpu_entries(&sample.procs) {
            let entry = totals.entry(name).or_default();
            *entry = entry.saturating_add(millis);
        }
    }
    let mut ranked: Vec<_> = totals.into_iter().collect();
    ranked.sort_by(|a, b| b.1.cmp(&a.1).then_with(|| a.0.cmp(&b.0)));
    ranked.truncate(5);
    ranked
}

/// Un relevé « resume » est pris au réveil : son courant est naturellement élevé,
/// il ne reflète pas la consommation pendant le sommeil.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum PowerFlow { Charge, Discharge, Unknown }

fn power_flow(s: &Sample) -> PowerFlow {
    match (s.status.as_str(), s.current_ma) {
        ("Charging", Some(current)) if current > 0.0 => PowerFlow::Charge,
        ("Discharging", Some(current)) if current < 0.0 => PowerFlow::Discharge,
        _ => PowerFlow::Unknown,
    }
}

fn is_screen_off_discharge(s: &Sample) -> bool {
    s.screen_on == Some(false) && power_flow(s) == PowerFlow::Discharge && s.reason != "resume"
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
const C_CHARGE: Rgb = (0.18, 0.72, 0.38);
const C_DISCHARGE: Rgb = (0.95, 0.42, 0.00);
/// Temps de suspension mesuré : une barre par intervalle.
const C_SUSPEND: Rgb = (0.21, 0.52, 0.89);


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

fn power_polyline(cr: &cairo::Context, p: &Plot, data: &[Sample], hi: f64, flow: PowerFlow, color: Rgb) {
    cr.set_source_rgb(color.0, color.1, color.2);
    cr.set_line_width(2.0);
    cr.set_line_join(cairo::LineJoin::Round);
    let mut previous = None;
    for sample in data {
        let value = sample.power_w.filter(|_| power_flow(sample) == flow);
        if let Some(value) = value {
            let (x, y) = (p.px(sample.t), p.py(value, 0.0, hi));
            if previous.map_or(false, |t| continuous_samples(t, sample.t)) { cr.line_to(x, y); }
            else { cr.move_to(x, y); }
            previous = Some(sample.t);
        } else {
            previous = None;
        }
    }
    let _ = cr.stroke();
}

fn no_data(cr: &cairo::Context, w: i32, h: i32, fg: Rgb) {
    text(cr, "Pas assez de données pour cette période", w as f64 / 2.0, h as f64 / 2.0, 0.5, fg, 0.7);
}

fn time_bounds(data: &[Sample], hours: Option<i64>, now: i64) -> Option<(i64, i64)> {
    if let Some(hours) = hours {
        return Some((now - hours * 3600, now));
    }
    Some((data.first()?.t, data.last()?.t))
}

fn complete_interval(sample: &Sample, cutoff: Option<i64>) -> bool {
    match (cutoff, sample.interval_s) {
        (None, _) => true,
        (Some(start), Some(seconds)) if seconds.is_finite() && seconds >= 0.0 =>
            sample.t - (seconds.ceil() as i64) >= start,
        _ => false,
    }
}

/// Graphique 1 : batterie (%, axe gauche) et puissance (W, axe droit).
fn draw_battery_chart(cr: &cairo::Context, w: i32, h: i32, data: &[Sample], dark: bool, hours: Option<i64>, now: i64) {
    let fg = fg_color(dark);
    if data.len() < 2 {
        return no_data(cr, w, h, fg);
    }
    let (start, end) = time_bounds(data, hours, now).unwrap();
    let p = Plot::new(w, h, start, end);
    let max_p = data.iter().filter_map(|s| s.power_w).fold(0.0_f64, f64::max);
    let p_hi = ((max_p / 2.0).ceil() * 2.0).max(2.0);

    draw_frame(cr, &p, fg, (0.0, 100.0, C_BATT), Some((0.0, p_hi, fg)));
    legend(cr, p.x0, 16.0, &[("Batterie %", C_BATT), ("Charge", C_CHARGE), ("Décharge", C_DISCHARGE)], fg);

    let cap: Vec<_> = data.iter().filter_map(|s| s.capacity.map(|v| (s.t, v))).collect();
    polyline(cr, &p, &cap, 0.0, 100.0, C_BATT);
    power_polyline(cr, &p, data, p_hi, PowerFlow::Charge, C_CHARGE);
    power_polyline(cr, &p, data, p_hi, PowerFlow::Discharge, C_DISCHARGE);
}

/// Graphique 2 : temps de suspension si disponible, sans preuve de veille profonde.
fn draw_sleep_chart(cr: &cairo::Context, w: i32, h: i32, data: &[Sample], dark: bool, hours: Option<i64>, now: i64) {
    let fg = fg_color(dark);
    if data.len() < 2 {
        return no_data(cr, w, h, fg);
    }
    let (start, end) = time_bounds(data, hours, now).unwrap();
    let p = Plot::new(w, h, start, end);
    if !data.iter().any(|s| s.interval_s.is_some()) {
        return no_data(cr, w, h, fg);
    }
    let max_s = data
        .iter()
        .filter(|s| complete_interval(s, hours.map(|h| now - h * 3600)))
        .filter_map(suspend_seconds)
        .fold(0.0_f64, f64::max);
    if max_s <= 0.0 {
        return text(cr, "Aucune suspension détectée", w as f64 / 2.0, h as f64 / 2.0, 0.5, fg, 0.7);
    }
    let max_minutes = (max_s / 60.0).ceil().max(1.0);
    draw_frame(cr, &p, fg, (0.0, max_minutes, C_SUSPEND), None);
    legend(cr, p.x0, 16.0, &[("Suspension (min)", C_SUSPEND)], fg);

    // One visible bar per recorded suspension, placed at the end of its interval.
    for pair in data.windows(2) {
        let (xa, xb) = (p.px(pair[0].t), p.px(pair[1].t));
        let width = (xb - xa).clamp(7.0, 14.0).min(p.x1 - p.x0);
        let interval = pair[1].interval_s.unwrap_or(0.0);
        let suspended = suspend_seconds(&pair[1]).unwrap_or(0.0);
        if interval <= 0.0 || suspended <= 0.0 || !complete_interval(&pair[1], hours.map(|h| now - h * 3600)) {
            continue;
        }
        let y_susp = p.py(suspended.min(interval) / 60.0, 0.0, max_minutes);
        let x = (xb - width / 2.0).clamp(p.x0, p.x1 - width);
        cr.set_source_rgb(C_SUSPEND.0, C_SUSPEND.1, C_SUSPEND.2);
        cr.rectangle(x, y_susp, width, p.y1 - y_susp);
        let _ = cr.fill();
    }
}

// ───────────────────────── Interface ─────────────────────────

struct Ui {
    all: RefCell<Vec<Sample>>,
    view: Rc<RefCell<Vec<Sample>>>,
    hours: Rc<Cell<Option<i64>>>,
    monitors: RefCell<Vec<gio::FileMonitor>>,
    info: gtk::Label,
    latest: gtk::Label,
    cpu_summary: gtk::Label,
    sleep_summary: gtk::Label,
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
            .filter(|s| s.t <= now && cutoff.map_or(true, |c| s.t >= c))
            .cloned()
            .collect();

        let boundaries = fs::File::open("/var/lib/battery-diag/sleep-boundaries.csv")
            .ok().and_then(|f| parse_boundaries(f).ok()).unwrap_or_default();
        if let Some((start, end, seconds)) = last_sleep_pair(&boundaries, cutoff, now) {
            self.sleep_summary.set_text(&sleep_pair_text(&start, &end, seconds));
        } else {
            self.sleep_summary.set_text("Aucune veille avec bornes complètes sur cette période.");
        }

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
            let entries = cpu_totals(&view);
            if entries.is_empty() {
                self.cpu_summary.set_text("Aucune activité CPU disponible sur cette période.");
            } else {
                let lines: Vec<String> = entries.iter().map(|(name, ms)| format!("{name}  ·  {:.2} s CPU", *ms as f64 / 1000.0)).collect();
                self.cpu_summary.set_text(&lines.join("\n"));
            }
        } else {
            self.latest.set_text("Aucun relevé sur cette période");
            self.cpu_summary.set_text("Aucune activité CPU disponible.");
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
        let suspend_total: f64 = view.iter().filter(|s| complete_interval(s, cutoff)).filter_map(suspend_seconds).sum();

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

fn live_number(name: &str) -> Option<f64> {
    let path = format!("/sys/class/power_supply/qcom-battery/{name}");
    fs::read_to_string(path).ok().and_then(|s| num(&s))
}

fn internal_screen_on() -> bool {
    let on = fs::read_dir("/sys/class/drm").ok().into_iter().flatten().flatten().any(|entry| {
        entry.file_name().to_string_lossy().contains("DSI") &&
            fs::read_to_string(entry.path().join("dpms")).ok().map_or(false, |v| v.trim().eq_ignore_ascii_case("on"))
    });
    let lit = fs::read_dir("/sys/class/backlight").ok().into_iter().flatten().flatten().any(|entry| {
        fs::read_to_string(entry.path().join("actual_brightness")).ok()
            .and_then(|v| v.trim().parse::<u64>().ok()).map_or(false, |v| v > 0)
    });
    on && lit
}

fn live_allowed(selected: bool, focused: bool, unlocked: bool, screen_on: bool) -> bool {
    selected && focused && unlocked && screen_on
}

type CpuSnapshot = std::collections::HashMap<(u32, u64), (String, u64)>;

fn process_cpu_snapshot() -> CpuSnapshot {
    let mut snapshot = CpuSnapshot::new();
    let Ok(entries) = fs::read_dir("/proc") else { return snapshot };
    for entry in entries.flatten() {
        let Some(pid) = entry.file_name().to_str().and_then(|s| s.parse::<u32>().ok()) else { continue };
        let Ok(stat) = fs::read_to_string(entry.path().join("stat")) else { continue };
        let (Some(open), Some(close)) = (stat.find('('), stat.rfind(')')) else { continue };
        let fields: Vec<&str> = stat[close + 1..].split_whitespace().collect();
        let (Some(user), Some(system), Some(start)) = (
            fields.get(11).and_then(|v| v.parse::<u64>().ok()),
            fields.get(12).and_then(|v| v.parse::<u64>().ok()),
            fields.get(19).and_then(|v| v.parse::<u64>().ok()),
        ) else { continue };
        snapshot.insert((pid, start), (stat[open + 1..close].to_string(), user.saturating_add(system)));
    }
    snapshot
}

fn live_cpu_ranking(previous: &CpuSnapshot, current: &CpuSnapshot) -> Vec<(String, u32, u64)> {
    let mut ranked: Vec<_> = current.iter().filter_map(|(key, (name, ticks))| {
        let old = previous.get(key)?.1;
        let delta = ticks.checked_sub(old)?;
        if delta == 0 { return None; }
        Some((name.clone(), key.0, delta))
    }).collect();
    ranked.sort_by(|a, b| b.2.cmp(&a.2).then_with(|| a.1.cmp(&b.1)));
    ranked.truncate(10);
    ranked
}

struct LiveView {
    selected: Cell<bool>,
    focused: Cell<bool>,
    unlocked: Cell<bool>,
    timer: RefCell<Option<glib::SourceId>>,
    lock_proxy: RefCell<Option<gio::DBusProxy>>,
    status: gtk::Label,
    current: gtk::Label,
    voltage: gtk::Label,
    power: gtk::Label,
    temperature: gtk::Label,
    cpu: gtk::Label,
    cpu_previous: RefCell<Option<CpuSnapshot>>,
    ticks_per_second: Option<f64>,
}

impl LiveView {
    fn stop(&self) {
        if let Some(id) = self.timer.borrow_mut().take() { id.remove(); }
        self.cpu_previous.borrow_mut().take();
    }

    fn update(&self) {
        let capacity = live_number("capacity");
        let status = fs::read_to_string("/sys/class/power_supply/qcom-battery/status").unwrap_or_default();
        let state = match status.trim() {
            "Charging" => "En charge", "Discharging" => "Sur batterie", "Full" => "Charge terminée",
            "Not charging" => "Charge arrêtée", _ => "État indisponible",
        };
        self.status.set_text(&format!("{} · {}", capacity.map(|v| format!("{v:.0} %")).unwrap_or_else(|| "– %".into()), state));
        let current = live_number("current_now");
        let voltage = live_number("voltage_now");
        self.current.set_text(&current.map(|v| format!("{:+.0} mA", v / 1000.0)).unwrap_or_else(|| "N/A".into()));
        self.voltage.set_text(&voltage.map(|v| format!("{:.2} V", v / 1_000_000.0)).unwrap_or_else(|| "N/A".into()));
        self.power.set_text(&match (current, voltage) {
            (Some(a), Some(v)) => format!("{:.2} W", (a * v).abs() / 1_000_000_000_000.0),
            _ => "N/A".into(),
        });
        self.temperature.set_text(&live_number("temp").map(|v| format!("{:.1} °C", v / 10.0)).unwrap_or_else(|| "N/A".into()));
        let current_cpu = process_cpu_snapshot();
        let mut previous = self.cpu_previous.borrow_mut();
        match (previous.as_ref(), self.ticks_per_second) {
            (Some(old), Some(hz)) if !current_cpu.is_empty() => {
                let ranking = live_cpu_ranking(old, &current_cpu);
                if ranking.is_empty() { self.cpu.set_text("Aucune activité CPU mesurable sur cet intervalle."); }
                else {
                    let lines: Vec<String> = ranking.iter().map(|(name, pid, ticks)| format!("{name} ({pid}) · {:.2} s CPU", *ticks as f64 / hz)).collect();
                    self.cpu.set_text(&lines.join("\n"));
                }
            }
            _ => self.cpu.set_text("Calcul en cours : attendre le prochain relevé."),
        }
        *previous = Some(current_cpu);
    }

    fn sync(self: &Rc<Self>) {
        if !live_allowed(self.selected.get(), self.focused.get(), self.unlocked.get(), internal_screen_on()) {
            self.stop();
            return;
        }
        if self.timer.borrow().is_some() { return; }
        self.update();
        let weak = Rc::downgrade(self);
        let id = glib::timeout_add_local(std::time::Duration::from_secs(5), move || {
            let Some(live) = weak.upgrade() else { return glib::ControlFlow::Break };
            if !live_allowed(live.selected.get(), live.focused.get(), live.unlocked.get(), internal_screen_on()) {
                live.timer.borrow_mut().take();
                return glib::ControlFlow::Break;
            }
            live.update();
            glib::ControlFlow::Continue
        });
        *self.timer.borrow_mut() = Some(id);
    }

    fn refresh_lock_state(self: &Rc<Self>, proxy: &gio::DBusProxy) {
        let unlocked = proxy.call_sync("GetActive", None, gio::DBusCallFlags::NONE, 1000, gio::Cancellable::NONE)
            .ok().and_then(|v| v.get::<(bool,)>().map(|(active,)| !active)).unwrap_or(false);
        self.unlocked.set(unlocked);
        self.sync();
    }
}

fn build_ui(app: &adw::Application) {
    let view = Rc::new(RefCell::new(Vec::<Sample>::new()));
    let hours = Rc::new(Cell::new(Some(24)));

    let chart1 = chart_area();
    let chart2 = chart_area();
    let v = view.clone();
    let range = hours.clone();
    chart1.set_draw_func(move |_, cr, w, h| {
        draw_battery_chart(cr, w, h, &v.borrow(), adw::StyleManager::default().is_dark(), range.get(), chrono::Utc::now().timestamp())
    });
    let v = view.clone();
    let range = hours.clone();
    chart2.set_draw_func(move |_, cr, w, h| {
        draw_sleep_chart(cr, w, h, &v.borrow(), adw::StyleManager::default().is_dark(), range.get(), chrono::Utc::now().timestamp())
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
    let cpu_summary = gtk::Label::new(None);
    cpu_summary.set_wrap(true);
    cpu_summary.set_xalign(0.0);
    let sleep_summary = gtk::Label::new(None);
    sleep_summary.set_wrap(true);
    sleep_summary.set_xalign(0.0);

    let ui = Rc::new(Ui {
        all: RefCell::new(Vec::new()),
        view,
        hours,
        monitors: RefCell::new(Vec::new()),
        info: info.clone(),
        latest: latest.clone(),
        cpu_summary: cpu_summary.clone(),
        sleep_summary: sleep_summary.clone(),
        v_power,
        v_suspend,
        v_proof,
        v_temp,
        list: list.clone(),
        chart1: chart1.clone(),
        chart2: chart2.clone(),
    });

    // A directory monitor follows both appends and CSV rotation without polling
    // or waking a suspended device. Coalesce bursts from one CSV write.
    for (directory, prefix) in [(data_dir(), "discharge_diag.csv"), (PathBuf::from("/var/lib/battery-diag"), "sleep-boundaries.csv")] {
      if let Ok(monitor) = gio::File::for_path(directory)
        .monitor_directory(gio::FileMonitorFlags::NONE, gio::Cancellable::NONE) {
        let weak_ui = Rc::downgrade(&ui);
        let pending = Rc::new(Cell::new(false));
        monitor.connect_changed(move |_, file, other, _| {
            let relevant = |f: &gio::File| f.basename()
                .map(|name| name.to_string_lossy().starts_with(prefix))
                .unwrap_or(false);
            if !relevant(file) && !other.map(relevant).unwrap_or(false) { return; }
            if pending.replace(true) { return; }
            let weak_ui = weak_ui.clone();
            let pending = pending.clone();
            glib::timeout_add_local_once(std::time::Duration::from_millis(400), move || {
                pending.set(false);
                if let Some(ui) = weak_ui.upgrade() { ui.reload(); }
            });
        });
        ui.monitors.borrow_mut().push(monitor);
      }
    }

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
    content.append(&section("Activité CPU observée", &cpu_summary));
    let cpu_note = gtk::Label::new(Some("Somme partielle sur la période : seuls les deux premiers processus de chaque relevé sont conservés, tâches système comprises. Ce n'est pas une consommation en mAh."));
    cpu_note.add_css_class("caption");
    cpu_note.add_css_class("dim-label");
    cpu_note.set_wrap(true);
    cpu_note.set_xalign(0.0);
    content.append(&cpu_note);
    content.append(&section("Batterie et puissance (W)", &chart1));
    let power_note = gtk::Label::new(Some("Vert : puissance reçue par la batterie. Orange : puissance fournie par la batterie. En charge, ce n'est pas la consommation totale du téléphone. Les valeurs incertaines et les périodes sans relevé ne sont pas reliées."));
    power_note.add_css_class("caption");
    power_note.add_css_class("dim-label");
    power_note.set_wrap(true);
    power_note.set_xalign(0.0);
    content.append(&power_note);
    content.append(&section("Temps de suspension", &chart2));
    let sleep_note = gtk::Label::new(Some("Chaque barre indique les minutes de suspension entre deux relevés. Pendant la veille, le téléphone ne prend pas de mesures intermédiaires ; la durée est calculée au réveil. Les intervalles incomplets sont exclus."));
    sleep_note.add_css_class("caption");
    sleep_note.add_css_class("dim-label");
    sleep_note.set_wrap(true);
    sleep_note.set_xalign(0.0);
    content.append(&sleep_note);
    content.append(&section("Dernière veille mesurée", &sleep_summary));
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

    let live_status = gtk::Label::new(Some("Mesure en attente"));
    live_status.add_css_class("title-2");
    live_status.set_xalign(0.0);
    let (live_current_card, live_current) = card("Courant batterie");
    let (live_voltage_card, live_voltage) = card("Tension batterie");
    let (live_power_card, live_power) = card("Puissance batterie");
    let (live_temp_card, live_temp) = card("Température");
    let live_cards = gtk::Grid::builder().column_spacing(8).row_spacing(8).column_homogeneous(true).build();
    live_cards.attach(&live_current_card, 0, 0, 1, 1);
    live_cards.attach(&live_voltage_card, 1, 0, 1, 1);
    live_cards.attach(&live_power_card, 0, 1, 1, 1);
    live_cards.attach(&live_temp_card, 1, 1, 1, 1);
    let live_note = gtk::Label::new(Some("Lecture toutes les 5 secondes uniquement sur cette page, au premier plan et écran allumé. Le courant signé indique le sens des échanges avec la batterie ; la puissance n'est pas la consommation par application."));
    live_note.set_wrap(true);
    live_note.set_xalign(0.0);
    live_note.add_css_class("dim-label");
    let live_cpu = gtk::Label::new(Some("Calcul en cours : attendre le prochain relevé."));
    live_cpu.set_wrap(true);
    live_cpu.set_xalign(0.0);
    let live_cpu_note = gtk::Label::new(Some("Temps CPU sur le dernier intervalle : jusqu'à 10 processus, tâches système comprises. Les nouveaux processus apparaissent au relevé suivant. Ce n'est pas une mesure en mAh."));
    live_cpu_note.set_wrap(true);
    live_cpu_note.set_xalign(0.0);
    live_cpu_note.add_css_class("caption");
    live_cpu_note.add_css_class("dim-label");
    let hz = unsafe { libc::sysconf(libc::_SC_CLK_TCK) };
    let live = Rc::new(LiveView {
        selected: Cell::new(false), focused: Cell::new(false), unlocked: Cell::new(false),
        timer: RefCell::new(None), lock_proxy: RefCell::new(None),
        status: live_status.clone(), current: live_current, voltage: live_voltage,
        power: live_power, temperature: live_temp, cpu: live_cpu.clone(),
        cpu_previous: RefCell::new(None), ticks_per_second: if hz > 0 { Some(hz as f64) } else { None },
    });
    if let Ok(proxy) = gio::DBusProxy::for_bus_sync(
        gio::BusType::Session, gio::DBusProxyFlags::NONE, None,
        "org.gnome.ScreenSaver", "/org/gnome/ScreenSaver", "org.gnome.ScreenSaver", gio::Cancellable::NONE,
    ) {
        live.refresh_lock_state(&proxy);
        let weak = Rc::downgrade(&live);
        proxy.connect_local("g-signal", false, move |args| {
            let signal = args.get(2).and_then(|v| v.get::<String>().ok());
            if signal.as_deref() == Some("ActiveChanged") {
                if let (Some(live), Some(params)) = (weak.upgrade(), args.get(3).and_then(|v| v.get::<glib::Variant>().ok())) {
                    if let Some((locked,)) = params.get::<(bool,)>() {
                        live.unlocked.set(!locked);
                        live.sync();
                    }
                }
            }
            None
        });
        let weak = Rc::downgrade(&live);
        proxy.connect_notify_local(Some("g-name-owner"), move |proxy, _| {
            if let Some(live) = weak.upgrade() { live.refresh_lock_state(proxy); }
        });
        *live.lock_proxy.borrow_mut() = Some(proxy);
    } else {
        live_status.set_text("Temps réel indisponible : état de l'écran inconnu.");
    }
    let live_content = gtk::Box::new(gtk::Orientation::Vertical, 16);
    live_content.set_margin_top(18);
    live_content.set_margin_bottom(18);
    live_content.set_margin_start(12);
    live_content.set_margin_end(12);
    live_content.append(&live_status);
    live_content.append(&live_cards);
    live_content.append(&live_note);
    live_content.append(&section("Activité CPU en direct", &live_cpu));
    live_content.append(&live_cpu_note);
    let live_scroll = gtk::ScrolledWindow::builder().child(&live_content).vexpand(true).build();

    let stack = gtk::Stack::new();
    stack.set_vexpand(true);
    stack.add_titled(&scroll, Some("history"), "Historique");
    stack.add_titled(&live_scroll, Some("live"), "Temps réel");
    {
        let live = live.clone();
        let history_refresh = refresh.clone();
        stack.connect_notify_local(Some("visible-child-name"), move |stack, _| {
            live.selected.set(stack.visible_child_name().as_deref() == Some("live"));
            history_refresh.set_visible(!live.selected.get());
            live.sync();
        });
    }
    let switcher = gtk::StackSwitcher::new();
    switcher.set_stack(Some(&stack));
    switcher.set_halign(gtk::Align::Center);
    switcher.set_margin_top(6);
    switcher.set_margin_bottom(6);
    let root = gtk::Box::new(gtk::Orientation::Vertical, 0);
    root.append(&header);
    root.append(&switcher);
    root.append(&stack);

    let window = adw::ApplicationWindow::builder()
        .application(app)
        .title("Diagnostic batterie")
        .default_width(360)
        .default_height(720)
        .content(&root)
        .build();

    {
        let live = live.clone();
        window.connect_is_active_notify(move |window| {
            live.focused.set(window.is_active());
            live.sync();
        });
    }

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
    fn power_direction_requires_status_and_current_to_agree() {
        let mut s = Sample { status: "Charging".into(), current_ma: Some(100.0), ..Default::default() };
        assert_eq!(power_flow(&s), PowerFlow::Charge);
        s.current_ma = Some(-100.0);
        assert_eq!(power_flow(&s), PowerFlow::Unknown);
        s.status = "Discharging".into();
        assert_eq!(power_flow(&s), PowerFlow::Discharge);
        s.current_ma = None;
        assert_eq!(power_flow(&s), PowerFlow::Unknown);
        s.current_ma = Some(0.0);
        assert_eq!(power_flow(&s), PowerFlow::Unknown);
    }

    #[test]
    fn cpu_ranking_parses_only_known_durations() {
        assert_eq!(cpu_entries("phosh(+1200ms)|gthd(+310ms)"), vec![("phosh".to_string(), 1200), ("gthd".to_string(), 310)]);
        assert!(cpu_entries("none|N/A|broken(+oopsms)").is_empty());
    }

    #[test]
    fn live_sampling_requires_visible_focused_lit_screen() {
        assert!(live_allowed(true, true, true, true));
        assert!(!live_allowed(false, true, true, true));
        assert!(!live_allowed(true, false, true, true));
        assert!(!live_allowed(true, true, false, true));
        assert!(!live_allowed(true, true, true, false));
    }

    #[test]
    fn live_cpu_ranking_limits_to_ten_and_ignores_reused_pids() {
        let mut old = CpuSnapshot::new();
        let mut new = CpuSnapshot::new();
        for pid in 1..=12 {
            old.insert((pid, 100), (format!("p{pid}"), 100));
            new.insert((pid, 100), (format!("p{pid}"), 100 + pid as u64));
        }
        old.insert((99, 1), ("old".into(), 10));
        new.insert((99, 2), ("new".into(), 900));
        let ranked = live_cpu_ranking(&old, &new);
        assert_eq!(ranked.len(), 10);
        assert_eq!(ranked[0], ("p12".to_string(), 12, 12));
        assert!(!ranked.iter().any(|(_, pid, _)| *pid == 99));
    }

    #[test]
    fn cpu_ranking_is_partial_and_skips_service_start() {
        let rows = vec![
            Sample { reason: "periodic".into(), procs: "a(+500ms)".into(), ..Default::default() },
            Sample { reason: "periodic".into(), procs: "a(+200ms)|b(+300ms)".into(), ..Default::default() },
            Sample { reason: "start".into(), procs: "a(+900000ms)".into(), ..Default::default() },
            Sample { reason: "periodic".into(), procs: "a(+150ms)".into(), ..Default::default() },
        ];
        assert_eq!(cpu_totals(&rows), vec![("a".to_string(), 350), ("b".to_string(), 300)]);
    }

    #[test]
    fn sleep_boundaries_are_paired_only_within_one_boot() {
        let csv = "phase,boot_id,wall_utc,boottime_s,monotonic_s,capacity_pct,status,msoc,msoc_mirror\n\
pre,12345678-1234-1234-1234-123456789abc,2026-11-16T06:00:00+00:00,100,90,80,Discharging,205,205\n\
post,12345678-1234-1234-1234-123456789abc,2026-11-16T06:05:00+00:00,400,100,79,Discharging,202,202\n";
        let rows = parse_boundaries(csv.as_bytes()).unwrap();
        let (start, end, seconds) = last_sleep_pair(&rows, None, i64::MAX).unwrap();
        assert_eq!(seconds, 290.0);
        let text = sleep_pair_text(&start, &end, seconds);
        assert!(text.contains("80 % → 79 %"));
        assert!(text.contains("205 → 202 / 255"));
        assert!(last_sleep_pair(&rows, Some(start.t + 1), i64::MAX).is_none());
        let mut changed_boot = rows.clone();
        changed_boot[1].boot_id = "boot2".into();
        assert!(last_sleep_pair(&changed_boot, None, i64::MAX).is_none());
        let mut missing_boot = rows.clone();
        missing_boot[0].boot_id = "N/A:2".into();
        missing_boot[1].boot_id = "N/A:2".into();
        assert!(last_sleep_pair(&missing_boot, None, i64::MAX).is_none());
        let mut plugged = end.clone();
        plugged.status = "Charging".into();
        assert!(sleep_pair_text(&start, &plugged, seconds).contains("comparaison limitée"));
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
    fn six_hour_window_is_not_stretched_to_samples() {
        let samples = vec![Sample { t: 99_000, ..Default::default() }, Sample { t: 99_900, ..Default::default() }];
        assert_eq!(time_bounds(&samples, Some(6), 100_000), Some((78_400, 100_000)));
        assert_eq!(time_bounds(&samples, None, 100_000), Some((99_000, 99_900)));
    }

    #[test]
    fn partial_suspend_interval_is_not_counted_in_short_window() {
        let sample = Sample { t: 1000, interval_s: Some(300.0), suspend_s: Some(200.0), ..Default::default() };
        assert!(complete_interval(&sample, Some(700)));
        assert!(!complete_interval(&sample, Some(701)));
        assert!(complete_interval(&sample, None));
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
                    capacity: Some(100.0 - 60.0 * f),
                    status: "Discharging".into(),
                    current_ma: Some(-250.0),
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
                ("battery", draw_battery_chart as fn(&cairo::Context, i32, i32, &[Sample], bool, Option<i64>, i64)),
                ("sleep", draw_sleep_chart),
            ] {
                let (w, h) = (336, 230);
                let surface = cairo::ImageSurface::create(cairo::Format::ARgb32, w, h).unwrap();
                let cr = cairo::Context::new(&surface).unwrap();
                if dark { cr.set_source_rgb(0.14, 0.14, 0.14) } else { cr.set_source_rgb(1.0, 1.0, 1.0) }
                cr.paint().unwrap();
                f(&cr, w, h, &data, dark, None, 1_800_086_400);
                let mut file = std::fs::File::create(format!("{dir}/{name}-{}.png", if dark { "dark" } else { "light" })).unwrap();
                surface.write_to_png(&mut file).unwrap();
            }
        }
    }
}
