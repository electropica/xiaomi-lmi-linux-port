# GPU72 historical sysroot provenance

Status: captured from the validated historical GPU68/GPU69/GPU72 build environment.

## Historical sysroot

- Path: `/home/linuxagent/pmos-d-repro-01/analysis/gpu68-wayland-egl-init/sysroot-combined`
- Installed dpkg packages: **187**
- Distribution: Debian GNU/Linux 13 (trixie)
- APT source: `deb http://deb.debian.org/debian trixie main`

## Proven construction facts

- `libdrm-dev` version `2.4.124-2` was already installed before the recorded GPU68 APT transaction.
- `libpciaccess-dev` and the libdrm runtime family were also already installed.
- This is directly confirmed by `eipp.log.xz`: these packages have `Status: installed` but are absent from its `Install:` transaction set.
- The recorded GPU68 APT transaction adds 102 packages.
- The final dpkg database contains 187 installed packages.
- Therefore 85 dpkg packages pre-existed the recorded GPU68 APT transaction.
- Wayland runtime/dev files and `libffi-dev` were additionally extracted manually from preserved `.deb` files and are not registered as installed packages in the final dpkg status database.
- All 23 regular files and all 4 symlinks from `sysroot-overlay` were verified identical in `sysroot-combined`.

## Recorded GPU68 APT command

```text
/usr/bin/apt-get install -y build-essential meson ninja-build pkg-config python3 python3-mako python3-packaging python3-yaml bison flex glslang-tools libdrm-dev
```

## EIPP packages added by that transaction

Count: **102**

```text
binutils
binutils-aarch64-linux-gnu
binutils-common
bison
build-essential
bzip2
ca-certificates
cpp
cpp-14
cpp-14-aarch64-linux-gnu
cpp-aarch64-linux-gnu
dpkg-dev
fakeroot
flex
g++
g++-14
g++-14-aarch64-linux-gnu
g++-aarch64-linux-gnu
gcc
gcc-14
gcc-14-aarch64-linux-gnu
gcc-aarch64-linux-gnu
glslang-tools
libalgorithm-diff-perl
libalgorithm-diff-xs-perl
libalgorithm-merge-perl
libasan8
libatomic1
libbinutils
libcc1-0
libctf-nobfd0
libctf0
libdpkg-perl
libexpat1
libfakeroot
libffi8
libfile-fcntllock-perl
libfl-dev
libfl2
libgcc-14-dev
libgdbm-compat4t64
libgdbm6t64
libgomp1
libgpm2
libgprofng0
libhwasan0
libisl23
libitm1
libjansson4
liblocale-gettext-perl
liblsan0
libmpc3
libmpfr6
libncursesw6
libperl5.40
libpkgconf3
libpython3-stdlib
libpython3.13-minimal
libpython3.13-stdlib
libreadline8t64
libsframe1
libstdc++-14-dev
libtsan2
libubsan1
libyaml-0-2
m4
make
media-types
meson
netbase
ninja-build
openssl
patch
perl
perl-modules-5.40
pkg-config
pkgconf
pkgconf-bin
python3
python3-autocommand
python3-inflect
python3-jaraco.context
python3-jaraco.functools
python3-jaraco.text
python3-mako
python3-markupsafe
python3-minimal
python3-more-itertools
python3-packaging
python3-pkg-resources
python3-setuptools
python3-typeguard
python3-typing-extensions
python3-yaml
python3-zipp
python3.13
python3.13-minimal
readline-common
spirv-tools
sq
tzdata
xz-utils
```

## Final dpkg package manifest

```text
apt | arm64 | 3.0.3
base-files | arm64 | 13.8+deb13u6
base-passwd | arm64 | 3.6.7
bash | arm64 | 5.2.37-2+b9
binutils | arm64 | 2.44-3
binutils-aarch64-linux-gnu | arm64 | 2.44-3
binutils-common | arm64 | 2.44-3
bison | arm64 | 2:3.8.2+dfsg-1+b2
bsdutils | arm64 | 1:2.41-5
build-essential | arm64 | 12.12
bzip2 | arm64 | 1.0.8-6
ca-certificates | all | 20250419
coreutils | arm64 | 9.7-3
cpp | arm64 | 4:14.2.0-1
cpp-14 | arm64 | 14.2.0-19
cpp-14-aarch64-linux-gnu | arm64 | 14.2.0-19
cpp-aarch64-linux-gnu | arm64 | 4:14.2.0-1
dash | arm64 | 0.5.12-12
debconf | all | 1.5.91
debian-archive-keyring | all | 2025.1
debianutils | arm64 | 5.23.2
diffutils | arm64 | 1:3.10-4
dpkg | arm64 | 1.22.22
dpkg-dev | all | 1.22.22
fakeroot | arm64 | 1.37.1.1-1
findutils | arm64 | 4.10.0-3
flex | arm64 | 2.6.4-8.2+b4
g++ | arm64 | 4:14.2.0-1
g++-14 | arm64 | 14.2.0-19
g++-14-aarch64-linux-gnu | arm64 | 14.2.0-19
g++-aarch64-linux-gnu | arm64 | 4:14.2.0-1
gcc | arm64 | 4:14.2.0-1
gcc-14 | arm64 | 14.2.0-19
gcc-14-aarch64-linux-gnu | arm64 | 14.2.0-19
gcc-14-base | arm64 | 14.2.0-19
gcc-aarch64-linux-gnu | arm64 | 4:14.2.0-1
glslang-tools | arm64 | 15.1.0+1.4.309.0-1
grep | arm64 | 3.11-4+b1
gzip | arm64 | 1.13-1
hostname | arm64 | 3.25
init-system-helpers | all | 1.69~deb13u1
libacl1 | arm64 | 2.3.2-2+b1
libalgorithm-diff-perl | all | 1.201-1
libalgorithm-diff-xs-perl | arm64 | 0.04-9
libalgorithm-merge-perl | all | 0.08-5
libapt-pkg7.0 | arm64 | 3.0.3
libasan8 | arm64 | 14.2.0-19
libatomic1 | arm64 | 14.2.0-19
libattr1 | arm64 | 1:2.5.2-3
libaudit-common | all | 1:4.0.2-2
libaudit1 | arm64 | 1:4.0.2-2+b2
libbinutils | arm64 | 2.44-3
libblkid1 | arm64 | 2.41-5
libbz2-1.0 | arm64 | 1.0.8-6
libc-bin | arm64 | 2.41-12+deb13u3
libc-dev-bin | arm64 | 2.41-12+deb13u3
libc6 | arm64 | 2.41-12+deb13u3
libc6-dev | arm64 | 2.41-12+deb13u3
libcap-ng0 | arm64 | 0.8.5-4+b1
libcap2 | arm64 | 1:2.75-10+deb13u1+b1
libcc1-0 | arm64 | 14.2.0-19
libcrypt-dev | arm64 | 1:4.4.38-1
libcrypt1 | arm64 | 1:4.4.38-1
libctf-nobfd0 | arm64 | 2.44-3
libctf0 | arm64 | 2.44-3
libdb5.3t64 | arm64 | 5.3.28+dfsg2-9
libdebconfclient0 | arm64 | 0.280
libdpkg-perl | all | 1.22.22
libdrm-amdgpu1 | arm64 | 2.4.124-2
libdrm-common | all | 2.4.124-2
libdrm-dev | arm64 | 2.4.124-2
libdrm-etnaviv1 | arm64 | 2.4.124-2
libdrm-freedreno1 | arm64 | 2.4.124-2
libdrm-nouveau2 | arm64 | 2.4.124-2
libdrm-radeon1 | arm64 | 2.4.124-2
libdrm-tegra0 | arm64 | 2.4.124-2
libdrm2 | arm64 | 2.4.124-2
libexpat1 | arm64 | 2.7.1-2
libfakeroot | arm64 | 1.37.1.1-1
libffi8 | arm64 | 3.4.8-2
libfile-fcntllock-perl | arm64 | 0.22-4+b4
libfl-dev | arm64 | 2.6.4-8.2+b4
libfl2 | arm64 | 2.6.4-8.2+b4
libgcc-14-dev | arm64 | 14.2.0-19
libgcc-s1 | arm64 | 14.2.0-19
libgdbm-compat4t64 | arm64 | 1.24-2
libgdbm6t64 | arm64 | 1.24-2
libgmp10 | arm64 | 2:6.3.0+dfsg-3
libgomp1 | arm64 | 14.2.0-19
libgpm2 | arm64 | 1.20.7-11+b2
libgprofng0 | arm64 | 2.44-3
libhogweed6t64 | arm64 | 3.10.1-1
libhwasan0 | arm64 | 14.2.0-19
libisl23 | arm64 | 0.27-1
libitm1 | arm64 | 14.2.0-19
libjansson4 | arm64 | 2.14-2+b3
liblastlog2-2 | arm64 | 2.41-5
liblocale-gettext-perl | arm64 | 1.07-7+b1
liblsan0 | arm64 | 14.2.0-19
liblz4-1 | arm64 | 1.10.0-4
liblzma5 | arm64 | 5.8.1-1+deb13u1
libmd0 | arm64 | 1.1.0-2+b1
libmount1 | arm64 | 2.41-5
libmpc3 | arm64 | 1.3.1-1+b3
libmpfr6 | arm64 | 4.2.2-1
libncursesw6 | arm64 | 6.5+20250216-2
libnettle8t64 | arm64 | 3.10.1-1
libpam-modules | arm64 | 1.7.0-5
libpam-modules-bin | arm64 | 1.7.0-5
libpam-runtime | all | 1.7.0-5
libpam0g | arm64 | 1.7.0-5
libpciaccess-dev | arm64 | 0.17-3+b3
libpciaccess0 | arm64 | 0.17-3+b3
libpcre2-8-0 | arm64 | 10.46-1~deb13u1
libperl5.40 | arm64 | 5.40.1-6
libpkgconf3 | arm64 | 1.8.1-4
libpython3-stdlib | arm64 | 3.13.5-1
libpython3.13-minimal | arm64 | 3.13.5-2+deb13u3
libpython3.13-stdlib | arm64 | 3.13.5-2+deb13u3
libreadline8t64 | arm64 | 8.2-6
libseccomp2 | arm64 | 2.6.0-2
libselinux1 | arm64 | 3.8.1-1
libsframe1 | arm64 | 2.44-3
libsmartcols1 | arm64 | 2.41-5
libsqlite3-0 | arm64 | 3.46.1-7+deb13u1
libssl3t64 | arm64 | 3.5.6-1~deb13u2
libstdc++-14-dev | arm64 | 14.2.0-19
libstdc++6 | arm64 | 14.2.0-19
libsystemd0 | arm64 | 257.13-1~deb13u1
libtinfo6 | arm64 | 6.5+20250216-2
libtsan2 | arm64 | 14.2.0-19
libubsan1 | arm64 | 14.2.0-19
libudev1 | arm64 | 257.13-1~deb13u1
libuuid1 | arm64 | 2.41-5
libxxhash0 | arm64 | 0.8.3-2
libyaml-0-2 | arm64 | 0.2.5-2
libzstd1 | arm64 | 1.5.7+dfsg-1
linux-libc-dev | all | 6.12.94-1
m4 | arm64 | 1.4.19-8
make | arm64 | 4.4.1-2
mawk | arm64 | 1.3.4.20250131-1
media-types | all | 13.0.0
meson | all | 1.7.0-1
ncurses-base | all | 6.5+20250216-2
ncurses-bin | arm64 | 6.5+20250216-2
netbase | all | 6.5
ninja-build | arm64 | 1.12.1-1+b1
openssl | arm64 | 3.5.6-1~deb13u2
openssl-provider-legacy | arm64 | 3.5.6-1~deb13u2
patch | arm64 | 2.8-2
perl | arm64 | 5.40.1-6
perl-base | arm64 | 5.40.1-6
perl-modules-5.40 | all | 5.40.1-6
pkg-config | arm64 | 1.8.1-4
pkgconf | arm64 | 1.8.1-4
pkgconf-bin | arm64 | 1.8.1-4
python3 | arm64 | 3.13.5-1
python3-autocommand | all | 2.2.2-3
python3-inflect | all | 7.3.1-2
python3-jaraco.context | all | 6.0.1-1+deb13u1
python3-jaraco.functools | all | 4.1.0-1
python3-jaraco.text | all | 4.0.0-1
python3-mako | all | 1.3.9-1
python3-markupsafe | arm64 | 2.1.5-1+b4
python3-minimal | arm64 | 3.13.5-1
python3-more-itertools | all | 10.7.0-1
python3-packaging | all | 25.0-1
python3-pkg-resources | all | 78.1.1-0.1
python3-setuptools | all | 78.1.1-0.1
python3-typeguard | all | 4.4.2-1
python3-typing-extensions | all | 4.13.2-1
python3-yaml | arm64 | 6.0.2-1+b2
python3-zipp | all | 3.21.0-1
python3.13 | arm64 | 3.13.5-2+deb13u3
python3.13-minimal | arm64 | 3.13.5-2+deb13u3
readline-common | all | 8.2-6
rpcsvc-proto | arm64 | 1.4.3-1+b1
sed | arm64 | 4.9-2+deb13u1
spirv-tools | arm64 | 2025.1~rc1-1
sq | arm64 | 1.3.1-2+b2
sqv | arm64 | 1.3.0-3+b2
sysvinit-utils | arm64 | 3.14-4
tar | arm64 | 1.35+dfsg-3.1
tzdata | all | 2026b-0+deb13u1
util-linux | arm64 | 2.41-5
xz-utils | arm64 | 5.8.1-1+deb13u1
zlib1g | arm64 | 1:1.3.dfsg+really1.3.1-1+b1
```

## Preserved manually extracted DEBs

```text
Package: libffi-dev | Architecture: arm64 | Version: 3.4.8-2 | sha256=55f6d389cc954407cdba6e4ba5e7039dd2042d2ca8929d6f5eb49d6b97ba92de | analysis/gpu68-wayland-egl-init/debs-libffi/libffi-dev_3.4.8-2_arm64.deb
Package: libwayland-client0 | Architecture: arm64 | Version: 1.23.1-3 | sha256=8abdc649e46470548c545f827e16f52e1bc16d05d4a3794e6dedb2d74ce58c9a | analysis/gpu68-wayland-egl-init/debs-runtime/libwayland-client0_1.23.1-3_arm64.deb
Package: libwayland-cursor0 | Architecture: arm64 | Version: 1.23.1-3 | sha256=824c1ca46458530a670bfd003f1c083e66e395e1800c294a22af38641ccdc11a | analysis/gpu68-wayland-egl-init/debs-runtime/libwayland-cursor0_1.23.1-3_arm64.deb
Package: libwayland-dev | Architecture: arm64 | Version: 1.23.1-3 | sha256=0f93e9f114479730d172c244289b983959159d22c1eeb954bead49a4e6072af2 | analysis/gpu68-wayland-egl-init/debs/libwayland-dev_1.23.1-3_arm64.deb
Package: libwayland-egl-backend-dev | Architecture: arm64 | Version: 1.23.1-3 | sha256=9beef43782e387967958164714a78d6190ce3db8418ea8514351e4f2fed118ec | analysis/gpu68-wayland-egl-init/debs/libwayland-egl-backend-dev_1.23.1-3_arm64.deb
Package: libwayland-egl1 | Architecture: arm64 | Version: 1.23.1-3 | sha256=fe01fb2f3c5d5b54784563d9826fa505fab61dc30333d71343352bddd3812b18 | analysis/gpu68-wayland-egl-init/debs-runtime/libwayland-egl1_1.23.1-3_arm64.deb
Package: libwayland-server0 | Architecture: arm64 | Version: 1.23.1-3 | sha256=062702d57cf07b42ab7f0fa1aac8bc3f605eb47f2f0b9ecb1614674140d79f1b | analysis/gpu68-wayland-egl-init/debs-runtime/libwayland-server0_1.23.1-3_arm64.deb
Package: wayland-protocols | Architecture: all | Version: 1.44-1 | sha256=3bbe8044f92fbf6822039064764d1d4b3a1dbb931083ab40ea189c9fd1d7a04f | analysis/gpu68-wayland-egl-init/debs-protocols/wayland-protocols_1.44-1_all.deb
```

## Historical metadata hashes

- `var/lib/dpkg/status`: `65753ac7497fefaecba14eb794ae3f87800103fef57616c0c53af370cd3fde27`
- `var/log/apt/history.log`: `f1673314ef28bf75509156a38d83279a8afe4739fca224acdab8b9665d0cbd62`
- `var/log/apt/eipp.log.xz`: `9c5c2bead4548500bbe720a1b98804f6700c732effb5702c3f1954638784b5bd`

## Reconstruction boundary

The exact command that originally created the 85-package pre-existing base is no longer present in the surviving logs. Its final package state is preserved above. The later GPU68 transaction and all manually extracted Wayland/libffi development payloads are directly evidenced by surviving artifacts.
