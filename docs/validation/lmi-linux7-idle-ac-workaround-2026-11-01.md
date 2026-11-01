# Linux 7 idle suspend with stale USB power state

On 1 November 2026, a handset-local observer recorded input VBUS at zero while
the battery current was negative, but UPower reported `OnBattery=false` for
seven observations over one minute. UPower classified `tcpm-source-psy` as
online line power. This is a reported supply-state mismatch, not proof of the
exact TCPM/PMIC failure or of a charging hardware fault.

The Mobian user's AC idle action was changed from `nothing` to `suspend`, with
the existing 900-second timeout retained. Battery idle action was already
`suspend`. In the subsequent unplugged, unattended test, the system entered
s2idle about 13 minutes 37 seconds after unplug and remained suspended for
about 12 minutes 10 seconds until the post-sleep observation after reconnection;
the suspend-success counter increased from 2 to 3. No current integral or
deep hardware residency was established. The observed wake source was not
independently attributed.

The `lmi-current` userdata build profile now requests suspend after 900 seconds
on AC as well as battery. This is a **workaround**, not a correction to USB
power detection. It also permits idle suspension on real AC and applies to the
shared userdata, including when booted with the 4.19 fallback. Existing user
settings may override schema defaults. A full rebuilt image has not been
produced or tested with this default.

On the existing handset, revert the user's change by setting
`org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type` to `nothing`.
On an image built with this profile, restore the desired policy explicitly if
the workaround is no longer appropriate. No charger threshold or power-supply
register was changed for this workaround.
