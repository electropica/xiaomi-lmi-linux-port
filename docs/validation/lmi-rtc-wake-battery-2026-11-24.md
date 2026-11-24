# RTC wake and battery observations — 24 November 2026

## Temporary RTC driver

The active Linux 7.2.12 kernel had `CONFIG_RTC_DRV_PM8XXX=m`, a compatible
PM8150 RTC device-tree node, and no installed module or `/dev/rtc0`. A separately
built upstream 7.2.12 module had the matching release string and its undefined
symbol names were present among the live kernel exports. The exact source tree
and ABI of the handset kernel are not proven, so that check does not establish
full binary compatibility. The module was loaded temporarily; no kernel image
or module was installed persistently.

The original driver registered `rtc0` and a relative alarm successfully woke
the handset from s2idle. However, the raw RTC reported a 1975 date and, on
registration, the kernel set the system clock to that date. Network time later
restored the correct system time. The device tree did not provide a persistent
RTC-offset source. Never assume that loading this driver is read-only: probe
sets the RTC enable bit, and an alarm programs hardware.

An experimental module candidate adds an in-memory offset derived from the
current system time when no persistent offset and no permission to set the
hardware clock are available. With NTP synchronized before loading, the RTC
showed the correct date, and the observed wall-clock change at load was about
0.21 seconds rather than decades. The candidate does not intentionally write
the RTC time or persist the offset. A plausible system date is not proof of
correct time: do not autoload the candidate before a trusted system time is
available. The [experimental patch](../../kernel/experimental/linux7/patches/rtc-volatile-offset-experimental.patch)
is not wired into the normal image recipe.

## Handset validation

On battery, an alarm woke the candidate from a 90-second s2idle test. Three
subsequent 45-second cycles all completed, with three RTC interrupts and three
successful suspends. A longer test completed twelve 15-minute RTC wake cycles
between 18:11:49 and 21:12:34, with RTC IRQ count 6→18 and suspend success
count 8→20. No alarm remained after USB reconnection.

During those three hours, displayed battery level fell 66→54% and coherent raw
MSOC 169→137. Assuming 2,617 mAh and 255 raw intervals gives roughly 109 mA;
this is not direct current measurement and includes scheduled wake overhead.
The prior ordinary-sleep observation around 102 mA used different charge
levels, duration and conditions, so the difference does not isolate wake cost.

An earlier unattended sequence stopped after two successful wakes because a
new suspend request raced logind's completion of the previous resume; its
low-battery monitoring did not continue after the stop. A later version waits
before requesting suspend and retries only the specific transient refusal.
Three short cycles and the twelve-cycle observation succeeded. The waiting
branch above 85% and poweroff below 25% have passed simulation only and are
not hardware-qualified.

The loaded module has a nonzero kernel reference count; an attempt to unload
it returned `in use`. Reboot removed the first temporary candidate, but the
corrected module is not an installed or proven permanent solution. No flash,
full image rebuild, physical rail change or measured battery improvement is
claimed.

## Screen behavior on RTC wake

The operator confirmed that the screen really illuminates during the scheduled
wakes. The battery logger reported `screen_on=1` after each of the twelve RTC
resumes; Phoc logged DSI modesetting followed by `Turning off` about five to
six seconds later. These logs are not a measurement of panel luminance or energy.

The installed Phosh binary matches the `pulldownbubble1` package. Its retained
source invokes the ordinary screen wake on resume unless a narrowly scoped
quiet-gauge filter qualifies the wake. On the active boot the opt-in was not
found in the process environment, and the filter's `last_resume_reason` and
USB-online paths were absent. The existing gauge policy therefore cannot
qualify these RTC wakes. Timing and code are consistent with the observed screen
behavior, but the complete display/D-Bus path was not instrumented.

A future RTC-specific quiet policy must distinguish an intentionally owned
alarm from power-button, touch, USB and simultaneous wake activity, and must
fail open when that distinction is uncertain. Neither an RTC interrupt count
alone nor a shared wake-source counter proves exclusive cause. No screen policy
change has been installed, and no panel-related current saving is established.
