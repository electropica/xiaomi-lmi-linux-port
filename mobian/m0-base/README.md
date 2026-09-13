# Mobian M0 base reconstruction

The historical M0 working data lives outside the canonical repository at:

/home/linuxagent/pmos-d-repro-01/Mobian-M0

The canonical scripts under:

/home/linuxagent/pmos-d-repro-01/github-export/mobian

accept the `MOBIAN_M0_BASE` environment variable to operate on that working tree.

To reconstruct `rootfs-final-330`, use:

MOBIAN_M0_BASE=/home/linuxagent/pmos-d-repro-01/Mobian-M0 /home/linuxagent/pmos-d-repro-01/github-export/mobian/build-unshare-330.sh

The build script creates:

/home/linuxagent/pmos-d-repro-01/Mobian-M0/rootfs-final-330

Required inputs currently retained under `Mobian-M0` include:

- manifests/m0-minimal-closure.tsv
- local-repo-330
- keyrings-330
- downloads
- tools

`rootfs-final-330` is therefore a generated artefact, not a canonical source input.
