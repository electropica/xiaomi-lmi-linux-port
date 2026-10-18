# Phoc shell-layer data-device drag candidate

Status: source candidate only; no Phoc package built or installed yet.

Phosh homedrag2 starts native DnD and reveals home, but the operator cannot
reorder favorites or deposit shortcuts. Real callback counters showed one
`drag-begin` and one reveal callback, with zero destination receive/apply
callbacks. The small drag icon remains without a completed drop. Temporarily
disabling client deck swipe and, separately, forcing the home global drag mode
to NONE did not resolve this. Both diagnostic overrides were removed and their
rollback timers stopped; normal homedrag2 remains installed.

Phoc 0.46.0 cursor routing bypasses active seat grabs for layer surfaces. During
a data-device drag this can bypass wlroots DnD dispatch as well. Its separate
layer drag gesture can also cancel the client's touch sequence. This patch
preserves the data-device grab and yields layer drag/swipe handling while a
seat drag exists. Other shell-layer grab bypass behavior is retained. Ending a
pending layer drag uses the existing drag-end path to clear pending offsets.
This is a source-backed hypothesis, not a hardware success claim.

## Operator build

Run in Ubuntu WSL:

```sh
sudo bash /home/linuxagent/xiaomi-lmi-linux-port/userspace/phosh/phoc-layer-dnd-candidate/build-arm64.sh
```

The recipe uses the retained ARM64 chroot and package-build lock. Official
Debian source archives and the original cursor source are SHA-256 pinned.
Preparation is resumable and rejects an unexpected cursor edit. proc/devpts
are prepared only in a private mount namespace. Dependency installation is
noninteractive. Upstream tests remain enabled; the Debian build directory is
made explicitly `_build` to match its test invocation. Compilation uses two
jobs. The script produces only `phoc_0.46.0-1+lmishelldnd1_arm64.deb`, prints
its checksum and does not install/restart the phone or build a kernel/image.
Keep stock Phoc available for rollback before any later installation.

## Validation performed before operator build

- Patch applies with zero fuzz to Debian 0.46.0-1.
- Actual touch/pointer predicate bodies are compiled in a host test with mocked
  seat/surface helpers: 16 routing combinations and 16 null checks. Original
  code fails the DnD case; patched code passes. This does not test Wayland event
  delivery, compositor lifetime, gesture arbitration or physical drop success.
- Fresh preparation, identical resume and rejection of a tampered source pass
  in a disposable tree. Shell/Python syntax checks pass.
- Full package compilation and upstream compositor tests are pending.

After installation, verify both favorite reorder and drawer-to-home drop,
shortcut persistence, ordinary drawer swipe, lock/unlock, and touchscreen.
Do not fold this candidate into the complete image as a validated fix yet.

Primary source: [Debian Phoc 0.46.0-1](https://deb.debian.org/debian/pool/main/p/phoc/phoc_0.46.0-1.dsc),
[upstream cursor](https://gitlab.gnome.org/World/Phosh/phoc/-/blob/v0.46.0/src/cursor.c).
