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
    jwt_expire_minutes: int = 60 * 24

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
    supabase_url: str = "https://hngljslkwyzzlcugiiqz.supabase.co"
    supabase_anon_key: str = "sb_publishable_YTyCF9SfOoh-5TaFLUVxmw_NYk3_jiO"

    @property
    def supabase_project_url(self) -> str:
        raw = (self.supabase_url or "").strip().strip('"').strip("'").rstrip("/")
        lowered = raw.lower()
        if lowered.endswith("/rest/v1"):
            raw = raw[: -len("/rest/v1")]
        return raw.rstrip("/")

    @property
    def pg_url(self) -> str:
        raw_url = (self.database_url or "").strip().strip('"').strip("'")
        normalized = raw_url.lower()

        # Render/Heroku may expose postgres://, while SQLAlchemy expects postgresql://
        if normalized.startswith("postgres://"):
            return "postgresql://" + raw_url[len("postgres://") :]

        # Guard against misconfigured URLs (e.g. service HTTP URL pasted as DATABASE_URL).
        # Fallback to SQLite so the app can still boot in development.
        if normalized.startswith("http://") or normalized.startswith("https://"):
            return "sqlite:///./self_trust.db"

        return raw_url or "sqlite:///./self_trust.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
