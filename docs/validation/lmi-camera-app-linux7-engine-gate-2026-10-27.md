# Camera application on the permanent Linux 7 boot — engine gate and explained refusal

Date: 2026-10-27
Canonical repository: `/home/linuxagent/xiaomi-lmi-linux-port`, branch `lmi-linux7`,
HEAD `d2d0897`.
Handset: POCO F2 Pro / Xiaomi lmi, permanent `system5` boot, kernel
`7.2.12-lmi-community-port1-dirty`, Debian 13 (trixie) userspace, Phosh session
running as `mobian` (uid 1000), booted 2026-10-27 17:14.

Scope: diagnosis of the reported dead camera application, one launcher fix, one
privileged-service guard, off-handset guard tests, and on-device validation of
the fixed launcher. No partition was written, no bootloader entry was changed,
no proprietary blob was copied into the repository, and no commit was made.

## 1. Symptom

Starting the "Camera" application of the app grid did nothing. The launcher
raised an `AssertionError` and exited before any window was mapped.

Reproduced on the handset, as the session user, with the session environment:

```
$ /usr/local/bin/lmi-snapshot
Traceback (most recent call last):
  File "/usr/local/bin/lmi-snapshot", line 97, in <module>
    if __name__=='__main__':main()
  File "/usr/local/bin/lmi-snapshot", line 18, in main
    assert os.uname().release=='4.19.325-cip128-st12-perf-ga5b3099017ae-dirty'
AssertionError
```

The second "Camera" entry, the stock `gnome-snapshot` 48.0.1 package
(`Exec=snapshot`), starts normally but has nothing to show: the GStreamer
PipeWire device provider enumerates **0** devices, so the viewfinder stays
empty and no capture is possible.

```
provider factory: <GstPipeWireDeviceProvider>
device count: 0
```

Both entries share the desktop file id `org.gnome.Snapshot.desktop`, and
`/usr/local/share` precedes `/usr/share` in `XDG_DATA_DIRS`, so the app grid
shows the bundle launcher, not the stock package. The dead application is
therefore the bundle launcher.

## 2. Cause

The launcher pinned the kernel by string. The permanent boot now runs
`7.2.12-lmi-community-port1-dirty`, so the assertion fails on every start.

The assertion was not decorative: it marked the exact combination on which the
rear capture engine was qualified. The engine is the OEM HAL — `camera.qcom.so`
and its sensor modules — mounted from the handset vendor partition, driven by
the Xiaomi camera techpack in the kernel. On the 4.19 kernel that combination
was validated and produced rear preview frames; on Linux 7.2.12 none of it
exists.

The behaviour was therefore wrong in two ways at once: the launcher died
silently instead of reporting the reason, and the reason was never visible to
the operator.

## 3. Why no image is possible on this kernel

Each line below was read on the handset on 2026-10-27.

| Check | Result |
|---|---|
| Vendor tree | `/mnt/android-vendor` is **empty**: no `lib64/camera`, no `lib64/hw/camera.qcom.so` |
| Camera HAL blob on the device | none (`find / -xdev` over `camera.qcom.so`, `libcamera*.so`, `com.qti.sensor*` → no hit) |
| Camera firmware | `/mnt/vendor/firmware_mnt` is mounted read-only but holds no `qcom/camera` |
| Kernel camera techpack | `/proc/config.gz` has `CONFIG_VIDEO_QCOM_CAMSS=y`, `CONFIG_VIDEO_QCOM_IRIS=m`, `CONFIG_VIDEO_QCOM_VENUS=y` and **no** `CONFIG_TECHPACK_CAMERA_XIAOMI` |
| Rear sensor binding | the `ov13b10` driver registers (`ov13b10_i2c_driver_init`) but the device tree node `soc@0/cci@ac4f000/i2c-bus@1/camera@10` is **not bound**: `/sys/bus/i2c/devices/21-0010/driver` does not exist |
| V4L2 nodes | only the 14 `msm_vfe*_video*` ISP outputs of `qcom-camss`; no sensor node, no `/dev/v4l-subdev*` |
| OEM preview history | the preview unit ran on 2026-10-26 with 317, 243, 559 and 184 published frames — that is the 4.19 kernel, before the Linux 7 boot |

The sensor node is nearly complete. It carries `compatible = "ovti,ov13b10"`,
`reg = <0x10>`, two clocks, `reset-gpios`, three supplies and a `port` with an
endpoint that declares four `data-lanes`, `link-frequencies` and a
`remote-endpoint`. What it does **not** carry is `clock-names`, which the
mainline driver needs to resolve `in_clk` and `xclk`; that is the immediate
reason the probe does not bind. This is the first concrete dependency of the
next stage, not a fixed defect.

Two further observations, recorded to keep the record complete:

- PipeWire's libcamera SPA plugin is not installed on this system
  (`wp-device: SPA handle 'api.libcamera.enum.manager' could not be loaded`).
  It is not a blocker for the bundle, which publishes its own PipeWire node,
  but it would be a blocker for any libcamera-based source.
- Screen capture is unavailable in this session: both `grim` and the Phosh
  screenshot API fail with `failed to copy output DSI-1` on the pixman/DSI
  output. No screenshot claim is made anywhere in this record.

## 4. The fix

Two files changed. The validated 4.19 path is untouched.

### `userspace/camera/snapshot-bundle/lmi-snapshot`

The hard assertion became an explicit gate:

```
ENGINE_KERNEL='4.19.325-cip128-st12-perf-ga5b3099017ae-dirty'
ENGINE_VENDOR=Path('/mnt/android-vendor/lib64/hw/camera.qcom.so')

def engine_state():
    """Report the capture engine availability. Never raises."""
    release=os.uname().release
    if release!=ENGINE_KERNEL:return False,release,'kernel'
    if not ENGINE_VENDOR.is_file():return False,release,'vendor'
    return True,release,'none'
```

The qualified kernel string is kept as the gate, so the launcher still refuses
any combination that was never validated. The vendor blob is checked as a
second, independent condition, so a missing vendor tree is reported as such
instead of being mistaken for a kernel problem.

When the engine is unavailable the launcher now opens a GTK 4 window that
states the reason and names the running kernel, logs one machine-readable
line, and exits 0:

```
LMI_CAMERA_ENGINE_UNAVAILABLE Le moteur photo (HAL OEM) n'est validé que sur le
noyau Mobian 4.19. Noyau actif : 7.2.12-lmi-community-port1-dirty ...
```

The message points at the fallback boot entry, which the installed `system5`
menu keeps next to the Linux 7 entry. The `uid`/`argc` guard was changed the
same way: it now refuses with `LMI_CAMERA_LAUNCHER_REFUSED` and exit 1 instead
of a traceback.

The only other behavioural change on the supported path is the exit status: the
launcher now ends with `sys.exit(main())`, and `main()` returns `None` on the
normal path, so the exit code stays 0.

### `userspace/camera/files/lmi-camera-preview-service.py`

The privileged publisher keeps the same protection, with a legible reason
instead of a traceback:

```
if os.uname().release!='4.19.325-cip128-st12-perf-ga5b3099017ae-dirty':
    print('LMI_CAMERA_PREVIEW_UNSUPPORTED_KERNEL '+os.uname().release,flush=True)
    raise SystemExit(1)
```

The launcher already gates the unit; this refusal keeps the guarantee when the
unit is started directly.

`build-bundle.py` copies the launcher verbatim and rewrites two strings in the
publisher, so the bundle picks up both changes without a new build rule.

## 5. Validation

### Guard tests, off handset

`work/camera-fix/test_engine_gate.py` extracts `engine_state`, `notice_body`
and `show_notice` from the patched launcher with `ast`, executes them in a
controlled namespace and drives every case. No device, no camera, no service.

```
15/15 cases pass
```

The cases cover: the patched file parses; no `assert os.uname().release`
remains; the qualified kernel string is still present; the original file did
assert (baseline); Linux 7 is refused with reason `kernel`; the qualified
kernel without the vendor blob is refused with reason `vendor`; the qualified
kernel with the vendor blob is accepted; the notice names the running kernel
and mentions 4.19; the vendor notice mentions the vendor partition; and
`show_notice` returns 0 and logs both `LMI_CAMERA_ENGINE_UNAVAILABLE` and
`LMI_CAMERA_NOTICE_WITHOUT_GTK` when GTK cannot be loaded.

### On the handset

Deployed on the running system, with backups in
`/root/lmi-camera-backup-20261027/`:

| File | SHA256 |
|---|---|
| `/usr/local/bin/lmi-snapshot` | `b926b3f3521b75046bd26b07b8616815d6079d573cb8367dd4869ab94252c225` |
| `/usr/local/lib/lmi-camera/preview-service.py` | `0401d126168961c7ec55c704c451ab24165cc91e2bb59d2f2c4aa1360aca33a5` |
| backup of the previous launcher | `902b5b704e4981a62069c515f5065bf0b39fcf0b663fa6878272d5d8bfa249bf` |
| backup of the previous publisher | `aa3e80d8d703bc708ad71c6f87e53bc5f47ed237f7dbe84eab6113b280209b44` |

The deployed publisher was compared against the installed one before
installation: the difference is the guard hunk and nothing else, and the two
bundle rewrites (`lmi-snapshot` lease path and command line) were reproduced
exactly as `build-bundle.py` applies them.

Behaviour after the fix, started as `mobian` in the live session:

```
LMI_CAMERA_ENGINE_UNAVAILABLE Le moteur photo (HAL OEM) n'est validé que sur le
noyau Mobian 4.19. Noyau actif : 7.2.12-lmi-community-port1-dirty ...
```

- no `AssertionError`, no traceback;
- the process stays alive with the GTK 4 notice window mapped
  (`libgtk-4.so.1.1800.6`, Wayland connection, state `S`);
- no camera process is started and `lmi-camera-preview.service` stays
  `inactive`: the refusal happens before any capture path;
- the stock `gnome-snapshot` entry is unaffected.

The previous behaviour was a dead application, so this is the first state in
which the camera application says anything at all on this kernel.

## 6. What this fix does not do

It does not produce an image. On the Linux 7.2.12 boot there is no frame
source: the OEM HAL and its vendor blobs are absent, the kernel has no
Xiaomi camera techpack, and the rear sensor does not bind. The application now
reports that instead of failing silently; it does not pretend to capture.

The rear camera remains a validated feature **only** on the Mobian 4.19 entry,
which the installed boot menu keeps as its fallback. The journal of
2026-10-26 (184 to 559 published frames per run) belongs to that entry.

## 7. Next dependency

The shortest path to a real camera on this kernel is bounded and has a first
concrete step:

1. add `clock-names = "in_clk", "xclk";` to the rear sensor node
   `soc@0/cci@ac4f000/i2c-bus@1/camera@10` in the community device tree, so the
   `ov13b10` driver can bind;
2. confirm that the sensor binds and that the CSI-2 endpoint reaches the
   `camss` receiver and the VFE ISP of this board;
3. publish the V4L2 frames on PipeWire, so the GStreamer device provider
   reports one camera and the application gains a viewfinder.

Steps 1 and 2 are kernel and device-tree work on the community port, which the
project carries as patches under `kernel/experimental/linux7/patches/`. Step 3
is userspace work with the same shape as the existing `native-pipewire-source`
producer. Until step 1 is built and booted, the camera application on the
Linux 7 entry will keep reporting the missing engine, which is the intended
behaviour.
