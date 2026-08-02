"""Merging per-batch enriched CSVs, and the manifest write that follows it.

The merge records its output in the batch manifest with a read-modify-write.
``update_batch_status`` takes a lock for exactly that reason; the merge did not,
so a worker flipping a batch to "done" in the gap would have had its status
erased and the batch re-run.
"""

from __future__ import annotations

import csv
import json
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from personalization.manifest_lock import manifest_lock, update_batch_status  # noqa: E402
from personalization.merge_enriched import merge_enriched  # noqa: E402


def batch_csv(directory: Path, batch: str, rows: list[dict]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"mix-leads-batch-{batch}-enriched.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["primary_email", "company"])
        writer.writeheader()
        writer.writerows(rows)
    return path


def manifest_file(tmp_path: Path, ids=("001", "002")) -> Path:
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps({"batches": [{"id": b, "status": "pending"} for b in ids]}),
        encoding="utf-8",
    )
    return path


@pytest.fixture
def two_batches(tmp_path):
    enriched = tmp_path / "enriched"
    batch_csv(enriched, "001", [{"primary_email": "a@x.com", "company": "A"},
                                {"primary_email": "b@x.com", "company": "B"}])
    batch_csv(enriched, "002", [{"primary_email": "b@x.com", "company": "B again"},
                                {"primary_email": "c@x.com", "company": "C"}])
    return enriched


# ---------------------------------------------------------------------------
# Merging
# ---------------------------------------------------------------------------


def test_batches_merge_and_dedupe_by_address(two_batches, tmp_path):
    out = tmp_path / "merged.csv"

    assert merge_enriched(two_batches, out, tmp_path / "absent.json") == 3

    with out.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert [r["primary_email"] for r in rows] == ["a@x.com", "b@x.com", "c@x.com"]
    assert rows[1]["company"] == "B"  # first batch wins the duplicate


def test_no_batch_files_is_an_error_not_an_empty_file(tmp_path):
    empty = tmp_path / "enriched"
    empty.mkdir()

    with pytest.raises(SystemExit):
        merge_enriched(empty, tmp_path / "merged.csv", tmp_path / "absent.json")

    assert not (tmp_path / "merged.csv").exists()


def test_a_missing_manifest_is_not_fatal(two_batches, tmp_path):
    assert merge_enriched(two_batches, tmp_path / "merged.csv", tmp_path / "nope.json") == 3


# ---------------------------------------------------------------------------
# The manifest write
# ---------------------------------------------------------------------------


def test_merge_records_its_output_in_the_manifest(two_batches, tmp_path, monkeypatch):
    import personalization.merge_enriched as me

    monkeypatch.setattr(me, "ROOT", tmp_path)
    path = manifest_file(tmp_path)

    me.merge_enriched(two_batches, tmp_path / "merged.csv", path)

    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert manifest["merged_output"] == "merged.csv"
    assert manifest["merged_row_count"] == 3
    assert [b["status"] for b in manifest["batches"]] == ["pending", "pending"]


def test_the_manifest_write_waits_for_the_lock(two_batches, tmp_path, monkeypatch):
    """A status flip that lands mid-merge must survive the merge's write.

    Without the lock the merge reads the manifest, a worker writes "done", and
    the merge's write puts "pending" back — losing a batch's completed status.
    """
    import personalization.merge_enriched as me

    monkeypatch.setattr(me, "ROOT", tmp_path)
    path = manifest_file(tmp_path)

    merging = threading.Thread(
        target=me.merge_enriched, args=(two_batches, tmp_path / "merged.csv", path)
    )
    with manifest_lock(path):
        merging.start()
        # An unlocked merge finishes this in milliseconds. Still running means
        # it is waiting on the lock, which is the whole point.
        merging.join(timeout=0.25)
        assert merging.is_alive(), "merge wrote the manifest without taking the lock"

        data = json.loads(path.read_text(encoding="utf-8"))
        data["batches"][0]["status"] = "done"
        path.write_text(json.dumps(data), encoding="utf-8")

    merging.join(timeout=5)
    assert not merging.is_alive()

    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert manifest["batches"][0]["status"] == "done"  # not clobbered
    assert manifest["merged_row_count"] == 3           # and the merge landed


def test_update_batch_status_and_merge_use_the_same_lock_file(tmp_path):
    path = manifest_file(tmp_path)
    update_batch_status(path, "002", "done")

    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert [b["status"] for b in manifest["batches"]] == ["pending", "done"]
    assert path.with_suffix(path.suffix + ".lock").exists()
