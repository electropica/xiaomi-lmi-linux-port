# Mobian M0 base reconstruction

The current M0 reconstruction data is stored under:

    /home/linuxagent/ProjetMobian/base/files

The reconstruction scripts are stored under:

    /home/linuxagent/ProjetMobian/base/scripts

The scripts use `base/files/` as `MOBIAN_M0_BASE` by default. The environment variable remains available when an alternate working tree is required.

The main reconstruction entry point is:

    /home/linuxagent/ProjetMobian/base/scripts/build-unshare-330.sh

With the default layout, the generated rootfs is created under:

    /home/linuxagent/ProjetMobian/base/files/rootfs-final-330

Required reconstruction inputs retained under `base/files/` include the manifests, local repository data, keyrings, downloads and supporting tools used by the M0 recipe.

`rootfs-final-330` is a generated artifact, not a canonical source input.
