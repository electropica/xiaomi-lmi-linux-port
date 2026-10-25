# Drawer search improvements candidate

Operator-only incremental Phosh package recipe. No phone access.
Baseline is the accepted IRQ-name + drawerpreview1 version; normal
power policy, home8 drag-and-drop, Phoc FBO and GSD sources are pinned.

Changes: Enter activates folders as well as individual app results.
A French empty-result hint updates on searches and model changes.
The five-argument ordinary items-changed callback fixes a blocking ABI
mistake in the original external proposal. Explicit post-search refresh
does not depend on a model-membership change.

Host checks: patch forward/reverse application and source hashes pass;
XML identifiers unique and template binding matches. A native GObject
signal-marshalling reproduction rejects the original callback and accepts
the corrected callback on add/remove. This is NOT GTK or phone acceptance.

Default command performs preflight only:
python3 userspace/phosh/drawer-search-candidate/build-packages.py

Operator build:
sudo python3 /home/linuxagent/xiaomi-lmi-linux-port/userspace/phosh/drawer-search-candidate/build-packages.py --execute

The established incremental builder stages and verifies the patch in a
temporary copy, then updates the package build tree on explicit --execute.
It does not alter canonical source outside this recipe or contact the phone.
Both accepted rollback packages must already exist. Shared package locks,
private mount namespace and all Debian tests remain enabled.

No compilation was started by Codex. No kernel or image build, no installation.
Result after operator success:
 /home/linuxagent/phosh-gauge-wake-build/rootfs/build/lmi-drawer-search1-build-result.json

Do not update the complete-image package lock until package and hardware
validation pass. Hardware checks must include search, empty search, clearing,
folder Enter, favourites drag/drop, drawer scroll/close and preview visibility.
