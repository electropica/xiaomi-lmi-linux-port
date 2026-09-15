# New lmi M0 closure acquisition

This is the first stage of a new reference, not a rootfs or image build.
The approved functional roots are in `m0-direct-packages.txt`: exactly 16
packages, without `mobian-base`. The acquisition adds mmdebstrap's minbase
selectors (essential and required packages), apt, the Debian archive keyring,
and hard dependencies. Recommends and Suggests are disabled. The resulting
package count is not fixed at 330.

Entry point: `base/scripts/acquire-m0-closure.sh`.
Host prerequisites: `/usr/bin/python3` with `python3-apt`, `apt-get`,
`dpkg-deb`, and `mmdebstrap` (version recorded, never executed as a builder).
QEMU and namespaces are not needed for downloading packages.

Read-only offline check:

```sh
base/scripts/acquire-m0-closure.sh --check-contract
```

For a future manual acquisition, supply authenticated public Debian and Mobian
keyrings and a fresh directory beneath this repository's `output/`:

```sh
base/scripts/acquire-m0-closure.sh \
  --output-dir output/m0/new-reference \
  --debian-keyring /path/to/debian-archive-keyring.pgp \
  --mobian-keyring /path/to/mobian-archive-keyring.gpg
```

The keyring paths above are placeholders. Establish their official provenance
and expected fingerprints before use; the script does not download keys or
decide which keys to trust. It copies the supplied public keyrings to the
reference directory and records their SHA-256. APT verifies the repositories
using those keyrings, with no authentication bypass. An expired or inadequate
key stops acquisition. No credentials or host proxy configuration are inherited.

Add `--plan-only` to fetch authenticated indexes and resolve without downloading
archives. This still writes an isolated APT state under output/ and contacts the
repositories. It is not an offline check. Each invocation requires a fresh
directory; failed or plan-only references are retained and never overwritten.

Only these public sources are enabled, with Mobian origin priority 700:

- `https://deb.debian.org/debian`, `trixie main`
- `https://security.debian.org/debian-security`, `trixie-security main`
- `https://repo.mobian.org/`, `trixie main`

APT uses an empty dpkg status and an isolated configuration, without host
sources, preferences, hooks, authentication files or foreign architectures.
No package installation, maintainer script, rootfs, QEMU invocation, image
assembly, BASE_RAW or M1 operation occurs.

Outputs, all excluded from Git by the existing output/ rule:

- `m0-closure.candidate.tsv`: resolution checked against authenticated indexes;
  not proof that archives have been downloaded.
- `cache/*.deb`: downloaded archives, never added to Git.
- `apt/state/lists/`: authenticated index and release evidence.
- `keyrings/`, `logs/`, `provenance.json`: acquisition evidence, tool versions,
  time, index hashes, sources and keyring hashes.
- `m0-closure.lock.tsv`: created only after the exact-version download plan
  matches the first plan and every archive passes identity, size and SHA-256
  checks. Columns: package, version, architecture, origin, suite, URL, size,
  SHA-256 and cache path relative to the reference directory.

The lock rejects unexpected architectures, duplicate identities and forbidden
M0 packages (mobian-base, Linux image/headers, Phosh, NetworkManager,
mobile-usb-networking and initramfs-tools). It must contain all 16 roots plus
apt and debian-archive-keyring. Nothing is promoted into base/files automatically.

The existing build-unshare-330 scripts do not yet consume this lock. The next
stage must reconstitute a local-only repository with relative Filename fields
and a trixie Release file, preserve the validated namespace/private binfmt
mechanism, restore authenticated runtime sources only after installation, and
compare the installed dpkg package/version/architecture set exactly to the lock.

This acquisition freezes package objects, not bit-identical rootfs output.
Current repository URLs are not permanent archives. Long-term public recovery
URLs (Debian Snapshot and any needed Mobian retention) remain to be verified.
Do not discard the cache on the assumption that today's URLs are permanent.
