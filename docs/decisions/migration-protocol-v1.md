# Workspace migration protocol v1

This protocol governs future changes to the local workspace at
`/home/linuxagent/pmos-d-repro-01`. It does not authorize a migration by
itself. The canonical Git repository remains
`/home/linuxagent/pmos-d-repro-01/github-export`. The separate root Git
directory, `/home/linuxagent/pmos-d-repro-01/.git`, is temporary and must not
be removed, transformed, or modified without a specific decision.

## General gates

1. Begin with a read-only map of each candidate: role, size, file type,
   current references, absolute paths, symlinks, Git ownership, and known
   dependencies. Record the baseline before changing a path.
2. Leave active items and items with unknown dependencies in place. In
   particular, GPU68, GPU69, GPU71, and GPU72 remain protected while GPU72
   still depends on historical GPU69 sources and GPU68 build inputs. The
   active GPU72 boot image and rootfs remain at their current paths until a
   separate, explicit migration is validated.
3. Select a method for the data type: copy then verify, recreate from a
   documented recipe, retain temporarily, or archive later. Do not infer
   active or historical status from a directory name.
4. Record source path, destination path, method, version or commit where
   relevant, expected metadata, SHA-256 values, verification result, and
   authorization in a provenance note. Keep the old path usable until the
   replacement is separately accepted.
5. A new copy is not active merely because it exists. Active status requires
   an explicit manifest identifying the selected artifact by hash and its
   validation evidence. Names such as `final`, `complete`, and `current` do
   not establish that status.
6. Any deletion, replacement, or retirement of an old location is a separate
   phase with its own review and authorization. A successful copy does not
   authorize deleting the source.

## Method by data type

For a small, low-risk regular file or coherent file set:

1. Verify the source and confirm that the destination will not overwrite an
   unexpected file.
2. Create only the intended destination directory and copy normally, without
   deleting or renaming the original.
3. Compare each source/copy pair by byte size and SHA-256. Stop on any
   mismatch; do not silently replace or remove either copy.
4. Retain the original during a validation period. Promote the copy to an
   active reference, or archive the original, only by a later decision.

Large trees, rootfs trees, sysroots, flashable images, and autonomous Git
repositories require a tailored procedure before any copy or move. Review
absolute paths, symlinks, hard links, ownership, modes, ACLs, xattrs, sparse
files, device nodes, mount state, Git metadata, and references from other
components as applicable. Verify the properties required by that data type,
not only a top-level size. Do not move an existing Meson/Ninja build tree:
its generated metadata can encode absolute source, sysroot, and build paths.
Recreate it in a new directory from reviewed inputs and compare the result.

The workspace layout and the separation between Git-tracked recipes and
local heavy data are defined in `project-layout-v1.md`. The canonical
repository's `pmaports/` and `weston/` are ordinary tracked directories;
autonomous source repositories elsewhere in the workspace retain their own
Git metadata and require separate treatment.

## Migration pilote Phoc 0.46.0

Phase 2C copied the following Debian Phoc source package files from
`/home/linuxagent/pmos-d-repro-01/analysis/` to
`/home/linuxagent/pmos-d-repro-01/prerequisites/sources/phoc-0.46.0/`:

| File | SHA-256 |
| --- | --- |
| `phoc_0.46.0-1.dsc` | `2b88ce6f84e95e6ab4ba56830443b625f2c1c33a09ee9f05cdbbd65e75ec44a0` |
| `phoc_0.46.0-1.debian.tar.xz` | `920d023291ad37739c048014db2b3fd1d41ca35a715fd459ac35f3530b7e26f5` |
| `phoc_0.46.0.orig.tar.xz` | `862e93ed915ffa7230db3e6fbf80c348f5d36f027e49b69d1b23220239bef899` |

For all three pairs, source and copy sizes and SHA-256 values matched.
`VALIDATION : OK`. The originals remain at their original paths; the copies
have not been designated active or used to replace an existing build input.
