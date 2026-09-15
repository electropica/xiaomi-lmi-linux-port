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

The historical entry point requires manifests, exact local packages, keyrings
and supporting tools. These inputs are not all retained under `base/files/`;
the current checkout alone cannot run that historical reconstruction.

`rootfs-final-330` is a generated artifact, not a canonical source input.

The first stage for acquiring a new public-repository M0 closure is documented
in [M0-ACQUISITION.md](M0-ACQUISITION.md). It does not run the M0 builder or
change the BASE_RAW/M1 workflow.
