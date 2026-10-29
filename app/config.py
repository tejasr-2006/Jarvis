
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "JARVIS")
    APP_ENV: str = os.getenv("APP_ENV", "development")

    EMAIL_MANAGER_BASE_URL: str = os.getenv(
        "EMAIL_MANAGER_BASE_URL", "http://127.0.0.1:8001"
    )
    FITNESS_MANAGER_BASE_URL: str = os.getenv(
        "FITNESS_MANAGER_BASE_URL", "http://127.0.0.1:8002"
    )
    EMAIL_MANAGER_API_KEY: str = os.getenv("EMAIL_MANAGER_API_KEY", "")


settings = Settings()
