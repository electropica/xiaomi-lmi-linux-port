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
