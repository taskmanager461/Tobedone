from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Task Manager API"
    app_version: str = "3.0.0"
    api_prefix: str = ""

    database_url: str = "sqlite:///./self_trust.db"
    environment: str = "development"

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 30

    email_provider: str = "smtp"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_user: str = ""
    email_password: str = ""
    smtp_from_email: str = ""
    smtp_enabled: bool = False

    cors_origins: str = "*"
    frontend_base_url: str = "http://localhost:8501"

    @property
    def pg_url(self) -> str:
        # Handle Render/Heroku 'postgres://' vs SQLAlchemy 'postgresql://'
        if not self.database_url or self.database_url.startswith("http"):
            return "sqlite:///./self_trust.db"
        
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql://", 1)
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
