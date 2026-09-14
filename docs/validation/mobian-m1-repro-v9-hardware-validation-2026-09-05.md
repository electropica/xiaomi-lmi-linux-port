# Mobian M1 REPRO v9 hardware validation — 2026-09-05

**D-v43 XDG USER DIRS TIMEOUT FIX VALIDATED ON HARDWARE**

Target: POCO F2 Pro / Redmi K30 Pro (`lmi`) with downstream D-v43.

## Tested artifact

- source commit:
  `e7e63bad6cf6327ae409613c9c9d91e42d26256f Avoid D-v43 xdg-user-dirs session timeout`
- Android sparse userdata:
  `Mobian-M1-REPRO-v9-userdata-phosh-4G.android-sparse.img`
- SHA-256: `17e5c0427358803beac9f2313caa008fd3303119c0020ebacc42a45a15f9b401`
- userdata flash: PASS
- D-v43 boot: PASS

No generated image is stored in Git.

## v8 failure and targeted correction

On v8, GNOME Session launched the Debian `xdg-user-dirs.desktop` entry in its
`Initialization` phase. GLib then failed to track the short-lived process:

```text
waitid(pid:3317, pidfd=14) failed: Invalid argument (22)
```

Because GNOME Session did not observe process exit or registration, it kept
the entry pending for roughly 90 seconds and then reported:

```text
Application 'xdg-user-dirs.desktop' failed to register before timeout
```

Squeekboard started immediately after that phase timeout. The recipe fix marks
only this legacy autostart `X-GNOME-HiddenUnderSystemd=true` and preserves the
same `/usr/bin/xdg-user-dirs-update` operation through the device-specific
`xdg-user-dirs-lmi.service` oneshot before `gnome-session-pre.target`.

## v9 result

The fresh v9 image reported for `xdg-user-dirs-lmi.service`:

```text
Result=success
ExecMainCode=1
ExecMainStatus=0
```

The service is `Type=oneshot` without `RemainAfterExit`, so inactive/dead after
successful completion is expected. The former registration-timeout message
was absent.

All localized XDG directories existed:

```text
XDG_DESKTOP_DIR=/home/mobian/Bureau
XDG_DOWNLOAD_DIR=/home/mobian/Téléchargements
XDG_TEMPLATES_DIR=/home/mobian/Modèles
XDG_PUBLICSHARE_DIR=/home/mobian/Public
XDG_DOCUMENTS_DIR=/home/mobian/Documents
XDG_MUSIC_DIR=/home/mobian/Musique
XDG_PICTURES_DIR=/home/mobian/Images
XDG_VIDEOS_DIR=/home/mobian/Vidéos
```

Squeekboard was running as `/usr/bin/squeekboard`, appeared immediately after
unlock, and logged:

```text
Info: Loaded layout Resource: fr
```

The French AZERTY layout was functional. This validates both the compiled
`[('xkb', 'fr')]` default and the targeted xdg-user-dirs workaround on a fresh
image.

## Remaining scope

The workaround does not change GNOME Session's global timeout and does not
remove or bypass `xdg-user-dirs-update`. The underlying D-v43 incompatibility
with GLib child watching through `waitid`/pidfd remains relevant to other
short-lived processes and is not claimed to be fixed globally.
