---
name: tdd
description: Implement a JARVIS change using a test-first workflow.
argument-hint: Describe the behavior to add or fix.
agent: agent
---

Implement the requested JARVIS behavior using a test-first workflow:

1. Inspect the relevant implementation, tests, and existing conventions.
2. Add or update a focused test that expresses the expected behavior; run it and confirm it fails for the intended reason.
3. Make the smallest implementation change that makes the test pass.
4. Run the focused test and relevant neighboring tests, then inspect the final diff.

Use the project's existing test tools (`python -m pytest` where applicable). Preserve API contracts, modular boundaries, authorization checks, and established error handling. Do not weaken or delete tests merely to obtain a pass. Report commands and results, including any external-service limitations.
