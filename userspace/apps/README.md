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
