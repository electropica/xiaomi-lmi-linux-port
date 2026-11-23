# Drawer pull-down gesture: bubble-phase candidate

The `+pulldownbubble1` packages were installed on 22 November 2026. On 23 November Julien reported no current drawer issue and asked to treat it as corrected. The earlier test with the pull-down gesture disabled had appeared to restore correct launches, but that observation does not prove the gesture caused the original fault. Continued use, including closure by swipe, is not a substitute for a documented test matrix.

This patch changes the pull-down gesture propagation from capture to bubble. It is based on the local `+drawerlayout1` source, with the original source file SHA-256 `31c2cbea8a4b176523afe8f37436f2c6d67741f50a8f8d90555319043fcbc12f`. Three matching packages are required. Built packages are external inputs and are not committed here.

The running binary SHA-256 at installation was `bb1c9f7ad048e38f97557571303b6d71f8cf3ac3b28f331382f7ce2b8e3f1cfc`. Rollback to the previous packages remains possible; `+pulldownab1` also requires the session environment `LMI_DISABLE_DRAWER_PULLDOWN=1` to reproduce that test. Full image rebuild and boot remain unverified.
The archived patch uses zero context; validate with `git apply --unidiff-zero --check pulldown-bubble.patch` against the pinned source before applying.
