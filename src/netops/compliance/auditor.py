"""Evaluate devices against the rule set and report violations.

The auditor is read-only. It connects, reads the running config, and checks every
applicable rule. It never changes a device.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from ..connections import connect
from ..inventory import Device, load_inventory
from ..settings import settings
from .rules import Match, Rule, RuleSet, load_rules

log = logging.getLogger(__name__)


@dataclass
class Finding:
    device: str
    rule_id: str
    title: str
    severity: str
    violated: bool


def get_config(device: Device) -> str:
    with connect(device) as conn:
        return conn.send_command("show running-config", read_timeout=120)


def is_violated(config: str, rule: Rule) -> bool:
    present = bool(rule.compiled().search(config))
    if rule.match is Match.must_not_contain:
        return present
    return not present


def audit_device(device: Device, ruleset: RuleSet) -> list[Finding]:
    config = get_config(device)
    findings: list[Finding] = []
    for rule in ruleset.rules:
        if not rule.applies_to(device.platform):
            continue
        violated = is_violated(config, rule)
        findings.append(Finding(device.name, rule.id, rule.title, rule.severity, violated))
        if violated:
            log.warning("[%s] %s on %s: %s", rule.severity.upper(), rule.id, device.name, rule.title)
    return findings


def run_audit(rules_path: str) -> list[Finding]:
    ruleset = load_rules(rules_path)
    inventory = load_inventory(settings.inventory_path)

    findings: list[Finding] = []
    for device in inventory.devices:
        try:
            findings.extend(audit_device(device, ruleset))
        except Exception as exc:
            log.error("audit failed for %s: %s", device.name, exc)

    violations = [f for f in findings if f.violated]
    log.info("audit complete: %d checks, %d violation(s)", len(findings), len(violations))
    return findings
