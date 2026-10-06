# Power-domain observation candidate

The running D-repro configuration disables `CONFIG_DEBUG_FS`. This prevents
inspection of downstream clock and regulator debug summaries. The preparer
creates a **private, unvalidated** reset-GPIO diagnostic boot recipe with just
`CONFIG_DEBUG_FS=n -> y`; it does not change the canonical locked configuration
or either canonical audio constructor. The historical source patches, audio
instrumentation and functional reset-GPIO correction remain in the variant.
No boost/GPIO, regulator policy, gauge calibration or thermal setting is changed.

Debugfs also exposes writable controls: enabling it is not a read-only security
boundary. The intended protocol reads only `clk/clk_summary` and
`regulator/regulator_summary`, with no writes to debugfs controls. Reads may
access hardware and affect the measured state. Awake snapshots after resume
are not proof of domain residency during deep suspend. Diagnostic and original
boots must be compared under the same conditions before interpreting current.

The preparer verifies the exact original recipe and config hashes, refuses an
existing output directory and retains all original boot/input/toolchain checks.
The derived builder still requires byte-identical configuration after
`olddefconfig`; if enabling debugfs selects additional defaults, it fails closed.
Review the resulting delta rather than bypassing that check. No Kconfig check,
Image build, DTB build or boot validation has yet been performed for this candidate.

## Manual stages

Prepare a new private directory; this stage writes text files only.

?? WSL / Linux ? ??? Prepare only ? suggested model: GPT-6 Luna high

```sh
python3 kernel/diagnostics/power/prepare-debugfs-variant.py \
  --output-directory "$PWD/kernel/diagnostics/audio/state-power-debugfs-candidate"
```

Use the external inputs and native Alpine toolchain described in the
[existing audio recipe](../audio/README.md). Set `AUDIO_DIAG_ROOT` to the generated
directory and `AUDIO_DIAG_PROJECT_ROOT` to the canonical repository root; set
input/source/tool paths explicitly. Invoke the generated reset-GPIO constructor
first with `--preflight`, then `--check-only`. The latter compiles only Kconfig
host utilities/probes, not a kernel. A heavy build without an option is a
separate manual user operation after those checks pass. It produces
`D-repro-01-power-debugfs-reset-gpio-diagnostic-boot.img`, preserving the ramdisk
and boot metadata. This candidate has not been built or booted and must not
replace the durable boot. No flash or phone operation is included.

## Host validation - 2026-10-06

Private generation succeeded. Validation checked the exact single-symbol config
delta, every reset-variant transformation anchor, Bash syntax of both generated
constructors and the final derived reset constructor, preserved config/output
gates, refusal to overwrite an existing generation directory, and new local
links. Candidate config SHA-256 is
`8ad8736c2e96b7d7edfd4ff53ea4d18c8b5836113384b3804eed672d6a553eda`.
External-input preflight, native Kconfig and hardware validation remain pending.
