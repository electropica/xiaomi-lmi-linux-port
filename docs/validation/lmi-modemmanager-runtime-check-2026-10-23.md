# Runtime review after the cleanup — October 23, 2026

The current Mobian boot was inspected over its existing USB SSH connection.
No service was restarted, no power/radio/GPIO/IRQ setting changed, no AT
command sent and no unplug, suspend, build or flash initiated.

## Confirmed observations

- ModemManager is active with ExecStart=/usr/sbin/ModemManager and no drop-ins.
  The quick-suspend-resume option proposed as the first MiniMax lead is absent.
- mmcli -L returns "No modems were found". No modem registration query or AT
  command is justified by that output. Absence from the manager does not prove
  the external modem's electrical shutdown.
- The awake NPU power attribute reports "off". The earlier installed NPU policy
  and controlled tests must not be erased by a new claim that Mobian never
  controls the NPU. This reading does not establish the entire suspend policy.
- SSR reports esoc0, NPU, SLPI and several other registered subsystems as
  OFFLINING, and ADSP, Venus, a650_zap and WLAN as ONLINE. These are driver
  state labels, not current/residency measurements. The October 13 ESOC audit
  already demonstrated why an initial nominal PWR_OFF is not proof of a
  physical power-down operation. No modem force-off is proposed here.
- The SDX55M PCIe ESOC identity is present. Modem handshake GPIOs TLMM1 and3
  read input low; TLMM56 and57 read output low. These are plugged-awake
  observations. The older truncated GPIO capture did not preserve this whole
  TLMM block, so it cannot serve as a reliable four-pin baseline.
- Generic runtime PM is unsupported on many of the listed downstream devices.
  "unsupported" must not be interpreted as "powered on" or "powered off".

## What follows

The suggested quick-resume experiment is not justified: its premise is absent
on the current installation. This narrows that userspace lead, not the whole
modem/power branch. Do not spend another unplug window testing it unchanged.

The same bounded shell reader is prepared for the next LineageOS boot, with no
extra unplug needed. It will compare the subsystem labels and the four GPIO
levels in the same connected-awake state. A difference will remain a candidate
for mechanism review, rather than being attributed a current saving. Missing
master-stat output at the reader's candidate paths remains unavailability at
those paths, not proof that the firmware exposes no records anywhere.

Raw snapshots and transport receipts are private. Public conclusions are limited
to the facts above; the battery drain and gauge-scale uncertainty remain open.
