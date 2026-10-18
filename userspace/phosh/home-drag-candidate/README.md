# Native home drag candidate

## homedrag7: native Restart button (installed; confirmation validated)

The operator-built pair passes 36/36 tests and is installed with executable
health verified. Only the user shell restarted; no handset reboot occurred.
The operator confirms button visibility and cancellable confirmation; actual
reboot execution was not tested. Older build-pending
statements below describe preparation history.

Adds Restart to the long-press power menu, translated through the existing
French catalog. It calls the existing session-manager reboot flow and is
disabled on the lock screen. Manager/resource compilation and static action
checks pass; no reboot was issued. The command below now builds homedrag7.
The handset remains on the qualified homedrag6 pair until operator build and
installation; check button visibility and cancel the normal confirmation first.


## homedrag6: move between saved surfaces (installed and confirmed)

The homedrag6 pair is installed after an operator build with 36/36 tests.
Contacts was physically moved favorites → home → favorites: both moves remove
the source shortcut. Saved settings confirm the final five favorites and no
Contacts home shortcut. The earlier five-icon fit remains qualified.

Homedrag5 had established that five favorites fit on the handset. The operator then
clarified that dragging a favorite to home must remove it from the dock. The
previous copy behavior is replaced with an origin-aware transfer between home
and favorites. Drawer drags remain copies; moving within either saved surface
retains its existing reorder behavior.

Both lists are validated against their initial snapshots before a grouped
GSettings apply. Failure/concurrent changes leave the source and destination
unchanged. A full five-entry dock cannot consume a home shortcut. Already-
present destination entries permit moving away the other saved copy.

Compiled source-removal and grouped-commit/concurrent-source tests accompany
the change. The same WSL command below builds homedrag6; operator-built
packages and the stated bidirectional handset transfer checks now pass. No
additional package was built autonomously.


## homedrag5: fit five icons and avoid deferred removal starvation

The installed homedrag4 accepts a fifth favorite, but runtime measurements and
a screenshot show right-edge clipping. GtkFlowBoxChild theme padding was not
included in the earlier width calculation. Home and favorite cells now remove
that padding through scoped style providers. Compiled tests using the actual
Phosh button factories and stylesheet measure four home cells at 354px and
five favorites at 344px; both fit the 360px logical display including margins.

Intermittent removal delays were reported. The deferred action now runs at
normal main-loop priority, retaining idle/deferred execution and the existing
slot/concurrent-change checks. A bounded busy-loop-source regression test
covers starvation; this does not yet prove the user's intermittent trigger.

The WSL command below now builds homedrag5. No package/image was built by the
agent. Actual five-icon fit and prompt repeated removal remain to be checked
on hardware after installation. The temporary geometry/action observer has
been fully removed; the phone continues on normal homedrag4.


## homedrag4: up to five favorites (operator package build pending)

Adds drawer-to-dock drops on an existing favorite or dock whitespace. New
favorites are inserted or appended, existing favorites are reordered, and a
sixth entry is rejected without losing saved desktop IDs. Menu additions obey
the same limit. Favorite icons are 48px with 64px clamps and a five-column
maximum so they fit the 360px logical display in one row.

Ordering/limit host tests cover an empty dock, fifth entry, insertion, reorder
at capacity, rejection of a sixth and invalid input. The targeted GTK button
test also compiles/runs. Package build and five-icon handset checks are pending.
The same WSL build command below now produces the homedrag4 pair.


## homedrag3 follow-up (installed; removal confirmed)

The homedrag3 pair is now built (36/36 tests), installed and the operator
confirms home shortcut removal works. Lateral preview, spacing and folded-edge
behavior still await physical confirmation. No complete image was rebuilt.

Phoc lmishelldnd1 is installed and the operator confirms actual DnD works.
A temporary global home gesture isolation test also confirms direct lateral
favorite reorder; the diagnostic module/drop/timer has been removed.

The next Phosh/common pair adds:

- home shortcut context menu: **Retirer de l’accueil**, without uninstalling;
- compact icon/name grouping inside each stretched home grid cell;
- explicit 48px drag preview independent of movement direction;
- global layer drag disabled only when the overview is fully unfolded, keeping
  the app-edge behavior while folded. Recheck app-edge return on hardware.

Run in Ubuntu WSL:

```sh
sudo bash /home/linuxagent/xiaomi-lmi-linux-port/userspace/phosh/home-drag-candidate/build-arm64.sh
```

This builds only the paired homedrag3 packages with normal tests, not a kernel
or complete image. All previous quiet-gauge changes remain pinned. A targeted
compiled test verifies slot removal, preservation of another shortcut and
refusal to overwrite concurrent settings. Physical removal, icon/label spacing,
preview visibility and folded-edge behavior remain pending package install.
The complete-image profile is still homedrag2 until this candidate is qualified.


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
