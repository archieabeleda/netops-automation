"""Line-level drift detection using difflib."""

from __future__ import annotations

import difflib


def diff_configs(old: str, new: str, name: str) -> tuple[bool, str]:
    """Return (changed, unified_diff).

    changed is False when the configs match, which is the common case and means
    no commit is needed for this device.
    """
    diff = list(
        difflib.unified_diff(
            old.splitlines(),
            new.splitlines(),
            fromfile=f"{name} (previous)",
            tofile=f"{name} (current)",
            lineterm="",
        )
    )
    return bool(diff), "\n".join(diff)
