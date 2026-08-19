"""The shared Reoon cache must never lose paid-for results.

``--force`` used to rebuild the cache from ``{}`` and save over the shared
file — every other list's verified addresses were erased and re-paid for. The
cache is now always loaded, merged under a lock, and written atomically; bulk
tasks are remembered on creation so an interrupted poll resumes instead of
re-spending credits on a duplicate task.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import verify_emails_reoon as ver  # noqa: E402


def test_merge_into_cache_never_erases_other_entries(tmp_path, monkeypatch):
    monkeypatch.setattr(ver, "CACHE_FILE", tmp_path / "cache.json")
    ver.save_cache({"other-list@x.com": {"status": "safe"}})

    ver.merge_into_cache({"new@x.com": {"status": "invalid"}})

    cache = ver.load_cache()
    assert cache["other-list@x.com"]["status"] == "safe"
    assert cache["new@x.com"]["status"] == "invalid"


def test_a_corrupt_cache_is_quarantined_not_fatal(tmp_path, monkeypatch):
    cache_file = tmp_path / "cache.json"
    cache_file.write_text('{"trunc', encoding="utf-8")
    monkeypatch.setattr(ver, "CACHE_FILE", cache_file)

    assert ver.load_cache() == {}
    quarantined = list(tmp_path.glob("cache.json.corrupt-*"))
    assert len(quarantined) == 1


def test_resumable_task_matches_name_and_emails(tmp_path, monkeypatch):
    monkeypatch.setattr(ver, "TASK_FILE", tmp_path / "bulk_task.json")
    from datetime import datetime, timedelta, timezone

    fresh = datetime.now(timezone.utc).isoformat()
    ver.save_json(
        ver.TASK_FILE,
        {
            "task_id": "t-1",
            "task_name": "july-1",
            "emails": ["a@x.com", "b@x.com"],
            "created_at": fresh,
        },
    )

    assert ver._resumable_task_id(["b@x.com", "a@x.com"], "july-1") == "t-1"
    assert ver._resumable_task_id(["a@x.com"], "july-1") is None  # different set
    assert ver._resumable_task_id(["a@x.com", "b@x.com"], "other") is None

    stale = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
    ver.save_json(
        ver.TASK_FILE,
        {"task_id": "t-2", "task_name": "july-1",
         "emails": ["a@x.com", "b@x.com"], "created_at": stale},
    )
    assert ver._resumable_task_id(["a@x.com", "b@x.com"], "july-1") is None


def test_api_get_retries_transient_http_errors(monkeypatch):
    calls = {"n": 0}

    class FakeHTTPError(ver.urllib.error.HTTPError):
        def __init__(self):
            super().__init__(None, 503, "unavailable", None, None)  # type: ignore[arg-type]

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        if calls["n"] < 3:
            raise FakeHTTPError()
        return __import__("io").BytesIO(b'{"status": "success"}')

    monkeypatch.setattr(ver.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(ver.time, "sleep", lambda s: None)

    result = ver.api_get("verify", {"email": "a@x.com"}, "key")

    assert result == {"status": "success"}
    assert calls["n"] == 3
