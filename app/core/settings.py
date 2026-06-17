from enum import Enum
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()

BASE_DIR = Path(__file__).parent.parent


class APISettings(BaseModel):
    """API configuration settings."""

    title: str = "BE Answer Hub API"
    description: str = "API for BE Answer Hub"
    version: str = "0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)


class LogLevel(str, Enum):
    """Logging level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    ERROR = "ERROR"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class LoggerSettings(BaseModel):
    """Logger configuration settings."""

    level: LogLevel = LogLevel.INFO


class DatabaseSettings(BaseModel):
    """Database configuration settings."""

    host: str = "localhost"
    port: int = Field(default=5432, ge=1, le=65535)
    user: str = "postgres"
    password: str = "postgres"
    name: str = "answer_hub"
    pool_size: int = Field(default=20, gt=0)
    max_overflow: int = Field(default=10, ge=0)

    @property
    def url(self) -> str:
        """Async PostgreSQL database URL."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class Settings(BaseSettings):
    """Application settings."""

    api: APISettings = APISettings()
    logger: LoggerSettings = LoggerSettings()
    database: DatabaseSettings = DatabaseSettings()

    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env"),
        env_nested_delimiter="__",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()  # type: ignore[call-arg]
