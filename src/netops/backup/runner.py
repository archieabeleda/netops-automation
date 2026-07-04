"""Orchestrate a backup run across the inventory and detect drift.

Devices are collected in parallel. One device failing does not stop the run. New
configs are written to the store, compared against the previous capture, and
committed to git. Drifted device names go into the commit message.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from git import Actor

from ..inventory import Device, load_inventory
from ..settings import settings
from .collector import fetch_running_config
from .differ import diff_configs
from .repo import commit_and_push, ensure_repo

log = logging.getLogger(__name__)


@dataclass
class DriftResult:
    device: str
    ok: bool
    changed: bool
    diff: str = ""
    error: str = ""


def _backup_one(device: Device, store: Path) -> DriftResult:
    target = store / f"{device.name}.cfg"
    try:
        current = fetch_running_config(device)
    except Exception as exc:  # broad on purpose, isolate per device
        log.error("collection failed for %s: %s", device.name, exc)
        return DriftResult(device.name, ok=False, changed=False, error=str(exc))

    previous = target.read_text() if target.exists() else ""
    changed, diff = diff_configs(previous, current, device.name)
    target.write_text(current)

    if changed and previous:
        log.warning("drift detected on %s", device.name)
    elif changed:
        log.info("baseline captured for %s", device.name)
    else:
        log.info("no change on %s", device.name)

    return DriftResult(device.name, ok=True, changed=changed, diff=diff)


def run_backup(push: bool = True) -> list[DriftResult]:
    inventory = load_inventory(settings.inventory_path)
    store = settings.config_store
    repo = ensure_repo(store, remote=settings.git_remote, branch=settings.git_branch)

    results: list[DriftResult] = []
    with ThreadPoolExecutor(max_workers=settings.max_workers) as pool:
        futures = {pool.submit(_backup_one, d, store): d for d in inventory.devices}
        for future in as_completed(futures):
            results.append(future.result())

    drifted = [r.device for r in results if r.ok and r.changed]
    failed = [r.device for r in results if not r.ok]

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    message = f"config backup {stamp}"
    if drifted:
        message += f" | drift: {', '.join(sorted(drifted))}"

    author = Actor(settings.git_author_name, settings.git_author_email)
    committed = commit_and_push(
        repo,
        message=message,
        author=author,
        remote=settings.git_remote,
        branch=settings.git_branch,
        push=push,
    )
    log.info("committed backup: %s", message) if committed else log.info("no changes to commit")
    if failed:
        log.error("devices with errors: %s", ", ".join(sorted(failed)))
    return results


def schedule_backup(at_time: str = "02:00") -> None:
    import time

    import schedule

    log.info("scheduling daily backup at %s (Ctrl-C to stop)", at_time)
    schedule.every().day.at(at_time).do(run_backup)
    while True:
        schedule.run_pending()
        time.sleep(30)
