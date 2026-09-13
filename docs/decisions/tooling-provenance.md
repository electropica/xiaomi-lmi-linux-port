# Local tooling provenance

The historical workspace directory `/home/linuxagent/pmos-d-repro-01/tools`
contains reconstructible development tooling and is not a canonical source
input.

## pmbootstrap source checkout

- Repository: https://gitlab.postmarketos.org/postmarketOS/pmbootstrap.git
- Commit: `a72d80ee0101e7fe7b9361b63f3b2f4046ef40a6`
- Historical path: `/home/linuxagent/pmos-d-repro-01/tools/pmbootstrap-src`

## pmbootstrap Python environment

- Package: `pmbootstrap`
- Version: `3.10.1`
- Historical path: `/home/linuxagent/pmos-d-repro-01/tools/pmbootstrap-3.10.1-venv`

## Android mkbootimg checkout

- Repository: https://android.googlesource.com/platform/system/tools/mkbootimg
- Commit: `d2bb0af5ba6d3198a3e99529c97eda1be0b5a093`
- Historical path: `/home/linuxagent/pmos-d-repro-01/tools/android-mkbootimg`

## vmlinux-to-elf

- Package: `vmlinux-to-elf`
- Version: `1.3.5`
- Historical path: `/home/linuxagent/pmos-d-repro-01/tools/vmlinux-to-elf-py`
- This was a local Python package installation with dependencies, not a unique source tree.

No active reference to these four historical tool directories was found in
`github-export`, the workspace `scripts`, or the workspace `docs` during the
cleanup audit.
