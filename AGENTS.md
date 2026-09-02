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
