# archi-validation-02 derived userdata builder

This text-only builder derives a new Xiaomi `lmi` userdata from the
hardware-validated GPU72 golden userspace. It never rebuilds or replaces the
kernel. Its boot compatibility reference is the D-repro D-v43 boot image
(SHA-256 `0b6c7d88b3068ae4e3d106fd4b15a1a79bf00c3e576be7b3fcd8ab62faed73ad`).
The raw and sparse golden images, package cache, cache archive, private inputs,
build states and generated outputs are external and are not versioned here.

## External inputs and portability

Set the following environment variables to the verified local copies before
running a preflight or build:

| Variable | Required value |
| --- | --- |
| `ARCHI_GOLDEN_RAW` | Raw golden, 4,551,868,416 bytes; SHA-256 `329e2124f97032a2f4b15167bbd9bbbd9395bb422f2794a2117ee610a2368f27` |
| `ARCHI_GOLDEN_SPARSE` | Android sparse golden, 2,960,036,280 bytes; SHA-256 `84182b57edb7be8e49c29e0f0b472e9b6a54f7efa645ef99664dc0e004759f78` |
| `ARCHI_DEB_CACHE` | Complete verified cache directory containing exactly 1,086 `.deb` files, 521,861,380 payload bytes |
| `ARCHI_DEB_ARCHIVE` | Deterministic cache archive, 523,274,240 bytes; SHA-256 `65058c4bc74c6aea3854060a8e7b9a7617ea6aee66d503d90564bcee214a69fd` |
| `ARCHI_LOCK_DIR` | Optional override; defaults to `../locks/userspace` relative to this builder |
| `ARCHI_TFA_FIRMWARE_INPUT` | Optional, required only by `daily-base-audio-fw-test`; defaults to the ignored `inputs/vendor-firmware/tfa98xx.cnt` |

The input path table in `manifests/INPUTS.tsv` records portable variable names,
not workstation paths. The canonical lock's
`deb-cache/SOURCES.tsv` (SHA-256
`cd62a5271e379e5b8c68f95e2871a1e66bc191c01b60f322bc0d04126ef79b75`) and the
external package cache's `SOURCES.tsv` (SHA-256
`e65c86154d2bb5f50be5672de5fed3f4ac3c5bbe7ceb9569b7ce8367fa4dee09`) are
different files with different roles; the builder verifies the latter inside
`ARCHI_DEB_CACHE`. The lock remains the authoritative package closure.

Example setup (replace each placeholder with the locally verified path):

```sh
export ARCHI_GOLDEN_RAW=/path/to/archi-validation-02.img
export ARCHI_GOLDEN_SPARSE=/path/to/archi-validation-02.img.android-sparse.img
export ARCHI_DEB_CACHE=/path/to/archi-validation-02-deb-cache
export ARCHI_DEB_ARCHIVE=/path/to/archi-validation-02-deb-cache-1086-20260927.tar
```

`ARCHI_LOCK_DIR` is not needed at the canonical repository layout; the lock
lives directly under `build/locks/userspace/`. Every external artifact is checked against its
locked size, SHA, structure and package inventory before a real build begins.
The lock's package and boot/userspace contract is documented in
[`build/locks/userspace/`](../locks/userspace/README.md).

## Safety model

The builder refuses existing outputs and creates a private persistent
`state-*` directory. The working raw is made with `cp --reflink=auto`. The
4 KiB-sector GPT is validated before partition discovery; only the copied
rootfs partition is mounted. The embedded EFI/`pmOS_boot` partition is never
mounted, and its bytes, filesystem UUID, partition UUID and the GPT are
compared before and after. Cleanup traps restore temporary package policy,
unmount the rootfs and detach only a loop device proven to use this attempt's
working image. Mount and loop cleanup is idempotent and covered by a simulated
test.

The raw output is published only after invariant checks and read-only
`e2fsck`. Android sparse conversion is round-tripped and must hash identically
to the raw. The baseline profile intentionally makes no functional changes;
ext4 metadata can still change when its copied root partition is mounted
read-write, so byte identity of the whole raw output is not expected.

Package operations use only the external locked `.deb` cache, inside the
copied ARM64 root with networking disabled and a temporary `policy-rc.d=101`.
No package is downloaded. A working ARM64 binfmt is needed only when a profile
changes packages or runs hooks. Hooks execute as root inside the copied root;
they are disabled unless explicitly authorized with `--enable-hooks`.

## Profiles

- `baseline-nochange`: no package, overlay or hook changes; validates the
  derivation path while retaining the golden userspace behavior.
- `time-seed`: adds a root-only UTC epoch seed initialized at build time from
  the host clock. At boot it advances the system clock only when older than
  the seed, then permits time synchronization to take over. It does not repair
  or depend on the non-writable RTC.
- `daily-base`: combines `time-seed` with a user XDG `Hidden=true` override for
  only the Chatty daemon autostart. Chatty remains installed, and its manual
  launcher and system desktop entry remain intact. This profile was
  hardware-validated: Phosh unlocked responsively, and the Chatty-related
  minute-long delay did not recur.
- `daily-base-audio-fw-test`: experimental extension of `daily-base`. Its
  only additional behavior installs the verified TFA9874 firmware container
  to `/lib/firmware/postmarketos/tfa98xx.cnt`, owned by `root:root`, mode
  `0644`. The external source must be a regular non-symlink file of exactly
  510 bytes with SHA-256
  `07abfca151aaa296595fff35d53c2aa2999e7d16cdc373ade2fd5954ff90c9a9`; its
  containing directory must be mode `0700`. The build stages it temporarily
  in the copied rootfs, and the hook never reads `/vendor`, downloads anything
  or changes packages. No firmware bytes are included in Git. Hardware checks
  confirmed the container loads, TFA9874 probes, the ALSA card registers and a
  direct speaker route produces audible output at the lower grille, but the
  level is extremely weak. PipeWire routing/UCM2 and usable speaker gain remain
  unresolved, so audio is not considered fully fixed. This profile remains
  experimental and always requires `--enable-hooks`.

The first-generation profiles do not purge or regenerate passwords/PINs, SSH
or host keys, machine-id, NetworkManager profiles, DConf, logs, caches or user
state. Any future sanitation profile must be explicit and separately reviewed.

## Preflight and build

With the environment variables above set, all profiles have a read-only
preflight. Hooks are opt-in both for hook-dependent profiles and for the
experimental firmware profile:

```sh
./build-derived-userdata.sh --profile baseline-nochange --version check --check-only
./build-derived-userdata.sh --profile time-seed --version check --check-only
./build-derived-userdata.sh --profile time-seed --version check --enable-hooks --check-only
./build-derived-userdata.sh --profile daily-base --version check --enable-hooks --check-only
./build-derived-userdata.sh --profile daily-base-audio-fw-test --version check --enable-hooks --check-only
```

For the audio profile also set `ARCHI_TFA_FIRMWARE_INPUT` to the private
verified export. The preflight verifies it but does not copy it into the
repository or rootfs. A real image build requires root and is deliberately
performed by the user, not as part of repository validation.

Successful outputs are written under ignored `outputs/`; each build records
manifests and hashes under an ignored private `state-*` directory. A completed
state can be verified without mounting its images:

```sh
./verify-derived-userdata.sh --state /path/to/state-directory
```

The generated userdata is compatible only with a boot satisfying the
canonical lock's `BOOT-USERSPACE-CONTRACT.md`. The embedded
`/boot/boot.img` is distinct from the active D-repro RAM boot.
