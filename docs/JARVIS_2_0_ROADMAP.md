# JARVIS 2.0 Architecture Audit and Roadmap

**Audit snapshot:** 2026-11-02  
**Scope:** Current JARVIS workspace source, dependency manifests, tests, and product/design documentation. This is a source review, not a penetration test or a live integration certification.

## Executive summary

JARVIS is currently a Python/FastAPI modular monolith with SQLite-backed domains, static web clients, an optional desktop shell, and API adapters for independently operated services. Its most mature safeguards are shared-key API authentication, read-only allow-listed AI tools, explicit confirmation on several action routes, local-first memory defaults, and opt-in external context sharing.

It is not yet a single orchestration system. The legacy `/command` classifier/executor, deterministic `/assistant/command`, LLM-driven `/assistant/agent/chat`, and proposal/approval `/agent` flow have overlapping but different capabilities. The first implementation in this mission fixes a confirmed Fitness Manager configuration mismatch in the deterministic assistant. The remaining roadmap prioritizes making behavior consistent and verifiable before increasing autonomy.

## Current architecture

| Layer | Current implementation |
|---|---|
| Application | `app/main.py` mounts FastAPI routers, serves static pages, audits selected request metadata, and starts in-process reminder/monitor/background loops. |
| API | `app/api/` contains domain endpoints for tasks, planning, routines, reminders, calendar, integrations, memory, knowledge, agents, security, dashboards, and assistant workflows. Most control/data routes require `JARVIS_API_KEY`. |
| AI | `app/services/ai_service.py` abstracts Gemini and Ollama. The command classifier returns constrained JSON; `app/agent/orchestrator.py` separately plans allow-listed tool calls, validates them, executes read-only handlers, and synthesizes a response. |
| Tool safety | `app/agent/` defines tool contracts, argument validation, policies, execution, and metadata traces. Current registered AI tools are read-only and configured through `JARVIS_ENABLED_TOOLS`. |
| Local domains | Separate SQLite-backed stores support tasks, plans, routines, reminders/notifications, memory/context, knowledge, finance, computer actions, scheduling, and agent history. |
| Integrations | Email Manager uses a server-side API key; Fitness Manager uses server-side login credentials with a short token cache and a legacy token option; Google Calendar uses local OAuth files; Home Assistant is optional and entity-allow-listed. |
| Automation | Lifespan-managed loops process reminders, health checks, local background cycles, and opt-in email count monitoring. Current automations create in-app notifications rather than sending messages or performing arbitrary actions. |
| Voice and UI | `app/static/` contains standalone dashboard, workspace, unified JARVIS, mobile, voice, computer, and knowledge pages. Browser speech APIs are browser-dependent; the optional desktop wake-word listener uses local Vosk/sounddevice. The current UI has a dark intelligence visual direction and responsive CSS, but does not yet implement the design brief's signature animated presence system. |
| Tests | Pytest currently covers basic app behavior, hybrid knowledge search (worktree changes), integration auth formatting, and the Fitness Manager assistant-routing regression. Most API domains, calendar/OAuth, background lifecycle, and browser behavior still lack focused automated coverage. |

### Implemented versus planned

- **Tasks and routines:** Local create/list/complete/enable/notification flows exist. The AI task planner is a proposal followed by explicit approval; it is not an autonomous scheduler.
- **Day planning:** `/daily-planner/plan` returns a proposed schedule from local tasks, request-supplied routine blocks, and optional calendar/email/fitness reads. It does not persist the proposal or modify those sources.
- **Email and fitness:** JARVIS adapters read from separate services. The examined JARVIS flows do not send email or modify workout records.
- **Calendar:** Optional OAuth status, bounded event listing, and event creation with conflict detection exist. Calendar creation currently writes through its API route rather than the shared agent approval pipeline; define and test the intended confirmation UX before broadening it.
- **AI tool calls:** Tool use is constrained by a local registry and read-only policy. This is a JARVIS JSON planning/execution layer, not unrestricted model execution.
- **Memory:** Explicit facts and preferences live in local SQLite; cloud context is opt-in. Bounded assistant context is stored separately. Agent traces omit raw upstream tool results but retain the user's goal and planned tool arguments.
- **Voice:** Browser speech recognition/synthesis is optional and browser-dependent. The desktop wake listener can be offline when optional dependencies and a local model are installed. Voice capture prepares commands for review; it does not automatically submit them in the inspected UI.

## Audit findings

### Fixed in this mission

1. **Fitness Manager login configuration disagreed across assistant entrypoints.** `UnifiedAssistant.handle()` required the legacy `FITNESS_MANAGER_API_TOKEN`, while `FitnessManagerClient` and `CommandExecutor` support `FITNESS_MANAGER_EMAIL` plus `FITNESS_MANAGER_PASSWORD`. Users configured with the current login flow were incorrectly told they lacked authentication. The guard now accepts either complete login credentials or the legacy token. Regression tests cover both the supported login path and missing credentials.

### Prioritized outstanding work

1. **Unify assistant orchestration contracts (P1).** Select a canonical request-to-plan-to-policy-to-tool-to-response pipeline. Route legacy and deterministic flows through shared capability checks or clearly deprecate them. Preserve explicit approval and read-only defaults; add compatibility tests for each public entrypoint before migration.
2. **Define sensitive-data retention and deletion (P1).** Trace records retain command goals and planned arguments; conversation context and saved conversations have separate stores and controls. Document exactly what is retained, add retention/deletion controls for traces, and test that email/workout payloads and credentials never enter persisted history.
3. **Strengthen safety and API contract tests (P1).** Add tests for authorization on all sensitive routes, confirmation on every externally visible write, AI malformed/hostile plans, unknown/disabled tools, provider failures, and retry/idempotency behavior. Confirm the intended confirmation contract for direct calendar event creation.
4. **Integration resilience and observability (P2).** Add mock-service contract tests for email, fitness, calendar, and Home Assistant; bound end-to-end request time; log integration failures without personal payloads; validate response shapes and status semantics.
5. **Database lifecycle and configuration (P2).** SQLite schemas are initialized in store code with `CREATE TABLE IF NOT EXISTS`; introduce versioned migrations before schema evolution, validate environment values at startup, and document supported Python/dependency ranges.
6. **Route ownership cleanup (P2).** `app/main.py` registers `/dashboard` twice with handlers serving the same page. Remove the shadowed duplicate during route cleanup and add route-level checks so UI paths have one owner.
7. **Background execution model (P2).** In-process lifespan loops are simple for a single local JARVIS process; the README already recommends one Uvicorn worker. Preserve that deployment constraint, make scheduled work idempotent across restarts, and add lifecycle/shutdown tests before supporting multiple workers.
8. **Frontend product alignment (P2).** Consolidate overlapping dashboard/workspace/JARVIS surfaces around a shared navigation and interaction model. Incrementally implement the design brief's JARVIS presence/motion system with reduced-motion and keyboard-accessibility support; retain text-first and voice-fallback workflows.
9. **Release validation (P2).** Expand CI from the currently small test set to focused unit/API/integration-contract checks, static checks, and supported-runtime validation. External integrations must remain mocked in CI and be separately verified with user-provided local configuration.

## Proposed implementation sequence

### Phase 0 — Reliability baseline

- [x] Fix Fitness Manager credential gating in deterministic assistant dispatch.
- [x] Add regression coverage for credential acceptance and missing-credential rejection.
- [ ] Add authorization and safe-failure tests around all sensitive APIs.
- [ ] Add a test inventory and CI workflow that runs the supported Python test matrix.

### Phase 1 — One safe orchestration path

- [ ] Document public assistant entrypoints, capability differences, and response schemas.
- [ ] Define a versioned orchestration contract and map existing APIs to it.
- [ ] Centralize tool authorization, argument validation, approval, timeouts, traces, and error mapping.
- [ ] Keep write tools disabled by default; require explicit approval for external or destructive effects.
- [ ] Migrate one read-only workflow at a time with API compatibility tests.

### Phase 2 — Privacy and dependable integrations

- [ ] Specify retention for goals, traces, conversation context, and saved conversations; add authenticated deletion/retention controls.
- [ ] Add mock-based integration contract tests and clear degraded/partial-result behavior.
- [ ] Establish calendar event confirmation and conflict-override UX before enabling calendar writes from the assistant.
- [ ] Add startup validation for provider/integration configuration and redact sensitive fields from diagnostics.

### Phase 3 — Product and operations

- [ ] Document local setup, privacy boundaries, and which capabilities require separate services/configuration.
- [ ] Improve background scheduler restart, idempotency, and multi-worker behavior.
- [ ] Bring the frontend closer to the design brief with accessible motion, consistent status/error states, and a single canonical assistant experience.
- [ ] Add migration/versioning policy and CI quality gates.

## Validation record

- Baseline before this mission's changes: `python -m pytest -q` — **13 passed**.
- Focused after the Fitness Manager routing fix: `python -m pytest tests\test_unified_assistant.py tests\test_integrations.py -q` — **4 passed**.
- Final full suite: `python -m pytest -q` — **17 passed**, with two existing FastAPI/Starlette deprecation warnings.
- Syntax check: `python -m compileall -q app tests` — passed.
- Diff check: `git diff --check` — passed.
- Integration adapter tests verify the existing Fitness Manager bearer-token refresh behavior and Home Assistant authorization header; the displayed source may redact authorization values, so runtime tests were used rather than the rendered text.
- External services and OAuth credentials were not used.

## Audit boundaries

No separate Email Manager/Fitness Manager repositories, Google credentials, Gemini credentials, or live external services were available in this JARVIS workspace. Their production availability, remote API behavior, and OAuth refresh behavior remain unverified. The audit did not inspect `.env` or other secret-bearing runtime files, modify external applications, or run a penetration test.
