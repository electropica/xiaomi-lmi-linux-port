# Application drawer scroll priority

The home8 vertical HdyDeck unconditionally permits backward swipes. With more than twenty icons, downward gestures can therefore start closing the drawer while its GtkScrolledWindow still has earlier application rows above the viewport.

This candidate connects the existing vertical adjustment's value-changed and changed signals to the outer deck's can-swipe-back property. Closure is allowed only at the adjustment's lower bound. Opening the drawer and icon drag/drop are unchanged. The patch preserves the ESR quiet-wake source and the other home8 files; only app-grid.c and Debian changelog change.

Default build-packages.py invocation performs pinned source/rollback and scratch patch checks. The --execute build is operator-launched and creates a matched Phosh/common pair without phone access. Runtime qualification must demonstrate: scroll down to the final row; drag downward to reach the first row without closing the drawer; release; use a new downward gesture to close; reopen; move an icon to home and between favorites. Source reasoning alone does not establish GTK touch arbitration at the upper boundary.

The unrelated Phoc linear-thumbnail candidate did not resolve the striped previews in the captured device test. Do not claim it fixed. The session restart also collided with asynchronous GNOME session teardown; avoid immediate stop/start during further deployment. The subsequent handset boot restored the installed October 7 kernel, replacing the temporary FG test kernel. The prior overnight evidence remains preserved separately.
