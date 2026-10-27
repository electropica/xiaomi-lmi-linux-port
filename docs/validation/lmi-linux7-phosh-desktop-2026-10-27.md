# Linux 7.2.12: first Phosh desktop and drawer hardware trial

The operator confirms that the Mobian desktop appeared during the 90-second
trial (not after returning to the permanent 4.19 OS), and that the drawer
worked. The strict journal identifies the accepted kernel703819e4/DTB306315e8
and diagnostic initramfs d3ec261b. Temporary menu SHA256:
`43dccd8f5e8543ed5bae17bcdd7129a24fafde8534ba4874efec66176fc41cd6`.

The 26,648-byte graphics log SHA256 is
`5e29281a6ec773d676680144c8aa2ceaa82fe4a5bb787c84192341f6f31ed50a`.
It confirms the dedicated Mobian rootfs mounted read-only with journal replay
disabled, touch udev classification, libseat builtin, Phoc MSM KMS and a pixman
renderer. The session stays up for the full 90-second limit and reports cleanup.
Phosh runs and the operator exercises its drawer. Earlier attempts stopping
before Phosh are historical failures, not the outcome of this third trial.

The figures above were re-checked directly against the retained graphics log
and journal before publication: the log records ID_INPUT=1 and
ID_INPUT_TOUCHSCREEN=1, Phoc on the builtin libseat with the MSM DRM backend on
/dev/dri/card0, WLR_RENDERER=pixman, GRAPHICS_WINDOW_END elapsed=90 and
TRIAL_FINISHED, and the journal carries the strict 703819e4/306315e8/d3ec261b
identity with no panic, BUG or internal error.

The relevant fix is scoped SYSTEMD_IN_CHROOT=0 for temporary udevadm commands.
The local Debian ARM64 dry-run and systemd v257 sources show that trigger and
settle otherwise skip a chroot request while returning success. RAM-only
device nodes and udev metadata remain separate from the installed OS.

Scope: real Mobian userspace compositor/shell under Linux7, using software
rendering, a read-only rootfs, empty RAM home, private session bus and no full
systemd/login session. This is not an accelerated GPU test, persistent OS boot,
normal application/service qualification, suspend or battery validation.
Portal, missing system-bus and application startup warnings occur. An app
startup timeout is not evidence that all installed applications work.

Julien requests Linux7 as the future default. It has NOT been installed or
made default: this diagnostic session still exits at 90 seconds and cannot
retain settings. First prepare an autonomous boot, keep recoverable 4.19 and
Lineage choices, and qualify that boot before changing the permanent policy.
The next investigation is GPU firmware/userspace compatibility, preserving
the working 4.19 KGSL stack. The operator returned to Mobian4.19 afterward.
