# Experimental Linux 7 Type-C patch pair

The first patch is the historical wakeup/resync candidate; the second changes
its primary IRQ handler to wake the threaded handler. Their intended order is
0001 then 0002. They are retained for review and are not wired into a complete
kernel or image builder. See the [handset validation](../../../../../docs/validation/lmi-linux7-typec-detach-2026-11-01.md).

These patches alone do not reconstruct the complete tested kernel. A future
build must reproduce its audio, camera, MHI, DTB and other source changes and
preserve its boot-menu rescue paths. Do not apply this pair blindly to a tree
that already contains either change.
