# Megapixels downstream camera blocker — 2026-09-27

## Immediate application failure

The installed package is Megapixels `1.8.3-1`. Its desktop entry invokes
`megapixels` without arguments. On Xiaomi `lmi`, the recorded launch reports
that it cannot find a configuration and specifically looks for
`/usr/share/megapixels/config/qcom,kona-mtp.ini`; that file is absent. No
coredump was found, and the available evidence does not demonstrate a device
permission or Wayland/DBus session problem. The missing configuration is the
first visible userspace blocker, before a usable camera pipeline is selected.

## Established live topology

The live Device Tree contains six generic `qcom,cam-sensor` entries whose
request labels identify the roles `ULTRA`, `FRONT`, `WIDE`, `TELE`, `DEPTH`
and `MACRO`. The vendor camera directories contain module/tuning artifacts
whose names suggest OV13B10, S5K3T2, IMX686, OV08A10, GC02M1 and S5K5E9YX04
for those roles. These names are suggestive vendor metadata only: the
available evidence does not prove that each physical sensor was detected or
establish an individual mapping from a V4L2 node to a role/model.

The media enumeration showed 34 entities but zero media pads, and no standard
sensor-to-CSIPHY-to-CSID-to-ISP-to-capture graph. `/dev/video0` is
`cam-req-mgr`, `/dev/video1` is `cam_sync`, and `/dev/video32` and
`/dev/video33` are VIDC nodes, not demonstrated camera capture nodes. The six
candidate sensor subdevices are `/dev/v4l-subdev12` through
`/dev/v4l-subdev17`, all named `cam-sensor-driver` in sysfs.

On each candidate, read-only `VIDIOC_SUBDEV_QUERYCAP` returned `EINVAL`, as
did `VIDIOC_SUBDEV_ENUM_MBUS_CODE` for pad 0, active format, index 0. No media
bus format was exposed by these calls. `EINVAL` does not by itself prove a
physical sensor fault; it establishes that these standard queries did not
provide the capabilities or formats needed for a configuration.

## Why no INI is proposed

Megapixels configuration examples require a camera driver and media-driver,
capture/preview formats, dimensions and rates, and (for the Qualcomm example)
explicit media-link edges. The package has no `qcom,kona-mtp.ini` or lmi
configuration. Its Qualcomm example describes a different, standard
`qcom-camss` graph and cannot safely be transplanted to the downstream
`cam_req_mgr` topology observed here.

The exact sensor model per node, CCI address, lane count/map and link
frequency, supported media-bus and capture formats, and a usable capture node
remain unestablished. The local upstream `sm8250-xiaomi-lmi.dts` describes a
different OV13B10 endpoint and is not proven to be the source of the running
D-repro kernel/DTB. Therefore no speculative `qcom,kona-mtp.ini` was created.
The first visible failure is the missing config; the non-standard downstream
pipeline is the next structural blocker. The exact Megapixels compatible
fallback behavior also remains unproven because its matching source is not
available locally.

## Evidence and boundary

Read-only ioctl results and the method note were retained outside Git in the
private workstation directory
`/home/linuxagent/dv43-openrc-reconstruction/camera-diagnostic/megapixels-topology-20260927/`.
Their SHA-256 values are:

- `v4l2-readonly-ioctl-results.txt` —
  `5ab4e377cb6a1464de2c8d3beecd2a2f9f2440b42fddba39c99f5dcefc8fd0b8`
- `v4l2-readonly-method.md` —
  `b105c4e418484581a5ec282d36b24418c702a8bfae55f7e1e874b924d325178a`

The private path is provenance for the source workstation, not a repository
dependency. No DT dump, full journal, device identifier, binary or image is
included here. No camera configuration or kernel change is proposed. A
provenance-matched camera description and a usable media/capture topology are
needed before an INI can be authored safely.
