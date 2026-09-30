# Initial repository migration note

This short note replaces the workstation-specific migration scratch document
from the initial repository import. The original note described the first
domain-based layout (`base/`, `display/`, `wifi/`, `bluetooth/`, `gpu/`,
`phosh/`, `apps/`, and `kernel/`) and the then-planned output area. Those
paths and its statement that no root build entry point existed are historical
and superseded.

The current unified architecture is documented in
[`docs/architecture/ARCHITECTURE.md`](../architecture/ARCHITECTURE.md). The
initial import mapping remains available as
[`repository-migration-manifest.tsv`](repository-migration-manifest.tsv);
it records that earlier migration snapshot and is not an active path manifest.
No prior source workspace is required to understand or clone the current
repository.
