# Private GLES thumbnail target for lmi

## Evidence before another package build

A raw shared-memory thumbnail is already striped before Phosh paints it (210x439, stride840). No screenshot/client-side rescaling repair is applied. The unsuccessful linear and row-readback packages were reverted; software rendering was unusably slow and did not qualify pixel correctness.

A small standalone process reproduces corrupt pixel values with uniform-color targets through the actual wlroots0.18 GLES2 renderer, GBM LINEAR ARGB buffers and the running compositor's Zink/Turnip environment. This does not use Phosh or real app content. Direct reads of that shared target, a pre-submit glFinish, and a100ms delay did not remove corruption. Failed DMA sync export messages are observations, not a demonstrated root cause.

An internal GL texture/FBO gives zero incorrect pixels for RGB fills at192/210/256x439. Redirecting the same wlroots drawing pass to that internal target gives zero incorrect pixels for fills, scaled32x64/1080x2259 textures, and an asymmetric four-quadrant pattern:12 exact GPU cases, including orientation. The compositor PID stays unchanged throughout these offscreen controls. See gpu-evidence.json and the minimal probe sources. They localize a failing shared-target path in these conditions; they do not prove every buffer/format or the exact Mesa/kernel defect.

## Candidate implementation

Only the per-view thumbnail function changes. The GBM allocation remains as a carrier for wlroots pass dimensions/context. During GLES drawing a same-size private GL framebuffer is bound, existing surface draw operations are reused, and BGRA pixels are copied directly to the client's declared SHM stride before pass submission. The original framebuffer and pack alignment are restored and private GL objects deleted. Non-GLES renderers retain the standard path. The failed row helper is removed. No CPU renderer, display/output renderer change, kernel change, radio or battery policy adjustment.

This relies on the pinned0.18 GLES render-pass context and immediate draw behavior, verified by the offscreen control; do not silently reuse it across wlroots major changes. SHM access, GL allocation, framebuffer completeness and pass failures have cleanup paths. The actual modified render unit passed syntax-only compilation with the existing Meson command/headers. Standard package tests remain enabled for the operator build. Real application thumbnails remain UNVALIDATED until installation and screenshots.

## Operator build

Run `sudo python3 userspace/phosh/thumbnail-internal-target-candidate/build-packages.py --execute`. It builds only Phoc; no phone install, kernel or image build. Default invocation verifies source pins, exact scratch patch output, qualified cursor DnD and rollback.

Source baseline is the already built rejected row candidate, but the rollback package is explicitly the currently installed +thumblinear1. Do not substitute the rejected row package as rollback. The new version is +thumbrows1+thumbfbo1 for monotonic source-changelog history; the row workaround itself is removed.

Activation must use the protected graphics restart (temporary power-key/shutdown inhibition, wait for GNOME teardown, bounded retry after clean exit and stable shell verification), with automatic package rollback. Check actual runtime binary, unchanged temporary kernel/profile, clean thumbnails/orientation, responsiveness and home drag/drop. Do not promote complete-image pins before acceptance. The next overnight battery observer must be armed only after graphical work and logging cleanup are finished, recording actual package versions.
