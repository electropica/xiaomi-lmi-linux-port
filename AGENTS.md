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
  least `mobian/STATUS.md`, the applicable README, and related notes -- so that
  manual validation, automated validation, and host-only validation remain
  clearly distinguished.

## Current Mobian lmi userspace build reference

This section describes the repository architecture being prepared for the
current Xiaomi lmi Mobian/Phosh userspace image.

All paths below are relative to the repository root. Do not infer current
procedures from historical experiments when an active implementation exists.

The current userspace/Phosh build entry point in this architecture is:

    phosh/scripts/build-m1-phosh.sh

The optional application installer is:

    apps/scripts/install.sh

`INSTALL_OPTIONAL_APPS=1` makes the Phosh/userspace build invoke this optional
application installation step.

The M0/base-rootfs construction scripts are separate and live under:

    base/scripts/

Their associated base-build files and working inputs live under:

    base/files/

The M0 base rootfs, the Phosh/userspace image, and the kernel are separate
layers. A userspace or application-only change does not by itself require a
kernel rebuild.

GPU runtime files consumed by the current userspace build live under:

    gpu/files/

Wi-Fi and Bluetooth integration are maintained independently under:

    wifi/
    bluetooth/

Display integration is maintained under:

    display/

Generated images and other build outputs belong under:

    output/

The reorganized repository architecture has completed a successful image build and is now the active project layout. The validated build reference is recorded in `docs/CURRENT-BUILD.md`, and the authoritative layout is documented in `docs/ARCHITECTURE.md`.

Historical experiments must not override a current implementation or a later hardware-validated result merely because historical material contains more diagnostic detail.
