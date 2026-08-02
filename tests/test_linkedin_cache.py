"""The Apify LinkedIn cache is shared mutable state, and workers run in parallel.

``run_batches --workers N`` puts several batches in a ThreadPoolExecutor and each
one scrapes LinkedIn. ``scrape_profiles`` is read-modify-write over one JSON
file: load the whole cache, add this call's handles, write the whole thing back.
Without a lock the second writer's load happens before the first writer's save,
and the first writer's handles are gone — silently, and they cost money to
re-fetch.

``run_batches`` warms the cache up front to avoid this, but the warm pass leaves
failed Apify chunks uncached on purpose ("leave for a later retry"), so exactly
the handles it could not resolve are the ones the workers then race on.
"""

from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lead_personalization import linkedin  # noqa: E402

WORKERS = 8


def _post(handle: str) -> dict:
    return {
        "type": "post",
        "content": f"A recent update from {handle} about project handoffs.",
        "postedAt": {"date": "2026-07-01"},
        "author": {"publicIdentifier": handle, "name": handle.title()},
    }


@pytest.fixture
def slow_actor(monkeypatch):
    """Stand in for Apify, wide enough that an unlocked writer loses the race."""

    def fake(urls, token, max_posts):
        time.sleep(0.05)
        return [_post(linkedin.li_handle(u)) for u in urls]

    monkeypatch.setattr(linkedin, "_call_actor", fake)
    return fake


def test_parallel_workers_do_not_lose_cache_entries(tmp_path, slow_actor):
    cache_file = tmp_path / "linkedin_cache.json"
    handles = [f"worker-{i}-profile" for i in range(WORKERS)]
    errors: list[BaseException] = []
    start = threading.Barrier(WORKERS)

    def work(handle: str) -> None:
        try:
            start.wait(timeout=5)
            linkedin.scrape_profiles(
                [f"https://www.linkedin.com/in/{handle}/"], cache_file, "token-x"
            )
        except BaseException as exc:  # noqa: BLE001 - reported, not swallowed
            errors.append(exc)

    threads = [threading.Thread(target=work, args=(h,)) for h in handles]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert not errors, errors
    assert not any(t.is_alive() for t in threads), "a worker deadlocked on the cache lock"

    cached = json.loads(cache_file.read_text(encoding="utf-8"))
    missing = [h for h in handles if h not in cached]
    assert not missing, f"{len(missing)}/{WORKERS} handles lost to a write race: {missing}"


def test_a_partial_write_is_never_visible(tmp_path, monkeypatch):
    """The cache is written temp-file-then-rename, so a reader either sees the
    old file or the new one — never a truncated one. A plain write_text of a
    large dict can be caught mid-flush, and _load_cache treats unparseable JSON
    as an empty cache, which throws away every handle in it."""
    cache_file = tmp_path / "linkedin_cache.json"
    linkedin._save_cache(cache_file, {"a": {"posts": [], "scraped_at": "2026-07-01"}})

    seen: list[str] = []
    real_replace = linkedin.os.replace

    def watching_replace(src, dst):
        # At the moment of the swap the destination still holds the old content.
        seen.append(Path(dst).read_text(encoding="utf-8"))
        return real_replace(src, dst)

    monkeypatch.setattr(linkedin.os, "replace", watching_replace)
    linkedin._save_cache(cache_file, {"a": {}, "b": {}})

    assert seen and json.loads(seen[0]) == {"a": {"posts": [], "scraped_at": "2026-07-01"}}
    assert json.loads(cache_file.read_text(encoding="utf-8")) == {"a": {}, "b": {}}


def test_the_shim_keeps_the_systemexit_contract(tmp_path, monkeypatch):
    """process_batch catches SystemExit to skip LinkedIn and finish the batch.
    The library raises RuntimeError; letting that through would kill the batch."""
    from personalization import linkedin_apify as la

    monkeypatch.setattr(la, "api_token", lambda: "")
    with pytest.raises(SystemExit):
        la.scrape_profiles(["https://www.linkedin.com/in/someone/"])


def test_the_shim_delegates_rather_than_reimplementing():
    from personalization import linkedin_apify as la

    assert la.li_handle is linkedin.li_handle
    assert la.posts_for_url is linkedin.posts_for_url
    assert la.clean_post_topic is linkedin.clean_post_topic
    for private in ("_call_actor", "_load_cache", "_save_cache", "_summarize_post"):
        assert not hasattr(la, private), f"{private} came back"
