#!/usr/bin/env python3
"""Verify lead emails via Reoon API with a hard daily credit cap (default 500)."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".reoon"
STATE_FILE = STATE_DIR / "daily_usage.json"
CACHE_FILE = STATE_DIR / "verified_cache.json"
REJECTED_FILE = STATE_DIR / "rejected.json"
API_BASE = "https://emailverifier.reoon.com/api/v1"

EMAIL_COLUMNS = ("primary_email", "Email", "email", "Email Address")

# Keep these Reoon statuses in the single verified list; drop everything else.
KEEP_STATUSES = frozenset({"safe", "role_account"})


def campaign_stem(stem: str) -> str:
    """Return campaign prefix without row-count or stage suffixes."""
    s = stem.lower().replace("-38k", "")
    for suffix in ("-with-email", "-cleaned", "-verified", "-valid", "-normalized"):
        if s.endswith(suffix):
            s = s[: -len(suffix)]
    parts = s.split("-")
    alpha: list[str] = []
    for part in parts:
        if part.isdigit():
            break
        if part in {"cleaned", "verified", "valid", "normalized"}:
            break
        alpha.append(part)
    return "-".join(alpha) or "mixed"


def verified_output_path(source: Path, override: Path | None = None) -> Path:
    """Stable path: leads/<campaign>-verified.csv (same file every daily run)."""
    if override is not None:
        return override if override.is_absolute() else ROOT / override
    return source.parent / f"{campaign_stem(source.stem)}-verified.csv"


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def api_get(path: str, params: dict, api_key: str) -> dict:
    params = {**params, "key": api_key}
    url = f"{API_BASE}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def api_post(path: str, body: dict) -> tuple[int, dict]:
    url = f"{API_BASE}/{path}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url, data=data, method="POST", headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode()
        try:
            return exc.code, json.loads(payload)
        except json.JSONDecodeError:
            return exc.code, {"status": "error", "reason": payload}


def today_str() -> str:
    return date.today().isoformat()


def load_json(path: Path, default: dict) -> dict:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def daily_usage() -> dict:
    usage = load_json(STATE_FILE, {"date": today_str(), "verified_count": 0})
    if usage.get("date") != today_str():
        usage = {"date": today_str(), "verified_count": 0}
    return usage


def record_usage(count: int) -> None:
    usage = daily_usage()
    usage["verified_count"] = int(usage.get("verified_count", 0)) + count
    save_json(STATE_FILE, usage)


def account_balance(api_key: str) -> dict:
    balance = api_get("check-account-balance/", {}, api_key)
    if balance.get("status") != "success":
        raise SystemExit(f"Balance check failed: {balance}")
    return balance


def remaining_today(daily_limit: int, api_key: str) -> int:
    usage = daily_usage()
    local_left = max(0, daily_limit - int(usage.get("verified_count", 0)))

    try:
        balance = account_balance(api_key)
        api_daily = int(balance.get("remaining_daily_credits", 0))
        print(
            f"Reoon credits — daily remaining: {api_daily}, "
            f"instant remaining: {balance.get('remaining_instant_credits', '?')}"
        )
        return min(local_left, api_daily)
    except Exception as exc:
        print(f"Warning: could not check balance ({exc}); using local cap only.", file=sys.stderr)
        return local_left


def verify_batch(
    batch: list[str],
    api_key: str,
    task_name: str,
    stamp: str,
) -> dict[str, dict]:
    verified: dict[str, dict] = {}
    if len(batch) < 10:
        for email in batch:
            verified[email] = verify_single(email, api_key)
            verified[email]["verified_at"] = stamp
            time.sleep(0.2)
    else:
        results = verify_bulk(batch, api_key, task_name)
        for email, data in results.items():
            data["verified_at"] = stamp
            verified[email.lower()] = data
    return verified


def load_cache() -> dict:
    return load_json(CACHE_FILE, {})


def save_cache(cache: dict) -> None:
    save_json(CACHE_FILE, cache)


def load_rejected() -> dict[str, dict]:
    """Addresses known to have been checked, but with no result on hand.

    The cache already records every Reoon answer, rejections included. This
    file covers the other case: a run whose cache was later lost, where
    ``seed_cache_from_verified`` could restore only the addresses that
    *passed*. The rejects are recovered by inference from a list that finished
    verifying, and kept in a separate file so an inference is never mistaken
    for a Reoon result. ``--recheck-rejected`` ignores it.
    """
    data = load_json(REJECTED_FILE, {})
    addresses = data.get("addresses") if isinstance(data, dict) else None
    return addresses if isinstance(addresses, dict) else {}


def split_emails(raw: str) -> list[str]:
    parts = [p.strip() for p in (raw or "").replace(";", "|").split("|")]
    return [p.lower() for p in parts if p and "@" in p]


def extract_emails_from_csv(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise SystemExit(f"No columns in {path}")
        col = next((c for c in EMAIL_COLUMNS if c in reader.fieldnames), None)
        if not col:
            raise SystemExit(
                f"No email column found in {path}. Expected one of: {', '.join(EMAIL_COLUMNS)}"
            )
        seen: set[str] = set()
        ordered: list[str] = []
        for row in reader:
            for email in split_emails(row.get(col, "")):
                if email not in seen:
                    seen.add(email)
                    ordered.append(email)
        return ordered


def verify_single(email: str, api_key: str) -> dict:
    data = api_get("verify", {"email": email, "mode": "power"}, api_key)
    data.setdefault("email", email)
    return data


def verify_bulk(emails: list[str], api_key: str, task_name: str) -> dict[str, dict]:
    status, created = api_post(
        "create-bulk-verification-task/",
        {"name": task_name[:25], "emails": emails, "key": api_key},
    )
    if status != 201 or created.get("status") != "success":
        raise SystemExit(f"Bulk task creation failed ({status}): {created}")

    task_id = created["task_id"]
    print(f"Bulk task {task_id} created — verifying {created.get('count_processing', len(emails))} emails…")

    while True:
        result = api_get(
            "get-result-bulk-verification-task/",
            {"task_id": task_id},
            api_key,
        )
        task_status = result.get("status")
        pct = result.get("progress_percentage", 0)
        checked = result.get("count_checked", 0)
        total = result.get("count_total", "?")
        print(f"  status={task_status} progress={pct}% ({checked}/{total})")

        if task_status == "completed":
            return result.get("results") or {}
        if task_status in {"file_not_found", "file_loading_error"} or result.get("status") == "error":
            raise SystemExit(f"Bulk verification failed: {result}")

        time.sleep(5)


def write_verified_list(
    source: Path,
    output: Path,
    cache: dict[str, dict],
) -> tuple[int, int, dict[str, int], Path]:
    """Rewrite the single verified list from source + cache.

    Keeps only Status in KEEP_STATUSES (safe, role_account). Same output path
    every run so each day's 500 verification grows the same file.

    A row may carry several addresses (``a@x.com|b@x.com``) and every one of
    them costs a credit, because ``extract_emails_from_csv`` sends them all.
    The row is kept if *any* of them passed, and the address written back is the
    one that did — otherwise a business would be dropped over a dead info@ while
    its owner's working address sat verified in the same cell, and a row kept on
    its secondary would send mail to the address we know is bad.
    """
    with source.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        if "Status" not in fieldnames:
            fieldnames.append("Status")

        col = next((c for c in EMAIL_COLUMNS if c in fieldnames), "Email")
        rows: list[dict] = []
        seen_emails: set[str] = set()
        checked = 0
        status_counts: dict[str, int] = {}

        for row in reader:
            results: list[tuple[str, str]] = []
            for email in split_emails(row.get(col, "")):
                status = str(cache.get(email, {}).get("status") or "").strip().lower()
                if not status:
                    continue
                # Counted per address, not per row: the ratio printed against
                # the source is a count of addresses, and every one was paid for.
                checked += 1
                status_counts[status] = status_counts.get(status, 0) + 1
                results.append((email, status))

            keep = next(((e, s) for e, s in results if s in KEEP_STATUSES), None)
            if keep is None:
                continue
            email, status = keep
            if email in seen_emails:
                continue
            seen_emails.add(email)
            out_row = {k: row.get(k, "") for k in fieldnames if k != "Status"}
            out_row[col] = email
            out_row["Status"] = status
            rows.append(out_row)

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    return len(rows), checked, status_counts, output


def main() -> None:
    load_dotenv(ROOT / ".env")

    parser = argparse.ArgumentParser(
        description="Verify lead emails via Reoon (max 500/day on free tier)."
    )
    parser.add_argument("csv", type=Path, help="Input lead CSV in leads/")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Stable verified list (default: leads/<campaign>-verified.csv)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=int(os.environ.get("REOON_DAILY_LIMIT", "500")),
        help="Max emails to verify today (default: 500 or REOON_DAILY_LIMIT)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show plan only; no API calls")
    parser.add_argument("--force", action="store_true", help="Re-verify cached emails")
    parser.add_argument(
        "--recheck-rejected",
        action="store_true",
        help="Spend credits on addresses tombstoned in .reoon/rejected.json",
    )
    parser.add_argument(
        "--full-list",
        action="store_true",
        help="Verify all pending emails via bulk API (uses instant credits after daily cap)",
    )
    parser.add_argument(
        "--instant",
        action="store_true",
        help="Ignore the local/daily free-credit cap and verify --limit emails via bulk (uses instant credits)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=2000,
        help="Bulk batch size when using --full-list (default: 2000, max 50000)",
    )
    args = parser.parse_args()

    api_key = os.environ.get("REOON_API_KEY", "").strip()
    if not api_key and not args.dry_run:
        raise SystemExit(
            "REOON_API_KEY not set. Copy .env.example to .env and add your key."
        )

    source = args.csv if args.csv.is_absolute() else ROOT / args.csv
    if not source.is_file():
        raise SystemExit(f"File not found: {source}")

    output = verified_output_path(source, args.output)

    all_emails = extract_emails_from_csv(source)
    cache = load_cache() if not args.force else {}
    rejected = {} if (args.force or args.recheck_rejected) else load_rejected()
    pending = [e for e in all_emails if e not in cache and e not in rejected]
    skipped_cached = sum(1 for e in all_emails if e in cache)
    skipped_rejected = sum(1 for e in all_emails if e not in cache and e in rejected)

    print(f"Source: {source}")
    print(f"Verified list (stable): {output}")
    print(f"Keep statuses: {', '.join(sorted(KEEP_STATUSES))}")
    print(f"Unique emails in CSV: {len(all_emails)}")
    print(f"Already cached (skipped): {skipped_cached}")
    if skipped_rejected:
        print(f"Known rejected, no result cached (skipped): {skipped_rejected} "
              "— use --recheck-rejected to spend credits on these")
    print(f"Pending verification: {len(pending)}")

    if args.dry_run:
        if args.full_list:
            print(f"Full-list mode: would verify all {len(pending)} pending emails in bulk")
        elif args.instant:
            print(f"Instant mode: would verify next {min(args.limit, len(pending))} pending via bulk/instant credits")
        else:
            budget = remaining_today(args.limit, api_key)
            batch = pending[:budget]
            print(f"Daily budget remaining: {budget}")
            print(f"Will verify this run: {len(batch)}")
            if len(pending) > len(batch):
                print(f"Deferred: {len(pending) - len(batch)} — use --instant or --full-list or run again tomorrow")
        return

    total_verified_run = 0
    stamp = today_str()

    if args.full_list:
        if not pending:
            print("Nothing new to verify.")
        else:
            balance = account_balance(api_key)
            instant = int(balance.get("remaining_instant_credits", 0))
            daily = int(balance.get("remaining_daily_credits", 0))
            print(f"Reoon credits — daily remaining: {daily}, instant remaining: {instant}")
            chunk = max(1, min(args.chunk_size, 50000))
            remaining = list(pending)
            batch_num = 0
            while remaining:
                batch_num += 1
                batch = remaining[:chunk]
                print(f"\nBulk batch {batch_num}: verifying {len(batch)} emails…")
                verified = verify_batch(batch, api_key, f"{source.stem[:20]}-{batch_num}", stamp)
                cache.update(verified)
                save_cache(cache)
                record_usage(len(batch))
                total_verified_run += len(batch)
                remaining = remaining[len(batch):]
                kept = sum(
                    1
                    for e in batch
                    if str(verified.get(e, cache.get(e, {})).get("status", "")).lower()
                    in KEEP_STATUSES
                )
                print(f"Batch {batch_num} done — {kept} kept (safe/role_account). Remaining: {len(remaining)}")
            print(f"\nFull-list verification complete: {total_verified_run} emails checked.")
    elif args.instant:
        batch = pending[: args.limit]
        print(f"Instant mode: verifying {len(batch)} emails via bulk (uses instant credits)")
        if not batch:
            print("Nothing new to verify. Refreshing verified list from cache.")
        else:
            balance = account_balance(api_key)
            print(
                f"Reoon credits — daily remaining: {balance.get('remaining_daily_credits')}, "
                f"instant remaining: {balance.get('remaining_instant_credits')}"
            )
            verified = verify_batch(batch, api_key, source.stem[:25], stamp)
            cache.update(verified)
            save_cache(cache)
            total_verified_run = len(batch)
            kept = sum(
                1
                for e in batch
                if str(verified.get(e, cache.get(e, {})).get("status", "")).lower()
                in KEEP_STATUSES
            )
            print(f"\nDone. Verified {len(batch)} emails this run ({kept} kept: safe/role_account).")
    else:
        budget = remaining_today(args.limit, api_key)
        batch = pending[:budget]
        print(f"Daily budget remaining: {budget}")
        print(f"Will verify this run: {len(batch)}")
        if len(pending) > len(batch):
            print(f"Deferred (daily cap): {len(pending) - len(batch)} — use --instant or --full-list or run again tomorrow")

        if not batch:
            print("Nothing new to verify. Refreshing verified list from cache.")
        else:
            verified = verify_batch(batch, api_key, source.stem[:25], stamp)
            cache.update(verified)
            save_cache(cache)
            record_usage(len(batch))
            total_verified_run = len(batch)
            kept = sum(
                1
                for e in batch
                if str(verified.get(e, cache.get(e, {})).get("status", "")).lower()
                in KEEP_STATUSES
            )
            print(f"\nDone. Verified {len(batch)} emails this run ({kept} kept: safe/role_account).")

    kept_count, checked, status_counts, output = write_verified_list(source, output, cache)
    print(f"API-checked in source: {checked} / {len(all_emails)}")
    if status_counts:
        print("Status breakdown (checked):")
        for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
            mark = "keep" if status in KEEP_STATUSES else "drop"
            print(f"  {status}: {count} ({mark})")
    print(f"Verified list: {kept_count} rows -> {output}")

    usage = daily_usage()
    print(f"Used today (daily free cap tracker): {usage['verified_count']}/{args.limit}")


if __name__ == "__main__":
    main()
