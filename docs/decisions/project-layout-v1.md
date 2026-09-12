# Project layout v1: migration decision record

Status: approved target layout; documentation phase only. No existing path has
been moved, renamed, deleted, or made obsolete by this document.

## Repository and local data

`/home/linuxagent/pmos-d-repro-01/github-export` is the canonical Git
repository. It records build recipes, patches, configuration, manifests,
decisions, and test evidence. Large source checkouts, sysroots, build trees,
rootfs trees, images, caches, and mutable tool state remain local data outside
Git. The separate Git directory at `/home/linuxagent/pmos-d-repro-01/.git` is
temporary and must remain untouched until a separate migration decision.

The paths `github-export/pmaports` and `github-export/weston` are ordinary
directories tracked directly by the canonical repository. They are not the
same as autonomous source checkouts elsewhere in the workspace, including
`/home/linuxagent/pmos-d-repro-01/pmaports`; an independent checkout keeps its
own Git history and must not be moved or rewritten implicitly.

## Target logical layout

```text
project/
  prerequisites/
    packages/ toolchains/ sysroots/ firmware/ sources/ docs/
  repos/
  builds/
    kernel/dev/ kernel/build/
    display/dev/ display/build/
    wifi/dev/ wifi/build/
    gpu/dev/ gpu/build/
  integration/dev/ integration/build/
  images/active/boot/ images/active/rootfs/
  images/candidates/boot/ images/candidates/rootfs/ images/archived/
  scripts/common/ scripts/helpers/
  docs/status/ docs/decisions/ docs/tests/
  state/pmbootstrap/ state/caches/ state/mounts/
  archive/experiments/ archive/snapshots/ archive/legacy-repos/
```

Until the canonical repository's physical placement is separately resolved,
this is a logical classification, not permission to duplicate or relocate the
active stack. Version-controlled definitions belong in `github-export`;
large local outputs belong in corresponding workspace data areas. Each active
build must have one manifest connecting its tracked recipe to its local source,
toolchain, sysroot, outputs, and hashes.

## Dev and build rules

`dev/` holds edited source, patches, work-in-progress configuration, and small
component-specific tools. `build/` holds the exact build recipe, options,
dependency manifest, logs worth preserving, outputs, and, only when useful,
the local build tree. Git tracks recipes and provenance, not generated rootfs
trees, flashable images, caches, or build trees.

Existing Meson/Ninja build trees encode absolute source, sysroot, and output
paths. Do not move them directly. Recreate each new build in its new location
from a reviewed source snapshot, cross-file, dependency set, and build recipe;
then compare output hashes and ABI before changing any active reference.

GPU72 currently depends on GPU69 Mesa sources and GPU68 cross-build inputs.
Neither GPU68 nor GPU69 may be archived until GPU72 has a self-contained,
verified source and build manifest and a new build reproduces the required
artifacts. The historical `gpu71-mobian-gles2-integration` name remains an
active GPU72 path for now.

An `active` manifest must identify immutable artifact paths, SHA-256 hashes,
paired boot/rootfs UUIDs, and validation evidence. Names such as `final`,
`complete`, or `current` are not proof of active status. Keep historical names
and artifacts unchanged until a separately authorized migration verifies any
replacement.
