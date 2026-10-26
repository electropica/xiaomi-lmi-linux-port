# Isolated front-camera native candidate

This is a diagnostic prerequisite, not installed front-camera support.
It prepares the reviewed R2 argument-selection changes on copies, then applies
the selected timing/fixed-FPS/NEON bundle preparation. The shared camera source,
accepted rear bundle, installed application and full-image pins remain unchanged.

Default preflight (no compilation or device contact):

```sh
python3 -B userspace/camera/front-camera-candidate/build-native.py
```

Operator-only compilation:

```sh
sudo python3 -B /home/linuxagent/xiaomi-lmi-linux-port/userspace/camera/front-camera-candidate/build-native.py --execute
```

The marker is `FRONT_CAMERA_NATIVE_TOOLS_BUILT_NOT_INSTALLED`.
Default output is `output/front-camera-native-candidate` (must not exist).
The retained NDK r27d and qualified Oct-21 camera bundle are external inputs;
`--cc`, `--bundle` and `--output` select explicit alternatives. No download,
package installation, chroot, rootfs/kernel build or phone command is performed.
Missing or mismatched inputs stop preparation; an existing output is never erased.

Two Android/bionic executables are compiled: the standalone module enumerator
and capture harness. The latter retains non-rear refusal unless explicitly
allowed. The emitter-facing patch is preserved as a reviewed prerequisite but
no new PipeWire producer or second camera node is compiled/installed here.
Existing bridge/shim/metadata assets are checksum-verified and copied to the
isolated output; proprietary Android dependencies are not added to Git.

`enumerate-private-runtime.py` selects the standalone enumerator in the
existing private bionic/HIDL runtime. It is not a passive file inventory:
loading the OEM module and calling init can touch hardware, even though this
executable does not call camera-device open or start a stream. Do not run it
outside the coordinator's bounded device protocol.

`capture-private-runtime.py` and `preview-private-runtime.py` are later-stage
assets, not permission to open the front sensor. Their fixed paths target a
separate `/var/tmp/lmi-front-hal-trial-20261026/backend`, never the installed
rear backend. Motor supervision, exclusive HAL ownership, firmware/mount cleanup,
privacy and foreground/lock behavior still require integration and validation.
No fake source should be published just to make Snapshot show a switch button.

Host validation: exact before/after hashes for four R2 files; forward patch
check/application on scratch; selected bundle patches applied without fuzz;
Python AST and private-wrapper path checks. The earlier extracted-code R2
harness passed91 checks, not a full camera-runtime test. No compilation or
handset use is claimed by the preflight marker. A compile failure leaves its
output intact for inspection; do not delete the accepted rear rescue.
