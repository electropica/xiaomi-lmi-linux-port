#ifndef LMI_CAMERA_QTI_BRIDGE_H
#define LMI_CAMERA_QTI_BRIDGE_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Returns 0 on success, QTI positive Error enum on vendor failure,
 * or negative errno for bridge argument/state/ABI failures.
 * Allocate BLOB bytes x 1. Handle remains opaque and bridge-owned until release.
 * The caller must wait the camera's release fence before CPU lock.
 * No release while camera owns the handle or while CPU locked.
 */
int lmi_qti_allocate(uint32_t bytes, uint64_t usage, const void **handle);
int lmi_qti_release(const void *handle);
int lmi_qti_lock(const void *handle, void **address);
int lmi_qti_lock_cpu(const void *handle, void **address); /* Same as lock. */
int lmi_qti_unlock(const void *handle);
/* Validated actual QTI allocation size, at most128MiB and offset0.
 * Query alone does not grant access: read only after successful CPU lock.
 */
int lmi_qti_get_capacity(const void *handle, uint32_t *capacity);
#ifdef __cplusplus
}
#endif
#endif
