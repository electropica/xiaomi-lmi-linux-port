# Reconstructed kernel used on 27 November

This folder records the configuration, targeted fixes, checks and build workflow for the reconstructed Linux 7.2.12 kernel used in menu `1426e2e8…`. The menu was written to `boot`; Fastboot reported success and Mobian later started with the kernel and DTB identifiers below. Rear-camera preview, charging indication and 20 seconds of speaker playback were observed. The boot partition was not independently read back after that write, Android was not requalified for that exact menu, and intermittent charging indications and audio errors remain under investigation.

## Fixes and source inputs

* `patches/qcom-charger-iio-fallback.patch` accepts the board's `usbin_v` and `usbin_i` IIO names when the previous names are absent.
* `patches/qcom-power-status-restore.patch` restores charge-state and gauge sign/charger-binding behavior from the retained earlier reference. `tools/test-charger-status-host.py SOURCE` exercises six charger-status cases against the actual source.
* The rear sensor binding is the existing [`0004-lmi-ov13b10-of-match.patch`](../patches/0004-lmi-ov13b10-of-match.patch).
* Audio support uses the existing [`0007-lmi-audio-mi2s-clock-q6afe-dai-v3.patch`](../patches/0007-lmi-audio-mi2s-clock-q6afe-dai-v3.patch), the API adaptations in `tools/fix-tfa98xx-712.py` and `patches/tfa-warning-corrections.patch`. The latter addresses compiler diagnostics; it is not proof that audio errors are fixed.
* `patches/qcom-fg-local-irq.patch` makes two local IRQ handlers static to address missing-prototype warnings.

These are historical targeted changes against specific inputs, not a complete automated patch series for a fresh upstream checkout. The vendor-derived audio source, initial import transformations and full source provenance are not completely established in this repository. Do not assume the patches alone recreate the tested tree. The manifest checks in the build script pin several important files, not every source file.

## Build from an already prepared source tree

Obtain an independently reviewed prepared source tree containing the corrections above, and the previously tested board DTB separately. Neither proprietary firmware nor generated images are shipped here. The DTB used for the tested menu has SHA-256 `1fc0316ac94754dac33c34cb8ab57b76ba4dc10b074f64c93d03f99beeec310b`; the `.config` is `config-tested` and its hash is checked by the script. The observed compiler was GCC 15.2.0. A newly generated DTB is not assumed equivalent to the tested one.

```sh
bash build-kernel.sh --plan /path/to/prepared/source /path/to/new/output /path/to/tested.dtb
bash build-kernel.sh --execute /path/to/prepared/source /path/to/new/output /path/to/tested.dtb
```

The plan hashes the config, DTB and selected camera, charger, gauge and TFA files. Execute builds into a new directory, refuses configuration drift, reports compiler warnings and never touches the phone. The tested kernel identifier advertised by the menu was `a7c53444cda24011a821031829219056e5d948b55536a0e6e3d0734baa3264b7`; that command-line identifier is not a cryptographic measurement of running RAM. A later build is not expected to be byte-identical without further reproducibility work.

`prepare-bundle.py WORKING_BUNDLE NEW_IMAGE NEW_OUTPUT_DIRECTORY` builds a candidate bundle by replacing only the kernel in the retained working bundle, checks the DTB, components and CRCs, and does not touch a device. The outer firmware must then be rebuilt with its new bundle metadata; see [the menu recipe](../../../../build/boot-menu/outer-tested-20261127/README.md). Neither output is automatically flashable.
