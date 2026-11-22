# Sleep retry after a blocked suspend

The runtime version `48.1-1+lmiquietgauge3+esrquiet1+irqnames1+sleeprefusal1+retry2` retries the normal idle policy after a suspend request is refused. It waits before checking logind inhibitors, backs off while sleep is blocked, and re-arms the normal idle watch rather than bypassing session policy.

Apply `0001-recover-after-sleep-refusal.patch` to the project's GSD 48.1 `irqnames1` source (`plugins/power/gsd-power-manager.c` SHA-256 `73f28230c13e3edf9dcd349064f223e151938e1cfdb4f64506b76dfae208783c`), then apply `0002-retry-after-sleep-refusal.patch`. The resulting source SHA-256 is `be655e36472478df01d0c51d4d82606898cc42ef35d33fa2a0519331c5b392ec`.

For the host tests, copy the resulting source into this directory as `gsd-power-manager.c` and run `python3 test-inhibitors.py` and `python3 test-retry-callback.py`. They compile code extracted from that source and require a C compiler and `gio-2.0` development files. They exercise inhibitor parsing and callback behavior with simulated D-Bus responses; they do not replace device tests.

On the handset, the test on 22 November established a refused suspend while a sleep inhibitor was held, a delayed retry after release, and successful s2idle entry. The test did not independently establish screen illumination behavior or all user-activity and policy-change races. The previous package is retained separately for rollback. Do not interpret a successful suspend as proof of improved battery consumption.
