# USB maintenance sleep guard — 2026-11-06

On the lmi handset, a verified USB network profile restored SSH while awake,
but the connection later stopped responding with the display off. The local
power policy allowed the phone to enter s2idle on external power; maintaining
network access and allowing system suspend are separate requirements.

A targeted service now runs on the handset. It uses a logind sleep inhibitor
only after observing, twice, external charger online, USB input voltage of at
least 4 V, a Type-C partner, a configured USB gadget and usb0 carrier. Any
missing, unreadable or negative signal releases the inhibitor at the next
three-second poll. This retains screen blanking while preventing logind-managed
sleep, including manual suspend, during a qualified USB connection. It does
not promise USB operation while the SoC is actually suspended. A systemd
watchdog and control-group cleanup provide recovery if the process fails.

The first on-device iteration was observed acquiring the inhibitor, releasing
it after unplug, and acquiring it again on replug. With the installed unit,
stopping the service released the inhibitor and restarting it reacquired the
inhibitor. A first screen-off trial failed because the inhibitor unexpectedly
released; the cause was not captured. Logging of the relevant signals at
release was added. The subsequent trial kept SSH accessible over USB for over
eight minutes with screen brightness zero and the inhibitor continuously held.

The local Python tests use synthetic inputs and mocked child processes; three
tests passed. The systemd unit was verified on the handset. Actual suspend
after unplug, wall charger behavior, boot behavior and watchdog fault injection
remain unqualified. The sysfs device paths are hardware-specific; missing
paths fail open to normal system sleep rather than keeping it inhibited.

The clean-image recipe carries this same service, but the resulting image has
not been built or tested. The independent NetworkManager profile remains
necessary to configure usb0's static maintenance address.
