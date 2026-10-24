# Drawer direction arbitration and home activity visibility

Builds on the accepted drawerscroll1 pair. No battery policy, compositor, kernel, favorites or shortcut-storage change.

The outer vertical deck previously kept can-swipe-forward enabled even when showing its final application page. The candidate enables forward navigation only on home, backward navigation only on the application page at the list's upper boundary, and updates both when the visible page or vertical adjustment changes. This removes an unnecessary competing navigation direction. It is a plausible gesture-responsiveness improvement, not a demonstrated resolution of the reported one-to-two-second delay.

Overview's running-activity carousel is hidden on home and shown on the application page if running activities exist. Its visibility is updated both when changing drawer pages and when the number of running windows changes. Applications are not closed and their metadata is retained. This requested visibility change is separate from the still-unresolved striped thumbnail pixel corruption.

A bounded 20-second probe made 100 ScreenSaver GetActive requests to the running shell, maximum response time 0.003012 seconds, with no errors. No one-to-two-second global main-loop stall was observed during that particular probe. This does not prove all interactions were sampled or establish that GTK gesture arbitration causes the entire perceived delay. Libhandy source has short nominal transition timings, but frame pacing and touch-sequence handling still require device acceptance.

The operator-only build recipe validates the pinned app-grid/overview files, other home/ESR source identities, rollback packages and a scratch patch replay. It compiles the Phosh tree once, runs package tests and produces one matched Phosh/common pair. Default invocation does not build or contact the handset. --execute must be launched by the operator.

Acceptance: immediately after each drawer opening, scroll upward and downward on icons and gaps; reach the last row; return to the first row before closing with a new downward gesture. Verify home has favorites/shortcuts without running previews, open drawer shows running previews, opening/closing a window updates them correctly, and icon drag/drop still works. Do not promote complete-image pins until accepted. Installation should restart only the user Phosh shell, not race an entire GNOME session stop/start.
