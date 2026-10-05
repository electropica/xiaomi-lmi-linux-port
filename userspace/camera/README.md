# Camera userspace status

Current diagnostic-boot result: automatic rear 720p capture works through the
[opt-in snapshot app](#opt-in-rear-snapshot-application--2026-10-05).
Operator button/open validation is pending. Megapixels remains incompatible.
The following dated sections preserve the earlier blockers and their resolution.

Megapixels is installed, but its required `qcom,kona-mtp.ini` is absent
and its native media API is incompatible with this downstream stack. The
rear IMX686 is now confirmed through the isolated OEM backend below. No
speculative Megapixels configuration is included. See the
[`camera blocker validation`](../../docs/validation/archi-validation-02-camera-blocker-2026-09-27.md).

## Current functional recheck — 2026-10-04

A bounded launch still exits immediately with status 1 and the missing
`qcom,kona-mtp.ini` message. The existing source's request-manager private
ioctl and sensor core-only operation tables support the previously recorded
downstream-interface mismatch. No speculative INI, replacement application,
capture attempt or kernel build was added. The functional blocker remains
open; see the [current checklist](../../docs/validation/lmi-app-checklist-2026-10-03.md#functional-priority-and-camera-recheck--2026-10-04).

## OEM backend feasibility — 2026-10-04

The read-only [backend inspection](scripts/inspect-capture-backend.py) was
executed on the current diagnostic boot. It reads fixed-path runtime presence,
sysfs video names and the ELF interpreter/direct dependencies of two camera
objects. It never loads a library, executes a vendor binary, opens a video
device, changes a mount or starts Android. Its JSON is an inventory, not a
successful linkage or capture test; even a complete inventory does not prove
ABI compatibility or sensor operation.

The phone contains `camera.qcom.so`, the 64-bit Android camera provider 2.4,
and a resolvable Android linker backed by the mounted runtime APEX. The
provider depends on Binder/HIDL and graphics-mapper interfaces. The camera
module depends on CamX, DSP and Android libraries. These are Android objects;
their presence alone does not make them loadable by a native Mobian app.

The running kernel enables Binder IPC, BinderFS, the three Binder device names
and ashmem. Ashmem exists, but neither the conventional Binder nodes nor the
checked BinderFS nodes exist. Android properties and their service socket
are absent. `hwservicemanager` is a dangling symlink to
`/system/system_ext/bin/hwservicemanager`. The process named `camera` has PPID 2
and is a kernel thread, not a running Android camera provider. These facts do
not rule out an Android adaptation; they establish that it is not ready here.

The upstream [libhybris description](https://github.com/libhybris/libhybris)
explains that Android drivers need an adapted Android service environment and
wrappers for native Linux applications. A downstream route therefore needs a
coherent, isolated Android runtime, working Binder/properties/service managers,
then an explicitly compatible camera bridge. Starting the vendor provider
alone or mounting BinderFS alone would not complete that integration.

Separately, the existing alternate lmi source at commit
`3a8409fb1020b5952310072713ce97edea5e65d7` already declares CAMSS, CCI0 and
an OV13B10 endpoint, with `CONFIG_VIDEO_QCOM_CAMSS=y` and
`CONFIG_VIDEO_OV13B10=y` in its M1 config. These declarations were checked
from the committed objects, apart from its local changes. See the
[immutable DTS](https://github.com/ccc007ccc/linux-sm8250-xiaomi-lmi/blob/3a8409fb1020b5952310072713ce97edea5e65d7/arch/arm64/boot/dts/qcom/sm8250-xiaomi-lmi.dts)
and [configuration](https://github.com/ccc007ccc/linux-sm8250-xiaomi-lmi/blob/3a8409fb1020b5952310072713ce97edea5e65d7/lmi/configs/m1.config).
This is a separate kernel route, not a description of the running 4.19
diagnostic kernel and not a validated camera. No swap/build is proposed as an
application-level quick fix.

Next acceptance gates, in order: a working backend enumerates actual sensors;
one bounded still capture produces a readable image; Megapixels or its
integration displays a preview and saves/reopens that image; only then test
controls and additional capabilities. The current work completes inspection,
not these capture gates. No vendor binaries, output inventory, partition data
or private device information are included in Git.

## Isolated HIDL registration milestone — 2026-10-04

The Android linker's documented `--list` mode resolved the provider and camera
module dependency trees with exit status 0 in the observed runs; a missing
generated linker-configuration warning remains. This maps dependency objects,
not a successful HAL initialization or capture. The
[AOSP linker implementation](https://android.googlesource.com/platform/bionic/+/94657009839a4918337ac069652085906e3ee322/linker/linker_main.cpp)
documents this list mode separately from target execution.

The apparent missing HIDL manager was located in the existing `system_ext`
logical partition. A [read-only metadata reader](diagnostics/inspect-system-ext-metadata.py)
checked geometry, header and table checksums before its single linear extent
was inspected. The manager is 99,832 bytes and uses the Android bootstrap
linker. System and vendor both report Android SDK 36. A private mount used a
read-only loop and `ro,noload,nosuid,nodev,noexec`; it was then removed. No
partition was copied, repaired or written.

An isolated runtime then mounted system/vendor/runtime/system_ext read-only
and created private BinderFS devices. Mount and network namespaces were
separate; its device tree exposed null, urandom, ashmem and private Binder,
but no video/media/subdevice/block/DRM devices. All three Binder protocol
queries returned version 8. The unchanged HIDL manager aborted with
`Failed to acquire hwservicemanager context.` The running kernel has
`CONFIG_SECURITY_SELINUX` disabled. AOSP's
[AccessControl implementation](https://android.googlesource.com/platform/system/hwservicemanager/+/e609036145cd4457439e4798878f6ff5bf9c756f/AccessControl.cpp)
places this error at the failed `getcon` call; this supports the failure
interpretation, without asserting an exact source match for the OEM binary.

The [private context test source](diagnostics/private-context-test.c) supplies
one synthetic process context solely to this diagnostic runtime. It is not
installed by any recipe, not a production policy, and must not be preloaded
into the host session. With it, the manager stayed active for the six-second
test and a second context-manager registration attempt returned `EBUSY`,
showing the private HIDL manager already owned that Binder context. No camera
provider was started. This is registration evidence, not full IPC validation.

The final test used a real 256 MiB cgroup memory cap, zero swap, at most 64
tasks and a 25-second outer runtime limit. An earlier 384 MiB address-space
limit was unsuitable for Scudo's large virtual reservation and is not
recommended. Missing Android property service warnings remain. CPU time was
6.222 seconds over a 6.280-second test: unexpectedly high, requiring diagnosis
before enabling camera hardware. The process group was stopped; mounts,
temporary root and loop mapping were removed. No HIDL process remained.

Next gates: explain the busy runtime and implement coherent properties;
verify real client/server IPC in the isolated environment; only then permit
the camera provider and bounded sensor enumeration. A native-app capture
bridge is still required. Do not interpret a synthetic-context startup as a
security or production-runtime solution. Test binaries, partition metadata
output and phone-private wrappers stay outside Git.

## Readiness spin resolved; client IPC blocked — 2026-10-04

This follow-up supersedes the unexplained high-CPU observation above, but
does not validate a camera backend. Bounded tracing found no syscalls during
the spin; a one-second, 49 Hz target-only profile placed the dominant samples
in `WaitForProperty` through `steady_clock::now`. The runtime has no Android
shared property area. A diagnostic-local `hwservicemanager.ready` token,
updated by the manager's own property-set call, made the manager wait in
`do_epoll_wait`. Comparable ten-second unit runs consumed 10.587 seconds of
CPU before and 429 milliseconds after the token. These are whole-unit totals,
not isolated manager utilization. Other Android properties are not emulated.

The client receives this local readiness token only after the supervisor
observes `EBUSY` from a second private Binder context registration attempt.
`lshal list --types=binderized --neat --interface` then reaches the manager,
but returns status 8. With the original security-context request enabled,
Binder reports `EOPNOTSUPP` (-95): the running kernel cannot produce the
requested transaction security context without SELinux. The matching local
Binder source places this failure at `security_secid_to_secctx`.

One private test cleared only `FLAT_BINDER_FLAG_TXN_SECURITY_CTX` for the
context-manager registration. The transaction progressed further, but the
manager aborted and the client received `DEAD_OBJECT`. An observing hook
printed the original abort reason while preserving the abort:

```
Check failed: nullptr == self->getServingStackPointer()
Pid [diagnostic client] missing service context.
```

The [Android 16 ServiceManager source](https://android.googlesource.com/platform/system/hwservicemanager/+/refs/heads/android16-release/ServiceManager.cpp)
contains this check when an incoming transaction has no caller SID. This
matches the observed failure; it is not a claim of an exact OEM source match.
Removing the kernel request alone therefore does not provide compatible IPC.
No assertion was disabled and no production access-control policy was changed.

The expanded [diagnostic source](diagnostics/private-context-test.c) is gated
by `LMI_PRIVATE_CONTEXT_ACTIVE=1`; the client-readiness flag must be supplied
only after the private context registration check. It observes aborts and
contains the failed security-context experiment, not a deployable fix. Its
variadic ioctl forwarding is limited to the tested pointer-argument callers.
Never preload it into the host session or an unrestricted camera provider.
The supervised test retained the 256 MiB / zero-swap / 64-task / 25-second
limits and excluded physical camera devices. Both processes stopped and all
private mounts, mappings and temporary roots were removed.

Next prerequisite is a coherent Android runtime bridge with an explicit
caller-identity/access-control design compatible with this kernel, or a
separately validated native capture backend. A readiness token and synthetic
manager label do not satisfy that requirement. Full properties, provider
initialization, sensor enumeration, preview and still capture remain unvalidated.
No camera provider was started in these experiments.

## OEM module and sensor-probe progress — 2026-10-04

This follow-up advances beyond the IPC failure above; photo capture still
does not work. A supervisor-selected client PID, recorded before its stopped
process was continued, received a synthetic diagnostic caller label. Unknown
peers retained the original behavior. The original `selinux_check_access`
function returned 0 for the observed list/find checks; the diagnostic only
logged its result. The empty-service `lshal` query then returned 0 and the
manager remained idle. Self-registration required the same synthetic label
for the manager's own `getpidcon` call, never for arbitrary PIDs.

Registered non-context-manager Binder objects also requested unsupported
security contexts. A private diagnostic gate now copies bounded outbound
Binder command/transaction buffers and clears only that request on local
Binder objects. The read buffer and consumed counters are preserved. This
removed `FAILED_TRANSACTION` from the observed manager/token interface
queries. `lshal` still returned 72 with a debug PID metadata warning, so this
is working interface-query evidence, not a clean complete lshal validation.
These synthetic identities and context adaptations are not a production
security model. No global kernel or Android security policy was changed.

The OEM provider initially exited 1 because the Android hardware-selection
properties were unavailable. The real boot parameter says
`androidboot.hardware=qcom`; vendor build properties say `ro.board.platform`
and `ro.product.board` are `kona`. Passing these checked values selected and
loaded the existing external `camera.qcom.so` and CamX implementation.
Symphony's platform check still exited 1 because it explicitly obtains the
property getter from a libc handle, bypassing ordinary preload lookup.
The diagnostic bridges only that explicit property-getter lookup to the
same checked values; it does not override the platform acceptance result.
With it, the Snapdragon refusal disappeared. The
[Bionic dlsym/dlvsym implementation](https://android.googlesource.com/platform/bionic/+/a026108ec10c0b711add1e5fb920710ced4a9046/libdl/libdl.cpp)
supports the nonrecursive real-symbol lookup used by this private hook.

The first hardware-exposing variant allowed ION, camera media/subdevices,
`cam-req-mgr` and `cam_sync`, while excluding block devices, input, DRM,
codec video nodes and host Binder. System/vendor/runtime remained read-only;
networking was isolated and temporary data belonged to the private root.
CamX reached real EEPROM probing. Successful candidate probes included
`lmi_sunny_imx686_mp_gt24p64b`, `lmi_sunny_s5k3t2_gt24p64`,
`lmi_ofilm_gc02m1`, `lmi_sunny_ov13b10_gt24p64` and
`lmi_sunny_s5k5e9yx04_gt24p64`. Alternative candidates also failed.
Candidate EEPROM results do not establish a count of physical cameras,
preview capability, camera IDs, or successful image capture.

The `cam-icp` open failure was traced to missing `CAMERA_ICP.elf` at the
kernel firmware lookup path. The external vendor file is 3,888,984 bytes,
SHA-256 `e9fcbd80f63e8a0475b2621e4adef89dfed37cfa2ecf6636837b2154776441c7`.
The local source's `a5_core.c` calls `request_firmware` with that exact name.
A host firmware reference alone did not fix the chrooted call. Binding the
file read-only at the private runtime's `/lib/firmware/postmarketos/` path
did: the kernel reported `FW download done successfully` and CamX's ICP
open error disappeared. The [reference preparation helper](scripts/lmi-camera-firmware-prepare)
was syntax-checked and ran successfully on the phone's existing link.
It refuses replacement of regular files or different references, requires
the expected loader path/read-only external source, and never copies the
firmware into Git. A private runtime must separately expose that lookup path.
This helper is not automatically enabled by any image recipe yet.

The [direct-module enumeration source](diagnostics/camera-module-enumerate.c)
was compiled as a small bionic client with ABI layout assertions. It
recognized `HWMT/camera`, module API 2.5 and HAL API 1.0, and module `init()`
returned 0. Before the NCS override, `get_number_of_cameras()` did not finish within the 35-second
observed bound. A two-second thread snapshot placed the calling thread in
`cam_cci_core_cfg`; this alone does not prove the final timeout cause.
The direct client performs no stream setup or capture. HAL3 buffer allocation, a still capture and native application
integration remain the next acceptance gates.

A later 25-second user-space backtrace identified the final wait in
`CamX::SSCConnection`, reached through `SuidLookup`, `NCSIntfQSEE`,
`NCSService::Initialize`, `ChiOpenContext` and the CHI override constructor.
The vendor override file enabled `enableNCSService=TRUE`. Qualcomm documents
`enableNCSService=FALSE` for systems without an IMU in the
[QIM SDK Reference, section 5.1](https://docs.qualcomm.com/doc/80-50450-50/80-50450-50_REV_AC_Qualcomm_Intelligent_Multimedia_SDK__QIM_SDK__Reference.pdf).
A read-only private bind of the existing settings with only this key changed,
together with vendor tags and callbacks registered in the
[AOSP provider order](https://android.googlesource.com/platform/hardware/interfaces/+/5fa14c4bce/camera/provider/2.4/default/LegacyCameraProviderImpl_2_4.cpp),
returned `set_callbacks_result=0`, `camera_count=8` and IDs 0 through 7.
These include OEM logical/auxiliary IDs; they do not establish eight physical
camera sensors. No host vendor settings were modified.
The first probe aborted during normal process shutdown with Scudo's invalid
chunk-state error. Its revised diagnostic uses `_Exit` to avoid vendor exit
handlers; this is a diagnostic lifecycle restriction, not a production fix.

The hardware-probe units used 384 MiB memory, zero swap and 64 tasks, with
bounded supervisor deadlines; all completed runtimes were stopped/unmounted
and their loop mappings detached. Missing generated linker configuration,
an optional component's `libandroidicu.so` dependency and display-config
service warnings remain. No preview, JPEG, public camera service, new
kernel or userdata image was produced; Megapixels is still nonfunctional.

A follow-up enumerator queried all eight IDs successfully. Each returned
HAL device version 3.5 and non-null static metadata; rear-facing IDs used
orientation 90 and front-facing IDs 1 and 7 used orientation 270. The
revised `_Exit` probe avoided the observed vendor shutdown abort. These
characteristics remain enumeration evidence, not image-capture validation.
The only gralloc module present, `gralloc.default.so`, advertised the
legacy gralloc0 ABI. Opening `gpu0` and closing the allocator returned 0;
no buffer allocation was attempted in that inspection.

The bounded [private enumeration supervisor](diagnostics/camera-test-module-no-ncs.py)
and [late-backtrace variant](diagnostics/camera-test-module-backtrace.py)
are source-only diagnostics requiring the existing phone partitions,
metadata inspector and manually compiled temporary binaries. Run only
under the documented private namespaces and resource-limited test unit;
these are not unattended services or image build entry points.

The primary rear camera (ID 0) subsequently opened, initialized with stable
HAL3 callbacks and returned non-null `STILL_CAPTURE` defaults. Its close
returned 0 after initialization; closing before initialization had returned
-22. The [HAL3 preparation probe](diagnostics/camera-module-prepare.c) submits
no stream or capture request. The private mount settings and process-lifetime
limitations above still apply. Temporary supervisor paths refer to the
metadata inspector installed as `/tmp/lmi-camera-super-metadata.py`, from
[the source-only super metadata inspector](diagnostics/inspect-system-ext-metadata.py).

The rear ID 0 metadata advertised 23 BLOB output sizes and JPEG maximum
size 32,572,808 bytes. A single 320 x 240 JFIF BLOB stream configured
successfully, returning usage 0x20003 and max_buffers 8; close returned 0.
No buffer or capture request was submitted. The preparation probe's
`--configure` flag reproduces this bounded stream-only check.

The [legacy allocation probe](diagnostics/camera-gralloc-allocate.c) then
returned -2 for a 16 MiB BLOB allocation. A syscall trace showed no ION
open or ioctl. Static inspection established that `gralloc.default.so` is
an AOSP legacy ashmem allocator, not the Qualcomm DMA-buffer allocator:
its BLOB allocation calls `ashmem_create_region` and propagates -errno.
Fixing that path alone would not establish a compatible camera handle.
Existing external Qualcomm gralloccore/QTI and mapper 3/4 implementations
are the next allocation candidates. A production capture must size the
buffer from the JPEG maximum metadata and honor the HAL-returned usage;
the 16 MiB failed allocator test is not a valid capture-buffer recipe.
Megapixels still has no working preview or photo capture.

A subsequent [direct Qualcomm allocation diagnostic](diagnostics/camera-qti-allocate.cpp)
used the public `BufferDescriptor` layout, verified against the installed
`libgralloccore.so`: Android libc++ string prefix 24 bytes; descriptor 64
bytes with dimension, format, layer, usage, ID and reserved-size offsets
asserted. The small client linked against the existing system `libc++.so`.
`BufferManager::GetInstance` succeeded; allocation of a 32,572,808 x 1 BLOB
with usage 0x20003 returned 0 and a real vendor handle. Releasing that
handle also returned 0. No image data was read and no camera request was
submitted by this allocation-only test. The installed libraries remain
external inputs; neither their binaries nor any photo belongs in Git.
This verifies an allocation route, not yet full CamX buffer compatibility.

## First rear JPEG diagnostic — 2026-10-04

The [single-frame capture probe](diagnostics/camera-module-capture.c), with
its [QTI buffer bridge](diagnostics/camera-qti-bridge.cpp), submitted one
STILL_CAPTURE request on rear ID 0 at 320 x 240. The HAL returned 0,
metadata partials 1/2 and an output buffer with status OK, no error and no
release fence. QTI CPU lock/unlock, device close and buffer release returned
0. A bounded unique-footer diagnostic identified JPEG footer offset 416,708
and JPEG size 4,594 bytes. The file decoded at 320 x 240 but was nearly
black: scene/exposure correctness remains unvalidated. Photos and vendor
calibration outputs are private temporary data, never Git artifacts.

The footer position exactly matches Android's resolution-scaled JPEG
buffer sizing: 416,716 logical bytes for 320 x 240 using maximum 4624 x 3472,
JPEG maximum 32,572,808 and minimum 256 KiB + 8; the footer is eight bytes
before that logical end. See
[AOSP Camera3Device::getJpegBufferSize](https://android.googlesource.com/platform/frameworks/av/+/d56db1d/services/camera/libcameraservice/device3/Camera3Device.cpp).
The buffer's physical capacity is not its resolution-scaled JPEG end.
The current diagnostic accepts only a unique bounded footer with matching
SOI/EOI and size; a production client should compute the documented size.

The bridge validates the installed vendor native-handle header/magic before
reading its mapped base at offset 84, after vendor LockBuffer success. That
field and the allocation size at offset 72 were verified against both the
public packed Qualcomm handle and the installed library instructions.
It only manages handles it allocated, refuses release while locked and
requires this exact inspected ABI. It is a diagnostic, not a portable HAL.
The [private capture supervisor](diagnostics/camera-test-capture.py) requires
a new private temporary output directory and manual temporary binaries;
the successful tests used 640 MiB, zero swap, 128 tasks and a 48-second
outer deadline. All runtimes were stopped/unmounted and loop devices
released. Megapixels remains nonfunctional; preview, exposure validation
and native app integration are separate outstanding gates.

A second capture after the user oriented the rear lens toward a lit object
also produced a valid 320 x 240 JPEG (4,590 bytes) but remained nearly black.
Correct scene reproduction is therefore still blocked; a covered lens alone
does not explain the observations. A bounded multi-frame exposure check is
the next diagnostic, not a declaration of a working camera app.

A bounded five-request follow-up reused the same vendor buffer only after
each matching result/fence and CPU unlock. Frames 1 through 4 were discarded;
only frame 5 was saved. All five requests returned OK output buffers and
validated JPEGs; the fifth file was 4,646 bytes and decoded at 320 x 240,
but remained nearly black. The current capture source includes that five-
request diagnostic. Additional frames alone did not establish correct
exposure. The next useful checks are public 3A/exposure result metadata,
actual sensor exposure programming and the selected physical camera path,
before preview or Megapixels integration. No camera-front mechanism was used.

Public result-metadata telemetry then reported AE_STATE 1 (SEARCHING) for
frames 1-3 and 2 (CONVERGED) for frames 4-5. Every frame reported exposure
7,067,946 ns and ISO 50. All requests still produced valid JPEGs. This does
not establish correct optical exposure: the visible images remained nearly
black in the preceding lit-scene test. Waiting for AE convergence alone is
not demonstrated as a fix. Sensor programming, scene/statistics consistency
and the selected physical sensor remain to inspect. The capture source now
logs only these public numeric metadata fields, not private calibration.

A 1280 x 720 comparison selected that advertised BLOB size in the same
five-frame client. Configuration, requests, CPU access and teardown all
succeeded; the fifth JPEG was 31,078 bytes and decoded at 1280 x 720 but
was still nearly black. AE again reported SEARCHING then CONVERGED with
7,067,946 ns / ISO 50. Low output resolution alone does not explain the
observed darkness. The comparison changed only the advertised-size filter
in the metadata enumeration loop to require width 1280 and height 720.

Kernel logs confirmed acquisition/start/stop/release of sensor 0x686 at
slave address 0x34 (IMX686) and successful IFE acquisition/release. GPIO
"No GPIO data"/"Input Parameters are not proper" messages were also present;
their causal significance is unproven. No explicit CSI overflow/fatal error
was observed in the bounded selected log tail; this is not an exhaustive
sensor-register or raw-pixel validation. Next investigations should compare
actual exposure/gain programming and raw/statistics data with the reported
AE result, and verify the OEM tuning/physical sensor path. No camera test
runtime was left active after this comparison.

The [metadata-only manual-capability probe](diagnostics/camera-metadata-ranges.c)
reported MANUAL_SENSOR support, exposure range 9,470 to 32,110,118,400 ns
and sensitivity range ISO 50 to 6400 for rear ID 0. It exited before opening
a camera device; no exposure setting was changed and no image was captured.
A future bounded comparison can clone the immutable default request and
request AE OFF with 50 ms / ISO 800, only after checking frame-duration and
request-key constraints. This would distinguish unchanged/ignored sensor
settings from an automatic-3A issue; it is proposed, not yet tested.
The private metadata runtime was removed successfully.

## Manual exposure versus automatic — 2026-10-05

Two finite rear-ID-0 runs used the same phone orientation toward an illuminated
scene. The manual run requested AE OFF, 50,000,000 ns, ISO 800 and frame duration
66,666,667 ns after checking MANUAL_SENSOR, ranges and advertised request keys.
It copied immutable HAL defaults into a separately allocated metadata packet;
no vendor-owned metadata was edited. All five result frames reported 50 ms /
ISO 800 and AE state INACTIVE. The saved fifth-frame 320 x 240 JPEG was 10,468
bytes and visibly depicted the ceiling and lamp, with highlight clipping.

The paired automatic run reported 7,067,946 ns and ISO 50 for all five frames,
with AE CONVERGED on frames four/five. Its fifth JPEG was 4,752 bytes and nearly
black on the same scene. Thus usable scene pixels and manual exposure application
are demonstrated through the existing sensor/ISP/JPEG path. Automatic exposure
or its application in this still-only client remains faulty; the pair does not
identify whether the defect is CamX 3A tuning, client request/session setup or
sensor-mode gain handling. A working automatic preview/3A session remains a gate.

Both runtime units completed successfully in about ten seconds, with zero
capture errors, OK buffers and successful lock/unlock/close/release. Private
mounts and loop devices were removed. No front/pop-up camera was opened.
Photos, firmware, binary diagnostics and raw OEM logs remain outside Git.

The shared capture diagnostic now supports explicit `--manual-exposure` for
rear ID 0 only, retaining automatic mode by default. The supervisor passes
that opt-in and uses a fresh private output directory/log instead of overwriting
the previous run. It is a diagnostic, not a Megapixels integration or an
automatic camera fix. Metadata allocation/append/update ABI is from
[AOSP camera_metadata.h](https://android.googlesource.com/platform/system/media/+/refs/heads/main/camera/include/system/camera_metadata.h).

The consolidated opt-in source compiled with NDK r27d under
`-Wall -Wextra -Werror`; its Python supervisor passed syntax parsing.
A subsequent hardware run of that consolidated `--manual-exposure` option
returned all five frames at the requested values, an 8,450-byte JPEG,
successful buffer/device cleanup and unit exit 0 in 10.18 seconds.
This is separate from the initial matched-scene pair described above.

## AE precapture and YUV boundary — 2026-10-05

An explicit automatic request copied STILL_CAPTURE defaults and set control
mode AUTO, AE ON, AE unlocked and AE precapture START on frame one / IDLE on
later frames. The original defaults already had AUTO/ON/unlocked/IDLE. Results
entered PRECAPTURE (5) on frames one to three, then CONVERGED (2), but stayed
at 7,067,946 ns and ISO 50. All five buffers returned OK; the last JPEG was
4,736 bytes. Thus a missing precapture trigger does not explain the fixed
exposure. The source diagnostic retains `--ae-precapture` as an explicit
rear-only alternative to `--manual-exposure`, not as a fix. Trigger semantics:
[Android CaptureRequest](https://developer.android.com/reference/android/hardware/camera2/CaptureRequest#CONTROL_AE_PRECAPTURE_TRIGGER).

A configure-only mapping probe found the CHI override, CamX statscore,
QTI AEC/wrapper, QTI static AEC and Vidhance AEC libraries loaded. This does
not identify which algorithm instance supplies the exposure; the presence
of a static library is not sufficient evidence of a static-AEC fallback.

A private single-YUV-stream PREVIEW-template experiment selected advertised
format 0x23 with SW_READ_OFTEN usage and unknown dataspace, first 176 x 144,
then 1280 x 720. Both configure_streams calls returned -19 before submitting
any frames. A first attempt also exposed an NDK __ndk1 versus Android __1
libc++ linkage mismatch in the new allocation bridge; rebuilding with the
already-inspected Android namespace fixed linkage, not configuration.
A stale 176 x 144 binary was inadvertently retested after a 720p compilation
error; it is not counted as a 720p result. The later successful 720p build
and runtime explicitly reported 1280 x 720 and returned the same -19.
No YUV frame, preview or AE behavior was validated by these failed configurations.

Those failed YUV variants were private experiments. Their resource failure
was subsequently resolved in the automatic rear-preview milestone below. All finite
units ended and their private mounts/loop devices were cleaned up.

The supervisor previously returned success after cleanup even when the camera
client failed. It now propagates a nonzero client status or client timeout as
a failed overall run, after cleanup; manager shutdown alone is not a capture
success criterion. Hardware client failures in the YUV attempts remain failures
even though their older outer supervisor units exited 0.

The corrected supervisor was hardware-tested with intentionally incompatible
manual/AE flags: the client exited 2 before opening the camera, all private
resources were cleaned up, and the outer unit correctly exited 1 (failure).
The final C source compiles with -Wall -Wextra -Werror; the supervisor parses
with Python ast. The integrated AE option has not been re-run for a new photo;
its earlier experimental AE measurements remain the evidence described above.

## Automatic rear preview capture — 2026-10-05

The previous YUV configuration failure was traced through bounded private
CamX logs to Preview_CVP0: `/dev/synx_device` and `/dev/cvp` were absent from
the isolated runtime. Both are existing character devices with matching sysfs
DEVNAME identities and integrated kernel drivers. Making them visible advanced
initialization, but CVP firmware loading then failed with ENOENT for all ten
nonempty loadable segments. The MDT header was accessible inside the private
runtime; the segment files were not accessible to the kernel worker threads.

The matching kernel peripheral-loader source queues each segment on `pil_wq`
and calls `request_firmware_into_buf` there. Its error index is an entry index,
not necessarily a `.bNN` filename: segment[13] here requested `cvpss.b19`.
All required pieces already existed in the mounted OEM firmware partition.
The diagnostic validates their sizes against the ELF32 MDT program headers,
refuses to overwrite any existing host firmware path, and temporarily links
the existing cvpss files into the host firmware search directory. It removes
only those exact symlinks in its cleanup path. No OEM firmware is copied,
published or written to a partition. The private runtime also binds the
existing OEM calibration and firmware directories read-only. Calibration
warnings remain; this is not proof of complete tuning/calibration coverage.

With these resources available, three bounded 1280 x 720 PREVIEW-template runs
completed fifteen rear-ID-0 requests, returned OK buffers and closed/released
the device and allocation successfully. In the first run automatic exposure
progressed from 7,067,946 ns / ISO 50 to 30,000,000 ns / ISO 949, reaching
CONVERGED on frame eleven. The image-rendering and consolidated-source runs
converged near ISO 936. Thus the previous fixed-exposure STILL-only diagnostic
does not establish broken OEM AE; the realtime preview path runs adaptive AE.

The renderer calls the actual installed `GetYUVPlaneInfo` function rather
than assuming tightly packed NV12. The inspected public LP64 android_ycbcr
layout is 80 bytes. This allocation reported Y stride 1280, chroma stride
1280, chroma step 2, Y offset 0, Cb offset 983041 and Cr offset 983040 within
a 1,474,560-byte allocation. Every plane span is bounded before reading.
The Cb/Cr ordering is therefore NV21-like, not guessed NV12. One final frame
was rendered as a 2,764,816-byte PPM and independently inspected as a visible
ceiling, moulding and light fixture at 1280 x 720. The BT.601 limited-range
conversion is diagnostic; accurate colorimetry, focus and photo quality are
not validated. Images and full vendor logs remain private, outside Git.

The existing source diagnostic now has an explicit rear-only `--preview`
mode, mutually exclusive with manual exposure and AE precapture. It keeps
the JPEG path and common buffer bridge. The opt-in host wrapper is
[camera-test-rear-preview.py](diagnostics/camera-test-rear-preview.py), which
runs the existing supervisor with `--preview` in private mount/network
namespaces. It needs the matching diagnostic binaries, metadata inspector,
mounted OEM inputs and context shim already documented here. It must be run
under a finite service (48 seconds, 640 MiB, no swap, 128 tasks), with no
concurrent camera client. Ordinary cleanup and handled interruption remove
the temporary links; an uncatchable SIGKILL or host failure still requires
checking for them before another trial. This is not installed persistently.

Both final C and C++ sources compile with `-Wall -Wextra -Werror`, Android
`__1` libc++ namespace and the inspected matching system libc++. The final
consolidated hardware trial exited 0 in 10.874 seconds, saved a mode-0600 PPM,
and removed its isolated runtime and all thirteen temporary CVP links.
The helper retains nonzero result propagation. A five-frame manual JPEG
regression trial of these same binaries also exited 0 in 10.139 seconds,
returned valid JPEG buffers and closed/released the device successfully. No kernel/rootfs rebuild,
reboot, front-camera request or motor movement was used.

This is a working automatic rear capture backend, not yet an interactive
preview or functional Megapixels integration. Next: connect this bounded
backend to the photo application's capture/preview flow, retaining isolation,
resource cleanup and rear-only selection. It does not validate video recording,
other camera IDs, flash photography, continuous AF or a generic image recipe.
Public layout reference: [Qualcomm gralloc YUV layout source](https://android.googlesource.com/platform/hardware/qcom/sm7250/display/+/refs/heads/android12-s2-release/gralloc/gr_utils.cpp).

## Opt-in rear snapshot application — 2026-10-05

A small native GTK4 application now invokes the validated automatic rear
capture backend. It runs as the normal desktop user and provides "Prendre
une photo" and "Ouvrir la photo", displays the last saved image, and retains
normal window close controls. It has no text-entry widget. The UI uses the
existing Cairo renderer fallback and keeps work off the GTK event thread.
This is a snapshot application, not a live viewfinder; exposure/focus/zoom,
other lenses, video recording and flash photography are not app features.
Megapixels itself remains incompatible with this downstream camera API.

The privileged backend is a single fixed oneshot service. Installed helpers
and binaries are root-owned at fixed paths, outside `/tmp`; the service accepts
no caller-selected filename, command, library or camera ID. The dedicated
Polkit rule permits only starting that unit from the selected active local
user. Direct policy inspection using the live Mobian app's PID/start time/UID
allowed that action; restart and another unit's start instead required separate
authentication. No other service was started by that permission test.
An earlier nonprivileged pkcheck probe could not pass action details under
this Polkit version; it was not counted as a policy result.

The service has a 50-second TimeoutStartSec, no swap, 640 MiB memory limit,
128-task limit and control-group cleanup. RuntimeMaxSec was removed after
systemd correctly reported it ineffective for a oneshot unit. The backend
has its own shorter subprocess bounds. It validates the final PPM dimensions,
header and size, atomically publishes a group-readable mode-0640 intermediate
under `/run/lmi-camera`, and removes the newly created private diagnostic output
directory. That intermediate is volatile and replaced on the next shot.
The UI saves a distinct mode-0600 PNG in the user's XDG Pictures/Camera folder,
owned by that user; firmware, calibration and logs are not exported to Images.
The service is demand-started, not enabled at boot, and checks the exact
validated kernel release again on every invocation.

Two end-to-end UI trials launched under Mobian completed in 13.330 and 13.329
seconds, printed PHOTO_SAVED and exited successfully. Their saved PNGs were
939,274 and 941,222 bytes; decoding validated 1280 x 720. The latter used the
final volatile intermediate and a no-password service invocation. The fixed
service then reported success/inactive, with no CVP links left behind.
These checks exercise the same capture handler as the button, but operator
touch/save validation is now operator-confirmed; opening in Photos remains pending. Screen-copy inspection while the
display was off failed and is not counted as visual UI validation. There was no default PNG handler in the session, so the Open button now
invokes the existing validated `lmi-photos` launcher directly with the saved
filename, rather than relying on MIME association. Operator opening validation
remains pending. The UI smoke-test mode also propagates capture failure as a
nonzero exit instead of equating clean window shutdown with a saved photo.
The app has been left open for the operator check; no camera job is running at idle.

Sources: [GTK interface](files/lmi-camera.py),
[fixed service helper](files/lmi-camera-capture-service.py),
[unit](files/lmi-camera-capture.service),
[small diagnostic builder](scripts/build-rear-snapshot.sh), and
[explicit installer](scripts/install-rear-snapshot.py).
The builder requires an NDK toolchain bin directory, matching external Android
libc++.so and a fresh output directory. It compiles three small userspace
objects with warnings as errors and copies only project-authored helpers/UI;
no proprietary library/firmware is included in the output bundle or Git.
The build recipe was executed successfully on the host. The installer requires
an explicit user and diagnostic-boot opt-in and checks the exact measured
kernel release before deploying. It does not change the generic Mobian image
or the optional-app installer. A portable camera recipe needs later work.


### Portrait orientation and shorter teardown — 2026-10-05

The fixed backend now exports the rear sensor orientation from the HAL's
static metadata (90 degrees), rather than guessing from the image dimensions.
The unprivileged UI rotates the actual pixels clockwise before saving: the
portrait PNG is 720 x 1280. Decoded pixels matched the rotated raw frame, and
the operator confirmed the photograph is upright with the phone held vertically.
This corrects natural portrait orientation only; accelerometer-driven landscape
rotation remains unimplemented. Existing photos are unchanged.

After the capture client closes its device, the supervisor now explicitly stops
its own private manager process group. Previously it waited four seconds for
that permanent daemon to exit naturally. A full UI smoke trial, including its
startup and exit delays, completed successfully in 10.048 seconds, compared with
14.610 seconds in the preceding orientation trial. These are individual trials,
not a latency benchmark. The service was inactive with a success result after
capture; no private HIDL runtime or temporary CVP firmware links remained.
Capture still initializes the OEM runtime for each shot and has no live preview;
this improvement does not establish normal instant-camera responsiveness.


The next change removes two fixed two-second pauses. Private manager readiness
is now polled for at most two seconds using fresh private-hwbinder descriptors:
EBUSY confirms an existing context owner; an unowned probe is released on close.
An early manager exit or a different ioctl error fails the capture. The existing
IPC prerequisite query still follows this gate. The camera client result is
collected immediately, without a diagnostic sleep beforehand.
Two complete UI trials succeeded in 8.625 and 8.623 seconds, including the smoke
mode's 0.5-second startup and one-second exit delays. Both saved photographs;
the service was inactive afterwards and its temporary runtime/firmware links
were absent. This is still an on-demand, per-shot runtime, not live preview.


### Bounded rear live preview — 2026-10-05

The rear client now supports an explicit 45-frame sequence diagnostic and a
120-frame bounded live mode. Both open and configure camera ID 0 once, reuse the
same real buffer after result/fence/unlock completion, and save every third
frame from frame 15 onwards. PPM publication uses a temporary filename followed
by rename, so a reader never observes a partially written image. The original
single-shot mode remains available.

The 45-frame hardware trial returned eleven preview images, from 2.805 to
10.057 seconds after the request loop began: subsequent images were about
0.725 seconds apart in that dark-scene trial. Device close and buffer release
returned zero. A separate fixed preview service then published 36 images during
a 120-frame run; the unprivileged GTK interface decoded successive frames and
displayed upright portrait images. Automatic completion and repeated operator
relaunches were observed. This is a slow live view, not video-rate preview.

The normal UI now saves its current rotated preview buffer when the photo
button is pressed, without a new HAL initialization or privileged capture
request. Operator confirmation of the save responsiveness remains pending.
The original end-to-end single-shot smoke mode is retained. The preview stops
automatically after its bounded run (about 30 seconds in the observed scene);
use Relancer l’aperçu to resume. Normal window closure requests its fixed stop
action. The fixed stop action was separately tested while frames were arriving: the
service became inactive with no private runtime directory or CVP links left.
The first early-stop trial left an empty host directory; forwarding termination
and waiting for the private supervisor cleanup corrected that failure.

The preview service exports only an atomic image and minimal orientation/frame
metadata under /run/lmi-camera, root-owned and group-readable. Vendor logs,
calibration and runtime state remain private and are removed on completion.
It has a 48-second runtime limit, six-second stop limit, 640 MiB memory limit,
no swap and control-group cleanup. It conflicts with the single-shot service.
The scoped rule permits start/stop of this preview unit only, alongside the
existing snapshot-start permission. Live-app PID/start-time/UID policy checks
allowed preview start/stop and required separate authentication for restart
and another unit's start; no other unit was started.

Sources: [preview publisher](files/lmi-camera-preview-service.py) and
[bounded unit](files/lmi-camera-preview.service). The explicit installer and
small userspace builder include these sources. Exact diagnostic-kernel gating,
rear-only scope and external OEM inputs remain unchanged. This is not generic
image integration, Megapixels support, calibrated photography, autofocus,
landscape auto-rotation, or video recording.


Application interoperability check: the current Mobian PipeWire graph exposes
no Video/* nodes, and no v4l2loopback module was found in the installed module
tree. Megapixels 1.8.3-1 is installed; Snapshot has no candidate in the configured
APT repositories. These observations do not prove all camera applications are
unsupported; they show that installing another UI alone does not connect the
private OEM runtime to a standard camera source. A standards-compatible stream
bridge remains required before testing another frontend. The operator reported
that the current live preview is too slow; it remains a diagnostic prototype,
not an acceptable normal camera implementation. One operator-triggered save was
observed in the UI log, but perceived save latency is not yet confirmed.


### Preview cadence measurement and automatic reactivation — 2026-10-05

Per-frame monotonic timings separate request/result/fence wait, CPU lock,
conversion/write and unlock. In a 45-frame dark-scene trial, frames after warmup
without image publication averaged 234.633 ms waiting, 0.042 ms locking,
0.011 ms in the discard path and 0.023 ms unlocking. Published frames averaged
241.746 ms waiting, 0.052 ms locking, 13.667 ms conversion/write and 0.064 ms
unlocking. Thus RGB conversion is not the dominant measured delay.

The live prototype also deliberately published only every third frame, which
added a further factor of three to the visible interval. Live mode now publishes
every completed frame after its 15-frame warmup; the sequence diagnostic retains
its original every-third-frame sampling for comparison. The GTK poll interval
is reduced from 250 to 50 ms. A complete live run displayed all 106 eligible
frames with a mean UI-log interval of 0.242 seconds. The stream completed with
no private runtime directory or CVP firmware links left behind.

Fresh-window activation already started preview automatically. Re-activating
an existing window after its preview ended previously only presented the stale
last image. That path now starts preview too, and the stale picture is cleared
during initialization. A real same-application activation after automatic
completion produced a new stream without pressing the restart button.
Operator visual confirmation is pending.

The current client submits a single request and waits for its returned buffer
before submitting the next. This serial design and the measured HAL-result
wait cap the current preview around four frames per second. The timing alone
does not distinguish sensor exposure from internal processing/pipeline latency;
a queued multi-buffer client is the next diagnostic, not a proven fix yet.
No kernel rebuild was needed for these changes. Mainline has an SM8250 CAMSS
implementation, but that alone does not establish IMX686/lmi/Megapixels support
on this downstream kernel or a ready-to-use replacement kernel.


### Queued three-buffer rear preview — 2026-10-05

The operator confirmed automatic preview, but still found the serial path too
slow. A separate rear-only queued-buffer diagnostic then returned 106 published
images with a mean 0.0444-second interval, versus about 0.24 seconds for serial
requests. Device close and release of all three buffers returned zero. The
operator subsequently confirmed the displayed preview was clearly smoother.

Live mode now maintains three real QTI buffers and stable request/handle storage
in a ring. Result callbacks match frame number, stream and returned handle.
Each buffer is reused only after its result is complete, its release fence has
signalled and closed, and CPU conversion/unlock has finished. The negotiated
stream must allow at least three buffers. The single-shot and 45-frame serial
sequence remain separate paths. This follows the HAL request model allowing
multiple requests in flight; no kernel or firmware change was needed.
[Android HAL request model](https://source.android.com/docs/core/camera/camera3_requests_hal).

Queueing stops after 25 seconds, then drains already submitted requests. A
900-frame hard cap, bounded result/fence waits and existing service limits also
remain in force. In a full final UI run, the publisher delivered 553 images;
the real active application displayed 423, with a mean displayed interval of
0.0581 seconds (about 17 frames/s). This is not a controlled lighting benchmark
or a claim of 30 fps: earlier backend and UI trials used different scenes and
exposure. The root publisher polls every 20 ms and the GTK UI every 33 ms,
retaining only the latest image rather than accumulating a frame backlog.

Automatic completion removed all private runtime directories and temporary
CVP links. Early-stop testing also left neither behind. The original fixed
snapshot service still saved an orientation-90 frame and ended successfully.
The complete small userspace source bundle compiled with warnings as errors.
The existing window automatically restarts preview on reactivation after
completion. Operator confirmation covers startup and improved smoothness;
a fresh saved-photo responsiveness confirmation remains pending.

Preview is still bounded, rear-only, 1280 x 720 with portrait pixel rotation.
The app saves the displayed preview frame, not a full-resolution sensor still.
Continuous autofocus, landscape auto-rotation, generic-image integration,
Megapixels/PipeWire compatibility and video recording remain unvalidated.


### Foreground-owned continuous preview — 2026-10-05

The normal preview no longer stops every 25 seconds and the manual restart
button is removed. GTK window activation/visibility now determines whether the
camera should run. Bringing the app forward starts it; leaving for another app
or closing it stops it. The operator confirmed automatic resume after leaving
and returning through the desktop icon. SSH activation alone did not always
receive compositor focus and was not counted as a foreground-return success.

The dedicated foreground mode keeps the three-buffer queue running without a
per-session time cap. The 25-second/frame-capped live diagnostic, serial sequence
and single-shot paths remain available separately. Long-running vendor output
is drained into a 160-line tail rather than accumulated without limit. The UI
also reports progress at most once per second instead of logging every frame.

The unprivileged UI atomically renews a small mode-0600 lease in its user runtime
directory every second. The fixed root publisher checks freshness (under four
seconds), active state, owner UID, real GUI PID, process start ticks and expected
GUI command. A stale lease, hidden/inactive window or disappearing GUI causes
shutdown. No caller-selected command, camera ID or root output path is accepted.
The notify service has a ten-second watchdog and retains memory/swap/task limits;
its publisher also rejects an eight-second gap without a new frame. A session
cap is therefore replaced by ownership/liveness checks, not an unattended
background camera daemon. Foreground UID is supplied by the explicit installer.

A real foreground session ran for 137.8 seconds and published 3,034 images,
without a restart at 25 seconds. Opening the Calculator changed the window lease
to inactive and stopped the stream. Initial teardown testing found that a
three-second publisher wait could kill the firmware wrapper before its own
cleanup finished; increasing that wait to eight seconds and the unit stop limit
to twelve corrected it. Subsequent background teardown and a separate GUI-exit
trial removed both private runtime directories and temporary CVP links. The
operator validated returning from another app resumes automatically.

Start/stop commands are serialized off the GTK event thread. The UI waits for
service readiness before consuming frames from a new session, avoiding a stale
end marker during a rapid focus change. All existing portrait/rear-only and
preview-frame photo-quality limitations still apply. This change does not add
video recording, full-resolution stills or standard-camera-app integration.


### Existing camera application trial — 2026-10-05

Debian Lomiri Camera 4.0.8+dfsg-5 was installed experimentally. Its Wayland/OpenGL
interface launches, but the operator and a screenshot confirmed a black
viewfinder. No photo/video was validated; the Android camera bridge is not
installed. This is not a replacement for the validated rear HAL3 preview and is
not added to the image recipe. See `docs/validation/lomiri-camera-app-installation-test-2026-10-05.md`
(repository-root-relative) for installation findings and limitations.


### Snapshot / PipeWire rear-camera proof — 2026-10-05

Native Debian `gnome-snapshot 48.0.1-1` displays a real rear preview through an
experimental userspace PipeWire publisher (operator-confirmed). Five JPEGs
decode successfully. A second explicitly stopped video is a valid 6.58-second
WebM, portrait 720 x 1280 at 10 fps, with mono audio; playback assessment is
pending. Gallery and GPU issues remain. Capture trials are bounded, and a
foreground-owned Snapshot launcher/image integration is not implemented. See
`docs/validation/snapshot-pipewire-rear-preview-2026-10-05.md`
(repository-root-relative).
