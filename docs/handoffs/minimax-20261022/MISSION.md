# MiniMax battery investigation — three-day ownership

## Objective

Advance the Xiaomi lmi Mobian standby power investigation. Julien operates the phone and runs heavy builds. MiniMax may investigate, implement focused fixes, prepare reproducible recipes and validate its work on this dedicated branch. Review progress with Julien on October 25, 2026; report intermediate actionable findings and blockers. Do not promise continuous execution when the client session is stopped.

## Branch and source of truth

Work only on `codex/minimax-battery-20261022`, based on `0e9c3e73c2f208c0ca00636ad06015278574c69c`. Do not merge to or rewrite main/developpement. Read AGENTS.md, docs/status/CURRENT-BUILD.md and the current status documents first. Preserve the validated kernel/image references and recipes. A focused userspace change does not require a new kernel build.

Julien has additional private evidence and a detailed handoff in the Windows workspace: work/MINIMAX-THREE-DAY-PLAN-20261022.md, work/BATTERY-RESULTS-LEDGER-20261022.md and work/coordinator-state.md. Read these locally before making claims. Do not commit those raw private logs or upload them for external review. If the private evidence is unavailable, document that limitation rather than recreating results from memory.

## Execution and evidence

Choose tasks by their ability to discriminate a causal hypothesis, not by volume of reports. Complete an investigate/implement/validate cycle before opening another broad audit. Reuse retained evidence before proposing a new test. Record negative and incomplete results too. Keep a persistent next-action note so a short 'Continue' resumes useful work.

Maintain an English progress ledger in this directory with: hypothesis, source/artifact identity, evidence, changes, validation, limitations and next decision. Commit coherent source/docs changes with meaningful messages. Keep raw captures, identifiers, generated artifacts and secrets outside Git. Inspect staged diffs before each commit/push. Do not blanket-stage the repository. Push checkpoints only to this branch. No destructive cleanup or history rewriting.

The first useful task is to finish the narrow UFS comparison: the retained Android capture is unprivileged and policy values were denied; some summary ABSENT labels contradict listed names. Fix classification offline and obtain comparable authorized snapshots before interpreting policy differences. Absence under Android does not establish absence under Mobian. Plugged snapshots do not establish sleeping physical state. USB SSH needs the cable connected. A successful tool execution is not a confirmed hardware diagnosis.

Then rank at most three actual unresolved client/configuration differences from the existing peripheral checklist. Propose a single bounded discriminator only if it resolves a specific uncertainty. Do not repeat general RPMh/GPU audits or identical discharges without new evidence. Gauge-derived current is not calibrated per-rail power.

## Operator boundary

Julien continues with MiniMax as his project assistant: explain required actions briefly, prepare commands and restoration, and ask for the specific build or physical step when needed. Do independent offline work while waiting. Never flash, repartition, delete, install persistent changes, change power policy or permissions, or reboot without Julien's specific authorization for that operation. Do not contact the phone during an unplugged observation. Existing authorized read-only access may be used within its scope. Keep known working artifacts and recovery paths.

## Separate boot-menu state

Do not confuse menu work with battery evidence. The old resetguard image beginning SHA256 40cbcc40 has a restart-only Mobian entry and must not be installed permanently. The outer-Mobian candidate SHA256 ece3f4c4e6e2f6ed485d159b0b2f3f682ba8f758962a395490937120d44f423e is host-qualified but handset validation is pending. Direct Mobian requires the lmi_menu=outer-v1 command-line marker, correct dedicated root and normal UI, then all four entries tested on that exact candidate. No permanent installation is qualified by this handoff.

## Review deliverable

On October 25, provide Julien a concise account of confirmed progress, tested changes, unsupported/rejected hypotheses, unresolved blockers and the best next action. Link commits and validation records. If no causal fix emerged, say so plainly; preserve a reproducible investigation rather than claiming success from audit completion.
