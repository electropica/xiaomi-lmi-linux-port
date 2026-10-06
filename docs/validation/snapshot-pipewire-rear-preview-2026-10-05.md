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

## Higher-quality Snapshot trial failed

The operator authorized the next preview and manually initiated recording.
The 20 fps / 4 Mbit/s trial lost its live preview; the operator reported an
apparent freeze and horizontal mirroring. The phone remained reachable over
SSH, with about 5.9 GiB available memory. No matching OOM/GPU fault was found
in the inspected kernel window. Snapshot and acquisition were stopped; a
post-stop screenshot showed the responsive Phosh application grid.

The publisher logged 1,139 frames and root acquisition 1,144 frames during
the approximately 68-second source interval. This establishes continued
upstream delivery, not successful Snapshot reception or rendering. Snapshot
logged no explicit capture error in the inspected interval; the attempted
recording was zero bytes. This configuration is failed and must not be
described as functional higher-quality video. Preview freeze, mirroring,
recording finalization and safe shutdown remain unresolved. The last valid
operator recording established audio functionality only before its file was
subsequently truncated.

The operator can continue listening tests but is fatigued after the session.
Further capture still requires an explicit, clearly announced readiness
signal. Read-only diagnosis and offline preparation may continue; playback
and capture must never be conflated in operator instructions.


## Synthetic transport isolation and native producer

These tests used generated video and audio only. No camera acquisition,
microphone recording or speaker playback was started.

Direct GStreamer camerabin with videotestsrc and audiotestsrc completed a
20 fps recording. Routing a synthetic producer through GStreamer pipewiresink
with copied buffers instead reproduced a blocked stop-capture. A bounded GDB
inspection found the main thread waiting in a GstBaseSrc mutex during event
handling. Shared-buffer mode delivered 40 viewfinder frames over two seconds,
but stopping capture produced a gst_buffer_is_writable assertion and a
segmentation fault. These establish a transport failure without the OEM camera;
they do not identify the exact faulty source line or prove an upstream fix.

The experimental native producer `native-pipewire-synthetic.c` uses the public
PipeWire stream API with matched PipeWire/SPA 1.4.2 headers. It supplies BGRx
720 x 1280 at 20 fps, terminates after 30 seconds, and has no hardware-input
mode. With the copied-buffer camerabin consumer and generated mono 48 kHz
audio, the bounded run completed start, stop and teardown successfully:

- 40 viewfinder frames before recording;
- 6.1 seconds of WebM with one audio stream and 2,762,047 bytes;
- 122 decoded video frames, consistent with 20 fps over that duration;
- consumer and producer exit status zero; 221 total producer frames.

The existing scoped Snapshot tuning library was enabled for the consumer.
This is automated synthetic validation, not real-camera or Snapshot UI
validation. The native producer has not yet replaced the installed camera
bridge. Mirroring, real-camera quality, safe Snapshot shutdown and 30 fps
capture remain unresolved.

Source API reference: [PipeWire 1.4.2 video source example](https://github.com/PipeWire/pipewire/blob/1.4.2/src/examples/video-src.c).

The diagnostic launcher expects the binary, consumer and scoped tuning library
under `/tmp` on the phone, runs as the regular desktop user with its existing
PipeWire runtime, and stops its producer in a finally block. Its generated
WebM is temporary and must not be committed. Compile the C file using an ARM64
Linux compiler, PipeWire and SPA 1.4.2 include directories, and the matched
libpipewire-0.3 runtime library. The test source is not an installed application
or a production camera service.


## 25 fps synthetic target and PPM transport preparation

The agreed preview target is 25 real, regularly delivered frames per second
(40 ms intervals), not repeated display of an older image. The native
synthetic source was retested at 25 fps: recording and teardown completed,
with 152 decoded video frames over 6.08 seconds and 3,212,943 bytes.
Its committed default is now 25 fps; the earlier 20 fps result remains
historical validation of the previous revision.

A separate `native-pipewire-ppm-test.c` reads an explicitly supplied atomic
P6 1280 x 720 RGB file, rotates clockwise to portrait BGRx, and publishes
only newly observed inode/timestamp pairs. It neither starts acquisition nor
opens a microphone. Its source lifetime is bounded at 30 seconds.
Using generated PPM updates and generated audio, the consumer completed a
6.08-second recording (39,968 bytes) and clean teardown. The native source
reported 277 unique PPM frames over the full preview/record/teardown test;
this total must not be presented as a measured real-camera recording rate.

The real camera has not been tested with this native PPM producer yet.
An operator-confirmed, bounded preview-only test is prepared; camera
acquisition will not start before readiness. Real acquisition cadence,
Snapshot preview continuity, orientation, recording preservation and sound
synchronization still require validation. No production bridge was replaced.


## First real-camera native PPM preview

After explicit operator readiness, Snapshot displayed the native PPM source
for approximately 20 seconds, with no requested audio/video recording.
The operator reported fluid movement, but an inverted image and an offset
or delay; the meaning of the latter report still needs clarification.
The source journal shows streaming from 17:47:59 to 17:48:19 local time,
376 unique PPM publications, then clean source shutdown. This corresponds
to approximately 18.8 unique publications per second in that interval,
not the negotiated 25 fps. It is not a measured rendered-frame rate.

Root acquisition published 762 frames over its longer, separate lifetime;
that total must not be divided by the 20-second Snapshot interval. Snapshot,
the native source and root acquisition all stopped; root cleanup completed
successfully. The operator feedback establishes an improved preview, not
25 fps acquisition or corrected orientation. Real recording has not yet
been retested on this producer. Orientation and preview latency remain open.


## Rear-camera identity and synthetic latency preparation

The operator clarified the real-preview defects as left/right mirroring and
movement-to-preview delay. Inspection of the official Snapshot 48.0.1 source
found that `aperture/src/viewfinder.rs` treats any location other than Back as
front-facing for its preview transform. `camera.rs` reads
`api.libcamera.location`; `enums.rs` accepts `back`. The native node did not
supply this property. The prepared source now does. A PipeWire-only GStreamer
device-provider check confirmed both the node and the GstDevice expose `back`.
This supports the expected mirror correction, but operator confirmation in
Snapshot is still pending. No compensating mirror was applied to pixel data.

Official versioned source: [Snapshot 48.0.1](https://download.gnome.org/sources/snapshot/48/snapshot-48.0.1.tar.xz).

The prepared native PPM source polls for new files every 10 ms, rather than
40 ms, retaining unique inode/timestamp checks. It reports publication rate
and source-file age; neither metric includes sensor exposure or UI rendering.
A generated-file recording still completed normally (6.04 seconds, 39,866
bytes). A separate non-rendering PipeWire/GStreamer receiver test measured
175 unique samples, 25.04 frames/s, mean file-publication-to-sink delay 30.12 ms,
p95 33.51 ms and maximum 40.65 ms. The final property-verification run measured
174 unique samples, 25.05 frames/s, mean 25.85 ms, p95 30.81 ms and max 42.44 ms.
These are synthetic transport results, not real-camera latency validation.

An initial broad GstDeviceMonitor probe blocked while discovering providers;
it was terminated. The preserved latency diagnostic uses only
`pipewiredeviceprovider`, avoiding broad hardware discovery. All synthetic
processes finished or were stopped. No further real acquisition was started
while the operator was away.

`build-native-pipewire-test.sh` accepts the C source, matched include root,
matched ARM64 libpipewire library and output path. The compiled binary is a
private generated artifact. Sources compile with warnings as errors; the
launcher remains an experimental temporary test, not an installed replacement.


## Rear identity confirmed on the phone

After explicit readiness, the next real-camera Snapshot preview exposed
`api.libcamera.location=back`. The operator confirmed that left/right
mirroring was corrected, but could not verify movement-to-preview delay.
The native source measured 314 unique publications, 16.443 fps, mean source
file age 38.174 ms and maximum 90.692 ms. This rate is below the 25 fps target;
it must not be equated with the 25 fps synthetic result. Lighting and scene
were not controlled between the two real trials, so a cadence regression from
the polling change has not been established.

The root publisher counted 578 frames over its separate, longer lifetime.
Its configured runtime limit stopped the test and cleanup completed; a systemd
`timeout` result here denotes the intentional lifetime cap, not a proven
capture crash. All preview units stopped. A later idle CPU check showed
performance governors with hardware maximum frequency limits and modest
temperatures; it does not establish CPU scheduling or exposure during capture.

The PPM diagnostic now accepts an optional lifetime from 1 to 90 seconds
(default 30), so an operator can have a longer bounded preview to assess delay.
This changes only the temporary diagnostic lifetime, not an installed service.
No new capture was started while preparing it.


## One-minute preview: upstream rate and visible delay

The operator authorized a one-minute preview-only trial and subsequently
confirmed clearly visible movement-to-preview delay. During a 49.990-second
observation window, the root publisher advanced by 834 frames: 16.683 fps.
Observed update gaps averaged 59.94 ms, with p95 76.02 ms and max 114.77 ms.
These polling observations are publication intervals, not exact sensor timing.

Over its own streaming window the native source counted 1,009 publications,
16.895 fps, mean PPM age 37.950 ms and maximum 74.555 ms. Root acquisition
reported 1,037 frames across its longer lifetime. Thus low publication rate
already occurs upstream of the native PipeWire producer. The synthetic 25 fps
result does not establish 25 fps camera capture. Clocked preview, metadata
orientation and user-visible latency remain distinct validation dimensions.

During the trial all three CPU policies reported performance governors and
frequencies at their configured hardware maxima; sampled CPU thermal values
were approximately 39.5–46.5 degrees C. This snapshot does not exclude short
scheduling stalls, exposure limitations, conversion cost or downstream UI lag.
Snapshot, the native source and root acquisition stopped normally; root cleanup
completed successfully. No video or microphone recording was requested.

A temporary backend timing patch is prepared and cross-compiles with warnings
as errors. It adds aggregate means for result waiting, release-fence waiting,
and lock/conversion/save/unlock work, written every 15 published frames to a
small JSON inside the existing private capture directory. It does not change
camera settings, buffer count or installed services. The patch applies cleanly
to the current source. Runtime validation is still pending operator readiness.
The corresponding observer reads only live publication counters and never
starts acquisition. Generated binaries and private preview images stay outside
Git.


## Backend stage profiling completed

After explicit readiness, a 30-second preview-only timing trial completed.
The private runtime reported aggregate means over 555 processed images:
result wait 41.528 ms, release-fence wait 0.001 ms and lock/conversion/save/
unlock 13.864 ms. The native producer measured 519 unique publications,
17.542 fps, mean PPM age 36.021 ms and maximum 69.244 ms. Root publication
counted 556 images over its longer interval. All units stopped and private
runtime cleanup completed normally.

The approximately 55.4 ms sum is consistent with the observed rate, but the
result wait is not a pure sensor-exposure measurement: it includes waiting
for the HAL result after earlier processing. Conversion remains a significant
separate cost. No FPS, exposure or buffer-count setting was changed.

The prepared timing patch is extended to report the default preview AE FPS
range, whether a fixed 30/30 range is advertised, mean exposure/frame duration,
and sensor-to-RGB age only when timestampSource is REALTIME and a valid positive
CLOCK_BOOTTIME interval is observed. Unknown values remain explicitly unavailable.
Per-frame metadata is matched to the active slot under the existing mutex.
This extension compiles with warnings as errors but has not yet run on hardware.
The public NDK r27d metadata documentation establishes REALTIME timestamps use
elapsedRealtimeNanos; timestamps from an unknown timebase must not be subtracted
from the Linux monotonic clock. This remains a temporary measurement variant.


## Sensor timing identifies variable-rate exposure as a primary limitation

The operator authorized the extended 30-second preview measurement.
Across 510 measured images, default AE target range was 12–30 fps,
mean exposure 60.000 ms and reported frame duration 60.606 ms (about
16.5 fps). The source published 489 unique images at 16.533 fps.
The static metadata advertised fixed 30/30 fps support. Timestamp source
was REALTIME; 510 valid CLOCK_BOOTTIME comparisons gave mean sensor-to-RGB
age 115.107 ms. Result wait averaged 44.789 ms, conversion 14.359 ms and
fence wait 0.001 ms. Root publication counted 520 over its separate lifetime.
This establishes exposure/frame cadence as a primary limit in this scene;
it does not exclude conversion and downstream display latency.

All test units stopped and cleanup completed. No video/audio recording was
requested. A private fixed-rate trial is compiled: copy the default preview
metadata, require advertised 30/30 support, then set only the AE FPS range to
30/30. AE remains enabled; no manual gain or exposure is written. The patch
applies after the timing patch and checks cleanly against that intermediate
source. The prepared native publisher uses its previously tested 40 ms timer
for a 25 fps preview target with fresh-file checks. No installed service or
firmware is modified. Hardware success, brightness and latency remain pending.


## Supported fixed-FPS trial: reduced delay, cadence still below target

After explicit operator readiness, a 30-second preview-only trial selected
the advertised 30/30 AE FPS range while retaining automatic exposure. Across
705 measured images, exposure averaged 30.000 ms and sensor frame duration
33.333 ms. Mean sensor-to-RGB age fell from 115.107 to 86.495 ms; result wait
was 29.484 ms, conversion 14.124 ms and fence wait 0.001 ms. These are separate
trials, not a controlled simultaneous comparison.

The native producer published 574 unique images at 19.342 fps, with mean PPM
age 40.914 ms and maximum 77.457 ms. Root publication counted 711 over its
longer interval. A reported 30 fps sensor frame duration does not establish
30 fps delivery: the measured preview publication remains below the 25 fps
target. The operator confirmed noticeably reduced delay and adequate brightness.
The selected range is therefore a useful validated diagnostic change, not a
complete cadence or recording fix. No production service was replaced.

All three transient units stopped; root cleanup completed successfully. No
video or microphone recording was requested. Remaining work includes conversion
and delivery overhead, regular 25 fps preview delivery, foreground lifecycle
integration and reliable recording finalization.


## NEON conversion candidate prepared on the host - 2026-10-06

While a separately authorized battery trial ran, no camera or microphone
was opened. A temporary blocked-rotation candidate was checked against
the existing rotation on generated pixels: output matched exactly, but
it was slower on the x86 host, so it was not integrated or deployed.

A separate ARM64 NEON candidate targets the approximately 14 ms measured
YUV-to-RGB conversion stage. It preserves the existing integer BT.601
limited-range coefficients, rounding, clipping, plane strides, chroma-step
handling and file format. Eight-pixel rows use NEON; non-multiple-of-eight
widths retain the scalar fallback. The existing bridge's handle, span,
locking and output-file checks remain unchanged. Chroma samples are gathered
individually, avoiding an eight-byte load from a seven-byte minimal plane span.

Under QEMU ARM64, 200 deterministic random rows with chroma steps 1 and 2,
125 clipping/boundary color combinations and a minimal-plane case produced
byte-identical output to the scalar reference. The patched bridge compiles
with NDK r27d for Android ARM64, -O2 and warnings as errors; patch dry-run
applies to the current source. The generated object stays outside Git.
This is correctness/compilation evidence only: no phone speed, frame cadence,
brightness, recording or operator validation has been performed. The patch
and public test/header are diagnostic assets, not a production replacement.


## NEON hardware preview trial - 2026-10-06

After fresh operator readiness, Snapshot displayed a bounded 30-second rear
preview using the private NEON bridge and the same supported 30/30 AE range.
No video or microphone recording was requested. Across 960 measured images,
conversion averaged 9.256 ms, compared with 14.124 ms in the earlier scalar
trial (about 34% less). Mean sensor-to-RGB age was 81.025 ms, result wait
36.704 ms, fence wait 0.002 ms, exposure 30.000 ms and frame duration 33.333 ms.
These are separate trials; scene and scheduling variation prevent attributing
all timing differences to the converter.

The native producer published 556 unique images at 18.806 fps, with mean PPM
age 49.592 ms and maximum 79.903 ms. Root publication counted 965 over its
longer lifetime. Thus the faster converter did not improve measured publication
cadence over the earlier 19.342 fps scalar trial, and does not establish the
25 real images/s target. The operator reported low delay and a usable preview.

All bounded units stopped and root cleanup completed successfully. The installed
production bridge remains unchanged. This validates the candidate's visible
preview operation, not reliable video recording, foreground lifecycle integration
or a sustained 25 fps pipeline.


## Delay qualification and preview queue experiments - 2026-10-06

The operator qualified the usable NEON preview: visible delay remained roughly
0.2-0.5 seconds, with little obvious improvement. This is an operator estimate,
not a measured sensor-to-panel timestamp. The earlier sensor-to-RGB measurements
do not include Snapshot rendering or panel scanout.

Snapshot 48.0.1's upstream aperture/src/pipeline_tee.rs adds an ordinary queue
for its viewfinder branch. On the phone its defaults are 200 buffers, 10 MiB,
1 second and non-leaky. These are capacity limits, not evidence that the queue
was full or added one second of delay. A process-local candidate restricts only
GstQueue children of AperturePipelineTee to one buffer with downstream leakage;
recording queues are not targeted. A no-acquisition scope check confirmed the
ordinary GstBin queue stayed unchanged and the candidate was inactive without
its explicit environment flag. The diagnostic patch is not installed.

In a bounded real preview trial, the operator reported possible improvement but
could not confidently judge it. Publication was 18.201 fps (538 unique images),
mean PPM age 37.763 ms, mean sensor-to-RGB age 80.254 ms and conversion 9.003 ms.
This does not establish a cadence or end-to-end latency improvement.

A subsequent instrumented trial displayed a frozen loading indicator. The HAL
produced images, but the PipeWire source never entered streaming and published
zero images. Therefore no pipeline latency samples were collected. An initial
attribution to the GStreamer tracer was withdrawn: a later uninstrumented trial
also did not stream, and inspection found LockedHint=yes, ScreenSaver active
and backlight zero. Locking confounds the comparison; the tracer is not proven
to cause the startup failure. All hardware helpers were stopped cleanly.

After explicit unlocking, generated-color-only trials under a temporary idle
inhibitor streamed normally. Four compositor screenshots per variant bounded
the generated-file-to-compositor age by the start/end times of grim; captures
still took 67-165 ms even without PNG compression. With the ordinary queue,
the individual age ranges were 89-157, 45-160, 83-198 and 89-254 ms. With the
one-buffer queue they were 56-221, 114-230, 123-190 and 65-181 ms. These broad,
overlapping ranges and four samples do not demonstrate a gain. A separate
process-local attempt to disable preview sink synchronization also showed no
clear improvement (75-192, 71-186, 108-236 and 103-218 ms); it is not promoted.
Generated publication was about 22.2-22.5 fps in these tests. No camera or
microphone was opened by the generated-input tests, and no video was recorded.

The visible real delay remains unresolved. Future trials must keep the session
unlocked using a bounded idle inhibitor and distinguish camera acquisition,
publication, application rendering and panel scanout. No persistent camera,
recording or power policy was changed.

Source: https://download.gnome.org/sources/snapshot/48/snapshot-48.0.1.tar.xz
Queue semantics: https://gstreamer.freedesktop.org/documentation/coreelements/queue.html
