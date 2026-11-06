# Nautilus 48.3 touch multi-selection candidate

Status: source candidate only. It has not been compiled, installed, or run on the phone.

## Exact source base

This candidate is based on official GNOME Nautilus tag `48.3`, commit
`b6e37e2fbca44feb829b64729fcb8c73d168dfbd` (the corresponding Debian Trixie source
package is `48.3-2`). It modifies the shared GTK4 `NautilusListBase` used by both
`GtkGridView` and `GtkColumnView`, plus the view action and context-menu resource.

The implementation depends on the `NautilusViewModel` continuing to implement GTK's
`GtkSelectionModel`, and on `NautilusViewItem` identity remaining stable long enough for
the next main-loop turn. The GTK APIs used (`gtk_selection_model_get_selection()`,
`gtk_selection_model_set_selection()`, `gdk_event_get_event_sequence()`) exist in the
GTK 4 API family used by Debian 13; this branch was not compiled against the device's
actual package headers.

## Behavior proposed

The context menu gets a checkable “Tap to Select Multiple Files” action. While it is
checked, a touchscreen tap toggles that item in the current selection, preserving all
other selected entries. The click path snapshots selected `NautilusViewItem` identities
before GTK handles the ordinary primary tap and applies the toggled set in the next idle
turn, resolving current model positions by item identity. This avoids relying on stale
list positions if the model reorders between press and idle. The action is limited to
real GDK touch sequences. Mouse and keyboard modifier paths keep the normal selection
behavior. A double tap does not open an item while the mode is active.

The existing long-press callback still opens the selection or background context menu.
A canceled click/scroll/drag drops its saved selection snapshot, so a scroll gesture
must not alter selection. The active flag is per `NautilusFilesView` instance; switching
views may require enabling the mode again. The same checked menu item toggles the mode
off.

## Static checks performed

- `git diff --check` passed.
- The modified GtkBuilder XML parsed successfully with the PowerShell XML parser.
- The candidate patch applied cleanly in a temporary worktree based on the exact source
  commit, and `git apply --reverse --check` passed on the candidate tree.
- Source review confirmed the target's existing selection model already supports
  `gtk_selection_model_get_selection()` and `gtk_selection_model_set_selection()`.
- GTK4 docs were checked for touch event sequence detection, event-controller behavior,
  and gesture arbitration. No code was compiled and no runtime suite was run.
- No phone interaction or user-file access was performed.

This is not yet a validated fix. Compile-time API/type compatibility remains unverified.
Runtime ordering also needs confirmation: specifically, that
`GtkGestureClick::released` schedules the apply after GtkListBase's default selection,
that a completed tap reaches the idle callback before the click controller's `stopped`
cleanup, and that long-press/scroll arbitration on GTK 4.18 leaves the menu and scroll
paths intact. The operator must exercise these on the target package set.

## Patch use and reversal

From a clean Nautilus 48.3 source tree:

```sh
git apply --check /path/to/touch-selection.patch
git apply /path/to/touch-selection.patch
```

Revert with:

```sh
git apply -R /path/to/touch-selection.patch
```

First compare the source base to tag commit `b6e37e2fbca44feb829b64729fcb8c73d168dfbd`.
If Debian downstream patches alter `src/nautilus-list-base.c`, `src/nautilus-files-view.c`,
or `src/resources/ui/nautilus-files-view-context-menus.ui`, port the change instead of
applying blindly.

## Operator validation after building

Use a temporary test directory populated only with disposable empty files and folders.
Test both grid and list views:

1. Open the background context menu, enable “Tap to Select Multiple Files”, and close it.
2. Tap two nonadjacent test files; confirm both remain selected.
3. Tap one selected file again; confirm only it is deselected.
4. Tap a folder and verify it is selected without opening while the mode is active.
5. Scroll across items and drag an item; verify these gestures do not toggle selection.
6. Long-press a file and confirm its context menu still appears.
7. Reopen a context menu, uncheck the mode, then verify ordinary single/double-click behavior.
8. Recheck Ctrl/Shift selection with a keyboard if available, to confirm that path is unchanged.

Retain the stock package for rollback until all steps pass.