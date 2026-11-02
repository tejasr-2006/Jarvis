import os
from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "JARVIS")
    APP_ENV: str = os.getenv("APP_ENV", "development")

    # Existing service URLs are preserved.
    EMAIL_MANAGER_BASE_URL: str = os.getenv(
        "EMAIL_MANAGER_BASE_URL", "http://127.0.0.1:8001"
    )
    FITNESS_MANAGER_BASE_URL: str = os.getenv(
        "FITNESS_MANAGER_BASE_URL", "http://127.0.0.1:8002"
    )
    EMAIL_MANAGER_API_KEY: str = os.getenv("EMAIL_MANAGER_API_KEY", "")

    # AI provider abstraction: "gemini" or "ollama".
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "gemini").strip().lower()
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    OLLAMA_BASE_URL: str = os.getenv(
        "OLLAMA_BASE_URL", "http://127.0.0.1:11434"
    ).rstrip("/")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    AI_TIMEOUT_SECONDS: float = float(os.getenv("AI_TIMEOUT_SECONDS", "30"))

    # Phase 2 memory: local SQLite only. Memory endpoints require an API key.
    JARVIS_API_KEY: str = os.getenv("JARVIS_API_KEY", "")
    JARVIS_DATA_DIR: str = os.path.expanduser(
        os.getenv("JARVIS_DATA_DIR", "~/.jarvis")
    )
    MEMORY_STORE_CONVERSATIONS: bool = _env_bool(
        "MEMORY_STORE_CONVERSATIONS", False
    )
    MEMORY_CONTEXT_TO_CLOUD: bool = _env_bool("MEMORY_CONTEXT_TO_CLOUD", False)
    JARVIS_ENABLED_TOOLS: set[str] = {
        item.strip() for item in os.getenv(
            "JARVIS_ENABLED_TOOLS",
            "email.high_priority.read,fitness.workouts.read,knowledge.search"
        ).split(",") if item.strip()
    }
    # Fitness Manager server-to-server login. Never expose these to the frontend.
    FITNESS_MANAGER_EMAIL: str = os.getenv("FITNESS_MANAGER_EMAIL", "")
    FITNESS_MANAGER_PASSWORD: str = os.getenv("FITNESS_MANAGER_PASSWORD", "")
    # Retained temporarily for backwards compatibility with older integrations.
    FITNESS_MANAGER_API_TOKEN: str = os.getenv("FITNESS_MANAGER_API_TOKEN", "")
    AGENT_TOOL_TIMEOUT_SECONDS: float = float(os.getenv("AGENT_TOOL_TIMEOUT_SECONDS", "20"))
    AGENT_ALLOW_WRITES: bool = _env_bool("AGENT_ALLOW_WRITES", False)

    # Phase 5 background health monitoring; minimum cadence is enforced in code.
    MONITOR_INTERVAL_SECONDS: int = int(os.getenv("MONITOR_INTERVAL_SECONDS", "60"))
    NOTIFY_TASK_DUE_SOON_MINUTES: int = int(os.getenv("NOTIFY_TASK_DUE_SOON_MINUTES", "30"))

    # Phase 10: optional Google Calendar integration (OAuth files stay local).
    GOOGLE_CALENDAR_CREDENTIALS: str = os.path.expanduser(os.getenv(
        "GOOGLE_CALENDAR_CREDENTIALS", "~/.jarvis/google-calendar-credentials.json"
    ))
    GOOGLE_CALENDAR_TOKEN: str = os.path.expanduser(os.getenv(
        "GOOGLE_CALENDAR_TOKEN", "~/.jarvis/google-calendar-token.json"
    ))
    GOOGLE_CALENDAR_ID: str = os.getenv("GOOGLE_CALENDAR_ID", "primary")

    # Phase 18: optional Home Assistant integration. Keep disabled until configured.
    HOME_ASSISTANT_BASE_URL: str = os.getenv("HOME_ASSISTANT_BASE_URL", "").strip().rstrip("/")
    HOME_ASSISTANT_TOKEN: str = os.getenv("HOME_ASSISTANT_TOKEN", "").strip()
    HOME_ASSISTANT_ALLOWED_ENTITIES: set[str] = {
        item.strip() for item in os.getenv("HOME_ASSISTANT_ALLOWED_ENTITIES", "").split(",")
        if item.strip()
    }

    # Phase 21: local conversation context stores command text and brief summaries only.
    CONVERSATION_CONTEXT_ENABLED: bool = _env_bool("CONVERSATION_CONTEXT_ENABLED", True)
    CONVERSATION_CONTEXT_TURNS: int = int(os.getenv("CONVERSATION_CONTEXT_TURNS", "8"))



settings = Settings()
