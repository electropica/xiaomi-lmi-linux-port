# Empty search on drawer close — candidate revision2,25 October2026

Requested behavior: a zero-result search clears after a completed downward
drawer close, restoring favorites. Searches with results and cancelled swipes
retain their current text. This is not an installed/accepted feature yet.

The first supplied close patch missed the GtkSearchEntry editable-changed vs
search-changed delay. An isolated unshown GTK3.24.49 check observed approximately
151ms between these signals. Model counterexamples S10/S11 exposed an incorrect
clear of fresh matching text and a missed clear of fresh zero-result text.

Revision2 tracks normalized editable text immediately and records the input
generation when the outer HdyDeck closes. It compares the applied filter query
with this text, retaining the confirmed-close intent across delayed delivery
but rejecting a genuinely later edit. The15-assertion standalone design model
now passes when independently compiled and run. This is model validation,
not execution of patched Phosh, GTK gesture testing or ARM64 package validation.

The libhandy1.8.3 retained source contract identifies transition-running=false
and final home child as completion; visible-child-name alone changes too early
and can describe an uncompleted/cancelled gesture. Callbacks use ordinary,
complete signal signatures. No periodic timer or service is added.

Original external patch SHA256:
4a3ae6a54b73f54cd6bd2fcafa6723b29bef64a078c53e0e14c09a286773a30c.
Source baseline SHA256:
e946a5fa0a8e58482f8c57269116161f2b626a38fe4a90ca970baec9026ccfad.
Patched source SHA256:
a57758e67026ed28e19d241f18d5ec7b9e7403b7e8353a26893de131ad88429a.

Canonical zero-context patch reproduces that exact source with GNU patch,
zero fuzz, checked forward/reverse. Recipe preflight passes, preserves current
home/power/renderer sources and does not change the shared build tree.

Build baseline is drawersearch1; installed handset and rollback are the accepted
drawerpreview1 pair. The earlier search test encountered retained filtering on
the old version too; no causal new-version crash was established. Keep the
combined new search/close package unqualified until package tests and physical
acceptance pass. Complete-image pins remain on drawerpreview1.

Recipe: userspace/phosh/drawer-empty-search-close-candidate/README.md.
No package build, installation, phone contact or new battery experiment was
performed for this revision's preparation.
