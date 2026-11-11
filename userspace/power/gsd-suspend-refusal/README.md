# Recover idle state after a refused suspend

This patch targets the project's modified GNOME Settings Daemon 48.1 power plugin. It restores the previous logical idle mode when logind refuses a suspend request, without turning the backlight on or immediately rearming an expired idle watch.

The `+sleeprefusal1` package was installed on the lmi handset and the rejection path was observed. A controlled end-to-end test of suspend after releasing the inhibitor is still needed. The patch does not itself initiate another suspend immediately when an inhibitor disappears, and depends on the earlier project-specific power patches.
