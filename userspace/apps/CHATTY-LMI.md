# Local Chatty startup workaround

The opt-in `files/lmi-chatty-safe` helper is specific to the observed lmi
downstream video-node enumeration failure. It selects an isolated GStreamer
plugin directory excluding video4linux2 and uvch264, a private registry,
and a systemd-user scope limited to 384 MiB with no swap allowance. It has
no unconfined fallback. Original system plugins remain installed.

Installation on the tested phone also requires matching user desktop and
D-Bus overrides. This is not enabled in the generic installer. The directory
of plugin symlinks must be reviewed when GStreamer packages change.

See `../../docs/validation/lmi-app-checklist-2026-10-03.md` for the incident,
isolated test evidence, remaining validation and rollback boundary. SMS,
MMS and video calling are not validated by a successful application start.
