"""Discover live IP and MAC allocations and sync them to NetBox.

Discovery reads the ARP table from each device and returns structured rows.
Syncing is a preview by default and prints what it found. It writes to NetBox
only when apply is True. NetBox url and token come from settings.

The write below records host addresses with a description of where each was
seen. Deeper source-of-truth modeling (interfaces, MAC objects, prefixes) is a
natural next step, noted in the roadmap.
"""

from __future__ import annotations

import logging

from ..connections import connect
from ..inventory import Device, load_inventory
from ..settings import settings

log = logging.getLogger(__name__)


def discover_arp(device: Device) -> list[dict]:
    with connect(device) as conn:
        rows = conn.send_command("show ip arp", use_textfsm=True, read_timeout=120)

    entries: list[dict] = []
    if isinstance(rows, list):
        for row in rows:
            ip = row.get("address") or row.get("ip_address")
            mac = row.get("mac") or row.get("mac_address")
            interface = row.get("interface")
            if ip and mac:
                entries.append(
                    {"ip": ip, "mac": mac, "interface": interface, "device": device.name}
                )
    return entries


def sync(apply: bool = False) -> None:
    inventory = load_inventory(settings.inventory_path)

    discovered: list[dict] = []
    for device in inventory.devices:
        try:
            discovered.extend(discover_arp(device))
        except Exception as exc:
            log.error("discovery failed for %s: %s", device.name, exc)

    log.info("discovered %d IP/MAC allocation(s)", len(discovered))

    if not apply:
        for entry in discovered[:25]:
            log.info(
                "[PREVIEW] %(ip)s -> %(mac)s on %(device)s/%(interface)s", entry
            )
        log.info("preview only, re-run with --apply to write to NetBox")
        return

    if not settings.netbox_url or not settings.netbox_token:
        log.error("set NETOPS_NETBOX_URL and NETOPS_NETBOX_TOKEN to sync")
        return

    import pynetbox

    nb = pynetbox.api(settings.netbox_url, token=settings.netbox_token)
    for entry in discovered:
        address = f"{entry['ip']}/32"
        description = f"seen on {entry['device']} {entry['interface']} (mac {entry['mac']})"
        existing = nb.ipam.ip_addresses.get(address=address)
        if existing:
            existing.update({"description": description})
        else:
            nb.ipam.ip_addresses.create(address=address, description=description)
    log.info("NetBox sync complete for %d address(es)", len(discovered))
