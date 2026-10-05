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
comparison. The operator confirmed that this extracted soundtrack remained choppy when
played alone, with camera acquisition stopped. This does not isolate the cause
to Snapshot playback: capture defects or the retained audio itself remain possible.
No media, raw logs, core dump or device-specific runtime entered Git.

## Microphone-only control

With camera acquisition stopped, native `pw-record` captured 378,880 mono
S16_LE frames at 48 kHz (7.893 seconds). Peak was 631 and RMS 30.89. An isolated
playback copy was amplified by eight after checking that it would not clip.
The operator confirmed recognizable, fluent sound. The original capture and
source/sink gains were unchanged; the temporary listen copy alone was amplified.

This validates a microphone-only native PipeWire control, not simultaneous
video/audio recording. A separate microphone-only GStreamer `pulsesrc` control
was subsequently recorded at 44.1 kHz and finalized with 7.55 seconds of audio;
its operator listening assessment remains pending. No global rate, quantum,
latency, or gain setting was changed.

## Buffered audio and explicit camera clock control

The operator reported that the microphone-only GStreamer/PulseAudio control
at 44.1 kHz was choppy. A new control used 48 kHz mono, `latency-time=50000`
and `buffer-time=500000` on pulsesrc. Its final repeated capture contained
7.9 seconds; the operator confirmed correct sound from its amplified listen
copy. The rate and buffering were changed together: their individual causal
effects have not been isolated. No global PipeWire setting was changed.

A subsequent video test with these audio settings still crashed with SIGSEGV
despite `ORC_CODE=backup`. Therefore that ORC experiment is not an established
crash fix. Disabling the consumer pipewiresrc buffer pool and enabling
`always-copy` then yielded only one viewfinder frame, so recording was aborted
before start. In PipeWire 1.4.2 those two properties select the same no-pool
mode; they are not independent fixes.

Adding an explicit GstSystemClock to camerabin and `do-timestamp=true` on
pipewiresrc allowed 19 viewfinder frames before capture and successful
start/stop finalization: 168,116-byte WebM, duration 5.8 seconds, 48 kHz audio.
The decoded soundtrack contained 5.812 seconds, peak 964 and RMS 47.39 in
S16_LE units. The operator confirmed correct sound from an amplified isolated playback of
this video's soundtrack, with camera acquisition stopped. Full-video playback
in Snapshot with these settings remains unvalidated.
This proves one combined diagnostic configuration, not reliable Snapshot
integration or a single identified root cause.

The retained recording probe now reflects this combined test configuration.
Camera, publisher and recording units were stopped before isolated listening.
A permanent Snapshot audio/camera launcher has not been installed.

Upstream references: [PipeWire 1.4.2 source properties](https://github.com/PipeWire/pipewire/blob/1.4.2/src/gst/gstpipewiresrc.c)
and [GStreamer camerabin capture properties](https://gstreamer.freedesktop.org/documentation/camerabin/camerabin.html).

## Operator capture coordination

After this trial, the operator requested no autonomous ambient recording.
Every further microphone or video capture must wait for explicit readiness,
with capture and playback announced as separate steps. Technical preparation
and read-only diagnosis can proceed without starting acquisition.

## Snapshot process-local tuning preparation

The installed Snapshot schema exposes capture format and audio on/off, but
not microphone rate, pulsesrc latency, or pipeline clock selection. A small
experimental `lmi-snapshot-tuning.c` interposer applies the combined diagnostic
settings to newly constructed GstPulseSrc, GstPipeWireSrc and GstCameraBin
objects only when `LMI_SNAPSHOT_TUNING=1` is explicitly set. It is loaded through
LD_PRELOAD in a scoped test process; no system-wide preload or library
replacement is installed. This is a temporary adaptation, not an upstream
Snapshot patch or stable public plugin API. It relies on 64-bit GLib/GStreamer
runtime ABI and is currently restricted to the tested aarch64 environment.

The source was built with Clang targeting aarch64 Linux. The binary was placed
in the phone's temporary directory, outside Git. An inactive-object test
confirmed pulsesrc latency 50,000 us and buffer 500,000 us; pipewiresrc copying
mode and timestamping; mono 48 kHz camerabin audio caps; and GstSystemClock.
No pipeline was started during this verification. Actual Snapshot recording
and full-video playback with this interposer remain pending operator readiness.

## Application cleanup

At the operator's request, Megapixels 1.8.3-1 was removed from the test phone.
The package-manager simulation and actual removal affected only megapixels;
no dependency autoremove was performed. The lmi-camera prototype remains
provisionally available until Snapshot has replaced its validated functions.
The camera bridge/backend must be preserved independently of the prototype UI.

## First tuned Snapshot recording and video quality

The first Snapshot recording using the scoped tuning adaptation was initially
valid: 683,383 bytes, 13.810896 seconds, portrait 720 x 1280 at negotiated
10 fps, with mono 48 kHz audio. The operator confirmed correct sound during
video playback but reported missing frames and visible block artifacts in
paused video. A private screenshot showed pronounced compression blocks.
This is an audio success, not acceptable video-quality validation.

After the camera bridge was stopped while Snapshot remained open, the same
recording path unexpectedly became a zero-byte file. Causality is not fully
isolated; the session shutdown sequence is a suspected contributor. A later
quality probe therefore selected the older surviving recording, not the
13.81-second tuned trial: that older file had 43 encoded frames across
4.399 seconds and about 262 kbit/s of video. These numbers must not be used
as tuned-trial frame-loss measurements.

The next experimental publisher is prepared for 20 fps, closer to the measured
approximately 22.5 fps backend delivery. The scoped VP8 setting is prepared
for 4,000,000 bit/s, realtime deadline and two threads. Inactive-object checks
confirm those encoder values; no new capture was started for that check.
The next bounded test launcher closes Snapshot at 270 seconds, before the
300-second camera/publisher cutoff, as an experimental shutdown mitigation.
Its effect on recording preservation remains unvalidated. 30 fps capture,
acceptable quality at 20 fps and reliable saving remain open.
