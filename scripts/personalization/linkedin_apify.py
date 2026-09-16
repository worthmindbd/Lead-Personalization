#!/usr/bin/env python3
"""Environment shim over ``lead_personalization.linkedin``.

The scraping, caching and post-cleaning all live in the library. What belongs
here is everything that is about *this checkout* rather than about LinkedIn:
where ``.env`` is, where the cache file goes, and the ``SystemExit`` contract the
batch driver relies on.

This module used to carry its own copy of the whole thing. The two had drifted
in one way that mattered: the library takes an exclusive ``flock`` and writes the
cache atomically, and this file did neither — so ``run_batches --workers N`` had
workers racing a plain ``write_text`` over one shared JSON file. The warm-up pass
in ``run_batches`` hid most of it, but not all: a failed Apify chunk is
deliberately left uncached for a later retry, so precisely the handles the warm
pass could not resolve were the ones the workers then raced to write.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lead_personalization.config import load_dotenv  # noqa: E402
from lead_personalization.linkedin import (  # noqa: E402,F401
    ACTOR,
    DEFAULT_MAX_POSTS,
    ENDPOINT,
    HTTP_TIMEOUT,
    clean_post_topic,
    li_handle,
    parse_tokens,
    posts_for_url,
)
from lead_personalization.linkedin import scrape_profiles as _scrape_profiles  # noqa: E402

STATE_DIR = ROOT / ".apify"
CACHE_FILE = STATE_DIR / "linkedin_cache.json"


def api_token() -> str:
    load_dotenv(ROOT / ".env")
    return os.environ.get("APIFY_API_TOKEN", "").strip()


def api_tokens(*, _env: dict | None = None) -> list[str]:
    if _env is None:
        load_dotenv(ROOT / ".env")
        _env = os.environ
    raw_fallbacks = (
        _env.get("APIFY_API_TOKENS", "").strip()
        or _env.get("APIFY_FALLBACK_TOKENS", "").strip()
        or _env.get("APIFY_API_FALLBACK_TOKENS", "").strip()
    )
    primary = _env.get("APIFY_API_TOKEN", "").strip()
    combined = []
    if primary:
        combined.append(primary)
    if raw_fallbacks:
        combined.append(raw_fallbacks)
    return parse_tokens(",".join(combined))


def scrape_profiles(
    urls: list[str],
    max_posts: int = DEFAULT_MAX_POSTS,
    *,
    force: bool = False,
) -> dict[str, list[dict]]:
    """Return ``{handle: [post_summary, ...]}``, caching in ``.apify/``.

    Raises ``SystemExit`` when no token is configured. That is deliberate and not
    just inherited: ``process_batch`` catches ``SystemExit`` here to *skip*
    LinkedIn enrichment and carry on with the batch. The library raises
    ``RuntimeError`` instead, so letting that through would quietly turn "run
    without LinkedIn" into "the batch dies". The check happens before delegating
    so there is one path, not two.
    """
    if not api_token():
        raise SystemExit("APIFY_API_TOKEN not set. Add it to .env (see .env.example).")
    tokens = api_tokens()
    if not tokens:
        raise SystemExit("APIFY_API_TOKEN not set. Add it to .env (see .env.example).")
    return _scrape_profiles(urls, CACHE_FILE, tokens, max_posts, force=force)
