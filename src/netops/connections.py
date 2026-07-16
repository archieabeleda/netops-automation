"""Netmiko connection handling.

A single context manager opens a session, enters enable mode when a secret is
set, and always disconnects. Every tool goes through this so connection logic
lives in one place.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator

from netmiko import BaseConnection, ConnectHandler

from .inventory import Device
from .settings import settings

log = logging.getLogger(__name__)


@contextmanager
def connect(device: Device) -> Iterator[BaseConnection]:
    params = {
        "device_type": device.platform,
        "host": device.host,
        "port": device.port,
        "username": device.username or settings.username,
        "password": settings.password,
        "secret": settings.secret,
        "fast_cli": False,
        # Host key checking. Both flags follow the same setting: load
        # known_hosts and reject an unknown or changed key when it is on.
        "system_host_keys": settings.strict_host_key,
        "ssh_strict": settings.strict_host_key,
    }
    log.debug("connecting to %s (%s)", device.name, device.host)
    conn = ConnectHandler(**params)
    try:
        if settings.secret:
            try:
                conn.enable()
            except Exception as exc:  # not every platform uses enable
                log.debug("enable not applied on %s: %s", device.name, exc)
        yield conn
    finally:
        conn.disconnect()
