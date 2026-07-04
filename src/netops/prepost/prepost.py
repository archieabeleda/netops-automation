"""Capture network state before a change and validate it after.

Take a snapshot labeled 'pre', make the change, take a snapshot labeled 'post',
then compare. State is captured with use_textfsm so results are structured where
an ntc-template exists. The comparison flags lost BGP neighbors and interfaces
that went down. Extend the checks and command set for your platforms.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from ..connections import connect
from ..inventory import load_inventory
from ..settings import settings

log = logging.getLogger(__name__)

# Commands captured per platform. Add rows for prefixes, VRFs, and neighbors you
# care about. use_textfsm returns a list of dicts when a template matches.
STATE_COMMANDS = {
    "cisco_ios": ["show ip interface brief", "show ip bgp summary", "show ip route"],
    "cisco_xe": ["show ip interface brief", "show ip bgp summary", "show ip route"],
    "cisco_nxos": ["show ip interface brief", "show ip bgp summary", "show ip route"],
}

SNAP_DIR = Path("data/snapshots")


def take_snapshot(label: str) -> Path:
    inventory = load_inventory(settings.inventory_path)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot = {"label": label, "taken": stamp, "devices": {}}

    for device in inventory.devices:
        commands = STATE_COMMANDS.get(device.platform)
        if not commands:
            log.info("no state commands for %s (%s), skipping", device.name, device.platform)
            continue
        state: dict = {}
        try:
            with connect(device) as conn:
                for command in commands:
                    state[command] = conn.send_command(command, use_textfsm=True, read_timeout=120)
        except Exception as exc:
            log.error("snapshot failed for %s: %s", device.name, exc)
            continue
        snapshot["devices"][device.name] = state

    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    out = SNAP_DIR / f"{label}-{stamp}.json"
    out.write_text(json.dumps(snapshot, indent=2, default=str))
    log.info("snapshot written to %s", out)
    return out


def _bgp_neighbors(state: dict) -> set[str]:
    rows = state.get("show ip bgp summary")
    neighbors: set[str] = set()
    if isinstance(rows, list):
        for row in rows:
            addr = row.get("bgp_neigh") or row.get("neighbor")
            if addr:
                neighbors.add(addr)
    return neighbors


def _down_interfaces(state: dict) -> set[str]:
    rows = state.get("show ip interface brief")
    down: set[str] = set()
    if isinstance(rows, list):
        for row in rows:
            status = (row.get("status") or "").lower()
            proto = (row.get("proto") or row.get("protocol") or "").lower()
            name = row.get("intf") or row.get("interface")
            if name and ("down" in status or "down" in proto):
                down.add(name)
    return down


def _latest(label: str) -> Path:
    matches = sorted(SNAP_DIR.glob(f"{label}-*.json"))
    if not matches:
        raise FileNotFoundError(f"no snapshot found for label '{label}'")
    return matches[-1]


def compare_snapshots(before: str, after: str) -> int:
    pre = json.loads(_latest(before).read_text())
    post = json.loads(_latest(after).read_text())

    problems = 0
    for name, pre_state in pre["devices"].items():
        post_state = post["devices"].get(name)
        if not post_state:
            log.warning("%s is missing from the post snapshot", name)
            problems += 1
            continue

        lost = _bgp_neighbors(pre_state) - _bgp_neighbors(post_state)
        if lost:
            log.warning("%s lost BGP neighbor(s): %s", name, ", ".join(sorted(lost)))
            problems += 1

        newly_down = _down_interfaces(post_state) - _down_interfaces(pre_state)
        if newly_down:
            log.warning("%s interface(s) newly down: %s", name, ", ".join(sorted(newly_down)))
            problems += 1

    if problems:
        log.error("post-change validation found %d issue(s)", problems)
    else:
        log.info("post-change validation clean: no lost adjacencies or interface drops")
    return problems
