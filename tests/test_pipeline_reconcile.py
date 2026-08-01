"""Reconcile tests: a list is only 'done' once its cleaned emails are checked.

The bug these cover: reconcile compared enriched against verified and declared
the list finished, which marked lists 'done' whose cleaned emails had never
been verified at all (e.g. 3,426 cleaned / 7 verified / 7 enriched). Because
reconcile short-circuits on stage == 'done', that silently abandoned the
backlog for good.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "pipeline"))

import run_pipeline as rp  # noqa: E402


def write_csv(path: Path, emails: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["primary_email", "company"])
        writer.writeheader()
        for i, email in enumerate(emails):
            writer.writerow({"primary_email": email, "company": f"Co {i}"})
    return path


@pytest.fixture
def cache_file(tmp_path, monkeypatch):
    """Point the Reoon cache at a throwaway file."""
    path = tmp_path / ".reoon" / "verified_cache.json"
    monkeypatch.setattr(rp, "REOON_CACHE_FILE", path)
    return path


def emails(n: int, start: int = 0) -> list[str]:
    return [f"lead{i}@example.com" for i in range(start, start + n)]


# --- seed_cache_from_verified ---------------------------------------------


def test_seed_cache_records_verified_emails(tmp_path, cache_file):
    verified = write_csv(tmp_path / "verified.csv", emails(3))

    assert rp.seed_cache_from_verified(verified) == 3

    cache = rp.load_json(cache_file, {})
    assert set(cache) == set(emails(3))
    assert cache["lead0@example.com"]["status"] == "safe"


def test_seed_cache_never_overwrites_a_real_reoon_result(tmp_path, cache_file):
    rp.save_json_atomic(cache_file, {"lead0@example.com": {"status": "invalid"}})
    verified = write_csv(tmp_path / "verified.csv", emails(2))

    assert rp.seed_cache_from_verified(verified) == 1  # only lead1 is new
    cache = rp.load_json(cache_file, {})
    assert cache["lead0@example.com"]["status"] == "invalid"


def test_seed_cache_tolerates_a_missing_file(tmp_path, cache_file):
    assert rp.seed_cache_from_verified(tmp_path / "nope.csv") == 0


def test_seeding_makes_verified_emails_stop_counting_as_pending(tmp_path, cache_file):
    cleaned = write_csv(tmp_path / "cleaned.csv", emails(10))
    verified = write_csv(tmp_path / "verified.csv", emails(4))

    assert rp.pending_verification(cleaned) == 10
    rp.seed_cache_from_verified(verified)
    assert rp.pending_verification(cleaned) == 6


# --- reconcile stage decisions --------------------------------------------


@pytest.fixture
def reconcile(tmp_path, monkeypatch, cache_file):
    """Drive reconcile_list_with_drive with fake Drive contents.

    `counts` maps stage key -> number of rows that stage holds on Drive.
    Returns the mutated state entry.
    """
    # reconcile records paths relative to ROOT, so the fake workdir must sit
    # under a ROOT it agrees with.
    monkeypatch.setattr(rp, "ROOT", tmp_path)
    monkeypatch.setattr(rp, "WORK_ROOT", tmp_path / "work")
    monkeypatch.setattr(rp, "stage_line", lambda *a, **k: None)
    monkeypatch.setattr(rp, "save_state", lambda *a, **k: None)

    def run(counts: dict[str, int]):
        monkeypatch.setattr(
            rp, "drive_folder_csvs",
            lambda remote, folder, title: (["f.csv"] if _key(folder) in counts else []),
        )

        def adopt(remote, folder, title, csvs, dest):
            key = _key(folder)
            write_csv(dest, emails(counts[key]))
            return counts[key]

        monkeypatch.setattr(rp, "adopt_authoritative_csv", adopt)

        entry = {
            "slug": "july-17-2026", "stage": "new", "uploads": {},
            "pending_verification": None, "verify_complete": False,
        }
        args = type("A", (), {"local_only": False, "remote": "gdrive"})()
        rp.reconcile_list_with_drive("July 17,2026", entry, args, {})
        return entry

    return run


def _key(folder: str) -> str:
    return {
        rp.DRIVE_CLEANED: "cleaned",
        rp.DRIVE_VERIFIED: "verified",
        rp.DRIVE_PERSONALIZED: "enriched",
    }[folder]


def test_mostly_unverified_list_is_not_marked_done(reconcile):
    """The regression: 3426 cleaned, 7 verified, 7 enriched is NOT done."""
    entry = reconcile({"cleaned": 3426, "verified": 7, "enriched": 7})

    assert entry["stage"] == "verifying"
    assert entry["verify_complete"] is False
    assert entry["pending_verification"] == 3419


def test_fully_verified_and_personalized_list_is_done(reconcile):
    entry = reconcile({"cleaned": 100, "verified": 100, "enriched": 100})

    assert entry["stage"] == "done"
    assert entry["verify_complete"] is True
    assert entry["pending_verification"] == 0


def test_fully_verified_but_not_personalized_resumes_at_personalize(reconcile):
    entry = reconcile({"cleaned": 100, "verified": 100, "enriched": 40})

    assert entry["stage"] == "verifying"
    assert entry["verify_complete"] is True
    assert entry["pending_verification"] == 0


def test_cleaned_only_list_resumes_at_verify(reconcile):
    entry = reconcile({"cleaned": 500})

    assert entry["stage"] == "cleaned"
    assert entry["pending_verification"] == 500


def test_reconcile_reseeds_the_cache_so_quota_is_not_respent(reconcile, cache_file):
    reconcile({"cleaned": 100, "verified": 60, "enriched": 60})

    cache = rp.load_json(cache_file, {})
    assert len(cache) == 60, "verified emails should be recorded as already checked"


# --- ordering: unfinished lists before new uploads ------------------------


def _lists(**stages) -> dict:
    """title -> entry, with drive_mtime derived from the title's order."""
    out = {}
    for i, (title, spec) in enumerate(stages.items()):
        stage, cleaned = spec
        out[title] = {
            "stage": stage,
            "drive_mtime": f"2026-07-{i + 1:02d}T00:00:00Z",
            "discovered_at": f"2026-07-{i + 1:02d}T00:00:00Z",
        }
        if cleaned:
            out[title]["cleaned_csv"] = f"{title}.csv"
    return out


def prioritise(lists: dict) -> list[str]:
    args = type("A", (), {"list": None})()
    return rp.prioritise(list(lists), lists, args)


def test_partly_verified_list_runs_before_a_new_upload():
    """The daily verify budget is shared — the backlog must claim it first."""
    lists = _lists(
        backlog=("verifying", True),   # older, part-way through
        fresh=("discovered", False),   # newer, never touched
    )
    assert prioritise(lists) == ["backlog", "fresh"]


def test_new_upload_never_jumps_ahead_even_when_it_is_older():
    lists = _lists(
        old_new=("discovered", False),  # oldest mtime, but brand new
        newer_backlog=("verifying", True),
    )
    assert prioritise(lists) == ["newer_backlog", "old_new"]


def test_done_lists_sort_last():
    lists = _lists(
        finished=("done", True),
        fresh=("discovered", False),
        backlog=("cleaned", True),
    )
    assert prioritise(lists) == ["backlog", "fresh", "finished"]


def test_oldest_first_within_the_same_priority():
    lists = _lists(
        first=("verifying", True),
        second=("verifying", True),
        third=("verifying", True),
    )
    assert prioritise(lists) == ["first", "second", "third"]


def test_explicit_single_list_bypasses_prioritisation():
    lists = _lists(a=("done", True), b=("verifying", True))
    args = type("A", (), {"list": "a"})()
    assert rp.prioritise(["a"], lists, args) == ["a"]


def test_list_already_done_is_left_untouched(reconcile, monkeypatch):
    monkeypatch.setattr(rp, "drive_folder_csvs", lambda *a, **k: pytest.fail("no I/O"))
    entry = {"slug": "s", "stage": "done", "uploads": {}}
    args = type("A", (), {"local_only": False, "remote": "gdrive"})()

    rp.reconcile_list_with_drive("July 17,2026", entry, args, {})
    assert entry["stage"] == "done"
