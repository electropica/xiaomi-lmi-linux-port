# Community Linux 7.1 RAM boot: display and USB milestone

The operator reported a white screen followed by console text. The retained
129,701-byte observer capture has SHA256
`ae822d8ebdcab772f3e263020aee0f8b4fbe434bcfcfe862727899994a2f9bfe`.
The strict receiver accepted Linux `7.1.0-lmi-ccc-ram1` and the pinned kernel,
DTB and initramfs markers. Menu SHA256:
`d96f21a0b80f129bc73b09d6b9eaa4d4ac9e99352f681a9a0a4aff53c8de6f11`.

The journal reports DSI binding at 3.425598 s, DRM MSM initialization at
3.588207 s and `fb0: msmdrmfb frame buffer device` at 3.808570 s. Observer
heartbeats continue through 304.74 s. This establishes actual MSM/DSI/DRM
takeover plus functioning USB journal transport, rather than only a
bootloader framebuffer. UFS enumeration also succeeds.

Scope: RAM-only diagnostic boot, no root filesystem mounted and no Mobian GUI
tested. Touch was intentionally disabled for this first community trial.
GPU acceleration, Wi-Fi, Bluetooth, audio, cameras and suspend/battery behavior
are not qualified. Missing firmware messages must not be reported as hardware
qualification. The existing Mobian/Lineage installation is unchanged.

Next target explicitly chosen by Julien: Linux 7.2.12 with the relevant
community adaptations, keeping this 7.1 boot and the 7.2 touch-release trial
as reference artifacts. No heavy build is started by the agent.

Outcome: that target was reached on the same day. The 7.2.12-lmi-community-port1
port of this tree reached DSI, DRM MSM and framebuffer console output with a
working USB journal transport; see
[the 7.2.12 record](lmi-linux7-community-port-display-2026-10-27.md). This 7.1
boot is kept as the reference artifact it was intended to be.
