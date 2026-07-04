"""Inventory model and loader.

The inventory is a single YAML file, validated on load. A device carries only the
data needed to reach it. Passwords come from settings, not from this file.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class Device(BaseModel):
    name: str
    host: str
    platform: str  # a Netmiko device_type, e.g. cisco_ios, cisco_nxos, arista_eos
    port: int = 22
    username: str | None = None  # optional per-device override of the default
    groups: list[str] = Field(default_factory=list)
    running_config_command: str | None = None  # override the default show run command


class Inventory(BaseModel):
    devices: list[Device]

    def in_group(self, group: str) -> list[Device]:
        return [d for d in self.devices if group in d.groups]


def load_inventory(path: str | Path) -> Inventory:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"inventory not found at {path}")
    data = yaml.safe_load(path.read_text())
    return Inventory(**data)
