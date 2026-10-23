# One hypothesis for the sleep current: a resource left ACTIVE, not a request left unmade

## The hypothesis

On Mobian, the APSS goes into the RPM suspend with at least one resource
still **ACTIVE** that LineageOS has put to **SLEEP**. The requests
themselves are identical on the two platforms, the regulator summary
shows the same requests, and the kept evidence cannot see the difference
because the observed sleep-request handshake carries no decodable bank
coordinates on either side.

This is a hypothesis about the **state**, not about the **requests**.

## What the sources say

`drivers/soc/qcom/rpmh.c`, revision `a5b3099017ae581aae8bf597b2f9c8c765026af1`,
the exact revision of both platforms and byte identical between them, as
the packet manifest records. The RPMh master has three request states:

```c
case RPMH_ACTIVE_ONLY_STATE:
case RPMH_WAKE_ONLY_STATE:
case RPMH_SLEEP_STATE:
        /* Cache the RPMh request and send if the state is ACTIVE_ONLY.
         * SLEEP/WAKE_ONLY requests are not sent to the controller at
         */
        if (state == RPMH_ACTIVE_ONLY_STATE) {
        ...
        if (state != RPMH_ACTIVE_ONLY_STATE) {
                rpm_msg.msg.wait_for_compl = (state == RPMH_WAKE_ONLY_STATE);
                ret = send_single(dev, RPMH_SLEEP_STATE, p->addr, p->sleep_val);
```

and, further down, the completion comment: a request whose state was
SLEEP or WAKE_ONLY is treated as complete differently from an ACTIVE_ONLY
one.

The consequence is the mechanism of the hypothesis: **a request that was
made is not proof that the resource was put to sleep.** A SLEEP request
is cached by the master and only transmitted when the master next goes
ACTIVE_ONLY. If the system goes down before that flush, the resource
stays ACTIVE, while the request log still shows the SLEEP request, with
its address and its value. The two platforms reach that moment by
different paths, Mobian's 900 s inactivity delay and its gauge-driven
wake cycles every fifteen minutes against LineageOS's doze, so the state
of the master when the system goes down need not be the same.

This is also why the identical messages do not establish identical
states, and why the ACTIVE, SLEEP and WAKE distinction matters here
rather than the addresses.

## The counter-evidence

* **The requests are identical and the driver is byte identical.** There
  is nothing in the kept evidence that points at a request difference, so
  the hypothesis rests entirely on a material state that is not observed.
* **The Mobian trace used for the comparison is from an older build.**
  The 12 October observer artefacts record no kernel release string and
  are not certified to be the current build, so the comparison of the
  suspend paths may not hold for the build that produced the night.
* **Nothing measures the cost of a resource left ACTIVE.** The regulator
  framework reports no current, every current column reading 0 mA, and
  the gauge's readings, which are the only electrical data available
  during an unplugged sleep, are the same gauge whose scale is in
  question.
* **The gauge is three times faster on Mobian**, which implies more wake
  cycles and therefore more occasions on which the master could be in a
  different state. A resource left ACTIVE is one of several contributors
  that this hypothesis would have to be separated from, and nothing held
  separates it today.
* **The 86 mAh and 143 mAh discontinuities** at the unplug show that the
  gauge's own reporting changes at the charger removal, so a gauge
  reading is not a direct measurement of a physical quantity either.

## The smallest discriminating verification

**Read the state the resources are left in, on both platforms, instead of
the requests.** The candidate instrument is already visible in both
traces: the device `b221200.qcom,rpmh-master-stats`, the RPMh master's
own statistics, which appears as a suspend callback in the Android trace
and in the Mobian observer trace.

Two things have to be closed in order:

1. **What that device exposes.** Its driver was not located among the
   files fetched from this revision, so whether it reports the
   per-resource state is not established here.
2. **Whether what it reports is the state that decides the consumption.**
   A per-resource state is necessary but not sufficient: the cost of a
   resource left ACTIVE still has to be measured, and the gauge is the
   only instrument available during an unplugged sleep.

On Mobian the reading is one `cat`, and the tool for it already exists:
the phone takes its own snapshots, because the phone is only reachable
over the cable. On LineageOS the same reading needs the OS switch, which
is already planned and which the two systems sharing the phone makes
serial rather than parallel.

If that device turns out not to expose the per-resource state, the next
smallest thing is the suspend-path regulator trace of the **current**
Mobian build, with the observer method of 12 October, whose Android
counterpart is already kept. That comparison would also settle the one
observed difference in the suspend paths, `gpu_cx_gdsc`.

## What this does not claim

* It does not claim that the GPU core rail, or any other rail, is the
  responsible one. In the unplugged and awake state on Mobian the GPU
  core rail is not requested, which is evidence against it in that state
  and says nothing about the suspend path, which is a different code
  path.
* It does not claim that the modem, the APSS or the gauge are excluded.
  It is one candidate among the things the traces do not show, and the
  only one for which a concrete mechanism and an existing instrument can
  be named.
* It does not change the status of the factor of about 3.4, which remains
  a difference of gauge readings and not an established electrical
  measurement.
