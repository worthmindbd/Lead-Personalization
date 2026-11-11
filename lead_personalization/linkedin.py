"""LinkedIn recent-post enrichment via Apify (harvestapi/linkedin-profile-posts).

For leads that carry a LinkedIn URL, fetch the latest N posts so copy can open
with a genuinely observed signal ("your recent post on ..."). Results are cached
per handle so re-runs never re-pay. The cache read-modify-write is guarded by a
file lock and written atomically (fixes the original unlocked-cache race).

No cookies/account required by the actor. Requires an Apify API token.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from typing import Sequence

from lead_personalization import fsutil

ACTOR = "harvestapi~linkedin-profile-posts"
ENDPOINT = f"https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items"
DEFAULT_MAX_POSTS = 2
HTTP_TIMEOUT = 600
CHUNK = 40

_URL_RE = re.compile(r"https?://\S+|lnkd\.in/\S+", re.I)
_HASHTAG_RE = re.compile(r"#\w+")
_MENTION_RE = re.compile(r"@\w+")
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF\u2190-\u21FF\u2300-\u23FF]",
    re.UNICODE,
)


def parse_tokens(token_input: str | Sequence[str] | None) -> list[str]:
    """Parse one or more Apify API tokens from a string, list, or sequence.

    Supports comma-separated, semicolon-separated, or whitespace/newline-separated
    tokens, removing surrounding whitespace, quotes, and duplicates while
    preserving order.
    """
    if not token_input:
        return []
    if isinstance(token_input, str):
        parts = re.split(r"[\s,;\n\r]+", token_input)
    else:
        parts = []
        for item in token_input:
            if isinstance(item, str):
                parts.extend(re.split(r"[\s,;\n\r]+", item))
    seen: set[str] = set()
    tokens: list[str] = []
    for p in parts:
        cleaned = p.strip().strip('"').strip("'")
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            tokens.append(cleaned)
    return tokens


def li_handle(url: str) -> str:
    """Extract the canonical handle from a LinkedIn profile/company URL."""
    if not url:
        return ""
    m = re.search(r"linkedin\.com/(?:in|company|school|pub|showcase)/([^/?#]+)", url, re.I)
    if not m:
        return ""
    return m.group(1).lower().strip().rstrip("/")


@contextmanager
def _cache_lock(cache_file: Path):
    with fsutil.file_lock(cache_file):
        yield


def _load_cache(cache_file: Path) -> dict:
    return fsutil.load_json(cache_file, {})


def _save_cache(cache_file: Path, cache: dict) -> None:
    """Atomic write: temp file + os.replace so readers never see a partial file."""
    fsutil.atomic_write_json(cache_file, cache)


def clean_post_topic(content: str, max_words: int = 12) -> str:
    """Derive a short, safe topic phrase from post content for use in copy."""
    if not content:
        return ""
    text = _URL_RE.sub("", content)
    text = _HASHTAG_RE.sub("", text)
    text = _MENTION_RE.sub("", text)
    text = _EMOJI_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    sentence = re.split(r"(?<=[.!?])\s+|\n", text)[0].strip(" .,:;!-\"'")
    clause = sentence
    if len(clause.split()) > max_words:
        # Never quote a post cut mid-sentence ("...with Kelly H, Partner at").
        # Fall back to a leading clause that ends on punctuation the author
        # wrote; if there is none short enough, there is no quotable topic.
        clause = ""
        for match in re.finditer(r"[,:;]\s|\s[-–]\s", sentence):
            prefix = sentence[: match.start()].strip(" .,:;!-\"'")
            if 4 <= len(prefix.split()) <= max_words:
                clause = prefix
    clause = clause.strip(" .,:;!-\"'")
    if len(clause) < 8 or len(clause.split()) < 3:
        return ""
    return clause


def _summarize_post(post: dict) -> dict:
    posted = post.get("postedAt") or {}
    eng = post.get("engagement") or {}
    author = post.get("author") or {}
    return {
        "content": (post.get("content") or "").strip(),
        "topic": clean_post_topic(post.get("content") or ""),
        "date": posted.get("date", ""),
        "posted_ago": posted.get("postedAgoShort", ""),
        "likes": eng.get("likes", 0),
        "comments": eng.get("comments", 0),
        "url": post.get("linkedinUrl", ""),
        "type": post.get("type", "post"),
        "author_name": (author.get("name") or "").strip(),
    }


def _post_handles(post: dict) -> set[str]:
    author = post.get("author") or {}
    handles = set()
    for key in ("publicIdentifier", "universalName"):
        val = (author.get(key) or "").strip().lower()
        if val:
            handles.add(val)
    h = li_handle(author.get("linkedinUrl") or "")
    if h:
        handles.add(h)
    return handles


def _call_actor(urls: list[str], token: str, max_posts: int) -> list[dict]:
    payload = {
        "targetUrls": urls,
        "maxPosts": max_posts,
        "scrapeReactions": False,
        "scrapeComments": False,
        "includeReposts": True,
        "includeQuotePosts": True,
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        body = resp.read().decode()
    parsed = json.loads(body) if body.strip() else []
    if isinstance(parsed, dict) and "error" in parsed:
        error_msg = parsed.get("error")
        if isinstance(error_msg, dict):
            error_msg = error_msg.get("message") or str(error_msg)
        raise RuntimeError(f"Apify actor error: {error_msg}")
    return parsed if isinstance(parsed, list) else []


def scrape_profiles(
    urls: list[str],
    cache_file: Path,
    token: str | Sequence[str],
    max_posts: int = DEFAULT_MAX_POSTS,
    *,
    force: bool = False,
) -> dict[str, list[dict]]:
    """Return {handle: [post_summary, ...]} for the given LinkedIn URLs.

    Uses the on-disk cache to skip already-scraped handles. One batched actor
    call covers all uncached URLs. When multiple tokens are provided (list or
    comma-separated string), if an API call fails with one token, it
    automatically falls back to the next token in the list. Handles returning
    no posts are cached as empty lists so silent profiles are not re-paid for.
    """
    tokens = parse_tokens(token)
    if not tokens:
        with _cache_lock(cache_file):
            cache = _load_cache(cache_file)
            result: dict[str, list[dict]] = {}
            for url in urls:
                h = li_handle(url)
                if not h:
                    continue
                if not force and h in cache:
                    result[h] = cache[h].get("posts", [])
            if result:
                return result
        raise RuntimeError("APIFY_API_TOKEN not set. Add it to .env (see .env.example).")

    # Snapshot under the lock, fetch outside it. The lock used to wrap the
    # whole loop including the HTTP calls (up to 600s per chunk), so parallel
    # workers serialized for minutes on paid fetches.
    with _cache_lock(cache_file):
        cache_snapshot = _load_cache(cache_file)
    result = {}
    pending: list[str] = []
    pending_handles: list[str] = []

    for url in urls:
        h = li_handle(url)
        if not h:
            continue
        if not force and h in cache_snapshot:
            result[h] = cache_snapshot[h].get("posts", [])
        else:
            pending.append(url)
            pending_handles.append(h)

    if not pending:
        return result

    LINKEDIN_CHUNK = CHUNK
    # UTC, matching the Reoon daily-usage tracker: cache stamps feed
    # freshness decisions that must not depend on the machine's timezone.
    stamp = datetime.now(timezone.utc).date().isoformat()
    active_token_idx = 0
    num_tokens = len(tokens)
    fetched: dict[str, list[dict]] = {}

    for offset in range(0, len(pending), LINKEDIN_CHUNK):
        chunk_urls = pending[offset : offset + LINKEDIN_CHUNK]
        chunk_handles = pending_handles[offset : offset + LINKEDIN_CHUNK]
        chunk_num = offset // LINKEDIN_CHUNK + 1

        items = None
        attempts = 0
        while attempts < num_tokens:
            curr_token = tokens[active_token_idx]
            token_display = (
                f"{curr_token[:4]}...{curr_token[-4:]}" if len(curr_token) > 8 else "***"
            )
            try:
                items = _call_actor(chunk_urls, curr_token, max_posts)
                break
            except urllib.error.HTTPError as exc:
                if exc.code in (401, 403):
                    raise RuntimeError(
                        f"Apify auth failed with token {token_display} "
                        f"(HTTP {exc.code}): check APIFY_API_TOKEN."
                    ) from exc
                detail = ""
                try:
                    detail = exc.read().decode()[:200]
                except Exception:
                    detail = ""
                err_msg = f"{exc} {detail}".strip()
                attempts += 1
                if attempts < num_tokens:
                    print(
                        f"Apify LinkedIn scrape failed with token {token_display} "
                        f"(chunk {chunk_num}): {err_msg}. Falling back to next token..."
                    )
                    active_token_idx = (active_token_idx + 1) % num_tokens
                else:
                    print(
                        f"Apify LinkedIn scrape failed (chunk {chunk_num}): {err_msg} "
                        f"(exhausted all {num_tokens} token(s))"
                    )
                    active_token_idx = (active_token_idx + 1) % num_tokens
            except (urllib.error.URLError, TimeoutError, OSError, RuntimeError) as exc:
                err_msg = str(exc).strip()
                attempts += 1
                if attempts < num_tokens:
                    print(
                        f"Apify LinkedIn scrape failed with token {token_display} "
                        f"(chunk {chunk_num}): {err_msg}. Falling back to next token..."
                    )
                    active_token_idx = (active_token_idx + 1) % num_tokens
                else:
                    print(
                        f"Apify LinkedIn scrape failed (chunk {chunk_num}): {err_msg} "
                        f"(exhausted all {num_tokens} token(s))"
                    )
                    active_token_idx = (active_token_idx + 1) % num_tokens

        if items is None:
            continue

        grouped: dict[str, list[dict]] = {}
        for post in items:
            if (post.get("type") or "post") not in ("post", "repost", "quote"):
                continue
            summary = _summarize_post(post)
            for h in _post_handles(post):
                grouped.setdefault(h, []).append(summary)

        for h in chunk_handles:
            fetched[h] = grouped.get(h, [])[:max_posts]

    if fetched:
        # Re-lock only to merge. Another process may have written while we
        # fetched, so reload and merge rather than overwrite.
        with _cache_lock(cache_file):
            merged_cache = _load_cache(cache_file)
            if not isinstance(merged_cache, dict):
                merged_cache = {}
            for h, posts in fetched.items():
                merged_cache[h] = {"posts": posts, "scraped_at": stamp}
            _save_cache(cache_file, merged_cache)
        result.update(fetched)

    return result


def posts_for_url(url: str, scraped: dict[str, list[dict]]) -> list[dict]:
    return scraped.get(li_handle(url), [])
