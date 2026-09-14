# Historical migration note

> This document records the repository migration preparation state. It is not the current architecture reference. See `docs/ARCHITECTURE.md` for the active layout and `docs/CURRENT-BUILD.md` for the validated build.

# Architecture preparation

Source repository:
  /home/linuxagent/pmos-d-repro-01/github-export

Migration preview:
  /home/linuxagent/pmos-d-repro-01/archi

The source repository is left untouched.

Active domains:
- base
- display
- wifi
- bluetooth
- gpu
- phosh
- apps
- kernel

Generated artifacts belong in output.

Historical and replaced implementations belong in historical.

No root build.sh is created yet.
Existing build logic must first be adapted and validated against the new paths.
