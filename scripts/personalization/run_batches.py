#!/usr/bin/env python3
"""Run personalization for one or more batches from the manifest."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from personalization import process_batch as pb  # noqa: E402
from personalization.merge_enriched import merge_enriched  # noqa: E402
from personalization.process_batch import merged_output_path, process_batch  # noqa: E402

MANIFEST = ROOT / "campaigns" / "mix-leads-batch-manifest.json"


def _source_from_manifest() -> Path:
    """Read the source CSV recorded in the manifest; fall back to the default."""
    default = ROOT / "leads" / "all-leads-with-email-normalized.csv"
    if not MANIFEST.exists():
        return default
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    src = manifest.get("source")
    return (ROOT / src) if src else default


SOURCE = _source_from_manifest()


def update_master_review(manifest_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    copy_dir = ROOT / "copy"
    total_pass = 0
    total_emails = 0
    batch_summaries = []

    for batch in manifest["batches"]:
        bid = batch["id"]
        json_path = copy_dir / f"mix-leads-emails-batch-{bid}.json"
        if not json_path.exists():
            continue
        data = json.loads(json_path.read_text(encoding="utf-8"))
        bp = sum(1 for lead in data for step in lead["sequence"] if step["qa"]["pass"])
        bt = sum(len(lead["sequence"]) for lead in data)
        total_pass += bp
        total_emails += bt
        batch_summaries.append((bid, len(data), bp, bt, batch.get("status", "")))

    lines = [
        "# Mix leads master review",
        f"Date: {date.today().isoformat()}",
        f"Total leads processed: {sum(s[1] for s in batch_summaries)}",
        f"QA pass rate: {total_pass}/{total_emails}",
        "",
        "| Batch | Leads | QA pass | Status |",
        "| --- | ---: | ---: | --- |",
    ]
    for bid, leads, bp, bt, status in batch_summaries:
        lines.append(f"| {bid} | {leads} | {bp}/{bt} | {status} |")

    out = ROOT / "copy" / "mix-leads-master-review.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Master review -> {out}")


def _warm_linkedin_cache(targets: list[str]) -> None:
    """Scrape all LinkedIn URLs across target batches in one call up front.

    Warming the cache before parallel workers start prevents duplicate paid
    Apify calls and cache-file write races.
    """
    if not pb.LINKEDIN_ENRICH or not MANIFEST.exists():
        return
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    target_set = set(targets)
    row_ids: list[int] = []
    for batch in manifest["batches"]:
        if batch["id"] in target_set:
            row_ids.extend(batch["rows"])
    if not row_ids:
        return
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    urls = []
    for i in row_ids:
        if 0 <= i < len(rows):
            url = (rows[i].get("Linkedin_URL") or "").strip()
            if url:
                urls.append(url)
    if not urls:
        return
    print(f"Warming LinkedIn cache for {len(urls)} URLs across {len(targets)} batches...")
    try:
        scraped = pb.linkedin_apify.scrape_profiles(urls, max_posts=pb.LINKEDIN_MAX_POSTS)
        found = sum(1 for v in scraped.values() if v)
        print(f"LinkedIn cache warmed: {found} profiles with posts.")
    except SystemExit as exc:
        print(f"LinkedIn warm skipped ({exc}); continuing without LinkedIn.")


def _run_one_batch(bid: str, auto_merge: bool = True) -> tuple[str, dict | Exception]:
    try:
        result = process_batch(bid, SOURCE, MANIFEST, auto_merge=auto_merge)
        return bid, result
    except Exception as exc:
        return bid, exc


def run_batches(
    batch_ids: list[str] | None = None,
    all_pending: bool = False,
    merge: bool = False,
    workers: int = 1,
) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    # Parallel runs must not merge concurrently; merge once at the end instead.
    auto_merge = workers <= 1

    if all_pending:
        targets = [b["id"] for b in manifest["batches"] if b.get("status") == "pending"]
    elif batch_ids:
        targets = batch_ids
    else:
        raise SystemExit("Specify --batch-id, --from/--to, or --all-pending")

    if not targets:
        print("No batches to process.")
        return

    _warm_linkedin_cache(targets)

    if workers <= 1:
        for i, bid in enumerate(targets, 1):
            print(f"[{i}/{len(targets)}] Processing batch {bid}...")
            _, result = _run_one_batch(bid, auto_merge=auto_merge)
            if isinstance(result, Exception):
                raise result
            print(f"  -> batch {bid}: {result.get('qa_pass', '?')}/{result.get('qa_total', '?')} QA pass")
    else:
        print(f"Processing {len(targets)} batches with {workers} parallel workers...")
        completed = 0
        failures: list[tuple[str, Exception]] = []
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_run_one_batch, bid, False): bid for bid in targets}
            for future in as_completed(futures):
                bid, result = future.result()
                completed += 1
                if isinstance(result, Exception):
                    failures.append((bid, result))
                    print(f"[{completed}/{len(targets)}] batch {bid} FAILED: {result}")
                else:
                    print(
                        f"[{completed}/{len(targets)}] batch {bid}: "
                        f"{result.get('qa_pass', '?')}/{result.get('qa_total', '?')} QA pass"
                    )
        if failures:
            failed_ids = ", ".join(bid for bid, _ in failures)
            raise SystemExit(f"{len(failures)} batch(es) failed: {failed_ids}")

    if merge or not auto_merge:
        merge_enriched(output_path=merged_output_path(SOURCE), manifest_path=MANIFEST)
        update_master_review(MANIFEST)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-id", action="append")
    parser.add_argument("--from", dest="from_id", default="001")
    parser.add_argument("--to", dest="to_id")
    parser.add_argument("--all-pending", action="store_true")
    parser.add_argument("--merge", action="store_true")
    parser.add_argument("--workers", type=int, default=1, help="Parallel batch workers (default: 1)")
    parser.add_argument(
        "--no-render",
        action="store_true",
        help="Disable the headless-browser fallback for JS-rendered sites",
    )
    parser.add_argument(
        "--no-linkedin",
        action="store_true",
        help="Disable Apify LinkedIn recent-post enrichment",
    )
    args = parser.parse_args()

    if args.no_render:
        pb.RENDER_FALLBACK = False
    if args.no_linkedin:
        pb.LINKEDIN_ENRICH = False

    if args.all_pending:
        run_batches(all_pending=True, merge=args.merge, workers=args.workers)
        return

    if args.batch_id:
        run_batches(batch_ids=args.batch_id, merge=args.merge, workers=args.workers)
        return

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    all_ids = [b["id"] for b in manifest["batches"]]
    start = args.from_id
    end = args.to_id or all_ids[-1]
    targets = [bid for bid in all_ids if start <= bid <= end]
    run_batches(batch_ids=targets, merge=args.merge, workers=args.workers)


if __name__ == "__main__":
    main()
