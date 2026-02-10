from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LEXIMA_DMS_",
        env_file=".env",
        extra="ignore",
    )

    data_dir: Path = Path("./data")

    jwt_secret: str = "dev-secret"
    jwt_alg: str = "HS256"
    jwt_expires_minutes: int = 12 * 60

    # LDAP/AD DS
    ldap_enabled: bool = False
    ldap_url: str = "ldap://dc.example.com"
    ldap_base_dn: str = "DC=example,DC=com"
    ldap_bind_dn: str = ""
    ldap_bind_password: str = ""
    ldap_user_search_filter: str = "(sAMAccountName={username})"
    ldap_user_dn_template: str = ""  # для direct bind: "{username}@domain.local"
    ldap_default_role: str = "author"

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "files").mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s

