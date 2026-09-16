#!/usr/bin/env python3
"""Apply signal/copy sanitizer to all batch artifacts and rebuild exports."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from lead_personalization import fsutil  # noqa: E402
from lead_personalization.qa import qa  # noqa: E402
from lead_personalization.sanitize import sanitize_email  # noqa: E402
from personalization import artifacts  # noqa: E402
from personalization.build_enriched import build_batch  # noqa: E402


def fix_batch(
    batch_id: str,
    source: Path,
    campaigns_dir: Path,
    enriched_dir: Path,
    copy_dir: Path,
    prefix: str = artifacts.DEFAULT_PREFIX,
) -> dict:
    research_path = artifacts.research_json(prefix, batch_id, campaigns_dir)
    copy_path = artifacts.copy_json(prefix, batch_id, campaigns_dir)
    if not research_path.exists() or not copy_path.exists():
        raise FileNotFoundError(f"Missing research/copy for batch {batch_id}")

    copy_data = fsutil.load_json(copy_path, {})

    emails_fixed = 0
    before_fail = 0
    after_fail = 0

    # research_signal is internal bookkeeping (never pasted into copy); the
    # copy paragraphs are the only text that can leak, so only they are scanned.
    for email, seq in copy_data.items():
        new_seq = []
        for step in seq:
            if isinstance(step, dict):
                subj, body = step["subject"], step["body"]
            else:
                subj, body = step[0], step[1]
            before_fail += int(not qa(subj, body)["pass"])
            new_subj, new_body = sanitize_email(subj, body)
            after_fail += int(not qa(new_subj, new_body)["pass"])
            if new_subj != subj or new_body != body:
                emails_fixed += 1
            new_seq.append([new_subj, new_body])
        copy_data[email] = new_seq

    fsutil.atomic_write_json(copy_path, copy_data)

    build_result = build_batch(
        source, research_path, copy_path, batch_id, enriched_dir, copy_dir, prefix=prefix
    )
    return {
        "batch_id": batch_id,
        "emails_touched": emails_fixed,
        "qa_before_fail": before_fail,
        "qa_after_fail": after_fail,
        **build_result,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="leads/mixed-4951-normalized.csv")
    parser.add_argument("--campaigns-dir", default="campaigns")
    parser.add_argument("--batch-id", action="append", help="Repeatable; default all 001-100")
    parser.add_argument(
        "--prefix",
        default=artifacts.DEFAULT_PREFIX,
        help="Which run's artifacts to sanitize (the pipeline names them by list slug)",
    )
    args = parser.parse_args()

    source = Path(args.source)
    if not source.is_absolute():
        source = ROOT / source
    campaigns_dir = Path(args.campaigns_dir)
    if not campaigns_dir.is_absolute():
        campaigns_dir = ROOT / campaigns_dir

    batch_ids = args.batch_id or [f"{i:03d}" for i in range(1, 101)]
    results = []
    total_before = 0
    total_after = 0

    for batch_id in batch_ids:
        result = fix_batch(
            batch_id,
            source,
            campaigns_dir,
            ROOT / "leads" / "enriched",
            ROOT / "copy",
            prefix=args.prefix,
        )
        results.append(result)
        total_before += result["qa_before_fail"]
        total_after += result["qa_after_fail"]
        print(
            f"Batch {batch_id}: QA {result['qa_pass']}/{result['qa_total']} "
            f"(pre-fix fails in copy scan: {result['qa_before_fail']} -> {result['qa_after_fail']})"
        )

    print(f"\nSanitized {len(batch_ids)} batches")
    print(f"QA failures in scanned emails: {total_before} -> {total_after}")


if __name__ == "__main__":
    main()
