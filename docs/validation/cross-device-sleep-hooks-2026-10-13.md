# Cross-device Mobian and postmarketOS sleep-hook review

Read-only source review, 2026-10-13. Revision:
`7f53f93a1a51c0ad15b27d3939c318a32ed27b56` (official pmaports HEAD at lookup).
The postmarketOS sub-review involved no phone contact, installation, build or flash.

## Scope and concrete result

The full package file lists and available text sources were read for:

- `device/community/soc-qcom`
- `device/community/device-xiaomi-beryllium` (Poco F1 / SDM845)
- `device/community/device-oneplus-enchilada` (OnePlus 6 / SDM845)
- `device/testing/device-oneplus-instantnoodlep` (SM8250)
- `device/testing/device-qualcomm-sdm845`
- `device/downstream/device-xiaomi-monet`

No pre-suspend/post-resume script or system-sleep hook writing CPU, NPU,
memory-bandwidth or regulator controls was found in these packages.
This is a bounded package result, not an assertion about all postmarketOS
history or every upstream driver's PM callbacks.

`soc-qcom-sdm845` has been replaced by common `soc-qcom`; the APKBUILD declares
this replacement. Current lmi paths under testing, downstream and archived
returned 404. The private lmi port must not be confused with an official
upstream pmaports device package.

An additional complete filename sweep of current `device/downstream`
contained 258 tree/blob entries. No file named sleep/suspend/resume hook
was found. Three power-related matches were unrelated kernel patches for
AXP20x battery calibration and Samsung low-power charging.
Filename sweep alone does not prove no PM logic embedded in arbitrary files.

## Existing scripts/configuration that can be mistaken for sleep hooks

1. `soc-qcom/call_audio_idle_suspend_workaround.sh` is a call-state D-Bus
   listener, NOT a whole-system sleep hook. Call state 0 or 3 unloads
   PulseAudio module-suspend-on-idle (if PulseAudio is running), waits a
   second, and starts two PipeWire loopbacks. Call state 7 kills loopbacks
   and reloads the PulseAudio module. It keeps audio working during calls;
   copying it does not reduce residual deep-suspend current and can keep
   audio paths active. Compatibility requires ModemManager call signals,
   pactl/PulseAudio or pw-loopback. It is not a 4.19 CPU/NPU policy.

   https://gitlab.postmarketos.org/postmarketOS/pmaports/-/blob/7f53f93a1a51c0ad15b27d3939c318a32ed27b56/device/community/soc-qcom/call_audio_idle_suspend_workaround.sh

2. The base UI enables ModemManager `--test-quick-suspend-resume` in both
   systemd and OpenRC service configuration. This is real service suspend
   integration, not a reusable hardware sysfs hook or CPU throttle.

   https://gitlab.postmarketos.org/postmarketOS/pmaports/-/blob/7f53f93a1a51c0ad15b27d3939c318a32ed27b56/main/postmarketos-base-ui/rootfs-usr-lib-systemd-system-ModemManager.service.d-quick-suspend-resume.conf

3. `sleep-inhibitor.conf` enables SSH-session and APK-lock plugins with
   six-second polls. It prevents suspension while those operations run;
   it does not reduce current after suspension. This replaced an old
   elogind pre-sleep cancellation hook, because cancelling after
   PrepareForSleep had already disabled modems/radios caused failures.
   Debian uses different package locks; blindly copying APK policy is wrong.

   https://gitlab.postmarketos.org/postmarketOS/pmaports/-/blob/7f53f93a1a51c0ad15b27d3939c318a32ed27b56/main/postmarketos-base-ui/rootfs-etc-sleep-inhibitor.conf
   https://gitlab.com/postmarketOS/pmaports/-/merge_requests/1815

4. Elogind config permits interrupted suspend (`AllowSuspendInterrupts=yes`),
   delegates power-key handling to the UI, and leaves IdleAction commented.
   This is OpenRC/elogind policy, not a hardware current optimization to
   transplant into the present systemd Mobian setup.

   https://gitlab.postmarketos.org/postmarketOS/pmaports/-/blob/7f53f93a1a51c0ad15b27d3939c318a32ed27b56/main/postmarketos-base-ui/rootfs-etc-elogind-logind.conf

## Conclusion for lmi

No additional official Qualcomm pre/post sleep script was identified within
the explicitly searched packages. Existing NPU suspend restoration already
targets the demonstrated downstream vote defect. The source review does
not justify installing a generic CPU/governor hook, disabling idle audio,
or replacing deep suspend with s2idle. ModemManager quick resume can be
checked against installed service configuration, but cannot be declared
the cause of an already-suspended 50 mA gauge estimate from these sources.

## Secondary report, not a transplant candidate

Official pmaports issue 4846 reports high screen-off current on a near-mainline
Motorola Dubai, comparing it to downstream Droidian on a different device.
It suspects camera retention and links an SDM845 camera issue. These are
different devices and screen-off/idle methodology; the reported current
figures and unit labels do not establish a deep-suspend lmi cause.

https://gitlab.postmarketos.org/postmarketOS/pmaports/-/work_items/4846


## Mobian source-package follow-up

The official `qcom-support`, `oneplus6-support` and `pocof1-support` repositories
were followed through their package dependencies rather than treated as absent
support because their own trees contain only metapackage recipes.

`qcom-phone-utils` at `c58ea490cd098b9514eb422e2ac4fafe4c860d1b` contains boot-image,
initramfs and modem initialization helpers, not a pre/post system-suspend hook.
The older Poco F1 and OnePlus 6 `sdm845-setup` oneshots run before ModemManager;
their scripts provision a UIM/SIM session and open the QMI data port. They do not
reduce CPU, NPU or memory votes at suspend and must not be copied as a battery fix.

- [Poco F1 setup source](https://salsa.debian.org/Mobian-team/devices/pocof1-tweaks/-/blob/7da2dfe601ad8c1558a7eacd35645213ca6dc381/tweaks/sdm845-setup)
- [OnePlus 6 setup source](https://salsa.debian.org/Mobian-team/devices/oneplus6-tweaks/-/blob/32f3f4d73e8bd2316d47af8fd98cbccba5551828/tweaks/sdm845-setup)
- [Qualcomm utility package](https://salsa.debian.org/Mobian-team/packages/qcom-phone-utils/-/blob/c58ea490cd098b9514eb422e2ac4fafe4c860d1b/debian/control)
- [Mobian ModemManager quick-resume setting](https://salsa.debian.org/Mobian-team/tweaks-data/-/blob/cdcbedd0e330958b11c04a08e87817500a5700c0/mobile-tweaks/common/modemmanager/mobile-tweaks.conf)

This is a precisely scoped negative source result, not proof that no useful
historical or third-party sleep script exists. Source existence alone would not
qualify a script on this downstream 4.19 kernel.

## Distinguishing CPU and NPU request contexts on the current port

The preserved live device tree marks seven reviewed CPU devbw bandwidth/latency
clients active-only. The locked devbw driver passes that flag into the bus client;
the RPMh backend explicitly assigns zero sleep bandwidth/clock requests to
active-only clients. Thus their awake `performance` governors cannot simply be
equated to the demonstrated dual-context NPU defect. This is software routing
evidence, not independent electrical measurement of every shared rail.

A further NPU `latfloor` declaration was checked against current driver binding.
It is bound, but already uses `powersave` with minimum zero. The three previously
corrected clients remain distinct. No fourth maximum request or additional
standby-saving intervention was demonstrated. The GPU bandwidth client uses its
separate `bw_vbif` lifecycle; its declaration does not justify a blind governor
change. No CPU/NPU/GPU settings were changed in this review.

The next target qualification remains the guarded `msoc-high` userspace candidate
documented in [the overnight result](quiet-gauge-night-2026-10-13.md). No
additional physical test follows from the script search alone.
