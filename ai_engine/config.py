"""
Configuration settings for AI Engine
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings"""

    # API Keys
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@postgres:5432/website_builder"
    )

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    REDIS_ENABLED: bool = True

    # External Services
    PLAYWRIGHT_SERVICE_URL: str = os.getenv(
        "PLAYWRIGHT_SERVICE_URL",
        "http://playwright:3001"
    )
    TOPMATE_API_URL: str = os.getenv(
        "TOPMATE_API_URL",
        "https://api.topmate.io"
    )
    GALACTUS_API_URL: str = os.getenv(
        "GALACTUS_API_URL",
        "https://gcp.galactus.run/fetchByUsername/"
    )

    # Chat Settings
    CHAT_MAX_HISTORY: int = 20  # Maximum conversation turns to keep

    # Feature Flags
    USE_SDK_AGENTS: bool = os.getenv("USE_SDK_AGENTS", "false").lower() == "true"

    # Monitoring
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    SENTRY_ENVIRONMENT: str = os.getenv("SENTRY_ENVIRONMENT", "development")
    SENTRY_TRACES_SAMPLE_RATE: float = float(
        os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")
    )

    # Claude Models
    CLAUDE_MODEL_SONNET: str = "claude-sonnet-4-20250514"
    CLAUDE_MODEL_OPUS: str = "claude-opus-4-20250514"
    CLAUDE_MODEL_HAIKU: str = "claude-3-5-haiku-20241022"

    # Default Claude Model (change this to switch models easily)
    DEFAULT_CLAUDE_MODEL: str = os.getenv("DEFAULT_CLAUDE_MODEL", "claude-opus-4-20250514")

    # Gemini Models
    GEMINI_MODEL_FLASH: str = "gemini-1.5-flash"
    GEMINI_MODEL_PRO: str = "gemini-1.5-pro"

    # Generation Settings
    MAX_TOKENS: int = 8192
    TEMPERATURE: float = 0.7
    MAX_ITERATIONS: int = 5  # For autonomous agents

    # File paths
    GENERATED_WEBSITES_DIR: str = "/app/generated_websites"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_redis_client():
    """Get Redis client with error handling"""
    if not settings.REDIS_ENABLED:
        return None

    try:
        import redis
        client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        # Test connection
        client.ping()
        return client
    except Exception as e:
        print(f"Redis connection failed: {e}. Continuing without cache.")
        settings.REDIS_ENABLED = False
        return None
