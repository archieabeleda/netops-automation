"""Git storage for captured configs via GitPython.

The config store is its own repository with a dedicated remote so device configs
stay separate from the toolkit code.
"""

from __future__ import annotations

import logging
from pathlib import Path

from git import Actor, Repo

log = logging.getLogger(__name__)


def ensure_repo(path: Path, remote: str = "", branch: str = "main") -> Repo:
    path.mkdir(parents=True, exist_ok=True)
    if (path / ".git").exists():
        repo = Repo(path)
    else:
        repo = Repo.init(path, initial_branch=branch)
        log.info("initialised config repository at %s", path)

    if remote:
        names = [r.name for r in repo.remotes]
        if "origin" in names:
            repo.remotes.origin.set_url(remote)
        else:
            repo.create_remote("origin", remote)
    return repo


def commit_and_push(
    repo: Repo,
    message: str,
    author: Actor,
    remote: str = "",
    branch: str = "main",
    push: bool = True,
) -> bool:
    """Stage everything, commit if there is a change, and push when asked.

    Returns True when a commit was made.
    """
    repo.git.add(A=True)
    if not repo.is_dirty(untracked_files=True):
        return False

    repo.index.commit(message, author=author, committer=author)
    if push and remote:
        try:
            repo.git.push("origin", branch)
        except Exception as exc:
            log.error("git push failed: %s", exc)
    return True
