# Cumulative quiet-gauge v3 source patches

These two patches recover the complete qualified v3 source changes from the
pinned Debian baselines, rather than requiring the private v1/v2 working tree.
They complement the historical incremental patches in `msoc-high-resume/`.

| Component | Debian source baseline | Candidate package version |
| --- | --- | --- |
| Phosh | `0.46.0-3+deb13u1` | `0.46.0-3+deb13u1+lmigaugewake3` |
| GNOME Settings Daemon | `48.1-1` | `48.1-1+lmiquietgauge3` |

The patches include the paired opt-in, screen/actual-sleep guards, delay
inhibitor handling, USB-cycle correction and guarded noncritical msoc-high
handling already present in the installed sources. They do not recalibrate
the gauge or fix the unresolved residual deep-sleep consumption.

`identity.json` pins baseline LF bytes, resulting LF bytes and patch bytes.
`prepare-source.py` uses GNU patch in temporary scratch space with zero fuzz,
then checks the complete resulting source hash. Its default mode does not
change the supplied source; `--apply` explicitly updates that one file.
Unknown sources, altered patches and symlink targets are rejected.

From exact unpacked Debian package source directories, verify first:

```sh
python3 prepare-source.py phosh /path/to/phosh-0.46.0
python3 prepare-source.py gsd /path/to/gnome-settings-daemon-48.1
```

Add `--apply` only to prepare an operator-requested package build. Use the
candidate versions above in Debian changelogs and build the matching runtime
and common packages together. This helper does not fetch dependencies, edit
changelogs, compile packages, install anything or contact a phone. Package
builds remain operator-run. Verify package identities and source hashes before
updating the existing private image-profile input manifest.

The current image profile already pins the four v3 package identities. This
publication adds source recovery; it is not a newly built image or a claim of
byte-identical Debian packages. The existing runtime evidence and scope are in
[the consolidated validation](../../../docs/validation/quiet-gauge-night-2026-10-13.md).

Source recovery validation on 2026-10-14: all 12 preparation/rejection cases
passed through the published verifier test entry point. Both resulting source
hashes also match the retained ARM package-build trees, whose changelogs name
the v3 versions above. No package compilation, phone installation or new
performance measurement was performed by this source publication.
