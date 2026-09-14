# Mobian M1 Bluetooth SLIM/PDR runtime validation — 2026-09-05

**PDMAPPER -> PDR -> ADSP -> NGD -> BTFM SLIM VALIDATED AT RUNTIME**

Target: POCO F2 Pro / Redmi K30 Pro (`lmi`), downstream D-v43, M1 REPRO v9
userdata.

This note records an authorized runtime experiment. It does not claim that the
mechanism is present in a reproducible image, and it does not validate a
Bluetooth HCI controller.

## Initial failure

The kernel and DT already provided:

- `CONFIG_BTFM_SLIM=y`, `CONFIG_BT_SLIM_QCA6390=y` and MSM NGD SLIMbus;
- `3ac0000.slim` bound to `ngd_msm_ctrl`;
- the `qcom,btfmslim_slave` QCA6390 DT child and its elemental addresses;
- a registered `btfmslim-driver`;
- NGD receive and slave-notification threads.

Nevertheless, NGD had zero runtime-active time, `/sys/bus/slimbus/devices`
contained only `sb-1`, and `/sys/class/bluetooth` was empty. Booting the ADSP
without pd-mapper made QRTR service `769/1/0` visible but did not enumerate a
slave.

The confirmed missing prerequisite was Service Registry Locator `64/1/1`.
NGD calls `get_service_location("appsngd1", "avs/audio")` so that it can
register for the audio process-domain notifier. D-v43's service-locator code
uses `LOCATOR_SERVICE_TIMEOUT=3000000` milliseconds. With no locator service,
the request timed out only after 3000 seconds and the subsequent SSR fallback
was too late to drive the normal domain-up sequence.

## Stock inputs and bounded setup

The experiment used the Android stock components already present on the
device:

- `/mnt/android-vendor/bin/pd-mapper`;
- `/mnt/android-vendor/lib64/libpdmapper.so` and existing Android libraries;
- `/mnt/vendor/firmware_mnt/image/adspr.jsn`;
- `/mnt/vendor/firmware_mnt/image/adspua.jsn`.

`adspua.jsn` maps provider `avs`, service `audio`, to domain `adsp`, subdomain
`audio_pd`, QMI instance 74. A transient systemd unit gave pd-mapper a private
read-only bind of the stock firmware partition at the Android path resolved as
`/mnt/android-vendor/firmware_mnt` (`/vendor` is a symlink). Mountinfo and an
in-namespace read verified `ro` and access to `adspua.jsn`. No proprietary
file was changed, copied into the repository, or made writable.

The initial guard incorrectly looked for the unresolved mount target
`/vendor/firmware_mnt`; it stopped safely before ADSP boot. Read-only review
showed that systemd had canonicalized the destination through `/vendor` and
that the resulting mount was correctly read-only. The existing pd-mapper was
then retained and the corrected guards were revalidated before continuing.

## Pre-ADSP result

The stock pd-mapper remained active and published:

```text
64 1 1 node 1 port 16957  Service registry locator service
```

The kernel reported:

```text
Connection established with the Service locator
Service locator initialized
PDR notifier for adsp registered for msm/adsp/audio_pd
msm/adsp/audio_pd ... PDR service for adsp is uninitialized
```

`uninitialized` was expected while the ADSP was still offline. Before the
single boot request, the ADSP had `crash_count=0`, no earlier boot marker, and
the locator and pd-mapper were still alive.

## Single ADSP boot and result

Exactly one authorized write was made to `/sys/kernel/boot_adsp/boot`. The
ADSP reached:

```text
state=ONLINE
crash_count=0
```

QRTR then exposed all three relevant services:

```text
64  1  1   Service registry locator service
66  1  74  Service registry notification service
769 1  0   SLIMbus control service
```

The notifier reported `msm/adsp/audio_pd` UP and acknowledged instance 74.
NGD runtime-active time changed from zero to 328 ms before returning to the
normal suspended state with no active audio stream. Its slave-notification
thread progressed beyond its previous wait.

SLIMbus created:

```text
btfmslim_slave
btfmslim_slave_ifd
```

`btfmslim_slave` exposed `OF_NAME=qca6390`, the
`qcom,btfmslim_slave` compatible, and binding to
`/sys/bus/slimbus/drivers/btfmslim-driver`.

## Scope and remaining work

The operator confirmed after the experiment:

- Phosh: PASS;
- touch: PASS;
- Wi-Fi: PASS;
- general stability: PASS;
- spontaneous Bluetooth UI change: none.

`/sys/class/bluetooth` remained empty. This is not a failure of the tested
PDR/SLIM milestone: HCI creation is the distinct next layer.

The current mechanism is not persistent. It uses a transient stock pd-mapper
and a private read-only bind, while ADSP startup was manually gated and
triggered once. The required next objective is:

> Integrate the required pd-mapper/PDR chain cleanly and reproducibly into the
> build, then validate it from a clean boot without manual intervention before
> continuing HCI diagnosis.

That integration must consume proprietary components from the read-only stock
partitions rather than adding them to Git. It must order the locator before a
single ADSP startup, retain failure guards, and avoid manual SLIM binding,
runtime-PM forcing, Bluetooth toggles, or BlueZ assumptions.

A separate boot observation remains open: USB/RNDIS and SSH may occasionally
require disconnecting and reconnecting the USB cable. This experiment neither
identified nor changed that behavior.
