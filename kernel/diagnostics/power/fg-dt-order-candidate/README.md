# FG profile lookup: order-only diagnostic menu candidate

This is a diagnostic recipe, not the active boot reference or a proven battery fix. It does not boot, flash or contact a handset. The qualified installed menu and installer remain unchanged.

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

Output is separately named `boot-lmi-fg-dt-order-test.img`, with `fg-dt-order-artifact-manifest.json`. The qualified `boot-lmi-outer-dual-extent-test.img` is retained. No installer is repinned. Do not flash the candidate. After host artifact review, a separately guarded temporary trial would first check normal UI, original kernel identity, intended DT resolution and published BMS profile. Only an observed valid state could justify a later 30–40 minute counter comparison. Neither three repeated blind reboots nor a forced profile/SRAM write is part of this recipe.

Host results: real locked-input patch/repack preflight passes; property and node invariants pass; changed, truncated and already-reordered inputs are refused. No firmware compilation or hardware qualification has occurred. Physical energy and the cause of the residual battery drain remain unresolved.
