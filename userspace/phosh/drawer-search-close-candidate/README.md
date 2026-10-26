# Clear search on completed drawer close

The operator now requests clearing every search when the downward gesture
finishes closing the drawer, whether or not it has results. This supersedes
the previous empty-result-only behavior. Cancelled swipes preserve the query.

The final HdyDeck home child and transition-running=false are required. The
callback cancels the filter debounce, clears both editable text and the stored
query and restores the full model immediately. It no longer needs the previous
result-dependent generation state machine. No new timeout or service is added.

Source baseline: built draweremptysearch1. Accepted installed rollback remains
drawerpreview1. The new pair includes drawersearch1 and this revised behavior;
neither earlier candidate is promoted to accepted handset status.

Default preflight (no build or shared-source changes):

    python3 userspace/phosh/drawer-search-close-candidate/build-packages.py

Operator build:

    sudo python3 /home/linuxagent/xiaomi-lmi-linux-port/userspace/phosh/drawer-search-close-candidate/build-packages.py --execute

Normal package tests remain enabled. No automatic phone contact, installation,
kernel build, image build or accepted full-image pin change.

After guarded installation, test matching and empty searches, an immediate
close after typing, cancelled close, reopen with complete list, and ordinary
drawer scrolling, favorites, previews and Enter activation.

Host-only exact-callback checks (stubbed GTK, ASan/UBSan):

    python3 userspace/phosh/drawer-search-close-candidate/test-close-callback.py

These seven checks passed; real package and gesture acceptance remain pending.
