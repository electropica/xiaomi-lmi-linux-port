# Closed-drawer preview candidate

Baseline: accepted drawerscroll1+irqnames1. The source proposal moves the activity carousel into the applications page while keeping the outer app-grid allocation stable. The original MiniMax proposal passed28 source tests but omitted the template-child binding; an actual GTK3 control proved lookup returned NULL without it. This candidate registers that child, corrects the inaccurate packing/vexpand explanation, and removes explicit expansion from the empty preview wrapper (the initial proposal reserved324px with zero apps).

Independent GTK3/Handy runs against the transformed real UI with synthetic cards show stable app-grid geometry in12 settled states (closed/open/closed again, zero through3 apps), correct mapping only in the open drawer, and<=1px empty strip. These are real GTK checks, not compositor/input/user acceptance. Source callbacks and Phosh CSS are not exercised by this harness. Actual gestures, favorite placement and first-scroll latency remain to be tested on the handset. The proposal's historical-rejection explanations remain hypotheses where no runtime trace exists.

The only modified production files are app-grid.c (binding only), overview.c (reparenting and parent expansion) and app-grid.ui (preview container). Battery policy, existing swipe arbitration, home and DnD code, GSD and accepted private-FBO Phoc are hash-guarded/untouched. Do not change the IRQ-name fix or kernel/profile.

Default preflight:

    python3 userspace/phosh/closed-drawer-preview-candidate/build-packages.py

Operator build:

    sudo python3 /home/linuxagent/xiaomi-lmi-linux-port/userspace/phosh/closed-drawer-preview-candidate/build-packages.py --execute

Normal package tests stay enabled. Marker CLOSED_DRAWER_PREVIEW_PACKAGES_BUILT. Manifest rootfs/build/lmi-closed-drawer-preview1-build-result.json. No automatic phone install or image/kernel build. Rescue packages are the currently accepted IRQ-name versions, not older fixed-number policies.

## Accepted closed-drawer previews — 25 October 2026

The incremental Phosh drawerpreview1 package is installed and operator-accepted: running previews are hidden on the closed home page and visible inside the open drawer; favorites remain at the bottom and gestures respond normally. All36 Phosh package tests passed. The actual running binary SHA256 is17f5cb077e08a1e93b13b6a828e69b225d7008e3c3db4faa03e26325b58ea159. Rescue rollback was cancelled after acceptance.

The same temporary kernel/published j11 profile, GSD IRQ-name policy and accepted Phoc private-FBO thumbnail renderer are retained. This is an incremental userspace milestone, not a new full image. Natural gauge-resume/energy validation remains pending. Evidence: userspace/phosh/closed-drawer-preview-candidate/device-acceptance-20261025.json.
