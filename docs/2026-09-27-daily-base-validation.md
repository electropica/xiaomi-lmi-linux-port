# `daily-base` derived userdata hardware validation — 2026-09-27

## Result

The `daily-base` derivative was flashed as userdata in fastbootd and booted
successfully with the D-repro D-v43 boot already installed durably. Phosh was
visible and usable, the configured unlock code was accepted, and lock/unlock
remained responsive without a notable delay. DSI-1 was active. The hardware
renderer path was confirmed as GLES2 → Zink → Turnip → KGSL → Adreno 650.

The exact tested external outputs were:

| Form | Size | SHA-256 |
| --- | ---: | --- |
| Raw `archi-validation-02-derived-daily-base-20260927.img` | 4,551,868,416 bytes | `5cc226cd96c324b68d74e33eec461a091e7f5dd69b80e0529c2d0267cfa3cad5` |
| Sparse `archi-validation-02-derived-daily-base-20260927.img.android-sparse.img` | 2,960,466,444 bytes | `172a4f950252e810f408bf4d5caf5075c699020e6a2198999f7f0b30c7f19928` |

Sparse expansion matched raw; GPT, partitions, boot/root UUIDs and the
embedded userdata boot partition were checked. The root-only build state at
`state-daily-base-daily-base-20260927-20260927T112711Z-506187` was mode 0700
and owned by `nobody:nogroup`; it could not be reread without interactive
sudo. This is a provenance-access limitation, not a functional failure. The
image hashes and sparse/raw round trip were checked independently, and the
operator confirmed the real boot and UI behavior.

## Profile changes and demonstrated causes

The Poco RTC was stuck at 1975 and rejected writes with `EPERM`. A boot
therefore started at 2026-04-13 although the actual date was 2026-09-27, and
PAM warned that the `mobian` password had been changed in the future. The
`time-seed` profile initializes a root-only UTC epoch from the build host; at
boot its service advances the system clock only if it is older than the seed.
The hardware run confirmed the active seed, a system time at or above it, and
no new PAM “password changed in future” warning. No claim is made that NTP
received packets or that the RTC was repaired.

Automatic startup of the Chatty daemon had separately caused an approximately
one-minute unlock delay. `daily-base` adds only the per-user XDG override
`/home/mobian/.config/autostart/sm.puri.Chatty-daemon.desktop` with
`Hidden=true`, owned by `mobian:mobian`, mode 0644. The package Chatty
`0.8.7-2`, its system autostart entry and its manual launcher remain intact;
Chatty was not running during this validation. The delay did not recur.

The builder, verifiers, helper tests, manifests, profiles, hooks and overlays
are text-only under
[`reproduction/archi-validation-02-derived-builder/`](../reproduction/archi-validation-02-derived-builder/README.md).
The generated raw/sparse images, `.deb` cache, boot image, rootfs, and private
build state are external and are not versioned. `baseline-nochange` remains
unchanged; hooks for `time-seed` and `daily-base` require explicit
`--enable-hooks`.

## Boot/userspace boundary

The validated D-repro D-v43 boot/kernel is separate from the `boot.img`
embedded inside userdata. `daily-base` derives only a copy of the userdata
rootfs and preserves the embedded boot partition, partition table and UUIDs.
This milestone does not rebuild the kernel, install a different boot, or
establish bit-for-bit reconstruction from source.
