# Camera userspace status

Megapixels is installed in the validated userspace, but its required
`qcom,kona-mtp.ini` configuration is absent and the downstream camera media
pipeline was not demonstrated. Sensor identities remain suggestions rather
than confirmed node-to-device mappings. No speculative Megapixels
configuration is included. See the
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
