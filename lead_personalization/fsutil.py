"""Shared file-system helpers: atomic writes, file locks, tolerant JSON loads.

Every JSON file this project treats as durable state (the Reoon cache, the
pipeline state, batch manifests, the LinkedIn cache) is written atomically
(tmp + os.replace) and mutated under a file lock, so a crash or a concurrent
process can never leave a truncated or half-written file behind.
"""

from __future__ import annotations

import fcntl
import json
import os
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def atomic_write_text(path: Path, text: str) -> None:
    """Write text via tmp + os.replace so readers never see a partial file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def atomic_write_json(path: Path, data, newline: bool = True) -> None:
    text = json.dumps(data, indent=2)
    if newline:
        text += "\n"
    atomic_write_text(path, text)


@contextmanager
def file_lock(path: Path):
    """Hold an exclusive flock on ``<path>.lock`` for the wrapped block."""
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def load_json(path: Path, default):
    """Load JSON from ``path``, returning ``default`` when missing or corrupt.

    A file that fails to parse is quarantined next to itself (renamed to
    ``<name>.corrupt-<utc stamp>``) instead of crashing every future run on
    the same decode error.
    """
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        quarantine = path.parent / f"{path.name}.corrupt-{stamp}"
        try:
            os.replace(path, quarantine)
            print(
                f"Warning: {path} is corrupt JSON; moved to {quarantine.name}.",
                file=sys.stderr,
            )
        except OSError:
            pass
        return default
