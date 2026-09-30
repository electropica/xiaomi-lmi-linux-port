# Historical Alpine Clang 22 toolchain reconstruction — 2026-09-18

> Historical build-environment investigation for Xiaomi lmi. This is separate
> from the later native Alpine Kconfig checks documented in the
> [audio diagnostic recipe](../../kernel/diagnostics/audio/README.md). It is
> not a current build instruction or a claim of a completed Clang rebuild.

## Scope and status at the recorded date

The investigation attempted to reconstruct the historical native x86_64
Alpine/pmbootstrap environment associated with Clang 22 packages used in the
project. The original native chroot and its package cache were not available
for reuse. At the end of the 2026-09-18 record, source verification succeeded
and the reconstructed buildroot had reached dependency setup, but the actual
Clang compilation had not completed: two `abuild -r` attempts stopped before
compilation and a further attempt was still running. No successful Clang
package result is established by that snapshot.

This limit is distinct from the later successful Clang/LLD 22.1.8 link probes
and `olddefconfig` check in the native Alpine environment. Those checks
validate the kernel Kconfig/toolchain path; they do not prove that historical
Clang APKs were rebuilt byte-for-byte.

## Historical source and package identity

The target recipe state was `clang22 22.1.8-r0`, with `_llvmver=22` and
`_default_clang="yes"`. The recorded LLVM source context is commit
[`c0c1905cddbf0da3e57f8274fafae8a4443d8696`](https://github.com/llvm/llvm-project/commit/c0c1905cddbf0da3e57f8274fafae8a4443d8696).
The corresponding `llvm-project-22.1.8.src.tar.xz` witness was 167,061,596
bytes with SHA-512
`2615b20ba08534f83ab8ecc7b5ba43b5f1dfcf9cdb2534a32fcdbf0ccdd9a008b46276e45ef26ed9377f65b5e4ae89ea798f3863fd034484b5715140f3a7b35c`;
the recorded `abuild verify` accepted the archive and all six recipe patches:

- `10-add-musl-triples.patch`
- `30-Enable-stack-protector-by-default-for-Alpine-Linux.patch`
- `clang-001-fortify-include.patch`
- `clang-002-fortify-enable.patch`
- `clang-003-as-needed.patch`
- `py3-clang-add-version-to-so-name.patch`

The later Alpine `clang22 22.1.8-r1` recipe changed both the package release
and `_default_clang` from `yes` to `no`; version-family equality alone does
not make it equivalent to the recorded r0 recipe.

Historical package witnesses recorded for comparison were:

| Package | Version | Size | Historical checksum witness |
| --- | --- | ---: | --- |
| `clang22` | `22.1.8-r0` | 704,612 bytes | SHA1 suffix `9bdce7b7` |
| `clang22-headers` | `22.1.8-r0` | 1,037,482 bytes | SHA1 suffix `a33ecd85` |
| `clang22-libs` | `22.1.8-r0` | 38,048,553 bytes | APKINDEX SHA1 `5866305587ff7ab583a6509e73f8a52d61062978` |
| `lld22-libs` | `22.1.8-r0` | 2,823,514 bytes | SHA1 suffix `f3de37f2` |

The historical record also distinguished the Clang/LLD r0 build wave from a
later LLVM 22.1.8-r1 dependency wave. The latter had build date `1784148360`
and independently matched checksum suffixes for `llvm22` (`4a0df8aa`),
`llvm22-libs` (`1b851c70`) and `llvm22-linker-tools` (`9694e833`). The recorded
Clang/LLD build date was `1781685583`.

## Environment and dependency anchors

The reconstructed native build context recorded these versions:

| Component | Historical version or value |
| --- | --- |
| Host architecture | `x86_64` |
| pmbootstrap | `3.10.1` |
| Python used by pmbootstrap | `3.14.4` |
| apk-tools | `3.0.7-r0` |
| abuild | `3.17.0-r0` |
| fakeroot | `1.37.2-r0` |
| GCC generation | `15.2.0` |
| Historical aports snapshot | [`614add499ad7d79351b0bdc0c3900d25a85907a2`](https://gitlab.postmarketos.org/postmarketOS/pmaports/-/tree/614add499ad7d79351b0bdc0c3900d25a85907a2) |

The wider cross-build setup used `crossdirect`; the native x86_64 chroot was
mounted into an aarch64 buildroot as `/native`, with its musl loader under
`/native/lib`. Those are environment relationships, not portable host paths.

Selected package-version anchors recovered from the historical aports state
include:

- Core build and libraries: `alpine-baselayout 3.7.2-r1`,
  `alpine-baselayout-data 3.7.2-r1`, `build-base 0.5-r4`,
  `busybox 1.37.0-r31`, `busybox-binsh 1.37.0-r31`, `gcc/g++ 15.2.0-r5`,
  `binutils 2.45.1-r1`, `linux-headers 7.0.0-r1`, `musl 1.2.6-r2`,
  `fortify-headers 3.0.1-r2`, `libcap 2.78-r0`, `libffi 3.5.2-r1`,
  `libxml2 2.13.9-r2`, `openssl 3.5.7-r0`, `zlib 1.3.2-r0`,
  `xz 5.8.3-r0`, `zstd 1.5.7-r2`, `tar 1.35-r5` and `patch 2.8-r0`.
- Other recovered base dependencies: `acl 2.3.2-r1`, `bzip2 1.0.8-r6`,
  `jansson 2.15.0-r0`, `lz4 1.10.0-r1`, `isl25 0.25-r2`, `isl26 0.26-r2`,
  `ca-certificates 20260413-r0`, `expat 2.8.1-r0`, `lzip 1.26-r0`,
  `perl 5.42.2-r0`, `pkgconf 2.5.1-r0`, `pax-utils 1.3.9-r1`,
  `libarchive 3.8.7-r0`, `rhash 1.4.6-r0`, `libuv 1.52.1-r0`,
  `gmp 6.3.0-r4`, `mpc1 1.3.1-r1` and `mpfr4 4.2.2-r0`.
- Python and curl dependency anchors: `python3 3.14.5-r1`,
  `bluez-headers 5.86-r0`, `mpdecimal 4.0.1-r0`, `ncurses 6.6_p20260516-r0`,
  `readline 8.3.3-r1`, `sqlite 3.53.2-r0`, `tcl 8.6.17-r1`, `curl 8.20.0-r1`,
  `brotli 1.2.0-r1`, `c-ares 1.34.6-r0`, `libidn2 2.3.8-r0`,
  `libpsl 0.21.5-r3`, `nghttp2 1.69.0-r0`, `groff 1.24.1-r0`,
  `libunistring 1.4.2-r0` and `libev 4.33-r1`.

The Clang recipe's build dependencies were `cmake`, `help2man`, `libxml2-dev`,
`llvm22-dev`, `llvm22-gtest`, `llvm22-static`, `llvm22-test-utils`, `python3`
and `samurai`. Its `options="!check"` meant the declared check dependencies
were not required for that package build.

## Reconstruction lessons and confidence limits

The historical notes recorded several environment issues that were not Clang
source failures: the initial minimal root lacked account databases and a
usable `/dev`; `abuild` needed an explicit source-cache destination to avoid
fetching and rewriting the working recipe; `abuild-apk` was supplied by
`abuild-sudo`; and the closed package repository needed the historical
`build-base` dependency providers. The reference recipe was restored after
the accidental checksum-path rewrite. Local bootstrap copies disabled some
checks to close dependency cycles; such packages were functional bootstrap
artifacts, not proven byte-identical historical packages. Signing material
and workstation-specific paths are deliberately omitted from this record.

The reconstructed Clang buildroot reached 71 packages after adding
`abuild-sudo`, matching a historical native-chroot package-count witness.
The historical wider toolchain state had about 101 packages and 996.9 MiB;
the fresh root had also briefly reached 68 packages before its final
corrections. These counts are structural clues only, not package-by-package
identity proofs.

The source snapshot recorded that the historical Clang compilation had not
yet completed. A correct package version, successful dependency closure, or
successful modern Kconfig check does not prove a bit-identical Clang APK.
Any future reproducibility claim must compare package metadata, build dates,
sizes and the historical checksum witnesses above. No APK, buildroot, private
log, signing credential, or source archive is included in Git.

For the separate D-v43/OpenRC hardware result, see the
[D-v43 reconstruction record](d-v43-openrc-reconstruction-2026-09-23.md).
