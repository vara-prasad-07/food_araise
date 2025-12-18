from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # API Keys
    GOOGLE_API_KEY: str = ""
    SERPAPI_API_KEY: str = ""
    SERPAPI_MIN_INTERVAL: float = 1.0  # seconds between requests
    SERPAPI_MAX_RETRIES: int = 2
    SERPAPI_BACKOFF_FACTOR: float = 1.5

    # Application Settings
    APP_NAME: str = "Food Agent Server"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # AI Model Configuration
    # Prioritized list based on research (Nov 2025 availability)
    GEMINI_MODELS: List[str] = [
        "gemini-2.0-flash-exp"
    ]


settings = Settings()