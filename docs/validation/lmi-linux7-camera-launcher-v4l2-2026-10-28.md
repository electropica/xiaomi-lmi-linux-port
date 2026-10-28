# Camera launcher in V4L2 mode on the Linux 7 line — October 28, 2026

Date: 2026-10-28
Canonical repository: `/home/linuxagent/xiaomi-lmi-linux-port`, branch `lmi-linux7`.
Handset: POCO F2 Pro / Xiaomi lmi, permanent `system5` boot, kernel
`7.2.12-lmi-community-port1-dirty`, Debian 13 (trixie) userspace, Phosh session
as `mobian`.

Continuation of the engine-gate record of 2026-10-27 and of the sensor binding
record of 2026-10-28. Those two records made the camera application honest
about the missing engine and identified why the rear sensor never binds. This
record covers the last piece of the userspace path: the launcher now has a
second camera source, and the producer that feeds it.

## 1. What the launcher had to decide

The launcher owns the camera for the whole life of the application. It
publishes the foreground lease, it starts and stops the producer, and it keeps
the privileged preview service in step with the focus of the window. Until
now it had exactly one source: the OEM producer, which reads the PPM file
that the privileged preview service writes.

On the Linux 7 line there is no such service, because there is no OEM HAL. The
source of truth is the V4L2 node of the CAMSS VFE, and the producer that
publishes it has to answer one question before the application can show
anything: **is there really a camera behind that node?**

A PipeWire node exists as soon as a producer connects, even when no frame
ever arrives. Opening the camera application on a node that never frames
would give the user a black viewfinder, which is the failure this work is
meant to remove. The launcher therefore waits for the producer to report a
real frame.

## 2. The contract

The producer prints one line on its standard output when a frame arrived:

```
V4L2_SOURCE_READY <device> <width>x<height>
```

and exits with status 3 when no candidate node delivered a frame. The
launcher reads that line, and only then opens the camera application. The
producer is a real contract, not a convention: the launcher starts it, reads
its first line, and treats anything else as the absence of a camera.

The producer also follows the foreground lease of the launcher: it streams
only while the lease says the camera application is in the foreground, and it
exits when the lease disappears with the launcher. The camera is therefore
powered only while the user is looking at it, and the PipeWire node stays
alive, so the application keeps its camera when the window loses and regains
the focus.

## 3. The launcher

`userspace/camera/snapshot-bundle/lmi-snapshot` now chooses its source with a
pure function, which is covered by the guard tests:

```python
def select_source(reason,producer_present,nodes):
    """Choose the camera source. Pure decision: no process, no device access."""
    if reason=='none':return 'oem','none'
    if not producer_present:return 'none','missing_producer'
    if not nodes:return 'none','no_video'
    return 'v4l2','none'
```

The OEM path is untouched: same producer, same privileged service, same
signals, same order. The V4L2 path starts the producer first, and only starts
the focus monitor and the application when the producer reported a frame. On
the OEM engine being unavailable and no producer installed, the notice of the
2026-10-27 record is shown exactly as it was.

Two behaviours were corrected while the mode was written:

- **No child left behind by the notice.** The focus monitor used to be
  started before the source was known, so a launcher that ended in the notice
  kept a child process alive for as long as the notice was open. In the V4L2
  mode the focus monitor is started after the producer is ready.
- **The notice closes on a terminal signal.** The launcher installs its own
  `SIGTERM` handling before it reaches the notice, and that handler only arms
  a flag the notice loop never reads, so the notice survived `SIGTERM`. GLib
  now handles the signal inside the main loop, and the notice really closes.

A second start, while an instance already holds the lock, now raises the
window of that instance: it tries the camera application first and the notice
application second, instead of failing with a bus error.

## 4. The producer

`userspace/camera/diagnostics/native-pipewire-v4l2-source.c` opens a V4L2
capture node, publishes the frames as a PipeWire camera node with the media
properties the session provider expects, and follows the lease.

It looks for the node that carries the camera by itself: it probes the video
nodes of the handset and keeps the first one that delivers a frame. On the
handset the probe visits the fourteen `msm_vfe*` outputs and finds nothing in
under a second, because the stream-on of a VFE without input fails at once.

The producer reads the video node with the public V4L2 ioctls and the public
PipeWire stream API, never opens a microphone and never records.

## 5. Validation

### Host

The producer compiles with the strict flags of the bundle build
(`-O2 -Wall -Wextra -Werror`) and, for the handset, against the PipeWire
version of the handset itself: the aarch64 cross build uses the 1.4.2 headers
and library of the target rootfs, so the binary is linked against exactly the
library it will run with. Its only dependencies are `libpipewire-0.3.so.0` and
`libc.so.6`.

The guard tests of the launcher cover the new decision function. The launcher
functions are extracted verbatim with `ast` and driven through every case:

```
22/22 cases pass
```

The cases cover the OEM path staying the OEM path, the V4L2 path being taken
when the OEM engine is missing and the producer is installed, the refusal
when the producer is missing or when there is no video node at all, and the
notice naming the outcome and keeping the fallback hint.

### Handset

Deployed on the running system: the launcher at `/usr/local/bin/lmi-snapshot`
and the producer at `/usr/local/lib/lmi-camera/native-pipewire-v4l2-source`,
with the previous launcher kept in `/root/lmi-camera-backup-20261027/`.

Measured on the handset, with the current system that has no bound sensor:

| Observation | Result |
|---|---|
| Producer alone | probes the fourteen video nodes in under a second, `V4L2_NO_FRAME` for each, `V4L2_NO_FRAME_ALL`, exit status **3** |
| Launcher | takes the V4L2 path, waits for the producer, reads `LMI_CAMERA_V4L2_NO_FRAME`, shows the notice naming the outcome |
| Notice | stays open with its GTK 4 window mapped, no `AssertionError` |
| Children | none: no producer, no focus monitor, no privileged service |
| Privileged service | `lmi-camera-preview.service` stays `inactive` |
| Second start | raises the notice of the running instance, exit status 0, no bus error |
| `SIGTERM` | the notice closes, the launcher exits, the foreground lease is removed |

The honest outcome on this system is still "no camera", and that is what the
application says. What changed is that the application now *tries* the source
that will work once the kernel carries the patch, and it tells the difference
between "there is no camera" and "the camera is there".

## 6. What is not qualified

- No frame has been published, because the sensor does not bind on the
  current kernel. The success path of the V4L2 mode is therefore **not**
  qualified on the handset; only its failure path is.
- The producer is not yet built by the bundle of the operator: the bundle
  build of the repository produces it, but the bundle installed on the
  handset predates this change. The binary used for the measurement above was
  cross built against the handset PipeWire version.
- The camera switch of the front camera remains out of reach: the pop-up
  mechanism of this board needs its own work, as the front-camera record of
  2026-10-26 states.

## 7. The remaining path to a picture

1. build and install a kernel that carries
   `patches/0004-lmi-ov13b10-of-match.patch` and the camera configuration;
2. rebuild the bundle so that the producer is installed with the launcher;
3. start the camera application: the producer finds the node that frames, the
   application opens with a viewfinder;
4. qualify the capture itself, which is the next record.
