# Fuel-gauge mode and memory-release follow-up — October 21, 2026

No calibration, PBS request or gauge data write was performed. The connected
observations below add no demonstrated battery-saving fix.

## Previously inaccessible rapid-SOC proposal retrieved

The actual [MiCode PR 41136](https://github.com/MiCode/Xiaomi_Kernel_OpenSource/pull/41136)
was retrieved through GitHub's public API. It is an open, unmerged proposal
against elish-r-oss, not a validated lmi patch. It adds recovery from rapid SOC
decrease when filtered voltage exceeds 3700 mV. The local downstream driver
contains the corresponding function without this recovery addition.

The running lmi DT enables both soc-scale-mode-en and rapid-soc-dec-en, with
3600 mV scaling and 3400 mV cutoff thresholds. Cached scale_mode_en was zero.
That boolean is not the private rapid-mode flag. Instead, two narrowly scoped
SRAM reads checked the actual rapid-mode parameters:

| Parameter | Observed encoding | Normal encoding from retained source | Rapid-mode encoding |
|---|---:|---:|---:|
| Cutoff current, word 19 | 409 (0x0199) | 200 mA encodes as 409 | 15999 mA encodes as 32766 (0x7ffe) |
| Slope limit, word 32 | 47 (0x2f) | 5738 encodes as 47 | 31128 encodes as 255 (0xff) |

The connected snapshot matches the normal configuration, not the rapid
configuration. This does not justify applying the proposal as a fix for the
current residual. It does not prove that rapid mode never occurred previously.
Address/count reader selectors were restored and verified; SRAM data was only
read. The proposal concerns SOC recovery, not a measured electrical load.

## Memory-request release is observed

Three connected snapshots read the two request registers after the earlier
SRAM access. MEM_ARB_REQ at 0x4340 bit 0 and MEM_ACCESS_REQ at 0x4350 bit 7 were
clear in all three; IACS select bit 5 was also clear. Register values were
0x02 and 0x00 respectively. This is stronger than absence of error messages
for these instants, but is not a measurement of every suspend-time state.

IMA configuration 0x4352 was 0x90, with the bit named STATIC_CLK_EN set in the
retained header. That name alone does not establish excess power or justify
clearing it. The reviewed [Qualcomm memory-interface source](https://android.googlesource.com/kernel/msm/+/60e67638d95e7fd48f602b15729ea13c13c478d5/drivers/power/supply/qcom/fg-memif.c)
has a clear-sequence path which sets this bit and subsequently clears only the
separate IACS-clear bit. Its applicable hardware clock-gating semantics and
full-Android state have not been established. No bit was toggled.

## One future full-Android capture, not another Mobian trial

The [snapshot helper](../../tools/android-power-init-snapshot.sh) prepares the
missing runtime comparison: selected CP calibration properties, cached BMS
calibration/mode, charge-pump topology, the same configuration registers, and
the two SOC parameters. It rejects non-lmi, non-root, recovery, incomplete
Android startup and kernels outside downstream 4.19. Missing interfaces are
reported without mounting debugfs or launching a vendor daemon. Hardware data
files are only read; temporary address/count reader selectors are restored.
No calibration, charging, service, firmware or partition setting is changed.

The helper has passed POSIX shell syntax validation on the host. It has NOT
been executed on Android, and its target behavior is not declared validated.
Its presence does not authorize reinstalling Android. Only after a separately
agreed full-Android boot and authorized root ADB setup, manual Windows commands
would be:

```powershell
adb push android-power-init-snapshot.sh /data/local/tmp/android-power-init-snapshot.sh
adb shell sh /data/local/tmp/android-power-init-snapshot.sh > android-power-init-private.txt
```

Keep that output private. Script SHA-256: `d53bfa8eef66a82099f154dd568ce1fd65a137c4bd67d5bd27f7a1ca81c39afe`.
Current evidence does not support a new calibration write, kernel build or
identical unplugged trial. The prior conditional hvdcp caller and the missing
full-Android runtime evidence remain documented in the October 19 follow-up.
