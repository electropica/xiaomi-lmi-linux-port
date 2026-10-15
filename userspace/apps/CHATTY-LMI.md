# Local Chatty startup workaround

The `files/lmi-chatty-safe` helper is specific to the observed lmi
downstream video-node enumeration failure. It selects an isolated GStreamer
plugin directory excluding video4linux2 and uvch264, a private registry,
and a systemd-user scope limited to 384 MiB with no swap allowance. It has
no unconfined fallback. Original system plugins remain installed.

The optional-app installer now stages `files/install-chatty-safe.sh` and the
helper in the M1 image. It builds the isolated plugin view, disables the daemon
autostart, sets DBusActivatable=false on the translated launcher, and routes
explicit D-Bus activation through the same bounded helper. Existing user desktop
overrides are updated so they cannot retain the unsafe activation flag. The
directory of plugin symlinks must be reviewed when GStreamer packages change.
The updated image recipe has not yet been rebuilt or boot-tested.

See `../../docs/validation/lmi-app-checklist-2026-10-03.md` for the incident,
isolated test evidence, remaining validation and rollback boundary. SMS,
MMS and video calling are not validated by a successful application start.


## Startup recurrence, 15 October 2026

The kernel OOM killer terminated Chatty about 169 seconds after boot with
approximately 6.15 GiB anonymous RSS. The notification was emitted by GSD
Housekeeping; it did not identify a GSD crash. All inspected GSD services were
running with no automatic restarts. The phone had a safe manual wrapper, but
its user desktop still had DBusActivatable=true and the unprotected daemon
autostart was not disabled. These paths could bypass the wrapper.

The live correction suppresses daemon autostart, disables launcher D-Bus
activation, and protects explicit D-Bus activation. A harmless scope probe
confirmed memory.max=402653184 and memory.swap.max=0. The pids controller is
not exposed by this kernel, so TasksMax must not be described as a verified
runtime limit. No SMS, account connection, media probe or heavy build was
performed to validate this deployment. A fresh startup and manual UI launch
remain to be checked; this is containment of the known enumeration failure,
not an upstream Chatty memory-leak fix or proof of a standby-drain correction.
