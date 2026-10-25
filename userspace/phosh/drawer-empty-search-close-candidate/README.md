# Clear empty search after completed drawer close

Candidate only, not installed. Based on external revision2, independently
reviewed against the observed immediate editable-changed / delayed
search-changed event ordering. The previous revision is superseded.

The outer HdyDeck's completed transition to home requests clearing only a
nonempty query whose applied model has no results. Raw input text and its
generation distinguish a pre-close edit's delayed signal from a new edit
after close. Cancelled swipes and searches with results retain their text.
No permanent timer or new service is added; existing debounce retained.

Source build baseline is drawersearch1. Handset/rescue is drawerpreview1.
The new package includes both the earlier search features and this close fix.
Do not choose the unaccepted drawersearch1 package as handset rollback.

Independent host checks: original and normalized patches apply/reverse with
zero fuzz, before/after hashes match; the supplied15-assertion design harness
passes when recompiled locally. This is NOT patched-Phosh GTK execution or
tactile validation. Prior isolated GTK timing established the151ms event gap.
External host syntax checks are not native ARM64 build validation.

Default preflight:
python3 userspace/phosh/drawer-empty-search-close-candidate/build-packages.py

Operator package build:
sudo python3 /home/linuxagent/xiaomi-lmi-linux-port/userspace/phosh/drawer-empty-search-close-candidate/build-packages.py --execute

The established incremental builder stages a verified scratch patch, then on
explicit execute updates the package build tree. Shared build locks, mount
namespace, Debian package tests and accepted rescue packages remain required.
No phone access, installation, kernel/image build or complete-image pin update.

Hardware acceptance must cover: empty-result swipe close restores favorites;
matching-query close keeps text; cancelled swipe keeps text; edits before and
after close with pending debounce; manual clear; favorites/DnD; scroll/close;
preview visibility; Enter on app/folder results.
