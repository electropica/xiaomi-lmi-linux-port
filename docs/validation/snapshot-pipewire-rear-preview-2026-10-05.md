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
rotates preview pixels clockwise to portrait before delivery. The operator subsequently confirmed correct video image but reported choppy
sound. That recording is not a successful audio playback validation.

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

## Temporal segment correction and follow-up

A later Snapshot trial created an empty file and reported PipeWire buffer
allocation failure. A controlled automatic camerabin trial also stalled at
stop-capture. Audio-only PulseAudio/PipeWire capture succeeded, and the same
camerabin setup recorded a 6.1-second synthetic video with audio, isolating the
problem to the real bridge path rather than proving microphone failure.

The appsrc publisher was incorrectly using its default byte-format segment even
though it supplies timestamped live video. GStreamer logged
`gst_segment_to_stream_time: assertion segment->format == format failed`.
Explicit `format=time` corrected this defect. The retained publisher uses
portrait BGRx output and buffer copying (`use-bufferpool=false`). The automated
camerabin diagnostic fixes portrait 720 x 1280 / 10 fps caps, waits for at least
five viewfinder frames before starting, and uses a non-synchronizing fake
viewfinder sink to avoid testing display timing as a recording precondition.

After the correction, 19 viewfinder frames arrived before recording. The
six-second start/stop trial completed and produced a valid 123,001-byte WebM
with 5.68-second duration and one audio track. Audio-only decoding produced
91,092 samples at 16 kHz, peak 0.01129 and RMS 0.000449, with no decoded timestamp
gaps exceeding 10 ms. This numerical result does not prove audible continuity
or adequate level in all conditions. The operator reported choppy sound again in the follow-up. The only retained
Snapshot file from that trial was empty (0 bytes), so that report cannot yet be
attributed to a decoded recording. The bounded camera source stopped at its
five-minute deadline; Snapshot then reported target-not-found and not-negotiated.
Recording completion and audible playback remain unvalidated.

The scoped Snapshot launch disables GL/Vulkan/dmabuf through `GDK_DISABLE` in
addition to Cairo rendering to investigate previously observed GPU faults.
No global GPU configuration or kernel setting was changed. All automatic
acquisition/publisher trials stop their units in a finally block and retain
hard systemd timeout limits. Neither a permanent foreground-owned Snapshot
launcher nor image integration is implemented yet.

## Intermittent recording crash and isolated audio trial

A repeated real-source camerabin recording crashed with SIGSEGV. GDB reproduced
the failure in the `queue1:src` streaming thread during the capture/stop interval;
the program counter was unresolved and the stack could not be unwound reliably.
This does not identify a specific defective library or prove a kernel cause.

A scoped `ORC_CODE=backup` experiment then completed one automated recording:
103,600 bytes, 5.72 seconds, one audio track. Decoding produced 91,835 samples
at 16 kHz, peak 0.05377, RMS 0.001500, and no timestamp gaps over 10 ms.
This single success is insufficient to establish a reliable crash workaround.
The diagnostic `probe-camerabin-rear-recording.py` retains the bounded six-second
start/stop test; it requires the experimental source to be running already.

Snapshot was subsequently launched with the same process-local ORC setting.
The retained operator recording was 179,320 bytes with duration 4.499 seconds
and Vorbis audio. The operator still reported choppy playback in Snapshot.
Audio decoding produced 66,340 samples at 16 kHz, peak 0.01866, RMS 0.001243,
and no timestamp gaps over 10 ms. Continuous timestamps do not establish
continuous captured sound or successful audible playback.

The bounded Snapshot, source and root acquisition units were stopped before
extracting that recording's audio to a temporary WAV for an isolated playback
comparison. Operator assessment of this isolated comparison remains pending.
No media, raw logs, core dump or device-specific runtime entered Git.
