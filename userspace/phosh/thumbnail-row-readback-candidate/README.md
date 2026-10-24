# GLES thumbnail row-readback candidate

The installed linear-modifier backport did not fix striped running-app cards on lmi. A fresh screenshot after the RTC test reproduces stripes in all three cards while surrounding icons and output capture remain readable. No source-level cause is claimed proven.

This candidate restricts the workaround to GLES2 ARGB8888 per-view thumbnails. A staging row pitch of width*4+4 selects the existing wlroots0.18 GLES row-by-row read path, then copies exactly width*4 bytes per row into the client-provided stride. Other renderers/formats use the original call. Output rendering, GPU selection, panel, kernel, battery policy, Phosh drawer code and qualified cursor DnD are untouched. The linear modifier is retained.

This tests the one-call readback path as a candidate; it cannot repair an already corrupted render target or a different upload bug. It adds temporary thumbnail-sized memory and multiple GPU readbacks, so real thumbnail appearance and overview responsiveness must both pass before acceptance. Do not claim a fixed GPU row pitch as observed merely from stripes.

The exact helper passed96 layouts (odd/aligned widths, heights, tight/padded destination rows), guard-byte checks, allocation/read failures, invalid dimensions/overflow and software/other-format fallbacks under ASan+UBSan. These are native host controls with a mock pixel reader, not real GPU or package qualification. `test-readback.py` replays them. The helper included in the patch must remain byte-identical to thumbnail-readback-helper.inc.

`sudo python3 userspace/phosh/thumbnail-row-readback-candidate/build-packages.py --execute` is operator-run and builds only Phoc in the existing locked arm64 chroot, private mount namespace, no phone contact or installation. Default invocation verifies source/changelog/DnD pins, scratch-patch output and the installed-baseline rollback package. The standard package test suite remains enabled. No kernel or full image build is required.

After build, use guarded package verification and retain current +thumblinear1 rollback. A compositor restart will be needed for acceptance; do not casually restart the full Mobian graphical wrapper because a prior session teardown caused a handset reboot and would lose the temporary battery kernel. Plan the activation separately. Check clean miniatures, launch/close, DnD, and responsiveness. Current status: prepared and host-tested, not built or installed, not a verified device fix.

Primary API contract: https://wlroots-38153e.pages.freedesktop.org/wlr/render/wlr_texture.h.html (`stride` in bytes, destination offsets). Branch choice verified against the retained wlroots0.18 GLES2 texture implementation, not inferred from API documentation alone. Current Phoc render source before/after pins are in build-packages.py.
