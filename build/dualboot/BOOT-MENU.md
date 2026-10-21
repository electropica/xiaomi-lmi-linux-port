# Requested autonomous handset menu — October 21, 2026

The operator wants Android/Mobian selection on the handset, with a 15-second
timeout and **Mobian as default**. The prior Android-default proposal is
superseded. boot-menu-policy.json records requirements only; no current boot
component reads it. Do not report the policy file as a working menu.

The dedicated Mobian first boot is already qualified independently of a menu.
The current active kernel exposes `# CONFIG_KEXEC is not set` in /proc/config.gz;
a kexec menu cannot simply be enabled by configuration in this installation.
Changing boot initialization before the Android power-reference capture can also
confound that comparison. Keep direct-image boots as the initial reference.

Two primary-source leads were reviewed, not installed:

- [k30pro-linux-dualboot](https://github.com/chenpp1999/k30pro-linux-dualboot)
  documents an Android-first layout with Linux in recovery and one-shot BCB
  switching on this model. It is not evidence of our requested normal-power-on
  timed menu. Its README does not qualify overwriting our retained recovery.
- [EDK2-MSM](https://github.com/edk2-porting/edk2-msm) contains a specific
  [lmi device configuration](https://github.com/edk2-porting/edk2-msm/blob/master/configs/devices/lmi.conf)
  and lmi memory-map implementation. The project describes multi-boot support,
  but presence of a target is not proof that our two downstream boot images,
  display/input and firmware handoff work. Its lmi wrapper declares boot-header
  version 1 and Android 11; ours use header 2 and Android 16 userspace.
  The [published SimpleInit example](https://github.com/edk2-porting/renegade-project.org/blob/master/en/multiboot.md)
  demonstrates Android image and Linux entries on SDM845/Polaris, not lmi.

Next qualification must establish an lmi payload built from pinned sources,
compatible display/buttons, loading both exact boot images without rewriting
boot per selection, device-tree/command-line handoff, timeout semantics and
an independent rescue path. A temporary Fastboot test precedes any persistent
installation. No ABL/XBL write, recovery replacement, firmware download/boot,
kexec kernel build or persistent menu installation has been performed.
