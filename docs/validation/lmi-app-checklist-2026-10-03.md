# lmi application checklist — October 3, 2026

Each application is tested separately. Successful startup does not validate
every function. Confirmations obtained before a reboot are distinguished from
checks on the current boot. No personal account, message or contact is created
for these tests. Requested operator actions wait for confirmation, without a
deadline for performing the gesture. Autonomous gestures below are explicitly
identified as simulated input, rather than operator confirmation.

The table summarizes the latest evidence; the dated sections preserve the
sequence of earlier findings, corrections and superseding checks. French UI
labels are retained where useful to identify controls on the test phone.

| Application | Overall functionality | Menu functionality | Translation |
|---|---|---|---|
| Discussions (Chatty) | Startup and reopening confirmed after the workaround; actual 384 MiB limit, zero swap and no new OOM in the checked scope. SMS/MMS unvalidated; no modem detected. | Shortcuts initially too wide. With Phoc window adjustment and Close restored, the whole dialog and touch-simulated close/reopen were verified on October 4. Other menus need further checks. | Settings still contain English despite the French locale; partial catalog. Local correction prepared but not fully validated; low priority. |
| Calculator | Touch-button arithmetic includes 2+3=5 and 9²=81. App-only simple GTK input context keeps the keypad visible without OSK; operator confirmation and normal close/reopening retained. Current menu test closed with status 0. | Basic → Advanced → Conversion → Basic navigation passed. Touch entry of 180 degrees produced 3.141592654 radians. Preferences opened and closed using the visible Close button. Shortcuts remain horizontally clipped, without a visible Close; outside touch failed, injected Escape dismissed them. | Examined labels French; full coverage unvalidated. |
| Files | Operator explicitly confirmed that Files was already functional on October 4; do not repeat its passed basic operations merely to extend the checklist. Test-folder creation/opening/return retained. On October 4, touch-driven Copy created an identical 39-byte file, Rename changed its path, and Trash removed only that copy with the correct original-path metadata. Normal exit status 0; fixtures cleaned. Chinese names confirmed only before reboot. | Copy/Rename/Trash contextual actions and rename dialog usable. OSK remained after Rename; tested bottom long press did not hide it and the globe menu had no Hide action. Remote DBus hiding enabled that initial test continuation. A later two-second hold centered on the home bar toggled OSK on/off in Files; operator gesture confirmation remains pending. Terminal OSK → latched Ctrl → touch items selected three folders. Ctrl was released and selection cleared; no grouped deletion tested. Other actions unvalidated. | Pending; Chinese filename rendering is validated separately from menu language. |
| Portfolio | Debian `portfolio-filemanager` 1.0.2-1 trial subsequently uninstalled. Long press then tap selects multiple files without OSK, checked by simulated touch. Operator rejected the candidate as providing no useful improvement; next-build package addition withdrawn. | Grouped permanent removal tested on two disposable files, leaving the third intact. Trash and normal closure/reopening still being checked; do not infer them from removal alone. | French labels observed; complete coverage unvalidated. |
| Text Editor | Input, creation/save, reopening and modification/save verified on test files. Initial renderer teardown produced SIGSEGV; two normal closures obtained with app-only Cairo. Operator confirmed touch usability of Save As with the final launcher. | Save As through the actual menu creates a separate file with identical contents; GNOME chooser fits the display. Preferences and search opened and closed through simulated touch. Shortcuts still clip; touch-only dismissal unvalidated. Printing, replacement and other actions pending. | Operator previously reported French preferences; translation is not the priority. |
| Papers | Two-page synthetic PDF displayed; swipe navigation and reopening retained. Search for Xiaomi returns one hit per page; absent-term search reports no results. Touching the second hit opens page two with the word highlighted and OSK hidden. Normal closure status 0. | Sidebar/search navigation and Save As usable through simulated touch. Save As created an identical 2,273-byte test copy; chooser and Save fit above OSK, which hid afterwards. Test copy removed after comparison and normal app close. Annotation, forms, printing and remaining menus unvalidated. Pixman invalid-rectangle warning observed during navigation, without a crash in this test. | Examined search labels French; full coverage unvalidated. |
| Photos (Koko) | Operator opened and zoomed a test image; thumbnail visible in a capture after the KIO cache workaround. No camera capture validated. | Return to gallery and hidden keyboard confirmed after correction. Sliding menu accessible; Images bar and labels remain poorly adapted. Search/editing/video unvalidated. | French labels visible; complete coverage unvalidated. |
| Clocks | Stopwatch start, progression, lap, pause and reset checked with simulated touch. One-minute timer start, countdown, pause and removal of only the test timer verified. Five-second timer expiration and audible alert confirmed on October 4 after installing Feedback and its PulseAudio backend. Alarm wakeup/delivery unvalidated. | Pending. | Pending. |
| Calendar | Month navigation and Today, explicitly authorized local dummy-event creation, reading and removal verified. Reopening without a leftover and normal exit status 0 confirmed. Synchronization and reminders unvalidated. | Creation/edit dialog and Delete usable after hiding the keyboard; other menus unvalidated. | French labels visible; complete coverage unvalidated. |
| Contacts | Local dummy contact without contact details, persistence after reopening and positive/negative search verified. Initial deletion caused SIGSEGV; two removal/exit-status-0 cycles passed with app-only Cairo. Launcher installed and next build prepared. | Add form and Delete menu tested; editing, import/export and merging unvalidated. | French labels visible; complete coverage unvalidated. |
| Settings | Overview and Mouse and Touchpad, Keyboard and System pages accessible through simulated touch; two normal exits with status 0. Last-panel restoration confirmed; overview-on-launch unresolved. No system settings changed in that navigation test. | Mouse-test dialog opens without a visible Close button; outside touches did not dismiss it, Escape did. Touch-only dismissal unresolved; other submenus unvalidated. | Examined pages mostly French; complete coverage unvalidated. |
| Console | Test text and shell arithmetic displayed. Shell termination misdetected: status -1 and GLib waitid(P_PIDFD)=EINVAL. Temporary pidfd fallback tested; no persistent launcher change. | Pending. | Pending. |
| lmi Flashlight | On/off confirmed before reboot; recheck pending. | No additional menu tested. | French interface present; no multilingual validation. |
| Amberol | MP3 playback and volume confirmed before reboot. The later diagnostic boot restored ALSA and operator-confirmed PipeWire speaker playback; Amberol-specific playback on this boot still needs recheck. | Pending. | Pending. |
| Showtime | MP4 playback confirmed before reboot. Speaker audio was later restored on the diagnostic boot; this does not establish a fresh Showtime playback/video check. | Pending. | Pending. |
| Recorder | Diagnostic-boot microphone capture recognized through native ALSA preview; two complete KRecorder WAV saves measured. Application recording confirmed good by the operator after replay. | Microphone chooser, WAV/PCM saving and persisted `0:08` after normal relaunch passed with opt-in audio fixes. Rename and Delete tested on our temporary recording; confirmed recording preserved. Other codecs/export unvalidated. | Configuration labels French; complete coverage untested. |
| Megapixels | Blocked: bounded current launch exits with status 1 because `qcom,kona-mtp.ini` is absent; no established standard capture pipeline. | Unvalidated. | Not the priority before functional capture. |
| Calls | Startup, reopening, Keypad tab and normal exit status 0 verified. UI reports no modem/VoIP account; no number entered or call placed. | VoIP Accounts opened; session preference restores Close, and simulated touch dismisses the dialog while Calls stays open. | French labels on examined screens; complete coverage unvalidated. |
| Web | Pending; Internet DNS failed at the last check. | Pending. | Pending. |
| Maps | Pending; network and position unvalidated. | Pending. | Pending. |
| Weather | Pending; updates require network access. | Pending. | Pending. |
| Geary | Startup and reopening on Accounts without an account, then two normal exits with status 0. Receiving/sending unvalidated. | Add opens the form; Back cancels, then Back from Accounts closes normally. No account created or credentials entered. | French labels and English welcome text observed; partial coverage. |

### Separate system checks

- Operator reported incorrect time. Phone reading: `2026-10-02T13:42:19+00:00`,
  timezone `Etc/UTC`, `NTPSynchronized=no`, while the operator date was
  October 3, 2026 in Europe/Paris. Check the clock/synchronization and timezone;
  do not attribute the entire offset to the timezone alone. No time setting
  changed during this initial check; the later correction is recorded below.
- Keyboard appears during input without a visible hide control.
  `sm.puri.OSK0.SetVisible(false)` works over SSH, but this alone does not
  validate a gesture or button usable from the UI. Issue remains open;
  subsequent simulated long-press checks are distinguished below.

Operator priority: overall functionality, then menus, then translation.
One test application at a time, allowing time to confirm each physical
gesture. Calculator and Clocks were the latest overall-function checks at
the initial checkpoint; Editor, Chatty and Photos evidence remains preserved.

## Initial validation order

Finish the isolated Chatty test and preserve its diagnosis, then test
Calculator, Files, Text Editor, Papers and Photos. Check utilities, flashlight
and multimedia next. Camera, modem and Internet functions remain explicitly
blocked while their hardware or network prerequisites are unavailable.

## Chatty incident

Installed version: 0.8.7-2. The previous boot's kernel log reports anonymous
RSS of 6 438 704 kB before the process was killed. The session bus also
suffered an OOM; the phone rebooted during the incident. Diagnosis sent no
SMS and changed no user data.

GDB stopped at the first critical error in the video4linux2 provider,
uvch264 provider, GStreamer device monitor and libpurple path. Lowering
provider ranks was insufficient. An isolated plugin view excluding
`libgstvideo4linux2.so` and `libgstuvch264.so`, with a separate registry,
kept the process alive during the initial check. This identifies video
detection as a causal lead at startup, without locating the exact
driver/kernel error. System GStreamer packages remain installed. Opening
the interface does not validate messaging or the modem.

The reboot interrupted the temporary six-hour battery monitor: no complete
runtime result was obtained. CPU and UPower corrections are active;
the ALSA card is no longer detected on this boot.

## Recovery after an ordinary relaunch

The operator closed the isolated test and reopened Discussions through the
ordinary launcher, which did not yet include the workaround. Consumption
blocked the session again. Chatty was killed over SSH as soon as access
returned; available memory rose to approximately 7 GB. The ordinary launcher
should have been secured before the manual check. This does not establish
failure of the isolated filter; it confirms the ordinary launch path was
still unsafe.

`userspace/apps/files/lmi-chatty-safe` was then installed locally as
`/usr/local/bin/lmi-chatty-safe`. Its symlink plugin view excludes only
video4linux2 and uvch264, using a private registry. User desktop and D-Bus
launchers now route through the helper. It requests a user systemd scope
with MemoryMax=384 MiB, MemorySwapMax=0 and TasksMax=128, without an
unlimited fallback. These changes were not enabled in the generic image
builder at this checkpoint.

Both Exec commands were inspected. User memory delegation was checked after
reboot: a harmless scope exposed memory.max=402653184 and memory.swap.max=0.
Both overrides and the helper remained present. No application was launched
for that delegation check. Normal startup/navigation remained pending at
this checkpoint, before Discussions could be marked OK.
The other 20 applications were not validated in this batch; testing stopped
to preserve the quota reported by the operator.

After GStreamer plugin updates, links in the isolated view need review.
Rollback removes only the two created user overrides and installed helper/view;
original system files and plugins were not changed. Rollback re-exposes the
initial defect: do not relaunch Chatty without confinement in that state.

## Targeted recovery: ordinary Discussions launcher

The protected user launcher was tested. The operator confirmed its menu,
closure and reopening without a freeze. The reopened process belonged to
a user scope exposing memory.max=402653184, memory.swap.max=0,
memory.current=71299072 and zero oom/oom_kill events at inspection.
This supersedes the pending launch/delegation items in earlier notes;
it does not validate SMS/MMS.

A French correction of only the settings resource was generated locally
from Chatty 0.8.7-2. It does not modify the system package and is neither
visual validation nor a generic-builder modification. The operator asked
to defer translation in favor of functionality.

Windows SSH reached the server but could not read the WSL private key
and host-key file. Existing WSL access remains in use; no private key was
copied and host verification was not disabled.

## Battery comparison rule: Wi-Fi and UI testing

The operator states that current battery references were recorded without
Wi-Fi association, with the radio disabled in some tests. Do not mix a future
Wi-Fi-connected measurement with those references. Record separately: radio
enabled/disabled, actual association, screen, USB, music/flashlight and CPU
correction. Unassociated is not equivalent to radio disabled. Detailed
historical comparisons retain their own Wi-Fi states; none are reclassified here.

A temporary idle+suspend inhibitor tied to USB online was started for UI
tests, limited to two hours and released when USB goes offline. It changes
no persistent preferences. Stop it before another battery measurement:
screen inhibition and USB monitoring are test conditions to control.
Activation while plugged in was checked; physical unplug behavior was not
tested in this batch. No new battery test was performed.

## Manual time correction — October 3, 2026

The system clock was set from the PC's UTC time; installed timezone is
Europe/Paris. Verified reading: 2026-10-03T09:55:19+02:00. timedatectl refused
authorization; root directly updated localtime/timezone and used date.
No reboot or RTC write occurred. Automatic NTP synchronization and time
retention after reboot remain unverified. This supersedes the incorrect-time
status for the current boot, not earlier observations.

## Operator feedback — October 3, after time correction

These are operator reports. OK does not validate hardware functions that
were not explicitly tested. Priority: overall functionality, menus, then
translation; one application at a time.

| Application | Overall functionality | Menu functionality | Translation |
|---|---|---|---|
| Text Editor | Operator could not close it; disappeared after several minutes. Crash not confirmed at this checkpoint. | Save/Save As overflow the display. Preferences accessible. | French preferences confirmed. |
| Calls | Interface OK; calls and modem unvalidated. | No defect reported. | Not assessed separately. |
| Discussions | Functionality confirmed after freeze workaround. | Shortcuts too large; cannot return. | Partially French preferences; full correction deferred. |
| Contacts | OK according to operator. | No defect reported. | Not assessed separately. |
| Amberol | Playback previously validated; no new audio measurement here. | Keyboard shortcuts poorly adapted. | Not assessed separately. |
| Console, Files, Papers | OK according to operator. | No defect reported. | Not assessed separately. |
| Geary | Startup OK; no account, receiving/sending untested. | Further checks needed. | Not assessed separately. |
| Clocks | OK according to operator; hardware alarm not explicitly validated. | No defect reported. | Not assessed separately. |
| Megapixels | Loading followed by empty window; capture nonfunctional. | Unvalidated. | Secondary. |
| Photos (Koko) | Empty window. | Unvalidated. | Secondary. |
| Settings | Restores last page instead of overview. | Some options appear limited; full review still needed. | Not assessed separately. |

### Cross-application defects and pending tests

- Open-app overview: black/white stripes; cause unestablished.
- Keyboard Shortcuts dialogs overflow and lack a return control in several apps.
  They remain useful with an external keyboard but must be dismissible on a phone.
- App grid overflow and scroll gestures need visual checks.
- Mobile-filter label is clipped. Current app-filter-mode=['adaptive'],
  force-adaptive=[]; declaring mobile support differs from actual compatibility.
- Recorder: microphone and internal earpiece untested; distinguish them from
  the bottom loudspeaker.
- Automatic rotation, GPS and compass unvalidated.
- Photo/video gallery and camera capture are different functions. Showtime
  plays video; Koko still needed repair at this checkpoint, and Megapixels
  has no established capture pipeline.
- Software keyboard still lacks an obvious visible hide button.

### Remote checks at this checkpoint

Koko 25.04.0-1 reports a missing Qt Wayland plugin, missing QSQLITE driver,
then Main.qml load failure due to missing org.kde.kquickcontrolsaddons.
This establishes missing dependencies, not that installing them will fix
every graphical issue. The recipe uses --no-install-recommends.

Editor 48.3-3 logged GtkLabel dimension errors and dialog cancellations.
No OOM/segfault was found in the targeted check of this boot at that time;
its disappearing window remained unexplained.

The three exposed IIO devices are PM8150/PM8150B/PM8150L ADCs, not
accelerometers or magnetometers. iio-sensor-proxy is not installed;
no standard rotation sensor is established. GeoClue is installed, which
proves neither an available GPS receiver nor satellite positioning.

### Battery and protocol during operator absence

Phone unplugged around 10:40 and later reconnected. Reading after reconnection
at 11:58: 96%, charge_counter=2753852 µAh, Charging. Without a synchronized
starting value, this reading alone cannot quantify interval consumption.
CPU-idle service active; temporary plugged-in screen inhibitor active.
Stop it before any new comparative battery protocol. During operator absence,
do not request or assume unplugging, listening or visual confirmation.
No Wi-Fi changes for battery testing.

## Photos: dependencies and limited test — October 3, 2026

The application recipe now explicitly includes qt6-wayland,
libqt6sql6-sqlite, qml6-module-org-kde-kquickcontrolsaddons and
qml6-module-org-kde-purpose. These four packages and dependencies
(29 new packages total) were installed on the phone without a general
upgrade. dpkg --audit is empty. QSQLITE, Wayland-plugin and missing-QML
module errors disappeared.

Accelerated startup then showed Mesa get-param/pipe allocation errors and
egl: failed to create dri2 screen. An app-only QT_QUICK_BACKEND=software
test loaded Koko's interface without those errors in the startup sample,
at approximately 69 MiB in its cgroup. Two QML placement/stacking warnings
remain. The test service used MemoryMax=512 MiB and RuntimeMaxSec=20;
no unlimited test process remains. This validates automatic loading, not
visual rendering, navigation, zoom or video playback.

The userspace/apps/files/lmi-photos helper and a user Photos launcher override
apply software rendering only to Koko on the test phone. At this checkpoint,
the helper was not enabled by default in the generic builder before visual
validation; explicit dependencies were included in the recipe.
Local rollback: remove the user org.kde.koko.desktop override; the system
launcher is intact. Software rendering could cost more CPU while showing
images; consumption was not measured.

Settings remembers last-panel='privacy' in org.gnome.Settings. Installed
help exposes no --overview option; clearing the key selects the first panel
without guaranteeing an overview. No unproven launcher correction was applied.
Mobile navigation back to the panel list still needed visual validation then.

Technical references:

- [Qt Quick software rendering](https://doc.qt.io/qt-6.5/qtquick-visualcanvas-adaptations.html).
- [GNOME Settings 48 last-panel restoration](https://sources.debian.org/src/gnome-control-center/1:48.4-1~deb13u1/shell/cc-window.c/).

### Installing applications and hardware options

The application list is not fixed: Debian ARM64 packages can be installed
through APT. Firefox is firefox-esr in Debian trixie; Firefox was not installed
in this test. GNOME Software provides a graphical catalog with appropriate
backends but is not installed here. ARM64 availability and phone-adapted
interfaces are separate requirements.

Mouse and Touchpad concerns pointing devices, including external devices;
it does not configure the screen's touch input or virtual keyboard. Panels
depend on available hardware/services; limited options do not alone prove
a rendering defect. Automatic rotation and compass require exposed sensors
and software support; the observed ADCs are not substitutes. Maps may use
GeoClue, but network-derived location would not validate GPS.

References: [Debian Firefox ESR](https://packages.debian.org/trixie/firefox-esr),
[GNOME Software](https://apps.gnome.org/Software/).

Remote screenshots: grim was installed as a diagnostic tool (84 kB installed).
Capture works but initially showed the lock screen; no secrets or lock settings
were changed. Captures stay private, outside Git. Visual confirmation of
Photos and other menus was therefore still pending at that checkpoint.

## Photos: operator feedback and navigation — October 3, 2026

The operator confirmed a working interface with a sliding menu. A test PNG
was transferred outside Git and displayed, but returning to the gallery
was initially impossible, with the keyboard visible during viewing.
Zoom in/out appeared unlimited.

The OSK API temporarily hid the keyboard; that remote action is not a general
keyboard correction. The Photos helper now sets QT_QUICK_CONTROLS_MOBILE=1
only for Koko. Missing qt6-svg-plugins was installed and added to the recipe:
a video icon appears in the capture afterward, but not every button is validated.
Later operator confirmation: Return works and the keyboard stays hidden
after opening an image with the final helper.

Official Koko v25.04.0 BaseImageDelegate.qml sets minimumZoomSize=8 and
maximumZoomFactor=100: the range is broad, not infinite. These bounds were
not changed. Phone-appropriate limits remain a separate decision after
restoring navigation.

References: [Kirigami mobile layout](https://develop.kde.org/hig/layout_and_nav/),
[Koko zoom bounds](https://github.com/KDE/koko/blob/v25.04.0/src/qml/imagedelegate/BaseImageDelegate.qml).

### Photos: thumbnails and final launcher

The transparent gallery is worked around by automatically generating the
standard thumbnail cache. A capture without selection shows the test image.
Phone checks validate 256-pixel resizing, URI/date/size PNG metadata and
reuse without rewriting an unchanged cache. The operator subsequently
confirmed working Return and a hidden keyboard.

The helper uses the lmi Zink runtime when available, mobile mode, Breeze,
compose input and an offscreen worker without GLX. Three previously tested
engines did not restore KIO generation. A shmget=ENOSYS trace and installed
version sources support incompatibility of the preview path without shared
memory. The workaround covers the XDG image directory and launcher arguments,
with time/memory limits; it does not cover video.

The Images line near the bottom is AlbumView's folder navigation bar;
layout and clipped tabs remain unresolved. Zoom bounds were not changed.
See [Photos lmi](../../userspace/apps/PHOTOS-LMI.md) for diagnosis, sources
and limitations. Captures/test image stay outside Git. Temporary USB screen
inhibition is reserved for UI testing and must stop before battery measurement.

## Text Editor: saving and closure — October 3, 2026

Tested versions: gnome-text-editor 48.3-3, nautilus 48.3-2,
xdg-desktop-portal 1.20.3+ds-1 and GNOME backend 48.0-2.
The initial GTK dialog is wider than the display; Save is off-screen,
blocking a normal touch workflow. Remote keys alone could not test every
button. A temporary uinput touchscreen touched visible controls and was
destroyed after each gesture. wtype is a test tool, not a new build dependency.
No personal document was edited.

FileChooser routing now uses GNOME for Phosh while retaining other portal
preferences. The local Editor launcher forces GTK4 portals and exports
Wayland environment to the activation bus. Before that export, D-Bus-activated
Nautilus could not connect its display, with org.gnome.Mutter.ServiceChannel
error. Afterward it starts and provides the adapted chooser. This did not
require a new kernel or rootfs.

Checks actually completed: two lines typed in Editor; Save through the visible
button and disk contents checked; window disappearance followed by reopening
with visible text; actual Save As menu producing another identical file;
third line added/saved in that file; further closure with process disappearance.
Disappearance alone does not prove normal termination; see the journal
correction below.

Helper and routing file are installed on the phone; recipe and builder
staging prepare them for the next build. Desktop translations are retained;
New Window also routes through the helper. No heavy build ran. The operator
opened Save As, canceled and confirmed its usability with the confirmation
button visible. Keyboard remains visible in Editor input mode; this batch
does not correct general hiding. Sandboxed application portals are unvalidated;
document portal FUSE still fails on the current kernel.

Source: [GNOME 47 file dialogs](https://release.gnome.org/47/).

### Correction after operator-reported closure

Service inspection found signal=11/SEGV exits for reopen and ready tests.
Earlier process disappearance was insufficient evidence of normal closure;
that validation is withdrawn. Both test files exist, and the second contains
all three saved lines, reopened visibly in a capture. No test-text loss was
observed. No personal document was read.

An isolated reopening test with GSK_RENDERER=cairo was then active; the
persistent launcher remained unchanged at that checkpoint. Opening passed,
but crash cause and closure stability still needed testing. No available
coredump established whether renderer or portal caused the crash.

### Closure workaround: Cairo limited to Editor

Two independent GSK_RENDERER=cairo units ended with Result=success and
ExecMainStatus=0 after window closure. The second included saved-text
reopening, actual Save As menu and cancellation before closing. The
three-line file remains present. The durable helper now uses Cairo only
for Editor; other applications and the global renderer remain unchanged.

This is a workaround validated on that workflow, not a precise backtrace-based
fault location or prolonged stability validation. Keyboard hiding and other
menus remained open work at this checkpoint.

## Editor keyboard and menus — October 3 follow-up

Approximately 1.2 seconds holding the lower white bar hides the keyboard;
a second hold shows it, with Visible=true read from the bus. A temporary
uinput touchscreen produced the gesture without SetVisible; manual
confirmation remains desirable. No keyboard layout or persistent preference
was changed.

Preferences: opened through the menu, visible X and simulated-touch closure,
without changing options. Search: opened through the menu, Mobian entered,
match highlighted in the document, then dismissed with X. Three-line document
unchanged and Editor service active afterward. Replacement was not tested.

Shortcuts: significant overflow confirmed in a capture; no visible return
control. Remote Escape exits, which does not validate touch-only return.
App-specific Phoc adjustment did not fix it; a brief global test reduced it
without establishing usability. Global and Editor-specific settings were
both restored to false then. Defect remained open; no size fix published in
that batch.

## Priority to overall functionality: Calculator

The operator explicitly deferred menu optimization. Editor mobile-menu
experimentation stopped: no menu overlay added to the durable launcher or
builder. The Shortcuts defect remains documented.

Calculator 48.1-2+b1: keyboard hidden by long press on lower bar, then
2, +, 3 and = touched on actual keypad. Capture shows 2+3=5. Alt+F4 gave
Result=success and ExecMainStatus=0; independent reopening remained active
without initial errors. This validates elementary arithmetic/reopening,
not every mathematical mode or prolonged stability. No Calculator setting
or package was changed in this test.

## Calculator: preventing automatic keyboard return

The operator reported the keyboard still over Calculator after reopening.
The earlier hide gesture was not a durable correction. lmi-calculator sets
GTK_IM_MODULE=gtk-im-context-simple only for this process, keeping the native
keypad visible. No global keyboard setting changes. Isolated test:
Visible=false at startup and after touch-button 2+3=5; the field also accepts
8/2 through wtype-injected keys. No actual physical keyboard was connected.
Helper/desktop routing are integrated into installer and next-build staging;
no heavy build ran. Manual confirmation was pending at this checkpoint.

The simple context avoids this application's Wayland text-input activation.
Complex input methods are unvalidated in Calculator; other applications
retain their usual method.
Source: [GTK 4.18.6 input-context selection](https://github.com/GNOME/gtk/blob/4.18.6/gtk/gtkimmodule.c).

## Calculator confirmation and Clocks check

After installation the operator confirmed the full keypad without a keyboard.
This validates the corrected launcher's visual outcome, beyond the earlier
temporary hide gesture.

Clocks was already running in the background and presented through its
overview. Stopwatch initially zero; start, progression, lap around 3.1 seconds,
pause around 54.7 seconds and reset checked on captures. First pause attempt
used the old position, which moved after a lap; pause succeeded at the current
visible button. Returned to the initial World tab. No existing city or alarm
was removed/changed. Timer, wake from suspend and audible alarm were not yet
validated. Phosh overview stripes remain observed but untreated in this
functional batch.

Targeted camera check: Megapixels 1.8.3-1, qcom,kona-mtp compatible,
without its configuration in the package listing. sysfs shows
video0=cam-req-mgr and video1=cam_sync, with no standard capture node
established. Device files alone do not prove an operational camera.
Downstream-pipeline blockage remains open. No GStreamer enumeration,
speculative configuration or kernel build in this follow-up.

## Autonomous tests: Files, Papers, timer and Console

October 3, 2026 afternoon, one application at a time. Captures, PDF and test
data remain outside Git; no personal files changed. Gestures used uinput/wtype
without operator confirmation during absence; they do not validate every
application function.

Files: New Folder opened in an empty test-only directory; name entered and
Create touched. Disk presence and thumbnail verified. Selected folder opened
with Enter; an initial single touch selected rather than opened it. Lower
Back arrow worked, then Alt+F4 gave Result=success, ExecMainStatus=0.
Copy, rename and delete were neither tested nor declared validated.

Papers: synthetic two-page PDF created/checked on the host, then opened on
phone. Both pages readable on captures, with swipe navigation. Test unit
closed with status 0 and independent reopening passed. Search, annotation,
printing and forms untested. Test process subsequently stopped.

Clocks: Timer tab initially empty; one-minute shortcut started, capture at
58 seconds, paused at 10 seconds. Only the test timer was removed, then
returned to World. No existing city/alarm changed. Expiration, audio and
wake from suspend unvalidated.

Console 48.0.1 / GLib 2.84.4-3~deb13u5: test text and shell 2+3=5 visible.
After exit, terminal shows read-only and status -1; journal reports
waitid(P_PIDFD)=EINVAL. Current kernel is downstream 4.19.325; at this
checkpoint the observation did not yet identify the incomplete backport.
Official GLib opens a pidfd, uses waitid(P_PIDFD) and falls back to SIGCHLD
only when pidfd_open fails.

Two diagnostic units temporarily blocked pidfd_open using
SystemCallFilter=~pidfd_open and SystemCallErrorNumber=ENOSYS. Shell exit 0
then gives the normal blue termination banner, without -1. Shell exit 7
shows 1792 (raw wait status, 7<<8), not -1; exit-status presentation is still
incorrect. Both units were stopped; the filter is not in the launcher.
This mechanism can enforce NoNewPrivileges and interfere with privilege
elevation in a terminal; it is not a validated durable correction. No global
library, kernel configuration or Console preference was replaced.

Source: [GLib 2.84.4 gmain.c](https://github.com/GNOME/glib/blob/2.84.4/glib/gmain.c).
Next priority: repair Console process monitoring without restricting its
uses, then continue overall app functions. Presentation improvements remain
secondary.

### Console syscall incompatibility confirmed

A Python probe independent of GTK/GLib created its own child exiting at 7,
successfully opened its pidfd, then obtained errno=22/EINVAL from
waitid(P_PIDFD). waitpid fallback reaped that child with exit=7. All
descriptors closed; no test process remains. This confirms incompatibility
of the two interfaces on the booted kernel beyond a GUI application trace.

Preserved reference source a5b3099017ae contains SYSCALL_DEFINE2(pidfd_open)
in kernel/pid.c. include/uapi/linux/wait.h defines only P_ALL, P_PID and P_PGID;
kernel/exit.c has no P_PIDFD branch. Source inspection agrees with the
hardware probe. Adding pidfd_open without waitid support matches GLib's
observed failure. No kernel fix compiled or booted in this test. Next fix
must make these interfaces coherent and validate normal and signaled exits
before declaring Console repaired.

Calendar started, but both captures failed with failed to copy output DSI-1.
ScreenSaver.GetActive=true, USB online=1: screen was locked. Unit stopped
without creating an event; visual functionality was unvalidated at that
checkpoint. Do not count startup alone as checklist success.

## Calendar local workflow — October 3, after quota reset

gnome-calendar 48.1-2+b1: opening at October 3, navigation to November and
Today return to October checked on captures. Personnel calendar uses a local
backend; no remote account added. After explicit operator authorization,
only dummy event TEST-LMI-AGENDA-20261003 was saved, with visible list title
and matching SUMMARY in the ICS calendar. No participant, invitation or
configured reminder. Preview opened; edit dialog exposed Delete Event.

The first swipe started on the keyboard and inserted gt into the dialog
title; this edit was not saved. Long press on lower bar hid the keyboard;
swipe within content revealed Delete. Notification still offered Undo;
closing it was followed by visual removal and zero test SUMMARY occurrences
in the calendar file. Independent reopening showed no event/test leftover.

Second unit used RemainAfterExit=yes to preserve metadata after closure:
Result=success, ExecMainCode=1 (normal exit), ExecMainStatus=0,
SubState=exited. Default values from a garbage-collected unit are not used
as exit evidence. No Calendar launcher/package changes or renderer fix
needed on this workflow. Synchronization, recurrence, invitations and audible
reminders remain unvalidated.

## Contacts deletion-crash workaround — October 3, 2026

gnome-contacts 48.0-2+b1, local system address-book backend, initially empty.
UI created TEST-LMI-CONTACT-20261003 without phone/email. Persistence after
exit status 0 and reopening verified. Name search finds it; nonmatching name
returns an empty list. No personal contact changed, remote account added,
message sent or call placed.

Delete left the window frozen, then service ended with Result=signal,
ExecMainCode=2 and ExecMainStatus=11. Contact still existed after reopening;
deletion was not validated. App-only GSK_RENDERER=cairo then allowed removal
and normal closure: Result=success, ExecMainCode=1, ExecMainStatus=0.
A second independent durable-helper cycle created and removed
TEST-LMI-CONTACT-20261003-B with the same normal codes. Undo notifications
were closed to finalize removals.

lmi-contacts helper and desktop routing are installed. DBusActivatable=false
prevents bypass through that launcher; upstream desktop translations remain.
Installer and Phosh staging include the helper for the next build, not run.
Global renderer unchanged. Without a backtrace this establishes neither
precise SIGSEGV cause nor prolonged stability. Contact editing, photo,
calls, messaging, import/export, merge and synchronization unvalidated.

## Settings navigation — October 3, 2026

Installed gnome-control-center 1:48.4-1~deb13u1. Back from the restored panel
opens the overview. Mouse and Touchpad, Keyboard and System opened through
simulated touch. Mouse/touchpad controls concern physical devices, not the
phone touchscreen; their presence does not prove such a device is connected.
No input-source, network, time or power setting changed in these tests.

Test Your Settings opens a click/scroll dialog without visible Close.
Two outside touches did not dismiss it; remote Escape did, then Back
restored the list. Touch-only dismissal unvalidated. Mouse-test functions
were not validated with a physical mouse.

Two Alt+F4 closures observed with retained service results:
Result=success, ExecMainCode=1, ExecMainStatus=0. No renderer change needed.
Even closing after returning to the overview, reopening showed System.
org.gnome.Settings last-panel remembers the last panel. Installed schema says
an unknown value selects the first panel; [GNOME 48.4 source](https://github.com/GNOME/gnome-control-center/blob/48.4/shell/cc-window.c)
confirms fallback in maybe_load_last_panel. Clearing that preference is not
a demonstrated overview-on-launch fix. Preference not reset; no helper installed.

Temporary services and USB-only screen inhibition stopped after testing.
All panels/menus still require testing; Settings is not fully validated.

## Geary, Calls and Close buttons — October 3, 2026

Geary 46.0-7: startup/reopening without account, Add form and Back cancellation
verified. Back from Accounts closes normally; another Alt+F4 closure also
gave Result=success, ExecMainCode=1, ExecMainStatus=0. No account/message
created. Mail functions and menus requiring login unvalidated.

Calls 48.2-1: Recents and Keypad displayed; VoIP Accounts opened. Banner
reports no available modem/VoIP account. No number, call or account created.
Initial org.gnome.desktop.wm.preferences button-layout was appmenu:, omitting
Close. appmenu:close exposed the button in observed GTK windows and VoIP
dialog. A new instance verified simulated-touch dialog dismissal while Calls
remained visible, then normal closure through its own button (status 0).
Settings also closed normally through the restored button.

Correction installed in the phone user preference and prepared as next-build
schema default. Custom headers are not guaranteed: mouse Test Your Settings
still has no dialog Close. That defect remains open. Other apps' Shortcuts
had not been rechecked at this checkpoint. Test units stopped; no image build.

Recipe validation: bash -n and git diff --check pass. Installed schema/enum XML
and overrides copied to a temporary directory with the new override;
glib-compile-schemas --strict passes. GSETTINGS_BACKEND=memory reads
appmenu:close for generic, Phosh and Phosh:GNOME contexts. Temporary directory
automatically removed. This does not rebuild a complete image.

## Editor Shortcuts recheck — October 4, 2026

button-layout=appmenu:close remains set. Editor 48.3-3 launched through
lmi-text-editor; libadwaita 1.7.6-1~deb13u1. Actual Keyboard Shortcuts menu
opens a view wider than display: left labels clipped and no accessible dialog
Close. Long press on bottom bar hides keyboard and frees height without
fixing horizontal overflow. Touch-only dismissal unvalidated; remote Escape
returns to document.

App-local Phoc scale-to-fit for org.gnome.TextEditor, initially false, was
enabled and reverted after no visible improvement. No global scaling change
in this initial recheck. Embedded help-overlay.ui declares GtkShortcutsWindow
and GtkShortcutsSection max-height=15; unmodified. No resource patch/new
helper installed. Test document unchanged. After Escape, main Close button
gave normal termination (Result=success, ExecMainCode=1, ExecMainStatus=0).
Test unit stopped. Restored buttons alone do not fix oversized shortcut windows.

## Discussions shortcuts and Phoc adjustment — October 4, 2026

Discussions launched through lmi-chatty-safe and a test unit limited to
384 MiB with no swap. Without Phoc adjustment, Shortcuts overflows horizontally
and its Close button is off-screen. Global Phoc scale-to-fit changed from
false to true. Whole dialog then visible with accessible Close. Simulated-touch
close, actual-menu reopen, second dialog close and normal Discussions closure
verified: Result=success, ExecMainCode=1, ExecMainStatus=0 for the wrapper unit.
No account/message created. Transient black lines appeared in the first
post-toggle capture, absent in the reopened-dialog capture; this does not
validate a general GPU fix.

Editor retested separately: dialog shrinks but still clips on both sides.
Touch-only dismissal remains unvalidated. Escape followed by main Close
gave status 0. No test file changed; test units stopped. Global adjustment
remains enabled for oversized windows; Editor-specific preference remains
false as before its earlier test. No network/power preference changed.

Next-build schema override and compiled-value check prepare this default;
no image rebuilt. Amberol and other applications' shortcuts need rechecks.


Recipe checks for window adjustment: bash -n and git diff --check pass.
Installed schema/enum XML and overrides, with both lmi window overrides,
compile with glib-compile-schemas --strict in a temporary directory.
Memory-backend reads return scale-to-fit=true and button-layout=appmenu:close
in generic, Phosh and Phosh:GNOME contexts. Temporary files are automatically
removed. These checks do not build or boot an image.

## Recorder and missing-card audio startup — 2026-10-04

KRecorder 25.04.0-2 opened, navigated to Configuration and returned to its
recording list. The Audio Input chooser was empty. Two simulated-touch
main-window closes, including a reopening after the service correction,
returned Result=success, ExecMainCode=1, ExecMainStatus=0. No recording was
started, no existing recording was changed and temporary test units stopped.
Configuration labels were French in the captures; full translation untested.
The on-screen keyboard appeared in Configuration without a text-entry action;
that usability defect remains open. Codec, container and recording operations
have not been validated.

This runtime had no ALSA card: /proc/asound/cards reported no soundcards and
/dev/snd contained only timer. The installed speaker adapter failed to open
lmi_speaker; PipeWire terminated with exit status 234 and WirePlumber stopped.
This does not overturn earlier clear-speaker validation on the separate
temporary diagnostic boot, nor identify the currently loaded boot image by
hash. The displayed kernel release alone cannot distinguish those images.

The adapter now declares flags = [ nofail ], as specified by the
[PipeWire configuration documentation](https://docs.pipewire.org/page_man_pipewire_conf_5.html).
After installation of this single configuration change and an audio-service
restart, PipeWire 1.4.2, pipewire-pulse and WirePlumber stayed active through
the recorder reopening/close test. wpctl showed only Dummy Output and no
audio source. The correction restores server availability when the card is
absent; it does not restore physical speaker or microphone operation. The
missing-card warning remains expected. Physical-card playback with the new
flag awaits the diagnostic boot retest. No kernel/image build or flash ran.

## Diagnostic-boot audio retest — 2026-10-04

The operator loaded the preserved reset-GPIO diagnostic boot temporarily
through Windows Fastboot. The host file SHA-256 was verified as
`43132d1ad4a73728e3e4408ff3570d7693d43bc45bbc9ab9945880e1d1ae2638`.
No partition was flashed. SSH initially refused the connection and became
available on the next attempt without a USB unplug/replug request.

The ALSA `kona-mtp-snd-card` returned, and the revised PipeWire speaker adapter
loaded normally with `flags = [ nofail ]`. Ten seconds of the existing music
fixture played through `pw-play --target=lmi-speaker --volume=0.5` with exit
status 0. The operator confirmed clear music without distortion. That volume
is the stream's software setting, not a measurement of speaker loudness.
No microphone source was automatically exposed to applications.

A private capture experiment used the on-device OEM static overlay's
`speaker-mic` route, plus the base `audio-record` route: ADC4/INP5 via
TX SMIC MUX0, DEC0 and TX_CDC_DMA_TX_3 into MultiMedia1. ALSA hooks retained
and restored all eight controls. PCM preparation succeeded with mono S16_LE,
48 kHz. A custom nonblocking reader first captured zero frames; an explicit
start produced a short sample, but a subsequent trial failed with EFAULT and
kernel `msm_pcm_capture_copy: Invalid dsp buf offset`. That trial is not counted
as microphone validation.

The existing ALSA aplay executable's standard arecord mode subsequently
captured exactly 384,000 frames (eight seconds), peak 1,923 and RMS 77.34 in
signed-16 units. All eight controls matched their original values afterwards.
No persistent microphone configuration or PipeWire source was installed.
Capture data exists, but recognition of the recorded video sound and app-level
recording still require validation. Audio fixtures/recordings remain private,
outside Git. A preview amplified eight times was prepared without clipping;
listening confirmation is pending at this checkpoint.

## Microphone and Recorder result — 2026-10-04

Native eight-second capture was operator-recognized after amplified playback.
An opt-in PipeWire microphone source and numeric KRecorder WAV/PCM settings
then produced two complete 8.96-second recordings. The final saved trial
survived normal close/relaunch and displayed `0:08`. After replaying it,
the operator confirmed that the application-produced recording was good. Both hardware PCMs
closed at idle. This supersedes earlier no-source/microphone-unvalidated
observations on this diagnostic boot only. Full UCM2, headset/earpiece and
durable boot deployment remain pending. See the
[audio integration record](../../userspace/audio/README.md#microphone-and-recorder-capture--2026-10-04).


## Recorder controls and normal launcher — 2026-10-04

The functional recording reported as quiet was confirmed good after replay;
the operator clarified that playback volume, not microphone gain, was too
low and set the output to 1.00. Microphone gain remains 1.00.

The default Qt theme left Recorder's Play/Pause, Stop and action buttons
without visible icons. Selecting `XDG_CURRENT_DESKTOP=KDE` only in Recorder's
process resolves the already installed Breeze icons and exposes a window
Close button. The `lmi-recorder` wrapper also retains the tested mobile and
compose input settings. Phosh and other apps retain their session environment.
The normal desktop entry keeps upstream translations and invokes the wrapper;
the app installer stages this wrapper for the next image. Audio configuration
and version-specific recorder preferences remain a separate opt-in.

On-phone checks: launch from the Phosh icon, record, usable Save/Discard
dialog with visible icons, save a WAV, and close using the visible window
button. Playback reached the fixture's eight-second duration; Back returned
to the list. Other codecs, export destinations and every edit operation
remain unvalidated. No new image was built and no session-wide theme changed.

## Timer feedback and clock offset — 2026-10-04

Timer sound is now operator-confirmed after installing the missing Feedback
service and PulseAudio backend. Test timers were removed. The reported clock
offset was measured while NTP had no Internet route; the system clock was
aligned from Windows and saved without changing Wi-Fi. Recorder Rename and
Delete passed on a temporary test file. See the
[scoped validation record](lmi-clock-feedback-2026-10-04.md).

## Files operations, Calculator menus and Settings trial — 2026-10-04

These checks used simulated touch on the existing diagnostic boot, one app
at a time. They do not represent a new image or additional operator listening.

Files: a dedicated test directory contained one 39-byte text fixture. Copy
created an identical second file; Rename changed that copy's filename. Trash
removed it from the directory and recorded the expected original path.
The source stayed intact. After normal app closure (status 0), cleanup checked
the exact source contents, trash contents and origin metadata, then removed
only those fixtures and their empty directory. No general trash cleanup ran.
The keyboard remained visible after Rename; the tested bottom long press did
not hide it. The globe menu offered layouts and keyboard settings, without a
Hide action. Remote DBus hiding allowed continuation but is not a UI solution.

Calculator: touch buttons produced 9²=81; mode selection reached Advanced and
Conversion. Entering 180 degrees produced 3.141592654 radians. Returning to
Basic and opening/closing Preferences through its visible Close button passed,
without an overlaid keyboard. Shortcuts remained horizontally clipped and
without a visible Close; an outside touch failed to dismiss them. Injected
Escape dismissed the dialog, then normal app closure returned status 0.
Financial/programming calculations and other conversions remain unvalidated.

Settings: resetting the last-panel preference did not open a general overview;
it opened Wi-Fi. The installed help exposes no overview option. The original
preference was restored to `mouse`, and the app closed normally with status 0.
No persistent Settings fix was installed and no Wi-Fi switch was changed.
Overview-on-launch and touch-only dismissal of the mouse-test dialog remain
open issues. Screenshots stay private and outside Git.

## Papers search — 2026-10-04

The existing synthetic two-page PDF was opened without modifying it. Through
simulated touch, the sidebar and its search control opened. Injected text
`Xiaomi` returned two results, one per page; `TEST-LMI-NOT-PRESENT` displayed
`Aucun résultat trouvé`. Touching the second positive result opened page two
and highlighted the matching word. The keyboard hid when the result opened,
without a remote OSK hide command in this test. Normal closure returned
Result=success and ExecMainStatus=0. This does not validate annotation,
printing, forms or arbitrary document formats.

The app journal emitted `pixman_region32_init_rect: Invalid rectangle passed`
during navigation. No crash occurred in this scoped test; the warning's cause
and broader rendering impact remain unestablished. Screenshots and the PDF
fixture remain private, outside Git. No persistent app change was installed.

Save As was also checked from the actual document menu. After loading, the
chooser displayed Documents and an editable name field; Save remained visible
above the keyboard. A distinct temporary PDF name created a 2,273-byte copy
identical to the original. The chooser closed and OSK hid after saving.
Normal application close returned status 0. Only the new copy was removed
after another content comparison; the original PDF fixture remains intact.

## Keyboard home-bar gesture — 2026-10-04

With Phosh 0.46.0 and Squeekboard 1.43.1, a simulated two-second hold centered
on the bottom white home bar hid the keyboard in Text Editor. Repeating the
gesture showed it, then another hold hid it. DBus Visible values and captures
confirmed the transitions. The editor restored its existing test document;
no text was entered or saved. Normal close returned status 0.

In Files, a new isolated 29-byte fixture was renamed. This attempt hid OSK
automatically after Rename, unlike the earlier observation. The same home-bar
hold then showed OSK, and another hold hid it. The fixture was removed only
after exact content comparison and its empty directory removed. Files was
quit normally after its window closed. No layout, accessibility preference,
delay setting or application wrapper was modified.

Practical instruction: hold the center of the bottom white home bar for about
two seconds to toggle the keyboard. This is simulated-touch validation in
these two apps, not operator confirmation or proof for every dialog. The
installed Phosh schema describes osk-unfold-delay as a long-press delay factor;
its existing value 1.0 was retained. Shorter earlier failed holds remain
recorded and do not establish that the two-second gesture is universally
required. A visible, discoverable Hide control remains desirable.

## Files touch multiselection — 2026-10-04

The operator clarified the deletion report: individual deletion was found;
the remaining difficulty was selecting several files. On the phone, opening
OSK through the home-bar hold, selecting Terminal from the globe menu and
tapping Ctrl latched the modifier. Touching two additional folder tiles kept
the original selection, showing three selected folders. No file was opened,
moved, copied or deleted during this selection check. Ctrl was subsequently
released; the grouped selection ended with one item still selected. The Terminal layout remains available
for the operator; no system-wide default or keyboard configuration changed.

Practical sequence: show OSK, globe → Terminal, tap Ctrl, then tap each wanted
item. Tap Ctrl again after selecting to release it. The normal file context
menu can then act on the selection, but grouped Trash itself has not been
tested and should not be inferred from this selection-only check. A native
mobile checkbox/selection mode remains preferable to this keyboard-assisted
workaround. See the official
[GNOME selection behavior](https://help.gnome.org/gnome-help/nautilus-behavior.html).

## Mobile multiselection requirement remains open

The operator rejected the Terminal/Ctrl sequence as too complicated for a
phone. Its technical validation does not meet the usability requirement.
The next solution must provide direct touch selection, preferably checkboxes
and a clear selection mode, without exposing keyboard modifiers.

Initial availability checks found no index-fm candidate in the phone's
current APT lists; Portfolio was also unavailable. This does not prove their
absence from other repositories or distribution formats. Neither app was
installed, no package lists were refreshed, and Nautilus remains available.
No alternative manager or native multiselection fix is claimed validated.

## Portfolio native touch multiselection — 2026-10-04

The earlier availability check queried the wrong package name (`portfolio`).
The phone's existing Debian trixie/main index offers `portfolio-filemanager`
1.0.2-1. Its 58,184-byte package was downloaded from Debian, checked against
the APT SHA-256 (`f6d9e75db0ce1440fd7536d5c1ebad8cbdeecbef5381a9f3fb62305fb1ad9a50`)
and installed without additional dependencies, upgrades or removals.
`dpkg --audit` was empty. No package-list refresh or phone network change
was made. Its upstream launcher advertises `X-Purism-FormFactor=Mobile`.

Simulated touch held the first disposable text file, then tapped the second;
both rows remained highlighted, the third unselected, and OSK stayed hidden.
The bottom action bar was available. This meets the input requirement without
Terminal/Ctrl, but operator usability confirmation remains pending.

Deletion opens an inline confirmation with three buttons, left to right:
permanent confirmation (`emblem-ok-symbolic`), Cancel, and Trash
(`user-trash-symbolic`). The first icon rendered poorly and the description
was ellipsized on this phone. The initial test tapped the left button:
both selected fixtures were permanently removed, not sent to Trash; the third
file remained intact. No user file was selected or deleted. Do not treat this
as a verified corbeille operation. The source and UI resource confirm the
rightmost button is the separate Trash action.

Portfolio is added to the app recipe alongside Nautilus. No wrapper, desktop
default change, upstream source patch or image build is included. The old
Terminal keyboard was restored to French and hidden after the earlier trial;
its visible state was test residue, not evidence of an automatic dismissal
fix. General menus, copy/move, storage handling and complete translation
remain outside this selection test.

### Operator rejection of Portfolio

The operator reported that the application provided no useful improvement.
The simulated selection result does not establish acceptance or resolve the
reported file-management problem. The operator clarified that a second application was unnecessary. The
package was removed from the next app recipe and uninstalled from the phone
without autoremove. `dpkg --audit` remained empty. No user data was removed
as part of this rollback. Native touch selection in the existing
Files application remains an open requirement.

## Functional priority and camera recheck — 2026-10-04

The operator confirmed Files was functional and rejected adding another file
manager. Basic operation takes priority, followed by essential menus;
translation and additional features are last. Already accepted basic functions
must not be repeatedly tested instead of addressing a nonfunctional app.
Touch multiselection remains a recorded limitation, not grounds to reopen
the entire Files validation.

A fresh Megapixels 1.8.3-1 launch used a bounded user service (256 MiB memory,
zero swap, maximum 15 seconds). It exited immediately with status 1 and:

```text
Could not find any config file
/usr/share/megapixels/config/qcom,kona-mtp.ini not found
```

The current sysfs names still identify video0 as `cam-req-mgr` and video1 as
`cam_sync`. This repeats the existing blocker, not a capture success. No
GStreamer device enumeration, camera stream, speculative INI or build was
started; the diagnostic service was stopped and no Megapixels process remained.

Targeted review of the preserved a5b3099017ae source found that
`techpack/camera/drivers/cam_req_mgr/cam_req_mgr_dev.c` supplies event
subscription and a private ioctl accepting `VIDIOC_CAM_CONTROL`, not a
standard capture-format/buffer/stream ioctl table. The sensor driver at
`techpack/camera/drivers/cam_sensor_module/cam_sensor/cam_sensor_dev.c`
registers core ioctl/power operations, with no pad operation table there.
These source observations support the earlier standard-query failures; they
do not establish individual sensor detection or prove that every runtime
camera component has been identified.

Camera work needs a demonstrated capture backend compatible with this
downstream stack, or a provenance-matched standard driver pipeline. Adding
another camera app or inventing only an INI does not establish that backend.
See the [camera blocker](archi-validation-02-camera-blocker-2026-09-27.md).

### Camera backend feasibility follow-up

A read-only, bounded metadata probe confirms OEM camera objects and the
Android loader exist, but the required service environment is incomplete.
Binder is enabled in the current kernel; its device nodes and Android property
service are absent, and the HIDL manager symlink is unresolved. No proprietary
binary was executed and no camera stream, service or mount was started.
An alternate source already describes CAMSS/OV13B10, but its camera is not
validated and it is not the running kernel. The reproducible inspection and
backend acceptance gates are in the [camera README](../../userspace/camera/README.md#oem-backend-feasibility--2026-10-04).
Camera capture remains blocked; this is progress on identifying prerequisites,
not a working camera or a replacement app installation.

### Isolated camera HIDL milestone

The HIDL manager was found in system_ext and registered on private Binder
after a diagnostic-only synthetic-context adaptation for the no-SELinux
kernel. Physical camera nodes and networking were excluded; no camera
provider or capture was started. Runtime CPU use was unexpectedly high and
properties/client IPC remain unresolved. The process and all temporary
mounts/mappings were removed. See the [backend test and limits](../../userspace/camera/README.md#isolated-hidl-registration-milestone--2026-10-04).
Megapixels remains nonfunctional; this milestone does not change that status.
