# Lock-screen power menu — October 23, 2026

The operator-built phosh and phosh-common homedrag8 pair is installed. All
36 package tests passed. The running Phosh executable matches the built
package (SHA256 45cec0a07bb8fac7f2fbf4ca8bd6670eeb80d7024cb40a13aa6c1223109192cd).
The existing Phoc version and quiet-gauge opt-in remain unchanged; dpkg audit
is clean and no NPU restore state is pending.

The operator confirmed the power menu and confirmation work without unlocking.
A subsequent handset restart was explicitly confirmed as voluntary, rather
than a restart despite cancellation. The phone returned healthy on homedrag8.
Its transient rollback timer is absent/inactive after that restart, so no
automatic downgrade remains scheduled.

Only power-menu-manager.c changed against qualified homedrag7: shutdown and
restart actions remain enabled while locked. Native confirmation handlers,
the lock state, home/drawer sources and quiet-gauge source are unchanged.
Actual shutdown was not executed during this validation.

The complete-image builder, profile staging/installation and staging tests
now select homedrag8. This is a package update to the running phone and a
next-build recipe update, not a newly generated or flashed system image.
No kernel build, flash, battery-policy modification or new drain test was run.
