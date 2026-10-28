# Camera kernel recipe for the community tree — October 28, 2026

Date: 2026-10-28
Canonical repository: `/home/linuxagent/xiaomi-lmi-linux-port`, branch `lmi-linux7`.
Kernel of the permanent boot: `7.2.12-lmi-community-port1-dirty`, built from the
community tree, not from the pinned tree of the observer kit.

Companion of the sensor binding record of 2026-10-28 and of the Snapshot 51
record of the same date. Those records established that the rear sensor never
binds because the driver has no OF match table, and that the candidate of the
application needs the FUSE device of the kernel. This record delivers the
recipe that builds a kernel carrying both, and states what the operator has
to check after the installation.

## 1. What the recipe does

`kernel/experimental/linux7/tools/build-community-camera-kernel.sh` takes the
community tree, produces a kernel that carries the rear camera and the FUSE
device, and checks the result. It never touches the input tree unless
`--in-place` is given: by default the tree is copied to a scratch directory,
so the operator can run it twice and compare two results.

```
Usage: bash tools/build-community-camera-kernel.sh [--tree DIR] [--build DIR]
        [--out DIR] [--jobs N] [--prepare-only] [--in-place]
```

The steps are:

1. **the working tree** — a copy of the community tree, or the tree itself
   with `--in-place`;
2. **the camera patch** — `patches/0004-lmi-ov13b10-of-match.patch`, which
   restores the OF match table of the sensor driver, with a backup of the
   original file;
3. **the camera configuration** — the configuration of the build is merged
   with `configs/camera.fragment`, which carries the thirteen symbols of the
   camera chain and `CONFIG_FUSE_FS=y`;
4. **the build** — the kernel image and the device tree of the board;
5. **the check** — the produced device tree is read back and must carry the
   rear sensor with its compatible string, its four data lanes, its link
   frequency, its supplies and its endpoint; the hashes of the two artifacts
   are written.

`--prepare-only` stops after the third step, which is what makes the recipe
testable without an hour of build time.

## 2. What the configuration fragment carries

The camera symbols, taken from the running handset configuration, and the
FUSE file system:

| Symbol | Reason |
|---|---|
| `CONFIG_MEDIA_SUPPORT`, `CONFIG_MEDIA_CAMERA_SUPPORT`, `CONFIG_MEDIA_PLATFORM_SUPPORT` | the media support and the two sub-menus the drivers live in |
| `CONFIG_MEDIA_CONTROLLER` | binds the sensor to the CSI-2 receiver through the device tree graph |
| `CONFIG_VIDEO_DEV`, `CONFIG_V4L_PLATFORM_DRIVERS` | the V4L2 core and the platform layer the CAMSS driver requires |
| `CONFIG_V4L2_ASYNC`, `CONFIG_V4L2_FWNODE` | the asynchronous notifier and the fwnode graph |
| `CONFIG_VIDEO_V4L2_SUBDEV_API`, `CONFIG_VIDEOBUF2_DMA_SG` | the subdev API and the buffer allocator |
| `CONFIG_VIDEO_CAMERA_SENSOR` | the camera sensor framework |
| `CONFIG_VIDEO_OV13B10` | the rear sensor driver |
| `CONFIG_VIDEO_QCOM_CAMSS` | the camera subsystem with its SM8250 resource set |
| `CONFIG_FUSE_FS` | the document portal of the session, and through it the candidate of the application |

The chain has to be enabled as a whole: a fragment that only sets the two
driver symbols is silently dropped by `olddefconfig`. That was measured.

## 3. What was validated before the operator build

The preparation step was run against the community tree:

```
== apply the camera patch ==
patching file drivers/media/i2c/ov13b10.c
1719:		.of_match_table = ov13b10_of_match,

== merge the camera configuration ==
  ok   CONFIG_MEDIA_SUPPORT=y
  ...
  ok   CONFIG_VIDEO_OV13B10=y
  ok   CONFIG_VIDEO_QCOM_CAMSS=y
  ok   CONFIG_FUSE_FS=y

== result ==
CAMERA_KERNEL_PREPARED_NO_BUILD
```

The camera stack of the same tree also compiles with the patch and the
configuration, in a scratch copy that never touches the operator tree:

```
  CC      drivers/media/i2c/ov13b10.o
  CC      drivers/media/platform/qcom/camss/camss.o
  ok   drivers/media/i2c/ov13b10.o 23224 bytes
  ok   drivers/media/platform/qcom/camss/camss.o 539928 bytes
```

and the board device tree of that tree compiles with the rear sensor in it:

```
  ok   ovti,ov13b10
  ok   camera@10
  ok   data-lanes
  ok   link-frequencies
  ok   reset-gpios
  ok   avdd-supply
  dtb size: 128513 bytes
COMMUNITY_CAMERA_STACK_COMPILES
```

## 4. The operator sequence

1. run the recipe:
   `bash kernel/experimental/linux7/tools/build-community-camera-kernel.sh --out <dir>`;
2. check that the recipe ends with `CAMERA_KERNEL_BUILT` and that the two
   artifacts are in `<dir>` with their hashes in `<dir>/SHA256SUMS`;
3. install the kernel image and the device tree as the permanent `system5`
   entry, **keeping the Mobian 4.19 entry as the fallback**, because that
   entry carries the only rear camera that is qualified today;
4. boot, then check:

| Check | Expected |
|---|---|
| `/sys/bus/i2c/devices/21-0010/driver` | exists: the sensor is bound |
| `/dev/v4l-subdev*` | appears: the sensor is a subdev |
| the boot log | carries the identification of the sensor |
| `/dev/fuse` | appears: the document portal can mount |
| `native-pipewire-v4l2-source /dev/video0` | prints `V4L2_SOURCE_READY` |
| the camera application | opens with a viewfinder |

5. rebuild the bundle so that the producer is installed with the launcher,
   and open the camera application.

## 5. What is not claimed

- No kernel was built with this recipe: the preparation step and the camera
  objects were validated, the full build is the operator's.
- No sensor binding is claimed on the handset, because nothing was flashed.
- The camera of the application is **not** qualified. The candidate of the
  application is installed but does not start, because the FUSE device is
  missing until this kernel is installed.
