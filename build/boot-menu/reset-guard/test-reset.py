#!/usr/bin/env python3
"""Compile and replay the actual pinned reset initializer with mock services."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import sys

here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('reset_patch', here / 'patch-reset.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
source = Path(sys.argv[1]) / module.RELATIVE_SOURCE
raw = source.read_bytes()
candidate = module.patch(raw).decode()
start = candidate.index('InitializeResetSystem (')
opening = candidate.index('{', start)
depth, end = 1, opening + 1
while depth:
    depth += (candidate[end] == '{') - (candidate[end] == '}')
    end += 1
function = 'EFI_STATUS\n' + candidate[start:end]
original = raw.decode().replace('\r\n', '\n')
old_start = original.index('InitializeResetSystem (')
old_end = original.index('\n}\n', old_start) + 3
original_function = 'EFI_STATUS\n' + original[old_start:old_end]
prefix = r'''
#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#define IN
typedef unsigned long EFI_STATUS;
typedef void VOID;
typedef void *EFI_HANDLE;
typedef struct {int unused;} EFI_SYSTEM_TABLE;
#define EFI_SUCCESS 0UL
#define EFI_NOT_FOUND 14UL
#define EFI_ALREADY_STARTED 20UL
#define EFI_DEVICE_ERROR 7UL
#define EFI_ERROR(x) ((x) != EFI_SUCCESS)
#define ASSERT_EFI_ERROR(x) assert(!EFI_ERROR(x))
#define ASSERT_PROTOCOL_ALREADY_INSTALLED(handle,guid) ((void)0)
static int gEfiResetArchProtocolGuid, gEfiResetNotificationProtocolGuid;
static int gEdkiiPlatformSpecificResetFilterProtocolGuid;
static int gEdkiiPlatformSpecificResetHandlerProtocolGuid;
static struct {int ResetNotification;} mResetNotification;
static struct {int ResetNotification;} mPlatformSpecificResetFilter;
static struct {int ResetNotification;} mPlatformSpecificResetHandler;
static void platform_reset(void) {}
static void RuntimeServiceResetSystem(void) {}
static struct {void (*ResetSystem)(void);} runtime;
static typeof(runtime) *gRT = &runtime;
static EFI_STATUS locate_status;
static int install_count;
static EFI_STATUS locate(void *guid, void *registration, void **interface) {
  (void)registration; assert(guid == &gEfiResetArchProtocolGuid);
  *interface = NULL; /* An architectural protocol legitimately has no interface. */
  return locate_status;
}
static EFI_STATUS install(EFI_HANDLE *handle, ...) {
  (void)handle; ++install_count; return EFI_SUCCESS;
}
static struct {EFI_STATUS (*LocateProtocol)(void *,void *,void **);
 EFI_STATUS (*InstallMultipleProtocolInterfaces)(EFI_HANDLE *,...);} services={locate,install};
static typeof(services) *gBS=&services;
'''
suffix = r'''
int main(void) {
  EFI_SYSTEM_TABLE st={0};
  runtime.ResetSystem=platform_reset; locate_status=EFI_SUCCESS;
#ifdef LMI_TEST_ORIGINAL
  assert(InitializeResetSystem(NULL,&st)==EFI_SUCCESS);
  assert(runtime.ResetSystem==RuntimeServiceResetSystem && install_count==1);
  puts("ORIGINAL_RELEASE_INITIALIZER_REPLACES_PLATFORM_SERVICE_REPRODUCED");
#else
  assert(InitializeResetSystem(NULL,&st)==EFI_ALREADY_STARTED);
  assert(runtime.ResetSystem==platform_reset && install_count==0);
  locate_status=EFI_DEVICE_ERROR;
  assert(InitializeResetSystem(NULL,&st)==EFI_DEVICE_ERROR);
  assert(runtime.ResetSystem==platform_reset && install_count==0);
  locate_status=EFI_NOT_FOUND;
  assert(InitializeResetSystem(NULL,&st)==EFI_SUCCESS);
  assert(runtime.ResetSystem==RuntimeServiceResetSystem && install_count==1);
  puts("ACTUAL_RESET_INITIALIZER_PLATFORM_PRESERVED_FALLBACK_AND_ERROR_PASS");
#endif
}
'''
with tempfile.TemporaryDirectory(prefix='lmi-reset-guard-') as tmp:
    folder = Path(tmp)
    for name, body, flags in [('original', original_function, ['-DLMI_TEST_ORIGINAL']),
                              ('candidate', function, [])]:
        cfile, binary = folder / (name + '.c'), folder / name
        cfile.write_text(prefix + body + suffix)
        subprocess.run(['cc', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
                        '-Wno-unused-parameter', *flags, str(cfile),
                        '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True)
try:
    module.patch(raw + b'\n')
except ValueError:
    print('UNREVIEWED_SOURCE_REJECTED_PASS')
else:
    raise AssertionError('Tampered input accepted')
