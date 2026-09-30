# D-repro SoundWire diagnostic boot recipes

These host-side recipes preserve the experiments that isolated the WCD938x
reset-mux issue. They do not contact a phone. They produce a separate
temporary boot artifact intended only for a manually supervised
fastboot boot; neither script contains a flash operation, and the installed
boot must remain untouched.

## Evidence and patch roles

The source input is the verified LineageOS
android_kernel_xiaomi_sm8250 archive for base commit
a5b3099017ae581aae8bf597b2f9c8c765026af1, SHA-256
9e3bde7cde952682225a0375444bd3c1d33d99ddb80fa17b6a3abf3957f36c94.
The original D-repro boot SHA-256 is
0b6c7d88b3068ae4e3d106fd4b15a1a79bf00c3e576be7b3fcd8ab62faed73ad;
the locked kernel config is
[../../configs/dv43-qca6390-v2.config](../../configs/dv43-qca6390-v2.config),
SHA-256 6512a0c29ebf987d25c0cceb79917df32d6fed4b67e4c3b94bfad9fdb1745e37.
The full source archive, original boot, unpacked sections, and mkbootimg tools
are external inputs. Their identities and roles are listed in
[INPUTS.tsv](INPUTS.tsv); none is stored in Git.

The diagnostic-only constructor applies patches 1–3 below. The separate
reset-GPIO variant applies the same first three patches and then adds patch 4
to rebuild the corrected DTB; patch 4 is not silently included in the
instrumentation-only boot:

1. [0001-mobian-add-boot-safe-QCA6390-UART-support-and-restor.patch](../../patches/0001-mobian-add-boot-safe-QCA6390-UART-support-and-restor.patch)
   — retained historical source lineage, SHA-256
   d193cfbaad83811703f5db5990eaa52358e1828af581e09c702f4efa10aec782.
2. [0002-esoc-preserve-crash-state-on-late-run-notification.patch](../../patches/0002-esoc-preserve-crash-state-on-late-run-notification.patch)
   — retained historical source lineage, SHA-256
   c94fe70ae385e1f74fb56566b9743d4b5df23b6fc42aeabecbdbee9c3a2004aa.
3. [patches/0001-lmi-wcd938x-rx-soundwire-diagnostic.patch](patches/0001-lmi-wcd938x-rx-soundwire-diagnostic.patch)
   — read-only LMI_SWR_DIAG instrumentation, SHA-256
   2d5c2188356b0708ebf88b6a2694b216b4ccb62e6e8ab74124a53ea96d3b6e79.
4. [../../patches/audio/0001-lmi-wcd938x-reset-gpio-mux.patch](../../patches/audio/0001-lmi-wcd938x-reset-gpio-mux.patch)
   — functional DTS correction, SHA-256
   1d1859556bb05c207b70225ecccc922c9338eff485f729012abc41ba75fbfef7.

The instrumentation captures registers only on the first failed lookup of the
target RX slave. It does not force ATTACHED, change the returned error, or
alter reset, pinctrl, clock, or timing behavior. The register accessor can
take its normal transient clock vote; this is not claimed to be a
hardware-state-free read.

The reset-GPIO patch changes func2 to gpio in the active and sleep GPIO32
states. Live testing with a DTB containing that correction observed neither
the invalid pinctrl-function error nor the earlier RX/TX clash, and both
WCD938x SoundWire slaves bound. The reset patch remains distinct from the
diagnostic instrumentation.

The TFA gain interpretation in the dated validation summary was checked
against a separate sanitized host note, SHA-256
e966e54aae0cbd8bed5f20bb9034a5bc7d0cd3ee77a0bc05199ca5550b4d1b11. The note
and all raw runtime evidence remain outside this repository.

## Portable inputs

Set these paths explicitly; there is no machine-specific fallback:

- AUDIO_DIAG_INPUT_DIR: private input directory containing the verified
  original boot, source archive, unpacked boot sections, boot information,
  and its SHA256SUMS.
- AUDIO_DIAG_SOURCE_DIR: extracted source tree matching the checked archive.
  The preflight compares every patched source file against the archive.
- AUDIO_DIAG_MKBOOTIMG_TOOLS: directory containing the verified
  unpack_bootimg and mkbootimg.
- NATIVE_CHROOT: complete native Alpine Clang/LLD 22.1.8 environment,
  required for --check-only and a real build.
- Optional AUDIO_DIAG_CONFIG, AUDIO_DIAG_OUTPUT_DIR, and
  AUDIO_DIAG_STATE_DIR overrides. An override config must still match the
  locked SHA above.

The default output and state directories are local ignored paths under this
directory. .gitignore excludes inputs/, outputs/, extracted source-*,
and state-*; never add those paths or their contents.

## Validation and build commands

Host-only preflight checks the input manifest and fixed hashes, validates the
archive layout and source correspondence, and applies the patch sequence to
a temporary subset of source files with --fuzz=0. It does not enter a chroot
or compile:

    AUDIO_DIAG_INPUT_DIR=/path/to/verified-inputs \
    AUDIO_DIAG_SOURCE_DIR=/path/to/extracted-a5b3099017ae \
    AUDIO_DIAG_MKBOOTIMG_TOOLS=/path/to/verified-mkbootimg-tools \
    bash kernel/diagnostics/audio/build-audio-swr-diagnostic-boot.sh --preflight

    AUDIO_DIAG_INPUT_DIR=/path/to/verified-inputs \
    AUDIO_DIAG_SOURCE_DIR=/path/to/extracted-a5b3099017ae \
    AUDIO_DIAG_MKBOOTIMG_TOOLS=/path/to/verified-mkbootimg-tools \
    bash kernel/diagnostics/audio/build-audio-swr-reset-gpio-diagnostic-boot.sh --preflight

--check-only additionally enters the explicitly selected native Alpine
chroot, checks Clang/LLD, runs dynamic and static link probes, and runs
olddefconfig. Kconfig host utilities may be compiled; no kernel Image or DTB
target is built. This mode needs an interactive terminal if sudo is required.

After preflight, a manual native check uses the same external input variables
plus NATIVE_CHROOT:

    AUDIO_DIAG_INPUT_DIR=/path/to/verified-inputs \
    AUDIO_DIAG_SOURCE_DIR=/path/to/extracted-a5b3099017ae \
    AUDIO_DIAG_MKBOOTIMG_TOOLS=/path/to/verified-mkbootimg-tools \
    NATIVE_CHROOT=/path/to/alpine-chroot \
    bash kernel/diagnostics/audio/build-audio-swr-diagnostic-boot.sh --check-only

Only after that succeeds may a user manually invoke either builder without an
option, with the same variables and NATIVE_CHROOT. The reset-GPIO variant
uses the same gates and additionally rebuilds the DTB. Neither command is
run as part of repository validation.

The real builders are manual operations and are not run by automated checks.
The diagnostic-only variant replaces only the embedded kernel section. The
reset-GPIO variant also rebuilds and replaces only the base kona-v2.1 DTB
after checking its identity and both corrected reset states. Both preserve
the ramdisk, boot metadata, and command line and refuse to overwrite outputs.
The reconstructed kernel is not claimed to be bit-identical to the
historical D-repro kernel; matching archive and config hashes is provenance,
not proof of the original full build.

Run checksum verification from this directory:

    sha256sum -c SHA256SUMS
