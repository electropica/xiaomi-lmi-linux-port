# Dual-boot artifacts built; installation pending — October 21, 2026

The operator completed the maintained full-image build, including native home
drag/drop and the complete camera bundle. The build log reports both ext4
checks passing and BUILD_COMPLETE. The image filesystem identities match the
pinned boot. No target installation, repartition or Android boot was performed.

Finalization initially failed with PermissionError: output/ was intentionally
root-owned by the full-image builder, while prepare.py ran as the normal user.
The recipe now delegates its final step to finish.sh, which checks existing
image identities and elevates only the artifact writer. It does not chown or
chmod the output tree and does not repeat the full build. That finalizer was
then run successfully; only the small boot artifact and text manifests were
generated. The full-image hashes were independently read back unchanged:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| Complete raw image | 4551868416 | `371b029d328a293439a9ee07a1d4099092fe8df5a85799a595f008d506879185` |
| Complete Android sparse image | 3660075304 | `f803fae6954c4d5e13cfa77815640a895d3d051d8a56db7813c75edce2bd3f8e` |
| Dedicated Mobian boot | 54652928 | `75bb65facbd4146d4a1e668039ef52433ef90c2b6bdb07f2c59980caf3191374` |

The kernel SHA-256 remains
`87c53d33202d4607591fa0ba6d2bf091dc2dfc4673a3326436740a1f0e7bae6a`,
and DTB SHA-256 remains
`74edf0671376aa58df50897766500d04840af13d4bf27d0f78598ab7343d02f9`.
Only the initramfs storage-discovery function changes. The prior fourteen
host tests, fifteen complete-image staging tests and dependency-staging check
remain distinct from unperformed target validation.

The [recipe and installation gates](../../build/dualboot/README.md) still apply:
the sparse image is intended for a future dedicated 16 GiB `mobian` partition,
**not Android userdata**. Current Mobian is unchanged. The proposed GPT migration
requires a fresh recovery check and a separate reviewed installation procedure.
The PC selector remains locked; neither OS has yet booted in this arrangement.
No battery-saving claim follows from producing these artifacts. The already
armed pre-installation passive observation remains undisturbed while unplugged.
