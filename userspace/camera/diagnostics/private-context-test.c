#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Private no-camera HIDL startup diagnostic only. This is not a production
 * access-control policy and must never be injected into the host session. */
int getcon(char **context) {
    fputs("PRIVATE_HIDL_TEST_SYNTHETIC_CONTEXT_NO_CAMERA_ACCESS\n", stderr);
    *context = strdup("u:r:hwservicemanager:s0");
    return *context ? 0 : -1;
}
