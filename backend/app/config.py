from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CYBERVAL Platform API"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://cyberval:cyberval@localhost:5433/cyberval"
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:5173"
    nvd_api_url: str = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    nvd_api_key: str | None = None
    cisa_kev_url: str = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    http_timeout_seconds: float = 15.0

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def sync_database_url(self) -> str:
        url = self.database_url.strip()
        # Automatically normalize standard cloud PostgreSQL URLs for psycopg3
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://"):]
        elif url.startswith("postgresql+psycopg2://"):
            url = "postgresql+psycopg://" + url[len("postgresql+psycopg2://"):]
        return url

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

