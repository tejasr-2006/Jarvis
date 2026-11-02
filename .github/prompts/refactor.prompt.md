---
name: refactor
description: Refactor JARVIS code while preserving externally observable behavior.
argument-hint: Describe the code to refactor and the desired maintainability improvement.
agent: agent
---

Refactor the requested JARVIS code without changing externally observable behavior:

1. Inspect callers, tests, API contracts, and nearby conventions to establish current behavior.
2. Identify the specific maintainability problem and choose the smallest cohesive change.
3. Preserve validation, authorization, error behavior, data formats, and integration boundaries.
4. Update tests only where needed to protect existing behavior or cover the refactored path.
5. Run relevant tests/checks and review the final diff for unrelated changes.

Avoid speculative abstractions and broad rewrites. Explain any unavoidable behavior change before making it; otherwise keep behavior unchanged and report how that was verified.
