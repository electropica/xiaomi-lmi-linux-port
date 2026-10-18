# Favorites home and vertical application drawer

Resource-only adaptation of Phosh 0.46.0's `src/ui/app-grid.ui` (GPL-3.0-or-later).
The existing favorites revealer is moved to the first page of a vertical
HdyDeck. A flexible spacer keeps favorites at the bottom, above a small drawer
indicator. The full application grid and original folder navigation stay on
the second page. Favorites use Phosh's original model and activation handlers;
no duplicate desktop shortcuts or background polling service is introduced.

`app-filter-mode=[]` disables adaptive-only filtering and natively hides its
button. Existing per-user favorites are preserved. The resource overlay is
scoped to the Phosh user service and keeps the separate quiet-gauge opt-in.
The current image profile pins the matching Phosh version. `identity.json`
records the original and adapted resource hashes for review.

Operator validation on October 18 confirmed favorites on the home, opening
and closing a favorite, returning home and opening the full drawer. Bottom
dock alignment and placing its chevron below the favorites are subsequent
layout adjustments; the final placement was verified by a native Phosh screenshot.
A first resource-only GTK probe checked parsing and page selection. This does
not implement global left-edge minimization or qualify battery behavior after
this UI adaptation. A future full image incorporating it remains unbuilt.
