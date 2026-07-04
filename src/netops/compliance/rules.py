"""Compliance rule model.

A rule is a regular expression checked against the running config, plus the
config lines that fix a violation. Rules are declarative and live in YAML so the
rule set grows without touching code.
"""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class Match(str, Enum):
    must_not_contain = "must_not_contain"  # violation when the pattern IS present
    must_contain = "must_contain"  # violation when the pattern is ABSENT


class Rule(BaseModel):
    id: str
    title: str
    severity: str = "medium"
    match: Match
    pattern: str  # regex, evaluated against the whole config in multiline mode
    remediation: list[str] = Field(default_factory=list)  # config lines that fix it
    platforms: list[str] = Field(default_factory=list)  # empty means all platforms

    def compiled(self) -> re.Pattern:
        return re.compile(self.pattern, re.MULTILINE)

    def applies_to(self, platform: str) -> bool:
        return not self.platforms or platform in self.platforms


class RuleSet(BaseModel):
    rules: list[Rule]


def load_rules(path: str | Path) -> RuleSet:
    data = yaml.safe_load(Path(path).read_text())
    return RuleSet(**data)
