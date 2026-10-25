# IRQ-number-independent quiet resume candidate

Verified defect: running Phosh/GSD use fixed IRQ438/441/445 while this boot assigns451/454/447. This candidate matches the complete single event name following its numeric IRQ. Unknown, multiple and malformed reasons remain rejected. Existing opt-ins, USB, screen, sleep-cycle and guarded capacity/status checks are unchanged.

The source tree currently contains an unqualified drawerscroll4 UI. The builder first reconstructs and hashes the accepted drawerscroll1 UI in scratch by reversing three pinned patches. Only --execute writes the restored UI and new power-policy source into the existing build tree. No new rootfs/build directory is created. Rescue packages are pinned. The private-FBO Phoc thumbnail fix is untouched.

Default command runs preflight only:

    python3 userspace/power/irq-name-candidate/build-packages.py

Operator build, from WSL:

    sudo python3 /home/linuxagent/xiaomi-lmi-linux-port/userspace/power/irq-name-candidate/build-packages.py --execute

Both package suites run normally; tests are not disabled. Completion marker IRQ_NAME_PACKAGES_BUILT. Result manifest /home/linuxagent/phosh-gauge-wake-build/rootfs/build/lmi-irqnames1-build-result.json. No phone contact, installation, kernel or image build. Package file/type/link lists must match the qualified rescue packages.

Host validation:62 tests execute the actual identical qualification functions from both patched sources, with ASan/UBSan; patch replay verifies exact outputs. Real-world quiet wake and autonomy benefit remain unvalidated. Observed300+900 second settings agree with1201 second inter-suspend awake gaps, but do not measure electrical current or prove a sole cause.

## Incremental runtime activation — 25 October 2026

The IRQ-name-independent Phosh/GSD packages are installed and user-accepted for normal application use, drawer and power-button handling. Runtime process hashes and both opt-ins match the built artifacts; same temporary kernel boot and published j11 profile were retained, as was the accepted private-FBO Phoc renderer. The owned automatic rescue timer was cancelled after acceptance. Phosh package tests:36 OK; GSD:1 OK and9 SKIP.

The original fixed-IRQ mismatch is established; corrected natural gauge-resume behavior and battery benefit are still unvalidated. No full image or permanent boot was changed or promoted. See `userspace/power/irq-name-candidate/device-activation-20261025.json` and `docs/validation/lmi-irq-name-policy-2026-10-25.md`.

## Natural gauge-resume validation —25 October 2026

Two detached msoc-delta resumes with the IRQ-name policy returned to suspend after14.862s and15.010s between D-Bus events; kernel suspend-exit to next deep-entry intervals were15.673s and15.792s. The preceding uncorrected-night median was1201.076s. No WakeUpScreen signal occurred during these two natural cycles and ScreenSaver.GetActive stayed true. This is not a direct panel-power measurement. Same boot/profile, clean capture closure and active Phosh/GSD with zero restarts were confirmed; the collector finished successfully.

The return-to-sleep defect is hardware-validated for these two cycles. A final USB-triggered resume is excluded. Two separate raw-counter brackets give25.201 and24.614 reported units per suspended second (awake callback margin included in the numerator); these are not calibrated current. Current charge_full2637000 differs from the historical2677000. Historical comparison and autonomy/sole-cause conclusions remain limited. Full-image pins have not yet been promoted to these incremental runtime packages.

Evidence: userspace/power/irq-name-candidate/natural-resume-validation-20261025.json. No additional test, reboot or policy change was launched on return.
