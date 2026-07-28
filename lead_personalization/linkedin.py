"""LinkedIn recent-post enrichment via Apify (harvestapi/linkedin-profile-posts).

For leads that carry a LinkedIn URL, fetch the latest N posts so copy can open
with a genuinely observed signal ("your recent post on ..."). Results are cached
per handle so re-runs never re-pay. The cache read-modify-write is guarded by a
file lock and written atomically (fixes the original unlocked-cache race).

No cookies/account required by the actor. Requires an Apify API token.
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import urllib.error
import urllib.request
from contextlib import contextmanager
from datetime import date
from pathlib import Path

ACTOR = "harvestapi~linkedin-profile-posts"
ENDPOINT = f"https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items"
DEFAULT_MAX_POSTS = 2
HTTP_TIMEOUT = 600

_URL_RE = re.compile(r"https?://\S+|lnkd\.in/\S+", re.I)
_HASHTAG_RE = re.compile(r"#\w+")
_MENTION_RE = re.compile(r"@\w+")
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF\u2190-\u21FF\u2300-\u23FF]",
    re.UNICODE,
)


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
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    lock_path = cache_file.with_suffix(cache_file.suffix + ".lock")
    with lock_path.open("w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def _load_cache(cache_file: Path) -> dict:
    if not cache_file.is_file():
        return {}
    try:
        return json.loads(cache_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_cache(cache_file: Path, cache: dict) -> None:
    """Atomic write: temp file + os.replace so readers never see a partial file."""
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = cache_file.with_suffix(cache_file.suffix + ".tmp")
    tmp.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    os.replace(tmp, cache_file)


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
    clause = re.split(r"(?<=[.!?])\s+|\n", text)[0].strip(" .,:;!-\"'")
    words = clause.split()
    if len(words) > max_words:
        clause = " ".join(words[:max_words])
    clause = clause.strip(" .,:;!-\"'")
    if len(clause) < 8:
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
    url = f"{ENDPOINT}?token={token}"
    req = urllib.request.Request(
        url, data=data, method="POST", headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        body = resp.read().decode()
    return json.loads(body) if body.strip() else []


def scrape_profiles(
    urls: list[str],
    cache_file: Path,
    token: str,
    max_posts: int = DEFAULT_MAX_POSTS,
    *,
    force: bool = False,
) -> dict[str, list[dict]]:
    """Return {handle: [post_summary, ...]} for the given LinkedIn URLs.

    Uses the on-disk cache to skip already-scraped handles. One batched actor
    call covers all uncached URLs. Handles returning no posts are cached as
    empty lists so silent profiles are not re-paid for.
    """
    with _cache_lock(cache_file):
        cache = _load_cache(cache_file)
        result: dict[str, list[dict]] = {}
        pending: list[str] = []
        pending_handles: list[str] = []

        for url in urls:
            h = li_handle(url)
            if not h:
                continue
            if not force and h in cache:
                result[h] = cache[h].get("posts", [])
            else:
                pending.append(url)
                pending_handles.append(h)

        if not pending:
            return result

        if not token:
            raise RuntimeError("APIFY_API_TOKEN not set. Add it to .env (see .env.example).")

        CHUNK = 40
        stamp = date.today().isoformat()
        for offset in range(0, len(pending), CHUNK):
            chunk_urls = pending[offset : offset + CHUNK]
            chunk_handles = pending_handles[offset : offset + CHUNK]
            try:
                items = _call_actor(chunk_urls, token, max_posts)
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
                detail = ""
                if isinstance(exc, urllib.error.HTTPError):
                    try:
                        detail = exc.read().decode()[:200]
                    except Exception:
                        detail = ""
                print(f"Apify LinkedIn scrape failed (chunk {offset // CHUNK + 1}): {exc} {detail}")
                continue

            grouped: dict[str, list[dict]] = {}
            for post in items:
                if (post.get("type") or "post") not in ("post", "repost", "quote"):
                    continue
                summary = _summarize_post(post)
                for h in _post_handles(post):
                    grouped.setdefault(h, []).append(summary)

            for h in chunk_handles:
                posts = grouped.get(h, [])[:max_posts]
                cache[h] = {"posts": posts, "scraped_at": stamp}
                result[h] = posts
            _save_cache(cache_file, cache)

        return result


def posts_for_url(url: str, scraped: dict[str, list[dict]]) -> list[dict]:
    return scraped.get(li_handle(url), [])
