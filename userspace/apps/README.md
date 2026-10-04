# lmi application integration

Application fixes are maintained on the `developpement` branch. Most changes
are launch wrappers, dependencies or session preferences; they are not forks
of the upstream applications. The original system binaries remain in use.

## Where to find each fix

| Application or feature | Implementation | Purpose and limits |
|---|---|---|
| Text Editor | [lmi-text-editor](files/lmi-text-editor), [portal routing](files/phosh-portals.conf) | GNOME file chooser routing and app-only Cairo workaround. Shortcut dialog remains clipped. |
| Calculator | [lmi-calculator](files/lmi-calculator) | Simple app-only input context keeps the native keypad visible. |
| Contacts | [lmi-contacts](files/lmi-contacts) | App-only Cairo workaround for deletion/teardown crash. |
| Discussions (Chatty) | [lmi-chatty-safe](files/lmi-chatty-safe), [diagnosis and installation scope](CHATTY-LMI.md) | Isolated GStreamer plugin view and bounded memory scope. SMS/MMS and modem remain unvalidated. |
| Photos (Koko) | [lmi-photos](files/lmi-photos), [thumbnail helper](files/lmi-photos-thumbnails), [diagnosis](PHOTOS-LMI.md) | Mobile launch environment and image-thumbnail workaround. Does not establish camera capture or video support. |
| Clocks timer alert | [package recipe](scripts/install.sh), [validation](../../docs/validation/lmi-clock-feedback-2026-10-04.md) | Explicit Feedback service and PulseAudio sound backend restore the tested timer alert; suspend wakeup and closed-app alarms unvalidated. |
| Recorder (KRecorder) | [lmi-recorder](files/lmi-recorder), [audio integration and opt-in settings](../audio/README.md#microphone-and-recorder-capture--2026-10-04) | App-only KDE theme restores action icons and Close. Microphone route, scheduling workaround and WAV/PCM preferences remain opt-in; the app installer stages only the launcher. |
| Flashlight | [application](files/lmi-flashlight.py), [desktop entry](files/lmi-flashlight.desktop), [usage](files/LMI-FLASHLIGHT.md) | lmi flashlight controls. |
| Close buttons | [Phosh schema override](../phosh/files/92_lmi-window-controls.gschema.override) | Restores Close in standard GTK headers; custom headers can still omit it. |
| Oversized windows | [Phoc schema override](../phosh/files/93_lmi-scale-to-fit.gschema.override) | Adjusts oversized windows. Chatty shortcut dismissal tested; Editor still clips. |

[install.sh](scripts/install.sh) installs the application integration and
launcher routing. See its switches and the app-specific documents for the
exact activation scope. The [Phosh builder](../phosh/scripts/build-m1-phosh.sh)
stages the next image's integration and validates session defaults. Preparing
a recipe is distinct from actually building and booting an image.

## Validation

The [application checklist](../../docs/validation/lmi-app-checklist-2026-10-03.md)
distinguishes operator confirmation, simulated-touch checks, historical
observations and unresolved functions. The
[project status](../../docs/status/MOBIAN-STATUS.md) records current milestones.
Application startup alone does not validate audio, camera, cellular service,
mail synchronization or every menu.

Repository documentation is written in English. Original UI labels and
operator quotations may remain in their original language for identification.

### Files and Calculator scope — October 4

The current launcher supports the tested Calculator arithmetic, angle
conversion and Preferences closure without OSK overlap. Its Shortcuts dialog
still clips and required injected Escape; no touch-only fix is claimed.
Files Copy/Rename/Trash passed on disposable fixtures, but the keyboard stayed
open after Rename. The Settings last-panel reset trial was reverted because
it did not open an overview. These checks introduced no new launch wrappers.
Full details and remaining functions are in the application checklist above.

### Keyboard gesture

Hold the center of Phosh's bottom white home bar for about two seconds to
toggle the keyboard. Simulated-touch checks showed hide/show/hide in Text
Editor and show/hide in Files on October 4, without a settings change.
Operator confirmation and other dialogs remain pending; see the checklist's
keyboard home-bar gesture record. A visible Hide control remains desirable.

### Files touch multiselection

Show the keyboard with the home-bar hold, choose globe → Terminal, tap Ctrl,
then touch the wanted items. Tap Ctrl again to release it after selecting.
Three-folder selection was checked by simulated touch; no grouped deletion
was performed. This uses the existing terminal keyboard, without a new
launcher or preference. Details are in the checklist above.
