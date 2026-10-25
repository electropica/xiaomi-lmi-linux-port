# IRQ-number-independent quiet resume candidate

Verified defect: running Phosh/GSD use fixed IRQ438/441/445 while this boot assigns451/454/447. This candidate matches the complete single event name following its numeric IRQ. Unknown, multiple and malformed reasons remain rejected. Existing opt-ins, USB, screen, sleep-cycle and guarded capacity/status checks are unchanged.

The source tree currently contains an unqualified drawerscroll4 UI. The builder first reconstructs and hashes the accepted drawerscroll1 UI in scratch by reversing three pinned patches. Only --execute writes the restored UI and new power-policy source into the existing build tree. No new rootfs/build directory is created. Rescue packages are pinned. The private-FBO Phoc thumbnail fix is untouched.

Default command runs preflight only:

    python3 userspace/power/irq-name-candidate/build-packages.py

Operator build, from WSL:

    sudo python3 /home/linuxagent/xiaomi-lmi-linux-port/userspace/power/irq-name-candidate/build-packages.py --execute

Both package suites run normally; tests are not disabled. Completion marker IRQ_NAME_PACKAGES_BUILT. Result manifest /home/linuxagent/phosh-gauge-wake-build/rootfs/build/lmi-irqnames1-build-result.json. No phone contact, installation, kernel or image build. Package file/type/link lists must match the qualified rescue packages.

Host validation:62 tests execute the actual identical qualification functions from both patched sources, with ASan/UBSan; patch replay verifies exact outputs. Real-world quiet wake and autonomy benefit remain unvalidated. Observed300+900 second settings agree with1201 second inter-suspend awake gaps, but do not measure electrical current or prove a sole cause.
