# Mobian M1 gsd-power spontaneous display wake validation — 2026-09-06

**USERSPACE CAUSE AND RUNTIME WORKAROUND VALIDATED ON XIAOMI LMI**

## Problem and scope

With Mobian/Phosh running on Xiaomi `lmi`, the panel could turn on without
operator input and turn off again roughly 15 seconds later. WAKE7 through
WAKE17 instrumented the existing session without changing kernel wakeup
sources. The result identifies the userspace path responsible for this
observed display cycle; it does not claim that every hardware wake or general
suspend/resume mechanism has been characterized.

## D-Bus and idle-watch evidence

WAKE7 captured a session-bus `WatchFired` signal from owner `:1.26` to client
`:1.53` on:

```text
/org/gnome/Mutter/IdleMonitor/Core
org.gnome.Mutter.IdleMonitor
```

ScreenSaver, DisplayConfig and Presence changes followed immediately.
`gsd-power` also emitted:

```text
g_variant_new_string: assertion 'string != NULL' failed
```

Phoc then enabled `DSI-1`, and disabled it again about 15 seconds later.
WAKE9 confirmed a normal `gsd-power` PID 3399 and the expected IdleMonitor
methods and signal. `GetIdletime` returned `NotSupported` in this environment,
so the diagnosis used bus events and watch lifecycle rather than that method.

WAKE10 and WAKE11 identified `:1.53` as the owner of the relevant idle-watch
requests. Its observed lifecycle included:

- `AddIdleWatch 900000` ms;
- `AddIdleWatch 450000` ms;
- `AddIdleWatch 150000` ms;
- after display blanking, `AddIdleWatch 30000` ms.

WAKE11 explicitly mapped watch ID 114 to the 30000 ms request and observed
`WatchFired(114)` 30 seconds later.

## Timeout correlation

WAKE12 initially attempted to change the inactive timeouts through a closed
dconf connection; the effective values correctly remained 900/900. WAKE12bis
repeated the operation in the valid session context and set both AC and battery
timeouts to 1200 seconds.

WAKE13 then observed:

- `AddIdleWatch 1200000` ms;
- `AddIdleWatch 600000` ms;
- transient reevaluation variants 1201000 and 600500 ms.

This establishes that the former 900000 ms watch represented the 900-second
inactive timeout and the 450000 ms watch its halfway point. Both changed in
lockstep with the configured timeout; their association with `gsd-power` is
therefore causal rather than a timestamp-only correlation.

## Workaround and validation

WAKE14 temporarily set:

```text
sleep-inactive-ac-type='nothing'
sleep-inactive-battery-type='nothing'
```

while leaving both timeouts at 1200 seconds. After reevaluation, WAKE15 showed
that the 1200000 and 600000 ms watches had been removed. Only the short 30000
ms mechanism remained transiently.

WAKE16 passively observed the system for 700 seconds with these preconditions:

```text
AC_TYPE='nothing'
BATTERY_TYPE='nothing'
AC_TIMEOUT=1200
BATTERY_TIMEOUT=1200
```

The observation exceeded the usual failure window and produced:

- no `DSI-1` enable or disable event;
- no new `gsd-power` error;
- no stopped service;
- no wakeup-source modification;
- no modem or DV155 state modification.

This validates disabling the `gsd-power` autosuspend action as a workaround
for the spontaneous display wake in the tested configuration.

WAKE17 restored the temporary timeout experiment while retaining the validated
workaround. The final runtime values were:

```text
sleep-inactive-ac-timeout=900
sleep-inactive-battery-timeout=900
sleep-inactive-ac-type='nothing'
sleep-inactive-battery-type='nothing'
```

## Established causal chain

The experimentally supported chain is:

```text
gsd-power sleep-inactive settings
  -> Mutter IdleMonitor watches
  -> idle-watch expiration
  -> ScreenSaver/DisplayConfig activity
  -> Phoc enables DSI-1
  -> DSI-1 is disabled again about 15 seconds later
```

The timeout perturbation and removal of the long watches demonstrate the
`gsd-power`/IdleMonitor cause for this symptom. Mutter/Phosh implementation
details may influence how the policy becomes a display transition, but a
separate kernel hardware-wakeup hypothesis is not required to explain the
captured event. This milestone does not validate broad suspend/resume behavior,
physical-button wake, or every possible source of a future display wake.
