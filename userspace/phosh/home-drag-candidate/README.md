# Native home drag candidate

Candidate for Phosh 0.46.0 quiet-gauge v3; not installed or hardware-qualified.
The resource-only favorites home remains installed while this is prepared.

- Favorite buttons become local drag sources/targets; dropping one favorite
  on another changes its saved order without deleting missing desktop entries.
- Launcher buttons become drag sources. Hovering the drawer's upper edge for
  500 ms reveals the home, where sixteen cells accept shortcuts. Moving an
  existing shortcut swaps cells. Adding to an occupied cell preserves its
  previous shortcut in a free cell, or refuses a full home without deleting it.
- A shortcut does not move/uninstall the application or remove a favorite.
- Settings writes are deferred until drag completion, and refused if another
  settings writer changed the saved layout in the meantime.
- The app menu/long-press, drawer edge-hover and tactile drag arbitration need
  actual device testing. This candidate does not implement global lateral
  minimization. Removing a home shortcut from its context menu remains pending.

Preparation pins four baseline source files and preserves the full reviewed
quiet-gauge source hash. Host order/placement tests, ARM syntax checks on both
changed C translation units, and strict schema validation passed. No package
build or capture was run by the agent.

`build-arm64.sh` is operator-run. It reuses the existing ARM build root, saves
the affected original source files, checks both initial and resumed inputs,
then builds the Phosh packages. It never contacts a phone or builds an image.
Do not manually install the packages alone: their template/schema and the
existing runtime resource overlay must be updated together after review.

## Package-test regression repair — 2026-10-18

The first package build caught an invalid `g_app_info_get_id(NULL)` in drag
setup. Null app-info constructors remain supported for both ordinary and
favorite buttons. Source preparation now carries an extension to the existing
upstream null-info test. Fresh source preparation matches the repaired build
inputs, the quiet-gauge source is unchanged, and all 36 Phosh tests pass after
incremental recompilation/relinking. No checks were disabled. This does not
replace post-flash touchscreen gesture validation.
