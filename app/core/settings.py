from enum import Enum
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic.config import Extra
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()

BASE_DIR = Path(__file__).parent.parent


class APISettings(BaseModel):
    """API configuration settings."""

    title: str
    description: str
    version: str
    port: int = Field(ge=1, le=65535)


class LogLevel(str, Enum):
    """Logging level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    ERROR = "ERROR"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class LoggerSettings(BaseModel):
    """Logger configuration settings."""

    level: LogLevel


class DatabaseSettings(BaseModel):
    """Database configuration settings."""

    host: str
    port: int = Field(ge=1, le=65535)
    user: str
    password: str
    name: str
    pool_size: int = Field(gt=0)
    max_overflow: int = Field(ge=0)

    @property
    def url(self) -> str:
        """Async PostgreSQL database URL."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def sync_url(self) -> str:
        """Sync PostgreSQL database URL for Alembic."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class AuthSettings(BaseModel):
    """JWT settings. Accounts live in the database; there is no registration."""

    jwt_secret: str = Field(min_length=16)
    access_ttl_seconds: int = Field(default=900, gt=0)
    refresh_ttl_seconds: int = Field(default=60 * 60 * 24 * 7, gt=0)


class S3Settings(BaseModel):
    """S3-compatible object storage settings."""

    endpoint_url: str
    access_key: str
    secret_key: str
    bucket: str
    region: str
    presigned_ttl: int = Field(ge=60)


class Settings(BaseSettings):
    """Application settings."""

    api: APISettings
    logger: LoggerSettings
    database: DatabaseSettings
    s3: S3Settings
    auth: AuthSettings

    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env"),
        env_nested_delimiter="__",
        env_prefix="",
        case_sensitive=False,
        extra=Extra.ignore,
    )


settings = Settings()  # type: ignore[call-arg]
