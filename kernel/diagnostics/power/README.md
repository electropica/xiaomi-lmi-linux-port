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
