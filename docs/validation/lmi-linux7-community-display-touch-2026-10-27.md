# Linux 7.2.12 community base: display plus touch release milestone

The operator ran the RAM-only combined display+touch menu
`bdd18157d0e9f3e9a83e53c2d10d5f1ee3e2d187947f23937dbb21b187bc36ed`.
The exact component markers confirm kernel
`703819e444e378d0de4a79523a7faed2066ada9d514dcabb249a96e1f11938d3`,
DTB `306315e8288ea13c4dc10c017eda3c75aefe4a3a189c906c6567ed6b75b602db`
and the unchanged diagnostic initramfs. Uname remains
`7.2.12-lmi-community-port1`; hashes distinguish this from the display-only trial.

The retained evdev capture SHA256 is
`f69fccea869532d7e01f73c081148e94ed5e9bf32432b043ba0808a1461399fd`.
It contains 3,131 events, 46 contact starts and 46 releases, 1,211 XY updates,
484 sync reports, no SYN_DROPPED, no active slots at the end and BTN_TOUCH=0.
The capture is complete and below the raw byte cap. Recorded event span:
12.081312 s; XY ranges: [227, 845] / [801, 1825].
The associated journal confirms successful GPI, I2C and touch probing and
MSM framebuffer initialization; no kernel-panic, BUG or RCU-stall marker occurs.

This combines the display-capable community port with the handset-validated
GPIO72 main supply, PM8150L LDO1 1.8 V IO, FT5452 power ordering and snapshot
release handling. It validates bounded raw touch/release sequences on the
combined base. It does not establish GUI usability, full ten-finger behavior,
coordinate calibration, GPU acceleration, suspend or battery consumption.
No installed Mobian or Lineage partition was changed. Raw captures stay private.

Next milestone: plan a guarded boot of userspace with this display/input base,
first reviewing rootfs/initramfs and compatible firmware dependencies; do not
assume that the 4.19 userspace hardware integration is interchangeable.
