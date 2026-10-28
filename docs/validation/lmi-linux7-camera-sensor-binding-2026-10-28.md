# Rear camera sensor binding on the Linux 7.2.12 community port — October 28, 2026

Date: 2026-10-28
Canonical repository: `/home/linuxagent/xiaomi-lmi-linux-port`, branch `lmi-linux7`,
HEAD `3c640a9`.
Handset: POCO F2 Pro / Xiaomi lmi, permanent `system5` boot, kernel
`7.2.12-lmi-community-port1-dirty`, Debian 13 (trixie) userspace, Phosh session
as `mobian`.

Continuation of the engine-gate record of 2026-10-27. That record established
that the camera application on this kernel has no frame source, and named the
missing engine binding as the first concrete dependency. This record closes
that dependency at the source level: it identifies the exact reason the rear
sensor never binds, states the smallest change that fixes it, and proves that
change on the host. Nothing has been flashed, so no handset result is claimed.

## 1. The question

The rear sensor is described in the board device tree, the driver is built in
and registers, and the i2c core creates the client — yet the sensor is never
probed and no subdev appears. What exactly is missing?

## 2. The evidence on the handset

Read on 2026-10-28 on the running system:

| Check | Result |
|---|---|
| Driver symbol | `CONFIG_VIDEO_OV13B10=y` |
| Driver registration | `calling ov13b10_i2c_driver_init+0x0/0x28 @ 1` in the boot log, returning 0 |
| i2c client | `/sys/bus/i2c/devices/21-0010` exists, `name` is `ov13b10`, `modalias` is `of:NcameraT(null)Covti,ov13b10`, an `of_node` is present |
| Driver link | **absent**: `/sys/bus/i2c/devices/21-0010/driver` does not exist, the client is not bound to any driver |
| Probe message | **none**: the boot log carries no probe error and no probe at all for the sensor |
| Subdev | **none**: no `/dev/v4l-subdev*`, only the fourteen `msm_vfe*_video*` ISP outputs of `qcom-camss` |
| Camera platform device | `ac6a000.camss`, compatible `qcom,sm8250-camss`, probed and registered |

A driver that is registered, a device that exists with the right compatible
string, and no probe at all: the i2c core never associated the two.

## 3. The cause

The matching table of the driver is the reason. In the tree that produced the
running kernel, `drivers/media/i2c/ov13b10.c` carries **only an ACPI match
table**:

```c
static struct i2c_driver ov13b10_i2c_driver = {
	.driver = {
		.name = "ov13b10",
		.pm = pm_ptr(&ov13b10_pm_ops),
		.acpi_match_table = ACPI_PTR(ov13b10_acpi_ids),
	},
	.probe = ov13b10_probe,
	...
```

There is no `of_device_id` table and no `.of_match_table`. An OF device is
matched through the driver `of_match_table`, so a sensor described in the
device tree can never bind to this driver, whatever the device tree says.

This is not a local edit of the community tree. The pinned upstream tree used
by the project (`output/minimax-kernel7-feasibility/linux-v7.2.12-clean`,
revision `cc9de5d4b5ab6459f5774946aa3195ad51236fa8`) and the community tree
that produced the handset kernel (`/home/linuxagent/lmi-modem-trial/source`)
carry a **byte-identical** driver: the unified diff between the two files is
empty. The rework that took this driver to the fwnode API left it ACPI-only,
so the OF support of the sensor is gone upstream, not locally.

The camera subsystem itself is fine on this kernel: the mainline CAMSS driver
has an SM8250 resource set (`sm8250_resources`, matched through
`qcom,sm8250-camss`) and it registers. It binds its sensor through the fwnode
graph, so a bound sensor subdev is exactly what it waits for.

## 4. The device tree is already complete

The sensor node of the community board tree
(`arch/arm64/boot/dts/qcom/sm8250-xiaomi-lmi.dts`) carries everything the
driver checks:

| Driver requirement | Board device tree | Result |
|---|---|---|
| `compatible` | `ovti,ov13b10` | present |
| clock rate `OV13B10_EXT_CLK` | `assigned-clock-rates = <19200000>` | 19.2 MHz, exact |
| supplies `avdd`, `dovdd`, `dvdd` | `avdd-supply`, `dovdd-supply`, `dvdd-supply` | present |
| reset gpio | `reset-gpios = <&tlmm 91 GPIO_ACTIVE_LOW>` | present |
| four CSI-2 data lanes | `data-lanes = <1 2 3 4>` | present |
| 560 MHz link | `link-frequencies = /bits/ 64 <560000000>` | present |
| endpoint to the CSI-2 receiver | `remote-endpoint = <&csiphy1_ep>` | present |

`clock-frequency` is absent, but the driver tolerates that: the clock helper
is called with a fixed rate of false, so a missing property leaves the rate at
zero instead of failing, and the driver then compares the **clock rate** with
`OV13B10_EXT_CLK`, which the assigned 19.2 MHz satisfies.

**No device tree change is needed.** That is the reason the deliverable of
this stage is a driver patch and not a board change.

## 5. The kernel patch

`kernel/experimental/linux7/patches/0004-lmi-ov13b10-of-match.patch` restores
the OF match table for the two upstream compatible strings and declares it in
the driver:

```c
static const struct of_device_id ov13b10_of_match[] = {
	{ .compatible = "ovti,ov13b10" },
	{ .compatible = "ovti,ov13b10r" },
	{ /* sentinel */ }
};
MODULE_DEVICE_TABLE(of, ov13b10_of_match);
```

```c
	.driver = {
		.name = "ov13b10",
		.pm = pm_ptr(&ov13b10_pm_ops),
		.of_match_table = ov13b10_of_match,
		.acpi_match_table = ACPI_PTR(ov13b10_acpi_ids),
	},
```

The ACPI table and the ACPI behaviour are untouched, so the platforms the
rework targeted keep working. The patch was generated mechanically from the
driver file, so it applies without fuzz.

## 6. The camera configuration

`kernel/experimental/linux7/configs/camera.fragment` carries the camera
symbols. They are not a guess: they are the exact symbols of the running
handset configuration, read from its own `/proc/config.gz`.

The chain has to be enabled as a whole. The sensor driver sits behind the
camera sub-menu of the media support, and the CAMSS driver additionally
requires the V4L2 platform driver layer, which requires `CONFIG_VIDEO_DEV`
and the media controller. A fragment that only sets the two driver symbols is
silently dropped by `olddefconfig`, because the symbols that make them
reachable are missing; that was measured, not assumed.

| Symbol | Role |
|---|---|
| `CONFIG_MEDIA_SUPPORT` | media support |
| `CONFIG_MEDIA_CAMERA_SUPPORT` | camera sub-menu, where the sensor driver lives |
| `CONFIG_MEDIA_PLATFORM_SUPPORT` | platform sub-menu, where the CAMSS driver lives |
| `CONFIG_MEDIA_CONTROLLER` | media controller, used to bind the sensor to the receiver |
| `CONFIG_VIDEO_DEV` | V4L2 core |
| `CONFIG_V4L_PLATFORM_DRIVERS` | V4L2 platform layer, required by the CAMSS driver |
| `CONFIG_V4L2_ASYNC`, `CONFIG_V4L2_FWNODE` | asynchronous notifier and fwnode graph |
| `CONFIG_VIDEO_V4L2_SUBDEV_API` | sensor subdev API |
| `CONFIG_VIDEOBUF2_DMA_SG` | buffer allocator of the CAMSS driver |
| `CONFIG_VIDEO_CAMERA_SENSOR` | camera sensor framework |
| `CONFIG_VIDEO_OV13B10` | the rear sensor driver |
| `CONFIG_VIDEO_QCOM_CAMSS` | the camera subsystem with its SM8250 resource set |

Every symbol has to be built in: the initramfs carries no module payload, so
a modular symbol would never load and the sensor would never bind, with no
message to explain it.

## 7. Host validation

`kernel/experimental/linux7/tools/check-camera-patch.sh` proves the whole
chain on the host, without producing an image and without touching the
handset:

```
HOST_VALIDATION_OK
```

What it checks, in order:

1. the pinned tree is still at revision `cc9de5d4`;
2. the patch series applies cleanly to a copy of that tree;
3. the patched driver carries `MODULE_DEVICE_TABLE(of, ov13b10_of_match)` and
   `.of_match_table`, and the ACPI table is still there;
4. the merged configuration resolves all thirteen camera symbols as `=y`;
5. the patched driver compiles as an object
   (`drivers/media/i2c/ov13b10.o`, 23784 bytes);
6. the same patch applies to the community tree that produced the handset
   kernel;
7. the community board device tree carries the eight properties the driver
   requires, so no device tree change is needed.

The compile is the strongest of these: the patched driver builds with the
kernel's own flags in the tree that will produce the next kernel.

## 8. The userspace piece

The application needs a camera on PipeWire, because the camera application of
this session is GNOME Snapshot and it enumerates cameras through the
GStreamer PipeWire device provider. The existing OEM producer reads a PPM
file that the privileged preview service writes; on the Linux 7 line there is
no such service, because there is no OEM HAL.

`userspace/camera/diagnostics/native-pipewire-v4l2-source.c` is the Linux 7
producer: it opens a V4L2 capture node, the CAMSS VFE output, and publishes
the frames as a PipeWire camera node with the media properties the provider
expects (`media.class` Video/Source, `media.category` Capture, `media.role`
Camera, `api.v4l2.device`, `api.libcamera.location` back). It reads the video
node with the public V4L2 ioctls and the public PipeWire stream API, and it
never opens a microphone and never records.

The producer compiles with the strict flags of the bundle build
(`-O2 -Wall -Wextra -Werror`, PipeWire 0.3 and SPA headers), verified on the
host. It is wired into the bundle preparation, the bundle build in the
retained ARM chroot and the installer, so the operator build produces
`native-pipewire-v4l2-source` on the device next to the OEM producer.

## 9. What is not qualified

- Nothing has been flashed. The sensor binding is **not** proven on the
  handset; it is proven at the source level, and the handset result comes
  after the operator builds and installs a kernel that carries the patch.
- The producer has **not** produced a frame. On the current system there is
  no bound sensor, so there is nothing to publish.
- The camera application still shows the engine notice of the 2026-10-27
  record on the current system. That is the intended behaviour while no
  frame source exists, and it is unchanged by this stage.
- The producer is not wired into the launcher yet: the launcher decides
  between the OEM engine and the notice, and switching it to the V4L2
  producer belongs to the stage where frames exist, so that the switch can be
  qualified on the handset.

## 10. Operator sequence

1. apply `kernel/experimental/linux7/patches/0004-lmi-ov13b10-of-match.patch`
   to the tree that builds the Linux 7 kernel, the community tree, and rebuild
   the kernel and its device tree with the camera symbols of
   `kernel/experimental/linux7/configs/camera.fragment`;
2. install the kernel and the device tree as the permanent `system5` entry,
   keeping the Mobian 4.19 entry as the fallback;
3. boot and check that the sensor binds: `/sys/bus/i2c/devices/21-0010/driver`
   must exist, a `/dev/v4l-subdev*` node must appear, and the boot log must
   carry the sensor identification;
4. start `native-pipewire-v4l2-source /dev/video0` as the session user and
   check that the provider enumerates one camera;
5. only then wire the producer into the launcher.

The 4.19 fallback entry keeps a validated rear camera throughout, so this
sequence can be run without losing a working camera.
