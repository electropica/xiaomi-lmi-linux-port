# Mobian M1 SDX55 ESOC B1 validation — 2026-09-06

## Scope

This note records the ESOC late-run-state deadlock diagnosis, kernel B1 fix,
and nominal SDX55 boot validation through mission mode and `ESOC_BOOT_DONE`.
It does not claim that the exact crash race has been reproduced after applying
B1, nor that cellular registration, voice, SMS or data work.

## Historical failure and runtime proof

An SDX55 `ERR_FATAL` set `mdm_drv->mode=CRASH` and queued `ssr_work`, which
waited for `ssr_ready`. The modem later reached mission mode while the original
`mdm_subsys_powerup()` remained pending. A delayed `ESOC_BOOT_DONE` generated
`ESOC_RUN_STATE`; the old handler unconditionally changed the mode to `RUN`
before completing `pon_done` and `ssr_ready`.

The latent SSR then resumed through `mhi_control_error()` and
`subsystem_restart_dev(esoc0)`. Its forced shutdown received mode `RUN`, skipped
the crash teardown, and the following power-up waited again for `pon_done`.
DV166 captured exactly one blocked worker:

```text
PID=14769 TID=14769
COMM=kworker/u17:0+ssr_wq
STATE=D
WCHAN=mdm_subsys_powerup

mdm_subsys_powerup
subsystem_powerup
subsystem_restart_wq_func
process_one_work
worker_thread
kthread

MATCHING_SSR_WORKERS=1
```

This proves the historical deadlock. It does not by itself prove the result of
the same race after B1.

## B1 correction and rationale

B1 changes only the `ESOC_RUN_STATE` mode assignment:

```diff
 mdm_drv->pon_state = PON_SUCCESS;
-mdm_drv->mode = RUN,
+if (mdm_drv->mode != CRASH &&
+    mdm_drv->mode != PEER_CRASH)
+        mdm_drv->mode = RUN;
 complete(&mdm_drv->pon_done);
 complete(&mdm_drv->ssr_ready);
```

Preserving `CRASH` or `PEER_CRASH` retains the information required by the SSR
shutdown. `pon_state=PON_SUCCESS`, `complete(pon_done)` and
`complete(ssr_ready)` deliberately remain unchanged so the original power-up
and latent SSR can both proceed. DV167 and the adversarial DV168 review
concluded `B1_CONFIRMED_AS_IS` and `PATCH_READY_FOR_APPLICATION=YES`.

## Build and boot artifact

The operator-built kernel was:

```text
path=analysis/qca6390-v2-control-config-build-v2/arch/arm64/boot/Image
size=43235352
sha256=57f19e282b475f2635c97d39c29c1c990e6fff3c6af52265cc6d8ce3fac9dcfc
vmlinux=present
System.map=present
drivers/esoc/esoc-mdm-drv.o=present
```

It replaced only the kernel in the validated boot image base. The resulting
RAM-boot artifact was:

```text
name=D-repro-01-kernel-Dv43-qca6390-v2-complete-fcsource-esoc-b1-boot.img
size=52924416
sha256=5928523a7ca15a318c81bca17a3183db76a08a2e6d9d99a0ca43456e8f48f7ef
embedded_kernel_sha256=57f19e282b475f2635c97d39c29c1c990e6fff3c6af52265cc6d8ce3fac9dcfc
ramdisk_sha256=301e1222e3043353a46e4b904ca8cba37c19640634d01cbb56c94acbe0e5b5b9
dtb_sha256=212d80826ceef522aff2d967082b5708d20ddccc13ae322edce72412f1a06b51
HEADER_METADATA_MATCH=PASS
```

Windows `fastboot boot` reported both Sending and Booting `OKAY`; nothing was
flashed persistently. Mobian mounted rootfs and retained Phoc, Phosh, USB and
Wi-Fi without a patch-related panic, Oops or BUG.

## Initial OFFLINING state

DV178 established that the initially displayed `OFFLINING` state was not a
blocked worker. In this kernel `SUBSYS_OFFLINING` is enum value zero, while
`subsys_register()` allocates the tracking structure with `kzalloc()` and does
not explicitly initialize `track.state`. A registered but never-started ESOC
subsystem therefore appears as `OFFLINING`. With zero crashes, no holder and no
SSR worker, this is a misleading initial label rather than a B1 regression.

## Fresh B1 power-up and Sahara

DV179 registered the ESOC request engine and received `ESOC_REQ_IMG`. SDX55
enumerated as PCI `17cb:0306`, bound to MHI and exposed its BL and Sahara
devices with `crash_count=0`; no `mhi_control_error`, ERR_FATAL, unexpected
reset or SSR occurred.

For the controlled transfer, the validation-only `sdx55_ks_no_reset.arm64`
client had size 73128 and SHA256:

```text
73c37133df3898ef909347ca015e5f661dfb4eaceeddddf4a4143dc630db97c1
```

Its sole behavioral change makes `sahara_send_reset()` a no-op, preventing an
automatic Sahara RESET even on protocol error. It is not part of the kernel
commit. DV180 ran it exactly once with the complete 17-entry mapping, including
Xiaomi's `xbl_cfg.elf`, EFS1/2/3 and `mdmddr`:

```text
SAHARA_PROCESS_RC=0
SAHARA_CLIENT_EXECUTIONS=1
NO_RESET_CLIENT=YES
SAHARA_RUN_RC=0
SAHARA_SESSION_FINISHED=YES
```

No retry, reset, `ESOC_IMG_XFER_DONE` or `ESOC_BOOT_DONE` occurred during the
transfer. This also demonstrates that `ESOC_IMG_XFER_DONE` was not required for
the observed transition to mission mode.

## Mission mode and nominal BOOT_DONE

DV185 observed QMI0, QMI1, RMNET_CTL, DIAG, IP_HW0 and `rmnet_mhi0`. The kernel
reported an SSCTL connection between the QMI handle and esoc0; `crash_count`
remained zero.

DV186 then verified the pending helper, mission-mode devices and zero crash
count before sending exactly one nominal `ESOC_BOOT_DONE`. The notifier and
ioctl returned zero. Three seconds later:

```text
SUBSYS_OPENED=YES
MODEM_POWERUP_COMPLETED=YES
SUBSYS_STATE=ONLINE
CRASH_COUNT=0
```

The `mdm_subsys_powerup` thread had exited, mission mode remained present and
no new kernel error appeared. The validated nominal sequence is therefore:

```text
PWR_OFF
  -> first subsystem_get
  -> ESOC_REQ_IMG
  -> one Sahara transfer
  -> mission mode
  -> one ESOC_BOOT_DONE
  -> ESOC_RUN_STATE
  -> mode=RUN
  -> complete(pon_done)
  -> mdm_subsys_powerup returns
  -> subsystem ONLINE
```

## Validation boundary

Validated materially:

- B1 build, packaging, RAM boot and general boot safety;
- fresh SDX55 power-up through MHI BL/Sahara;
- one complete no-reset Sahara transfer;
- mission-mode MHI and SSCTL presence;
- nominal `ESOC_BOOT_DONE`, completed power-up and `ONLINE` state;
- zero crashes and no nominal-path regression during the experiment.

Validated by source/runtime diagnosis but not reproduced under B1:

- the historical deadlock cause;
- B1's preservation of `CRASH`/`PEER_CRASH` under a late run notification.

Still unvalidated:

- material reproduction of `CRASH -> late RUN_STATE -> SSR` under B1;
- cellular registration and usable modem service;
- voice, SMS and packet data.
