# Optional lmi torch application

The Python GTK3 application and desktop entry were installed and both buttons
were confirmed on the validated downstream lmi kernel. See the
[hardware record](../../../docs/validation/lmi-battery-audio-torch-2026-10-03.md).
Install the script as `/usr/local/bin/lmi-flashlight` (mode 755) and the entry
as `/usr/local/share/applications/lmi-flashlight.desktop` (mode 644). Requires
Python3, GTK3/PyGObject and the active user's logind session; no sudo is used.
This optional app is not yet part of the golden image or generic app installer.
Normal close and a 180-second process-local timer switch it off; no independent
watchdog protects against a crash. The downstream `flashlight` LED controls
both torch channels, using 20 mA per LED; do not reuse without driver review.
