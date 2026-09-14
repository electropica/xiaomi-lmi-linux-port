# Mobian M1 A650 Turnip/KGSL dma-buf hardware validation — 2026-09-08

## Scope

This note records the first hardware validation on Xiaomi `lmi` (SM8250 /
Adreno 650) of Turnip/KGSL exporting Vulkan memory as a dma-buf and importing
the same dma-buf back into Vulkan:

```text
Turnip/KGSL
    -> exportable Vulkan buffer allocation
    -> DMA_BUF fd export
    -> DMA_BUF fd re-import
    -> GPU access through the imported buffer
    -> host-visible readback
    -> deterministic content verification
```

This is a headless, process-local external-memory test. It does not involve
Wayland, EGL, GBM, DRM/KMS, `msm_drm`, scanout or Phoc.

## Relationship to GPU-54 through GPU-57

GPU-54 established that the isolated Mesa Turnip 25.0.7 driver could open
`/dev/kgsl-3d0` and enumerate the real Adreno 650. GPU-55 then submitted and
verified a real GLES render through EGL surfaceless, Zink and Turnip/KGSL.

GPU-56 statically established that the KGSL backend implements dma-buf
allocation, export and import, while leaving hardware interoperability with
downstream `msm_drm` and cross-driver synchronization unproven. GPU-57 created,
cross-compiled and audited the isolated self-test used for this validation.

## Test identity

The one-shot ARM64 self-test transferred for GPU-58 was:

| Property | Value |
|---|---|
| Phone path | `/root/gpu57-dmabuf-selftest.arm64` |
| Architecture | AArch64 |
| SHA-256 | `92aa34aa64c4c0510815dc2ecd6f20b42ea3a198d1b7dce60c1c572cc06834fa` |

The binary is a transient validation artifact and is not stored in Git.

## Self-test architecture

The test uses `VkBuffer` objects rather than images. This avoids image
modifiers, UBWC, WSI and display-stack dependencies. The shared resource is
4096 bytes and the deterministic payload contains 1024 index-dependent
32-bit words.

The data path is:

1. create a host-visible staging buffer containing the pattern;
2. create buffer A with
   `VkExternalMemoryBufferCreateInfo(DMA_BUF)`;
3. allocate A with `VkExportMemoryAllocateInfo(DMA_BUF)`;
4. copy the pattern from staging into A on the GPU and wait for a Vulkan fence;
5. export A's allocation with `vkGetMemoryFdKHR`;
6. duplicate the application-owned fd for import;
7. query its `memoryTypeBits` with `vkGetMemoryFdPropertiesKHR`;
8. create buffer B with the same external-memory handle type;
9. import the duplicate with `VkImportMemoryFdInfoKHR` and bind it to B;
10. copy from B on the GPU into an independent host-visible readback buffer;
11. wait for a second Vulkan fence and compare every 32-bit word.

The external-buffer properties had to advertise both EXPORTABLE and
IMPORTABLE for `VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT`. The hardware
reported `DMA_BUF_DEDICATED_ONLY=NO`.

## File-descriptor lifecycle

`vkGetMemoryFdKHR` returned a dma-buf fd owned by the application. The test
kept that original fd and passed a `dup()` to
`VkImportMemoryFdInfoKHR`. Successful `vkAllocateMemory` transferred ownership
of the duplicate to Vulkan, while the original remained application-owned and
was closed exactly once during cleanup.

The observed lifecycle markers were:

```text
FD_IMPORT_COPY_CREATED=YES
FD_IMPORT_OWNERSHIP_TRANSFERRED_TO_VULKAN=YES
FD_EXPORT_CLOSED=YES
GPU57_CLEANUP=PASS
```

## Synchronization boundary

Both GPU copies used Vulkan command buffers and finite fence waits. The first
fence completed before dma-buf export/import; the second completed before the
readback mapping was inspected. This validates synchronization sufficient for
this single-process Vulkan test.

It does not validate dma-buf reservation-object synchronization, implicit or
explicit synchronization with another driver, Wayland synchronization, or KMS
fence handling.

## GPU-58C hardware result

The relevant output was:

```text
TU: info: Created an instance
GPU57_VULKAN_INSTANCE=PASS

TU: info: Found compatible device '/dev/kgsl-3d0'.
DEVICE_NAME=Turnip Adreno (TM) 650
TURNIP_DEVICE_FOUND=YES
GPU57_TURNIP_DEVICE=PASS

GPU57_EXTERNAL_BUFFER_PROPERTIES=PASS
DMA_BUF_EXPORT_SUPPORTED=YES
GPU57_EXPORT_CAPABILITY=PASS
DMA_BUF_IMPORT_SUPPORTED=YES
GPU57_IMPORT_CAPABILITY=PASS
DMA_BUF_DEDICATED_ONLY=NO

GPU57_EXPORT_MEMORY=PASS
PATTERN_GENERATION=PASS
GPU_WRITE_COMPLETE=YES
GPU57_GPU_WRITE=PASS
DMA_BUF_FD_EXPORTED=YES
GPU57_DMA_BUF_EXPORTED=PASS

FD_IMPORT_COPY_CREATED=YES
FD_IMPORT_OWNERSHIP_TRANSFERRED_TO_VULKAN=YES
DMA_BUF_REIMPORT=PASS
GPU57_DMA_BUF_IMPORTED=PASS

IMPORTED_BUFFER_GPU_READ_COMPLETE=YES
GPU57_IMPORTED_RESOURCE_ACCESS=PASS
IMPORTED_BUFFER_READBACK=PASS
CONTENT_MATCH=PASS
GPU57_CONTENT_MATCH=PASS
GPU57_DMABUF_SELFTEST=PASS

FD_EXPORT_CLOSED=YES
GPU57_CLEANUP=PASS
GPU58_SELFTEST_RC=0
```

## Validated result

GPU-58 validates on real hardware:

- Turnip/KGSL external-buffer capability reporting;
- allocation of exportable Vulkan memory;
- a real dma-buf fd export;
- correct application/Vulkan fd ownership transfer in the successful path;
- re-import of the same dma-buf into a second Vulkan allocation;
- GPU access through the imported resource;
- Vulkan synchronization sufficient for this test;
- deterministic readback with identical content;
- successful cleanup and process return code zero.

## Validation boundary

GPU-58 does **not** validate:

- import of this dma-buf by downstream `msm_drm`;
- hardware PRIME fd-to-handle conversion;
- framebuffer creation or KMS scanout;
- display format or modifier interoperability;
- UBWC interoperability;
- dma-buf reservation-object or implicit synchronization with KMS;
- explicit Wayland synchronization;
- onscreen presentation or accelerated Phoc.

The next step is to prepare an isolated PRIME-import test which passes a
Turnip/KGSL dma-buf to `msm_drm/card0` without creating a framebuffer, scanning
it out, or modifying the running graphical session.
