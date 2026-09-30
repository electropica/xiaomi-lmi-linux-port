# Kernel build boundary

This directory is reserved for a future portable kernel/boot build entry
point. The repository currently tracks selected downstream configuration and
patches under `kernel/`, but it does not yet contain a source-locked,
end-to-end recipe that reproduces the externally validated D-repro boot.

The D-repro boot remains a separate external artifact. The current
`build/userdata/` flow modifies only a copy of the userspace userdata and does
not rebuild or replace that boot. Kernel/DTB diagnostic builds must remain
separate and must not be described as production boot replacements unless
their inputs, output identities, and hardware validation are documented.
