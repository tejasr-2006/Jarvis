# JARVIS — Complete Product Design Specification

**Version:** 1.0  
**Status:** Design direction approved for implementation planning  
**Product:** Personal AI assistant  
**Primary user:** Single-user personal system  
**Primary platform:** Responsive web application  
**Recommended frontend:** React + TypeScript  
**Design approach:** Desktop-first, responsive, voice-ready

---

# 1. Design Principles

These are the three rules every JARVIS screen must obey.

## Principle 1 — Intelligence without complexity

JARVIS should make complicated operations feel simple.

The user should be able to ask:

"What's important today?"

JARVIS should combine emails, tasks, calendar events and routines into one understandable response.

Rules:
- Prefer natural-language interaction over complex navigation.
- Show useful summaries before detailed information.
- Group related information together.
- Avoid unnecessary configuration.
- Never force users to understand internal system architecture.

**Design test:** Can the user understand what needs attention within five seconds of opening the dashboard?

## Principle 2 — User control over AI autonomy

JARVIS is an autonomous agent, but it must never feel unpredictable.

Rules:
- Clearly distinguish recommendations from executed actions.
- Show pending approvals prominently.
- Explain what an action will change before execution.
- Display execution results.
- Provide cancellation or undo where technically possible.
- Make automation permissions visible and configurable.

**Design test:** Can the user identify what JARVIS is about to do, why it is doing it and whether approval is required?

## Principle 3 — Calm, continuous awareness

JARVIS should keep the user informed without becoming distracting.

Rules:
- Prioritize important information.
- Avoid excessive notifications.
- Use motion only to communicate meaningful changes.
- Maintain consistent status indicators.
- Keep the assistant accessible throughout the application.
- Surface urgent information without turning the entire interface into an alert system.

**Design test:** Can the user identify the most important current event without searching through multiple screens?

---

# 2. Visual Direction

## 2.1 Chosen direction: Dark Intelligence

JARVIS should look like a premium personal AI command center.

### Mood

- Futuristic.
- Intelligent.
- Minimal.
- Precise.
- Professional.
- Calm.
- Technologically advanced.

### Visual references

Use the following as design inspiration, not as templates to copy.

| Reference | What to take from it |
|---|---|
| Linear | Information hierarchy, compact layouts, keyboard-first interactions |
| Apple macOS | Consistent spacing, restrained interface, premium simplicity |
| Raycast | Command interface and fast interactions |
| OpenAI ChatGPT | Conversational interaction and AI response presentation |
| Notion | Organization of information and readable content |
| Mission-control interfaces | Status visibility and system awareness |

### Visual direction examples

**Dashboard:** A calm overview with today's schedule, important emails, pending tasks and assistant status.

**AI assistant:** A central conversational workspace with a persistent command composer.

**Approvals:** A clear action-review interface that makes consequences understandable.

**System status:** Small indicators showing the health of integrations and background services.

## 2.2 What to avoid

Do not use:

- Excessive neon colors.
- Bright glowing borders on every card.
- Constant animations.
- Decorative holographic effects.
- Large unnecessary gradients.
- Excessive glassmorphism.
- Tiny futuristic fonts.
- Complicated circular gauges.
- Overloaded dashboard layouts.
- Fake real-time system activity.
- Decorative graphs without useful information.

**Reason:** JARVIS is a working personal assistant, not a visual demonstration of an AI concept.

## 2.3 Signature visual element

Create a distinctive JARVIS AI presence indicator.

This should be a small circular animated identity mark.

Its visual states:

| State | Appearance |
|---|---|
| Idle | Static cyan ring |
| Listening | Animated cyan waveform |
| Thinking | Slowly rotating segmented ring |
| Executing | Moving cyan progress indicator |
| Speaking | Pulsing waveform |
| Waiting for approval | Amber ring |
| Error | Red indicator |
| Offline | Muted grey ring |

The indicator should communicate actual system state. Never animate it to imply that JARVIS is processing when it is not.

---

# 3. Design Tokens

These tokens define the visual system and must be shared across the entire frontend.

## 3.1 Color palette

### Background colors

| Token | Hex | Usage |
|---|---|---|
| Background Primary | #0B0F14 | Main application background |
| Background Secondary | #101720 | Sidebar and secondary regions |
| Surface Primary | #141D27 | Standard cards |
| Surface Elevated | #1C2733 | Modals, popovers and elevated cards |
| Surface Hover | #22303D | Hovered interactive surfaces |
| Border Subtle | #273442 | Dividers and card borders |
| Border Strong | #394A5C | Emphasized borders |

**Reason:** The near-black graphite foundation creates a premium, low-distraction environment without relying on pure black.

### Brand colors

| Token | Hex | Usage |
|---|---|---|
| Primary Cyan | #54D6E8 | Main accent and AI identity |
| Cyan Hover | #75E2EF | Hover and active emphasis |
| Cyan Muted | #173C45 | Subtle accent backgrounds |
| On Cyan | #071318 | Text on cyan-filled buttons |

**Reason:** Cyan communicates technology and intelligence while remaining readable against the dark foundation.

Cyan should identify JARVIS-related actions, not every clickable element.

### Text colors

| Token | Hex | Usage |
|---|---|---|
| Text Primary | #F4F7FA | Main content |
| Text Secondary | #B1BDCA | Descriptions and secondary labels |
| Text Muted | #8795A5 | Supporting information |
| Text Disabled | #647181 | Disabled controls |

### Status colors

| Status | Hex | Usage |
|---|---|---|
| Success | #55C99A | Completed operations |
| Warning | #F4B860 | Pending approval and attention |
| Error | #FF7272 | Failed operations |
| Information | #70B8FF | Informational notices |

Status must always include a text label or icon. Never communicate status using color alone.

### Category colors

| Category | Hex |
|---|---|
| AI | #54D6E8 |
| Email | #70B8FF |
| Fitness | #55C99A |
| Tasks | #A78BFA |
| Calendar | #F4B860 |
| Routines | #E69AC8 |
| Finance | #78C8B2 |

Use category colors sparingly for icons, labels and small visual indicators.

## 3.2 Typography

### Primary font: Inter

Use **Inter** as the primary interface font.

Why:
- Excellent readability at small sizes.
- Clear distinction between characters.
- Works well with dense dashboards.
- Consistent appearance across operating systems.
- Suitable for both technical and everyday information.

### Secondary font: JetBrains Mono

Use **JetBrains Mono** only for:
- Timestamps.
- Technical identifiers.
- API status details.
- System logs.
- Latency and numerical diagnostics.

Do not use monospace for normal conversations or dashboard headings.

### Type scale

| Style | Size | Weight | Usage |
|---|---:|---:|---|
| Display | 36px | 650 | Dashboard welcome |
| H1 | 30px | 650 | Main page headings |
| H2 | 24px | 600 | Major sections |
| H3 | 20px | 600 | Card headings |
| H4 | 16px | 600 | Component headings |
| Body Large | 16px | 400 | Main descriptions |
| Body | 14px | 400 | Default interface text |
| Body Small | 13px | 400 | Secondary information |
| Caption | 12px | 500 | Metadata |
| Micro | 11px | 500 | Dense technical labels only |

Recommended line heights:
- Headings: 1.2.
- Body: 1.5.
- Metadata: 1.4.

Avoid using 11px text for essential content.

## 3.3 Spacing scale

Use a consistent 4px base unit.

| Token | Value |
|---|---:|
| Space 1 | 4px |
| Space 2 | 8px |
| Space 3 | 12px |
| Space 4 | 16px |
| Space 5 | 20px |
| Space 6 | 24px |
| Space 8 | 32px |
| Space 10 | 40px |
| Space 12 | 48px |
| Space 16 | 64px |
| Space 20 | 80px |

Recommended usage:
- Icon-to-label spacing: 8px.
- Input padding: 12–16px.
- Card padding: 20–24px.
- Section spacing: 24–32px.
- Major page separation: 32–40px.

## 3.4 Radius scale

| Token | Value | Usage |
|---|---:|---|
| Radius XS | 4px | Small indicators |
| Radius SM | 6px | Compact controls |
| Radius MD | 10px | Inputs and buttons |
| Radius LG | 14px | Cards |
| Radius XL | 20px | Large panels |
| Radius 2XL | 24px | Major overlays |
| Radius Full | 999px | Pills and avatars |

Avoid making every component fully rounded.

## 3.5 Shadows

Dark interfaces should use subtle elevation rather than heavy shadows.

| Token | Specification | Usage |
|---|---|---|
| Shadow SM | 0 2px 8px rgba(0,0,0,.18) | Small popovers |
| Shadow MD | 0 6px 20px rgba(0,0,0,.24) | Cards and dropdowns |
| Shadow LG | 0 12px 36px rgba(0,0,0,.34) | Modals and command palette |
| Focus Ring | 0 0 0 3px rgba(84,214,232,.28) | Keyboard focus |

Use borders for normal card separation. Shadows are reserved for actual elevation.

## 3.6 Motion tokens

| Token | Duration | Usage |
|---|---:|---|
| Fast | 120ms | Hover and focus |
| Normal | 200ms | Dropdowns and state changes |
| Slow | 300ms | Drawer and modal |
| AI | 600–1200ms | Subtle processing indicator |

Use ease-out for entering elements and ease-in for exiting elements.

Respect reduced-motion preferences.

---

# 4. Screen Inventory

The application will contain 15 primary screens.

| ID | Screen | Purpose | Priority |
|---|---|---|---|
| S01 | Welcome / Setup | Initial configuration | P0 |
| S02 | Home Dashboard | Daily command center | P0 |
| S03 | AI Assistant | Conversations and commands | P0 |
| S04 | My Day | Daily plan and schedule | P0 |
| S05 | Task Manager | Task management | P0 |
| S06 | Routine Manager | Recurring routines | P0 |
| S07 | Calendar | Events and availability | P0 |
| S08 | Email Center | Email summaries and priorities | P0 |
| S09 | Fitness Center | Fitness information and progress | P0 |
| S10 | Notifications | Important alerts | P1 |
| S11 | Memory Center | View and manage memory | P0 |
| S12 | Approval Center | Review and approve actions | P0 |
| S13 | Activity History | Review executed actions | P1 |
| S14 | Integrations | Manage connected services | P0 |
| S15 | Settings | Configure JARVIS | P0 |

## Navigation structure

Primary sidebar:

1. Home
2. AI Assistant
3. My Day
4. Tasks
5. Routines
6. Calendar
7. Email
8. Fitness

Secondary navigation:

- Notifications
- Memory
- Approvals
- Activity History
- Integrations
- Settings

The sidebar should remain visually compact. The user should not have to navigate through deeply nested menus.

---

# 5. User Flows

## Flow 1 — First-time setup

**Goal:** Get JARVIS ready for its first interaction.

1. User opens JARVIS.
2. Welcome screen introduces the assistant.
3. User configures display preferences.
4. User confirms timezone.
5. User configures AI provider and API credentials.
6. User connects Email Manager.
7. User connects Fitness Manager.
8. User connects Google Calendar.
9. JARVIS tests integration health.
10. User configures permission preferences.
11. Setup completes.
12. User enters the Home Dashboard.

Important:
- Allow users to skip optional integrations.
- Show missing configuration clearly.
- Never display API keys after they have been saved.
- Provide a retry option for failed integrations.

## Flow 2 — Ask JARVIS a question

**Goal:** Get a contextual answer.

1. User opens AI Assistant.
2. User enters a natural-language command.
3. JARVIS displays the submitted message.
4. AI processing indicator appears.
5. JARVIS identifies the intent.
6. Required tools execute.
7. Retrieved results are combined.
8. JARVIS displays its answer.
9. User can continue the conversation.

Example:

"How is my day looking?"

Expected result:
- Upcoming calendar events.
- Pending tasks.
- Important emails.
- Scheduled routines.
- Relevant recommendations.

## Flow 3 — Voice interaction

**Goal:** Use JARVIS hands-free where supported.

1. User presses the microphone button.
2. JARVIS enters listening state.
3. Waveform indicates microphone activity.
4. User speaks.
5. Speech is transcribed.
6. Transcript is displayed.
7. User submits or confirms if necessary.
8. JARVIS processes the request.
9. Response appears.
10. Speech playback begins if enabled.

If transcription is unclear, JARVIS asks the user to repeat the command.

## Flow 4 — Create and manage tasks

1. User opens Task Manager.
2. Selects Add Task or enters a conversational command.
3. Task creation form appears.
4. User enters title, priority and deadline.
5. User saves the task.
6. JARVIS validates the input.
7. Task is saved.
8. Success notification appears.
9. Task becomes visible in the task list.
10. The task can be included in the daily plan.

## Flow 5 — Generate daily plan

1. User opens My Day.
2. Selects Generate Plan.
3. JARVIS retrieves calendar events.
4. JARVIS retrieves pending tasks.
5. JARVIS checks configured routines.
6. JARVIS retrieves relevant email priorities.
7. JARVIS considers scheduled fitness activities.
8. JARVIS generates a proposed plan.
9. User reviews the schedule.
10. User edits or accepts the proposal.
11. JARVIS saves the plan.
12. Calendar changes require separate authorization.

## Flow 6 — Email management

1. User opens Email Center.
2. JARVIS retrieves available email information.
3. Emails are grouped by priority.
4. User selects an email.
5. Email details and summary appear.
6. User requests a suggested reply.
7. JARVIS generates a draft.
8. User reviews and edits the draft.
9. User selects Send.
10. Approval confirmation appears.
11. User approves.
12. JARVIS executes the send operation.
13. Result is recorded in Activity History.

## Flow 7 — Fitness management

1. User opens Fitness Center.
2. JARVIS checks Fitness Manager connectivity.
3. Workout information loads.
4. User selects a workout or progress view.
5. JARVIS displays available information.
6. User asks for a progress summary.
7. JARVIS generates insights using retrieved records.
8. User can request fitness activities be added to My Day.

## Flow 8 — Calendar coordination

1. User opens Calendar.
2. Events load from Google Calendar.
3. User chooses a date.
4. JARVIS displays existing commitments.
5. User requests a new event.
6. Event details are entered.
7. JARVIS checks for conflicts.
8. User reviews the proposed event.
9. Approval is requested.
10. Event is created.
11. Calendar refreshes.
12. Activity History records the result.

## Flow 9 — Autonomous approval

1. JARVIS identifies an action requiring authorization.
2. Approval card appears.
3. User opens action details.
4. JARVIS explains the reason and consequences.
5. User reviews the exact operation.
6. User approves or rejects.
7. JARVIS validates the approval.
8. Approved operation executes.
9. Result is displayed.
10. Activity History is updated.

If the operation changes after approval, the previous approval becomes invalid.

## Flow 10 — Memory management

1. User opens Memory Center.
2. JARVIS displays stored memories.
3. User filters by category.
4. User selects a memory.
5. User views its details and source.
6. User edits, deletes or retains it.
7. Changes are saved.
8. Memory status updates.

## Flow 11 — Proactive notifications

1. Background monitoring identifies a configured event.
2. JARVIS evaluates its relevance.
3. Notification is generated.
4. Duplicate notification check runs.
5. Notification appears in the application.
6. User opens the notification.
7. Relevant screen or action is opened.
8. User acts or dismisses it.

---

# 6. Per-Screen Layout Specifications

## S01 — Welcome / Setup

**Purpose:** Introduce JARVIS and configure initial services.

### Layout

1. JARVIS identity mark.
2. Welcome heading.
3. Short product introduction.
4. Configuration progress indicator.
5. Setup form.
6. Integration connection cards.
7. Permission configuration.
8. Continue button.

**Hierarchy:**
- Product identity.
- Setup progress.
- Current configuration step.
- Primary action.

**Primary action:** Continue Setup.

**Components:**
- Stepper.
- Input fields.
- Integration cards.
- Connection status.
- Password field.
- Primary button.
- Error alert.

## S02 — Home Dashboard

**Purpose:** Give the user an immediate overview of their digital life.

### Layout

Top bar:
- JARVIS logo.
- Search / command trigger.
- Notifications.
- Profile and settings.

Sidebar:
- Main navigation.

Main content:

1. Greeting: "Good morning."
2. JARVIS status and command panel.
3. Pending approvals summary.
4. Today's schedule.
5. Priority tasks.
6. Important emails.
7. Fitness overview.
8. Upcoming routines.
9. Recent activity.

Recommended desktop layout:

- Main column: approximately 68%.
- Secondary column: approximately 32%.
- Sidebar: 240px expanded, 72px collapsed.

**Primary action:** Ask JARVIS.

**Secondary actions:**
- View My Day.
- Complete task.
- Review approval.
- View important email.

**Components:**
- Sidebar.
- Top navigation.
- AI status card.
- Command input.
- Task card.
- Schedule card.
- Email summary card.
- Fitness summary card.
- Activity feed.
- Notification badge.

## S03 — AI Assistant

**Purpose:** Main conversational workspace.

### Layout

1. Conversation header.
2. JARVIS status.
3. Conversation history.
4. AI response area.
5. Tool activity indicator.
6. Message composer.
7. Voice button.
8. Attachment action, if supported.
9. Conversation controls.

The message composer remains at the bottom.

AI responses should support:
- Paragraphs.
- Lists.
- Tables.
- Action suggestions.
- Integration result cards.
- Approval cards.
- Error messages.

**Primary action:** Send command.

**Components:**
- Message bubble.
- AI response.
- Command composer.
- Voice control.
- Processing indicator.
- Tool execution card.
- Approval card.
- Suggested prompt.

## S04 — My Day

**Purpose:** Show and manage the user's daily plan.

### Layout

1. Date and greeting.
2. Generate Plan button.
3. Daily completion summary.
4. Timeline.
5. Upcoming events.
6. Task schedule.
7. Routine checklist.
8. Conflicts and recommendations.

**Primary action:** Generate Plan.

**Components:**
- Timeline.
- Schedule event card.
- Task item.
- Routine item.
- Completion progress.
- Conflict banner.
- Plan action bar.

## S05 — Task Manager

**Purpose:** Manage all personal tasks.

### Layout

1. Page heading.
2. Add Task button.
3. Search.
4. Filters.
5. Task statistics.
6. Task list.
7. Task detail drawer.

Task groups:
- Overdue.
- Today.
- Upcoming.
- Completed.

**Primary action:** Add Task.

**Components:**
- Task row.
- Priority badge.
- Due-date label.
- Checkbox.
- Filter menu.
- Search input.
- Task form.
- Empty state.

## S06 — Routine Manager

**Purpose:** Create and monitor recurring activities.

### Layout

1. Heading.
2. Add Routine.
3. Today's routines.
4. Active routines.
5. Completion history.
6. Routine details drawer.

**Primary action:** Create Routine.

**Components:**
- Routine card.
- Recurrence selector.
- Time selector.
- Completion toggle.
- Streak indicator, if supported by actual history.
- History list.

## S07 — Calendar

**Purpose:** Coordinate scheduled activities.

### Layout

1. Calendar heading.
2. Date navigation.
3. Today button.
4. View selector.
5. Calendar grid or timeline.
6. Event details panel.
7. Add Event button.
8. Conflict indicators.

Views:
- Day.
- Week.
- Month.

**Primary action:** Add Event.

**Components:**
- Calendar grid.
- Event block.
- Date picker.
- Event form.
- Conflict indicator.
- Event detail drawer.
- Approval dialog.

## S08 — Email Center

**Purpose:** Prioritize and understand emails.

### Layout

1. Email heading.
2. Integration connection indicator.
3. Priority summary.
4. Category filters.
5. Email list.
6. Email details panel.
7. AI summary.
8. Suggested actions.

Email groups:
- High priority.
- Requires response.
- Informational.
- Archived, if supported.

**Primary action:** Open important email.

**Components:**
- Email row.
- Sender avatar or initials.
- Priority indicator.
- Email summary.
- Detail viewer.
- AI response suggestion.
- Draft editor.
- Send approval dialog.

## S09 — Fitness Center

**Purpose:** Show workout history and fitness progress.

### Layout

1. Fitness overview.
2. Integration status.
3. Recent workouts.
4. Weekly activity.
5. Supported progress metrics.
6. Workout details.
7. AI insights.

**Primary action:** View Workout History.

**Components:**
- Fitness metric card.
- Workout card.
- Progress chart.
- Date filter.
- AI insight card.
- Empty state.

Only show metrics returned by Fitness Manager. Never fabricate calories, weight, repetitions or progress.

## S10 — Notifications

**Purpose:** Present important events and reminders.

### Layout

1. Notification heading.
2. Unread count.
3. Filters.
4. Notification groups.
5. Notification detail.
6. Mark all as read.

**Primary action:** Open notification.

**Components:**
- Notification item.
- Category icon.
- Timestamp.
- Unread indicator.
- Filter tabs.
- Empty state.

## S11 — Memory Center

**Purpose:** Give the user control over JARVIS memory.

### Layout

1. Memory heading.
2. Search memories.
3. Category filters.
4. Memory list.
5. Memory details panel.
6. Edit and delete actions.

Categories:
- Preferences.
- Goals.
- Personal context.
- Workflows.
- Historical decisions.

**Primary action:** Review Memory.

**Components:**
- Memory card.
- Category tag.
- Search field.
- Edit form.
- Delete confirmation.
- Source and timestamp metadata.

## S12 — Approval Center

**Purpose:** Centralize pending autonomous actions.

### Layout

1. Pending approval count.
2. Approval list.
3. Risk indicators.
4. Action detail.
5. Reason for action.
6. Exact proposed changes.
7. Approve and Reject buttons.

**Primary action:** Review Action.

**Components:**
- Approval card.
- Risk badge.
- Action summary.
- Before/after details.
- Approve button.
- Reject button.
- Expiration indicator.
- Confirmation modal.

The Approve button must never be placed next to an ambiguous or hidden action description.

## S13 — Activity History

**Purpose:** Show what JARVIS has actually done.

### Layout

1. Activity heading.
2. Date filter.
3. Service filter.
4. Status filter.
5. Activity timeline.
6. Activity detail.

**Primary action:** View Activity.

**Components:**
- Activity item.
- Service icon.
- Execution status.
- Timestamp.
- Detail drawer.
- Retry action where safe.

## S14 — Integrations

**Purpose:** Connect and monitor external services.

### Layout

1. Integration overview.
2. Connection status.
3. Email Manager card.
4. Fitness Manager card.
5. Google Calendar card.
6. AI provider configuration.
7. Reconnect actions.
8. Connection diagnostics.

**Primary action:** Connect or Repair Integration.

**Components:**
- Integration card.
- Connection badge.
- Health indicator.
- OAuth connect button.
- Configuration form.
- Retry button.
- Error details.

## S15 — Settings

**Purpose:** Configure the assistant's behavior.

### Sections

1. General.
2. AI provider.
3. Voice and speech.
4. Memory.
5. Notifications.
6. Permissions.
7. Automation.
8. Privacy and security.
9. Appearance.
10. About.

**Primary action:** Save Changes.

**Components:**
- Settings navigation.
- Toggle.
- Select.
- Input.
- Permission matrix.
- Save button.
- Reset confirmation.

---

# 7. Reusable Component Library

Every component should have a consistent visual language and documented states.

## 7.1 Navigation components

### Sidebar
Variants:
- Expanded.
- Collapsed.
- Mobile drawer.

States:
- Default.
- Hover.
- Active.
- Disabled.

### Navigation Item
Variants:
- Standard.
- With icon.
- With count.
- With status indicator.

### Topbar
Contains:
- Logo.
- Search.
- Notification control.
- Profile menu.

## 7.2 AI components

### JARVIS Presence Indicator

Variants:
- Idle.
- Listening.
- Thinking.
- Speaking.
- Executing.
- Waiting.
- Error.
- Offline.

### Command Composer

Variants:
- Text input.
- Voice enabled.
- Multiline.
- Disabled.

States:
- Empty.
- Focused.
- Typing.
- Submitting.
- Error.

### Message Bubble

Variants:
- User.
- Assistant.
- System.
- Tool result.

### AI Response Card

Variants:
- Text.
- Summary.
- Recommendation.
- Structured data.
- Action proposal.

### Tool Activity Card

States:
- Waiting.
- Running.
- Completed.
- Failed.
- Cancelled.

## 7.3 Productivity components

### Task Card
Variants:
- Compact.
- Standard.
- Detailed.

States:
- Pending.
- In progress.
- Completed.
- Overdue.
- Disabled.

### Routine Card
Variants:
- Upcoming.
- Completed.
- Missed.
- Paused.

### Schedule Event Card
Variants:
- Calendar event.
- Task.
- Routine.
- Suggested activity.

### Progress Indicator
Variants:
- Linear.
- Circular.
- Percentage.

Use only when the underlying data supports meaningful progress.

## 7.4 Integration components

### Integration Card
Variants:
- Connected.
- Disconnected.
- Connecting.
- Error.
- Not configured.

### Status Badge
Variants:
- Success.
- Warning.
- Error.
- Information.
- Neutral.

### Health Indicator
Displays:
- Service name.
- Connection status.
- Last successful check.
- Last error, if present.

## 7.5 Approval components

### Approval Card
Variants:
- Low risk.
- Medium risk.
- High risk.

States:
- Pending.
- Approved.
- Rejected.
- Expired.
- Executing.
- Completed.
- Failed.

### Confirmation Dialog
Variants:
- Standard confirmation.
- Destructive confirmation.
- External action approval.

### Permission Toggle
States:
- Enabled.
- Disabled.
- Pending update.
- Error.

## 7.6 Feedback components

- Toast notification.
- Inline alert.
- Error banner.
- Empty-state illustration.
- Skeleton loader.
- Modal.
- Drawer.
- Tooltip.
- Dropdown.
- Search field.
- Date picker.
- Tabs.
- Pagination.
- Filter chip.
- Checkbox.
- Toggle.
- Button.
- Icon button.

## 7.7 Button system

| Variant | Usage |
|---|---|
| Primary | Main action, cyan background |
| Secondary | Supporting action |
| Outline | Less prominent action |
| Ghost | Navigation and low-emphasis action |
| Danger | Destructive action |
| Success | Confirm completion, when appropriate |

Sizes:
- Small: 32px.
- Medium: 40px.
- Large: 48px.

All interactive controls should provide hover, focus, pressed, disabled and loading states.

---

# 8. Screen States

Every key screen must be designed for more than its successful data-loaded state.

## 8.1 State definitions

| State | Design requirement |
|---|---|
| Empty | Explain why no information is available and provide a useful next action |
| Loading | Use skeletons for data regions and progress indicators for operations |
| Error | Explain what failed and provide a recovery action |
| Success | Confirm what changed and show updated information |
| Offline | Clearly distinguish unavailable services from empty data |

## 8.2 Screen-by-screen state matrix

| Screen | Empty | Loading | Error | Success | Offline |
|---|---|---|---|---|---|
| Setup | No integrations connected | Setup progress | Connection failed | Setup complete | Network unavailable |
| Dashboard | No activity yet | Dashboard skeleton | Partial data error | Updated dashboard | Cached data and status |
| AI Assistant | Suggested prompts | Thinking indicator | AI error | Response displayed | Text limitations explained |
| My Day | No plan created | Plan generation | Planning failed | Plan generated | Last saved plan |
| Tasks | No tasks | Task skeleton | Save failed | Task updated | Local cached list, read-only if needed |
| Routines | No routines | Routine skeleton | Load failed | Routine saved | Last synced routines |
| Calendar | No events | Calendar skeleton | Calendar error | Event created | Last synchronized events |
| Email | No emails available | Email skeleton | Email service error | Emails loaded or action confirmed | Email unavailable |
| Fitness | No workouts recorded | Fitness skeleton | Fitness service error | Data loaded | Last synced data |
| Notifications | No notifications | Loading list | Load failed | Notification marked read | Cached notifications |
| Memory | No saved memories | Memory skeleton | Retrieval failed | Memory updated | Cached read-only view |
| Approvals | No pending approvals | Approval skeleton | Approval service error | Action completed | Approval execution unavailable |
| Activity History | No activity recorded | History skeleton | Load failed | Activity recorded | Cached history |
| Integrations | No integrations connected | Connection check | Authentication or API failure | Connected | Service unreachable |
| Settings | Default preferences | Saving indicator | Save failed | Settings saved | Disable unsupported updates |

## 8.3 Important state rules

- Never show an empty screen when data loading has not finished.
- Never display stale information as live information.
- Always show when cached data was last updated.
- Do not show success before backend confirmation.
- Failed external operations must remain visible in Activity History.
- Retry actions should be safe and avoid duplicate execution.

---

# 9. Responsive Behaviour

JARVIS is desktop-first because planning, reviewing information and managing integrations require screen space.

However, mobile should be treated as a first-class interaction environment, not simply a compressed desktop layout.

## 9.1 Breakpoints

| Device | Width | Layout |
|---|---|---|
| Mobile | 320–767px | Single column |
| Tablet | 768–1023px | Compact sidebar or drawer |
| Desktop | 1024–1439px | Standard dashboard |
| Large desktop | 1440px+ | Expanded dashboard |

## 9.2 Desktop behaviour

- Persistent sidebar.
- Two-column dashboard.
- Full calendar views.
- Side-by-side email list and detail.
- Large AI conversation area.
- Approval details visible without excessive scrolling.
- Keyboard shortcuts.

Recommended content maximum width: approximately 1600px.

## 9.3 Tablet behaviour

- Collapsible navigation.
- Two-column layout only when space permits.
- Calendar defaults to week or agenda.
- Email detail opens as a separate panel.
- Dashboard cards rearrange into a responsive grid.
- Approval cards use a single-column layout.

## 9.4 Mobile behaviour

Navigation:
- Replace desktop sidebar with a mobile navigation drawer.
- Provide a persistent bottom navigation for the most frequently used destinations.
- Recommended destinations: Home, Assistant, My Day, Tasks and More.

Dashboard:
- Single-column layout.
- AI command panel near the top.
- Important approvals visible immediately.
- Compact schedule and task cards.

AI Assistant:
- Full-screen conversation.
- Composer fixed to the bottom with safe-area spacing.
- Prominent microphone button.
- Voice input should not obscure the text input.

Calendar:
- Agenda-first presentation.
- Day and week views optimized for mobile.
- Avoid forcing a dense month grid.

Email:
- List-first navigation.
- Email details open full-screen.
- Draft editing uses a full-width editor.

Approvals:
- One action per card.
- Full action details before approval.
- Large approve and reject controls.
- Destructive actions require an additional confirmation.

Mobile interaction sizes:
- Minimum touch target: 44 × 44px.
- Important buttons: preferably 48px high.
- Avoid hover-only interactions.

---

# 10. Accessibility

Target: **WCAG 2.2 Level AA**.

Accessibility must be part of component implementation, not a final visual audit.

## 10.1 Contrast requirements

Minimum contrast:

- Normal text: 4.5:1.
- Large text: 3:1.
- UI components and meaningful graphical indicators: 3:1 against adjacent colors.

The proposed text palette is designed for strong contrast against the dark background.

The final implementation must validate every foreground/background pairing, including hover, disabled and selected states.

Do not assume that a color is accessible simply because it is bright.

## 10.2 Keyboard navigation

Every interactive feature must be keyboard accessible.

Required support:

| Key | Expected action |
|---|---|
| Tab | Move to next interactive element |
| Shift + Tab | Move to previous element |
| Enter | Activate focused control |
| Space | Activate buttons and checkboxes |
| Escape | Close dialog, menu or drawer |
| Arrow keys | Navigate menus, tabs and calendar grids where appropriate |
| Ctrl/Cmd + K | Open command palette |
| Ctrl/Cmd + Enter | Submit supported composer forms |

Shortcuts must not interfere with normal text entry.

## 10.3 Focus management

- Use visible focus indicators.
- Maintain logical focus order.
- Move focus into an opened modal.
- Return focus to the triggering control when a modal closes.
- Trap focus inside modal dialogs.
- Never remove keyboard focus outlines without replacement.
- Do not automatically move focus during background updates.

## 10.4 ARIA requirements

Use semantic HTML first.

Required patterns:

- Navigation landmarks for navigation regions.
- Main landmark for primary content.
- Proper heading hierarchy.
- Accessible labels for all inputs.
- `aria-expanded` for expandable controls.
- `aria-current` for active navigation.
- `aria-live="polite"` for non-urgent status updates.
- `role="alert"` for important errors.
- Accessible dialog labels and descriptions.
- Accessible names for icon-only buttons.
- Descriptive labels for charts.
- Table headers for structured data.

Do not use ARIA attributes when native HTML already provides the required semantics.

## 10.5 Voice accessibility

- Microphone controls must have accessible names.
- Show speech transcription.
- Allow editing before submission when appropriate.
- Provide text alternatives for voice actions.
- Never make voice interaction mandatory.
- Display clear microphone permission errors.

## 10.6 Motion accessibility

- Support `prefers-reduced-motion`.
- Avoid flashing elements.
- Avoid constant movement.
- Provide static alternatives for animated AI states.
- Never communicate information exclusively through animation.

## 10.7 Screen reader considerations

Important status changes should be announced.

Examples:
- "JARVIS is listening."
- "Your task was created."
- "Approval required."
- "Email sending failed."
- "Calendar event created successfully."

Avoid announcing every minor visual update.

---

# Final Design Decisions

## Recommended visual identity

| Area | Decision |
|---|---|
| Design theme | Dark Intelligence |
| Primary accent | Cyan |
| Main background | Graphite |
| Main font | Inter |
| Technical font | JetBrains Mono |
| Component style | Clean, structured, restrained |
| Card style | Subtle borders and controlled elevation |
| Navigation | Persistent desktop sidebar |
| AI presence | Animated state indicator |
| Interaction | Conversational and keyboard-friendly |
| Mobile navigation | Bottom navigation + drawer |
| Accessibility | WCAG 2.2 AA |
| Motion | Minimal and state-driven |

## Design priorities

1. AI Assistant experience.
2. Home Dashboard.
3. Approval Center.
4. My Day.
5. Task Manager.
6. Email Center.
7. Calendar.
8. Remaining management screens.

## Definition of design completion

The design is ready for implementation when:

- All 15 screens are specified.
- Every core journey has a documented flow.
- Design tokens are finalized.
- Reusable components have variants and states.
- Empty, loading, error, success and offline states are specified.
- Mobile, tablet and desktop behaviour is documented.
- Accessibility requirements are accounted for.
- Approval and autonomous execution interactions are unambiguous.
- Designs use consistent navigation and interaction patterns.
- The design can be translated into reusable frontend components without inventing missing behaviour.

**Final design principle:**

JARVIS should feel like an intelligent system working alongside the user, not a collection of disconnected tools. Its interface must make intelligence visible, actions understandable and control effortless.