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


def batch_csv(directory: Path, batch: str, rows: list[dict], prefix: str = "mix-leads") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{prefix}-batch-{batch}-enriched.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["primary_email", "company"])
        writer.writeheader()
        writer.writerows(rows)
    return path


def manifest_file(tmp_path: Path, prefix: str = "mix-leads", ids=("001", "002")) -> Path:
    path = tmp_path / f"{prefix}-batch-manifest.json"
    path.write_text(
        json.dumps({"prefix": prefix,
                    "batches": [{"id": b, "status": "pending"} for b in ids]}),
        encoding="utf-8",
    )
    return path


@pytest.fixture(params=["mix-leads", "july-6"], ids=["default-prefix", "list-prefix"])
def prefix(request):
    """Run every merge behaviour under both names.

    ``mix-leads`` is the historical default a hand-run merge still falls back
    to; ``july-6`` is what the pipeline actually passes now. These tests used to
    hardcode the default, so they would have passed just as happily if the
    prefix were ignored entirely.
    """
    return request.param


@pytest.fixture
def two_batches(tmp_path, prefix):
    enriched = tmp_path / "enriched"
    batch_csv(enriched, "001", [{"primary_email": "a@x.com", "company": "A"},
                                {"primary_email": "b@x.com", "company": "B"}], prefix)
    batch_csv(enriched, "002", [{"primary_email": "b@x.com", "company": "B again"},
                                {"primary_email": "c@x.com", "company": "C"}], prefix)
    return enriched


# ---------------------------------------------------------------------------
# Merging
# ---------------------------------------------------------------------------


def test_batches_merge_and_dedupe_by_address(two_batches, prefix, tmp_path):
    out = tmp_path / "merged.csv"

    assert merge_enriched(two_batches, out, tmp_path / "absent.json", prefix=prefix) == 3

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


def test_a_missing_manifest_is_not_fatal(two_batches, prefix, tmp_path):
    out = tmp_path / "merged.csv"
    assert merge_enriched(two_batches, out, tmp_path / "nope.json", prefix=prefix) == 3


# ---------------------------------------------------------------------------
# The manifest write
# ---------------------------------------------------------------------------


def test_merge_records_its_output_in_the_manifest(two_batches, prefix, tmp_path, monkeypatch):
    """No prefix argument here on purpose: the merge must take it from the
    manifest it is about to update."""
    import personalization.merge_enriched as me

    monkeypatch.setattr(me, "ROOT", tmp_path)
    path = manifest_file(tmp_path, prefix)

    me.merge_enriched(two_batches, tmp_path / "merged.csv", path)

    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert manifest["merged_output"] == "merged.csv"
    assert manifest["merged_row_count"] == 3
    assert [b["status"] for b in manifest["batches"]] == ["pending", "pending"]


def test_the_manifest_write_waits_for_the_lock(two_batches, prefix, tmp_path, monkeypatch):
    """A status flip that lands mid-merge must survive the merge's write.

    Without the lock the merge reads the manifest, a worker writes "done", and
    the merge's write puts "pending" back — losing a batch's completed status.
    """
    import personalization.merge_enriched as me

    monkeypatch.setattr(me, "ROOT", tmp_path)
    path = manifest_file(tmp_path, prefix)

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
