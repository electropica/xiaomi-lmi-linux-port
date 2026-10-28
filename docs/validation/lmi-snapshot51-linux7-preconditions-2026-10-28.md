# Snapshot 51 on the Linux 7.2.12 boot — deployment, third blocker, convergence — October 28, 2026

Date: 2026-10-28
Canonical repository: `/home/linuxagent/xiaomi-lmi-linux-port`, branch `lmi-linux7`.
Handset: POCO F2 Pro / Xiaomi lmi, permanent `system5` boot, kernel
`7.2.12-lmi-community-port1-dirty`, Debian 13 (trixie) userspace, session
account `mobian`.

Companion to the Snapshot51 upgrade assessment of 2026-10-26, and continuation
of the preconditions record of the same date. The assessment established that
the Flatpak deployment of the Snapshot 51 candidate failed because the kernel
of that moment did not provide `STATX_MNT_ID`. This record measures the
facility on the kernel of the permanent boot, retries the deployment, and
follows the deployment to the next blocker.

## 1. The deployment blocker of the 4.19 kernel is gone

The `libglnx` path-chasing guard requires `TYPE`, `INO` and either `MNT_ID` or
`MNT_ID_UNIQUE`, and it emits `statx didn't return all required fields`
otherwise. On the 2026-10-26 attempt the masks were `0xfff`, `0x7ff` and
`0xfff`, without `MNT_ID`.

Measured on the running Linux 7.2.12 kernel of the permanent boot:

```
kernel: 7.2.12-lmi-community-port1-dirty
/                        mask=0x17ff ino=2 mnt_id=32 mnt_id_present=True
/proc                    mask=0x17ff ino=1 mnt_id=26 mnt_id_present=True
/home/mobian/.local      mask=0x17ff ino=242822 mnt_id=32 mnt_id_present=True
MNT_ID_AVAILABLE
```

The facility is really provided by this kernel. No security check is relaxed
and no mount identifier is invented.

## 2. The deployment now succeeds

The retry reused the objects of the failed attempt and completed:

```
Installing runtime/org.gnome.Platform/aarch64/51
Installing app/org.gnome.Snapshot/aarch64/stable
install exit: 0

org.gnome.Platform        51
org.gnome.Snapshot        51.0   stable
```

The application is installed for the session account. Nothing was installed
system wide.

## 3. The candidate reaches its own start, and stops on the next facility

The candidate starts and identifies itself:

```
Snapshot (org.gnome.Snapshot)
Version: 51.0
Datadir: /app/share/snapshot
```

and then stops with:

```
F: Can't get document portal: GDBus.Error:org.freedesktop.portal.Error.Failed:
   Can't mount path /run/user/1000/doc
```

The document portal of the session is the one that fails, and it says why:

```
xdg-document-portal: fuse: device not found, try 'modprobe fuse' first
xdg-document-portal: error: fuse init failed: Can't mount path /run/user/1000/doc
xdg-document-portal.service: Main process exited, code=exited, status=6/NOTCONFIGURED
```

The kernel carries `CONFIG_FUSE_FS=m`, with `CONFIG_FUSE_PASSTHROUGH=y` and
`CONFIG_FUSE_IO_URING=y` built in, but the module is not shipped: `/dev/fuse`
does not exist and no `fuse` module is present under `/lib/modules`. The
device node of the file system is therefore never created, the document
portal cannot mount its export directory, and the candidate of the application
cannot start.

This is the third kernel facility of this story, and it is the same kind of
blocker as the first two:

| Facility | Needed by | State on the 4.19 kernel | State on the 7.2.12 kernel |
|---|---|---|---|
| `STATX_MNT_ID` | the Flatpak deployment | missing | **present** |
| FUSE | the document portal, and through it the candidate | missing | **missing**, the module is not shipped |
| the rear sensor match | the camera of the application | not applicable | missing, the patch restores it |

## 4. The camera side of the upgrade stays compatible

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

The camera of Snapshot 51 is still a GStreamer `camerabin` pipeline, with
`glycin-2` added for the capture side. The session already carries the whole
camera stack of that path:

| Element | State on the handset |
|---|---|
| `libgstcamerabin.so` | present, from `gstreamer1.0-plugins-bad` 1.26.2-3 |
| `libgstpipewire.so` | present |
| `libgstvideo4linux2.so` | present |
| `libgstlibcamera.so` | present, but the PipeWire `libspa-0.2-libcamera` plugin is **not** installed |

The producer that this branch prepares publishes a PipeWire node with
`media.class` Video/Source and `media.role` Camera, which is what the session
device provider enumerates. The libcamera provider is present but has no
camera behind it, because the PipeWire libcamera plugin is absent, so the
libcamera route stays closed and the PipeWire route stays the one that
matters. **The producer contract does not change between the two versions of
the application.**

## 5. The launcher now knows both versions

`userspace/camera/snapshot-bundle/lmi-snapshot` chooses the application it
drives:

```python
def flatpak_candidate_usable():
    """True when the Flatpak candidate can be driven.

    The candidate needs the document portal of the session, and that portal
    needs the FUSE device of the kernel: without it the candidate stops at
    startup with "Can't get document portal". The native application stays
    the one to drive in that case.
    """
```

The candidate is preferred only when it is installed **and** when `/dev/fuse`
exists. On the current system the native application stays the one that is
driven, so the upgrade changes nothing for the user today; once the kernel
carries FUSE, the launcher drives the candidate.

The preloaded tuning library belongs to the native build and hooks the C
internals of Snapshot 48, while Snapshot 51 is a Rust rewrite, so the preload
is not applied to the candidate.

The desktop lookup was checked on the handset: the bundle entry still wins,
because it sits in `~/.local/share/applications`, which has priority over the
export directory of the Flatpak in `XDG_DATA_DIRS`:

```
resolved: /home/mobian/.local/share/applications/org.gnome.Snapshot.desktop
command : /usr/local/bin/lmi-snapshot
```

Without that shadowing, the entry of the candidate would open the
application without the launcher, and therefore without the camera producer.

## 6. The convergence

The camera of the Linux 7 line and the newer application of the camera need
**one kernel build**:

- the sensor patch and the camera configuration bind the rear sensor;
- `CONFIG_FUSE_FS=y` creates `/dev/fuse`, which lets the document portal
  mount, which lets the candidate of the application start.

Both are expressed in the same file,
`kernel/experimental/linux7/configs/camera.fragment`, and both are built by
the same recipe,
`kernel/experimental/linux7/tools/build-community-camera-kernel.sh`.

The block that the 2026-10-26 assessment asked about, a properly verified
kernel feature backport, is therefore not a separate piece of work on this
board: the facility is already carried by the community kernel for everything
but FUSE, and FUSE is a configuration line.

## 7. What is not claimed

- The candidate is installed but **does not run**: it stops at startup on the
  document portal. Nothing was changed to make it run, and nothing was
  weakened to make it run.
- The camera of the candidate is **not** qualified.
- The launcher was **not** switched to the candidate: it keeps the native
  application while `/dev/fuse` is missing, and the switch is prepared and
  covered by the guard tests.
- The bundle still pins `gnome-snapshot=48.0.1-1`; with the candidate
  installed next to it, the pin has to express the native application, the
  candidate, or both.
