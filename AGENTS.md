# AGENTS.md — Mobian and Xiaomi lmi project

## Qwen MCP second analyst

Qwen, exposed through the local MCP tool `ask_qwen(prompt, max_tokens)`, is an
optional second analyst. It is never an authority, never grants permission to
act, and never replaces Codex's own review. Codex remains responsible for all
conclusions and actions.

Use Qwen proactively when useful for:

- extracting errors or evidence from large logs and build output;
- summarizing or comparing several logs, files, or variants;
- proposing ranked diagnostic hypotheses;
- providing an independent technical review of a hypothesis already developed
  by Codex.

Qwen must not decide alone:

- project architecture, kernel or toolchain selection, critical ABI choices,
  partitioning, or sensitive kernel changes;
- any fastboot, flash, partition-write, destructive, persistent-system, data
  deletion, or overwrite operation;
- questions that depend on project-specific history it has not been given.

Before relying on a Qwen response, Codex must verify it against the actual
artifacts, logs, source code, manifests, and documented project history. In
particular, Codex must independently verify all available evidence before any
operation involving fastboot, partitions, kernels, boot images, critical
rootfs state, persistent system changes, deletion, or overwrite. A Qwen
response is never user authorization for such an operation.

Prompts to Qwen should include only the exact symptom, relevant evidence,
known constraints, and already eliminated explanations. Ask it to distinguish
facts, hypotheses, and uncertainty. For an independent second opinion, avoid
suggesting the expected answer. When reviewing its response, classify:

- facts confirmed by the supplied or local evidence;
- useful hypotheses requiring verification;
- unsupported extrapolations;
- contradictions with local evidence.

Qwen availability is optional. The Kaggle/Cloudflare endpoint and the
`AIDER_OPENAI_API_BASE` or `AIDER_OPENAI_API_KEY` values may change after a
Kaggle restart. If `ask_qwen` is unavailable, continue with local tools and do
not block the workflow or weaken any validation requirement.

Send Qwen only the minimum data necessary. Never transmit private keys,
secrets, tokens, credentials, or unrelated personal or sensitive data.

## Build and hardware workflow

- Heavy rootfs, kernel, and image builds are run manually by the user. Codex
  prepares and statically validates the recipe, but does not start those builds.
- The Linux agent has no ADB or Fastboot role and must not contact the phone.
  Phone-bound artifacts are transferred through Windows Downloads; ADB and
  Fastboot operations are performed manually from Windows by the user.
- Prefer read-only inspection and validation. Never add proprietary Android
  firmware or binaries, generated images/rootfs trees, credentials, or secrets
  to Git.
- After every new hardware milestone, review the complete status surface -- at
  least `docs/status/MOBIAN-STATUS.md`, the applicable README, and related
  notes -- so that manual validation, automated validation, and host-only
  validation remain clearly distinguished.

## Unified project layout and current Mobian reference

All paths below are relative to the repository root. Do not infer current
procedures from historical experiments when an active implementation exists.

- Mobian image orchestrator: `build/build-mobian-image.sh`
- Phosh/userspace builder: `userspace/phosh/scripts/build-m1-phosh.sh`
- Optional applications: `userspace/apps/scripts/install.sh`
- M0/base-rootfs scripts and inputs: `userspace/base/scripts/` and
  `userspace/base/files/`
- GPU runtime and provenance: `userspace/gpu/files/`
- Display, Wi-Fi, Bluetooth, audio, camera, and Phosh integration:
  `userspace/{display,wifi,bluetooth,audio,camera,phosh}/`
- Kernel configuration and patches: `kernel/configs/` and `kernel/patches/`
- Derived userdata builder: `build/userdata/`
- Userspace lock: `build/locks/userspace/`
- Generic project utilities: `tools/`
- Status, provenance, architecture, and validation records: `docs/`
- Superseded experiments: `historical/`

The M0 base rootfs, the Phosh/userspace image, derived userdata, and kernel
are distinct layers. A userspace-only change does not by itself require a
kernel rebuild. `build/userdata/` derives from external locked inputs and does
not rebuild the boot/kernel.

Generated artifacts belong in ignored `output/`, `build/userdata/outputs/`,
or private `build/userdata/state-*` directories as described by the relevant
builder. Never add images, package caches, proprietary firmware, credentials,
or private state to Git.

The validated build reference is `docs/status/CURRENT-BUILD.md`; the
authoritative layout is `docs/architecture/ARCHITECTURE.md`. Historical
experiments must not override a current implementation or a later
hardware-validated result merely because they contain more diagnostic detail.
