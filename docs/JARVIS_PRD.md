# JARVIS — Product Requirements Document

**Version:** 1.0  
**Status:** Approved product direction / Proposed implementation requirements  
**Product owner:** Tejas  
**Product type:** Single-user personal AI assistant  
**Budget:** ₹0 — free-tier APIs and open-source technologies  
**Backend:** Python + FastAPI  
**AI provider:** Google Gemini  
**Primary interface:** Web application with voice and text interaction

---

# 1. Problem Statement

## 1.1 The problem

Managing personal digital activities requires switching between multiple applications.

Emails, fitness tracking, daily planning, tasks, routines, calendars, reminders, and personal information exist in separate systems.

These systems generally do not understand one another or coordinate activities intelligently.

The user must manually:
- Check emails and identify important messages.
- Decide what tasks need attention.
- Plan daily activities.
- Maintain fitness routines.
- Manage calendar commitments.
- Remember important personal information.
- Monitor events and follow up on pending activities.
- Switch between multiple applications to complete tasks.

Existing AI assistants can answer questions, but often lack persistent personal context, integrated application access, and reliable autonomous execution.

## 1.2 The solution

JARVIS will provide one centralized personal AI assistant that connects existing applications and manages personal workflows.

It will:

1. Understand natural-language and voice commands.
2. Maintain useful long-term personal memory.
3. Retrieve information from connected applications.
4. Reason about priorities and user context.
5. Create plans and coordinate activities.
6. Execute approved actions through application integrations.
7. Monitor important events and conditions.
8. Proactively notify the user when attention is required.
9. Provide a unified interface for all supported capabilities.

## 1.3 Core value proposition

**One assistant. One interface. One connected personal ecosystem.**

JARVIS reduces manual coordination and helps the user make better decisions while maintaining control over sensitive actions.

---

# 2. Target Users — Two Personas

JARVIS is a single-user product. These personas represent two usage contexts of the same owner, not separate customer segments.

## Persona 1: Personal Digital Life Manager

**Profile:** The owner managing personal activities through multiple applications.

**Needs:**
- Centralized personal information.
- Email prioritization.
- Fitness progress tracking.
- Daily planning and task management.
- Routine management.
- Calendar coordination.
- Persistent memory.

**Pain points:**
- Too many disconnected applications.
- Manual task prioritization.
- Forgetting important commitments.
- Repeatedly entering the same information.
- Difficulty understanding what needs attention.

**Expected outcome:** JARVIS manages and coordinates everyday personal activities from one place.

## Persona 2: On-the-Go Voice Assistant User

**Profile:** The same owner interacting with JARVIS while studying, working, travelling, exercising, or away from the computer.

**Needs:**
- Voice commands.
- Fast responses.
- Context-aware answers.
- Hands-free interaction.
- Proactive notifications.
- Ability to execute approved tasks.

**Pain points:**
- Typing commands is inconvenient.
- Information is spread across devices.
- Important events can be missed.
- Manual application navigation interrupts activities.

**Expected outcome:** JARVIS becomes an accessible voice-first assistant that understands context and acts when authorized.

---

# 3. Goals and Non-Goals

## 3.1 Product goals

| ID | Goal | Priority |
|---|---|---|
| G01 | Natural-language AI interaction | Critical |
| G02 | Voice-based interaction | Critical |
| G03 | Persistent personal memory | Critical |
| G04 | Email Manager integration | Critical |
| G05 | Fitness Manager integration | Critical |
| G06 | Day Planner | Critical |
| G07 | Task Manager | Critical |
| G08 | Routine Manager | Critical |
| G09 | Google Calendar integration | High |
| G10 | Proactive monitoring and notifications | High |
| G11 | Permission-based autonomous execution | Critical |
| G12 | Unified dashboard and interface | Critical |
| G13 | Personal Finance Manager | Medium |
| G14 | Extensible modular architecture | Critical |

## 3.2 Non-goals

The following are outside the initial product scope:

- Multi-user accounts and public SaaS functionality.
- Enterprise administration.
- Paid AI APIs or subscriptions.
- Replacing Email Manager and Fitness Manager.
- Building a complete banking application.
- Executing financial transactions.
- Unrestricted computer control.
- Autonomous execution of sensitive actions without authorization.
- Training a custom foundation model.
- Guaranteeing 24/7 operation using free-tier cloud services.

JARVIS should prioritize reliability and useful integrations over unnecessary features.

---

# 4. User Stories

## 4.1 AI interaction

- As a user, I want to communicate with JARVIS using natural language so that I do not need to remember commands.
- As a user, I want voice interaction so that I can use JARVIS hands-free.
- As a user, I want contextual conversations so that I do not need to repeat previously provided information.
- As a user, I want JARVIS to ask clarifying questions when my instructions are ambiguous so that it does not perform incorrect actions.

## 4.2 Memory

- As a user, I want JARVIS to remember useful personal information so that future interactions are more contextual.
- As a user, I want to review and correct stored memories so that I remain in control.
- As a user, I want JARVIS to retrieve relevant historical information so that I do not need to repeat previous conversations.

## 4.3 Email Manager

- As a user, I want JARVIS to check my emails so that I can stay informed.
- As a user, I want important emails prioritized so that I focus on urgent matters.
- As a user, I want email summaries so that I can understand conversations quickly.
- As a user, I want JARVIS to prepare email replies so that I can save time.
- As a user, I want to approve outgoing emails so that messages are not sent without authorization.

## 4.4 Fitness Manager

- As a user, I want JARVIS to retrieve workout information so that I can monitor my fitness progress.
- As a user, I want personalized workout insights so that I understand my progress.
- As a user, I want fitness activities included in my daily plan so that my routines remain consistent.

## 4.5 Planning and productivity

- As a user, I want JARVIS to create daily plans so that I know what to do.
- As a user, I want to manage tasks using natural language so that task creation is convenient.
- As a user, I want to manage recurring routines so that important habits are maintained.
- As a user, I want JARVIS to prioritize tasks using deadlines and importance so that I use my time effectively.
- As a user, I want my daily plan coordinated with Google Calendar so that scheduling conflicts are minimized.

## 4.6 Proactive assistance

- As a user, I want JARVIS to monitor important events so that I do not need to check every application manually.
- As a user, I want notifications about urgent emails and upcoming tasks so that I can respond on time.
- As a user, I want JARVIS to recommend adjustments when my schedule changes so that my day remains organized.

## 4.7 Autonomous execution

- As a user, I want JARVIS to execute approved actions so that I spend less time on repetitive work.
- As a user, I want permission controls so that sensitive operations remain under my control.
- As a user, I want an execution history so that I can see what JARVIS has done.

---

# 5. Feature List — MVP / V2 / Later

The roadmap prioritizes a working end-to-end assistant over building every advanced capability simultaneously.

## 5.1 MVP — Core JARVIS

**Objective:** Build a functional personal assistant that can understand, remember, retrieve information, plan and execute approved actions.

| Feature | Scope | Priority |
|---|---|---|
| AI conversation | Natural-language understanding and responses | P0 |
| AI orchestration | Intent detection, planning and tool selection | P0 |
| Memory system | Short-term and persistent memory | P0 |
| Email integration | Read, summarize and prioritize emails | P0 |
| Fitness integration | Retrieve workout and fitness information | P0 |
| Task Manager | Create, update, complete and prioritize tasks | P0 |
| Day Planner | Daily schedules and recommendations | P0 |
| Routine Manager | Recurring personal routines | P0 |
| Calendar integration | Read and create calendar events | P0 |
| Approval system | Approve sensitive actions | P0 |
| Unified dashboard | Centralized interface | P0 |
| Voice interaction | Push-to-talk and speech responses | P1 |
| Notifications | Important reminders and alerts | P1 |
| Execution history | Record actions and outcomes | P1 |

## 5.2 V2 — Proactive JARVIS

**Objective:** Make JARVIS more context-aware and independently useful.

| Feature | Scope |
|---|---|
| Advanced voice | Improved conversational voice experience |
| Wake-word activation | Hands-free activation |
| Smart daily briefing | Personalized morning briefing |
| Advanced memory | Semantic retrieval and memory refinement |
| Proactive planning | Automatically suggest schedule adjustments |
| Email automation | Approved reply and email workflows |
| Cross-application workflows | Coordinate email, fitness, tasks and calendar |
| Advanced notifications | Context-aware alerts |
| Finance Manager | Expense tracking and financial summaries |
| Analytics | Productivity and routine insights |

## 5.3 Later — Advanced JARVIS

**Objective:** Develop a more capable personal autonomous agent.

- Advanced multi-step autonomous planning.
- Local computer interaction.
- Smart-home integrations.
- Offline functionality where practical.
- Multi-device synchronization.
- Advanced personal finance intelligence.
- Intelligent workflow generation.
- Context-aware location and activity assistance.
- Personalized agent capabilities.
- Additional third-party integrations.

**Scope rule:** Later features must not compromise the reliability, privacy or security of the MVP.

---

# 6. Detailed Functional Requirements — MVP

## 6.1 AI Conversation and Orchestration

**Description:** The central intelligence layer of JARVIS.

### Functional requirements

| ID | Requirement |
|---|---|
| AI-01 | Accept natural-language text input. |
| AI-02 | Interpret user intent and identify required actions. |
| AI-03 | Maintain conversation context. |
| AI-04 | Select the appropriate tool or integrated service. |
| AI-05 | Support multi-step task execution. |
| AI-06 | Ask for clarification when intent is uncertain. |
| AI-07 | Return structured, understandable responses. |
| AI-08 | Handle tool failures without fabricating successful results. |
| AI-09 | Record relevant execution metadata. |
| AI-10 | Respect user permissions and approval requirements. |

### Example

User: "Check my emails and tell me what I should do today."

Expected workflow:

1. Understand the request.
2. Retrieve relevant emails.
3. Identify urgent messages and deadlines.
4. Retrieve today's calendar events.
5. Retrieve pending tasks.
6. Combine the information.
7. Recommend an ordered daily plan.
8. Ask for approval before creating or changing calendar events.

**Acceptance criteria:**
- JARVIS correctly identifies supported intents.
- JARVIS calls the appropriate integrations.
- Results are grounded in retrieved information.
- Failed tool calls are reported honestly.
- Actions requiring approval cannot bypass the approval system.

## 6.2 Personal Memory System

**Description:** Store and retrieve useful personal context across conversations.

### Functional requirements

| ID | Requirement |
|---|---|
| MEM-01 | Store explicitly approved personal memories. |
| MEM-02 | Store relevant conversation context. |
| MEM-03 | Retrieve relevant memories during conversations. |
| MEM-04 | Support memory updates and corrections. |
| MEM-05 | Support memory review and deletion. |
| MEM-06 | Distinguish temporary context from persistent memory. |
| MEM-07 | Avoid storing credentials and sensitive secrets in conversational memory. |
| MEM-08 | Associate memories with timestamps and sources. |

Memory categories:
- Personal preferences.
- Important information.
- Goals.
- Tasks and commitments.
- Routine preferences.
- Application context.
- Historical decisions.

**Acceptance criteria:**
- Relevant stored context can be retrieved in a later session.
- Updated information supersedes outdated information.
- The user can inspect and delete memories.
- Sensitive information is not silently persisted.

## 6.3 Email Manager Integration

**Description:** Connect the existing Email Manager backend as an independent service.

**Existing service:** `http://127.0.0.1:8001`

### Functional requirements

| ID | Requirement |
|---|---|
| EMAIL-01 | Check Email Manager service health. |
| EMAIL-02 | Retrieve emails using supported API endpoints. |
| EMAIL-03 | Retrieve high-priority emails. |
| EMAIL-04 | Summarize email conversations. |
| EMAIL-05 | Identify deadlines and requested actions. |
| EMAIL-06 | Present important email information. |
| EMAIL-07 | Prepare email drafts where supported. |
| EMAIL-08 | Require authorization before sending emails. |
| EMAIL-09 | Handle authentication and service failures. |

### Example commands

- "Check my emails."
- "Show important emails."
- "Summarize my latest emails."
- "Do I need to reply to anyone?"
- "Draft a reply to this email."

**Acceptance criteria:**
- JARVIS retrieves information from the real Email Manager.
- It does not invent emails or message content.
- Drafting and sending are separate operations.
- Sending requires explicit approval.

## 6.4 Fitness Manager Integration

**Description:** Connect the existing Fitness Manager backend.

**Existing service:** `http://127.0.0.1:8002`

### Functional requirements

| ID | Requirement |
|---|---|
| FIT-01 | Check Fitness Manager health. |
| FIT-02 | Retrieve workout information. |
| FIT-03 | Retrieve supported fitness statistics. |
| FIT-04 | Summarize workout progress. |
| FIT-05 | Answer questions using available fitness records. |
| FIT-06 | Include supported fitness activities in daily planning. |
| FIT-07 | Report unavailable or incomplete fitness data. |

### Example commands

- "Show my workouts."
- "How was my fitness progress?"
- "What workouts have I completed?"
- "Include my workout in today's plan."

**Acceptance criteria:**
- All fitness information comes from actual service responses.
- Unsupported data is identified instead of assumed.
- Existing Fitness Manager functionality remains independent.

## 6.5 Task Manager

**Description:** Manage personal tasks through conversational commands and the dashboard.

### Functional requirements

| ID | Requirement |
|---|---|
| TASK-01 | Create tasks. |
| TASK-02 | Update task details. |
| TASK-03 | Delete tasks. |
| TASK-04 | Mark tasks complete or incomplete. |
| TASK-05 | Assign priorities. |
| TASK-06 | Set due dates and reminders. |
| TASK-07 | Retrieve pending tasks. |
| TASK-08 | Identify overdue tasks. |
| TASK-09 | Sort tasks by priority and deadline. |
| TASK-10 | Support natural-language task creation. |

### Example commands

- "Remind me to study Python tomorrow."
- "Show my pending tasks."
- "Mark assignment submission complete."
- "What are my most important tasks?"

**Acceptance criteria:**
- Tasks persist after application restarts.
- Updates are reflected in the dashboard.
- Due dates use the configured timezone.
- Duplicate task creation is avoided when an action is retried.

## 6.6 Day Planner

**Description:** Generate and maintain a daily personal schedule.

### Functional requirements

| ID | Requirement |
|---|---|
| PLAN-01 | Generate a daily plan. |
| PLAN-02 | Retrieve existing calendar commitments. |
| PLAN-03 | Include pending tasks. |
| PLAN-04 | Consider task priorities and deadlines. |
| PLAN-05 | Include configured routines. |
| PLAN-06 | Include scheduled fitness activities. |
| PLAN-07 | Detect scheduling conflicts. |
| PLAN-08 | Recommend schedule adjustments. |
| PLAN-09 | Allow manual schedule changes. |
| PLAN-10 | Preserve user-approved schedules. |

### Example

User: "Plan my day."

JARVIS:
1. Checks calendar availability.
2. Retrieves pending tasks.
3. Checks important emails.
4. Reviews configured routines.
5. Suggests a schedule.
6. Identifies conflicts.
7. Presents the proposed plan.
8. Requests approval before creating or changing external calendar events.

**Acceptance criteria:**
- Plans reflect actual retrieved information.
- Existing commitments are not silently overwritten.
- Scheduling conflicts are visible.
- Proposed changes remain separate from confirmed changes.

## 6.7 Routine Manager

**Description:** Maintain recurring activities and personal routines.

### Functional requirements

| ID | Requirement |
|---|---|
| ROUT-01 | Create routines. |
| ROUT-02 | Update routines. |
| ROUT-03 | Delete or deactivate routines. |
| ROUT-04 | Support recurring schedules. |
| ROUT-05 | Track routine completion. |
| ROUT-06 | Show upcoming routines. |
| ROUT-07 | Generate routine reminders. |
| ROUT-08 | Display completion history. |

### Example routines

- Morning routine.
- Study routine.
- Workout routine.
- Evening routine.
- Weekly review.

**Acceptance criteria:**
- Recurring schedules generate the correct occurrences.
- Completion history is retained.
- Missed routines are not automatically marked completed.
- Timezone changes are handled consistently.

## 6.8 Google Calendar Integration

**Description:** Coordinate JARVIS planning with Google Calendar.

### Functional requirements

| ID | Requirement |
|---|---|
| CAL-01 | Authenticate using Google OAuth 2.0. |
| CAL-02 | Retrieve upcoming events. |
| CAL-03 | Retrieve events for a specified date. |
| CAL-04 | Check calendar availability where supported. |
| CAL-05 | Create events after approval. |
| CAL-06 | Update events after approval. |
| CAL-07 | Cancel events after approval. |
| CAL-08 | Detect scheduling conflicts. |
| CAL-09 | Handle expired OAuth credentials. |

**Acceptance criteria:**
- Calendar data is retrieved from the authenticated account.
- Event creation and modification are confirmed by Google Calendar.
- Failed operations are not reported as successful.
- OAuth credentials are stored securely.

## 6.9 Voice Interaction

**Description:** Allow natural voice communication with JARVIS.

### Functional requirements

| ID | Requirement |
|---|---|
| VOICE-01 | Capture voice input. |
| VOICE-02 | Convert speech into text. |
| VOICE-03 | Process transcribed commands using the AI orchestration layer. |
| VOICE-04 | Generate spoken responses. |
| VOICE-05 | Display transcriptions. |
| VOICE-06 | Handle microphone permission failures. |
| VOICE-07 | Allow text interaction as a fallback. |

**MVP approach:** Push-to-talk first. Wake-word activation is V2 because it introduces additional background processing, permission and resource requirements.

## 6.10 Proactive Monitoring and Notifications

**Description:** Detect important events and notify the user without requiring a manual request.

### Functional requirements

| ID | Requirement |
|---|---|
| NOTIF-01 | Monitor configured sources at defined intervals. |
| NOTIF-02 | Identify important events. |
| NOTIF-03 | Generate task reminders. |
| NOTIF-04 | Generate calendar reminders. |
| NOTIF-05 | Notify about configured email priorities. |
| NOTIF-06 | Prevent repeated notifications for the same event. |
| NOTIF-07 | Allow notification preferences. |
| NOTIF-08 | Record notification delivery status. |

**MVP approach:** Scheduled polling and in-app notifications. Browser notifications may be supported with permission.

Background monitoring must use bounded polling intervals and respect free-tier API quotas.

## 6.11 Permission-Based Autonomous Execution

**Description:** Give JARVIS the ability to execute multi-step workflows safely.

### Autonomy levels

| Level | Behavior |
|---|---|
| L0 | Read-only information retrieval |
| L1 | Recommendations and planning |
| L2 | Reversible internal actions |
| L3 | External actions with explicit approval |
| L4 | Pre-authorized, narrowly scoped automation |

Examples:

- Reading emails: L0.
- Recommending an email response: L1.
- Creating a local task: L2.
- Sending an email: L3.
- Automatically creating a daily briefing: L4, if explicitly configured.

### Functional requirements

| ID | Requirement |
|---|---|
| AUTO-01 | Classify actions by risk. |
| AUTO-02 | Check user permissions before execution. |
| AUTO-03 | Request approval for sensitive actions. |
| AUTO-04 | Display action details before approval. |
| AUTO-05 | Execute only the approved operation. |
| AUTO-06 | Record execution outcomes. |
| AUTO-07 | Handle rejected and expired approvals. |
| AUTO-08 | Support cancellation where technically possible. |
| AUTO-09 | Prevent unauthorized tool execution. |
| AUTO-10 | Require renewed approval when an approved action materially changes. |

**Non-negotiable rule:** AI-generated intent is not authorization. JARVIS must independently validate permissions before executing any action.

## 6.12 Unified Dashboard

**Description:** Provide one interface to access all JARVIS capabilities.

### Required sections

1. Home Dashboard.
2. AI Chat.
3. Voice Assistant.
4. My Day.
5. Tasks.
6. Routines.
7. Calendar.
8. Email.
9. Fitness.
10. Memory.
11. Notifications.
12. Activity History.
13. Settings and Permissions.

### Home dashboard information

- Today's schedule.
- Pending tasks.
- Important emails.
- Upcoming routines.
- Fitness summary.
- Notifications.
- JARVIS service status.

**Acceptance criteria:**
- User can access major capabilities without navigating separate applications.
- Service connection status is visible.
- The dashboard distinguishes actual information from AI recommendations.

---

# 7. Data Model Sketch

The following is the proposed JARVIS-owned data model. Existing Email Manager and Fitness Manager data should remain in their respective services.

## 7.1 Core entities

### UserProfile

| Field | Type |
|---|---|
| id | UUID |
| display_name | String |
| timezone | String |
| preferences | JSON |
| created_at | Timestamp |
| updated_at | Timestamp |

Single-user architecture: one owner profile initially. No multi-user authentication system is required for MVP.

### Conversation

| Field | Type |
|---|---|
| id | UUID |
| title | String |
| created_at | Timestamp |
| updated_at | Timestamp |

### Message

| Field | Type |
|---|---|
| id | UUID |
| conversation_id | UUID |
| role | String |
| content | Text |
| metadata | JSON |
| created_at | Timestamp |

### Memory

| Field | Type |
|---|---|
| id | UUID |
| category | String |
| content | Text |
| source | String |
| confidence | Float |
| importance | Integer |
| created_at | Timestamp |
| updated_at | Timestamp |
| expires_at | Timestamp, nullable |

### Task

| Field | Type |
|---|---|
| id | UUID |
| title | String |
| description | Text |
| status | Enum |
| priority | Enum |
| due_at | Timestamp, nullable |
| reminder_at | Timestamp, nullable |
| created_at | Timestamp |
| updated_at | Timestamp |

### Routine

| Field | Type |
|---|---|
| id | UUID |
| name | String |
| description | Text |
| recurrence_rule | String |
| scheduled_time | Time |
| timezone | String |
| is_active | Boolean |
| created_at | Timestamp |

### RoutineCompletion

| Field | Type |
|---|---|
| id | UUID |
| routine_id | UUID |
| scheduled_at | Timestamp |
| completed_at | Timestamp, nullable |
| status | Enum |

### DailyPlan

| Field | Type |
|---|---|
| id | UUID |
| plan_date | Date |
| timezone | String |
| status | Enum |
| summary | Text |
| created_at | Timestamp |
| updated_at | Timestamp |

### PlanItem

| Field | Type |
|---|---|
| id | UUID |
| daily_plan_id | UUID |
| task_id | UUID, nullable |
| title | String |
| start_at | Timestamp |
| end_at | Timestamp |
| source | String |
| status | Enum |

### ApprovalRequest

| Field | Type |
|---|---|
| id | UUID |
| action_type | String |
| action_payload | JSON |
| risk_level | String |
| status | Enum |
| requested_at | Timestamp |
| expires_at | Timestamp |
| approved_at | Timestamp, nullable |
| executed_at | Timestamp, nullable |

### Integration

| Field | Type |
|---|---|
| id | UUID |
| service_name | String |
| base_url | String |
| status | String |
| configuration | JSON |
| last_health_check | Timestamp |

Credentials and tokens must not be stored as ordinary plaintext configuration.

### Notification

| Field | Type |
|---|---|
| id | UUID |
| title | String |
| message | Text |
| category | String |
| source | String |
| status | Enum |
| deduplication_key | String |
| scheduled_at | Timestamp |
| delivered_at | Timestamp, nullable |

### ActivityLog

| Field | Type |
|---|---|
| id | UUID |
| action_type | String |
| actor | String |
| status | String |
| request_id | UUID |
| details | JSON |
| created_at | Timestamp |

## 7.2 Relationships

- Conversation → Messages: one-to-many.
- DailyPlan → PlanItems: one-to-many.
- Task → PlanItems: one-to-many, optional.
- Routine → RoutineCompletions: one-to-many.
- ApprovalRequest → ActivityLog: one-to-many.
- Integration → External service configuration.
- Notification → ActivityLog: optional relationship through source or event reference.

## 7.3 Storage recommendation

**Recommended MVP database: PostgreSQL.**

Reasons:
- Free and open source.
- Structured relational data.
- Reliable transactions.
- JSON support.
- Suitable for tasks, schedules, approvals and logs.
- Supports future vector-search integration.

For semantic memory retrieval, begin with PostgreSQL full-text search or a lightweight local embedding solution. Add pgvector only when necessary.

---

# 8. Edge Cases and Failure States

| Scenario | Expected behavior |
|---|---|
| Gemini API unavailable | Display a clear error; preserve user input where possible. |
| AI returns malformed tool arguments | Validate, reject and request correction. |
| Email Manager unavailable | Report email integration as unavailable; other features continue. |
| Fitness Manager unavailable | Report missing fitness information without inventing data. |
| Google OAuth expires | Request reauthentication. |
| Calendar conflict detected | Show conflicting events and request a decision. |
| Duplicate task request | Use idempotency controls or ask for confirmation when ambiguous. |
| User gives an ambiguous command | Ask one clarifying question. |
| Database unavailable | Do not report unsaved changes as successful. |
| Duplicate notifications | Deduplicate using event identifiers and notification keys. |
| Notification permission denied | Keep notifications in the in-app notification center. |
| Voice transcription fails | Offer text input. |
| Internet unavailable | Show offline status and limit unavailable features. |
| Approval expires | Reject the pending action. |
| User rejects approval | Record rejection and do not execute. |
| Action partially succeeds | Report completed and failed steps separately. |
| External API rate limit | Apply backoff and retry within configured limits. |
| Timezone changes | Preserve timestamps and recalculate future schedules correctly. |
| Service returns incomplete data | Identify missing information explicitly. |
| User asks to delete memory | Delete the selected memory and associated retrievable content according to retention policy. |
| Unauthorized API request | Reject access and record the security event. |

## 8.1 Critical safety requirements

1. Never send emails without authorization.
2. Never delete important external data without explicit authorization.
3. Never create or modify calendar events without the configured approval.
4. Never expose API keys or OAuth tokens to the AI model.
5. Never treat AI-generated tool instructions as trusted code.
6. Validate all tool arguments on the backend.
7. Maintain an auditable execution history.
8. Do not fabricate successful operations.
9. Prevent duplicate execution during retries.
10. Provide a global automation disable control.

---

# 9. Success Metrics

Metrics should measure whether JARVIS actually reduces manual effort and completes useful workflows reliably.

## 9.1 Core product metrics

| Metric | Initial target |
|---|---|
| Successful supported command execution | ≥95% |
| Tool-routing accuracy | ≥95% |
| Successful memory retrieval for tested relevant queries | ≥90% |
| Task creation and update success | ≥99% |
| Integration health-check success when services are available | ≥99% |
| Duplicate notification rate | <1% |
| Unauthorized external actions | 0 |
| Actions falsely reported as successful | 0 |
| Approval enforcement | 100% |
| Daily plan generation success | ≥95% |

Targets apply to controlled testing and functioning dependencies, not guaranteed external API availability.

## 9.2 User experience metrics

- Time required to complete common tasks.
- Number of manual application switches avoided.
- Percentage of daily plans successfully generated.
- Number of important events correctly surfaced.
- Voice command success rate.
- Percentage of notifications considered useful.
- Frequency of repeated or unnecessary questions.

## 9.3 MVP release criteria

JARVIS is ready for its first major release when:

1. Natural-language conversation works reliably.
2. Persistent memory works across sessions.
3. Email Manager is integrated and usable.
4. Fitness Manager is integrated and usable.
5. Tasks can be created, updated and completed.
6. Daily plans can be generated.
7. Routines can be created and tracked.
8. Google Calendar can be connected and used.
9. Voice interaction works through push-to-talk.
10. Notifications work for configured events.
11. Approval-controlled actions are enforced.
12. Dashboard provides access to the major modules.
13. Error handling and execution history work.
14. No critical security issues remain.

---

# 10. Open Questions

These decisions must be finalized during implementation rather than silently assumed.

| ID | Question | Proposed default |
|---|---|---|
| OQ-01 | Which database should be used? | PostgreSQL |
| OQ-02 | Which frontend framework? | React + TypeScript |
| OQ-03 | Which voice technology? | Browser speech APIs initially; evaluate free alternatives |
| OQ-04 | Should memory be fully automatic? | Extract suggestions automatically; persist according to memory policy |
| OQ-05 | How frequently should integrations be monitored? | Configurable polling intervals |
| OQ-06 | Which notification channels? | In-app first, browser notifications second |
| OQ-07 | Should Finance Manager be part of MVP? | V2 initially; define scope before implementation |
| OQ-08 | Should JARVIS work when the computer is off? | Not guaranteed in MVP |
| OQ-09 | Where will JARVIS be hosted? | Local development initially |
| OQ-10 | Should autonomous actions have configurable permission levels? | Yes |
| OQ-11 | What is the memory retention policy? | User-controlled retention and deletion |
| OQ-12 | Should JARVIS support multiple AI providers? | Gemini first; provider abstraction recommended |

---

# Additional Product and Technical Decisions

## A. Architecture principles

JARVIS must use a modular architecture.

The central AI orchestrator should coordinate services rather than contain every feature's business logic.

Proposed components:

1. API Gateway — receives user requests.
2. AI Orchestrator — understands requests and coordinates workflows.
3. AI Service — communicates with Gemini.
4. Memory Service — stores and retrieves personal context.
5. Tool Registry — exposes approved tools to the orchestrator.
6. Task Service — manages tasks.
7. Planner Service — generates daily plans.
8. Routine Service — manages recurring activities.
9. Integration Layer — connects external applications.
10. Approval Service — authorizes sensitive operations.
11. Notification Service — manages alerts.
12. Database Layer — stores JARVIS-owned information.
13. Frontend — unified user experience.

## B. Existing application integration

The following applications remain independent:

- Email Manager — port 8001.
- Fitness Manager — port 8002.
- JARVIS — port 8000.

JARVIS communicates with them using authenticated, documented APIs where supported.

The integration layer must isolate service-specific logic so that changes to either application do not require rewriting the AI orchestrator.

## C. Technical constraints

- Use free and open-source technologies.
- Avoid mandatory paid subscriptions.
- Prefer asynchronous API operations.
- Implement timeouts, retries and circuit breakers.
- Validate API responses.
- Protect secrets using environment configuration and secure credential storage.
- Keep application-specific business logic in the respective services.
- Use a configurable timezone, initially `Asia/Kolkata`.
- Ensure integrations can be disabled independently.

Free-tier API quotas, availability and terms must be verified before deployment. ₹0 is a cost constraint, not a guarantee of unlimited operation.

## D. Product quality principles

JARVIS must be:

- Accurate rather than merely conversational.
- Context-aware rather than repetitive.
- Proactive rather than entirely reactive.
- Modular rather than tightly coupled.
- Secure rather than unrestricted.
- Transparent rather than silently autonomous.
- Reliable rather than feature-heavy.

## E. Final product definition

JARVIS is a single-user, context-aware personal AI agent that connects personal applications, maintains useful memory, manages daily activities, monitors important events and executes authorized workflows through a unified conversational interface.

**The ultimate goal is to move from an assistant that answers questions to an assistant that helps manage and execute everyday life.**