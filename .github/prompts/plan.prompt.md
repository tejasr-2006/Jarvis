---
name: plan
description: Inspect a JARVIS task and produce a focused implementation plan without changing files.
argument-hint: Describe the feature, bug, or change to plan.
agent: ask
---

Plan the requested JARVIS change. Inspect relevant source, tests, documentation, and repository conventions before proposing steps.

Include:
- A short summary of the request and observable acceptance criteria.
- The affected files/modules and important call paths.
- A step-by-step implementation and test plan, including the smallest relevant test command.
- Compatibility, security, integration, or migration risks and how to verify them.
- Any genuine ambiguity that blocks implementation.

Keep the plan focused. Do not edit files or present unverified assumptions as facts. Preserve JARVIS's modular, API-first design and permission boundaries.
