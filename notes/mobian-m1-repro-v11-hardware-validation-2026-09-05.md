# Mobian M1 REPRO v11 hardware validation — 2026-09-05

**AUTOMATIC QUALCOMM PDR/ADSP/NGD/BTFM STARTUP VALIDATED ON FRESH HARDWARE**

Target: POCO F2 Pro / Redmi K30 Pro (`lmi`) with downstream D-v43.

M1 REPRO v11 userdata was freshly flashed and booted with the reference
D-v43 RAM boot image. Phosh reached the lock screen and was unlocked before
the read-only collection. No manual operation was performed on pd-mapper,
ADSP, NGD, SLIM, BTFM, rfkill or Bluetooth.

## Regression result

- boot and unlock: PASS;
- Phosh: PASS;
- French Squeekboard layout: PASS;
- Wi-Fi: PASS;
- general stability: PASS.

`getty@tty1.service` remained the sole known failed unit. It is non-blocking
and expected with D-v43 `CONFIG_VT=n`.

## Diagnostic SSH key

The recipe-provided public `codex-lmi` key authenticated root successfully.
It appeared exactly once in `/root/.ssh/authorized_keys`.

```text
/root/.ssh                 0700 root:root
/root/.ssh/authorized_keys 0600 root:root
```

Only the public key is tracked and installed by this integration. No private
key is included in the recipe or installed by it.

## Automatic unit results

`lmi-adsp-firmware-prepare.service` completed successfully:

```text
LMI_ADSP_FIRMWARE_PREPARE_PASS
Result=success
ExecMainStatus=0
```

The firmware loader path was `/lib/firmware/postmarketos`. `adsp.mdt` and its
stock segments resolved to the read-only firmware partition.

`lmi-pd-mapper.service` remained active/running with PID 3066. Its private
mount namespace exposed `/vendor/firmware_mnt/image/adspua.jsn`; the backing
`/dev/sde51` mount was read-only. Its bounded readiness check reported:

```text
LMI_PD_MAPPER_LOCATOR_PASS service=64 version=1 instance=1 domain=msm/adsp/audio_pd notifier=74
```

`lmi-adsp-btfm.service` completed successfully:

```text
LMI_ADSP_BTFM_PASS adsp=ONLINE notifier=66/1/74 slim=769/1/0 driver=btfmslim-driver
Result=success
ExecMainStatus=0
```

## Automatic chronology

```text
19.959 s  lmi-adsp-firmware-prepare.service starting
20.023 s  LMI_ADSP_FIRMWARE_PREPARE_PASS
20.089 s  lmi-pd-mapper.service starting
20.144 s  Service Registry Locator connected and initialized
20.144 s  msm/adsp/audio_pd PDR notifier registered
20.486 s  LMI_PD_MAPPER_LOCATOR_PASS
20.492 s  lmi-adsp-btfm.service starting
20.560 s  ADSP firmware loading
20.688 s  ADSP brought out of reset
20.712 s  ADSP power/clock ready
20.717 s  notifier instance 74 connected
20.748 s  msm/adsp/audio_pd reported UP
20.786 s  LMI_ADSP_BTFM_PASS
```

## ADSP, QRTR and NGD

ADSP state after automatic startup:

```text
state=ONLINE
crash_count=0
```

The per-boot no-clobber marker existed, while each distinct firmware loading,
reset-release and power/clock-ready message occurred exactly once. This proves
one automatic ADSP attempt on the collected boot.

QRTR exposed:

```text
64/1/1   Service Registry Locator
66/1/74  Service Registry notification for audio_pd
769/1/0  SLIMbus control service
```

NGD accumulated 328 ms of runtime-active time, proving effective progression,
then returned to `suspended` with no active audio stream. The slave-notification
thread was observed beyond its former `slave_notify` wait.

## SLIM/BTFM result

SLIMbus automatically created:

```text
btfmslim_slave
btfmslim_slave_ifd
```

The first device reported `OF_NAME=qca6390`, compatible
`qcom,btfmslim_slave`, and was bound to `btfmslim-driver`.

`/sys/class/bluetooth` remained empty and no `hci0` existed. HCI creation is
therefore the next distinct diagnostic layer; it is not part of this PASS.

An intermittent boot-time USB/RNDIS issue remains relevant: SSH may require a
physical cable disconnect/reconnect. It did not prevent this collection and no
cause or fix is claimed here.
