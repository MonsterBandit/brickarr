from __future__ import annotations

import os
from pathlib import Path
from typing import Literal, Mapping, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

_PREFIX = "BRICKARR_"
_FILE_SUFFIX = "_FILE"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix=_PREFIX, case_sensitive=False, extra="ignore")

    # Set from the image's BRICKARR_VERSION build argument; shown by /system/status.
    version: str = "0.0.0-dev"

    db_type: Literal["sqlite", "mariadb"] = "sqlite"
    # MariaDB only; SQLite keeps its file in the config dir.
    db_host: str = "mariadb"
    db_port: int = 3306
    db_name: str = "brickarr"
    db_user: str = "brickarr"
    db_password: str = ""

    config_dir: Path = Field(default=Path("/config"))
    # The user's own files. Re-downloadable files go to cache_dir, which defaults
    # to the library so one mount is enough (BRK-15).
    library_dir: Path = Field(default=Path("/library"))
    cache_dir: Optional[Path] = None

    session_secret: str = "change-me"
    session_cookie_name: str = "brickarr_session"
    session_max_age_seconds: int = 60 * 60 * 24 * 30

    api_v1_prefix: str = "/api/v1"

    @field_validator("db_type", mode="before")
    @classmethod
    def _db_type_lower(cls, v):
        return v.strip().lower() if isinstance(v, str) else v

    @field_validator("cache_dir", mode="before")
    @classmethod
    def _blank_cache_dir(cls, v):
        return None if isinstance(v, str) and not v.strip() else v

    @model_validator(mode="after")
    def _cache_defaults_to_library(self) -> "Settings":
        if self.cache_dir is None:
            self.cache_dir = self.library_dir
        return self

    @property
    def sqlite_path(self) -> Path:
        return self.config_dir / "brickarr.db"

    @property
    def db_url(self) -> URL:
        if self.db_type == "sqlite":
            return URL.create("sqlite+pysqlite", database=str(self.sqlite_path))
        return URL.create(
            "mysql+pymysql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"charset": "utf8mb4"},
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


def secrets_from_files(environ: Mapping[str, str]) -> dict[str, str]:
    """Read every BRICKARR_<NAME>_FILE into the setting BRICKARR_<NAME>.

    LinuxServer's FILE__ idea in Brickarr's naming, so Docker secrets work.
    One trailing newline is trimmed. Setting both forms of a name is refused.
    """
    present = {k.upper() for k, v in environ.items() if v is not None}
    out: dict[str, str] = {}
    for key, path in environ.items():
        upper = key.upper()
        if not (upper.startswith(_PREFIX) and upper.endswith(_FILE_SUFFIX)):
            continue
        name = upper[len(_PREFIX):-len(_FILE_SUFFIX)]
        if not name:
            continue
        if _PREFIX + name in present:
            raise RuntimeError(f"Both {_PREFIX}{name} and {key} are set; set only one of them")
        value = Path(path).read_text(encoding="utf-8")
        if value.endswith("\r\n"):
            value = value[:-2]
        elif value.endswith("\n"):
            value = value[:-1]
        out[name.lower()] = value
    return out


settings = Settings(**secrets_from_files(os.environ))
