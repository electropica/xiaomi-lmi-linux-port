# Complete `.deb` cache evidence

This directory contains text manifests and an offline verifier for the
`archi-validation-02` Debian package closure. It contains no package archives.

The validated closure has 1,086 exact `.deb` files: 772 copied from the
original APT archive cache, 301 retrieved from Debian repositories, 12 from
Debian Snapshot, and one Mobian archive keyring retrieved from Debian
Snapshot. The cache payload totals 521,861,380 bytes.

The uncompressed deterministic tar archive is kept outside Git:

- WSL: `/home/linuxagent/archi-validation-02-deb-cache-1086-20260927.tar`
- Windows: `C:\Users\julien\Downloads\archi-validation-02-deb-cache-1086-20260927.tar`
- size: 523,274,240 bytes
- SHA-256: `65058c4bc74c6aea3854060a8e7b9a7617ea6aee66d503d90564bcee214a69fd`

Those paths record where the validated archive was saved; the archive itself
is not stored in this repository. `PACKAGES.tsv`, `SOURCES.tsv`, and
`SHA256SUMS` preserve the complete package identity, provenance, and payload
checksums. The four `DEB-*.tsv` files preserve the source cache inventory and
the retrieval plans. Snapshot pages exposed SHA-1 for those 13 candidates;
their local SHA-256 values are recorded in `SOURCES.tsv` and `SHA256SUMS`.

After obtaining or unpacking the external cache, verify it offline with:

```sh
reproduction/archi-validation-02-lock/deb-cache/verify-deb-cache.sh \
  /path/to/archi-validation-02-deb-cache
```

The argument is the directory containing the 1,086 `.deb` files and its
`STATUS` file. The verifier reads that directory and the tracked manifests;
it does not install packages or require network access.
