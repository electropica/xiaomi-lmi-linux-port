# IRQ-number-dependent quiet resume defect — 25 October 2026

## Hardware observation, not yet a corrected-runtime milestone

The currently running Phosh and GSD filters are opted in and contain exact IRQ438 msoc-delta /441 msoc-high /445 esr-delta literals. Current kernel names instead use451/454/447 respectively. Both strict comparators therefore reject those events. Read-only settings show session idle300s plus battery suspend900s. The retained kernel journal contains18 msoc-delta wakes with inter-suspend awake gaps1201.000..1201.173s (median1201.076s), then a USB wake. These findings agree with a full idle cycle after the quiet path is missed. Historical screen state and the exact electrical contribution are not measured; no new counter observer was active overnight.

## Prepared candidate

`userspace/power/irq-name-candidate/` replaces fixed numbering with an exact single-event-name match after a numeric IRQ. Existing opt-in, discharge/capacity guards, USB and screen/activity/sleep guards remain. Multi-reason and unknown wakeups reject. Host tests execute the exact source functions (62 cases, ASan/UBSan), and scratch replay verifies pinned hashes. No package was compiled or installed at preparation time.

The existing Phosh source tree had unqualified drawerscroll4 changes. The operator builder reconstructs the qualified drawerscroll1 geometry and overview in scratch using three pinned reverse patches, verifies accepted hashes, and applies only the policy change. It guards four qualified rescue packages, checks unchanged package file/type/link lists and preserves Phoc's accepted private-FBO thumbnail renderer. Compilation remains operator-run; default invocation is a scratch preflight. No kernel, full image or phone installation is performed.

## Required next milestone

After an operator build, inspect the generated package manifest and normal test results; install only the four targeted packages with a bounded rescue path and protected graphical restart. Keep the temporary kernel/profile and accepted Phoc. Validate normal UI, explicit button/USB wake, and a naturally occurring detached gauge wake. The latter must keep the screen blank and restore suspend promptly before any autonomy improvement is claimed. Report actual awake intervals and qualified gauge units separately from electrical current.
