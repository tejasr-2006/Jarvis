---
name: build-fix
description: Diagnose and fix a JARVIS build, test, or validation failure with a minimal change.
argument-hint: Paste the failure output or describe the failing command.
agent: agent
---

Diagnose the reported JARVIS build, test, lint, or type-check failure before editing:

1. Reproduce it with the narrowest relevant command and identify the first meaningful failure.
2. Trace the failure to its cause; separate task-related regressions from pre-existing failures.
3. Make the smallest safe fix without changing unrelated behavior or weakening validation.
4. Rerun the failing command and relevant tests, then inspect the diff.

Follow existing project conventions and preserve modular boundaries, security checks, and API behavior. Report the cause, files changed, commands/results, and any remaining failures or environment limitations. Do not claim a check passed unless it was run.
