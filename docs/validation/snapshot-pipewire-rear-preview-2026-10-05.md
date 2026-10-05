# GNOME Snapshot through the rear PipeWire bridge — 2026-10-05

## Validated results

The operator confirmed a real rear viewfinder in Debian `gnome-snapshot
48.0.1-1` on the lmi Mobian/Phosh phone. A temporary userspace GStreamer
publisher exposes the previously validated HAL3 preview as `Video/Source` with
camera role. This demonstrates reuse of an existing camera application without
a kernel change. It does not establish full-resolution still capture or hardware
video encoding.

Transport was first tested with ten synthetic frames, then ten distinct real
1280 x 720 RGB frames. Received buffer size was 2,764,800 bytes and SHA-256 of
each received frame matched a published input frame. The initial consumer failed
with `target not found`; WirePlumber logs identified absent `media.type`.
Explicit Video/Capture/Camera properties corrected the link.

Five Snapshot-generated JPEGs were decoded successfully at 1280 x 720. The
initial gallery had no glycin loaders. Installing `glycin-loaders 1.2.1+ds-2`
removed that missing-loader condition, but a subsequent gallery D-Bus socket
error remains unresolved. Saved JPEG validity and in-app gallery usability are
separate results.

The first video file was empty and is not a successful recording. In a second
trial, the operator explicitly started and stopped recording. GstPbutils
Discoverer reports a valid WebM file of 266,391 bytes, duration 6.582002498 s,
720 x 1280 at 10/1 fps, with one-channel 44,100 Hz audio. The second publisher
rotates preview pixels clockwise to portrait before delivery. User assessment
of playback image and sound remains pending at this commit.

## Scope and lifetime

The producer is normal-user GStreamer `appsrc` feeding `pipewiresink` in provide
mode, using at most two queued buffers. Camera acquisition retains the isolated
OEM/HAL3 diagnostic runtime. The two camera acquisition trials were explicitly
bounded to 120 and 300 seconds with systemd memory/task limits and watchdog.
The first root runtime completed normal teardown after 2,618 published frames;
its temporary CVP firmware links were absent afterward. No permanent background
camera daemon or generic camera access policy was enabled.

`probe-pipewire-rear-stream.py` checks a currently active validated preview.
`publish-rear-pipewire-test.py` is a five-minute transport diagnostic reading that
fixed runtime input. Neither helper starts privileged capture itself. They are
not integrated into the userspace image recipe or a production Snapshot launcher.
A foreground-owned lifecycle for Snapshot still needs implementation and testing.
The older lmi prototype remains available.

Snapshot was launched with the Cairo GTK renderer. Kernel logs nevertheless
reported a Snapshot-associated GPU page fault during the second trial. Isolating
its remaining GL use and validating stable playback are follow-up work.

## Installation correction and discarded Flatpak route

The correct Debian package name is `gnome-snapshot`, not `snapshot`; its native
package and dependencies were installed from official Debian archives over USB.
Before correcting that name, a Flatpak installation attempt failed with
`statx didn't return all required fields` on this kernel. No Snapshot Flatpak
was installed. `flatpak repair --system` removed non-deployed runtime refs and
pruned the partial objects (installation directory reduced from 1.7 GiB to
3.6 MiB). The temporary SSH SOCKS tunnel was closed in a finally block. Wi-Fi
settings were not changed.

## Remaining work

- Foreground-owned Snapshot capture/publisher lifecycle and build integration.
- Gallery loader/socket error and remaining GPU use.
- Operator playback validation, recording reliability and performance.
- Full-resolution stills, focus/exposure controls, flash, zoom and front popup.

## References

- [Native Debian Snapshot package](https://packages.debian.org/trixie/gnome-snapshot)
- [GNOME Camera](https://apps.gnome.org/Snapshot/)
- [PipeWire GStreamer sink implementation](https://github.com/PipeWire/pipewire/blob/master/src/gst/gstpipewiresink.c)
- [GTK renderer and feature controls](https://docs.gtk.org/gtk4/running.html)
