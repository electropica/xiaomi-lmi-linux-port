# Full Android initialization comparison — October 21, 2026

Following the dedicated-partition Mobian boot, the pinned official LineageOS
23.2 October 7 boot image was booted temporarily. The operator completed setup,
enabled USB debugging and rooted debugging. Native Windows ADB confirmed full
Android startup and uid 0. No boot partition was flashed.

The reviewed tools/android-power-init-snapshot.sh completed successfully while
USB was connected and the battery was charging (97%, 21.5 C). Host capture time
was 2026-10-21 14:13:35 UTC; Android's clock still reported October 7 and must
not be used to date this evidence. Running Android kernel:
4.19.325-cip131-st15-perf-g71b13e62f057, distinct from the Mobian kernel.

Observed runtime values:

| Item | Full Android result |
| --- | --- |
| bms/calibrate | -22 |
| bms/scale_mode_en | 0 |
| persist.vendor.cp.calib_force / disable / level | Empty |
| persist.vendor.hvdcp_opti.disallowed | 1 |
| hvdcp_opti process | Present |
| charge_pump_master / parallel / cp_slave supplies | Absent |
| DT soc-scale-mode-en / rapid-soc-dec-en | Present |
| DT force-calib-level | 130 |

The cached calibrate result and absent charge-pump/parallel interfaces are also
observed under Mobian. They therefore do not, by themselves, explain the drain
difference or justify forced calibration. A cached result does not establish
the history or accuracy of physical calibration. Process presence does not
establish that a conditional calibration path executed.

Register and SRAM comparisons remain unavailable. A separate read-only check
found no debugfs entry in /proc/filesystems, no debugfs mount and no
/sys/kernel/debug directory. SELinux remained enforcing. No mount, policy
change, calibration, hardware data write or daemon launch was attempted.
This is a plugged-in initialization snapshot, not a suspend-current comparison
and not evidence that all peripheral rails are off.

Snapshot source SHA256: d53bfa8eef66a82099f154dd568ce1fd65a137c4bd67d5bd27f7a1ca81c39afe
