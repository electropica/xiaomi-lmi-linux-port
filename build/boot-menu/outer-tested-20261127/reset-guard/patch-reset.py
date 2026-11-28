#!/usr/bin/env python3
"""Prepare a pinned reset-service guard without modifying the build cache."""
import argparse
import hashlib
from pathlib import Path

UPSTREAM_SHA256 = '5a7532c21272373c751bcdc1c8b0ee81eb9e31bb9fd5ff463bba22ac201b9786'
RELATIVE_SOURCE = 'Common/edk2/MdeModulePkg/Universal/ResetSystemRuntimeDxe/ResetSystem.c'


def patch(raw):
    if hashlib.sha256(raw).hexdigest() != UPSTREAM_SHA256:
        raise ValueError('Unreviewed ResetSystem.c; refusing candidate generation')
    text = raw.decode().replace('\r\n', '\n')
    needle = '  ASSERT_PROTOCOL_ALREADY_INSTALLED (NULL, &gEfiResetArchProtocolGuid);'
    if text.count(needle) != 1:
        raise ValueError('Reset initializer anchor mismatch')
    return text.replace(needle, '''  // LMI_RESET_PRESERVE_PLATFORM_V1: keep the earlier platform reset service.
  // The Qualcomm service understands RESET_PARAM boot reasons; the generic
  // PSCI implementation only performs an ordinary reset. An ASSERT alone
  // does not prevent replacement in RELEASE builds.
  VOID  *ExistingReset;

  ExistingReset = NULL;
  Status = gBS->LocateProtocol (&gEfiResetArchProtocolGuid, NULL, &ExistingReset);
  if (!EFI_ERROR (Status)) {
    return EFI_ALREADY_STARTED;
  }

  if (Status != EFI_NOT_FOUND) {
    return Status;
  }
''').encode()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source', type=Path, help='EDK2-MSM checkout')
    ap.add_argument('output', type=Path, help='New candidate C file, not the cache source')
    a = ap.parse_args()
    source = a.source / RELATIVE_SOURCE
    if a.output.resolve() == source.resolve():
        ap.error('In-place mutation is forbidden by this preparation helper')
    candidate = patch(source.read_bytes())
    with a.output.open('xb') as out:
        out.write(candidate)
    print('RESET_GUARD_SOURCE_PREPARED_NOT_BUILT', hashlib.sha256(candidate).hexdigest())
