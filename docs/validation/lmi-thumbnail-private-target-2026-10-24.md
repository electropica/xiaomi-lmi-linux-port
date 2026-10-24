# Application thumbnail corruption localized below Phosh - October 24, 2026

## Device facts

The row-readback candidate was built, activated, visually rejected and rolled back. A bounded pixman trial was too slow for useful pixel validation and was restored. The GPU renderer, original package and temporary battery kernel/profile are restored; no diagnostic/debug override remains.

A read-only capture of a named Phosh SHM mapping, matched to the logged protocol dimensions, yields an already striped raw image:210x439 pixels, stride840,368760 bytes. Only that named shared graphics mapping was read, not process heap/general memory. The observed data localizes this image corruption before Phosh's Cairo/widget painting. Actual app identity is not inferred from the operator's selected confirmation.

## Standalone controls, without shell restarts

Tiny native programs use the installed wlroots0.18 GLES2 renderer and the same allowlisted Zink/Turnip environment as Phoc. They render synthetic colors offscreen, never acquire a display output or reconfigure the running compositor. Its PID remains unchanged in all controls. Source and numerical results are in the [candidate directory](../../userspace/phosh/thumbnail-internal-target-candidate/README.md).

A LINEAR ARGB8888 GBM target produces wrong pixel values even for uniform red, and for scaled small/large green textures, at widths192,210,256 and height439. The read API reports success. glFinish before submit and a100ms delay do not remove the failure; direct reading of the shared framebuffer also fails. Thus a fixed row-copy or added wait alone is not justified. DMA_BUF_IOCTL_EXPORT_SYNC_FILE errors are logged, but their causal role is not established by these observations.

An ordinary internal GL texture/framebuffer produces exact RGB fills at all three sizes (nine cases). Redirecting the existing wlroots render-pass operations to that internal target and reading before pass submission gives exact fills, scaled textures and asymmetric quadrants in twelve cases, all pixels checked and zero errors. The quadrants verify orientation as well as color. Renderer reports Zink Vulkan1.3/Turnip Adreno650. These controls identify a reproducibly failing shared-target path and a working private-target path under these conditions, not the exact Mesa/kernel defect or every imported-buffer case.

## Targeted candidate and limits

The candidate binds a same-size internal GL framebuffer only for the GLES thumbnail pass, reuses surface drawing, copies BGRA directly to the client-declared SHM stride while the pass context is current, restores GL state and deletes private resources. A carrier allocation remains to establish wlroots pass dimensions/context; its shared pixels are not used. Non-GLES rendering keeps the standard path. No global software renderer or GPU-driver replacement.

Final render.c SHA256 e46eff42a6353c4393c846d45f183f8ef817b4293ffb3b29eed489bb7a2b525b passes syntax-only checking with the actual Meson compilation options. The guarded recipe verifies cursor DnD and uses the currently installed linear package as rollback, despite a rejected row candidate being the source-tree baseline. Package compilation and real app/UI acceptance remain operator steps. Synthetic pixel success does not establish a real-application fix or battery benefit. No complete-image pin is promoted.
