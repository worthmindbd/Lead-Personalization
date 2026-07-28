"""File lock helpers for concurrent batch manifest updates."""

from __future__ import annotations

import fcntl
import json
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def manifest_lock(path: Path):
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def update_batch_status(manifest_path: Path, batch_id: str, status: str) -> None:
    with manifest_lock(manifest_path):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for batch in manifest["batches"]:
            if batch["id"] == batch_id:
                batch["status"] = status
                break
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
