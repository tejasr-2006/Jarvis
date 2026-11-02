---
name: security-review
description: Review the requested JARVIS code or changes for actionable security vulnerabilities.
argument-hint: Specify files, a diff, or the security-sensitive behavior to review.
agent: agent
---

Review the requested JARVIS code or diff for concrete, exploitable security vulnerabilities. Trace relevant inputs and authorization/data flows as needed. Do not make changes during the review.

Prioritize:
- Authentication, authorization, approval, and tool allow-list enforcement.
- Injection, unsafe command or computer actions, path traversal, and unsafe deserialization.
- Secret exposure, personal data leakage, and sensitive logging/storage.
- Trust boundaries around AI-generated, user-provided, and external integration data.
- Remote exposure, insecure defaults, and regressions in existing safeguards.

Report only actionable findings, each with severity, file and line, affected scenario, impact, and confidence. Distinguish confirmed issues from questions or hardening suggestions. If no vulnerabilities are found, say so and note the scope and validation limitations.
