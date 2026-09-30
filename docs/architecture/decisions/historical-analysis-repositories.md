# Historical analysis repository provenance

The following historical analysis repositories were audited during workspace
cleanup. They contain no unique tracked modifications required for the
canonical Mobian/lmi source tree and can be reconstructed from the origins and
commits recorded below.

## dv183-qmux-reference

Historical path:
`/home/linuxagent/pmos-d-repro-01/analysis/dv183-qmux-reference`

Repository:
`https://gitlab.com/linux-mobile-broadband/libqmi.git`

Commit:
`3f07d6e5b4677558543b3b4484ea88ad92257e92`

The checkout is shallow and was at detached HEAD.

Its only untracked entry was a clean nested reference checkout:

### uqmi-crosscheck

Repository:
`https://github.com/openwrt/uqmi.git`

Commit:
`7914da43cddaaf6cfba116260c81e6e9adffd5ab`

Branch:
`master`

The nested checkout is shallow and clean.

## dv72-qdl

Historical path:
`/home/linuxagent/pmos-d-repro-01/analysis/dv72-qdl`

Repository:
`https://github.com/linux-msm/qdl.git`

Commit:
`657f12fa64582407fcca5144151a5879e7cd59a6`

Branch:
`master`

The checkout is shallow.

The audit found 24 untracked files. Every one of them was an empty zero-byte
file with names corresponding to identifiers such as `bEndpointAddress`,
`read_req.offset`, `out_ep`, and `wMaxPacketSize`. They were classified as
non-source artefacts.

## dv68-mdm-helper-source

Historical path:
`/home/linuxagent/pmos-d-repro-01/analysis/dv68-mdm-helper-source`

Repository:
`https://github.com/comprehensive9/vendor_qcom_proprietary.git`

Commit:
`36fc163a534963a5b3af52186af5efcc63401ad2`

Branch:
`11se`

The checkout is shallow and clean.

## Cleanup classification

These repositories are reproducible references rather than canonical project
source. Their exact origins and commits are retained here so the historical
analysis can be reconstructed if required.
