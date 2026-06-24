from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BRICKARR_", case_sensitive=False, extra="ignore")

    db_host: str = "mariadb"
    db_port: int = 3306
    db_name: str = "brickarr"
    db_user: str = "brickarr"
    db_password: str = ""

    redis_url: str = "redis://redis:6379/0"

    config_dir: Path = Field(default=Path("/config"))
    storage_dir: Path = Field(default=Path("/storage"))

    session_secret: str = "change-me"
    session_cookie_name: str = "brickarr_session"
    session_max_age_seconds: int = 60 * 60 * 24 * 30

    api_v1_prefix: str = "/api/v1"

    @property
    def db_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

    @property
    def secret_key_path(self) -> Path:
        return self.config_dir / "secret.key"

    @property
    def initial_api_key_path(self) -> Path:
        return self.config_dir / "initial_api_key.txt"

    @property
    def logs_dir(self) -> Path:
        return self.config_dir / "logs"


settings = Settings()
