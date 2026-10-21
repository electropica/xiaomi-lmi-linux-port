# Requested handset menu: current implementation boundary

The operator requests Android/Mobian selection with Mobian default after 15
seconds. Both OSes now boot on the dedicated layout and the PC-controlled
RAM-boot round trip is validated. That does not install a handset boot menu.

The dedicated [boot-menu recipe](../boot-menu/README.md) pins the lmi EDK2 and
SimpleInit sources and provides an operator-run isolated build. Its first stage
is a temporary display/input/countdown probe that returns to the already
installed Mobian boot. It is not a persistent dual-OS selector and must not be
flashed. No UEFI build or handset probe has yet been executed.

Source review found that the pinned SimpleInit aboot parser does not process
the v2 DTB field of our actual images. The recipe therefore includes a guarded
offline component extractor and documents the remaining RAM-asset and explicit
DTB/DTBO handoff work. It does not pretend that merely adding two abootimg paths
makes our downstream OS images bootable.

Current Mobian has CONFIG_KEXEC unset. Existing recovery, ABL, XBL, GPT and the
installed boot were not modified by this recipe preparation. The earlier
Android-default installation proposal is superseded; user policy is Mobian.
