# lmi front-camera Hall-only bring-up — 2026-10-26

## Result and scope

Eight successive poll-delivered AKM09970 samples were obtained on the running
Mobian Oct-7 kernel. Every sample had data-ready asserted and neither of the
ADC/XY error bits set; the decoded signed data words changed between samples.
This establishes a working Hall acquisition path in this trial, not a calibrated
position, a verified endpoint, motor operation or front-camera support.

No motor device or camera HAL was opened. No camera image, microphone or
mechanical movement was requested. No package, kernel or image was installed.

## Running-device and ABI evidence

The current decompressed kernel configuration SHA256 is
`c6da6e71cc7418f36997325ff5d72693d9861945cc4999b6be9661a150451e78`,
matching the retained Oct-7 configuration. Its correct symbols are
`CONFIG_HALL_AKM09970=y` and `CONFIG_MOTOR_DRV8846=y`.
Both device nodes exist and their corresponding platform/I2C drivers are bound.
An LP64 host compile check confirms the retained UAPI layouts: motor payload
40 bytes, Hall payload 11 bytes. This does not substitute for an ARM package
build or a motor ioctl trial.

## Bounded acquisition and cleanup

The isolated probe required USB online, the pinned configuration and no
existing Hall/motor device-file consumer. It checked the cached initial sensor
state was inactive, saved its baseline ioctl payload and activated only Hall.
It requested no mode change, collected at most eight events over four seconds,
and explicitly deactivated the sensor in a finally block. A transient systemd
service imposed a 12-second limit and an independent ExecStopPost deactivation.

The worker exited successfully; the transient service became inactive/dead with
Result=success. The kernel logged sensor-on/power-up, then sensor-off/power-down;
the final independent cleanup reported the same already-off state. These are
software observations, not an electrical measurement of the rail. The cached
initial payload alone is not a universal proof of prior hardware power state.

## Corrections to the external proposal

The vendor motor XML is present, but contains calibration thresholds rather
than the proposed PWM periods or motion durations. Static examination of the
retained vendor motor library found motion parameters in the library itself.
Those private inputs and disassembly are retained outside Git. They have not
been exercised as native motor commands.

The external prerequisite camera patch passed 91 replayed host checks. Those
checks cover extracted argument handling, policy gates, syntax and source
anchors; they do not exercise the complete HAL or make the front camera work.
The patch has not been integrated or installed.

## Remaining boundary

Motor close/release does not retract the assembly. Hall getters return cached
bytes; fresh polling and raw-status checks are necessary. Driver timer or poll
completion is not endpoint confirmation. Native use needs calibrated axis and
endpoint interpretation, exclusive ownership, bounded movement and failure
handling before a supervised mechanical test. A separate cleanup process cannot
guarantee retraction after a whole-system failure.

Snapshot still receives the selected rear-only source. Do not publish a dummy
front source just to expose a switch button. No complete-image pin changed.

## Factory calibration and vendor endpoint predicate — offline follow-up

The actual factory Hall calibration file was found at an already mounted,
read-only persist filesystem. It was read without mounting or remounting
anything; its contents and the vendor libraries remain private, outside Git.

Static inspection of the copied vendor code establishes that the three Hall
words are signed big-endian values converted to floating point without a
scale factor in the inspected endpoint path. The endpoint check uses
`atan2(Z, Y) * 10000`, compared with the corresponding calibration reference
angle plus the configured lower/upper offsets. The inspected bottom function
uses calibration entry 0; the top function uses entry 8. This is not simply
a threshold applied to a single axis, and no new angle wrapping was invented.

An offline helper replayed that predicate on the eight retained Hall samples:
all eight are inside the vendor bottom window and outside the top window.
Nine focused decoding, sign, angle-order and invalid-status checks also pass.
This supports the expected retracted initial state according to the inspected
vendor predicate. It is not independent mechanical observation or qualification
of the extended endpoint, a jam detector or a safe autonomous motor controller.
No new sensor activation or motor/camera operation ran for this follow-up.

The remaining mechanical gate is a bounded, supervised extension/retraction
trial with independent cleanup and fresh Hall feedback. Do not replace that
trial by a fabricated second PipeWire node or infer front-preview readiness
from endpoint mathematics alone.

## Supervised native extension/retraction — 2026-10-26

The operator confirmed being present with the assembly unobstructed. A bounded
native trial requested one extension and one retraction. The worker completed
both endpoint checks (fresh valid Hall feedback plus driver STOP) and recorded
`success=true`, `needs_retract=false`. The transient service completed in about
1.6 seconds, became inactive/dead and ran independent sensor deactivation.
The operator separately confirmed normal full extension and retraction without
abnormal noise or blockage. No camera HAL, image, microphone or recording was
opened. This qualifies one supervised mechanical cycle only.

The actual deployed controller SHA256 was
`e7003bfca06d053b35a181c2e57f2dbf8f3bd24d6168ef60b92062f1c55ecf99`.
Host tests before the trial passed eleven injected cycle/recovery cases and
five supervisor-contract cases. They are not eleven hardware trials.

### Retained evidence limitation

The independent cleanup instantiated a new event list and overwrote the
worker's detailed event journal. The completed state, cleanup receipt and
operator confirmation were preserved, but the raw movement trajectory and its
per-sample timestamps were not. Do not claim a retained detailed trace.
A local candidate now loads the previous journal before appending; its actual
constructor/log path passes a synthetic-file regression check. That correction
has not been installed or mechanically tested; no movement was repeated just
to obtain logs.

### Next integration boundary

The selected Snapshot source remains rear-only. Front HAL identification,
front images, foreground/lock motor lifecycle and in-app switching remain
unqualified. Mechanical success alone does not provide front-camera support.
Complete-image pins and installed packages are unchanged.

## Front HAL enumeration and first buffer — 2026-10-26

The operator built the isolated native diagnostic tools. Checksums and AArch64
ELF headers were verified before staging them separately from the rear runtime.
The OEM module initialized successfully and enumerated eight camera IDs. ID1
reports facing=front and orientation270; ID7 also reports front, but their
relationship is not established. ID1 was selected consistently with the Android
front-camera convention, then explicitly confirmed by its HAL information.

The enumerator exited0 and removed its private runtime. A supplementary loop
cleanup initially failed because losetup returned null fields for an already
unconfigured device. A passive sysfs check confirmed no backing file and no
private runtime directory. The helper was corrected and cleanup completed
without rerunning enumeration or detaching an unrelated device.

With explicit operator readiness and a neutral target requested, a bounded test
extended the mechanism, opened front ID1, obtained15 preview results and wrote
one 1280x720 RGB PPM. The HAL exited0 and the mechanism retracted. The worker
and independent cleanup succeeded; the operator confirmed normal full motion.
The raw motion record is preserved in this run (238 events,232 Hall rows,
one up and one down command), unlike the earlier motor-only logging defect.
No temporary firmware links or runtime directories remained; the owned loop
was already detached. No microphone, recording or installed runtime replacement.

The retrieved image is extremely dark and does not establish useful image
quality or orientation. The operator reported cleaning the dirty lens with a
finger possibly passing over it at acquisition time. This is a plausible
explanation, not a demonstrated cause. A clean-lens scene check remains needed.
Thus this milestone establishes front HAL buffer acquisition and lifecycle,
not an accepted front-camera application or a working Snapshot switch.
Images, factory calibration and vendor binary material remain private.

Capture binary SHA256:
`02184f8af4b17d964eb2423725c34b730f9862adf72b0bd888d889992e0c63c0`.
Enumerator SHA256:
`2708b53fbed5b31d199e19473f6d2bc0635d9511e785ad87447ea4b397c665dd`.
No full-image pin changed.
