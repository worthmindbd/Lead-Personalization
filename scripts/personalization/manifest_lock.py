"""File lock helpers for concurrent batch manifest updates."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lead_personalization import fsutil


@contextmanager
def manifest_lock(path: Path):
    with fsutil.file_lock(path):
        yield


def update_batch_status(manifest_path: Path, batch_id: str, status: str) -> None:
    with manifest_lock(manifest_path):
        manifest = fsutil.load_json(manifest_path, None)
        if not isinstance(manifest, dict) or "batches" not in manifest:
            return
        found = False
        for batch in manifest.get("batches", []):
            if batch.get("id") == batch_id:
                batch["status"] = status
                found = True
                break
        if found:
            fsutil.atomic_write_json(manifest_path, manifest)
