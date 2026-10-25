# Closed-drawer preview candidate

Baseline: accepted drawerscroll1+irqnames1. The source proposal moves the activity carousel into the applications page while keeping the outer app-grid allocation stable. The original MiniMax proposal passed28 source tests but omitted the template-child binding; an actual GTK3 control proved lookup returned NULL without it. This candidate registers that child, corrects the inaccurate packing/vexpand explanation, and removes explicit expansion from the empty preview wrapper (the initial proposal reserved324px with zero apps).

Independent GTK3/Handy runs against the transformed real UI with synthetic cards show stable app-grid geometry in12 settled states (closed/open/closed again, zero through3 apps), correct mapping only in the open drawer, and<=1px empty strip. These are real GTK checks, not compositor/input/user acceptance. Source callbacks and Phosh CSS are not exercised by this harness. Actual gestures, favorite placement and first-scroll latency remain to be tested on the handset. The proposal's historical-rejection explanations remain hypotheses where no runtime trace exists.

The only modified production files are app-grid.c (binding only), overview.c (reparenting and parent expansion) and app-grid.ui (preview container). Battery policy, existing swipe arbitration, home and DnD code, GSD and accepted private-FBO Phoc are hash-guarded/untouched. Do not change the IRQ-name fix or kernel/profile.

Default preflight:

    python3 userspace/phosh/closed-drawer-preview-candidate/build-packages.py

Operator build:

    sudo python3 /home/linuxagent/xiaomi-lmi-linux-port/userspace/phosh/closed-drawer-preview-candidate/build-packages.py --execute

Normal package tests stay enabled. Marker CLOSED_DRAWER_PREVIEW_PACKAGES_BUILT. Manifest rootfs/build/lmi-closed-drawer-preview1-build-result.json. No automatic phone install or image/kernel build. Rescue packages are the currently accepted IRQ-name versions, not older fixed-number policies.
