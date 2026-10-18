# Native home drag candidate

Candidate `homedrag2` for Phosh 0.46.0 quiet-gauge v3. The first integrated
image installed `homedrag1`, but its hardware test failed: the icon followed
the finger while the drawer stayed above the home. The v2 correction is
packaged and installed on the handset; startup is healthy, while the physical
drag/drop retest remains pending.

- Favorite buttons become local drag sources/targets; dropping one favorite
  on another changes its saved order without deleting missing desktop entries.
- Launcher buttons become drag sources. At drag start, an idle callback reveals
  the home automatically, where sixteen cells accept shortcuts. Moving an
  existing shortcut swaps cells. Adding to an occupied cell preserves its
  previous shortcut in a free cell, or refuses a full home without deleting it.
- A shortcut does not move/uninstall the application or remove a favorite.
- Settings writes are deferred until drag completion, and refused if another
  settings writer changed the saved layout in the meantime.
- The app menu/long-press, automatic drawer dismissal and tactile drag arbitration need
  actual device testing. This candidate does not implement global lateral
  minimization. Removing a home shortcut from its context menu remains pending.

Preparation pins five baseline source files, including the constructor test, and preserves the full reviewed
quiet-gauge source hash. Host order/placement tests, ARM syntax checks on both
changed C translation units, and strict schema validation passed. No package
build or capture was run by the agent.

`build-arm64.sh` is operator-run. It reuses the existing ARM build root, saves
the affected original source files, checks both initial and resumed inputs,
then builds the Phosh packages. It never contacts a phone or builds an image.
On the complete-image handset, the old resource overlay is already absent,
so the paired v2 Phosh/common packages can update v1 after review. An older
resource-overlay installation still needs that overlay removed together with
the matched package/template/schema update. Never install only one of the pair.
The operator build uses `-nc` and invalidates only the generated debhelper
build stamp so compilation remains incremental and tests still run.

## Package-test regression repair — 2026-10-18

The first package build caught an invalid `g_app_info_get_id(NULL)` in drag
setup. Null app-info constructors remain supported for both ordinary and
favorite buttons. Source preparation now carries an extension to the existing
upstream null-info test. Fresh source preparation matches the repaired build
inputs, the quiet-gauge source is unchanged, and all 36 Phosh tests pass after
incremental recompilation/relinking. No checks were disabled. This does not
replace post-flash touchscreen gesture validation.

## Drawer/drop correction — 2026-10-18

V2 schedules the home-page reveal from the GTK `drag-begin` callback, after the
drag context has been created. The source button stays owned by the hidden
drawer. The whole deck is no longer a drop target; only actual home cells and
favorites receive drops. No sensor/camera or battery policy is changed.
All 36 Phosh tests pass after targeted recompilation/relinking; stable and
complete staging tests pass too. Real deposit persistence and favorite reorder
still need handset tests after the operator builds the v2 pair.

## V2 deployment gate

The operator built the v2 pair and it was installed together. The runtime
executable matches the installed package, quiet-gauge opt-ins are preserved,
and no stale UI overlay is present. The temporary automatic rollback was
stopped after successful software startup checks. Touch drop persistence and
favorite reorder remain unqualified until the physical retest.
