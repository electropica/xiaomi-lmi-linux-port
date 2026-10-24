# FG profile lookup: order-only diagnostic menu candidate

This is a diagnostic recipe, not the active boot reference or a proven battery fix. It does not boot, flash or contact a handset. The qualified installed menu and installer remain unchanged.

A diagnostic image was built after the initial publication: SHA256 `7425c00bffefb677f52d76fa360c024a0c4b5d6e58312f33350b4eb8928cb9ff`, 81,051,648 bytes. Its manifest and bundle components pass host checks. A subsequent guarded temporary launch and read-only return confirmed Mobian startup on the original October7 kernel, the intended profile publication and the unchanged installed fallback; UI acceptance and battery observation remain pending. The original build used shared intermediate filenames. Those verified diagnostic files have since been moved into `output/fg-dt-order-candidate/`, and the reference outer bundle restored from the exact qualified image. The host-only isolation corrections do not modify that built image, so another firmware build is not required merely for this correction.

The old fuel-gauge driver searches the global Device Tree after its own node by name. In the qualified menu's Mobian DTB, that selects `/vendor/qcom,battery-data`; the intended j11sun profile is instead at `/soc/qcom,battery-data`, which the gauge's explicit phandle already references. A retained ABL-populated tree has the opposite relevant order and selects the correct container. Authentication readiness does not change these static tree relationships. The driver phandle-first patch remains the appropriate robust code fix, but changing the kernel and driver path together confounds the proposed battery comparison.

`reorder-dtb.py` moves only the complete, passive `/soc/qcom,battery-data` subtree after the SPMI subtree, retaining its parent path. The exact old menu DTB is required: input `6452f7bc7f12d25c1717ebfba9a5566a1001adc60b8f0652bef6309a15c0b56b`; output `12088ff3ebf5f22952e63f9699b20708e7ccae6ac311ccc079cb23ff1a6f96c1`. All 4017 nodes, every property's bytes, header, size, phandle target and the relative order of all other nodes are checked unchanged. The moved subtree must contain no compatible property. The candidate changes which container the old name-based lookup encounters first. This is source/FDT validation, not a live kernel outcome; effects on other order-dependent consumers remain a limitation.

`build-menu.py` derives an isolated content-addressed recipe from the existing resetguard/dual-extent menu builder. It uses the DTB extracted from exact qualified image `be9841c76cbe34d0c72606c47877f99582aee224144744349a9e78d15cfd0a94`, not an arbitrary runtime dump or freshly overlaid tree. A fresh overlay replay can assign six audio-node phandles differently; those unrelated changes are excluded by preserving the qualified DTB. All four non-DTB Mobian bundle components are checked unchanged. The normal outer-lock generation recompiles the new CRC into the firmware; no CRC correction padding, lock bypass or binary constant patch is used.

Preflight only (requires read access to protected retained inputs):

```sh
sudo python3 /home/linuxagent/xiaomi-lmi-linux-port/kernel/diagnostics/power/fg-dt-order-candidate/build-menu.py
```

Operator-only menu firmware build, with no kernel or rootfs rebuild:

```sh
sudo python3 /home/linuxagent/xiaomi-lmi-linux-port/kernel/diagnostics/power/fg-dt-order-candidate/build-menu.py --build
```

All diagnostic outputs, including intermediate blobs, raw firmware, manifests and build.log, are confined to `/home/linuxagent/lmi-boot-menu-build/output/fg-dt-order-candidate/`. Inside the build namespace that child directory is the writable `/output`; the parent reference directory is separately mounted read-only at `/qualified-output`. The final image is `boot-lmi-fg-dt-order-test.img`, with `fg-dt-order-artifact-manifest.json`. The qualified parent `boot-lmi-outer-dual-extent-test.img` is retained. The reference packer additionally refuses to replace an existing reference image with different bytes. No installer is repinned. Do not flash the candidate. After host artifact review, a separately guarded temporary trial would first check normal UI, original kernel identity, intended DT resolution and published BMS profile. Only an observed valid state could justify a later 30–40 minute counter comparison. Neither three repeated blind reboots nor a forced profile/SRAM write is part of this recipe.

Host results: real locked-input patch/repack preflight passes; property and node invariants pass; changed, truncated and already-reordered inputs are refused. Output-path and packer controls run with `test-output-isolation.py`; a full CLI negative replay of the reference packer with real diagnostic intermediates refused the overwrite and preserved a copy of the qualified image. Firmware has been built, but no new compilation was run for this isolation correction and the temporary runtime checks qualify only Mobian startup and profile publication, not battery behavior or the other menu entries. A future preflight reports only whether it compiled in that invocation, separately from the presence of the existing candidate. Physical energy and the cause of the residual battery drain remain unresolved.

## Native Windows temporary launch

The operator tool `temporary-boot-windows.py` defaults to a host-only plan. Put the reviewed diagnostic image in Downloads as `lmi-fg-dt-order-test-20261024.img`, the unchanged qualified reference as `lmi-menu-outer-dual-extent-20261023.img`, and native platform-tools/fastboot.exe in the same Downloads directory. Both complete image hashes and boot headers are checked. No device command runs without --execute.

After manually entering Fastboot with the cable connected, `python -B temporary-boot-windows.py --execute` checks exactly one device, product lmi and the expected boot/mobian partition sizes, then requests only a temporary RAM boot. It performs no flash, automatic OS reboot or discharge collection. Leave the menu countdown on Mobian. Launch success is recorded separately from runtime/hardware validation. Receipts are private and ignored by Git. `test-temporary-boot-guards.py` checks that five invalid device/product/size cases cannot request a boot and that a valid case requests exactly one RAM boot.

Before launch, a read-only baseline confirmed that the installed boot prefix still matches the qualified menu, the root is the dedicated Mobian partition, no known collector process or RTC alarm was observed, and the current gauge still publishes Unknown Battery/design0 with the vendor-container legacy lookup. After launch, check the new boot, same kernel, unchanged installed fallback, intended live-tree resolution and final j11sun/design4700000 state, then obtain operator UI confirmation. No discharge observation starts automatically. Initial authentication warnings may precede successful publication and must be evaluated in the complete boot sequence.
