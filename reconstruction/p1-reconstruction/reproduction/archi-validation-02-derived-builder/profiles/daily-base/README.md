# `daily-base` profile

`daily-base` is a distinct, package-neutral derivative combining the validated
`time-seed` clock floor with one per-user XDG autostart override for Chatty's
daemon. It does not modify `baseline-nochange` or `time-seed`.

The profile leaves the Chatty package, its system autostart desktop file and
the manual application launcher untouched. Its `20-disable-chatty-daemon`
hook creates
`/home/mobian/.config/autostart/sm.puri.Chatty-daemon.desktop` containing
`Hidden=true`, owned by `mobian:mobian`, mode `0644`. XDG autostart then masks
only the same-named system daemon entry; `sm.puri.Chatty.desktop` remains the
manual launcher. The hook refuses to replace a pre-existing non-identical
user override and creates no network or package changes.

The time-seed runtime, units and initializer are kept as a profile-local
snapshot of `time-seed`; the verifier checks the shared runtime/unit files
against that profile to prevent drift. Both profile hooks require explicit
`--enable-hooks`. The build-host UTC epoch seeds the copied rootfs; no fixed
timestamp is stored here.

No image build or new hardware test is implied by preparing this profile.
