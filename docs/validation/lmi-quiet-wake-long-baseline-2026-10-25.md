# Sustained quiet gauge wakes — 25 October 2026

A passive run on the accepted IRQ-name Phosh/GSD policy and drawerpreview1
configuration lasted 81.775 minutes unplugged. The intended one-hour slot
ended when the operator returned; no forced end wake was added. Deep sleep
totalled65.192minutes (79.72% including the normal initial inactivity wait).

Five further natural msoc-delta wakeups returned to suspend preparation in
14.887–14.987seconds. Four kernel exit-to-next-deep intervals retained in the
bounded journal were15.727–15.956seconds; the first is unavailable there.
This extends the morning's two accepted cycles to seven. No WakeUpScreen
signal occurred during the five new natural gaps; ScreenSaver.GetActive
remained true. This is not a physical panel-power reading.

Same boot/profile, clean20-row capture closure and inactive/success observer
were checked. No RTC alarm or NPU recovery remained; historical reference log
unchanged. The final USB-triggered counter bracket is excluded.

The displayed gauge changed100% to95%, including the initial roughly15minutes
awake. Five qualified raw-counter brackets had a median24.676663 reported
units per suspended second. These are not calibrated electrical current,
capacity loss or projected full battery life. ADC readings are endpoints,
software-counter continuity is not established, and raw/shadow are not
independent electrical references.

The prior ~1201-second awake dwell did not recur. The wake-return defect is
now validated across seven natural cycles; residual standby draw and absolute
autonomy remain open. No per-peripheral cause is established by this run.

Public selected proof:
userspace/power/irq-name-candidate/long-resume-validation-20261025.json.
Raw logs remain private. No package/kernel/profile change or new observer
was launched on return. The completed one-shot reminder was deleted.
