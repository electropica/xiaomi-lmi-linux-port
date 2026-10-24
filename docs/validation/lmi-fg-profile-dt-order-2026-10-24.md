# Fuel-gauge lookup depends on board-tree order — October 24, 2026

## Confirmed source and retained-input facts

The exact Qualcomm 4.19 driver resolves its battery container using `of_find_node_by_name(fg->dev->of_node, "qcom,battery-data")`. The OF implementation is a depth-first global traversal beginning AFTER the supplied node; it is not a subtree lookup and it consumes the supplied node reference. The phandle-first candidate instead uses the gauge's `qcom,battery-data` property, with a correctly referenced legacy fallback.

Source revision is a5b3099017ae581aae8bf597b2f9c8c765026af1. Audited files: drivers/of/base.c SHA256 8ad80d55892cf01086c4bd470ee1bf692dc3139fb6531a953a016566dc6b6cff; drivers/of/fdt.c 24e07b0f37e6cfd2044ad574ec0d25e06f778bb0265787113187d50244533262; include/linux/of.h 3bec7eeffd71459cddd18b5ba03355a657cacfd9f7889e4b9c5ce3d9a3145aa6. Unflattening restores sibling order to match the flat tree.

For the Mobian DTB extracted from the exact qualified permanent menu be9841c76cbe34d0c72606c47877f99582aee224144744349a9e78d15cfd0a94 (component 6452f7bc7f12d25c1717ebfba9a5566a1001adc60b8f0652bef6309a15c0b56b), replay selects `/vendor/qcom,battery-data`. This container has no j11sun profile. The gauge phandle instead resolves to `/soc/qcom,battery-data`, which contains j11sun_4700mah. The current boot FDT gives the same two resolutions. The retained ABL-populated Mobian tree and direct Lineage tree both resolve the legacy search to `/soc/qcom,battery-data`. These facts explain why assuming identical lookup behavior across boot routes is incorrect.

The live October 7 kernel currently publishes Unknown Battery/design 0. A historical capture with the same full version string publishes design 4700000; a separate historical boot capture publishes the j11sun name. Those two historical captures are not silently joined, and version-string identity alone does not establish binary/DT identity. Authentication readiness and its retries remain separate from the container-order defect. A later 'j11sun found' message can originate from another consumer and does not itself prove that the FG work retried successfully.

## Controlled diagnostic preparation, not an installed change

The proposed missing old-kernel/published-profile comparison cannot be obtained merely by assuming three ordinary reboots will change an unchanged tree. A new offline diagnostic moves only the passive profile subtree after the SPMI subtree. Every property, node path, phandle and all other node ordering remain unchanged; the old lookup then resolves the intended container. Kernel/initrd/cmdline/identity bundle hashes are retained. The normal firmware build must regenerate its outer CRC lock; a diagnostic image cannot be created by casually replacing bytes in the qualified image.

See kernel/diagnostics/power/fg-dt-order-candidate/README.md for the guarded operator-only recipe. Initial preparation and locked-input preflight passed without compiling. Subsequently, a diagnostic image was built: SHA256 7425c00bffefb677f52d76fa360c024a0c4b5d6e58312f33350b4eb8928cb9ff, 81,051,648 bytes. Its actual bundle CRC is1662599447 and all four non-DTB components match the qualified reference. No flash, reboot or hardware qualification has been performed for this candidate. The installed menu remains qualified for its previously recorded OS-startup behavior. This new profile-recognition limitation does not retroactively establish a battery cause.

## Battery evidence limits

Independent replay confirms the reported raw-counter rate 24.097906116 units/s for one 300.731522698-second suspended bracket, against reference median 45.620506441 units/s over 80 brackets. This is a difference in reported counter progression, not a physical-current measurement. 24.10 is outside a literal 25–30 interval. One bracket and co-varying kernel/driver/history/userspace cannot establish electrical causality, profile cost or project closure. A future controlled state comparison may discriminate hypotheses; it has not yet occurred.

## Post-build isolation audit and correction

MiniMax identified shared intermediate contamination: the diagnostic build had replaced the parent output's lmi-outer-mobian.bin/json, while the qualified image and reference manifest remained intact. The original packer's self-consistency check did not establish reference identity. Codex independently confirmed this and moved the verified diagnostic outputs into output/fg-dt-order-candidate/, restoring the parent reference bundle/metadata/CRC header from the qualified image. The diagnostic raw firmware input was moved out of the shared parent as well. No files were deleted and both final image hashes were preserved.

Future diagnostic builds isolate all intermediate/output/log paths in that child directory and mount the reference parent read-only. The reference packer also refuses a different existing reference image. Tests execute the actual packer helper and inspect generated shell paths; a full CLI replay with real self-consistent diagnostic inputs was refused before replacing a temporary copy of the qualified image or creating a reference manifest. Documentation now records the built candidate, separately from pending hardware validation. These host-only corrections do not alter the existing diagnostic firmware and do not require recompiling it.
