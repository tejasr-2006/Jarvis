# JARVIS — Personal AI Assistant

<p align="center">
  <strong>Your Personal AI. One Unified Assistant.</strong>
</p>

<p align="center">
  A modular, AI-powered personal assistant built with Python and FastAPI to help manage everyday activities through intelligent conversations, integrations, automation, and personalized workflows.
</p>

---

## Overview

**JARVIS** is a personal AI assistant designed to bring multiple areas of everyday life into one unified system.

It combines AI-powered reasoning, personal memory, task management, scheduling, voice interaction, and integrations with separate applications to provide a centralized assistant experience.

Instead of building every feature into one tightly coupled application, JARVIS follows a modular architecture. Independent services such as Email Manager and Fitness Manager remain separate applications and communicate with JARVIS through APIs.

The long-term goal is to create an intelligent assistant that can understand requests, maintain useful context, coordinate tools, and help manage personal workflows while respecting user permissions.

## Key Features

### AI Assistant
- Natural-language command understanding.
- AI-powered responses and task assistance.
- Configurable AI provider architecture.
- Tool registration and command routing.
- Unified assistant interface.

### Personal Memory and Context
- Store and manage explicit personal information.
- Maintain bounded conversation context.
- Retrieve relevant information when needed.
- Manage and clear saved memory.
- Import and search personal knowledge documents.

Knowledge search indexes document chunks in local SQLite FTS5, combines BM25 and TF-IDF cosine rankings with reciprocal-rank fusion, and returns source metadata plus neighboring chunk context. The authenticated `GET /knowledge/search` endpoint accepts `q`, `limit`, and optional `source`, `updated_after`, and `updated_before` filters. The read-only `knowledge.search` agent tool uses the same filters and result citations; it is enabled by default and can be disabled through `JARVIS_ENABLED_TOOLS`.

Open the browser-based knowledge library at `/knowledge-library` to add local text documents, filter/search indexed chunks, and manage saved sources. Enter the configured `JARVIS_API_KEY` in the page; the key is kept only in the current browser tab's session storage.

### Productivity and Planning
- Task management.
- Reminders and notifications.
- Recurring routines.
- Daily planning and scheduling.
- Proactive task and schedule notifications.
- Planning assistance.

### Email and Fitness Integration
- Connect to a separate Personal AI Email Manager.
- Retrieve and review high-priority emails.
- Connect to a separate Personal AI Fitness Tracker.
- Retrieve fitness and workout information.

### Calendar and Smart Home
- Optional Google Calendar integration using OAuth.
- Calendar event and scheduling workflows.
- Optional Home Assistant integration.
- Configurable smart-home device access.

### Voice and Interfaces
- Browser-based voice interface.
- Text-based assistant interaction.
- Optional offline wake-phrase recognition.
- Dashboard and mobile web interface.
- Optional desktop application.

### Additional Capabilities
- Personal finance ledger.
- Knowledge management.
- Multimodal document and image analysis.
- Controlled computer interaction.
- Agent execution and feedback workflows.
- Security auditing and operational monitoring.

> Feature availability depends on configuration, optional dependencies, connected services, and the implementation of individual modules. JARVIS does not grant an AI model unrestricted permission to execute actions.

---

## Architecture

JARVIS uses a modular architecture with a central FastAPI application coordinating independent components and external services.

```text
                    USER
                      |
          +-----------+-----------+
          |           |           |
       Dashboard    Mobile       Voice
          |           |           |
          +-----------+-----------+
                      |
                      v
              JARVIS BACKEND
                 FastAPI
                 Port 8000
                      |
          +-----------+-----------+
          |           |           |
       AI Engine   Agent System  Tool Registry
          |           |           |
          +-----------+-----------+
                      |
              Core Application
                      |
       +--------------+--------------+
       |              |              |
     Memory         Planner        Tasks
       |              |              |
    Knowledge       Routines      Reminders
       |              |              |
       +--------------+--------------+
                      |
              INTEGRATION LAYER
                      |
       +--------------+--------------+
       |              |              |
   Email Manager  Fitness Manager  Calendar
     :8001           :8002          Google
       |
   Home Assistant and other optional services
```

### Architecture Principles

- **Modularity:** Keep independent application domains separated.
- **API-first integration:** Communicate with external applications through defined APIs.
- **Centralized orchestration:** Use JARVIS to coordinate tools and workflows.
- **Permission-based execution:** Validate actions and enforce approval requirements.
- **Local-first personal data:** Use local storage for supported personal features.
- **Extensibility:** Allow new tools, integrations, and modules to be added independently.

See [the JARVIS 2.0 architecture audit and implementation roadmap](docs/JARVIS_2_0_ROADMAP.md) for verified implementation boundaries and prioritized engineering work.

### Technology Stack

| Component | Technology |
|---|---|
| Backend | Python |
| API framework | FastAPI |
| ASGI server | Uvicorn |
| AI integration | Google Gemini |
| Optional local AI | Ollama |
| HTTP communication | HTTPX |
| Data storage | SQLite |
| Configuration | Environment variables / dotenv |
| API documentation | OpenAPI / Swagger UI |
| Frontend | HTML, CSS, JavaScript |
| Voice | Browser speech capabilities and optional Vosk |
| Testing | Pytest |

---

## Project Structure

```text
Jarvis/
│
├── app/
│   ├── agent/              # Agent orchestration and execution
│   ├── api/                # FastAPI route modules
│   ├── calendar/           # Calendar integration
│   ├── computer/           # Controlled computer actions
│   ├── email_assistant/    # Email assistance workflows
│   ├── finance/            # Personal finance features
│   ├── integrations/       # External service clients
│   ├── knowledge/          # Knowledge management
│   ├── memory/             # Personal memory
│   ├── planner/            # Planning functionality
│   ├── reminders/          # Reminder and notification storage
│   ├── scheduling/         # Scheduling functionality
│   ├── security_ops/       # Security monitoring and auditing
│   ├── services/           # Core application services
│   ├── static/             # Web interfaces and frontend assets
│   ├── tasks/              # Task management
│   ├── tools/              # Assistant tools
│   ├── voice/              # Voice functionality
│   │
│   ├── config.py           # Application configuration
│   ├── main.py             # FastAPI application entry point
│   └── desktop.py          # Desktop application entry point
│
├── docs/                   # Product and design documentation
├── tests/                  # Automated tests
│
├── requirements.txt
├── requirements-calendar.txt
├── requirements-desktop.txt
├── requirements-voice.txt
├── .env.example
├── .gitignore
└── Run-JARVIS-Desktop.bat
```

---

## Getting Started

### Prerequisites

- Python installed on your system.
- Git.
- A Google Gemini API key if using Gemini.
- Optional external applications and credentials for integrations.

Use a Python version compatible with the project's installed dependencies.

### 1. Clone the Repository

```bash
git clone https://github.com/tejasr-2006/Jarvis.git
```

Navigate into the project:

```bash
cd Jarvis
```

### 2. Create a Virtual Environment

**Windows PowerShell:**

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Install optional dependencies only when required:

```powershell
pip install -r requirements-calendar.txt
```

```powershell
pip install -r requirements-desktop.txt
```

```powershell
pip install -r requirements-voice.txt
```

### 4. Configure Environment Variables

Create your local environment file:

```powershell
Copy-Item .env.example .env
```

Open `.env` and configure the credentials and settings required by the features you want to use.

For example:

```env
GEMINI_API_KEY=your_gemini_api_key

EMAIL_MANAGER_BASE_URL=http://127.0.0.1:8001
FITNESS_MANAGER_BASE_URL=http://127.0.0.1:8002

EMAIL_MANAGER_API_KEY=
JARVIS_API_KEY=

JARVIS_DATA_DIR=~/.jarvis
```

These are configuration examples. Check `.env.example` and `app/config.py` for the actual supported variables and defaults.

**Never commit your real `.env` file or API keys to GitHub.**

### 5. Run JARVIS

Start the backend from the repository root:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

JARVIS should be accessible at:

| Resource | URL |
|---|---|
| Main application | http://127.0.0.1:8000 |
| API documentation | http://127.0.0.1:8000/docs |
| Dashboard | http://127.0.0.1:8000/dashboard |
| Voice interface | http://127.0.0.1:8000/voice |
| Mobile interface | http://127.0.0.1:8000/mobile |
| Workspace | http://127.0.0.1:8000/workspace |

Actual routes depend on the current application configuration.

---

## Integrating Other Applications

JARVIS is designed to coordinate independent applications rather than replace them.

### Personal AI Email Manager

Repository:

https://github.com/tejasr-2006/personal-ai-email-manager

The Email Manager remains an independent application.

JARVIS communicates with it through its integration client.

Default development URL:

```text
http://127.0.0.1:8001
```

### Personal AI Fitness Tracker

Repository:

https://github.com/tejasr-2006/Personal-AI-Fitness-Tracker

The Fitness Manager remains an independent application.

JARVIS communicates with it through its integration client.

Default development URL:

```text
http://127.0.0.1:8002
```

### Integration Setup

1. Start the Email Manager independently.
2. Start the Fitness Manager independently.
3. Configure their base URLs and required credentials in JARVIS `.env`.
4. Start JARVIS.
5. Verify integration health through the available integration endpoints.

Optional integrations such as Google Calendar and Home Assistant require their own setup and authorization.

---

## Testing

Run the automated test suite from the project root:

```powershell
python -m pytest -q
```

For more detailed output:

```powershell
python -m pytest -v
```

Integration tests may require the corresponding external services and configuration.

---

## Security and Privacy

JARVIS is designed around controlled access to personal information and application capabilities.

Important security practices:

- Keep API keys and credentials in `.env`.
- Never commit OAuth tokens or private credentials.
- Use explicit tool allow-lists.
- Validate AI-generated data before using it.
- Require appropriate authorization for sensitive actions.
- Keep personal runtime data outside source control.
- Restrict access when exposing JARVIS beyond localhost.
- Use HTTPS and appropriate authentication for remote access.
- Review logs and backups for sensitive personal information.

**Important:** Local storage does not automatically mean encrypted storage. SQLite databases, backups, uploaded files, and other personal data should be protected through appropriate operating-system permissions and backup security.

Do not expose the development server directly to the public internet.

---

## Background Services

Some JARVIS capabilities depend on background processes running inside the application.

Examples include:

- Reminder checks.
- Scheduled routine notifications.
- Monitoring and proactive workflows.

Keep the backend running for these processes to operate.

The documented architecture recommends using a single Uvicorn worker for in-process background schedulers to avoid duplicate execution.

---

## Documentation

Additional project documentation is available in the `docs/` directory.

- `docs/JARVIS_PRD.md` — Product requirements and intended functionality.
- `docs/JARVIS_DESIGN_BRIEF.md` — Product design direction and interface requirements.
- `JARVIS_MASTER_REFERENCE.md` — Consolidated architecture, feature, integration, and implementation reference.

---

## Development Philosophy

JARVIS is being developed with the following goals:

1. Build a reliable personal AI assistant.
2. Keep independent applications modular.
3. Centralize reasoning and orchestration.
4. Make integrations reusable and maintainable.
5. Protect personal data and credentials.
6. Keep important actions permission-based.
7. Improve the assistant incrementally through testing and feedback.

---

## Roadmap

The broader project direction includes:

- More capable AI agent orchestration.
- Better long-term memory and personalization.
- Unified email, fitness, finance, and productivity workflows.
- Improved voice conversations and wake-word interaction.
- More advanced daily planning and proactive assistance.
- Expanded integrations and controlled computer interaction.
- Better mobile and desktop experiences.
- Stronger security, reliability, and observability.

Roadmap items are development goals and should not be interpreted as guarantees that every capability is already complete.

---

## Contributing

This is a personal AI assistant project currently under active development.

For changes and improvements:

1. Create a branch for your changes.
2. Keep modules independent where possible.
3. Follow existing project conventions.
4. Add or update tests.
5. Never include credentials or personal runtime data.
6. Verify that integrations continue to work.

---

## License

No license has been specified yet. Unless a license is added to this repository, standard copyright restrictions apply.

---

<p align="center">
  <strong>JARVIS</strong><br>
  Your Personal AI Assistant.
</p>
