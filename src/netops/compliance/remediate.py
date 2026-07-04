"""Push fixes for violated rules.

This is the only part of the toolkit that changes device state, so it is guarded.
It runs as a dry run by default and prints the exact config it would send. Pushes
happen only when apply is True, and each push is followed by a config save.
"""

from __future__ import annotations

import logging

from ..connections import connect
from ..inventory import Device, load_inventory
from ..settings import settings
from .auditor import get_config, is_violated
from .rules import RuleSet, load_rules

log = logging.getLogger(__name__)


def _fixes_for(device: Device, ruleset: RuleSet) -> list[str]:
    """Config lines needed to bring one device into compliance."""
    config = get_config(device)
    lines: list[str] = []
    for rule in ruleset.rules:
        if not rule.applies_to(device.platform):
            continue
        if rule.remediation and is_violated(config, rule):
            log.warning("%s violates %s, queuing %d fix line(s)", device.name, rule.id, len(rule.remediation))
            lines.extend(rule.remediation)
    return lines


def run_remediation(rules_path: str, apply: bool = False) -> None:
    ruleset = load_rules(rules_path)
    inventory = load_inventory(settings.inventory_path)

    for device in inventory.devices:
        try:
            fixes = _fixes_for(device, ruleset)
        except Exception as exc:
            log.error("remediation check failed for %s: %s", device.name, exc)
            continue

        if not fixes:
            log.info("%s is compliant, nothing to push", device.name)
            continue

        if not apply:
            block = "\n".join(fixes)
            log.info("[DRY RUN] %s would receive:\n%s", device.name, block)
            continue

        with connect(device) as conn:
            output = conn.send_config_set(fixes, read_timeout=120)
            conn.save_config()
        log.warning("applied %d fix line(s) to %s", len(fixes), device.name)
        log.debug(output)
