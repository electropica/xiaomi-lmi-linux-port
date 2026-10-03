# lmi battery, speaker and torch validation — 2026-10-03

These are changes deployed to the running phone, not new golden userdata or
boot identities. The phone clock lagged the operator's date; durations and
sample counts are used below rather than treating phone wall time as exact.

## Battery service deployment

The full Debian 13 ARM64 packages `upower`, `libupower-glib3` and
`gir1.2-upowerglib-1.0`, version `1.90.9-1+lmi1`, were built from Debian's
`1.90.9-1` source with the canonical opt-in patch. Polkit, libimobiledevice,
introspection and Debian hardening remain enabled. Seven selected integration
tests passed in the ARM64 build environment under umockdev with proc mounted:
negative-current opt-in, charge, AC, capacity/charge, overfull, state guessing
and online-AC properties. Debian disables automatic tests in its package
rules; this was a separate explicit test run.

A private full-package hardware check preceded installation. The original
three Debian packages were retained privately for rollback. The installed
service then used the documented battery/SMB5-scoped udev rule and explicit
marker; USB supply scope was not changed. A real unplug/replug collection
recorded 90 observations: 65 Discharging/State=2/OnBattery=true,
24 Charging/State=1/OnBattery=false, and one transient
Not charging/State=5/OnBattery=false. The current-sign workaround therefore
works in the installed service, not merely in a private test binary.

This fixes state interpretation. It does not establish capacity accuracy,
authenticate the selected fuel-gauge profile, or prove acceptable autonomy.
Battery inactivity suspend is locally enabled after 900 seconds; AC stays
awake. Notification screen-wakeup triggers were locally disabled for the
long test. Suspend counters grew by 104 successes without new failures;
frequent resume IRQ 438 (`msoc-delta`) remains under investigation. USB-attached
suspend had failed twice, while an unplugged timed deep-suspend test worked.

## Speaker through the user audio service

The temporary reset-GPIO diagnostic boot remains required, with SHA-256
`43132d1ad4a73728e3e4408ff3570d7693d43bc45bbc9ab9945880e1d1ae2638`.
The proprietary TFA container stays external; no calibration suitability is
claimed. Direct ALSA playback using a signed 32-bit frontend and S24_LE
backend produced recognizable, clear music, confirmed by the operator.

The opt-in user PCM in `userspace/audio/files/lmi-speaker.asoundrc` converts
to S32_LE at 48 kHz stereo. ALSA control hooks temporarily select S24_LE
on the backend and enable the MultiMedia1 route, preserving/restoring both
controls on close. The matching PipeWire drop-in exposes `Haut-parleur lmi`.
It was installed in the active user's configuration on PipeWire 1.4.2.

An initial raw-file PipeWire test produced no sound and terminated too soon;
it is not a successful validation. The same signed-32 signal wrapped in a
standard WAV then streamed for ten seconds through PipeWire and the operator
confirmed it worked. The lower-speaker sink was the default. After idle,
backend format returned to S16_LE and route to off/off, with no active streams.
No UCM2 profile, microphone, headset or durable diagnostic boot installation
is validated. The source-level Q-format explanation remains a hypothesis
supported by these format-dependent results, not a complete acoustic study.

The private music excerpt and full logs are not published. The reference
10-second signed-32 raw payload is 3,840,000 bytes with SHA-256
`cdfcd974ac1b0d0259c6f86cb25f563f38b1abc8f5fa27868231eac9a7e03fa3`.
An earlier malformed sign-extension test is excluded from conclusions.

## Graphical torch

`userspace/apps/files/lmi-flashlight.py` uses the active user's logind session
`SetBrightness` interface for the `flashlight` LED. Value 20 selects 20 mA
per torch channel in the downstream driver; zero switches both off.
A supervised 15-second test was visibly confirmed. The installed graphical
application's Allumer and Éteindre buttons were both confirmed functional.
Both switch brightness values were subsequently checked at zero.

The application switches off on normal close and after 180 seconds while
its process runs. There is no independent crash watchdog; unexpected process
termination is not claimed to guarantee automatic extinction. No global
sysfs permission change or passwordless sudo rule is required.

## Camera boundary

Megapixels is installed, but a usable capture pipeline is not established.
The downstream request-manager/sync video nodes are not a standard image
capture device. The existing camera-blocker record still applies; installing
another frontend alone is not demonstrated to solve it.

## MP3, MP4, volume controls and Chinese filenames — 2026-10-03

The operator confirmed normal MP3 and MP4 playback and working hardware
volume buttons. These confirmations extend the previous PipeWire WAV test;
the private songs/videos and their personal titles are excluded from Git.

`fonts-noto-cjk` version `1:20240730+repack1-1` was installed on the phone.
Because phone DNS failed, the official Debian package was downloaded on the
host and checked against the phone's APT metadata before local installation.
The package SHA-256 is
`f5dc28a754e17327d99f0a612134d92c8dd6187314ae967cb77f25df60860139`.
Fontconfig selected CJK families; the active user's font cache was rebuilt.
A new GTK window displayed the exact Chinese filename characters with both
default and explicit Noto fonts. The existing Files process initially still
showed incorrect glyphs; after a normal quit/relaunch, the operator confirmed
correct Chinese names in Files. The optional-app installer now includes the
font package, without modifying the external golden image or its historical
lock. Existing applications may need relaunching to refresh their font maps.

## Controlled battery idle/deep comparison — 2026-10-03

A finite phone-local collector waited for USB unplug, sampled awake idle,
then requested a 120-second RTC-timed deep suspend. The successful suspend
counter increased from 106 to 107 with failures unchanged at 2; RTC IRQ 323
caused resume. Kernel suspend timing reported 121.224 seconds asleep.

Over the measured 30.077-second awake-idle interval, the reported charge
counter fell from 1,434,830 to 1,433,005 uAh: approximately 218.4 mA average.
Across the 121.423-second before/after-suspend interval it fell to 1,429,556
uAh: approximately 102.3 mA average. Capacity stayed at 53%. These averages
come from the downstream fuel gauge, not an external current meter. The
comparison includes transition overhead and does not establish long-term
runtime. The immediate post-unplug negative-current sample was transient;
the settled unplugged samples had positive current and Discharging status.

The live battery type now reads `j11sun_4700mah`, nominal capacity 4,700,000
uAh, learned full capacity 2,845,000 uAh, and resistance ID 99,900 ohms. The
boot log reports authentication retries; the exact driver includes fallback
profile selection, so this name alone is not proof of authenticated battery
identity or correct learned capacity. Earlier unknown-profile observations
must not be treated as the current live value. No charge parameters, fuel-
gauge learning data or battery IRQ wake controls were changed in this test.

Debugfs is disabled in this kernel. Readable RPMh master and DDR residency
statistics exist in sysfs. The subsequent controlled comparisons below
show sleeping masters but unchanged DDR counters; they do not identify the
residual consumer.

## Repeated RPMh and CPU-idle comparisons — 2026-10-03

With Wi-Fi enabled, a 181.830-second interval reported 99.75 mA from the charge
counter. APSS slept 181.633 seconds and ADSP 181.826 seconds (19.2 MHz counter
conversion); RTC caused the only system resume. DDR residency was unchanged,
so its static frequency percentages cannot establish current memory activity.

With Wi-Fi temporarily disabled through NetworkManager, a 181.912-second
interval reported 96.48 mA. APSS and ADSP again slept almost the full interval.
The small difference does not establish Wi-Fi as the main residual consumer;
Wi-Fi was explicitly restored. No driver or regulator was force-disabled.

The live cmdline and sysfs parameter explicitly disable deeper CPU idle:
`lpm_levels.sleep_disabled=1`, parameter `Y`, no C1 usage. In the exact source,
`lpm_disallowed()` rejects normal cpuidle levels when this flag is set;
`lpm_suspend_enter()` uses a separate suspend path. This distinction explains
why deep suspend could work while awake idle was still inefficient.

A finite test measured baseline awake idle for 30.111 seconds at 208.39 mA
with zero C1 entries, then 30.138 seconds at 100.82 mA with 831 C1 entries
with the parameter `N`. A following 181.471-second suspend reported 97.21 mA
and succeeded without additional failures; APSS/ADSP slept almost throughout.
The original `Y` setting was restored and checked after reconnect.

A subsequent connected runtime test with `N` kept SSH/USB, Phosh and UPower
active and increased CPU0 C1 entries from 354 to 631 over 15 seconds. The
operator confirmed normal touch, music and volume controls. The optional
CPU-idle service was then installed, enabled and activated with the local
marker. Its stop/start check restored `Y`, removed the temporary state and
reactivated `N`; USB remained available. A staging-file/state-directory name
collision during the first activation was corrected before successful
deployment. Reboot and long-duration validation remain pending. All
currents are short-interval fuel-gauge estimates; acceptable long-term
battery life and an authenticated capacity/profile are not established.


## Suspend trace with the CPU-idle opt-in active — 2026-10-03

A finite collector used a private tracefs instance, without changing global
tracing, charging policy or regulator settings. It recorded 2,716 events;
the buffer retained all 2,716, without overflow. USB was unplugged for the
measurement and the RTC requested a 120-second deep suspend.

The before/after interval was 121.987 seconds, including 121.761 seconds
asleep according to the kernel. The charge counter implied 96.21 mA average.
Suspend success increased by one, failures did not increase, and RTC IRQ 323
caused resume. APSS accumulated 121.795 seconds asleep and ADSP 121.980
seconds at the source-defined 19.2 MHz timebase. These are fuel-gauge and
kernel-counter observations, not external power measurements.

The trace selected L3 cluster index 1 with `idle:0` during system suspend;
the live device tree names this level `llcc-off`. RPMh command writes were
recorded around the transition. This confirms the selected path and emitted
commands, not the independently measured power state of every resource.
The trace timestamp stayed unchanged across machine_suspend and advanced
during syscore_resume: the apparent zero-duration machine_suspend event must
not override the elapsed-time and sleep-counter evidence.

DDR residency was identical before and after. Its displayed percentages
cannot be used to claim active DDR frequency during this interval. Likewise,
a readable GPU clock value alone is not evidence that the GPU was powered.
No hardware domain is identified as the residual consumer by this trace.

After reconnect, the private trace instance was removed, USB online read 1,
battery status read Charging, and the CPU-idle service remained active with
`sleep_disabled=N`. No new boot was built or flashed. Approximately 96 mA
reported deep-suspend consumption remains unresolved; capacity/profile
accuracy and long-duration runtime still need validation.


## Unplugged peripheral idle inspection — 2026-10-03

A finite read-only collector sampled runtime PM and regulator states every
five seconds for 30 seconds after unplug. It did not request system suspend
or change a power policy. The collector exited successfully; Charging was
confirmed after reconnect.

The USB controller `a600000.ssusb` changed from active to suspended. Both
`usb30_prim_gdsc` and `hsphy@88e3000` changed from enabled/one user to
disabled/zero users and stayed disabled through all unplugged snapshots.
The exact `dwc3-msm.c` source disables these resources on cable-disconnected
runtime suspend. USB remaining powered after unplug is therefore not
supported as the cause of the residual current in this test.

GPU CX/GX regulators were disabled throughout, although the KGSL runtime-PM
attribute said active; that attribute alone cannot establish GPU consumption.
UFS alternated between active and suspended while the collector itself read
sysfs and appended its log. The settled 20.075-second charge-counter interval
reported 123.91 mA; this sampled awake-idle interval must not replace or be
directly equated to the previous uninterrupted deep-suspend measurement.

The live tree contains an always-on `vdd_boost_vreg` and a separate enabled
`regulator-haptics-boost` declaration referencing the same PM8150B GPIO 5.
The exact common DTS has these declarations too. The boost stayed enabled;
this is a device-tree review lead, not evidence of its current draw or of an
audio-supply fault. The separate `vdd_hap_boost` regulator was disabled with
zero users. The exact regulator core explicitly supports shared enable GPIOs
and balances their enable counts; sharing alone is not a GPIO conflict or a
driver bug. The AW8697 software activate/duration attributes both
read zero. No GPIO or regulator was force-disabled. Console suspend was
enabled, and no no_console_suspend/clock-ignore boot flag was observed.

DDR driver inspection showed that this exact downstream reader maps and
reads the firmware statistics area without sending a refresh command.
Upstream's newer QMP refresh mechanism is explicitly described for SM8450
and later, so it is not a validated fix for this SM8250 boot:
[upstream qcom_stats.c at a fixed commit](https://code.googlesource.com/linux/torvalds/linux/+/75f2c0b3690702c90863c2e138cb5520670845ea/drivers/soc/qcom/qcom_stats.c).
No AOP command or firmware-memory write was attempted.

Next diagnostic boundary: establish the boost's board function and consumer
ownership before considering a change, and obtain reliable resource/DDR
observability before attributing residual deep-suspend current to that domain.
The installed CPU-idle improvement remains active; acceptable autonomy is
still unvalidated.


A finite six-hour observation was then armed with the canonical runtime
collector at a ten-minute interval. It uses no RTC/wake timer and makes no
power-policy changes. Initial state: Charging, USB online, 95% capacity,
CPU-idle opt-in active. Long-run results are pending; this must not be reported
as completed autonomy validation.


## Règle de comparaison batterie — Wi-Fi et essais d'interface

L'opérateur précise que les références batterie actuelles ont été prises
sans connexion Wi-Fi, avec la radio désactivée pour certains essais.
Ne pas mélanger une future mesure avec Wi-Fi connecté à ces références.
Consigner séparément : radio activée/désactivée, association Wi-Fi effective,
écran, USB, musique/lampe et correctif CPU. « Non associé » n'est pas
équivalent à « radio désactivée ». Les comparaisons historiques détaillées
conservent leurs états Wi-Fi respectifs ; aucune n'est requalifiée ici.

Pour les tests d'applications, un inhibiteur temporaire idle+suspend lié à
USB online a été lancé, limité à deux heures et libéré lorsque l'USB passe
hors ligne. Il ne change pas les préférences persistantes. Arrêter ce service
avant une nouvelle mesure batterie : l'écran forcé et le collecteur de
surveillance USB font partie des conditions d'essai à maîtriser. L'activation
branchée a été vérifiée ; le débranchement de cette inhibition n'a pas été
testé physiquement dans ce lot. Aucun nouveau test batterie n'a été effectué.
