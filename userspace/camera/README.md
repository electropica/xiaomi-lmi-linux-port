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
