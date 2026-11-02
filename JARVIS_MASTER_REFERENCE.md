# JARVIS — Master Project Reference

> This single Markdown file combines the uploaded consolidated application reference and the detailed Phase 1–7 documents. The consolidated reference provides the broader project overview; the phase appendices preserve the original implementation notes and instructions.

## Contents

1. [Consolidated Application Reference](#consolidated-application-reference)

2. [Phase 1 — Agent Foundation](#phase-1--agent-foundation)

3. [Phase 2 — Integration Engine](#phase-2--integration-engine)

4. [Phase 3 — AI Agent Orchestrator](#phase-3--ai-agent-orchestrator)

5. [Phase 4 — Shared Memory & Context](#phase-4--shared-memory--context)

6. [Phase 5 — Autonomous Background Agents](#phase-5--autonomous-background-agents)

7. [Phase 6 — Unified JARVIS Interface](#phase-6--unified-jarvis-interface)

8. [Phase 7 — Voice Intelligence](#phase-7--voice-intelligence)


---


<a id="consolidated-application-reference"></a>


# Consolidated Application Reference


# JARVIS — Consolidated Application Reference

> **Purpose:** Single working reference for understanding the documented JARVIS application, its architecture, features, integrations, security boundaries, setup, and migration considerations.
>
> **Source reviewed:** 42 Markdown files from `Jarvis-main-1.zip` — `PHASE1.md` through `PHASE41.md`, plus `README_PHASES.md`.
>
> **Important scope note:** The uploaded ZIP contained Markdown documentation only. This document consolidates what those files claim is implemented. It does not independently verify the Python source, tests, runtime behaviour, dependency compatibility, or live integrations. Verify those against the source code and running application before making security or migration decisions.

---

## 1. Executive summary

JARVIS is a Python/FastAPI personal assistant designed around a local API, SQLite-backed personal features, configurable AI inference, and separate service integrations.

The documented application has evolved through 41 phases. Its capabilities include:

- Gemini or Ollama AI-provider configuration.
- Explicit personal memory and optional conversation storage.
- Allow-listed tools and conservative command routing.
- Browser voice/text interfaces and optional offline wake-phrase listening.
- Tasks, reminders, routines, notifications, planning, and proactive briefings.
- Optional Google Calendar and Home Assistant integrations.
- Email assistance through a separate Email Manager.
- Fitness data retrieval through a separate Fitness Manager.
- A local manual finance ledger.
- Controlled computer actions.
- Knowledge retrieval and multimodal document/image analysis.
- A dashboard, mobile web interface, desktop shell, and organized workspace.
- API audit records, health checks, backups, and security review endpoints.

The architecture is intentionally modular: Email Manager and Fitness Manager remain separate applications, while JARVIS coordinates them through HTTP APIs.

### Overall assessment

JARVIS is best understood as a **modular personal-assistant backend with a collection of guarded workflows**, rather than a fully autonomous agent. Many features are proposals, read-only views, or locally scheduled notifications. Several external actions require explicit API calls and confirmation.

---

## 2. Application architecture

### 2.1 Documented high-level architecture

```text
User
 ├── Browser dashboard /workspace
 ├── Browser dashboard /dashboard
 ├── Mobile web app /mobile
 ├── Voice console /voice
 └── Optional desktop shell
          |
          v
     JARVIS FastAPI
     (default port 8000)
          |
          +-- AI provider abstraction
          |     +-- Gemini (cloud)
          |     +-- Ollama (can be local)
          |
          +-- Command and tool routing
          |
          +-- Local SQLite data stores
          |     +-- Memory and conversation context
          |     +-- Tasks, reminders, notifications
          |     +-- Routines and planning proposals
          |     +-- Finance ledger
          |     +-- Agent runs and feedback
          |     +-- Audit and action history
          |     +-- Knowledge library
          |
          +-- External/local integrations
                +-- Email Manager (default port 8001)
                +-- Fitness Manager (default port 8002)
                +-- Google Calendar (optional OAuth)
                +-- Home Assistant (optional)
```

### 2.2 Main services

| Service | Documented default | Role |
|---|---:|---|
| JARVIS | `127.0.0.1:8000` | API, AI orchestration, personal-assistant features |
| Email Manager | `127.0.0.1:8001` | Email data and high-priority email integration |
| Fitness Manager | `127.0.0.1:8002` | Workout/fitness data |
| Ollama | `127.0.0.1:11434` | Optional local model inference |
| Google Calendar | Google API | Optional calendar access through OAuth |
| Home Assistant | User-configured | Optional smart-home integration |

The ports and service URLs are documented defaults/configuration examples. Confirm actual values in the current `.env`, settings code, and service launch commands.

### 2.3 Architectural principles visible in the documentation

1. JARVIS keeps Email Manager and Fitness Manager separate.
2. JARVIS calls external services through integration clients rather than owning their databases.
3. Local personal features generally use SQLite.
4. AI-generated plans are validated before they can be used.
5. Natural-language command routing is more restrictive than direct module APIs.
6. Mutating actions are separated from planning or preview steps where documented.
7. Optional integrations should not prevent core local features from running when disconnected.

---

## 3. Feature inventory by domain

### 3.1 AI provider and reasoning

Documented in Phases 1 and 3, and used by later AI-assisted features.

- Gemini is the documented default provider.
- Ollama is an optional local inference provider.
- Provider/model configuration is exposed through `/ai/provider` without revealing secrets.
- AI responses are validated more strictly than raw free-form model output.
- Provider failures are returned through safer application-level errors.
- Memory context can be bounded and selectively included in AI prompts.
- Saved memory is not sent to Gemini by default; cloud memory context requires explicit configuration.
- Ollama memory context is documented as restricted to loopback Ollama URLs.

**Important:** Selecting Ollama only keeps inference local if the configured Ollama endpoint is actually local. Email, Calendar, Home Assistant, and other connectors still communicate with their own services. Gemini prompts are sent to Google's service.

The documentation does not establish which provider/model is currently configured in the user's working environment.

### 3.2 Command routing and tools

- `/command`, `/ai/understand`, and `/ai/classify` are documented as AI/command-related routes.
- `/tools` reports enabled capabilities without exposing credentials.
- `JARVIS_ENABLED_TOOLS` controls an explicit tool allow-list.
- Early tool integrations are read-only: high-priority email retrieval and workout retrieval.
- `/assistant/capabilities` lists supported natural-language examples.
- `/assistant/command` provides a unified text/voice command entry point.
- Supported commands include tasks, routines, notifications, high-priority email, workouts, calendar status, and configured smart-home device-state reads.
- Requests that appear to mutate data or control devices are not executed through the documented unified natural-language dispatcher.

**Design boundary:** A command being understood by the AI does not grant permission to execute it. Tool registration, server-side permissions, and module-specific confirmation rules govern execution.

### 3.3 Personal memory and conversation context

The documentation describes several distinct data systems. They should not be treated as one interchangeable memory store.

| Memory/data feature | Purpose | Documented storage |
|---|---|---|
| Explicit personal facts | User-saved preferences, goals, routines, decisions | `memory.db` |
| Optional conversation history | Saved conversation records, opt-in | Memory database |
| Bounded assistant context | Recent command/session continuity | `conversation_context.db` |
| Knowledge library | Imported Markdown/text documents and searchable chunks | `knowledge.db` |
| Agent feedback | User ratings/comments about agent runs | `agent_learning.db` |
| Personalization feedback | Explicit planning feedback/preferences | `adaptation.db` |

Documented memory capabilities:

- Create, list, search, edit, and delete explicit facts.
- Group profile facts by preference, goal, routine, and decision.
- Conversation storage is opt-in and disabled by default in the documented setup.
- Memory context can be previewed before use.
- Cloud context is controlled separately from local memory.
- Memory export is available.
- Full memory clearing requires the exact confirmation phrase `CLEAR ALL MEMORY`.
- Knowledge documents can be imported, chunked, searched, listed, retrieved, and deleted.
- Knowledge search is documented as keyword-ranked retrieval, not vector/semantic search.
- Conversation context is bounded, with up to 20 stored turns per session and a configurable recent-turn count.
- Context stores command/intent/status/short response summaries, not full tool-result payloads.

**Privacy warning:** Local SQLite storage is not the same as encryption. Phase 2 explicitly says the memory database is not encrypted by that feature. Phase 40's controls govern whether information is used as context and whether new conversations are stored; they do not, by themselves, provide database encryption.

### 3.4 Tasks, reminders, notifications, and routines

**Tasks**
- SQLite-backed task list.
- Create tasks with title, description, priority, and optional timezone-aware due date.
- List pending/completed tasks.
- Complete or delete tasks.
- High-priority tasks sort first.
- Tasks are stored in `tasks.db`.

**Reminders**
- SQLite-backed reminders with ISO-8601 timezone-aware due times.
- Background scheduler checks reminders while JARVIS is running.
- Due reminders are surfaced through notifications.
- Reminder scheduling does not continue when the backend is stopped.

**Notifications**
- Persistent local notification feed.
- Acknowledgement support.
- Proactive due-soon and overdue task notifications.
- Deduplication prevents repeated identical task alerts.
- Optional desktop tray delivery.
- The documented notification features do not send SMS, email, or external push notifications.

**Routines**
- Recurring named routines with a message, local time, and selected weekdays.
- Enable, disable, list, and delete operations.
- Each routine fires at most once per local calendar date.
- Routine notifications are local; routine text is not executed as code or interpreted as an instruction.

### 3.5 Planning and proactive intelligence

Several phases add planning features with overlapping but distinct purposes.

| Feature | Main function | Nature |
|---|---|---|
| AI Task Planner (Phase 9) | Convert a goal into proposed tasks | AI-generated proposal; explicit approval creates tasks |
| Daily Planner (Phase 11) | Combine tasks, calendar, email, fitness, and request-supplied routine blocks | Read-only schedule proposal |
| Proactive notifications (Phase 12) | Due-soon and overdue task alerts | Local scheduled notifications |
| Proactive intelligence (Phase 22) | Rule-based task insights and quiet hours | Local, rule-based |
| Predictive planning (Phase 23) | Rank tasks and fit them into a time budget | Deterministic heuristic proposal |
| Adaptive personalization (Phase 24) | Apply saved focus/time preferences and explicit feedback | Opt-in local personalization |
| Agent workflow (Phase 32) | Propose a bounded goal plan, approve, then execute allowed inspections | Guarded agent workflow |
| Personalized briefing (Phase 34) | Explain task priorities and aggregate feedback | Read-only |
| Smart scheduling (Phase 35) | Create and confirm a workday schedule proposal | Local proposal; no external writes |
| Calendar sync (Phase 36) | Preview conflicts and sync a confirmed schedule | External write only after explicit confirmation |
| Proactive agent dashboard (Phase 39) | Show briefing and explicitly generate local notifications | Local notification generation |

Important limitations:
- Several ranking and scheduling functions are explicitly rule-based, not trained predictive models.
- Task duration estimates are heuristics.
- A proposal is not the same as an executed action.
- Phase 32's agent is deliberately limited to `review_tasks`, `review_routines`, `review_notifications`, and a `manual_step` result.
- The Phase 32 agent cannot use arbitrary URLs, shell commands, arbitrary tool names, or AI-generated code as execution actions.
- Calendar sync is a separate, explicit workflow.

### 3.6 Email Manager integration

Email Manager remains a separate service. JARVIS's documented email functionality includes:

- Health checks and service status.
- Retrieval of high-priority email metadata/content through the Email Manager's specific endpoint.
- Email labels such as urgent action, meeting scheduling, finance, work, and general.
- Heuristic identification of likely reply requests.
- AI-assisted reply draft generation.
- Local draft storage and review.
- Approve/reject draft workflow.
- Follow-up suggestions.
- Read-only combined email/calendar briefings.

**Critical limitation:** Phase 13 explicitly states that draft approval is for manual use and does not send the email. The documentation does not describe a JARVIS email-send endpoint. Do not assume that email sending, deletion, or full inbox access is implemented.

Email labels and urgency/reply suggestions are heuristic and can be wrong. Review the original message before acting.

### 3.7 Fitness Manager integration

Fitness Manager remains a separate service. JARVIS documents:

- Health/status checks.
- Workout retrieval.
- Read-only use of fitness data in daily planning and combined dashboards.
- A combined fitness/finance overview.

The Fitness Manager must be running at its configured URL. If it requires authentication, the corresponding token must be configured. One early phase explicitly warns that the exact Fitness Manager token/endpoint contract had not yet been verified against a live service.

The documentation does not claim that JARVIS edits workouts or fitness records.

### 3.8 Google Calendar integration

Google Calendar is optional and requires local OAuth setup.

Documented capabilities:
- Connection status.
- List events within a bounded timezone-aware date range.
- Create events with overlap detection.
- Preview conflicts.
- Sync confirmed schedule proposals.
- Explicit conflict override.
- One sync attempt per proposal to reduce duplicate event risk.

Security and behaviour:
- OAuth Desktop client setup is documented.
- OAuth credential and token files are stored locally at configured paths.
- The scopes described permit reading events and creating/editing events.
- Calendar writes are external side effects.
- Phase 36 requires a locally confirmed schedule, a read-only conflict preview, and a separate explicit sync confirmation.
- If conflict checking fails or Calendar is not configured, the documented sync workflow creates no events.
- Partial writes are reported and are not automatically retried.

### 3.9 Smart-home integration

Optional Home Assistant integration supports:
- Health/status check.
- Read states for exact allow-listed entities.
- `turn_on`, `turn_off`, and `toggle` for allow-listed `light`, `switch`, and `fan` entities.
- A proposal/confirmation workflow for device actions.

Restrictions:
- Exact entity IDs must be configured in `HOME_ASSISTANT_ALLOWED_ENTITIES`.
- No locks, alarms, garage doors, arbitrary service calls, scripts, or unrestricted device control.
- Device actions require an explicit confirmation request.
- Tokens and raw Home Assistant responses are not returned to the client.

### 3.10 Computer actions

Documented controlled computer actions are intentionally narrow:
- Open a complete HTTP(S) URL in the default browser.
- Launch configured allow-listed applications: Notepad, Calculator, or File Manager.
- Propose an action, inspect the exact target, then explicitly execute it.
- Record action history locally.

Not documented/supported by these phases:
- Arbitrary shell commands.
- Arbitrary scripts.
- Keystroke injection.
- Screen scraping.
- Unattended computer actions.
- General-purpose GUI automation.

Do not confuse this restricted action API with unrestricted computer control.

### 3.11 Finance

Phase 29 adds a local **manual finance ledger**:
- Record income and expenses.
- List transactions by month.
- Delete a ledger entry.
- Set monthly category budgets.
- Summarize income, expenses, net, category totals, and budget remaining.
- Combine finance summary with recent Fitness Manager workouts.

It is not a bank connection. It does not connect to bank accounts, initiate payments, trade investments, or provide automated financial advice. Data is manually entered and stored locally in `finance_ledger.db`.

### 3.12 Multimodal analysis

Phase 30 documents explicit authenticated analysis endpoints for:
- JPEG, PNG, and WebP images.
- PDF, UTF-8 text, and Markdown documents.
- Pasted text.

Limits documented:
- 8 MiB upload size.
- PDF extraction up to 30 pages.
- Extracted text capped at 60,000 characters.
- Scanned PDFs without a text layer may return no text; OCR is not included.
- Uploaded image bytes or extracted/pasted document text are sent to the configured AI provider when the user explicitly calls the endpoint.
- No automatic folder scanning, automatic instruction execution, or persistent upload storage is added by this phase.

### 3.13 User interfaces

| Interface | Route / launcher | Documented purpose |
|---|---|---|
| API docs | `/docs` | Explore/test API |
| Browser voice console | `/voice` | Text and optional speech input/output |
| Dashboard | `/dashboard` | Tasks, reminders, notifications, integrations, calendar, fitness, finance |
| Mobile web app | `/mobile` | Responsive mobile overview and quick commands |
| Computer console | `/computer-console` | Propose and confirm restricted desktop actions |
| Workspace | `/workspace` | Organized single-page view of sources, channels, memory, and overview |
| Desktop shell | `python -m app.desktop` | Optional PySide6 desktop window and tray notifications |

Voice details:
- Browser speech recognition depends on browser/device support and may use the browser vendor's speech service.
- The browser voice dashboard requires explicit user submission after dictation.
- Browser text-to-speech is opt-in per response.
- Optional Vosk wake phrase recognition is documented as local/offline after the user explicitly enables listening.
- Wake listening can use noticeable CPU and is not a dedicated low-power wake-word engine.
- The mobile service worker caches the app shell, not API responses or personal data.

---

## 4. API route index

This is a **document-derived index**, not a complete OpenAPI inventory. Route methods and request schemas should be checked against `/openapi.json` and the actual source.

| Area | Documented routes / route families |
|---|---|
| Core AI | `/ai/provider`, `/ai/understand`, `/ai/classify`, `/command`, `/tools` |
| Integrations | `/integrations/email/high-priority`, `/integrations/fitness/health`, `/integrations/home-assistant/health`, `/integrations/home-assistant/states`, `/integrations/home-assistant/action` |
| Memory | `/memory/status`, `/memory/facts`, `/memory/search`, `/memory/profile`, `/memory/conversations`, `/memory/overview`, `/memory/preferences`, `/memory/context-preview`, `/memory/export`, `/memory/all` |
| Knowledge | `/knowledge/documents`, `/knowledge/search`, `/knowledge/documents/{id}` |
| Assistant | `/assistant/capabilities`, `/assistant/command`, `/assistant/context/{session_id}` |
| Reminders | `/reminders` |
| Notifications | `/notifications`, `/notifications/{notification_id}/ack` |
| Monitoring | `/monitor/status`, `/briefing` |
| Tasks | `/tasks`, `/tasks/{id}/complete` |
| Planner | `/planner/plan`, `/planner`, `/planner/{plan_id}`, `/planner/{plan_id}/approve`, `/planner/{plan_id}/reject` |
| Calendar | `/calendar/status`, `/calendar/events` |
| Email assistant | `/email-assistant/high-priority`, `/email-assistant/drafts`, `/email-assistant/follow-up-suggestions` |
| Computer actions | `/computer/capabilities`, `/computer/actions/propose`, `/computer/actions/{id}/execute`, `/computer/actions` |
| Operations | `/operations/health`, `/operations/audit`, `/operations/backup` |
| Routines | `/routines` |
| Proactive intelligence | `/proactive/insights`, `/proactive/settings`, `/proactive/run`, `/proactive/briefing` |
| Planning | `/daily-planner/plan`, `/predictive-planning/recommendations`, `/predictive-planning/day-plan`, `/personalization/preferences`, `/personalization/plan`, `/personalization/feedback` |
| Finance | `/personal/finance/transactions`, `/personal/finance/budgets`, `/personal/finance/summary`, `/personal/fitness-finance-overview` |
| Multimodal | `/multimodal/analyze-image`, `/multimodal/analyze-document`, `/multimodal/analyze-text` |
| Security | `/security/policy`, `/security/threats`, `/security/audit` |
| Agent | `/agent/goals`, `/agent/runs`, `/agent/runs/{run_id}`, `/agent/runs/{run_id}/approve`, `/agent/runs/{run_id}/reject`, `/agent/runs/{run_id}/execute`, `/agent/runs/{run_id}/feedback`, `/agent/learning` |
| Personalized briefing | `/personalized-briefing/today` |
| Smart scheduling | `/smart-scheduling/proposals`, `/smart-scheduling/proposals/{id}`, `/smart-scheduling/proposals/{id}/confirm`, `/smart-scheduling/proposals/{id}/reject`, `/smart-scheduling/proposals/{id}/calendar-preview`, `/smart-scheduling/proposals/{id}/calendar-sync` |
| Dashboard | `/dashboard/overview` |

Most personal and operational API routes are documented as requiring the `X-JARVIS-API-Key` header. Verify route-by-route: do not assume every static UI route or health route uses identical authentication.

---

## 5. Data storage map

The documentation describes multiple SQLite databases under `JARVIS_DATA_DIR`, defaulting in many phases to `~/.jarvis`.

| Database/file name | Documented purpose |
|---|---|
| `memory.db` | Explicit personal facts and optional memory/conversation records |
| `conversation_context.db` | Bounded assistant conversation context |
| `knowledge.db` | Imported text/Markdown knowledge library |
| `tasks.db` | Tasks |
| `plans.db` | AI task-planning proposals |
| `reminders.db` / reminder store | Reminders (exact filename should be verified in source) |
| `notifications.db` | Notification feed |
| `proactive_intelligence.db` | Proactive preferences/insights |
| `adaptation.db` | Personalization preferences and feedback |
| `email_drafts.db` | Email draft review records |
| `computer_actions.db` | Computer action proposals/history |
| `agent_runs.db` | Goal-based agent runs |
| `agent_learning.db` | Agent feedback |
| `finance_ledger.db` | Manual finance ledger |
| `schedule_proposals.db` | Smart scheduling proposals |
| Audit store | Operational audit records (exact filename should be verified) |

The application also uses local OAuth credential/token files for Google Calendar and a local Vosk model directory if offline wake listening is enabled.

**Do not assume the table is exhaustive or that every phase uses a separate database.** Confirm the actual database initialization and filenames in the source.

---

## 6. Configuration and environment variables

The Markdown files explicitly mention the following settings. The actual `.env.example` and settings code are authoritative for the current application.

### Core / AI
- `JARVIS_API_KEY`
- `JARVIS_DATA_DIR`
- `AI_PROVIDER` (`gemini` or `ollama` in the documentation)
- `GEMINI_API_KEY`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `MEMORY_CONTEXT_TO_CLOUD`
- `JARVIS_ENABLED_TOOLS`

### Service integrations
- `EMAIL_MANAGER_BASE_URL`
- `EMAIL_MANAGER_API_KEY`
- `FITNESS_MANAGER_BASE_URL`
- `FITNESS_MANAGER_API_TOKEN`
- `HOME_ASSISTANT_BASE_URL`
- `HOME_ASSISTANT_TOKEN`
- `HOME_ASSISTANT_ALLOWED_ENTITIES`

### Calendar
- `GOOGLE_CALENDAR_CREDENTIALS`
- `GOOGLE_CALENDAR_TOKEN`

### Scheduler / notifications / conversation
- `MONITOR_INTERVAL_SECONDS`
- `NOTIFY_TASK_DUE_SOON_MINUTES`
- `CONVERSATION_CONTEXT_ENABLED`
- `CONVERSATION_CONTEXT_TURNS`
- `MEMORY_STORE_CONVERSATIONS`

### Voice / desktop
- `JARVIS_VOSK_MODEL_PATH`
- `JARVIS_WAKE_PHRASE`
- `JARVIS_DESKTOP_HOST`
- `JARVIS_DESKTOP_PORT`

### Proactive / analytics note
- `ANALYTICS_ENABLED` is described in Phase 1 as reserved and not connected to an external analytics client in that phase. Do not interpret the setting name as proof that analytics is active or disabled in later code without inspecting the implementation.

Never put real secrets in documentation, source control, screenshots, issue reports, or ZIP files shared for review.

---

## 7. Setup and local operation

### 7.1 Documented basic backend startup

From the JARVIS repository root, using the appropriate virtual environment:

```powershell
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/dashboard`
- `http://127.0.0.1:8000/voice`
- `http://127.0.0.1:8000/mobile`
- `http://127.0.0.1:8000/workspace`

Run tests from the repository root:

```powershell
python -m pytest -q
```

### 7.2 Optional dependencies

The documentation identifies separate optional dependency files:
- `requirements-calendar.txt` for Google Calendar.
- `requirements-desktop.txt` for the desktop shell.
- `requirements-voice.txt` for Vosk/sounddevice offline wake listening.

Do not install optional integrations unless they are needed.

### 7.3 Background scheduler constraint

Several features use in-process background schedulers. The documentation recommends **one Uvicorn worker** to avoid duplicated scheduler loops. Keep the backend running for reminders, routines, monitoring, and proactive notification cycles to operate.

### 7.4 Python compatibility

The uploaded Markdown documentation does not establish a definitive Python version support matrix. Check `pyproject.toml`, `requirements*.txt`, CI configuration, and the upstream dependency support before selecting a Python version or migrating environments.

---

## 8. Security and privacy assessment

### 8.1 Positive documented controls

- API-key protection for many personal-data and operational endpoints.
- Explicit tool allow-lists.
- Server-side validation of AI output.
- Separate proposal and execution steps for several sensitive workflows.
- Read-only natural-language command dispatcher for documented commands.
- Local SQLite storage for many personal features.
- Optional conversation storage and explicit memory controls.
- Cloud memory context disabled by default in documented settings.
- Calendar conflict preview and explicit sync confirmation.
- Home Assistant entity allow-list and per-action confirmation.
- Restricted computer action allow-list.
- Metadata-only audit records that omit request bodies, query strings, authorization headers, and API keys.
- Security response headers and `Cache-Control: no-store` for sensitive route groups.
- Backup endpoint with manual restore instructions.
- No automatic sending of email in the documented email-assistant phase.
- No arbitrary shell execution in the documented computer-action/agent phases.

### 8.2 Important limitations and risks

1. **No end-to-end encryption guarantee is documented.** The files do not establish end-to-end encryption across JARVIS, its databases, connected services, browser UI, and AI providers.
2. **SQLite data is not automatically encrypted.** Phase 2 explicitly says memory storage is local but not encrypted by that feature.
3. **API key is not full identity management.** The docs describe it as a shared-secret control, not multi-user identity or a complete session/authentication system.
4. **Local inference does not make all integrations local.** External connectors still contact their providers.
5. **Cloud AI receives prompts sent to it.** Uploaded content in multimodal analysis is sent to the configured AI provider when the endpoint is explicitly called.
6. **Browser speech recognition may use a vendor service.** It is not guaranteed to be offline. Vosk is a separate optional local mode.
7. **Audit/threat detection is limited.** Threat alerts are heuristic and advisory; they do not automatically block traffic. Audit records intentionally omit IPs and request content.
8. **No complete rate-limiting or intrusion-prevention guarantee is documented.**
9. **Confirmation configuration may not be sufficient by itself.** A previous repository review raised the concern that a tool-confirmation setting might be accepted but not enforced in one runtime path. This needs direct source-level verification; enforce approvals in a trusted server-side gateway.
10. **Prompt injection remains a risk.** Emails, PDFs, web content, and imported documents must be treated as untrusted data, not trusted instructions.
11. **Backups contain personal data.** Encrypt and access-control backup archives.
12. **Remote access requires more than an API key.** Use a private VPN or HTTPS reverse proxy with authentication, firewall restrictions, and rate limits. Do not port-forward the raw development server.

### 8.3 Recommended security baseline

- Bind development JARVIS to `127.0.0.1`.
- Use a unique, high-entropy `JARVIS_API_KEY`.
- Keep `.env`, OAuth files, database files, backups, and tokens out of Git.
- Restrict OS permissions on `JARVIS_DATA_DIR`.
- Encrypt the device and backups using OS/disk or backup encryption.
- Use a secrets manager or OS-protected credential storage for tokens where practical.
- Default to deny for agent tools; enable only specific read-only capabilities first.
- Put approval checks in server-side code outside the LLM.
- Separate read and write tools.
- Require explicit user confirmation for email sends, calendar writes, smart-home actions, file deletion, purchases, and other consequential side effects.
- Log action metadata without logging secrets or unnecessary personal content.
- Test prompt injection and authorization bypasses.
- Review and revoke OAuth scopes that are not needed.
- Do not connect banking credentials or highly sensitive accounts until a separate security review is complete.

---

## 9. Known functional boundaries

These are particularly important because the feature names may sound broader than the documented implementation.

| Feature name | What documentation actually supports | What should not be assumed |
|---|---|---|
| AI agent | Bounded planning and allow-listed inspections | Unrestricted autonomous agent |
| Email automation | High-priority retrieval, classification, drafting, manual approval | Automatic email sending/deletion |
| Predictive planning | Rule-based ranking and heuristic durations | Trained predictive model |
| Personal finance | Manual local ledger and budgets | Bank integration or transactions |
| Computer control | Allow-listed URL/app launch with proposal/confirmation | Full desktop automation |
| Knowledge retrieval | Local keyword-ranked chunks | Semantic/vector search |
| Voice | Browser speech plus optional Vosk wake phrase | Guaranteed offline browser speech |
| Calendar sync | Confirmed schedule, conflict preview, explicit sync | Automatic background scheduling |
| Proactive notifications | Local in-app notifications | SMS, push, or email delivery |
| Security monitoring | Metadata-based heuristic alerts | Full intrusion detection/prevention |
| Memory | Explicit facts, bounded context, optional conversation storage | Encrypted-by-default or automatic learning |
| Dashboard integration catalog | Active/optional/planned labels | Every listed provider is connected |

---

## 10. OpenJarvis migration implications

The documentation suggests a modular migration rather than replacing every part of JARVIS.

### 10.1 Recommended responsibility split

| Responsibility | Recommended owner after migration |
|---|---|
| User-facing JARVIS API and authentication | Keep a JARVIS FastAPI gateway |
| Permissions and approval enforcement | Keep in JARVIS gateway / trusted policy layer |
| AI model execution and agent runtime | Evaluate OpenJarvis |
| Existing email business logic and data | Keep Email Manager |
| Existing fitness business logic and data | Keep Fitness Manager |
| Personal task/reminder/routine data | Initially preserve existing JARVIS stores |
| Calendar OAuth and sync workflow | Preserve and audit existing integration |
| Finance ledger | Preserve existing local ledger |
| UI / mobile / voice | Preserve initially; migrate separately if needed |
| Audit, backups, security policy | Keep under JARVIS control and verify coverage |

### 10.2 Do not assume OpenJarvis replaces these automatically

OpenJarvis should not be assumed to replace:
- Existing FastAPI route contracts.
- Email Manager or Fitness Manager.
- Google Calendar OAuth implementation.
- Task/reminder/routine business logic.
- Finance ledger.
- Existing dashboard/mobile UI.
- User authentication and approval enforcement.
- Existing SQLite data or migration scripts.

Each item needs a compatibility mapping against the actual OpenJarvis source and APIs.

### 10.3 Suggested staged migration

1. **Inventory and backup:** Inspect the current source, dependencies, tests, environment settings, database schemas, and API contracts. Back up databases and configuration securely.
2. **Run OpenJarvis separately:** Use an isolated Python environment and separate port. Do not connect personal accounts.
3. **Benchmark AI:** Compare existing Gemini/Ollama behaviour with OpenJarvis on representative JARVIS commands and planning tasks.
4. **Create a narrow adapter:** Let the existing JARVIS gateway call OpenJarvis for reasoning while retaining authentication and policy enforcement.
5. **Reconnect read-only tools:** Add narrowly scoped Email Manager and Fitness Manager tools; verify authentication and data boundaries.
6. **Preserve data ownership:** Keep existing databases and service APIs. Avoid moving data into a new memory store until export, migration, retention, and deletion behaviour are understood.
7. **Add approvals:** Implement server-side approval tokens/state transitions for all external side effects.
8. **Security test:** Test prompt injection, tool escalation, token exposure, local network exposure, data leakage, and audit coverage.
9. **Canary rollout:** Run a small set of non-sensitive commands through the new runtime and compare outputs.
10. **Cut over only after verification:** Keep the old backend available for rollback until the new path passes functional and security tests.

### 10.4 Migration acceptance checklist

- [ ] OpenJarvis installs in an isolated environment.
- [ ] Existing JARVIS services still start independently.
- [ ] JARVIS API authentication remains enforced.
- [ ] OpenJarvis cannot bypass JARVIS tool permissions.
- [ ] Read-only Email Manager calls work with least-privilege credentials.
- [ ] Read-only Fitness Manager calls work with least-privilege credentials.
- [ ] No secrets appear in logs, prompts, traces, or responses.
- [ ] Cloud/local model routing is explicit and observable.
- [ ] Memory sharing with cloud models is opt-in.
- [ ] Write actions require server-side approval.
- [ ] Calendar conflict and duplicate-sync safeguards remain effective.
- [ ] Existing SQLite data can be backed up and restored.
- [ ] Tests pass and API contracts are documented.
- [ ] Rollback to the previous backend is tested.

---

## 11. Questions that require source-code inspection

The Markdown documentation is not enough to answer these conclusively:

1. Which routes are actually mounted in the current `app.main`?
2. Are all sensitive routes protected by the API-key dependency?
3. Are confirmation states validated server-side and bound to the exact action payload?
4. Can any AI tool path bypass the allow-list?
5. Which database files and schemas are actually created?
6. Are SQLite files, OAuth tokens, and backups encrypted at rest?
7. Are there any outbound telemetry, analytics, crash-reporting, or external logging calls?
8. Which dependencies and Python versions are actually supported?
9. Are all documented phases present in the uploaded code, or are some docs ahead of the implementation?
10. What tests exist, and do they cover authorization, prompt injection, approval replay, and integration failures?
11. What are the exact API contracts and authentication requirements of Email Manager and Fitness Manager?
12. How does OpenJarvis's tool execution and memory system compare with the existing JARVIS implementation?

These must be checked in the Python source, dependency files, tests, configuration, and—where appropriate—runtime network behaviour.

---

## 12. Source document index

The consolidated reference was built from all 42 Markdown files:

- `PHASE1.md` — AI core and safety.
- `PHASE2.md` — Local memory and personalization.
- `PHASE3.md` — Memory-aware, permission-controlled tools.
- `PHASE4.md` — Voice console, reminders, notifications.
- `PHASE5.md` — Monitoring, briefing, dashboard.
- `PHASE6.md` — Desktop shell and OS notifications.
- `PHASE7.md` — Optional offline wake phrase.
- `PHASE8.md` — Personal task management.
- `PHASE9.md` — AI task planner.
- `PHASE10.md` — Google Calendar integration.
- `PHASE11.md` — Intelligent daily planner.
- `PHASE12.md` — Proactive notifications.
- `PHASE13.md` — Advanced email assistance.
- `PHASE14.md` — Permission-controlled computer actions.
- `PHASE15.md` — Advanced personal memory.
- `PHASE16.md` — Security and reliability.
- `PHASE17.md` — Mobile interface and remote access.
- `PHASE18.md` — Smart-home integration.
- `PHASE19.md` — Daily routines.
- `PHASE20.md` — Unified voice assistant.
- `PHASE21.md` — Context-aware conversations.
- `PHASE22.md` — Proactive intelligence.
- `PHASE23.md` — Predictive planning.
- `PHASE24.md` — Adaptive personalization.
- `PHASE25.md` — Long-term memory and knowledge retrieval.
- `PHASE26.md` — Advanced voice.
- `PHASE27.md` — Controlled computer use.
- `PHASE28.md` — Email and calendar intelligence.
- `PHASE29.md` — Fitness and finance integration.
- `PHASE30.md` — Multimodal AI.
- `PHASE31.md` — Advanced security and threat detection.
- `PHASE32.md` — Goal-based agent.
- `PHASE33.md` — Agent memory and learning feedback.
- `PHASE34.md` — Personalized daily briefings.
- `PHASE35.md` — Proactive scheduling.
- `PHASE36.md` — Calendar sync with conflict detection.
- `PHASE37.md` — Unified personal assistant dashboard.
- `PHASE38.md` — Voice-controlled dashboard and commands.
- `PHASE39.md` — Proactive agent and daily briefings.
- `PHASE40.md` — Persistent personal memory controls.
- `PHASE41.md` — Organized single-page workspace.
- `README_PHASES.md` — Cumulative phase history.

---

## 13. Bottom line

The documentation describes a substantial modular personal-assistant application with useful local workflows and conservative action boundaries. Its strongest documented design choices are the separation of Email/Fitness services, explicit memory controls, local SQLite stores, read-only command routing, and proposal/approval flows for selected side effects.

Its most important gaps to verify are encryption at rest, end-to-end encryption (not established), complete authorization coverage, server-side enforcement of every approval path, prompt-injection resistance, external data flows, and the difference between documented features and actual code.

**Use this file as the project orientation document. Use the source code, tests, OpenAPI schema, and runtime checks as the evidence for implementation and security decisions.**


---


<a id="phase-1--agent-foundation"></a>


# Phase 1 — Agent Foundation


# JARVIS Phase 1 — Agent Foundation

This phase adds the safe, framework-independent foundations for an OpenJarvis-inspired agent runtime without replacing existing JARVIS services.

## Added modules

- `app/agent/contracts.py`: immutable `ToolSpec` contract, permission levels, handler slot, input schema, enablement and timeout metadata.
- `app/agent/registry.py`: duplicate-safe tool registry, discovery/description and validation for the JSON Schema subset used by JARVIS tools.
- `app/agent/policies.py`: centralized policy decisions for read, write, destructive and system operations.
- `tests/test_agent_foundation.py`: registry, schema validation and policy tests.

## Compatibility

`app/services/tool_registry.py` now exposes `AGENT_TOOL_REGISTRY` and builds its initial metadata from the two existing allow-listed tools:

- `email.high_priority.read`
- `fitness.workouts.read`

The existing `enabled_tools()` interface remains available to the current command executor. Existing command routing and service clients are not replaced in this phase.

Handlers are intentionally `None` in Phase 1. The registry is metadata-only until Phase 2 attaches trusted service adapters. This prevents AI-generated plans from invoking unreviewed code.

## Run tests

From the repository root:

```bash
python -m pytest tests/test_agent_foundation.py -q
python -m compileall -q app
```

## Next phase

Phase 2 will attach real, trusted handlers to the email and fitness tool specs, align authentication, and route execution through a policy-checked executor. Do not enable write or destructive tools until approval handling is implemented end-to-end.


---


<a id="phase-2--integration-engine"></a>


# Phase 2 — Integration Engine


# JARVIS Phase 2 — Integration Engine

Phase 2 connects the Phase 1 tool registry to the existing Email Manager and Fitness Manager services. The first two tools are deliberately read-only.

## What changed

- Added `app/agent/executor.py` for schema validation, permission checks, async execution, timeouts, and safe error responses.
- Added trusted handlers in `app/tools/integration_tools.py`.
- Connected `email.high_priority.read` to `GET /emails/high-priority` using the server-side `X-API-Key` contract.
- Connected `fitness.workouts.read` to `POST /auth/login` followed by `GET /workouts` using a cached bearer token. A 401 triggers one re-login attempt.
- Kept the existing `GET /tools` discovery endpoint and added `POST /tools/{tool_name}/execute`.
- Kept the old `FITNESS_MANAGER_API_TOKEN` setting as a backwards-compatible fallback for the existing `/command` path.
- Added tests for tool execution, invalid arguments, permissions, timeouts, error sanitization, and the authenticated API route.

## Configure the three services

### JARVIS `.env`

```dotenv
EMAIL_MANAGER_BASE_URL=http://127.0.0.1:8001
EMAIL_MANAGER_API_KEY=use-the-same-random-secret-as-email-manager

FITNESS_MANAGER_BASE_URL=http://127.0.0.1:8002
FITNESS_MANAGER_EMAIL=the-email-used-to-register-in-fitness-manager
FITNESS_MANAGER_PASSWORD=the-fitness-manager-account-password

JARVIS_API_KEY=replace-with-a-long-random-secret
JARVIS_ENABLED_TOOLS=email.high_priority.read,fitness.workouts.read
AGENT_TOOL_TIMEOUT_SECONDS=20
AGENT_ALLOW_WRITES=false
```

Do not commit real `.env` files or share these secrets with the browser.

### Email Manager `backend/.env`

Set `API_KEY` to exactly the same secret as JARVIS `EMAIL_MANAGER_API_KEY`. Its `GET /healthz` endpoint does not require authentication; email data endpoints accept the server-to-server `X-API-Key` header.

### Fitness Manager `backend/.env`

Use the Fitness Manager's existing database and `JWT_SECRET` configuration. The email/password configured in JARVIS must belong to an account already registered in that Fitness Manager database.

## Start order (Windows PowerShell)

Start each backend in its own terminal, using its own project folder and virtual environment:

```powershell
# Email Manager: backend folder
uvicorn main:app --reload --host 127.0.0.1 --port 8001

# Fitness Manager: backend folder
uvicorn app.main:app --reload --host 127.0.0.1 --port 8002

# JARVIS: project root
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Verify

Use the JARVIS API key in the `X-JARVIS-API-Key` header.

```powershell
# Discover enabled tools
Invoke-RestMethod http://127.0.0.1:8000/tools -Headers @{'X-JARVIS-API-Key'='YOUR_JARVIS_KEY'}

# Execute the email read tool
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/tools/email.high_priority.read/execute `
  -Headers @{'X-JARVIS-API-Key'='YOUR_JARVIS_KEY'} `
  -ContentType 'application/json' -Body '{"arguments":{}}'

# Execute the fitness read tool
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/tools/fitness.workouts.read/execute `
  -Headers @{'X-JARVIS-API-Key'='YOUR_JARVIS_KEY'} `
  -ContentType 'application/json' -Body '{"arguments":{}}'
```

## Safety boundaries

- The only connected tools in this phase are read-only.
- Tool names are selected from the server-side allow-list; clients cannot submit Python code or arbitrary URLs.
- Tool arguments are validated against each registered JSON schema.
- JARVIS authenticates to each downstream service from the backend only.
- Write, destructive, and system permissions remain disabled pending a separate approval workflow.
- Upstream exception bodies and credentials are not returned to API clients.

## Tests

```powershell
python -m compileall -q app
python -m pytest tests/test_agent_foundation.py tests/test_phase2_tool_execution.py tests/test_phase3.py -q
```


---


<a id="phase-3--ai-agent-orchestrator"></a>


# Phase 3 — AI Agent Orchestrator


# Phase 3 — AI Agent Orchestrator

Phase 3 adds an AI-driven orchestration endpoint to the existing JARVIS FastAPI application.

## What it does

1. Sends the user request and the currently enabled tool catalog to the configured AI provider (`gemini` or `ollama`).
2. Requires a structured JSON plan containing only registered tool names.
3. Rejects malformed plans, unknown tools, disabled tools, non-read-only tools, and invalid arguments.
4. Executes up to five registered read-only tools concurrently through the Phase 2 `ToolExecutor`.
5. Continues when an individual tool fails and reports partial success accurately.
6. Uses the AI provider to synthesize a response from actual tool results.
7. Writes a local execution trace containing tool names and statuses, but not raw email or fitness payloads.

The AI provider proposes tool calls; it does not execute code. The backend remains the authority for tool registration, argument validation, and permissions.

## Endpoint

`POST /assistant/agent/chat`

Requires the `X-JARVIS-API-Key` header.

Request:

```json
{
  "command": "Review my important emails and recent workouts",
  "session_id": "optional-session-123",
  "max_tool_calls": 4
}
```

`session_id` is optional and must contain 8–80 letters, digits, underscores, or hyphens. `max_tool_calls` is between 1 and 5.

Response fields include `status`, `answer`, `goal_summary`, `tool_calls`, `tool_results`, `trace_id`, and `memory_context_used`.

## Trace endpoint

`GET /assistant/agent/traces?limit=20`

Requires the same API key. Trace records intentionally omit raw tool results and message contents.

## Configuration

Existing Phase 2 configuration is reused:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.5-flash
AI_TIMEOUT_SECONDS=30
JARVIS_API_KEY=your_long_random_secret
JARVIS_ENABLED_TOOLS=email.high_priority.read,fitness.workouts.read
AGENT_ALLOW_WRITES=false
MEMORY_CONTEXT_TO_CLOUD=false
```

Memory context is excluded from AI provider prompts by default. Set `MEMORY_CONTEXT_TO_CLOUD=true` only if you explicitly want relevant saved memory facts included in cloud AI requests.

## Run

From the JARVIS project root:

```bash
uvicorn app.main:app --reload --port 8000
```

Then open `http://127.0.0.1:8000/docs`, find **Unified Assistant**, and call `POST /assistant/agent/chat`.

## Tests

```bash
python -m pytest tests/test_phase3_orchestrator.py tests/test_phase2_tool_execution.py -q
```

The Phase 3 tests cover multi-tool execution, unknown-tool rejection, partial failures, metadata-only trace storage, and API-key protection.

## Safety boundaries

- Only tools registered in `AGENT_TOOL_REGISTRY` are selectable.
- The orchestrator currently permits read-only tools only.
- Writes, destructive operations, device control, and message sending are not enabled by this endpoint.
- AI output is treated as untrusted data and validated before execution.
- Tool results are sent to the configured AI provider for synthesis. Do not connect sensitive data sources unless your provider/data handling settings are acceptable.
- Local traces store request text and tool metadata, not full email/workout payloads.


---


<a id="phase-4--shared-memory--context"></a>


# Phase 4 — Shared Memory & Context


# Phase 4 — Shared Memory & Context

## What this phase adds

- Reuses the existing SQLite `MemoryStore` and `ConversationContextStore`; no duplicate memory database is introduced.
- Agent sessions now receive a stable session ID and retrieve a bounded recent-turn context.
- Saved facts and recent session context are included in Gemini prompts only when `cloud_context_enabled` is explicitly enabled. With Ollama, context may be used locally when `context_enabled` is enabled.
- Bounded session context stores only the user command, intent, status, and a short assistant summary. Tool result payloads (including email and fitness data) are not stored in session context or traces.
- Full conversation history is saved only when `conversation_storage_enabled` is explicitly enabled.
- Existing authenticated memory APIs remain the controls for facts, preferences, export, and clearing memory.

## Configure

Memory defaults are privacy-conservative for cloud AI:

```env
CONVERSATION_CONTEXT_ENABLED=true
CONVERSATION_CONTEXT_TURNS=8
MEMORY_STORE_CONVERSATIONS=false
MEMORY_CONTEXT_TO_CLOUD=false
```

The persisted settings at `PUT /memory/preferences` take precedence for `context_enabled`, `cloud_context_enabled`, and `conversation_storage_enabled`. Enable cloud context only if you want saved facts and recent conversation summaries sent to Gemini.

## Agent API

`POST /assistant/agent/chat` accepts:

```json
{
  "command": "What did we decide about my workout schedule?",
  "session_id": "my-session-0001",
  "max_tool_calls": 4
}
```

The response includes `session_id`, `memory_context_used`, `session_context_used`, and `conversation_saved`. Reuse the returned `session_id` for follow-up requests.

## Memory controls

- `GET /memory/overview` — counts and privacy settings, not memory contents.
- `GET /memory/facts` and `GET /memory/search` — inspect saved facts.
- `POST /memory/facts` — explicitly save a fact. No automatic extraction or saving of personal facts is performed.
- `PUT /memory/preferences` — enable/disable context and conversation storage.
- `GET /memory/export` — export user-managed memory.
- `DELETE /memory/all` with confirmation `CLEAR ALL MEMORY` — clear saved facts and conversation context.

## Security notes

- Passwords, API keys, access tokens, and raw tool payloads must not be saved as memory.
- Memory and session endpoints remain protected by the JARVIS API key.
- Treat retrieved memory as untrusted data, never as executable instructions.


---


<a id="phase-5--autonomous-background-agents"></a>


# Phase 5 — Autonomous Background Agents


# Phase 5 — Autonomous Background Agents

## Scope

This phase adds configurable, permission-safe background agents to the existing JARVIS FastAPI application.

### Included agents

- **Task monitor:** checks pending task due dates and creates deduplicated in-app alerts.
- **Routine monitor:** queues notifications for routines that become due.
- **Daily briefing:** generates the existing local task briefing once per configured local date, after the configured time.
- **Email priority monitor (opt-in):** polls the Email Manager's high-priority endpoint, stores only the previous count, and creates an in-app notification when that count increases.
- **Service health monitor:** retains the existing Email Manager and Fitness Manager health polling.

## Safety boundaries

- Email monitoring is disabled by default.
- Email message bodies, subjects, senders and identifiers are not stored by the new monitor.
- Background agents do not send, reply to, archive or delete email.
- Background agents do not modify fitness records or task records.
- Notifications are in-app only.
- Existing quiet hours and timezone preferences are respected by email monitoring and daily briefings.
- API controls require `X-JARVIS-API-Key`.

## Configuration

The new settings are persisted in `~/.jarvis/background_agents.db`:

| Setting | Default | Meaning |
|---|---:|---|
| `enabled` | `true` | Master background-agent switch |
| `task_monitor_enabled` | `true` | Task deadline and routine notifications |
| `email_monitor_enabled` | `false` | Opt-in high-priority email count polling |
| `email_monitor_interval_seconds` | `300` | Email polling interval (60–86400) |
| `daily_briefing_time` | `08:00` | Local daily briefing time |

Timezone and quiet-hour preferences continue to come from `/proactive/settings`.

## API

- `GET /background-agents/status` — preferences, checkpoints and safety metadata.
- `PUT /background-agents/settings` — update agent settings.
- `POST /background-agents/run` — manually run a local cycle and an email check.

All endpoints require the JARVIS API key.

Example settings:

```json
{
  "enabled": true,
  "task_monitor_enabled": true,
  "email_monitor_enabled": false,
  "email_monitor_interval_seconds": 300,
  "daily_briefing_time": "08:00"
}
```

## Scheduler behavior

The application lifecycle scheduler checks reminders every five seconds, runs local background agents at most once per minute, and polls email only when explicitly enabled and the configured interval has elapsed. Daily briefing execution is deduplicated with a persistent date checkpoint.

## Verification

Run:

```bash
python -m compileall -q app
python -m pytest tests/test_phase5_background_agents.py -q
python -m pytest -q
```

The two known full-suite failures in the supplied baseline concern missing `PHASE6.md` and `PHASE7.md` documentation files; they are unrelated to Phase 5.


---


<a id="phase-6--unified-jarvis-interface"></a>


# Phase 6 — Unified JARVIS Interface


# Phase 6 — Unified JARVIS Interface

## What changed

The project now includes a single responsive browser application at:

- `GET /app` — unified JARVIS workspace.

The interface brings the existing backend capabilities into one navigation shell:

- Overview: authenticated dashboard aggregation for tasks, email priorities, fitness, calendar and notifications.
- AI Assistant: `/assistant/agent/chat`, with a per-page session ID.
- Tasks: list, create and complete local tasks.
- Email: read-only high-priority email summary from Email Manager.
- Fitness: read-only workout summary from Fitness Manager.
- Notifications: list and acknowledge in-app alerts.
- Memory: list, create and delete explicit facts; update memory preferences.
- Background agents: inspect, configure and manually run safe monitoring cycles.
- Settings: service health and API documentation links.

The previous `/workspace`, `/dashboard`, `/voice`, `/mobile` and `/computer-console` routes remain available for compatibility.

## Security and privacy

- The JARVIS API key is held only in JavaScript memory; it is not written to localStorage, sessionStorage or cookies.
- Reloading or leaving the page clears the key.
- All authenticated API calls send `X-JARVIS-API-Key`.
- The browser communicates with the JARVIS origin only; it does not receive Email Manager or Fitness Manager credentials.
- Email and fitness sections are read-only summaries.
- Memory is explicitly user-managed; the UI does not silently save personal facts.
- Cloud memory context remains a separate explicit opt-in.
- Background agent actions are limited to the existing backend's permission-controlled checks and in-app notifications.

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000/app`, enter the configured `JARVIS_API_KEY`, then select Connect.

## Notes

- The dashboard aggregates connected services independently; unavailable services appear as unavailable instead of hiding local JARVIS data.
- Browser speech recognition is optional and depends on browser support and microphone permission.
- The root `/` response remains the existing JSON health/info response for API compatibility.
- The UI is vanilla HTML/CSS/JavaScript and adds no frontend build or package dependency.

## Verification

```bash
python -m compileall -q app
python -m pytest tests/test_phase6_unified_ui.py -q
python -m pytest -q
```


---


<a id="phase-7--voice-intelligence"></a>


# Phase 7 — Voice Intelligence


# Phase 7 — Voice Intelligence

## Unified browser interface

Open `/app` and select **AI Assistant**. Phase 7 adds one-shot dictation, an optional browser wake-phrase listener (Hey JARVIS), selectable recognition language, read-aloud replies, and explicit stop controls. Voice is off until the user enables it. Recognition fills the composer; **review the text and press Send** to submit. Wake listening is not automatically restarted after interruption. Browser speech recognition may use cloud processing and is not guaranteed offline.

## Optional offline desktop listener

Microphone opens only after the user explicitly enables offline wake listening in desktop settings. The existing optional Vosk desktop listener recognizes the wake phrase locally. Install `requirements-voice.txt`, download a compatible local Vosk model, and configure its path. Use the desktop **Stop wake listening** control to stop. The listener does not start automatically.

## Privacy and limitations

Voice requires browser support and microphone permission. Browser wake-phrase detection is best-effort, not guaranteed always-on. Speech recognition is not equivalent to an offline local model. Browser-recognized commands are not automatically submitted to JARVIS. The agent still uses existing server-side permissions. The browser does not persist API keys.

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000/app`. Connect with the configured API key, then choose AI Assistant.

Microphone opens only after the user explicitly enables offline wake listening in desktop settings. The desktop listener is opt-in and can be stopped with **Stop wake listening**.


---
