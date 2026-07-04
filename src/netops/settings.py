"""Runtime settings loaded from environment variables and an optional .env file.

Credentials never live in the inventory or in the repository. They are read from
the environment with the NETOPS_ prefix, for example NETOPS_PASSWORD.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="NETOPS_", extra="ignore")

    # Device access
    username: str = ""
    password: str = ""
    secret: str = ""  # enable secret, left empty when not used

    # Inventory and local storage
    inventory_path: Path = Path("inventory/devices.yaml")
    config_store: Path = Path("data/configs")

    # Config backup git target (a dedicated repo, separate from this toolkit)
    git_remote: str = ""
    git_branch: str = "main"
    git_author_name: str = "netops-automation"
    git_author_email: str = "netops-automation@localhost"

    # NetBox source of truth
    netbox_url: str = ""
    netbox_token: str = ""

    # Behaviour
    max_workers: int = 8
    log_level: str = "INFO"


settings = Settings()
