# Power-domain observation candidate

The running D-repro configuration disables `CONFIG_DEBUG_FS`, preventing
inspection of downstream clock and regulator debug summaries. The preparer
creates a private reset-GPIO diagnostic boot recipe without changing the canonical
locked configuration or either canonical audio constructor. Historical source
patches, audio instrumentation and functional reset-GPIO correction are retained.
No boost/GPIO, regulator policy, gauge calibration or thermal setting is changed.

## Reviewed Kconfig delta

The [config patch](power-debugfs-config.patch) enables debugfs. In this source,
`MSM_PM` selects `MSM_IDLE_STATS` when debugfs is enabled; therefore the candidate
also enables Qualcomm idle statistics with the four existing default bucket
values. Other newly visible optional debug features, including block and
Bluetooth debugfs, are explicitly disabled. Existing functional options stay
unchanged. Enabling idle statistics may add observation overhead; this is a
diagnostic kernel, not a claimed power-saving change.

The preparer verifies the original constructor/config and reviewed delta hashes,
refuses an existing generation directory and retains original input/toolchain
checks. The derived builder still requires byte-identical configuration after
`olddefconfig`. Unexpected changes stop the check rather than relaxing its gates.

Debugfs exposes writable controls: enabling it is not a read-only security
boundary. The intended protocol reads only `clk/clk_summary` and
`regulator/regulator_summary`, with no writes to debugfs controls. Source review
found that clock summary traversal takes transient bus votes when the clock
provider implements them; regulator summary reads voltage/current information.
Snapshots can affect measured state and awake snapshots after resume do not prove
domain residency during deep suspend. Compare diagnostic and original boots
under the same conditions before interpreting current.

## Manual stages

Prepare a new private directory; this stage writes text files only.

?? WSL / Linux ? ??? Prepare only ? suggested model: GPT-6 Luna high

```sh
python3 kernel/diagnostics/power/prepare-debugfs-variant.py \
  --output-directory "$PWD/kernel/diagnostics/audio/state-power-debugfs-reviewed"
```

Use external inputs and the native Alpine toolchain described in the
[existing audio recipe](../audio/README.md). Set `AUDIO_DIAG_ROOT` to the generated
directory and `AUDIO_DIAG_PROJECT_ROOT` to the canonical repository root; set
input/source/tool paths explicitly. Invoke the generated reset-GPIO constructor
first with `--preflight`, then `--check-only`. The latter compiles only Kconfig
host utilities/probes, not a kernel. A heavy build without an option is a
separate manual user operation after those checks pass. It produces
`D-repro-01-power-debugfs-reset-gpio-diagnostic-boot.img`, preserving the ramdisk
and boot metadata. The candidate must not replace the durable boot. No flash or
phone operation is included.

## Validation - 2026-10-06

Initial generation passed exact one-symbol delta, Bash syntax, reset-variant
transformation anchors, preserved output/config gates and overwrite refusal.
External-input preflight then passed all checks, including strict sequential
patch application. Native dynamic/static toolchain probes passed, but initial
`olddefconfig` rejected the one-symbol configuration because newly visible defaults
changed it. The reviewed config patch includes the obligatory Qualcomm statistics
and disables optional Bluetooth/block defaults. Its candidate SHA-256 is
`c6da6e71cc7418f36997325ff5d72693d9861945cc4999b6be9661a150451e78`.
The second native check passed both link probes and byte-identical
`olddefconfig` validation. The later manual build completed successfully; see below. Hardware boot
validation remains pending.


## Manual build - 2026-10-06

The operator ran the heavy build. Both inner and wrapper states are COMPLETE;
post-olddefconfig configuration is byte-identical to the reviewed candidate.
The repacked ramdisk matches the original and the repacked DTB matches the
reset-GPIO-corrected DTB. The resulting temporary diagnostic boot has size
54,652,928 bytes and SHA-256
`147258b2df751cbcdb3c0cb2a10d10f2b0bcacaeee1fe13fdf3bdc79e71e06b0`.
A separate Windows Downloads copy was verified with the same hash. Neither
binary nor raw build logs are tracked. No boot, flash or hardware validation
has occurred yet; a successful build does not establish power improvement.


## Hardware startup - 2026-10-06

After the operator's temporary boot and USB reconnect, SSH reported
`4.19.325-cip128-st12-perf-ga5b3099017ae-dirty`, build timestamp
October 6 16:41:37 UTC. The live IKCONFIG SHA-256 matches the reviewed candidate
`c6da6e71cc7418f36997325ff5d72693d9861945cc4999b6be9661a150451e78`.
Debugfs is mounted and both clock/regulator summaries are readable.
CPU idle remains `sleep_disabled=N`; UPower and the existing CPU-idle opt-in
service are active. Initial state was USB online, 97% charging, 27 C.
The anticipated `/proc/msm_pm_stats` interface is absent, but debugfs
`lpm_stats` is present. Interface names alone are not proof of counters' validity.

An awake, USB-connected snapshot shows zero camera/GPU regulator use counts,
active primary USB and PCIe-0 domain use counts, and the known always-on boost.
These are software use counts under connected conditions, not direct power
measurements or residency during suspend. No regulator/clock debugfs control
was written. A separate bounded unplug/suspend observation is being prepared;
no consumption improvement or diagnostic-kernel long-run validation is claimed.


## First bounded suspend trial - 2026-10-06

A private, 180-second derivative of the existing gauge trial retained USB-off,
settled USB runtime status, capacity, input-quiet and logind-inhibitor checks.
It requested one initial suspend and disabled the gauge re-suspend branch for
this observation. An owned RTC end alarm was cleared on completion; the
transient service finished successfully and is inactive. No debugfs control,
radio or charge policy was changed. Camera and microphone were not opened.

The observed interval was 181.821441 boottime seconds and 0.675646 monotonic
seconds, implying approximately 181.145795 seconds suspended. The newly
available `lpm_stats/suspend` independently reported one successful L3 suspend
lasting 181.169277 seconds. USB stayed offline at both sample endpoints.
The gauge charge-counter decrease was 4,868 uAh, approximately 96.38 mA over
the interval; instantaneous samples were 104.98 mA before initial suspend and
95.703 mA at completion. This short gauge-derived estimate is not an independent
current measurement or a controlled cross-boot comparison. No improvement is
established against the previous approximately 94-97 mA observations.

Before initial suspend, software use counts for primary USB and its PHY had
fallen to zero. PCIe-0, the known always-on boost and several shared storage/radio
rails retained positive use counts. Camera/GPU regulator use counts were zero
in that pre-suspend snapshot. Post-resume snapshots can include display/GPU
activity and must not be described as deep-suspend residency. These summaries
identify consumers/votes, not actual current in individual rails; PCIe DRV
firmware ownership is especially relevant when interpreting a retained vote.
The directory `lpm_stats` cannot be read as a scalar file: future collection
must read its specific read-only `suspend`/`stats` children, with compact parsed
output. Raw logs remain private. After operator reconnection, status was
Charging with USB online and no remaining RTC alarm.
