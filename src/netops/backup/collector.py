"""Pull running configuration and strip volatile lines.

Devices print timestamps, byte counts, and clock periods that change on every
read. Those lines are removed before storage so a diff reports real drift, not
noise.
"""

from __future__ import annotations

import re

from ..inventory import Device

# Default show-running command per platform. Override per device in the inventory.
SHOW_RUN = {
    "cisco_ios": "show running-config",
    "cisco_xe": "show running-config",
    "cisco_nxos": "show running-config",
    "arista_eos": "show running-config",
    "juniper_junos": "show configuration | display set",
}

# Lines that change on every read and would create false drift.
VOLATILE = [
    re.compile(r"^Building configuration.*"),
    re.compile(r"^Current configuration : \d+ bytes"),
    re.compile(r"^! Last configuration change.*"),
    re.compile(r"^! NVRAM config last updated.*"),
    re.compile(r"^ntp clock-period \d+"),
    re.compile(r"^!Time:.*"),
    re.compile(r"^!Running configuration last done.*"),
]


def normalize(config: str) -> str:
    kept = [
        line.rstrip()
        for line in config.splitlines()
        if not any(pattern.match(line) for pattern in VOLATILE)
    ]
    return "\n".join(kept) + "\n"


def fetch_running_config(device: Device) -> str:
    from ..connections import connect

    command = device.running_config_command or SHOW_RUN.get(device.platform, "show running-config")
    with connect(device) as conn:
        raw = conn.send_command(command, read_timeout=120)
    return normalize(raw)
