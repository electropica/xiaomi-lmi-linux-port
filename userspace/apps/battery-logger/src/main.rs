//! battery-logger : journalise l'état électrique, système et noyau dans un CSV.
//!
//! Principe de sobriété : le programme dort 99 % du temps, bloqué sur un canal.
//! Il n'utilise AUCUNE horloge « alarme » : quand le téléphone passe en
//! suspend-to-RAM, ce programme est gelé avec lui et ne le réveille jamais.

use std::collections::HashMap;
use std::fmt::Display;
use std::fs::{self, OpenOptions};
use std::io::{self, BufRead, BufReader};
use std::os::fd::{AsRawFd, FromRawFd, OwnedFd};
use std::path::{Path, PathBuf};
use std::sync::mpsc::{self, Receiver, RecvTimeoutError, Sender, SyncSender};
use std::thread;
use std::time::{Duration, Instant};

const NA: &str = "N/A";
const SAMPLE_INTERVAL: Duration = Duration::from_secs(120);
const MIN_GAP: Duration = Duration::from_secs(5);
const MODEM_TIMEOUT: Duration = Duration::from_secs(4);

/// Colonnes du CSV (le viewer s'appuie sur ces noms exacts).
const HEADER: [&str; 30] = [
    "timestamp", "reason", "uptime_s", "status", "capacity_pct", "voltage_v",
    "current_ma", "current_avg_ma", "power_w", "cap_now", "cap_full", "cap_unit",
    "charge_counter_uah", "temp_c", "deep_sleep_pct", "load1", "cpu_freq_mhz",
    "brightness", "brightness_pct", "screen_on", "net", "top_procs",
    "wake_sources", "cpu_online", "cstate_name", "cstate_ms",
    "modem_signal_pct", "modem_tech", "interval_s", "suspend_s",
];

// ───────────────────────── Utilitaires de lecture ─────────────────────────

fn read_trim(path: impl AsRef<Path>) -> Option<String> {
    let s = fs::read_to_string(path).ok()?;
    let s = s.trim();
    if s.is_empty() { None } else { Some(s.to_string()) }
}

fn read_num<T: std::str::FromStr>(path: impl AsRef<Path>) -> Option<T> {
    read_trim(path)?.parse().ok()
}

/// Liste triée des entrées d'un dossier (vide si le dossier n'existe pas).
fn list_dir(path: &str) -> Vec<PathBuf> {
    let mut v: Vec<PathBuf> = fs::read_dir(path)
        .map(|rd| rd.flatten().map(|e| e.path()).collect())
        .unwrap_or_default();
    v.sort();
    v
}

fn fmt_f(v: Option<f64>, decimals: usize) -> String {
    v.map(|x| format!("{x:.decimals$}")).unwrap_or_else(|| NA.to_string())
}

fn fmt_any<T: Display>(v: Option<T>) -> String {
    v.map(|x| x.to_string()).unwrap_or_else(|| NA.to_string())
}

/// Évite de casser nos listes séparées par « | ».
fn clean(s: &str) -> String {
    s.chars().map(|c| if c == '|' || c.is_control() { '_' } else { c }).collect()
}

fn clock_secs(id: libc::clockid_t) -> Option<f64> {
    let mut ts = libc::timespec { tv_sec: 0, tv_nsec: 0 };
    // SAFETY: `ts` est une structure valide, vivante pendant l'appel.
    let rc = unsafe { libc::clock_gettime(id, &mut ts) };
    if rc == 0 { Some(ts.tv_sec as f64 + ts.tv_nsec as f64 / 1e9) } else { None }
}

// ───────────────────────── Batterie (power_supply) ─────────────────────────

/// Trouve dynamiquement la batterie du téléphone (nom différent selon le modèle).
fn find_battery() -> Option<PathBuf> {
    let dirs = list_dir("/sys/class/power_supply");
    let is_battery = |d: &PathBuf| {
        read_trim(d.join("type")).map_or(false, |t| t.eq_ignore_ascii_case("Battery"))
    };
    let is_system = |d: &PathBuf| {
        read_trim(d.join("scope")).map_or(true, |s| !s.eq_ignore_ascii_case("Device"))
    };
    dirs.iter()
        .find(|d| is_battery(d) && is_system(d) && d.join("capacity").exists())
        .or_else(|| dirs.iter().find(|d| is_battery(d)))
        .cloned()
}

#[derive(Default)]
struct Electrical {
    status: Option<String>,
    capacity: Option<i64>,
    voltage_v: Option<f64>,
    current_ma: Option<f64>,
    current_avg_ma: Option<f64>,
    power_w: Option<f64>,
    cap_now: Option<i64>,
    cap_full: Option<i64>,
    cap_unit: Option<&'static str>,
    charge_counter_uah: Option<i64>,
    temp_c: Option<f64>,
}

fn read_electrical(dir: &Path) -> Electrical {
    let voltage_v = read_num::<f64>(dir.join("voltage_now")).map(|uv| uv / 1e6);
    let current_ua = read_num::<f64>(dir.join("current_now"));
    // P = U × |I| : le signe du courant dépend du pilote, la puissance reste positive.
    let power_w = match (voltage_v, current_ua) {
        (Some(v), Some(i)) => Some(v * i.abs() / 1e6),
        _ => None,
    };
    let (cap_now, cap_full, cap_unit) =
        if let Some(n) = read_num::<i64>(dir.join("charge_now")) {
            (Some(n), read_num::<i64>(dir.join("charge_full")), Some("uAh"))
        } else if let Some(n) = read_num::<i64>(dir.join("energy_now")) {
            (Some(n), read_num::<i64>(dir.join("energy_full")), Some("uWh"))
        } else {
            (None, None, None)
        };
    Electrical {
        status: read_trim(dir.join("status")),
        capacity: read_num(dir.join("capacity")),
        voltage_v,
        current_ma: current_ua.map(|x| x / 1e3),
        current_avg_ma: read_num::<f64>(dir.join("current_avg")).map(|x| x / 1e3),
        power_w,
        cap_now,
        cap_full,
        cap_unit,
        charge_counter_uah: read_num(dir.join("charge_counter")),
        temp_c: read_num::<f64>(dir.join("temp")).map(|t| t / 10.0),
    }
}

fn read_status_only() -> Option<String> {
    find_battery().and_then(|d| read_trim(d.join("status")))
}

// ───────────────────────── Écran ─────────────────────────

/// (brightness brute, brightness %, écran allumé ?)
fn read_screen() -> (Option<i64>, Option<f64>, Option<bool>) {
    let mut raw = None;
    let mut pct = None;
    let mut backlight_on = None;
    if let Some(dir) = list_dir("/sys/class/backlight").into_iter().next() {
        raw = read_num::<i64>(dir.join("brightness"));
        let max = read_num::<f64>(dir.join("max_brightness"));
        if let (Some(b), Some(m)) = (raw, max) {
            if m > 0.0 { pct = Some(b as f64 / m * 100.0); }
        }
        // bl_power : 0 = allumé, autre valeur = éteint.
        let power_ok = read_num::<i64>(dir.join("bl_power")).map_or(true, |p| p == 0);
        backlight_on = raw.map(|b| b > 0 && power_ok);
    }
    // Second avis : l'état DPMS de la dalle interne (si exposé par le pilote DRM).
    let mut drm_on: Option<bool> = None;
    for dir in list_dir("/sys/class/drm") {
        let Some(name) = dir.file_name().map(|n| n.to_string_lossy().to_string()) else { continue };
        if !["DSI", "eDP", "LVDS", "DPI"].iter().any(|k| name.contains(k)) { continue; }
        if let Some(d) = read_trim(dir.join("dpms")) {
            drm_on = Some(drm_on.unwrap_or(false) || d.eq_ignore_ascii_case("on"));
        }
    }
    let on = match (drm_on, backlight_on) {
        (Some(d), Some(b)) => Some(d && b),
        (Some(d), None) => Some(d),
        (None, b) => b,
    };
    (raw, pct, on)
}

fn read_net() -> String {
    let items: Vec<String> = list_dir("/sys/class/net")
        .into_iter()
        .filter_map(|d| {
            let name = d.file_name()?.to_string_lossy().to_string();
            if name == "lo" { return None; }
            Some(format!("{}={}", clean(&name), read_trim(d.join("operstate")).unwrap_or_else(|| NA.into())))
        })
        .collect();
    if items.is_empty() { NA.to_string() } else { items.join("|") }
}

fn count_online_cpus() -> usize {
    list_dir("/sys/devices/system/cpu")
        .into_iter()
        .filter(|d| {
            let n = d.file_name().map(|n| n.to_string_lossy().to_string()).unwrap_or_default();
            n.len() > 3 && n.starts_with("cpu") && n[3..].chars().all(|c| c.is_ascii_digit())
        })
        // cpu0 n'a souvent pas de fichier « online » : il est alors toujours actif.
        .filter(|d| read_num::<i64>(d.join("online")).map_or(true, |v| v == 1))
        .count()
}

// ───────────────────────── Processus ─────────────────────────

/// pid -> (nom, ticks CPU cumulés utime+stime)
fn read_proc_ticks() -> HashMap<u32, (String, u64)> {
    let mut map = HashMap::new();
    let Ok(rd) = fs::read_dir("/proc") else { return map };
    for entry in rd.flatten() {
        let Some(pid) = entry.file_name().to_str().and_then(|s| s.parse::<u32>().ok()) else { continue };
        let Ok(stat) = fs::read_to_string(entry.path().join("stat")) else { continue };
        // Le nom est entre parenthèses et peut contenir des espaces : on cherche la dernière « ) ».
        let (Some(open), Some(close)) = (stat.find('('), stat.rfind(')')) else { continue };
        let comm = stat[open + 1..close].to_string();
        let rest: Vec<&str> = stat[close + 1..].split_whitespace().collect();
        // Après « ) » : [0]=état … [11]=utime, [12]=stime.
        let (Some(u), Some(s)) = (rest.get(11), rest.get(12)) else { continue };
        let ticks = u.parse::<u64>().unwrap_or(0) + s.parse::<u64>().unwrap_or(0);
        map.insert(pid, (comm, ticks));
    }
    map
}

// ───────────────────────── Modem (ModemManager via D-Bus) ─────────────────────────

struct ModemInfo {
    signal: Option<u32>,
    tech: String,
}

impl ModemInfo {
    fn unavailable() -> Self {
        ModemInfo { signal: None, tech: NA.to_string() }
    }
}

fn tech_label(mask: u32) -> &'static str {
    if mask & (1 << 15) != 0 {
        "5G"
    } else if mask & ((1 << 14) | (1 << 16) | (1 << 17)) != 0 {
        "4G"
    } else if mask & (0x3E0 | 0x3C00) != 0 {
        "3G"
    } else if mask & 0x1E != 0 {
        "2G"
    } else {
        "Aucun"
    }
}

fn query_modem(conn: &zbus::blocking::Connection) -> zbus::Result<ModemInfo> {
    // On vérifie que ModemManager tourne déjà, pour ne JAMAIS le démarrer par activation D-Bus.
    let dbus = zbus::blocking::fdo::DBusProxy::new(conn)?;
    let name = zbus::names::BusName::try_from("org.freedesktop.ModemManager1")?;
    if !dbus.name_has_owner(name)? {
        return Ok(ModemInfo::unavailable());
    }
    let om = zbus::blocking::fdo::ObjectManagerProxy::builder(conn)
        .destination("org.freedesktop.ModemManager1")?
        .path("/org/freedesktop/ModemManager1")?
        .build()?;
    for (_path, ifaces) in om.get_managed_objects()? {
        let Some(props) = ifaces.get("org.freedesktop.ModemManager1.Modem") else { continue };
        let signal = props
            .get("SignalQuality")
            .and_then(|v| <(u32, bool)>::try_from(v.try_clone().ok()?).ok())
            .map(|(pct, _recent)| pct);
        let tech = props
            .get("AccessTechnologies")
            .and_then(|v| u32::try_from(v.try_clone().ok()?).ok())
            .map(tech_label)
            .unwrap_or("Aucun");
        return Ok(ModemInfo { signal, tech: tech.to_string() });
    }
    Ok(ModemInfo { signal: None, tech: "Aucun".to_string() })
}

/// Le modem est interrogé dans un thread à part, avec délai maximal :
/// un ModemManager bloqué ne peut donc jamais bloquer le logger.
struct ModemClient {
    req_tx: SyncSender<u64>,
    res_rx: Receiver<(u64, ModemInfo)>,
    next_id: u64,
}

impl ModemClient {
    fn spawn() -> Self {
        let (req_tx, req_rx) = mpsc::sync_channel::<u64>(1);
        let (res_tx, res_rx) = mpsc::channel::<(u64, ModemInfo)>();
        let _ = thread::Builder::new().name("modem".into()).spawn(move || {
            let mut conn: Option<zbus::blocking::Connection> = None;
            while let Ok(id) = req_rx.recv() {
                if conn.is_none() {
                    conn = zbus::blocking::Connection::system().ok();
                }
                let info = match conn.as_ref().map(query_modem) {
                    Some(Ok(info)) => info,
                    Some(Err(_)) => {
                        conn = None; // on retentera une connexion neuve au prochain relevé
                        ModemInfo::unavailable()
                    }
                    None => ModemInfo::unavailable(),
                };
                if res_tx.send((id, info)).is_err() { break; }
            }
        });
        ModemClient { req_tx, res_rx, next_id: 0 }
    }

    fn request(&mut self) -> u64 {
        self.next_id += 1;
        let _ = self.req_tx.try_send(self.next_id); // si le worker est occupé, on ignore
        self.next_id
    }

    fn collect(&self, id: u64) -> ModemInfo {
        let deadline = Instant::now() + MODEM_TIMEOUT;
        loop {
            let left = deadline.saturating_duration_since(Instant::now());
            match self.res_rx.recv_timeout(left) {
                Ok((rid, info)) if rid == id => return info,
                Ok(_) => continue, // réponse périmée d'un relevé précédent
                Err(_) => return ModemInfo::unavailable(),
            }
        }
    }
}

// ───────────────────────── Collecteur ─────────────────────────

struct Collector {
    battery: Option<PathBuf>,
    prev_clocks: Option<(f64, f64)>, // (BOOTTIME, MONOTONIC)
    prev_ticks: HashMap<u32, u64>,
    prev_wake: HashMap<String, u64>,
    prev_cstate_us: Option<u64>,
    modem: ModemClient,
    clk_tck: f64,
}

fn clock_interval(previous: Option<(f64, f64)>, now: (f64, f64)) -> Option<(f64, f64, f64)> {
    let (before_boot, before_mono) = previous?;
    let (boot, mono) = now;
    let elapsed = boot - before_boot;
    let awake = mono - before_mono;
    if !elapsed.is_finite() || !awake.is_finite() || elapsed <= 0.0 || awake < 0.0 || awake > elapsed + 0.01 {
        return None;
    }
    let suspended = (elapsed - awake).clamp(0.0, elapsed);
    Some((elapsed, suspended, 100.0 * suspended / elapsed))
}
impl Collector {
    fn new() -> Self {
        // SAFETY: sysconf est sans danger avec une constante valide.
        let tck = unsafe { libc::sysconf(libc::_SC_CLK_TCK) };
        Collector {
            battery: find_battery(),
            prev_clocks: None,
            prev_ticks: HashMap::new(),
            prev_wake: HashMap::new(),
            prev_cstate_us: None,
            modem: ModemClient::spawn(),
            clk_tck: if tck > 0 { tck as f64 } else { 100.0 },
        }
    }

    /// Top 2 des processus par temps CPU consommé depuis le relevé précédent.
    fn top_procs(&mut self) -> String {
        let now = read_proc_ticks();
        if now.is_empty() { return NA.to_string(); }
        let mut deltas: Vec<(String, u64)> = now
            .iter()
            .map(|(pid, (name, ticks))| {
                let before = self.prev_ticks.get(pid).copied().unwrap_or(0);
                (name.clone(), ticks.saturating_sub(before))
            })
            .filter(|(_, d)| *d > 0)
            .collect();
        deltas.sort_by(|a, b| b.1.cmp(&a.1));
        self.prev_ticks = now.iter().map(|(pid, (_, t))| (*pid, *t)).collect();
        if deltas.is_empty() { return "none".to_string(); }
        deltas
            .iter()
            .take(2)
            .map(|(n, d)| format!("{}(+{}ms)", clean(n), (*d as f64 / self.clk_tck * 1000.0) as u64))
            .collect::<Vec<_>>()
            .join("|")
    }

    /// Top 3 des sources de réveil, par temps actif depuis le relevé précédent.
    fn wake_sources(&mut self) -> String {
        let dirs: Vec<PathBuf> = list_dir("/sys/class/wakeup")
            .into_iter()
            .filter(|d| d.file_name().map_or(false, |n| n.to_string_lossy().starts_with("wakeup")))
            .collect();
        if dirs.is_empty() { return NA.to_string(); }
        let mut current: HashMap<String, u64> = HashMap::new();
        let mut deltas: Vec<(String, u64)> = Vec::new();
        for d in dirs {
            let dirname = d.file_name().map(|n| n.to_string_lossy().to_string()).unwrap_or_default();
            let name = read_trim(d.join("name")).unwrap_or_else(|| dirname.clone());
            let Some(active) = read_num::<u64>(d.join("active_time_ms")) else { continue };
            let key = format!("{dirname}:{name}");
            let delta = active.saturating_sub(self.prev_wake.get(&key).copied().unwrap_or(0));
            if delta > 0 { deltas.push((name, delta)); }
            current.insert(key, active);
        }
        if current.is_empty() { return NA.to_string(); }
        self.prev_wake = current;
        deltas.sort_by(|a, b| b.1.cmp(&a.1));
        if deltas.is_empty() { return "none".to_string(); }
        deltas
            .iter()
            .take(3)
            .map(|(n, d)| format!("{}(+{}ms)", clean(n), d))
            .collect::<Vec<_>>()
            .join("|")
    }

    /// (nom de l'état C le plus profond, temps passé dedans depuis le relevé précédent en ms)
    fn deepest_cstate(&mut self) -> (String, String) {
        let deepest = list_dir("/sys/devices/system/cpu/cpu0/cpuidle")
            .into_iter()
            .filter_map(|d| {
                let idx = d.file_name()?.to_string_lossy().strip_prefix("state")?.parse::<u32>().ok()?;
                Some((idx, d))
            })
            .max_by_key(|(idx, _)| *idx);
        let Some((_, dir)) = deepest else { return (NA.to_string(), NA.to_string()) };
        let name = read_trim(dir.join("name")).map(|n| clean(&n)).unwrap_or_else(|| NA.into());
        let Some(us) = read_num::<u64>(dir.join("time")) else { return (name, NA.to_string()) };
        let ms = self.prev_cstate_us.map(|p| us.saturating_sub(p) / 1000);
        self.prev_cstate_us = Some(us);
        (name, fmt_any(ms))
    }

    /// Read both clocks once and update the previous sample only afterwards.
    fn sleep_interval(&mut self) -> (Option<f64>, Option<f64>, Option<f64>) {
        let (Some(boot), Some(mono)) =
            (clock_secs(libc::CLOCK_BOOTTIME), clock_secs(libc::CLOCK_MONOTONIC))
        else { return (None, None, None); };
        let result = clock_interval(self.prev_clocks, (boot, mono));
        self.prev_clocks = Some((boot, mono));
        match result {
            Some((elapsed, suspended, percent)) => (Some(percent), Some(elapsed), Some(suspended)),
            None => (None, None, None),
        }
    }

    fn sample(&mut self, reason: &str) -> Vec<String> {
        let modem_id = self.modem.request();

        if self.battery.as_ref().map_or(true, |p| !p.exists()) {
            self.battery = find_battery();
        }
        let e = self.battery.as_deref().map(read_electrical).unwrap_or_default();
        let (deep, interval, suspended) = self.sleep_interval();
        let load1 = read_trim("/proc/loadavg")
            .and_then(|s| s.split_whitespace().next().map(str::to_string))
            .unwrap_or_else(|| NA.into());
        let freq_mhz = read_num::<f64>("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
            .map(|khz| (khz / 1000.0).round() as i64);
        let (bright, bright_pct, screen_on) = read_screen();
        let procs = self.top_procs();
        let wake = self.wake_sources();
        let (cname, cms) = self.deepest_cstate();
        let modem = self.modem.collect(modem_id);

        vec![
            chrono::Local::now().to_rfc3339_opts(chrono::SecondsFormat::Secs, false),
            reason.to_string(),
            fmt_any(clock_secs(libc::CLOCK_BOOTTIME).map(|s| s as u64)),
            e.status.clone().unwrap_or_else(|| NA.into()),
            fmt_any(e.capacity),
            fmt_f(e.voltage_v, 3),
            fmt_f(e.current_ma, 1),
            fmt_f(e.current_avg_ma, 1),
            fmt_f(e.power_w, 3),
            fmt_any(e.cap_now),
            fmt_any(e.cap_full),
            e.cap_unit.unwrap_or(NA).to_string(),
            fmt_any(e.charge_counter_uah),
            fmt_f(e.temp_c, 1),
            fmt_f(deep, 1),
            load1,
            fmt_any(freq_mhz),
            fmt_any(bright),
            fmt_f(bright_pct, 1),
            screen_on.map_or(NA.to_string(), |b| if b { "1" } else { "0" }.to_string()),
            read_net(),
            procs,
            wake,
            count_online_cpus().to_string(),
            cname,
            cms,
            fmt_any(modem.signal),
            modem.tech,
            fmt_f(interval, 1),
            fmt_f(suspended, 1),
        ]
    }
}

// ───────────────────────── Fichier CSV ─────────────────────────

fn csv_path() -> PathBuf {
    let base = std::env::var_os("XDG_DATA_HOME")
        .map(PathBuf::from)
        .filter(|p| p.is_absolute())
        .or_else(|| std::env::var_os("HOME").map(|h| PathBuf::from(h).join(".local/share")))
        .unwrap_or_else(|| PathBuf::from("/tmp"));
    base.join("battery-diag").join("discharge_diag.csv")
}

/// Au démarrage : crée le dossier ; archive l'ancien fichier si ses colonnes ont changé.
fn prepare_log(path: &Path) -> io::Result<()> {
    if let Some(dir) = path.parent() { fs::create_dir_all(dir)?; }
    if path.exists() {
        let mut first = String::new();
        BufReader::new(fs::File::open(path)?).read_line(&mut first)?;
        if !first.trim().is_empty() && first.trim_end() != HEADER.join(",") {
            let stamp = chrono::Local::now().format("%Y%m%d%H%M%S");
            // Never overwrite an earlier archive, even after rapid restarts.
            let mut suffix = 0u32;
            loop {
                let extension = if suffix == 0 { format!("csv.old-{stamp}") } else { format!("csv.old-{stamp}-{suffix}") };
                let archive = path.with_extension(extension);
                match fs::hard_link(path, &archive) {
                    Ok(()) => { fs::remove_file(path)?; break; }
                    Err(e) if e.kind() == io::ErrorKind::AlreadyExists && suffix < 1000 => { suffix += 1; }
                    Err(e) => return Err(e),
                }
            }
        }
    }
    Ok(())
}

/// Le fichier est rouvert à chaque relevé : supprimer le CSV à la main ne casse rien.
fn append_record(path: &Path, row: &[String]) -> io::Result<()> {
    if let Some(dir) = path.parent() { fs::create_dir_all(dir)?; }
    let file = OpenOptions::new().create(true).append(true).open(path)?;
    let empty = file.metadata()?.len() == 0;
    let mut w = csv::WriterBuilder::new().has_headers(false).from_writer(file);
    if empty { w.write_record(HEADER)?; }
    w.write_record(row)?;
    w.flush()?;
    Ok(())
}

// ───────────────────────── Sources d'événements ─────────────────────────

enum Event {
    Resume,       // le système vient de sortir de veille
    PowerChanged, // un événement noyau concerne power_supply
}

/// Écoute le signal PrepareForSleep(false) de systemd-logind = réveil du système.
fn watch_resume(tx: &Sender<Event>) -> zbus::Result<()> {
    let conn = zbus::blocking::Connection::system()?;
    let proxy = zbus::blocking::Proxy::new(
        &conn,
        "org.freedesktop.login1",
        "/org/freedesktop/login1",
        "org.freedesktop.login1.Manager",
    )?;
    for msg in proxy.receive_signal("PrepareForSleep")? {
        if let Ok(going_to_sleep) = msg.body().deserialize::<bool>() {
            if !going_to_sleep && tx.send(Event::Resume).is_err() { break; }
        }
    }
    Ok(())
}

/// Écoute les uevents du noyau (netlink) : branchement/débranchement du chargeur.
fn watch_uevents(tx: &Sender<Event>) -> io::Result<()> {
    // SAFETY: appels système classiques ; le descripteur est confié à OwnedFd (fermeture auto).
    let fd = unsafe { libc::socket(libc::AF_NETLINK, libc::SOCK_DGRAM | libc::SOCK_CLOEXEC, 15) };
    if fd < 0 { return Err(io::Error::last_os_error()); }
    let fd = unsafe { OwnedFd::from_raw_fd(fd) };
    let mut addr: libc::sockaddr_nl = unsafe { std::mem::zeroed() };
    addr.nl_family = libc::AF_NETLINK as libc::sa_family_t;
    addr.nl_groups = 1; // groupe « kernel »
    let rc = unsafe {
        libc::bind(
            fd.as_raw_fd(),
            &addr as *const libc::sockaddr_nl as *const libc::sockaddr,
            std::mem::size_of::<libc::sockaddr_nl>() as libc::socklen_t,
        )
    };
    if rc < 0 { return Err(io::Error::last_os_error()); }
    let needle: &[u8] = b"SUBSYSTEM=power_supply";
    let mut buf = [0u8; 8192];
    loop {
        let n = unsafe { libc::recv(fd.as_raw_fd(), buf.as_mut_ptr() as *mut libc::c_void, buf.len(), 0) };
        if n < 0 {
            let err = io::Error::last_os_error();
            if err.kind() == io::ErrorKind::Interrupted { continue; }
            return Err(err);
        }
        let msg = &buf[..n as usize];
        if msg.windows(needle.len()).any(|w| w == needle) && tx.send(Event::PowerChanged).is_err() {
            return Ok(());
        }
    }
}

// ───────────────────────── Programme principal ─────────────────────────

fn main() {
    let path = csv_path();
    if let Err(e) = prepare_log(&path) {
        eprintln!("battery-logger: impossible de préparer {}: {e}", path.display());
        std::process::exit(1); // systemd relancera le service
    }
    eprintln!("battery-logger: écriture dans {}", path.display());

    let (tx, rx) = mpsc::channel::<Event>();

    let tx_resume = tx.clone();
    let _ = thread::Builder::new().name("resume".into()).spawn(move || {
        if let Err(e) = watch_resume(&tx_resume) {
            eprintln!("battery-logger: pas de détection de réveil via logind: {e}");
        }
    });

    let tx_power = tx.clone();
    let _ = thread::Builder::new().name("uevent".into()).spawn(move || {
        if let Err(e) = watch_uevents(&tx_power) {
            eprintln!("battery-logger: uevents indisponibles ({e}), repli sur un test toutes les 30 s");
            loop {
                thread::sleep(Duration::from_secs(30));
                if tx_power.send(Event::PowerChanged).is_err() { break; }
            }
        }
    });

    let mut collector = Collector::new();
    let mut last_status: Option<String> = None;
    let mut last_write: Option<Instant> = None;
    let mut next_due = Instant::now();
    let mut first = true;

    loop {
        // Instant = CLOCK_MONOTONIC : ne progresse pas pendant la veille, ne la réveille pas.
        let wait = next_due.saturating_duration_since(Instant::now());
        let reason: Option<&str> = match rx.recv_timeout(wait) {
            Ok(Event::Resume) => {
                thread::sleep(Duration::from_secs(2)); // laisse le système se stabiliser
                while rx.try_recv().is_ok() {}
                Some("resume")
            }
            Ok(Event::PowerChanged) => {
                if read_status_only() != last_status { Some("status_change") } else { None }
            }
            Err(RecvTimeoutError::Timeout) => Some(if first { "start" } else { "periodic" }),
            Err(RecvTimeoutError::Disconnected) => {
                thread::sleep(Duration::from_secs(60));
                Some("periodic")
            }
        };
        let Some(reason) = reason else { continue };

        let too_soon = last_write.map_or(false, |t| t.elapsed() < MIN_GAP);
        if too_soon && reason != "resume" && reason != "periodic" { continue; }

        let row = collector.sample(reason);
        last_status = row.get(3).cloned().filter(|s| s != NA);
        if let Err(e) = append_record(&path, &row) {
            eprintln!("battery-logger: écriture impossible: {e}"); // on réessaiera au prochain relevé
        }
        last_write = Some(Instant::now());
        next_due = Instant::now() + SAMPLE_INTERVAL;
        first = false;
    }
}

#[cfg(test)]
mod clock_tests {
    use super::*;
    #[test]
    fn old_csv_is_preserved_when_columns_change() {
        let dir = std::env::temp_dir().join(format!("lmi-logger-archive-{}", std::process::id()));
        fs::create_dir(&dir).unwrap();
        let path = dir.join("discharge_diag.csv");
        let original = b"timestamp,old\n2026-01-01,42\n";
        fs::write(&path, original).unwrap();
        prepare_log(&path).unwrap();
        assert!(!path.exists());
        let archived: Vec<_> = fs::read_dir(&dir).unwrap().map(|e| e.unwrap().path()).collect();
        assert_eq!(archived.len(), 1);
        assert_eq!(fs::read(&archived[0]).unwrap(), original);
        fs::remove_dir_all(dir).unwrap();
    }
    #[test]
    fn elapsed_and_sleep_are_from_the_same_interval() {
        assert_eq!(clock_interval(None, (100.0, 100.0)), None);
        let (elapsed, asleep, pct) = clock_interval(Some((100.0, 100.0)), (220.0, 110.0)).unwrap();
        assert_eq!((elapsed, asleep), (120.0, 110.0));
        assert!((pct - 91.6666667).abs() < 0.0001);
        assert_eq!(clock_interval(Some((100.0, 100.0)), (220.0, 220.0)), Some((120.0, 0.0, 0.0)));
        assert_eq!(clock_interval(Some((100.0, 100.0)), (99.0, 101.0)), None);
        assert_eq!(clock_interval(Some((100.0, 100.0)), (110.0, 120.0)), None);
    }
}