# Snapshot 51 preconditions on the Linux 7.2.12 boot — October 28, 2026

Date: 2026-10-28
Canonical repository: `/home/linuxagent/xiaomi-lmi-linux-port`, branch `lmi-linux7`.
Handset: POCO F2 Pro / Xiaomi lmi, permanent `system5` boot, kernel
`7.2.12-lmi-community-port1-dirty`, Debian 13 (trixie) userspace, session
account `mobian`.

Companion to the Snapshot51 upgrade assessment of 2026-10-26. That record
established that the Flatpak deployment of the Snapshot 51 candidate failed on
the handset because the kernel of that moment did not provide `STATX_MNT_ID`.
This record measures the same facility on the kernel that the permanent boot
runs now, and checks the camera side of the upgrade.

## 1. The deployment blocker is gone on this kernel

The Flatpak runtime refuses to deploy without mount identifiers: the
`libglnx` path-chasing guard requires `TYPE`, `INO` and either `MNT_ID` or
`MNT_ID_UNIQUE`, and it emits `statx didn't return all required fields`
otherwise. On the 2026-10-26 attempt the `statx` masks were `0xfff`, `0x7ff`
and `0xfff`, without `MNT_ID`.

Measured on the running Linux 7.2.12 kernel of the permanent boot, with a
`statx` probe asking for `STATX_BASIC_STATS | STATX_MNT_ID`:

```
kernel: 7.2.12-lmi-community-port1-dirty
/                        mask=0x17ff ino=2 mnt_id=32 mnt_id_present=True
/proc                    mask=0x17ff ino=1 mnt_id=26 mnt_id_present=True
/home/mobian/.local      mask=0x17ff ino=242822 mnt_id=32 mnt_id_present=True
MNT_ID_AVAILABLE
```

`STATX_MNT_ID` is in the mask on every path, including the user directory
that the deployment writes to. The kernel of the permanent boot provides the
facility that the runtime requires, so the deployment that failed on the
downstream 4.19 kernel has no kernel-level reason to fail here. No security
check is relaxed and no mount identifier is invented: the facility is really
provided by this kernel.

## 2. The state left on the handset

The failed attempt left its objects in place, so a retry does not download
the world again:

| Item | State |
|---|---|
| `flatpak` | 1.16.6-1~deb13u3, installed on 2026-10-26 |
| `flathub` user remote | configured |
| `/home/mobian/.local/share/flatpak` | 1.7 GB retained: the repository objects and the `org.gnome.Platform` runtime for aarch64 |
| Applications | none: the deployment of the candidate itself never completed |

## 3. The camera side of the upgrade

The upstream `meson.build` of Snapshot 51.0 was read:

```
dependency('gtk4', version: '>= 4.18')
dependency('libadwaita-1', version: '>= 1.8.alpha')
dependency('glycin-2', version: '>= 2')
dependency('glycin-gtk4-2', version: '>= 2')
dependency('gstreamer-1.0', version: '>= 1.20')
dependency('gstreamer-video-1.0', version: '>= 1.20')
# Needed for camerabin
dependency('gstreamer-plugins-bad-1.0', version: '>= 1.20')
```

The camera of Snapshot 51 is therefore still a GStreamer `camerabin` pipeline,
with `glycin-2` added for the capture side. The session already carries the
whole camera stack of that path:

| Element | State on the handset |
|---|---|
| `libgstcamerabin.so` | present, from `gstreamer1.0-plugins-bad` 1.26.2-3 |
| `libgstpipewire.so` | present |
| `libgstvideo4linux2.so` | present |
| `libgstlibcamera.so` | present, but the PipeWire `libspa-0.2-libcamera` plugin is **not** installed |

This matters for the producer that publishes the Linux 7 camera on PipeWire:
the session enumerates cameras through the PipeWire device provider, and the
producer publishes exactly that kind of node. The libcamera provider is
present but has no camera behind it, because the PipeWire libcamera plugin is
absent, so the libcamera route stays closed and the PipeWire route stays the
one that matters.

## 4. Consequences for the camera work

1. The producer contract does not change: a PipeWire node with
   `media.class` Video/Source and `media.role` Camera is what the session
   provider enumerates, with Snapshot 48 and with Snapshot 51.
2. The launcher has to know which application it drives. The Flatpak candidate
   publishes the same application id, `org.gnome.Snapshot`, but it is a
   different executable, and it installs a desktop entry of its own whose
   `Exec` is `flatpak run org.gnome.Snapshot`. That entry would open the
   application **without** the launcher, and therefore without the camera
   producer. The bundle entry that points at `/usr/local/bin/lmi-snapshot`
   has to keep shadowing it.
3. `lmi-snapshot-tuning.so` is preloaded into the application and hooks the
   internals of Snapshot 48.0.1, which is a C program. Snapshot 51 is a Rust
   rewrite, so the preload becomes inert and the `GSK_RENDERER` and
   `GDK_DISABLE` workarounds have to be re-evaluated for it.
4. The bundle pins `gnome-snapshot=48.0.1-1`; with a Flatpak candidate in
   parallel, the pin has to express "the native application, or the Flatpak
   candidate".

## 5. What is not claimed

- Snapshot 51 is **not** installed. Nothing was deployed on the handset.
- The camera of Snapshot 51 is **not** qualified. The dependency list and
  the presence of the plugins are evidence that the path exists, not a
  result.
- The flatpak deployment is **not** retried in this record: it changes the
  session account of the handset and is an operator decision.

The path is open on the kernel of the permanent boot, and the camera producer
that this branch prepares stays valid for both application versions.
