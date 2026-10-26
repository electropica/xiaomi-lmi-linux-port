# Clear every query on drawer close — prepared October 26, 2026

The operator now requests clearing the search when the downward drawer gesture
finishes closing it, including searches with matching results. The previous
empty-only requirement is superseded, not a failure of that candidate's stated
contract. Neither candidate is installed on the accepted preview1 handset.

The new source is reconstructed from the pinned drawersearch1 baseline by
reversing the previous empty-only patch in scratch. It uses a single ordinary
notify::transition-running handler: wait until animation ends, require final
home child, cancel filter debounce, clear editable and stored query, refilter.
The previous result-dependent generation state machine is removed. Cancelled
swipes ending on the applications child preserve text; no periodic timer or
service is introduced.

The incremental patch applies and reverses with zero fuzz and exact before/after
hashes. Default preflight verifies accepted home/power/renderer sources and
preview1 rescue packages without changing the shared source. Seven cases run
the exact extracted callback against stubbed GTK APIs under ASan/UBSan: active
transition, cancelled close, matching query, empty result, pending query, repeated
close and reopening/edit. These are host checks, NOT GTK gesture execution,
an ARM64 package build or tactile acceptance.

Source SHA256 before: a57758e67026ed28e19d241f18d5ec7b9e7403b7e8353a26893de131ad88429a.
Source SHA256 after: cd46f7391d75863924095ede2242080f30fb90fc42714f71adab21e75d8f77c4.

Recipe: userspace/phosh/drawer-search-close-candidate/README.md.
Operator build and normal package tests are next; installation must retain the
accepted drawerpreview1 rollback. The complete-image pins are unchanged.
